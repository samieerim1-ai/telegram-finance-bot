import os
import requests
import feedparser
from openai import OpenAI

# =========================
# ENV VARIABLES
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
AI_KEY = os.getenv("AI_KEY")

# =========================
# OPENROUTER CLIENT
# =========================
client = OpenAI(
    api_key=AI_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# =========================
# KEYWORDS (RELAXED)
# =========================
KEYWORDS = [
    "profit","revenue","dividend","q4","q3",
    "results","net","share","earnings",
    "stock","company","growth","decline"
]

def is_relevant(text):
    text = text.lower()
    return any(k in text for k in KEYWORDS)

# =========================
# AI FORMAT FUNCTION
# =========================
def format_news(title, summary):
    try:
        print("AI CALLED")

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"""
Format this business news cleanly:

Title: {title}
Summary: {summary}

Return:
Headline
• Bullet 1
• Bullet 2
Bottom Line
"""
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("AI ERROR:", e)
        return f"{title}\n{summary}"

# =========================
# TELEGRAM SEND
# =========================
def send_telegram(text):
    try:
        print("SENDING TELEGRAM")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": text
        }
        requests.post(url, data=data)
    except Exception as e:
        print("TELEGRAM ERROR:", e)

# =========================
# RSS SOURCES
# =========================
RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.reuters.com/reuters/businessNews"
]

# =========================
# MAIN BOT
# =========================
def run_bot():
    for feed_url in RSS_FEEDS:
        print("CHECKING:", feed_url)

        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:3]:  # only 3 news per feed
            title = entry.title
            summary = entry.summary

            print("TITLE:", title)
            print("SUMMARY:", summary[:120])

            # DEBUG MODE — COMMENT THIS TO FORCE SEND
            # if not is_relevant(title + summary):
            #     print("SKIPPED: Not Relevant")
            #     continue

            formatted = format_news(title, summary)
            send_telegram(formatted)

    print("RUN COMPLETED")


# =========================
# START
# =========================
if __name__ == "__main__":
    run_bot()
