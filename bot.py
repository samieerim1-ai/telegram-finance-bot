import os
import requests
import feedparser
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"
]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def get_news():
    all_news = []

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:2]:  # take 2 from each feed
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")

            text = f"📰 <b>{title}</b>\n\n{summary}\n\nRead more: {link}"
            all_news.append(text)

    return all_news

def main():
    print("BOT STARTED")

    if not BOT_TOKEN or not CHAT_ID:
        print("TOKEN OR CHAT ID MISSING")
        return

    news_list = get_news()

    if not news_list:
        send_telegram("No news found.")
        return

    for news in news_list[:5]:  # send max 5 messages
        send_telegram(news)

if __name__ == "__main__":
    main()
