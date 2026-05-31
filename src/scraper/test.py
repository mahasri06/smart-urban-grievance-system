import requests

headers = {
    "User-Agent": "Mozilla/5.0"
}

url = "https://old.reddit.com/r/chennai/.json"

r = requests.get(url, headers=headers)

print(r.status_code)