def normalize_reddit_post(post):

    data = post.get("data", {})

    title = data.get("title", "")
    body = data.get("selftext", "")

    return {

        "source": "reddit",

        "title": title,
        
        "body": body,

        "full_text":
            f"{title} {body}".lower().strip(),

        "url":
            f"https://reddit.com{data.get('permalink', '')}",

        "created_at":
            data.get("created_utc")
    }