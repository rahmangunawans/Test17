#!/usr/bin/env python3
"""
Debug script untuk memeriksa struktur data IQiyi
"""

import requests
import json
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def debug_iqiyi_structure(url):
    """Debug struktur data IQiyi untuk menemukan episode data"""
    print(f"🔍 Debugging IQiyi structure for: {url}")
    
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
        
        if not script_tag:
            print("❌ No __NEXT_DATA__ script tag found")
            return None
        
        try:
            player_data = json.loads(script_tag.string)
            print("✅ Player data loaded successfully")
            
            # Debug: Print top-level keys
            print("\n🔍 Top-level keys:")
            for key in player_data.keys():
                print(f"  - {key}")
            
            # Navigate and debug structure
            props = player_data.get('props', {})
            print(f"\n🔍 Props keys: {list(props.keys())}")
            
            if 'initialState' in props:
                initial_state = props['initialState']
                print(f"🔍 InitialState keys: {list(initial_state.keys())}")
                
                if 'play' in initial_state:
                    play = initial_state['play']
                    print(f"🔍 Play keys: {list(play.keys())}")
                    
                    # Check for different possible episode data locations
                    possible_paths = [
                        'cachePlayList',
                        'playlist',
                        'episodes',
                        'videoList',
                        'albumData',
                        'seriesData'
                    ]
                    
                    for path in possible_paths:
                        if path in play:
                            data = play[path]
                            print(f"✅ Found '{path}': {type(data)}")
                            if isinstance(data, dict):
                                print(f"   Dict keys: {list(data.keys())}")
                                for k, v in data.items():
                                    if isinstance(v, list):
                                        print(f"   '{k}' contains {len(v)} items")
                                        if len(v) > 0:
                                            print(f"     First item: {type(v[0])}")
                                            if isinstance(v[0], dict):
                                                print(f"     First item keys: {list(v[0].keys())}")
                            elif isinstance(data, list):
                                print(f"   List contains {len(data)} items")
                                if len(data) > 0:
                                    print(f"     First item: {type(data[0])}")
                                    if isinstance(data[0], dict):
                                        print(f"     First item keys: {list(data[0].keys())}")
                    
                    # Specifically check albumInfo and avlist
                    if 'albumInfo' in play:
                        album_info = play['albumInfo']
                        print(f"\n🎬 AlbumInfo detailed structure:")
                        print(f"   Type: {type(album_info)}")
                        if isinstance(album_info, dict):
                            print(f"   Keys: {list(album_info.keys())}")
                            
                            # Check important album information
                            if 'albumId' in album_info:
                                print(f"   Album ID: {album_info['albumId']}")
                            if 'name' in album_info:
                                print(f"   Album Name: {album_info['name']}")
                            if 'total' in album_info:
                                print(f"   Total Episodes: {album_info['total']}")
                            if 'maxOrder' in album_info:
                                print(f"   Max Order: {album_info['maxOrder']}")
                            
                            # Look for episode-related data
                            for key, value in album_info.items():
                                if isinstance(value, list) and len(value) > 0:
                                    print(f"   '{key}' has {len(value)} items")
                                    if isinstance(value[0], dict):
                                        print(f"     Sample keys: {list(value[0].keys())}")
                    
                    if 'avlist' in play:
                        avlist = play['avlist']
                        print(f"\n📺 Avlist detailed structure:")
                        print(f"   Type: {type(avlist)}")
                        if isinstance(avlist, list):
                            print(f"   Length: {len(avlist)}")
                            if len(avlist) > 0:
                                print(f"   First item keys: {list(avlist[0].keys())}")
                        elif isinstance(avlist, dict):
                            print(f"   Keys: {list(avlist.keys())}")
            
            # Check for pageProps as alternative
            if 'pageProps' in props:
                page_props = props['pageProps']
                print(f"🔍 PageProps keys: {list(page_props.keys())}")
                
                # Look for episode data in pageProps
                episode_related_keys = [k for k in page_props.keys() 
                                      if 'episode' in k.lower() or 'video' in k.lower() 
                                      or 'playlist' in k.lower() or 'series' in k.lower()]
                
                if episode_related_keys:
                    print(f"✅ Found episode-related keys in pageProps: {episode_related_keys}")
                    for key in episode_related_keys:
                        data = page_props[key]
                        print(f"   '{key}': {type(data)}")
                        if isinstance(data, list):
                            print(f"     Contains {len(data)} items")
                        elif isinstance(data, dict):
                            print(f"     Dict keys: {list(data.keys())}")
            
            return player_data
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    # Test with the Lazarus album URL
    test_url = "https://www.iq.com/album/3813997793733701"
    debug_iqiyi_structure(test_url)