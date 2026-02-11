import os
import requests
import feedparser
from datetime import datetime
import re
import html

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
AI_KEY = os.getenv("AI_KEY")

RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.reuters.com/reuters/businessNews"
]

# =============== UTILITIES =================

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)  # remove tags
    text = html.unescape(text)           # decode html
    return text.strip()


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    r = requests.post(url, json=payload)
    print("TELEGRAM:", r.status_code)
    if r.status_code != 200:
        print("TELEGRAM ERROR:", r.text)


# =============== AI SUMMARY =================

def ai_summarize(title, description):
    try:
        print("AI CALLED")

        headers = {
            "Authorization": f"Bearer {AI_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""
Summarize this business news in 3 short bullet points.
No links. Simple English.

Title: {title}
Description: {description}
"""

        data = {
           MODELS = [
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-2-9b-it:free"
]
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        if r.status_code != 200:
            print("AI ERROR:", r.text)
            return None

        result = r.json()
        summary = result["choices"][0]["message"]["content"]
        print("AI SUCCESS")
        return summary.strip()

    except Exception as e:
        print("AI EXCEPTION:", e)
        return None


# =============== MAIN BOT =================

def run_bot():
    print("BOT STARTED:", datetime.now())

    for feed_url in RSS_FEEDS:
        print("CHECKING:", feed_url)
        feed = feedparser.parse(feed_url)

        if not feed.entries:
            print("NO ENTRIES FOUND")
            continue

        for entry in feed.entries[:3]:  # send top 3 only
            title = clean_html(entry.get("title", ""))
            description = clean_html(entry.get("summary", ""))

            ai_text = ai_summarize(title, description)

            if ai_text:
                message = f"<b>{title}</b>\n\n{ai_text}"
            else:
                message = f"<b>{title}</b>\n\n{description[:200]}..."

            send_telegram(message)

    print("RUN COMPLETED")


# =============== RUN =================

if __name__ == "__main__":
    run_bot()
