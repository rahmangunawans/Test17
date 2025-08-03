#!/usr/bin/env python3
"""
Test IQiyi internal API untuk mendapatkan episode list
"""

import requests
import json
import urllib3
import re

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_iqiyi_api():
    """Test API IQiyi untuk mendapatkan episode list"""
    
    # Album ID yang kita tahu
    album_id = "3813997793733701"
    
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'referer': 'https://www.iq.com/',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
    }
    
    # Berbagai API endpoint yang mungkin
    api_endpoints = [
        f"https://pcw-api.iq.com/api/episodelist/{album_id}",
        f"https://pcw-api.iq.com/episodelist/{album_id}",
        f"https://www.iq.com/api/album/{album_id}/episodes",
        f"https://www.iq.com/api/episodelist/{album_id}",
        f"https://intl-api.iq.com/episodelist/{album_id}",
        f"https://pcw-api.iq.com/api/albuminfo/{album_id}",
    ]
    
    print(f"🧪 Testing IQiyi API endpoints for album {album_id}...")
    
    for endpoint in api_endpoints:
        print(f"\n🔍 Testing: {endpoint}")
        
        try:
            response = requests.get(endpoint, headers=headers, verify=False, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  ✅ JSON Response received")
                    print(f"  Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    
                    # Cari episode data
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, list) and len(value) > 0:
                                print(f"    '{key}' has {len(value)} items")
                                if isinstance(value[0], dict):
                                    print(f"      Sample keys: {list(value[0].keys())}")
                    
                except json.JSONDecodeError:
                    print(f"  📄 Non-JSON response (length: {len(response.text)})")
                    if len(response.text) < 500:
                        print(f"  Content: {response.text[:200]}...")
            else:
                print(f"  ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def try_web_scraping_approach():
    """Coba pendekatan web scraping untuk mendapatkan episode list"""
    
    print(f"\n🕷️ Trying web scraping approach...")
    
    # Test dengan URL album
    album_url = "https://www.iq.com/album/lazarus-2025-12qeocfw755?lang=en_us"
    
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(album_url, headers=headers, verify=False, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Cari episode links di HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Cari semua link yang berisi "episode" atau nomor episode
            episode_links = []
            
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text().strip()
                
                # Cari link episode
                if 'episode' in href.lower() or re.search(r'第\d+集', text) or re.search(r'episode\s*\d+', text.lower()):
                    if href.startswith('/'):
                        href = f"https://www.iq.com{href}"
                    episode_links.append((href, text))
            
            print(f"📺 Found {len(episode_links)} potential episode links:")
            for href, text in episode_links[:10]:  # Show first 10
                print(f"  {href} - {text}")
                
            return episode_links
        
    except Exception as e:
        print(f"❌ Web scraping error: {e}")
        return []

if __name__ == "__main__":
    test_iqiyi_api()
    episode_links = try_web_scraping_approach()