import os
import re
import html
import requests
import feedparser
import openai
from bs4 import BeautifulSoup

# ---------------- ENV ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
AI_KEY = os.getenv("AI_KEY")

openai.api_key = AI_KEY
openai.base_url = "https://openrouter.ai/api/v1"

# ---------------- RSS FEEDS ----------------
RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.reuters.com/reuters/businessNews"
]

# ---------------- KEYWORDS ----------------
KEYWORDS = [
    "india", "sensex", "nifty", "gdp", "inflation",
    "china", "trump", "imf", "world bank",
    "interest rate", "stock", "economy", "rupee"
]

posted_titles = set()

# ---------------- TEXT CLEAN ----------------
def clean_text(text):
    return html.unescape(text).replace("\n", " ").strip()

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

# ---------------- AI FORMAT ----------------
def ai_format_news(title, summary):
    prompt = f"""
Rewrite this financial news professionally.

Rules:
- Do NOT repeat headline
- 2 line intro
- 4 bullet key takeaways
- Bottom Line
- Simple English
- No links
- Bullets must be unique facts

Title: {title}
Summary: {summary}
"""

    try:
        response = openai.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content
    except:
        return None

# ---------------- FALLBACK FORMAT ----------------
def fallback_format(title, summary):
    sentences = [s.strip() for s in re.split(r'[.!?]', summary) if len(s.strip()) > 30]

    if not sentences:
        sentences = [summary]

    intro = sentences[0][:200]
    bullets = []

    for s in sentences[1:5]:
        bullets.append(f"⚫ {s[:140]}")

    bottom = sentences[-1][:150]

    return f"""
<b>{title}</b>

{intro}...

{chr(10).join(bullets)}

<b>Bottom Line:</b>
{bottom}

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

        requests.post(url, data=data, timeout=15)
    except:
        pass

# ---------------- KEYWORD FILTER ----------------
def is_relevant(text):
    text = text.lower()
    return any(k in text for k in KEYWORDS)

# ---------------- MAIN LOOP ----------------
for feed_url in RSS_FEEDS:
    feed = feedparser.parse(feed_url)

    for entry in feed.entries[:5]:
        raw_title = entry.title
        raw_summary = BeautifulSoup(entry.summary, "html.parser").text

        title = clean_text(raw_title)
        summary = clean_text(raw_summary)

         if title in posted_titles:
            continue

         if not is_relevant(title + summary):
            continue

        image = get_image(entry)

        ai_text = ai_format_news(title, summary)

        if ai_text and "Bottom" in ai_text:
            final_text = ai_text + "\n\n— Global Finance Desk"
        else:
            final_text = fallback_format(title, summary)

        send_message(final_text, image)
        posted_titles.add(title)
