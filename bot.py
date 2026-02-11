import os
import requests
import feedparser
import re
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
AI_KEY = os.getenv("AI_KEY")

RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml"
]

# ---------- CLEAN HTML ----------
def clean_html(text):
    if not text:
        return ""
    text = re.sub('<.*?>', '', text)  # remove tags
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("#39;", "'")
    return text.strip()

# ---------- AI FORMAT ----------
def ai_format(title, summary):
    prompt = f"""
Format this Indian stock/business news professionally.

Rules:
- Do NOT repeat headline.
- 2 bullet points only.
- Short Bottom Line.
- No links.
- Clean English.
- Max 5 lines.

Title: {title}
Summary: {summary}
"""

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {AI_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        result = r.json()
        content = result["choices"][0]["message"]["content"]
        return content
    except Exception as e:
        print("AI ERROR:", e)
        return summary[:200]

# ---------- TELEGRAM ----------
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    r = requests.post(url, json=payload)
    print("TELEGRAM:", r.status_code)

# ---------- MAIN ----------
def run_bot():
    print("BOT STARTED:", datetime.now())

    for feed_url in RSS_FEEDS:
        print("CHECKING:", feed_url)
        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:3]:
            title = clean_html(entry.title)
            summary = clean_html(entry.summary)

            print("TITLE:", title)

            ai_text = ai_format(title, summary)

            message = f"""
<b>{title}</b>

{ai_text}

— Global Finance Desk
"""

            send_telegram(message)

    print("RUN COMPLETED")

# ---------- RUN ----------
if __name__ == "__main__":
    run_bot()
