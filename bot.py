import os
import requests
import feedparser
import datetime
import re
import html

# ---------------- ENV ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GROQ_KEY = os.getenv("GROQ_KEY")

print("BOT STARTED:", datetime.datetime.now())
print("GROQ KEY LOADED:", bool(GROQ_KEY))

RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.reuters.com/reuters/businessNews"
    "https://www.moneycontrol.com/rss/business.xml",
 "https://feeds.reuters.com/reuters/businessNews",
 "https://www.moneycontrol.com/rss/economy.xml",
 "https://www.livemint.com/rss/economy"
    
]

# ---------------- CLEAN HTML ----------------
def clean_html(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub('<.*?>', '', text)
    return text.strip()

# ---------------- TELEGRAM SEND ----------------
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    r = requests.post(url, json=payload)
    print("TELEGRAM:", r.status_code)

# ---------------- GROQ AI ----------------
def ai_format(title, content):

    if not GROQ_KEY:
        print("NO GROQ KEY - USING FALLBACK")
        return None

    print("AI CALLED")

    prompt = f"""
Rewrite this business news professionally.

FORMAT STRICT:
Headline
2 line intro
4 bullet key takeaways
Bottom Line

No links. Simple English.

Title: {title}
Content: {content}
"""

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=25
        )

        if r.status_code == 200:
            result = r.json()
            return result["choices"][0]["message"]["content"]
        else:
            print("AI FAILED:", r.text)
            return None

    except Exception as e:
        print("AI EXCEPTION:", e)
        return None

# ---------------- FALLBACK FORMAT ----------------
def fallback_format(title, summary):

    sentences = re.split(r'[.!?]', summary)
    bullets = []

    for s in sentences[1:]:
        if len(s) > 40:
            bullets.append(f"• {' '.join(s.split()[:15])}...")
        if len(bullets) == 4:
            break

    bottom = sentences[-2] if len(sentences) > 2 else sentences[0]

    return f"""
<b>{title}</b>

{summary[:180]}...

{chr(10).join(bullets)}

<b>Bottom Line:</b>
{bottom[:120]}...

— Global Finance Desk
"""

# ---------------- PROCESS FEED ----------------
def process_feed(url):
    print("CHECKING:", url)
    feed = feedparser.parse(url)

    if not feed.entries:
        print("NO ENTRIES")
        return

    for entry in feed.entries[:15]:

        title = clean_html(entry.title)
        summary = clean_html(entry.summary)

        ai_text = ai_format(title, summary)

        if ai_text:
            final_text = ai_text + "\n\n— Global Finance Desk"
        else:
            final_text = fallback_format(title, summary)

        send_telegram(final_text)

# ---------------- MAIN ----------------
def main():
    for feed in RSS_FEEDS:
        process_feed(feed)

    print("RUN COMPLETED")

if __name__ == "__main__":
    main()
