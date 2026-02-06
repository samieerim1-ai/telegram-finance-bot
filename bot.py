import os
import feedparser
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# -------- RSS FEEDS --------
RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
]

# -------- KEYWORDS --------
KEYWORDS = [
    "india", "sensex", "nifty", "stock", "gdp", "inflation",
    "china", "trump", "economy", "imf", "world bank",
    "interest rate", "rupee"
]

# Only India stock filter
INDIA_STOCK_WORDS = ["sensex", "nifty", "bse", "nse"]

ENTRY_LIMIT = 5

POSTED_FILE = "posted.txt"

# -------- TELEGRAM SEND --------
def send_telegram(text, image=None):
    if image:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        data = {"chat_id": CHAT_ID, "caption": text, "parse_mode": "HTML"}
        files = {"photo": requests.get(image).content}
        requests.post(url, data=data, files=files)
    else:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
        requests.post(url, data=data)

# -------- DUPLICATE CHECK --------
def is_posted(link):
    if not os.path.exists(POSTED_FILE):
        return False
    with open(POSTED_FILE) as f:
        return link in f.read()

def mark_posted(link):
    with open(POSTED_FILE, "a") as f:
        f.write(link + "\n")

# -------- IMAGE PICK --------
def get_image(entry):
    if "media_content" in entry:
        return entry.media_content[0]["url"]

    soup = BeautifulSoup(entry.get("summary", ""), "html.parser")
    img = soup.find("img")
    if img:
        return img["src"]

    return None

# -------- KEYWORD FILTER --------
def keyword_match(text):
    text = text.lower()

    # if stock word present but not India stock, skip
    if "stock" in text:
        if not any(w in text for w in INDIA_STOCK_WORDS):
            return False

    return any(k in text for k in KEYWORDS)

# -------- BULLETS --------
def split_bullets(summary, title):
    sentences = re.split(r'[.!?]', summary)
    bullets = []
    title_words = set(title.lower().split())

    for s in sentences:
        s = s.strip()
        if len(s) < 60:
            continue

        words = set(s.lower().split())
        if len(title_words.intersection(words)) > 4:
            continue

        short = " ".join(s.split()[:18])
        bullets.append(f"⚫ {short}...")

        if len(bullets) == 4:
            break

    return "\n".join(bullets)

# -------- BOTTOM LINE --------
def bottom_line(summary):
    sentences = re.split(r'[.!?]', summary)
    if len(sentences) > 2:
        line = sentences[-2]
    else:
        line = sentences[0]

    short = " ".join(line.split()[:20])
    return f"\n\n<b>Bottom Line:</b>\n{short}..."

# -------- FORMAT NEWS --------
def format_news(title, summary):
    clean_summary = BeautifulSoup(summary, "html.parser").get_text()
    intro = clean_summary.replace(title, "")[:220]

    bullets = split_bullets(clean_summary, title)
    bottom = bottom_line(clean_summary)

    message = f"""🚨 <b>{title}</b>

{intro}...

{bullets}
{bottom}

— Global Finance Desk
"""
    return message

# -------- MAIN --------
def run():
    count = 0

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            if count >= ENTRY_LIMIT:
                return

            title = entry.title
            summary = entry.get("summary", "")
            link = entry.link

            if is_posted(link):
                continue

            combined_text = (title + " " + summary)

            if not keyword_match(combined_text):
                continue

            image = get_image(entry)
            message = format_news(title, summary)

            send_telegram(message, image)
            mark_posted(link)

            count += 1


if __name__ == "__main__":
    run()
