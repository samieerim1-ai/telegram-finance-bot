import os
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from openai import OpenAI
import html

# ---------------- ENV VARIABLES ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
AI_KEY = os.getenv("AI_KEY")

if not AI_KEY:
    raise ValueError("AI_KEY NOT FOUND")

# ---------------- OPENROUTER CLIENT ----------------
client = OpenAI(
    api_key=AI_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# ---------------- RSS FEEDS ----------------
RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.reuters.com/reuters/businessNews"
]

# ---------------- KEYWORDS ----------------
KEYWORDS = [
    "india", "sensex", "nifty", "gdp", "inflation",
    "china", "trump", "imf", "world bank",
    "interest rate", "stock", "economy"
]

posted_titles = set()

# ---------------- IMAGE PICKUP ----------------
def get_image(entry):
    try:
        if "media_content" in entry:
            return entry.media_content[0]['url']

        soup = BeautifulSoup(entry.get("summary", ""), "html.parser")
        img = soup.find("img")
        return img['src'] if img else None
    except:
        return None

# ---------------- CLEAN TEXT ----------------
def clean_text(text):
    text = html.unescape(text)
    return BeautifulSoup(text, "html.parser").text.strip()

# ---------------- AI FORMAT ----------------
def ai_format_news(title, summary):
    try:
        print("AI CALLED")

        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[
                {
                    "role": "user",
                    "content": f"""
Rewrite this financial news professionally.

FORMAT STRICTLY:

Headline

2 line introduction

⚫ Bullet 1
⚫ Bullet 2
⚫ Bullet 3
⚫ Bullet 4

Bottom Line: one strong closing sentence.

Simple English. No links. No repetition.

Title: {title}
Summary: {summary}
"""
                }
            ],
            temperature=0.3,
            max_tokens=350
        )

        return response.choices[0].message.content

    except Exception as e:
        print("AI FAILED:", e)
        return None

# ---------------- FALLBACK FORMAT ----------------
def fallback_format(title, summary):
    sentences = re.split(r'[.!?]', summary)
    bullets = []

    for s in sentences[1:]:
        s = s.strip()
        if len(s) > 40:
            bullets.append(f"⚫ {s[:120]}...")
        if len(bullets) == 4:
            break

    bottom = sentences[-2] if len(sentences) > 2 else sentences[0]

    return f"""
<b>{title}</b>

{summary[:200]}...

{chr(10).join(bullets)}

<b>Bottom Line:</b>
{bottom[:150]}...

— Global Finance Desk
"""

# ---------------- TELEGRAM SEND ----------------
def send_message(text, image=None):
    try:
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

        requests.post(url, data=data)
    except Exception as e:
        print("TELEGRAM ERROR:", e)

# ---------------- KEYWORD FILTER ----------------
def is_relevant(text):
    text = text.lower()
    return any(k in text for k in KEYWORDS)

# ---------------- MAIN LOOP ----------------
for feed_url in RSS_FEEDS:
    print("CHECKING:", feed_url)
    feed = feedparser.parse(feed_url)

    for entry in feed.entries[:5]:
        title = clean_text(entry.title)
        summary = clean_text(entry.summary)

        if title in posted_titles:
            continue

        if not is_relevant(title + summary):
            continue

        image = get_image(entry)

        ai_text = ai_format_news(title, summary)

        if ai_text:
            final_text = ai_text + "\n\n— Global Finance Desk"
        else:
            final_text = fallback_format(title, summary)

        send_message(final_text, image)
        posted_titles.add(title)

print("RUN COMPLETED")
