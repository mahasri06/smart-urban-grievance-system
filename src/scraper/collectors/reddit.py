import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from email.utils import parsedate_to_datetime
from typing import Any

import requests

from scraper.normalizers.reddit_normalizer import normalize_reddit_post
from scraper.processors.filter import is_relevant, detect_categories
from scraper.processors.scoring import calculate_severity


# HEADERS = {
#     "User-Agent":
#         "civicpulse-project/1.0 "
#         "(contact: malarmariam613@gmail.com)"
# }
HEADERS = {
    # This imitates a standard Windows machine running Google Chrome
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5"
}


def _fetch_recent_posts_sync() -> list[dict[str, Any]]:

    url = (
        "https://www.reddit.com/r/chennai/search.json?"
        "q=water OR power OR road OR flood OR garbage OR traffic OR pothole"
        "&restrict_sr=on&sort=new&limit=100"
    )

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    wait_seconds = int(retry_after)
                except ValueError:
                    retry_time = parsedate_to_datetime(retry_after)
                    date_header = response.headers.get("Date")
                    now_time = (
                        parsedate_to_datetime(date_header)
                        if date_header
                        else retry_time
                    )
                    wait_seconds = max(
                        0,
                        int((retry_time - now_time).total_seconds())
                    )
                print(
                    f"Rate limited by Reddit. Retry after {wait_seconds} seconds."
                )
                return []

            response = requests.get(url, headers=HEADERS, timeout=10)

        response.raise_for_status()

        return response.json()["data"]["children"]

    except Exception as e:

        print(f"Error fetching data: {e}")
        return []


async def run():
    posts = await asyncio.to_thread(_fetch_recent_posts_sync)
    reports = []

    for raw_post in posts:
        report = normalize_reddit_post(
            raw_post
        )

        if not is_relevant(report["title"]):
            continue

        categories = detect_categories(
            report["full_text"]
        )

        severity_score = calculate_severity(
            report["full_text"],
            categories
        )

        report["categories"] = categories

        report["severity_score"] = (
            severity_score
        )

        reports.append(report)

    return reports


async def fetch_and_process():
    return await run()


if __name__ == "__main__":
    asyncio.run(run())