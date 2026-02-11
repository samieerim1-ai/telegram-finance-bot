import os
import requests
import feedparser
import datetime
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
AI_KEY = os.getenv("AI_KEY")

RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.reuters.com/reuters/businessNews"
]

MODELS = [
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-2-9b-it:free"
]

def clean_html(text):
    if not text:
        return ""
    text = re.sub('<.*?>', '', text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&#39;", "'")
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

def ai_summarize(title, content):
    if not AI_KEY:
        return None

    prompt = f"""
Summarize this business news in 3 bullet points and one bottom line.
No links. No markdown. Simple English.

Title: {title}
Content: {content}
"""

    headers = {
        "Authorization": f"Bearer {AI_KEY}",
        "Content-Type": "application/json"
    }

    for model in MODELS:
        print("Trying model:", model)

        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=20
            )

            if r.status_code == 200:
                result = r.json()
                return result["choices"][0]["message"]["content"]

            else:
                print("MODEL FAILED:", r.text)

        except Exception as e:
            print("AI EXCEPTION:", e)

    return None

def format_message(title, summary):
    if not summary:
        return f"<b>{title}</b>"

    return f"<b>{title}</b>\n\n{summary}\n\n— Global Finance Desk"

def process_feed(url):
    print("CHECKING:", url)
    feed = feedparser.parse(url)

    if not feed.entries:
        print("NO ENTRIES FOUND")
        return

    for entry in feed.entries[:3]:
        title = clean_html(entry.title)
        content = clean_html(entry.summary)

        print("AI CALLED")
        summary = ai_summarize(title, content)

        message = format_message(title, summary)
        send_telegram(message)

def main():
    print("BOT STARTED:", datetime.datetime.now())

    for feed in RSS_FEEDS:
        process_feed(feed)

    print("RUN COMPLETED")

if __name__ == "__main__":
    main()
