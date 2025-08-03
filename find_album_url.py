#!/usr/bin/env python3
"""
Script untuk mencari URL album yang benar dari episode URL
"""

import requests
import json
from bs4 import BeautifulSoup
import urllib3
import re

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def find_album_url(episode_url):
    """Cari URL album dari episode URL"""
    print(f"🔍 Mencari URL album dari: {episode_url}")
    
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(episode_url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
        
        if not script_tag:
            print("❌ No __NEXT_DATA__ found")
            return None
        
        player_data = json.loads(script_tag.string)
        props = player_data.get('props', {})
        initial_state = props.get('initialState', {})
        play = initial_state.get('play', {})
        album_info = play.get('albumInfo', {})
        
        album_id = album_info.get('albumId')
        album_name = album_info.get('name', '')
        total_episodes = album_info.get('total', 0)
        
        print(f"📋 Album Info:")
        print(f"  ID: {album_id}")
        print(f"  Name: {album_name}")
        print(f"  Total Episodes: {total_episodes}")
        
        if not album_id:
            print("❌ No album ID found")
            return None
        
        # Coba berbagai format URL album
        possible_urls = [
            f"https://www.iq.com/album/{album_id}",
            f"https://www.iq.com/play/{album_id}",
            f"https://www.iq.com/album/lazarus-{album_id}",
            # Coba ekstrak nama series dari URL asli
        ]
        
        # Extract series name dari URL
        url_match = re.search(r'/play/([^-]+)', episode_url)
        if url_match:
            series_name = url_match.group(1)
            possible_urls.extend([
                f"https://www.iq.com/album/{series_name}",
                f"https://www.iq.com/play/{series_name}",
                f"https://www.iq.com/album/{series_name}-{album_id}",
            ])
        
        print(f"\n🧪 Testing possible album URLs:")
        
        for url in possible_urls:
            print(f"  Testing: {url}")
            if test_album_url(url, headers):
                print(f"  ✅ Working URL found: {url}")
                return url
            else:
                print(f"  ❌ Not working")
        
        # Coba cari link album di halaman HTML
        album_links = soup.find_all('a', href=True)
        for link in album_links:
            href = link.get('href', '')
            if '/album/' in href and str(album_id) in href:
                full_url = f"https://www.iq.com{href}" if href.startswith('/') else href
                print(f"  Found album link in HTML: {full_url}")
                if test_album_url(full_url, headers):
                    print(f"  ✅ Working URL found: {full_url}")
                    return full_url
        
        print("❌ No working album URL found")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_album_url(url, headers):
    """Test apakah URL album menghasilkan episode list"""
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        if response.status_code != 200:
            return False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
        
        if not script_tag:
            return False
        
        player_data = json.loads(script_tag.string)
        props = player_data.get('props', {})
        initial_state = props.get('initialState', {})
        play = initial_state.get('play', {})
        
        # Check if this has episode data
        avlist = play.get('avlist', [])
        cache_playlist = play.get('cachePlayList', {})
        
        has_episodes = len(avlist) > 0 or bool(cache_playlist.get('1', []))
        
        if has_episodes:
            print(f"    ✅ Found {len(avlist)} episodes in avlist")
            if cache_playlist.get('1'):
                print(f"    ✅ Found {len(cache_playlist.get('1', []))} episodes in cachePlayList")
        
        return has_episodes
        
    except Exception as e:
        print(f"    ❌ Test error: {e}")
        return False

if __name__ == "__main__":
    episode_url = "https://www.iq.com/play/lazarus-episode-1-1l0n170m0qc?lang=en_us"
    album_url = find_album_url(episode_url)
    
    if album_url:
        print(f"\n✅ Final Result: {album_url}")
    else:
        print(f"\n❌ Could not find working album URL")