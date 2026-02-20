import os
import requests
import feedparser
import datetime
import re
import html
import hashlib

# ---------------- ENV ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GROQ_KEY = os.getenv("GROQ_KEY")

POSTED_FILE = "posted_news.txt"

# ---------------- LOAD/SAVE ----------------
def load_posted():
    if not os.path.exists(POSTED_FILE):
        return set()
    with open(POSTED_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

def save_posted(news_id):
    with open(POSTED_FILE, "a") as f:
        f.write(news_id + "\n")

posted_news = load_posted()
posted_titles_session = []

# ---------------- RSS ----------------
RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.moneycontrol.com/rss/economy.xml",
    "https://www.livemint.com/rss/economy"
]

# ---------------- CLEAN ----------------
def clean_html(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub('<.*?>', '', text)
    return text.strip()

# ---------------- CATEGORY DETECTION ----------------
def detect_category(title):
    t = title.lower()

    if any(word in t for word in ["sensex","nifty","stocks","shares","market","ipo"]):
        return "📊 Markets"
    if any(word in t for word in ["rbi","policy","government","budget","sebi","ministry"]):
        return "🏛 Policy"
    if any(word in t for word in ["india","delhi","mumbai"]):
        return "🇮🇳 India"
    if any(word in t for word in ["china","us","europe","global","world"]):
        return "🌍 Global"
    return "🏢 Corporate"

# ---------------- INDIA PRIORITY ----------------
def india_priority(title):
    keywords = ["india","rbi","sebi","delhi","govt","nifty","sensex","finance ministry"]
    return any(word in title.lower() for word in keywords)

# ---------------- TOPIC CLUSTER FILTER ----------------
def is_similar(title):
    title_words = set(title.lower().split())

    for old in posted_titles_session:
        old_words = set(old.lower().split())
        overlap = title_words.intersection(old_words)
        if len(overlap) >= 4:
            return True
    return False

# ---------------- TELEGRAM ----------------
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)

# ---------------- AI FORMAT ----------------
def ai_format(title, content):

    if not GROQ_KEY:
        return None

    prompt = f"""
Rewrite this business news professionally.

STRICT FORMAT (HTML TAGS):
<b>Headline</b>

2 line intro

• Bullet
• Bullet
• Bullet
• Bullet

<b>Bottom Line:</b>
1 line summary

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
            return r.json()["choices"][0]["message"]["content"]
    except:
        pass

    return None

# ---------------- FALLBACK ----------------
def fallback_format(title, summary):
    intro = summary[:160] + "..."
    return f"""
<b>{title}</b>

{intro}

<b>Bottom Line:</b>
Key developments to watch.

— Global Finance Desk
"""

# ---------------- ID ----------------
def generate_id(title):
    return hashlib.md5(title.encode()).hexdigest()

# ---------------- PROCESS ----------------
def process_feed(url):
    feed = feedparser.parse(url)
    items = []

    for entry in feed.entries[:10]:
        title = clean_html(entry.title)
        summary = clean_html(entry.summary)
        items.append((title, summary))

    # 🇮🇳 India priority sorting
    items.sort(key=lambda x: india_priority(x[0]), reverse=True)

    for title, summary in items:

        news_id = generate_id(title)

        if news_id in posted_news:
            continue

        if is_similar(title):
            continue

        category = detect_category(title)

        ai_text = ai_format(title, summary)
        if ai_text:
            final = f"{category}\n\n{ai_text}\n\n— Global Finance Desk"
        else:
            formatted = fallback_format(title, summary)
            final = f"{category}\n\n{formatted}"

        send_telegram(final)

        save_posted(news_id)
        posted_news.add(news_id)
        posted_titles_session.append(title)

# ---------------- MAIN ----------------
def main():
    for feed in RSS_FEEDS:
        process_feed(feed)

if __name__ == "__main__":
    main()
