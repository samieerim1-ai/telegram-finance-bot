import os
import requests
import feedparser
import datetime
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GROQ_KEY = os.getenv("GROQ_KEY")

RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.reuters.com/reuters/businessNews"
]

def clean_html(text):
    if not text:
        return ""
    text = re.sub('<.*?>', '', text)
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
    if not GROQ_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
Summarize this business news.
Format:
3 bullet points
1 bottom line
Simple English.

Title: {title}
Content: {content}
"""

    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=20
        )

        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]

        print("GROQ ERROR:", r.text)
        return None

    except Exception as e:
        print("GROQ EXCEPTION:", e)
        return None

def process_feed(url):
    print("CHECKING:", url)
    feed = feedparser.parse(url)

    if not feed.entries:
        print("NO ENTRIES")
        return

    for entry in feed.entries[:3]:
        title = clean_html(entry.title)
        content = clean_html(entry.summary)

        print("AI CALLED")
        summary = ai_summarize(title, content)

        if summary:
            message = f"<b>{title}</b>\n\n{summary}\n\n— Global Finance Desk"
        else:
            message = f"<b>{title}</b>\n\n{content[:200]}..."

        send_telegram(message)

def main():
    print("BOT STARTED:", datetime.datetime.now())

    for feed in RSS_FEEDS:
        process_feed(feed)

    print("RUN COMPLETED")

if __name__ == "__main__":
    main()
