"""
DEPRECATED — Legacy PRAW-based Reddit scraper.
================================================
This file is kept for reference only. It has been superseded by the
new scraper architecture:

  scraper/collectors/reddit.py  — Reddit collector (no auth, public JSON API)
  scraper/collectors/news.py    — Google News RSS collector
  scraper/main.py               — Unified orchestrator (runs both + saves to DB)

To run the scraper:
    cd src
    python scraper/main.py

Or via the API:
    POST /scraper/run

The new system does NOT require Reddit API credentials.
If you need PRAW-based multi-subreddit search (10 subreddits, keyword search),
you can restore this file and call scrape_and_store() from scraper/main.py.
"""

raise ImportError(
    "scraper/reddit.py is deprecated. "
    "Use scraper/main.py or POST /scraper/run instead."
)
