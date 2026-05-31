from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from database.database import engine, Base

from api.complaint_controller import router as complaint_router

# Import all entities so SQLAlchemy registers them before create_all()
from entities.complaint_entity import Complaint
from entities.scraped_post_entity import ScrapedPost


app = FastAPI(
    title="Smart Urban Grievance Redressal System",
    description=(
        "Collects, classifies, and analyses urban civic complaints "
        "using NLP, Naive Bayes, and web data mining techniques."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all tables on startup
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(complaint_router)


# ---------------------------------------------------------------------------
# Scraper trigger endpoint
# ---------------------------------------------------------------------------

@app.post("/scraper/run", tags=["Scraper"])
def trigger_scraper(background_tasks: BackgroundTasks):
    """
    Triggers the unified scraper (Reddit + News) as a background task.
    Returns immediately — scraping happens asynchronously.
    Check the server logs for progress.
    """
    def _run_scraper():
        from scraper.main import scrape_and_store
        import asyncio
        asyncio.run(scrape_and_store())

    background_tasks.add_task(_run_scraper)
    return {"message": "Unified scraper (Reddit + News) started in background. Check server logs for progress."}


# ---------------------------------------------------------------------------
# Analytics endpoints for pattern mining + credibility
# ---------------------------------------------------------------------------

@app.get("/analytics/patterns/association", tags=["Analytics"])
def get_association_rules(
    min_support: float = 0.05,
    min_confidence: float = 0.4,
):
    """Run association rule mining and return results."""
    from database.dependencies import get_db as _get_db
    from database.database import SessionLocal
    from patterns.association_miner import run_association_mining

    db = SessionLocal()
    try:
        rules_df = run_association_mining(db, min_support=min_support, min_confidence=min_confidence)
        if rules_df.empty:
            return {"rules": [], "message": "No rules found. Add more data or lower thresholds."}
        return {"rules": rules_df.to_dict(orient="records")}
    finally:
        db.close()


@app.get("/analytics/patterns/sequential", tags=["Analytics"])
def get_sequential_patterns(min_support: int = 2):
    """Run sequential pattern mining and return results."""
    from database.database import SessionLocal
    from patterns.sequential_miner import run_sequential_mining

    db = SessionLocal()
    try:
        patterns = run_sequential_mining(db, min_support=min_support)
        return {"patterns": patterns}
    finally:
        db.close()


@app.post("/analytics/credibility/score", tags=["Analytics"])
def score_credibility(background_tasks: BackgroundTasks):
    """Trigger PageRank credibility scoring for all scraped posts."""
    def _run_scoring():
        from database.database import SessionLocal
        from credibility.pagerank_scorer import run_pagerank_scoring
        db = SessionLocal()
        try:
            run_pagerank_scoring(db)
        finally:
            db.close()

    background_tasks.add_task(_run_scoring)
    return {"message": "PageRank scoring started in background."}

# route to fetch the DB posts
@app.get("/analytics/scraped-posts", tags=["Analytics"])
def get_scraped_posts(
    min_credibility: float = 0.0,
    limit: int = 50,
):
    """Return scraped posts, optionally filtered by minimum credibility score."""
    from database.database import SessionLocal
    from repositories.scraped_post_repository import ScrapedPostRepository
    from location.location_processor import misaligned_location
    from entities.complaint_entity import Complaint

    def _resolve_coords(location_name, lat_value=None, lng_value=None):
        if lat_value is not None and lng_value is not None:
            return lat_value, lng_value
        if not location_name:
            return None, None
        result = misaligned_location(location_name)
        if result.get("location_name") == "Unknown":
            return None, None
        return result.get("latitude"), result.get("longitude")

    db = SessionLocal()
    try:
        if min_credibility > 0:
            posts = ScrapedPostRepository.get_high_credibility(db, threshold=min_credibility)
        else:
            posts = ScrapedPostRepository.get_all(db)

        complaints = (
            db.query(Complaint)
            .filter(Complaint.status == "PROCESSED")
            .order_by(Complaint.id.desc())
            .limit(limit)
            .all()
        )

        result = []
        for p in posts[:limit]:
            lat, lng = _resolve_coords(p.location, p.lat, p.lng)
            result.append({
                "id": p.id,
                "source": p.source,
                "title": p.title,
                "description": p.description,
                "cleaned_text": p.cleaned_text,
                "location": p.location,
                "lat": lat,
                "lng": lng,
                "category": p.category,
                "urgency": p.urgency,
                "sentiment": p.sentiment,
                "credibility_score": p.credibility_score,
                "scraped_at": p.scraped_at.isoformat() if p.scraped_at else None,
                "url": p.url,
            })

        for c in complaints:
            lat, lng = _resolve_coords(c.location, c.lat, c.lng)
            result.append({
                "id": c.id,
                "source": c.source or "citizen",
                "title": c.title,
                "description": c.description,
                "cleaned_text": c.cleaned_text,
                "location": c.location,
                "lat": lat,
                "lng": lng,
                "category": c.category,
                "urgency": c.urgency,
                "sentiment": c.sentiment,
                "credibility_score": None,
                "scraped_at": c.created_at.isoformat() if c.created_at else None,
                "url": None,
            })

        source_priority = {"citizen": 0, "reddit": 1, "news": 2}
        result.sort(key=lambda item: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(item.get("urgency"), 3),
            source_priority.get(item.get("source"), 9),
            item.get("id", 0),
        ))

        return result[:limit]
    finally:
        db.close()
