import feedparser
import requests
import json
import os
import re

# =========================
# TELEGRAM SETTINGS
# =========================
BOT_TOKEN = "8266991943:AAFz34w2ABb4yYpKjh6aJ91YHnjzzP7IHVI"
CHAT_ID = "-1003859674623"

# =========================
# RSS SOURCES
# =========================
RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.moneycontrol.com/rss/economy.xml",
    "https://www.moneycontrol.com/rss/market.xml" ,
    "https://www.moneycontrol.com/rss/business.xml" ,


    "https://www.imf.org/en/News/RSS",
]

# =========================
# KEYWORD FILTER
# =========================
KEYWORDS = [
    "global economy",
    "trump",
    "stock market",
    "sensex",
    "nifty",
    "s&p",
    "s&p 500",
    "china",
    "india economy",
    "india business",
    "indian economy",
    "imf",
    "world bank",
    "interest rate",
    "interest rates",
    "gdp",
    "inflation",
    "rupee",
    "federal reserve",
    "fed"
]

# =========================
# LOAD PREVIOUS POSTS
# =========================
POSTED_FILE = "posted.json"

if os.path.exists(POSTED_FILE):
    with open(POSTED_FILE, "r") as f:
        posted = set(json.load(f))
else:
    posted = set()

# =========================
# TELEGRAM FUNCTIONS
# =========================
def send_text(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload)

def send_photo(text, image_url):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": text
    }
    requests.post(url, json=payload)

# =========================
# CLEAN HTML TAGS
# =========================
def clean_html(raw_html):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', raw_html)

# =========================
# MAIN LOGIC
# =========================
for feed_url in RSS_FEEDS:
    feed = feedparser.parse(feed_url)

    for entry in feed.entries[:20]:

        title = entry.title.strip()
        summary = entry.summary if hasattr(entry, "summary") else ""
        summary = clean_html(summary)
        summary = summary[:280]

        combined_text = (title + " " + summary).lower()

        # KEYWORD FILTER
        if not any(keyword in combined_text for keyword in KEYWORDS):
            continue

        # DUPLICATE FILTER
        if title in posted:
            continue

        # HEADLINE STYLE
        headline = f"🚨 FINANCE ALERT | {title.upper()}"

        message = f"""{headline}

{summary}

— Global Finance Desk
"""

        # IMAGE DETECTION
        image_url = None
        if 'media_content' in entry:
            image_url = entry.media_content[0]['url']
        elif 'links' in entry:
            for link in entry.links:
                if link.type and "image" in link.type:
                    image_url = link.href
                    break

        # SEND
        try:
            if image_url:
                send_photo(message, image_url)
            else:
                send_text(message)

            posted.add(title)

        except Exception as e:
            print("Error:", e)

# =========================
# SAVE POSTED HEADLINES
# =========================
with open(POSTED_FILE, "w") as f:
    json.dump(list(posted), f)
