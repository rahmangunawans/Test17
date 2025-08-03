#!/usr/bin/env python3
"""
Smart Episode Detector untuk IQiyi
Mendeteksi apakah URL adalah episode tunggal atau album, dan mengonversi sesuai kebutuhan
"""

import requests
import json
from bs4 import BeautifulSoup
import urllib3
import re

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class IQiyiSmartDetector:
    """Smart detector untuk URL IQiyi"""
    
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.verify = False
    
    def analyze_url(self, url: str) -> dict:
        """Analisis URL IQiyi untuk menentukan tipe dan ekstrak informasi"""
        print(f"🔍 Analyzing URL: {url}")
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            
            if not script_tag:
                return {'success': False, 'error': 'No __NEXT_DATA__ found'}
            
            player_data = json.loads(script_tag.string)
            
            # Extract play data
            props = player_data.get('props', {})
            initial_state = props.get('initialState', {})
            play = initial_state.get('play', {})
            
            # Check if this is an episode or album page
            avlist = play.get('avlist', [])
            cache_playlist = play.get('cachePlayList', {})
            album_info = play.get('albumInfo', {})
            
            result = {
                'success': True,
                'original_url': url,
                'is_episode': len(avlist) == 0 and not cache_playlist,
                'is_album': len(avlist) > 0 or bool(cache_playlist),
                'album_info': {
                    'name': album_info.get('name', ''),
                    'total_episodes': album_info.get('total', 0),
                    'album_id': album_info.get('albumId', ''),
                    'max_order': album_info.get('maxOrder', 0)
                }
            }
            
            # If this is an episode page, try to construct album URL
            if result['is_episode'] and album_info.get('albumId'):
                album_id = album_info['albumId']
                
                # Try different album URL patterns
                possible_album_urls = [
                    f"https://www.iq.com/album/{album_id}",
                    f"https://www.iq.com/play/{album_id}",
                    f"https://www.iq.com/album/lazarus-{album_id}",
                ]
                
                # Extract series name from URL if possible
                url_match = re.search(r'/play/([^-]+)', url)
                if url_match:
                    series_name = url_match.group(1)
                    possible_album_urls.append(f"https://www.iq.com/album/{series_name}-{album_id}")
                
                result['suggested_album_urls'] = possible_album_urls
                
                # Test which album URL works
                for album_url in possible_album_urls:
                    if self._test_album_url(album_url):
                        result['working_album_url'] = album_url
                        break
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_album_url(self, url: str) -> bool:
        """Test apakah album URL menghasilkan episode list"""
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
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
            
            # Check if this album URL has episode data
            avlist = play.get('avlist', [])
            cache_playlist = play.get('cachePlayList', {})
            
            return len(avlist) > 0 or bool(cache_playlist.get('1', []))
            
        except Exception:
            return False

def analyze_iqiyi_url(url: str):
    """Helper function untuk analisis cepat URL IQiyi"""
    detector = IQiyiSmartDetector()
    return detector.analyze_url(url)

if __name__ == "__main__":
    # Test dengan URL Lazarus
    test_url = "https://www.iq.com/play/lazarus-episode-1-1l0n170m0qc?lang=en_us"
    result = analyze_iqiyi_url(test_url)
    
    print("\n📋 Analysis Result:")
    print(json.dumps(result, indent=2))