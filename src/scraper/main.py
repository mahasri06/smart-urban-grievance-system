import json
import asyncio
from collectors.reddit import fetch_and_process as reddit_fetch
from collectors.news import fetch_and_process as news_fetch


async def main():

    reddit_reports, news_reports = await asyncio.gather(
        reddit_fetch(),
        news_fetch()
    )

    for report in reddit_reports:
        output = {
            "source": report.get("source", ""),
            "title": report.get("title", ""),
            "body": report.get("body", ""),
            "categories": report.get("categories", []),
            "severity": report.get("severity_score", 0)
        }
        print(json.dumps(output, indent=2))
        print()

    for report in news_reports:
        output = {
            "source": report.get("source", ""),
            "title": report.get("title", ""),
            "body": report.get("body", ""),
            "categories": report.get("categories", []),
            "severity": report.get("severity_score", 0)
        }
        print(json.dumps(output, indent=2))
        print()


if __name__ == "__main__":
    asyncio.run(main())
