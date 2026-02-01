import feedparser
import requests

BOT_TOKEN = "8266991943:AAHQzznF97suI5i47N813YqiYe4E6S56hBA"
CHAT_ID = "7981684652"

RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.cnbc.com/id/10001147/device/rss/rss.html"
]

posted = set()

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload)

for feed_url in RSS_FEEDS:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:2]:
        title = entry.title
        summary = entry.summary if hasattr(entry, "summary") else ""

        message = f"""🚨 Global Finance Update

{title}

{summary}

— Global Finance Desk
"""
        if title not in posted:
            send_message(message)
            posted.add(title)
