import asyncio
from email.utils import parsedate_to_datetime

import httpx

from normalizers.reddit_normalizer import (
    normalize_reddit_post
)

from processors.filter import (
    is_relevant,
    detect_categories
)

from processors.scoring import (
    calculate_severity
)


HEADERS = {
    "User-Agent":
        "civicpulse-project/1.0 "
        "(contact: malarmariam613@gmail.com)"
}


async def fetch_recent_posts(client):

    url = (
        "https://www.reddit.com/"
        "r/chennai/new.json?limit=100"
    )

    try:

        response = await client.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        # Reddit rate limit handling
        if response.status_code == 429:

            retry_after = response.headers.get(
                "Retry-After"
            )

            if retry_after:

                try:
                    wait_seconds = int(retry_after)

                except ValueError:

                    retry_time = parsedate_to_datetime(
                        retry_after
                    )

                    date_header = response.headers.get(
                        "Date"
                    )

                    now_time = (
                        parsedate_to_datetime(date_header)
                        if date_header
                        else retry_time
                    )

                    wait_seconds = max(
                        0,
                        int(
                            (
                                retry_time - now_time
                            ).total_seconds()
                        )
                    )

                print(
                    f"Rate limited by Reddit. "
                    f"Retry after {wait_seconds} seconds."
                )

                await asyncio.sleep(wait_seconds)

        response.raise_for_status()

        return response.json()["data"]["children"]

    except Exception as e:

        print(f"Error fetching data: {e}")
        return []


async def run():
    reports = []

    async with httpx.AsyncClient() as client:
        posts = await fetch_recent_posts(client)

        def process_post(raw_post):
            report = normalize_reddit_post(raw_post)
            if not is_relevant(report["title"].lower()):
                return None
            
            categories = detect_categories(report["full_text"])
            severity_score = calculate_severity(report["full_text"], categories)

            report["categories"] = categories
            report["severity_score"] = severity_score
            return report
        
        tasks = [asyncio.to_thread(process_post, post) for post in posts]
        results = await asyncio.gather(*tasks)

        reports = [r for r in results if r is not None]

    return reports


async def fetch_and_process():
    return await run()


if __name__ == "__main__":
    reports = asyncio.run(run())