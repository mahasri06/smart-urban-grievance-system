"""
Unified Scraper Orchestrator:
Runs both the Reddit collector and the News collector, maps their output
to ScrapedPost entities using the shared category taxonomy, and persists
everything to the database.

Run standalone:
    cd src
    python scraper/main.py

Or trigger via the API:
    POST /scraper/run
"""

import sys
import os
import asyncio
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.collectors.reddit import fetch_and_process as reddit_fetch
from scraper.collectors.news import fetch_and_process as news_fetch
from scraper.config import CHENNAI_LOCALITIES

from database.database import SessionLocal
from entities.scraped_post_entity import ScrapedPost
from repositories.scraped_post_repository import ScrapedPostRepository
from nlp.nlp_service import process_text
from nlp.classifier import classify_text
from location.llm_parser import extract_locations_with_llm
from location.location_processor import misaligned_location


# Category mapping
# Maps scraper-specific keywords to system categories and resolves conflicts by priority.

_SCRAPER_TO_SYSTEM_CATEGORY = {
    "EMERGENCY":       "General",
    "SANITATION":      "Water & Sanitation",
    "INFRASTRUCTURE":  "Roads & Traffic",
    "UTILITIES":       "Electricity",
    "TRANSPORT":       "Roads & Traffic",
    "PUBLIC_HEALTH":   "Noise & Pollution",
}

# Priority order: first match wins when multiple categories are detected.

_CATEGORY_PRIORITY = [
    "EMERGENCY",
    "PUBLIC_HEALTH",
    "SANITATION",
    "UTILITIES",
    "INFRASTRUCTURE",
    "TRANSPORT",
]

def map_category(scraper_categories: list[str]) -> str:
    """Map scraper categories to system categories with priority ordering."""

    for priority_cat in _CATEGORY_PRIORITY:
        if priority_cat in scraper_categories:
            return _SCRAPER_TO_SYSTEM_CATEGORY[priority_cat]
    return "General"


def map_urgency(severity_score: float) -> str:
    """Map a severity score to urgency based on tuned thresholds."""
    if severity_score >= 10:
        return "HIGH"
    elif severity_score >= 5:
        return "MEDIUM"
    else:
        return "LOW"




def extract_location(text: str, method_counts: Counter | None = None) -> str | None:
    """
    Extracts a canonical location using the location package first.
    Strategy:
    1. Ask the LLM extractor for explicit neighborhood/location names.
    2. Normalize the first candidate through the Chennai fuzzy/geocode helper.
    3. Fall back to the old keyword matcher for deterministic coverage.
    """

    if not text:
        return None
    text_lower = text.lower()

    extracted_locations = extract_locations_with_llm(text)
    for candidate in extracted_locations:
        candidate = (candidate or "").strip()
        if not candidate:
            continue

        # Reject a generic city-level mention - prefer more specific zones
        _cand_norm = candidate.lower().strip("., ")
        if _cand_norm == "chennai":
            continue

        normalized = misaligned_location(candidate).get("location_name")
        if normalized and normalized != "Unknown":
            if method_counts is not None:
                method_counts["api"] += 1
            return normalized

        for locality in CHENNAI_LOCALITIES:
            if locality.lower() == candidate.lower():
                if method_counts is not None:
                    method_counts["llm"] += 1
                return locality

        if len(candidate) > 2:
            if method_counts is not None:
                method_counts["llm"] += 1
            return candidate.title()

    
    for locality in CHENNAI_LOCALITIES:
        if locality.lower() in text_lower:
            if method_counts is not None:
                method_counts["keyword"] += 1
            return locality

    return None


