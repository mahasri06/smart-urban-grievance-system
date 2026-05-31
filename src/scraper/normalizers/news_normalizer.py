import asyncio
import time

from googlenewsdecoder import gnewsdecoder
from newspaper import Article, Config


def fetch_article_body(article_link):
    try:
        result = gnewsdecoder(
            article_link,
            interval=0.2
        )

        if not result.get("status"):
            print("gnewsdecoder error:", result.get("message"))
            return ""
        real_url = result.get("decoded_url")

        if not real_url:
            print("gnewsdecoder returned no decoded_url")
            return ""

        # Configure newspaper3k
        config = Config()
        config.browser_user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        config.request_timeout = 10

        try:
            article = Article(real_url, config=config)
            article.download()
            article.parse()
            text = (article.text or "").strip()
            if text:
                return text
        except Exception:
            pass

        return ""

    except Exception as e:
        print(f"Failed to decode article: {e}")
        return ""


def normalize_news_article(article):
    title = article.get("title", "")
    url = article.get("url", "")

    return {
        "source":
            article.get("source", "news"),

        "title":
            title,

        "body":
            "",

        "full_text":
            "",

        "url":
            url,

        "pubDate":
            article.get("pubDate", "")
    }


async def enrich_news_article(report):
    start = time.perf_counter()
    body = await asyncio.to_thread(fetch_article_body, report["url"])
    elapsed = time.perf_counter() - start
    print(f"[NewsNormalizer] fetched body in {elapsed:.2f}s for {report.get('url')[:80]}")

    report["body"] = body
    report["full_text"] = f"{report['title']} {body}".lower().strip()

    return report