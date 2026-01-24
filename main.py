import feedparser
import requests
from datetime import datetime, time
import time as time_module
import json
import os
from urllib.parse import quote

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

INSTAGRAM_RSS_FEEDS = [
    "https://rss.app/feeds/RCz4LIiPWuaMlcLg.xml"
]

STATE_FILE = "insta_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in environment")
        return
    
    try:
        encoded_text = quote(text)
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        params = {
            "chat_id": CHAT_ID,
            "text": encoded_text,
            "disable_web_page_preview": True,
        }
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print(f"✅ Telegram: {text[:50]}...")
            else:
                print(f"❌ Telegram error: {result}")
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Telegram send failed: {e}")

def process_feed(feed_url):
    state = load_state()
    last_seen_id = state.get(feed_url)

    # Use a real browser-like User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(feed_url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code} from {feed_url}")
            return
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"❌ Error fetching/parsing feed: {e}")
        return

    if not feed.entries:
        print("❌ No entries in feed")
        return

    new_items = []
    for entry in feed.entries:
        try:
            # Use link as primary ID, fallback to guid, then a timestamp-based ID
            entry_id = entry.get('published')
            published_parsed = entry.get("published_parsed")
            if published_parsed is None:
                continue
            entry_timestamp = time_module.mktime(published_parsed)

            # If we already saw this post, stop here (no need to go back)
            if last_seen_id is not None and entry_timestamp == last_seen_id:
                break

            # Otherwise, it's new
            new_items.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry_timestamp,
                "id": entry_id
            })

        except Exception as e:
            print(f"⚠️ Error processing entry: {e}")
            continue

    # Sort by time (newest first)
    new_items.sort(key=lambda x: x["published"], reverse=True)

    # Send new posts
    for item in new_items:
        if item["link"]:
            msg = f"New Instagram post:\n{item['link']}"
            # send_telegram_message(msg)
            print("Sending telegram message")

    # Save the newest post's ID as last seen
    # if new_items:
    #     state[feed_id] = new_items["id"]
    #     save_state(state)
    if new_items:
        latest_time = max(item["published"] for item in new_items)
        state[feed_url] = latest_time
        save_state(state)

def main():
    print("🚀 Instagram → Telegram monitor starting...")
    
    current_dir = os.getcwd()
    print(f"📁 Current directory: {current_dir}")
    print(f"🗄️ Files in this directory: {os.listdir(current_dir)}")
    
    state_file = "insta_state.json"
    if os.path.exists(state_file):
        print(f"🟢 Found {state_file}")
        with open(state_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            print(f"📄 {state_file} content:")
            print(content)
    else:
        print(f"🟡 {state_file} not found (will be created)")
        
    for feed_url in INSTAGRAM_RSS_FEEDS:
        print(f"🔍 Checking feed: {feed_url}")
        try:
            process_feed(feed_url)
        except Exception as e:
            print(f"❌ Error checking feed '{feed_url}': {e}")

if __name__ == "__main__":
    main()
