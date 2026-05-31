import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

import feedparser

from scraper.normalizers.news_normalizer import normalize_news_article, enrich_news_article
from scraper.processors.filter import is_relevant, detect_categories
from scraper.processors.scoring import calculate_severity

USER_AGENT = "civicpulse-project/1.0"

RSS_FEEDS = {
    "Google News": (
        "https://news.google.com/rss/search?q=Chennai+AND+"
        "(pothole+OR+road+OR+garbage+OR+sewage+OR+drainage+OR+trash+OR+"
        "\"power+cut\"+OR+water+OR+flooding+OR+waterlogging+OR+traffic+OR+"
        "civic+OR+encroachment+OR+street+OR+infrastructure)"
        "+when:7d"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    )
}

async def fetch_rss_items(source, url):

    try:
        feed = await asyncio.to_thread(feedparser.parse, url, agent=USER_AGENT)

        items = []
        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")

            entry_source = entry.get("source")
            publisher = ""
            if isinstance(entry_source, dict) or hasattr(entry_source, "get"):
                try:
                    publisher = entry_source.get("title", "")
                except Exception:
                    publisher = ""
            elif isinstance(entry_source, str):
                publisher = entry_source

            # Fixed: Feedparser normalizes pubDate/pubdate into 'published'
            pub_date = entry.get("published", "") or entry.get("updated", "")

            items.append({
                "source": publisher or source,
                "title": title,
                "url": link,
                "pubDate": pub_date
            })

        return items

    except Exception as e:
        print(f"Error fetching RSS from {source}: {e}")
        return []


async def run():
    all_articles = []
    reports = []

    feed_tasks = [fetch_rss_items(source, url) for source, url in RSS_FEEDS.items()]
    feed_results = await asyncio.gather(*feed_tasks)

    for (source, _), articles in zip(RSS_FEEDS.items(), feed_results):
        all_articles.extend(articles)
        print(f"Found {len(articles)} raw headlines from {source}.")

    semaphore = asyncio.Semaphore(8)

    async def process_article(raw_article):
        async with semaphore:
            report = normalize_news_article(raw_article)
            report = await enrich_news_article(report)

            # Filter after enrichment so title-only articles do not get dropped
            # before we inspect the decoded body text.
            if not is_relevant(report["full_text"]):
                return None

            categories = detect_categories(report["full_text"])

            severity_score = calculate_severity(
                report["full_text"],
                categories=categories
            )

            report["categories"] = categories
            report["severity_score"] = severity_score

            return report

    if all_articles:
        results = await asyncio.gather(*(process_article(article) for article in all_articles))
        reports = [report for report in results if report]

    return reports


async def fetch_and_process():
    return await run()


if __name__ == "__main__":
    asyncio.run(run())