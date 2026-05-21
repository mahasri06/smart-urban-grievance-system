"""
Unified Scraper Orchestrator
=============================
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.collectors.reddit import fetch_and_process as reddit_fetch
from scraper.collectors.news import fetch_and_process as news_fetch
from scraper.config import CHENNAI_LOCALITIES

from database.database import SessionLocal
from entities.scraped_post_entity import ScrapedPost
from repositories.scraped_post_repository import ScrapedPostRepository
from nlp.nlp_service import process_text
from nlp.classifier import classify_text


# ---------------------------------------------------------------------------
# Category mapping
# ---------------------------------------------------------------------------
# The scraper config uses its own taxonomy (EMERGENCY, SANITATION, etc.)
# The rest of the system (DB, classifier, dashboard) uses a different set.
# This map translates scraper categories → system categories.
# When a post has multiple scraper categories, the highest-priority one wins.

_SCRAPER_TO_SYSTEM_CATEGORY = {
    "EMERGENCY":       "General",              # emergencies span multiple types
    "SANITATION":      "Water & Sanitation",
    "INFRASTRUCTURE":  "Roads & Traffic",
    "UTILITIES":       "Electricity",
    "TRANSPORT":       "Roads & Traffic",
    "PUBLIC_HEALTH":   "Noise & Pollution",
}

# Priority order — if a post matches multiple, pick the first in this list
_CATEGORY_PRIORITY = [
    "EMERGENCY",
    "PUBLIC_HEALTH",
    "SANITATION",
    "UTILITIES",
    "INFRASTRUCTURE",
    "TRANSPORT",
]


def map_category(scraper_categories: list[str]) -> str:
    """
    Maps a list of scraper categories to a single system category.
    Uses priority order so the most critical category wins.
    """
    for priority_cat in _CATEGORY_PRIORITY:
        if priority_cat in scraper_categories:
            return _SCRAPER_TO_SYSTEM_CATEGORY[priority_cat]
    return "General"


# ---------------------------------------------------------------------------
# Severity → Urgency mapping
# ---------------------------------------------------------------------------

def map_urgency(severity_score: float) -> str:
    """
    Converts the scraper's numeric severity score to HIGH / MEDIUM / LOW.
    Thresholds tuned to the scoring.py algorithm's typical output range.
    """
    if severity_score >= 10:
        return "HIGH"
    elif severity_score >= 5:
        return "MEDIUM"
    else:
        return "LOW"


# ---------------------------------------------------------------------------
# Location extractor
# ---------------------------------------------------------------------------

def extract_location(text: str) -> str | None:
    """
    Scans text for known Chennai localities (from config) and generic
    Indian city names. Returns the first match found, title-cased.
    """
    if not text:
        return None

    text_lower = text.lower()

    # Check Chennai localities first (more specific)
    for locality in CHENNAI_LOCALITIES:
        if locality.lower() in text_lower:
            return locality

    # Fallback: generic Indian cities
    generic_cities = [
        "bangalore", "bengaluru", "mumbai", "delhi", "chennai",
        "hyderabad", "pune", "kolkata", "nagpur", "ahmedabad",
    ]
    for city in generic_cities:
        if city in text_lower:
            return city.title()

    return None


# ---------------------------------------------------------------------------
# Report → ScrapedPost mapper
# ---------------------------------------------------------------------------

def report_to_scraped_post(report: dict, source_prefix: str) -> ScrapedPost | None:
    """
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
    location = extract_location(full_text)

    # Build a stable source_id so upsert can deduplicate
    # For Reddit: use the post ID embedded in the URL
    # For news: hash the URL
    url = report.get("url", "")
    if "reddit.com" in url:
        # URL format: https://reddit.com/r/chennai/comments/<id>/...
        parts = url.rstrip("/").split("/")
        source_id = f"reddit_{parts[6] if len(parts) > 6 else url[-12:]}"
        subreddit = "chennai"
        source = "reddit"
    else:
        import hashlib
        source_id = f"news_{hashlib.md5(url.encode()).hexdigest()[:12]}"
        subreddit = None
        source = report.get("source", "news")

    return ScrapedPost(
        source=source,
        source_id=source_id,
        subreddit=subreddit,
        title=title,
        body=body or None,
        url=url or None,
        location=location,
        upvotes=0,          # Reddit JSON API doesn't expose score easily; PRAW scraper handles this
        num_comments=0,
        author=None,
        cleaned_text=cleaned,
        category=system_category,
        urgency=urgency,
        sentiment=sentiment,
        # credibility_score set later by PageRank scorer
    )


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def scrape_and_store() -> dict:
    """
    Runs both collectors, maps reports to ScrapedPost entities,
    upserts into DB, and returns a summary dict.
    """
    print("[Scraper] Starting unified scrape (Reddit + News)...")

    all_posts: list[ScrapedPost] = []

    # 1. Reddit collector (no auth needed — uses public JSON API)
    print("[Scraper] Fetching from Reddit r/chennai...")
    try:
        reddit_reports = reddit_fetch()
        print(f"[Scraper] Reddit: {len(reddit_reports)} relevant posts collected.")
        for report in reddit_reports:
            post = report_to_scraped_post(report, "reddit")
            if post:
                all_posts.append(post)
    except Exception as e:
        print(f"[Scraper] Reddit collector failed: {e}")

    # 2. News collector (Google News RSS + article body fetch)
    print("[Scraper] Fetching from Google News RSS...")
    try:
        news_reports = news_fetch()
        print(f"[Scraper] News: {len(news_reports)} relevant articles collected.")
        for report in news_reports:
            post = report_to_scraped_post(report, "news")
            if post:
                all_posts.append(post)
    except Exception as e:
        print(f"[Scraper] News collector failed: {e}")

    if not all_posts:
        print("[Scraper] No posts collected from any source.")
        return {"reddit": 0, "news": 0, "total_new": 0}

    print(f"[Scraper] Total posts to upsert: {len(all_posts)}")

    # 3. Persist to DB (deduplicates by source_id)
    db = SessionLocal()
    try:
        new_posts = ScrapedPostRepository.upsert_bulk(db, all_posts)
        reddit_new = sum(1 for p in new_posts if p.source == "reddit")
        news_new = sum(1 for p in new_posts if p.source == "news")
        print(f"[Scraper] Inserted {len(new_posts)} new posts ({reddit_new} Reddit, {news_new} News).")
        return {"reddit": reddit_new, "news": news_new, "total_new": len(new_posts)}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = scrape_and_store()
    print(f"\n[Scraper] Done. Summary: {result}")
