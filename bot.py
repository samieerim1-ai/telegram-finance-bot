import os
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from html import unescape
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
AI_KEY = os.getenv("AI_KEY")

print("BOT STARTED")

client = OpenAI(
    api_key=AI_KEY,
    base_url="https://openrouter.ai/api/v1"
)

RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.reuters.com/reuters/businessNews"
]

posted_titles = set()

# ---------- CLEAN TEXT ----------
def clean_text(text):
    text = unescape(text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'http\S+', '', text)
    return text.strip()

# ---------- IMAGE ----------
def get_image(entry):
    if "media_content" in entry:
        return entry.media_content[0]['url']
    return None

# ---------- AI FORMAT ----------
def ai_format_news(title, summary):
    print("AI CALLED")

    prompt = f"""
Rewrite this financial news professionally.

Format:
Headline
2 line intro
4 bullet key takeaways
Bottom Line

Simple English. No links.

Title: {title}
Summary: {summary}
"""

    try:
        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        print("AI RESPONSE RECEIVED")
        return response.choices[0].message.content

    except Exception as e:
        print("AI ERROR:", e)
        return None

# ---------- TELEGRAM ----------
def send_message(text, image=None):
    text = re.sub(r'<img.*?>', '', text)

    if image:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        data = {
            "chat_id": CHAT_ID,
            "caption": text,
            "parse_mode": "HTML",
            "photo": image
        }
    else:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }

    r = requests.post(url, data=data)
    print("TELEGRAM:", r.status_code)

# ---------- MAIN ----------
for feed_url in RSS_FEEDS:
    print("CHECKING:", feed_url)

    feed = feedparser.parse(feed_url)

    for entry in feed.entries[:3]:
        title = clean_text(entry.title)
        summary = clean_text(entry.summary)

        if title in posted_titles:
            continue

        image = get_image(entry)

        ai_text = ai_format_news(title, summary)

        if ai_text:
            final_text = ai_text + "\n\n— Global Finance Desk"
        else:
            final_text = f"<b>{title}</b>\n\n{summary[:200]}..."

        send_message(final_text, image)
        posted_titles.add(title)

print("RUN COMPLETED")
