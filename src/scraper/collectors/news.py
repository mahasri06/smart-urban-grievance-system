import feedparser

from normalizers.news_normalizer import (
    normalize_news_article,
    enrich_news_article
)
from processors.filter import (
    is_relevant,
    detect_categories
)
from processors.scoring import (
    calculate_severity
)

USER_AGENT = "civicpulse-project/1.0"

RSS_FEEDS = {
    "Google News": (
        "https://news.google.com/rss/search?q=Chennai+AND+"
        "(pothole+OR+road+OR+garbage+OR+sewage+OR+drainage+OR+trash+OR+"
        "\"power+cut\"+OR+water+OR+flooding+OR+waterlogging+OR+traffic+OR+"
        "civic+OR+encroachment+OR+street+OR+infrastructure)"
        "+when:1d"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    )
}

def fetch_rss_items(source, url):

    try:
        feed = feedparser.parse(url, agent=USER_AGENT)

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

        return items[:5]

    except Exception as e:
        print(f"Error fetching RSS from {source}: {e}")
        return []


def run():
    all_articles = []
    reports = []

    for source, url in RSS_FEEDS.items():
        articles = fetch_rss_items(source, url)
        all_articles.extend(articles)
        print(f"Found {len(articles)} raw headlines.")

    for raw_article in all_articles:
        report = normalize_news_article(raw_article)

        if not is_relevant(report["title"].lower()):
            continue

        # fill in body
        report = enrich_news_article(report)

        categories = detect_categories(report["full_text"])

        severity_score = calculate_severity(
            report["full_text"],
            categories=categories
        )

        report["categories"] = categories
        report["severity_score"] = severity_score

        reports.append(report)

    return reports


def fetch_and_process():
    return run()


if __name__ == "__main__":
    run()