import instaloader
import os
from datetime import datetime, timedelta
import requests

# Configuration
USERNAMES_TO_TRACK = ['salemland_promoters']  # Add usernames here
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
CHECK_HOURS = 12  # Only notify if post is less than 12 hours old

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
    
    # Login to Instagram (optional but recommended)
    instagram_username = os.environ.get('INSTAGRAM_USERNAME')
    instagram_password = os.environ.get('INSTAGRAM_PASSWORD')
    
    if instagram_username and instagram_password:
        try:
            L.load_session_from_file(instagram_username)
            print("Loaded session from file")
        except:
            print("Logging in to Instagram...")
            L.login(instagram_username, instagram_password)
            L.save_session_to_file()
            print("Logged in successfully")
    
    new_posts_found = False
    cutoff_time = datetime.now() - timedelta(hours=CHECK_HOURS)
    
    for username in USERNAMES_TO_TRACK:
        try:
            print(f"Checking {username}...")
            profile = instaloader.Profile.from_username(L.context, username)
            
            # Get recent posts (check last 3 to be safe)
            posts = list(profile.get_posts())[:3]
            
            for post in posts:
                # Only notify if post is recent (within CHECK_HOURS)
                if post.date_local > cutoff_time:
                    new_posts_found = True
                    post_url = f"https://www.instagram.com/p/{post.shortcode}/"
                    
                    # Calculate how long ago
                    time_ago = datetime.now() - post.date_local
                    hours_ago = int(time_ago.total_seconds() / 3600)
                    
                    if hours_ago < 1:
                        time_str = f"{int(time_ago.total_seconds() / 60)} minutes ago"
                    else:
                        time_str = f"{hours_ago} hours ago"
                    
                    message = f"""
🔔 <b>New post from @{username}</b>

⏰ Posted {time_str}
❤️ {post.likes} likes
💬 {post.comments} comments

{post_url}
                    """.strip()
                    
                    send_telegram_message(message)
                    print(f"Notified about post from {username} ({time_str})")
                
        except Exception as e:
            print(f"Error checking {username}: {e}")
            continue
    
    if not new_posts_found:
        print(f"No posts in the last {CHECK_HOURS} hours from any tracked users")

if __name__ == "__main__":
    check_new_posts()