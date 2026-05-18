import json
from collectors.reddit import fetch_and_process as reddit_fetch
from collectors.news import fetch_and_process as news_fetch


if __name__ == "__main__":
    
    reddit_reports = reddit_fetch()
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

    news_reports = news_fetch()
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
