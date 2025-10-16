#!/usr/bin/env python3
"""
Auto-update cookies.txt from cnvmp3.com
Fetches fresh YouTube cookies to avoid bot detection
"""

import requests
import os
import hashlib
from datetime import datetime

COOKIES_URL = 'https://cnvmp3.com/cookies.txt'
COOKIES_FILE = 'cookies.txt'

def get_file_hash(filepath):
    """Get MD5 hash of file contents"""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def update_cookies():
    """Fetch and update cookies.txt if changed"""
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for cookie updates from cnvmp3.com...")

        # Get current hash
        old_hash = get_file_hash(COOKIES_FILE)

        # Fetch fresh cookies with browser User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        response = requests.get(COOKIES_URL, headers=headers, timeout=10)
        response.raise_for_status()

        new_content = response.text
        new_hash = hashlib.md5(new_content.encode()).hexdigest()

        # Check if changed
        if old_hash == new_hash:
            print(f"[OK] Cookies are up-to-date (hash: {old_hash[:8]}...)")
            return False

        # Update file
        with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"[UPDATE] Cookies updated successfully!")
        print(f"  Old hash: {old_hash[:8] if old_hash else 'none'}...")
        print(f"  New hash: {new_hash[:8]}...")
        print(f"  Size: {len(new_content)} bytes")
        return True

    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch cookies: {e}")
        if os.path.exists(COOKIES_FILE):
            print(f"[OK] Using existing cookies.txt file")
        else:
            print(f"[WARNING] No cookies.txt file available!")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

if __name__ == '__main__':
    update_cookies()
