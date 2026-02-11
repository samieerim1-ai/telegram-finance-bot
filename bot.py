import os
import requests
import feedparser
import re
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.reuters.com/reuters/businessNews"
]

# ---------- CLEAN HTML ----------
def clean_html(raw_html):
    if raw_html is None:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', raw_html)

# ---------- FORMAT MESSAGE ----------
def format_news(title, summary, link):
    summary = clean_html(summary)
    summary = summary.replace("&nbsp;", " ")
    summary = summary.replace("&amp;", "&")
    summary = summary.strip()

    message = f"""
<b>{title}</b>

{summary[:220]}...

<a href="{link}">Read Full News</a>
"""
    return message

# ---------- SEND TELEGRAM ----------
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    response = requests.post(url, json=payload)
    print("TELEGRAM STATUS:", response.status_code)
    print("TELEGRAM RESPONSE:", response.text)

# ---------- MAIN ----------
def run_bot():
    print("BOT STARTED:", datetime.now())

    for feed_url in RSS_FEEDS:
        print("CHECKING:", feed_url)

        feed = feedparser.parse(feed_url)
        entries = feed.entries[:3]  # send top 3 news
        print("TOTAL ENTRIES:", len(entries))

        if len(entries) == 0:
            print("NO ENTRIES FOUND")
            continue

        for entry in entries:
            title = entry.get("title", "No Title")
            summary = entry.get("summary", "")
            link = entry.get("link", "")

            print("TITLE FOUND:", title)

            msg = format_news(title, summary, link)
            send_telegram(msg)

    print("RUN COMPLETED")

# ---------- RUN ----------
if __name__ == "__main__":
    run_bot()
