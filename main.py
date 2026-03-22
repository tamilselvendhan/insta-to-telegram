import os
import requests
import json
from datetime import datetime, timedelta
import re

# Configuration
USERNAMES_TO_TRACK = ['salemland_promoters']
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
CHECK_HOURS = 12
STATE_FILE = 'last_posts.json'

def send_telegram_message(message):
    """Send notification via Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print("Telegram message sent successfully")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def load_state():
    """Load the last checked post shortcodes"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    """Save the current post shortcodes"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_instagram_posts(username):
    """Scrape Instagram profile page directly"""
    url = f"https://www.instagram.com/{username}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        print(f"Fetching {url}...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Extract JSON data from page
        pattern = r'<script type="application/ld\+json">({.*?})</script>'
        matches = re.findall(pattern, response.text, re.DOTALL)
        
        posts = []
        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict) and '@type' in data:
                    # Look for post data
                    if 'articleBody' in data or 'image' in data:
                        posts.append(data)
            except:
                continue
        
        # Also try to extract shortcodes from the page
        shortcode_pattern = r'"/p/([A-Za-z0-9_-]+)/"'
        shortcodes = re.findall(shortcode_pattern, response.text)
        
        # Remove duplicates and get first 3
        unique_shortcodes = list(dict.fromkeys(shortcodes))[:3]
        
        return unique_shortcodes
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Instagram page: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def check_new_posts():
    """Check for new posts from tracked users"""
    state = load_state()
    new_posts_found = False
    
    for username in USERNAMES_TO_TRACK:
        print(f"\nChecking {username}...")
        
        shortcodes = get_instagram_posts(username)
        
        if not shortcodes:
            print(f"Could not fetch posts for {username}")
            continue
        
        print(f"Found {len(shortcodes)} posts")
        
        # Get the last known shortcode for this user
        last_known = state.get(username)
        
        # Check if there are new posts
        if not last_known:
            # First time checking this user
            print(f"First time checking {username}, saving latest post")
            state[username] = shortcodes[0]
            new_posts_found = True
            latest_shortcode = shortcodes[0]
        elif shortcodes[0] != last_known:
            # New post detected
            print(f"New post detected for {username}!")
            new_posts_found = True
            latest_shortcode = shortcodes[0]
            state[username] = latest_shortcode
        else:
            print(f"No new posts for {username}")
            continue
        
        # Send notification
        post_url = f"https://www.instagram.com/p/{latest_shortcode}/"
        
        message = f"""
🔔 <b>New post from @{username}</b>

{post_url}

Tap to view on Instagram
        """.strip()
        
        send_telegram_message(message)
    
    # Save updated state
    save_state(state)
    
    if not new_posts_found:
        print("\nNo new posts from any tracked users")
    else:
        print("\n✓ Notifications sent!")

if __name__ == "__main__":
    print("=" * 50)
    print("Instagram Monitor Starting...")
    print("=" * 50)
    check_new_posts()
    print("=" * 50)
    print("Done!")