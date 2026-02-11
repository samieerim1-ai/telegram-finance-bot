import os
import re
import requests
import feedparser
import openai
from bs4 import BeautifulSoup
import html

# ---------------- ENV ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
AI_KEY = os.getenv("AI_KEY")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN or CHAT_ID missing")

if not AI_KEY:
    raise ValueError("AI_KEY not found in Secrets")

# ---------------- OPENROUTER SETUP ----------------
openai.api_key = AI_KEY
openai.base_url = "https://openrouter.ai/api/v1"

print("AI KEY LOADED:", AI_KEY[:8])

# ---------------- RSS ----------------
RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.reuters.com/reuters/businessNews"
]

KEYWORDS = [
    "india", "sensex", "nifty", "gdp", "inflation",
    "stock", "shares", "market", "economy"
]

posted_titles = set()

# ---------------- IMAGE PICKUP ----------------
def get_image(entry):
    if "media_content" in entry:
        return entry.media_content[0]['url']

    soup = BeautifulSoup(entry.get("summary", ""), "html.parser")
    img = soup.find("img")
    return img['src'] if img else None


# ---------------- TEXT CLEAN ----------------
def clean_text(text):
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ---------------- AI FORMAT ----------------
def ai_format_news(title, summary):
    prompt = f"""
You are a professional financial news editor.

Rewrite this news in SIMPLE ENGLISH.

Format EXACTLY like this:

Headline

2 line introduction

• Point 1  
• Point 2  
• Point 3  
• Point 4  

Bottom Line: 1 sentence summary.

No links. No repeating headline. No extra commentary.

Title: {title}
Summary: {summary}
"""

    try:
        response = openai.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400
        )

        text = response.choices[0].message.content.strip()
        return text

    except Exception as e:
        print("AI ERROR:", e)
        return None


# ---------------- FALLBACK FORMAT ----------------
def fallback_format(title, summary):
    sentences = re.split(r'[.!?]', summary)
    bullets = []

    for s in sentences[1:]:
        if len(s) > 40:
            bullets.append(f"• {' '.join(s.split()[:12])}...")
        if len(bullets) == 4:
            break

    if not bullets:
        bullets.append("• Key details emerging...")

    bottom = sentences[-2] if len(sentences) > 2 else sentences[0]

    return f"""
<b>{title}</b>

{summary[:180]}...

{chr(10).join(bullets)}

<b>Bottom Line:</b> {bottom[:120]}...

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
print("BOT STARTED")

for feed_url in RSS_FEEDS:
    print("Fetching:", feed_url)
    feed = feedparser.parse(feed_url)

    for entry in feed.entries[:5]:
        title = clean_text(entry.title)
        summary = clean_text(BeautifulSoup(entry.summary, "html.parser").text)

        print("Processing:", title)

        if title in posted_titles:
            continue

        # OPTIONAL FILTER — COMMENT IF YOU WANT ALL NEWS
        # if not is_relevant(title + summary):
        #     continue

        image = get_image(entry)

        ai_text = ai_format_news(title, summary)

        if ai_text:
            final_text = ai_text + "\n\n— Global Finance Desk"
        else:
            final_text = fallback_format(title, summary)

        send_message(final_text, image)
        posted_titles.add(title)

print("BOT FINISHED")
