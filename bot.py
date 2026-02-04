import feedparser
import requests
import os
import html
import re
from datetime import datetime

BOT_TOKEN = os.getenv("8266991943:AAFz34w2ABb4yYpKjh6aJ91YHnjzzP7IHVI")
CHAT_ID = os.getenv("-1003859674623")

# -------- RSS FEEDS --------
RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://www.livemint.com/rss/markets",
]

# -------- KEYWORDS --------
KEYWORDS = [
    "india", "economy", "gdp", "inflation", "interest rate",
    "stock", "market", "sensex", "nifty", "s&p", "china",
    "trump", "imf", "world bank", "business", "trade",
]

# -------- CLEAN TEXT FUNCTION --------
def clean_text(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub('<.*?>', '', text)
    text = text.replace("\n", " ")
    return text.strip()

# -------- TELEGRAM SEND --------
def send_telegram_message(text, image_url=None):
    if image_url:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        data = {
            "chat_id": CHAT_ID,
            "photo": image_url,
            "caption": text,
            "parse_mode": "HTML"
        }
    else:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }

    requests.post(url, data=data)

# -------- DUPLICATE TRACK --------
POSTED_FILE = "posted.txt"

def load_posted():
    if not os.path.exists(POSTED_FILE):
        return set()
    with open(POSTED_FILE, "r") as f:
        return set(f.read().splitlines())

def save_posted(posted):
    with open(POSTED_FILE, "w") as f:
        for p in posted:
            f.write(p + "\n")

posted_titles = load_posted()

# -------- MAIN LOGIC --------
def main():
    global posted_titles
    new_posted = set(posted_titles)

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)

        # ENTRY LIMIT = 12
        for entry in feed.entries[:12]:

            title = clean_text(entry.title)
            summary = clean_text(entry.summary if hasattr(entry, "summary") else "")

            combined_text = (title + " " + summary).lower()

            # KEYWORD FILTER
            if not any(k in combined_text for k in KEYWORDS):
                continue

            # DUPLICATE FILTER
            if title in posted_titles:
                continue

            # SHORT SUMMARY
            summary = summary.split(".")[0]
            summary = summary[:180]

            if len(summary) < 40:
                summary = "Key financial update impacting global or Indian markets."

            # HEADLINE FORMAT
            headline = f"🚨 FINANCE ALERT | {title.title()}"

            message = f"{headline}\n\n{summary}\n\n— Global Finance Desk"

            # IMAGE EXTRACTION
            image_url = None
            if "media_content" in entry:
                image_url = entry.media_content[0]["url"]
            elif "links" in entry:
                for link in entry.links:
                    if link.type and "image" in link.type:
                        image_url = link.href
                        break

            send_telegram_message(message, image_url)

            new_posted.add(title)

    save_posted(new_posted)

# -------- RUN --------
if __name__ == "__main__":
    main()
