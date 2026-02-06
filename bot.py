import feedparser
import requests
import os
import re
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html"
]

KEYWORDS = [
    "economy","gdp","inflation","interest","imf","world bank",
    "china","india","rupee","rbi","trade","currency","stock",
    "sensex","nifty","market","gold","oil","federal reserve","trump"
]

US_STOCK_BLOCK = [
    "dow jones","nasdaq","wall street","nyse","s&p 500"
]

posted_titles = set()

def send_message(text):
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(TELEGRAM_URL, data=payload)

def contains_keywords(text):
    text = text.lower()
    if any(u in text for u in US_STOCK_BLOCK):
        return False
    return any(k in text for k in KEYWORDS)

def clean_html(raw_html):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', raw_html)

def make_headline(title):
    title = title.replace("|","").strip()
    return f"🚨 {title}"

def split_bullets(summary):
    sentences = re.split(r'[.!?]', summary)
    bullets = []
    for s in sentences:
        s = s.strip()
        if len(s) > 40 and len(bullets) < 5:
            bullets.append(f"⚫ {s}")
    return "\n".join(bullets)

def bottom_line(summary):
    words = summary.split()
    short = " ".join(words[:25])
    return f"\n\n<b>Bottom Line:</b>\n{short}..."

def format_news(title, summary):
    headline = make_headline(title)
    bullets = split_bullets(summary)
    bottom = bottom_line(summary)

    final = f"""
<b>{headline}</b>

{summary[:220]}...

{bullets}

{bottom}

— Global Finance Desk
"""
    return final

def process_feed():
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries[:5]:
            title = entry.title
            summary = clean_html(entry.summary)

            if title in posted_titles:
                continue

            combined = title + " " + summary

            if contains_keywords(combined):
                message = format_news(title, summary)
                send_message(message)
                posted_titles.add(title)

def main():
    process_feed()

if __name__ == "__main__":
    main()
