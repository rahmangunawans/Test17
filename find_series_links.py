#!/usr/bin/env python3
"""
Script untuk mencari link series/album di halaman episode
"""

import requests
from bs4 import BeautifulSoup
import urllib3
import re

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def find_series_links(episode_url):
    """Cari semua link yang mungkin mengarah ke album/series"""
    print(f"🔍 Mencari link series di: {episode_url}")
    
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(episode_url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cari semua link yang mungkin relevan
        all_links = soup.find_all('a', href=True)
        
        # Filter link yang mungkin mengarah ke album/series
        potential_links = []
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text().strip()
            
            # Cari link yang mengandung kata kunci album, series, atau lazarus
            if any(keyword in href.lower() for keyword in ['album', 'series', 'lazarus']):
                potential_links.append((href, text))
            
            # Cari link dengan teks yang mengandung lazarus atau episode
            if any(keyword in text.lower() for keyword in ['lazarus', 'episode', '集']):
                potential_links.append((href, text))
        
        print(f"\n📋 Found {len(potential_links)} potential links:")
        
        unique_links = {}
        for href, text in potential_links:
            if href not in unique_links:
                unique_links[href] = text
                # Convert relative links to absolute
                if href.startswith('/'):
                    full_url = f"https://www.iq.com{href}"
                else:
                    full_url = href
                
                print(f"  Link: {full_url}")
                print(f"  Text: {text}")
                print()
        
        # Coba cari link dengan pattern tertentu
        print("🔍 Looking for specific patterns...")
        
        # Pattern 1: Link ke album dengan ID yang sama
        album_pattern = re.compile(r'/album/[^/]+')
        # Pattern 2: Link ke play dengan nama series
        play_pattern = re.compile(r'/play/lazarus[^/]*$')
        
        for link in all_links:
            href = link.get('href', '')
            
            if album_pattern.search(href):
                full_url = f"https://www.iq.com{href}" if href.startswith('/') else href
                print(f"  Album pattern: {full_url}")
            
            if play_pattern.search(href):
                full_url = f"https://www.iq.com{href}" if href.startswith('/') else href
                print(f"  Play pattern: {full_url}")
        
        return unique_links
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

if __name__ == "__main__":
    episode_url = "https://www.iq.com/play/lazarus-episode-1-1l0n170m0qc?lang=en_us"
    links = find_series_links(episode_url)
    
    if links:
        print(f"\n✅ Found {len(links)} potential album/series links")
    else:
        print(f"\n❌ No album/series links found")