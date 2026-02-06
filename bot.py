import os
import re
import requests
import feedparser
import openai
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
AI_KEY = os.getenv("AI_KEY")

openai.api_key = AI_KEY
openai.base_url = "https://openrouter.ai/api/v1"

RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://feeds.reuters.com/reuters/businessNews"
]

KEYWORDS = [
    "india", "sensex", "nifty", "gdp", "inflation",
    "china", "trump", "imf", "world bank",
    "interest rate", "stock", "economy"
]

posted_titles = set()


# ---------------- IMAGE PICKUP ----------------
def get_image(entry):
    if "media_content" in entry:
        return entry.media_content[0]['url']

    soup = BeautifulSoup(entry.get("summary", ""), "html.parser")
    img = soup.find("img")
    return img['src'] if img else None


# ---------------- AI FORMAT ----------------
def ai_format_news(title, summary):
    prompt = f"""
Rewrite this financial news professionally.

Format:
Headline
2 line intro
4 bullet key takeaways
Bottom Line

Simple English. No links.

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
    sentences = re.split(r'[.!?]', summary)
    bullets = []

    for s in sentences[1:]:
        if len(s) > 40:
            bullets.append(f"⚫ {' '.join(s.split()[:16])}...")
        if len(bullets) == 4:
            break

    bottom = sentences[-2] if len(sentences) > 2 else sentences[0]

    return f"""
<b>{title}</b>

{summary[:200]}...

{chr(10).join(bullets)}

<b>Bottom Line:</b>
{bottom[:120]}...

— Global Finance Desk
"""


# ---------------- TELEGRAM SEND ----------------
def send_message(text, image=None):
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


# ---------------- KEYWORD FILTER ----------------
def is_relevant(text):
    text = text.lower()
    return any(k in text for k in KEYWORDS)


# ---------------- MAIN LOOP ----------------
for feed_url in RSS_FEEDS:
    feed = feedparser.parse(feed_url)

    for entry in feed.entries[:5]:
        title = entry.title
        summary = BeautifulSoup(entry.summary, "html.parser").text

        if title in posted_titles:
            continue

       # if not is_relevant(title + summary):
            # continue

        image = get_image(entry)

        ai_text = ai_format_news(title, summary)

        if ai_text:
            final_text = ai_text + "\n\n— Global Finance Desk"
        else:
            final_text = fallback_format(title, summary)

        send_message(final_text, image)
        posted_titles.add(title)