def report_to_scraped_post(
    report: dict,
    source_prefix: str,
    location_method_counts: Counter | None = None,
) -> ScrapedPost | None:
    """
    Report → ScrapedPost Mapper:
    Converts a normalised report dict (from collectors) into a ScrapedPost entity.
    The report dict has these keys (set by normalizers + processors):
        source, title, body, full_text, url, categories, severity_score
        created_at (reddit only), pubDate (news only)
    Returns None if the report is missing a title (unusable).
    """

    title = report.get("title", "").strip()
    if not title:
        return None

    body = report.get("body", "") or ""
    full_text = report.get("full_text", "") or f"{title} {body}".lower().strip()

    # Map scraper categories → system category
    scraper_categories = report.get("categories", [])
    system_category = map_category(scraper_categories)

    # Map severity score → urgency
    severity = report.get("severity_score", 0)
    urgency = map_urgency(severity)

    # NLP: clean text + sentiment (classifier already ran category/urgency above)
    cleaned = process_text(full_text)
    _, _, sentiment = classify_text(cleaned)

    # Location
    location = extract_location(full_text, location_method_counts)
    lat = None
    lng = None
    if location:
        geo = misaligned_location(location)
        if geo.get("location_name") != "Unknown":
            lat = geo.get("latitude")
            lng = geo.get("longitude")

    # Build a stable source_id so upsert can deduplicate
    # For Reddit: use the post ID embedded in the URL
    # For news: hash the URL
    url = report.get("url", "")
    if "reddit.com" in url:
        # URL format: https://reddit.com/r/chennai/comments/<id>/...
        parts = url.rstrip("/").split("/")
        source_id = f"reddit_{parts[6] if len(parts) > 6 else url[-12:]}"
        source = "reddit"
    else:
        import hashlib
        source_id = f"news_{hashlib.md5(url.encode()).hexdigest()[:12]}"
        source = report.get("source", "news")

    return ScrapedPost(
        source=source,
        source_id=source_id,
        title=title,
        description=body or None,
        url=url or None,
        location=location,
        lat=lat,
        lng=lng,
        cleaned_text=cleaned,
        category=system_category,
        urgency=urgency,
        sentiment=sentiment,
        status="UNVERIFIED",
        # credibility_score set later by PageRank scorer
    )


# Main orchestrator

async def scrape_and_store() -> dict:
    """Run collectors, map reports, upsert into DB, and return a summary."""
    print("[Scraper] Starting unified scrape (Reddit + News)...")

    all_posts: list[ScrapedPost] = []
    location_method_counts = Counter()
    locations_found = 0

    # Run both collectors together so slow news body fetches do not block Reddit.
    print("[Scraper] Fetching Reddit and Google News in parallel...")
    reddit_task = asyncio.create_task(reddit_fetch())
    news_task = asyncio.create_task(news_fetch())

    reddit_reports = []
    news_reports = []

    try:
        reddit_reports, news_reports = await asyncio.gather(
            reddit_task,
            news_task,
            return_exceptions=True,
        )
    except Exception as e:
        print(f"[Scraper] Collector scheduling failed: {e}")

    if isinstance(reddit_reports, Exception):
        print(f"[Scraper] Reddit collector failed: {reddit_reports}")
        reddit_reports = []
    else:
        print(f"[Scraper] Reddit: {len(reddit_reports)} relevant posts collected.")

    if isinstance(news_reports, Exception):
        print(f"[Scraper] News collector failed: {news_reports}")
        news_reports = []
    else:
        print(f"[Scraper] News: {len(news_reports)} relevant articles collected.")

    for report in reddit_reports:
        post = report_to_scraped_post(report, "reddit", location_method_counts)
        if post:
            all_posts.append(post)
            if post.location:
                locations_found += 1

    for report in news_reports:
        post = report_to_scraped_post(report, "news", location_method_counts)
        if post:
            all_posts.append(post)
            if post.location:
                locations_found += 1

    if not all_posts:
        print("[Scraper] No posts collected from any source.")
        return {
            "reddit": 0,
            "news": 0,
            "total_new": 0,
            "locations_found": 0,
            "location_method_counts": {"llm": 0, "api": 0, "keyword": 0},
        }

    print(f"[Scraper] Total posts to upsert: {len(all_posts)}")

    # Persist to DB (deduplicates by source_id)
    db = SessionLocal()
    try:
        new_posts = ScrapedPostRepository.upsert_bulk(db, all_posts)
        reddit_new = sum(1 for p in new_posts if p.source == "reddit")
        news_new = sum(1 for p in new_posts if p.source == "news")
        print(f"[Scraper] Inserted {len(new_posts)} new posts ({reddit_new} Reddit, {news_new} News).")
        return {
            "reddit": reddit_new,
            "news": news_new,
            "total_new": len(new_posts),
            "locations_found": locations_found,
            "location_method_counts": {
                "llm": location_method_counts.get("llm", 0),
                "api": location_method_counts.get("api", 0),
                "keyword": location_method_counts.get("keyword", 0),
            },
        }
    finally:
        db.close()



# Standalone entry point

if __name__ == "__main__":
    result = asyncio.run(scrape_and_store())
    print(f"\n[Scraper] Done. Summary: {result}")
