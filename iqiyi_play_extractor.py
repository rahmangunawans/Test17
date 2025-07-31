#!/usr/bin/env python3
"""
Simple iQiyi Play URL to M3U8 Extractor
Extracts M3U8 content directly from iQiyi play URLs like:
https://www.iq.com/play/super-cube-episode-1-11eihk07dr8?lang=en_us
"""

import requests
import json
import logging
import re
from urllib.parse import urlparse, parse_qs
from enhanced_iqiyi_scraper import scrape_all_episodes_playlist

def extract_m3u8_from_iqiyi_play_url(play_url):
    """
    Extract M3U8 content from iQiyi play URL
    
    Args:
        play_url (str): iQiyi play URL like https://www.iq.com/play/super-cube-episode-1-11eihk07dr8?lang=en_us
        
    Returns:
        dict: Result with success status and M3U8 content or error
    """
    try:
        logging.info(f"🎬 Extracting M3U8 from iQiyi play URL: {play_url[:100]}...")
        
        # Method 1: Try to extract episode info from URL and use enhanced scraper
        try:
            # Extract episode info from URL pattern
            match = re.search(r'/play/([^-]+-episode-\d+)-([a-zA-Z0-9]+)', play_url)
            if match:
                episode_slug = match.group(1)
                episode_id = match.group(2)
                
                logging.info(f"🔍 Found episode info: {episode_slug}, ID: {episode_id}")
                
                # Use enhanced scraper to get DASH URL
                result = scrape_all_episodes_playlist(play_url, max_episodes=1)
                
                if result.get('success') and result.get('episodes'):
                    episode = result['episodes'][0]
                    if episode.get('dash_url'):
                        logging.info("✅ Got DASH URL from enhanced scraper, extracting M3U8...")
                        
                        # Import and use the DASH extractor
                        from iqiyi_dash_extractor import extract_m3u8_from_dash_url
                        dash_result = extract_m3u8_from_dash_url(episode['dash_url'])
                        
                        if dash_result.get('success'):
                            return {
                                'success': True,
                                'method': 'enhanced_scraper_dash',
                                'm3u8_content': dash_result['m3u8_content'],
                                'episode_info': {
                                    'title': episode.get('title', 'Unknown'),
                                    'episode_number': episode.get('episode_number', 1),
                                    'thumbnail': episode.get('thumbnail_url', '')
                                }
                            }
        
        except Exception as e:
            logging.warning(f"Enhanced scraper method failed: {e}")
        
        # Method 2: Try direct URL scraping (fallback)
        try:
            logging.info("🔄 Trying direct URL scraping method...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(play_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Look for DASH URL in page content
            dash_url_match = re.search(r'https://cache\.video\.iqiyi\.com/dash\?[^"\']+', response.text)
            if dash_url_match:
                dash_url = dash_url_match.group(0)
                logging.info(f"🎯 Found DASH URL in page: {dash_url[:100]}...")
                
                from iqiyi_dash_extractor import extract_m3u8_from_dash_url
                dash_result = extract_m3u8_from_dash_url(dash_url)
                
                if dash_result.get('success'):
                    return {
                        'success': True,
                        'method': 'direct_page_scraping',
                        'm3u8_content': dash_result['m3u8_content']
                    }
        
        except Exception as e:
            logging.warning(f"Direct scraping method failed: {e}")
        
        # If all methods fail
        return {
            'success': False,
            'error': 'Could not extract M3U8 from iQiyi play URL. URL might be invalid or content restricted.',
            'methods_tried': ['enhanced_scraper_dash', 'direct_page_scraping']
        }
        
    except Exception as e:
        logging.error(f"Error extracting M3U8 from play URL: {e}")
        return {
            'success': False,
            'error': f'Extraction failed: {str(e)}'
        }

def test_iqiyi_play_extraction():
    """Test function for iQiyi play URL extraction"""
    test_url = "https://www.iq.com/play/super-cube-episode-1-11eihk07dr8?lang=en_us"
    
    print("🧪 Testing iQiyi Play URL M3U8 Extraction")
    print("=" * 60)
    print(f"📍 Test URL: {test_url}")
    print()
    
    result = extract_m3u8_from_iqiyi_play_url(test_url)
    
    if result['success']:
        print("✅ SUCCESS!")
        print(f"🔄 Method: {result['method']}")
        print(f"📏 M3U8 Size: {len(result['m3u8_content']):,} characters")
        print(f"🎞️  Segments: {result['m3u8_content'].count('#EXTINF:')} video segments")
        
        if 'episode_info' in result:
            info = result['episode_info']
            print(f"📺 Episode: {info.get('title', 'Unknown')}")
            print(f"🔢 Number: {info.get('episode_number', 'Unknown')}")
    else:
        print("❌ FAILED!")
        print(f"💥 Error: {result['error']}")
        if 'methods_tried' in result:
            print(f"🔄 Methods tried: {', '.join(result['methods_tried'])}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_iqiyi_play_extraction()