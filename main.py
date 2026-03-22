import instaloader
import json
import os
from datetime import datetime
import requests

# Configuration
USERNAMES_TO_TRACK = ['salemland_promotors']
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
STATE_FILE = 'last_posts.json'

def load_state():
    """Load the last checked post IDs"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    """Save the current post IDs"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

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
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def check_new_posts():
    """Check for new posts from tracked users"""
    L = instaloader.Instaloader()
    
    # Load previous state
    state = load_state()
    new_posts_found = False
    
    for username in USERNAMES_TO_TRACK:
        try:
            print(f"Checking {username}...")
            profile = instaloader.Profile.from_username(L.context, username)
            
            # Get the most recent post
            posts = profile.get_posts()
            latest_post = next(posts, None)
            
            if not latest_post:
                continue
            
            latest_post_id = latest_post.shortcode
            last_known_id = state.get(username)
            
            # Check if this is a new post
            if last_known_id != latest_post_id:
                new_posts_found = True
                post_url = f"https://www.instagram.com/p/{latest_post_id}/"
                
                message = f"""
🔔 <b>New post from @{username}</b>

📅 {latest_post.date_local.strftime('%Y-%m-%d %I:%M %p')}
❤️ {latest_post.likes} likes
💬 {latest_post.comments} comments

{post_url}
                """.strip()
                
                send_telegram_message(message)
                
                # Update state
                state[username] = latest_post_id
                print(f"New post found for {username}")
            else:
                print(f"No new posts for {username}")
                
        except Exception as e:
            print(f"Error checking {username}: {e}")
            continue
    
    # Save updated state
    save_state(state)
    
    if not new_posts_found:
        print("No new posts from any tracked users")

if __name__ == "__main__":
    check_new_posts()