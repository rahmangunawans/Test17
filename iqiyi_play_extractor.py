#!/usr/bin/env python3
"""
IQiyi Play URL M3U8 Extractor - For Server 3 video playback
Enhanced extraction based on reference implementation
"""

import logging
import requests
import json
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

class EnhancedIQiyiExtractor:
    """Enhanced IQiyi extractor using reference methodology"""

    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()

    def _request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """Enhanced request method with better error handling"""
        try:
            kwargs.setdefault('headers', self.headers)
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            logging.error(f'❌ Error making request to {url}: {str(e)}')
            return None

    def get_player_data(self, play_url: str) -> Optional[Dict[str, Any]]:
        """Get player data from __NEXT_DATA__ script tag"""
        logging.info(f"🔍 Fetching player data from: {play_url[:50]}...")

        response = self._request('get', play_url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})

        if not script_tag:
            logging.warning("❌ No __NEXT_DATA__ script tag found")
            return None

        try:
            json_data = script_tag.string.strip()
            player_data = json.loads(json_data)
            logging.info("✅ Player data loaded successfully")
            return player_data
        except json.JSONDecodeError as e:
            logging.error(f"❌ Error parsing JSON data: {e}")
            return None

    def extract_dash_query(self, player_data: Dict[str, Any]) -> Optional[str]:
        """Extract DASH query from player data using reference method"""
        logging.info("🔍 Extracting DASH query from player data...")

        try:
            # Navigate to ssrlog like in reference
            ssrlog = player_data.get('props', {}).get('initialProps', {}).get(
                'pageProps', {}).get('prePlayerData', {}).get('ssrlog', '')

            if not ssrlog:
                logging.warning("❌ No ssrlog found in player data")
                return None

            # Use regex pattern from reference to extract DASH URL
            url_pattern = r'http://intel-cache\.video\.qiyi\.domain/dash\?([^\s]+)'
            urls = re.findall(url_pattern, ssrlog)

            if urls:
                dash_query = urls[0]
                logging.info(f"✅ DASH query extracted successfully")
                return dash_query
            else:
                logging.warning("❌ No DASH URL found in ssrlog")
                return None

        except Exception as e:
            logging.error(f"❌ Error extracting DASH query: {e}")
            return None

    def get_m3u8_from_dash(self, dash_query: str) -> Optional[str]:
        """Get M3U8 content from DASH query using reference method"""
        logging.info("🔍 Getting M3U8 from DASH query...")

        dash_url = f'https://cache.video.iqiyi.com/dash?{dash_query}'
        response = self._request('get', dash_url)

        if not response:
            return None

        try:
            data = response.json()

            # Check for API errors first
            if data.get('code') != 'A00000':
                error_code = data.get('code')
                error_msg = data.get('msg', 'Unknown error')
                logging.error(f"❌ iQiyi API error: {error_code} - {error_msg}")
                return f"ERROR_API:{error_msg}"

            # Extract M3U8 content - program is a list, not dict
            program_data = data.get('data', {}).get('program', [])
            
            # Program is a list, iterate through it
            for program_item in program_data:
                if isinstance(program_item, dict) and 'video' in program_item:
                    video_data = program_item['video']
                    
                    # Video is also a list
                    for video_item in video_data:
                        if isinstance(video_item, dict) and 'm3u8' in video_item and video_item['m3u8']:
                            m3u8_content = video_item['m3u8']
                            logging.info(f"✅ M3U8 content found: {len(m3u8_content)} characters")
                            return m3u8_content

            logging.warning("❌ No M3U8 content found in video data")
            return None

        except Exception as e:
            logging.error(f"❌ Error parsing DASH response: {e}")
            return None

def extract_m3u8_from_iqiyi_play_url(iqiyi_play_url: str) -> Dict[str, Any]:
    """
    Extract M3U8 content from IQiyi play URL for video streaming
    Using enhanced methodology from reference implementation
    """
    try:
        logging.info(f"🎬 Extracting M3U8 from IQiyi play URL: {iqiyi_play_url[:80]}...")
        
        # Validate URL format
        if not iqiyi_play_url or not ('iq.com/play/' in iqiyi_play_url or 'iqiyi.com/' in iqiyi_play_url):
            return {
                'success': False,
                'error': 'Invalid IQiyi play URL format',
                'method': 'validation'
            }
        
        extractor = EnhancedIQiyiExtractor()
        
        # Step 1: Get player data from page
        player_data = extractor.get_player_data(iqiyi_play_url)
        if not player_data:
            return {
                'success': False,
                'error': 'Could not load player data from iQiyi page',
                'method': 'enhanced_extraction'
            }

        # Step 2: Extract DASH query from ssrlog
        dash_query = extractor.extract_dash_query(player_data)
        if not dash_query:
            return {
                'success': False,
                'error': 'Could not extract DASH query from player data',
                'method': 'enhanced_extraction'
            }

        # Step 3: Get M3U8 from DASH API
        m3u8_result = extractor.get_m3u8_from_dash(dash_query)
        if not m3u8_result:
            return {
                'success': False,
                'error': 'No M3U8 content found in DASH response',
                'method': 'enhanced_extraction'
            }

        # Check for API errors
        if m3u8_result.startswith('ERROR_'):
            error_type, error_msg = m3u8_result.split(':', 1)
            return {
                'success': False,
                'error': f'iQiyi API error: {error_msg}',
                'error_type': 'api_error',
                'method': 'enhanced_extraction'
            }

        # Get episode info
        episode_info = {}
        try:
            current_episode = player_data.get('props', {}).get('initialState', {}).get('play', {}).get('curVideoInfo', {})
            episode_info = {
                'title': current_episode.get('name', 'Episode'),
                'episode_number': current_episode.get('order', 1),
                'duration': current_episode.get('duration', ''),
                'description': current_episode.get('description', '')
            }
        except Exception as e:
            logging.warning(f"Could not extract episode info: {e}")

        # Success!
        logging.info(f"✅ M3U8 extraction successful: {len(m3u8_result)} characters")
        return {
            'success': True,
            'm3u8_content': m3u8_result,
            'method': 'enhanced_extraction',
            'episode_info': episode_info,
            'dash_query': dash_query
        }
                
    except Exception as e:
        logging.error(f"❌ Error extracting M3U8 from IQiyi play URL: {str(e)}")
        return {
            'success': False,
            'error': f'Extraction failed: {str(e)}',
            'method': 'error'
        }

def test_extraction():
    """Test function to verify M3U8 extraction works"""
    test_url = "https://www.iq.com/play/lazarus-episode-1-1l0n170m0qc?lang=en_us"
    
    print("🧪 Testing IQiyi Play URL M3U8 Extraction...")
    print(f"📺 Test URL: {test_url}")
    
    result = extract_m3u8_from_iqiyi_play_url(test_url)
    
    print(f"\n📊 Result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Method: {result.get('method')}")
    
    if result.get('success'):
        m3u8_content = result.get('m3u8_content', '')
        print(f"  M3U8 Length: {len(m3u8_content)} characters")
        print(f"  M3U8 Preview: {m3u8_content[:200]}...")
        
        episode_info = result.get('episode_info', {})
        if episode_info:
            print(f"  Episode Title: {episode_info.get('title')}")
            print(f"  Episode Number: {episode_info.get('episode_number')}")
    else:
        print(f"  Error: {result.get('error')}")

if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    test_extraction()