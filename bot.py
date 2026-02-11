import os
import requests
import feedparser
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.reuters.com/reuters/businessNews"
]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    r = requests.post(url, data=data)
    print("TELEGRAM STATUS:", r.status_code)
    print("TELEGRAM RESPONSE:", r.text)


def format_news(title, summary, link):
    msg = f"""
<b>{title}</b>

{summary[:200]}...

<a href="{link}">Read more</a>
"""
    return msg


def run_bot():
    print("BOT STARTED:", datetime.now())

    for feed_url in FEEDS:
        print("CHECKING:", feed_url)

        feed = feedparser.parse(feed_url)
        print("TOTAL ENTRIES:", len(feed.entries))  # DEBUG LINE

        if len(feed.entries) == 0:
            print("NO ENTRIES FOUND")
            continue

        # Take only first news to avoid spam
        entry = feed.entries[0]

        title = entry.get("title", "No Title")
        summary = entry.get("summary", "No Summary")
        link = entry.get("link", "")

        print("TITLE FOUND:", title)

        message = format_news(title, summary, link)
        send_telegram(message)

    print("RUN COMPLETED")


if __name__ == "__main__":
    run_bot()
