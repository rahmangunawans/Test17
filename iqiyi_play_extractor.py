#!/usr/bin/env python3
"""
IQiyi Play URL M3U8 Extractor - For Server 3 video playback
Integrates with the professional IQiyi scrapers for M3U8 extraction
"""

import logging
from typing import Dict, Any
from iqiyi_scrapers.scrapers.professional_iqiyi_scraper import ProfessionalIQiyiScraper

def extract_m3u8_from_iqiyi_play_url(iqiyi_play_url: str) -> Dict[str, Any]:
    """
    Extract M3U8 content from IQiyi play URL for video streaming
    
    Args:
        iqiyi_play_url (str): IQiyi play URL (e.g., https://www.iq.com/play/lazarus-episode-1-1l0n170m0qc)
        
    Returns:
        Dict with success status, m3u8_content, and episode info
    """
    try:
        logging.info(f"🎬 Extracting M3U8 from IQiyi play URL: {iqiyi_play_url[:80]}...")
        
        # Validate URL format
        if not iqiyi_play_url or 'iq.com/play/' not in iqiyi_play_url:
            return {
                'success': False,
                'error': 'Invalid IQiyi play URL format',
                'method': 'validation'
            }
        
        # Use professional scraper to extract M3U8
        scraper = ProfessionalIQiyiScraper(iqiyi_play_url)
        
        # Get M3U8 content using the scraper's method
        m3u8_content = scraper.get_m3u8()
        
        if m3u8_content and len(m3u8_content) > 100:
            logging.info(f"✅ M3U8 content extracted successfully ({len(m3u8_content)} characters)")
            
            # Get additional episode info
            player_data = scraper.get_player_data()
            episode_info = {}
            
            if player_data:
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
            
            return {
                'success': True,
                'm3u8_content': m3u8_content,
                'method': 'professional_scraper',
                'episode_info': episode_info
            }
        else:
            # Try fallback method with DASH URL to extract actual M3U8
            logging.info("🔄 M3U8 direct extraction failed, trying DASH API method...")
            
            dash_query = scraper.dash()
            if dash_query:
                dash_url = f'https://cache.video.iqiyi.com/dash?{dash_query}'
                logging.info(f"✅ DASH URL generated, attempting M3U8 extraction...")
                
                # Try to extract M3U8 from DASH API response
                try:
                    response = scraper._request('get', dash_url)
                    if response:
                        dash_data = response.json()
                        if dash_data.get('code') == 'A00000':
                            video_data = dash_data.get('data', {}).get('program', {}).get('video', [])
                            
                            # Look for M3U8 in video data
                            for video_item in video_data:
                                if isinstance(video_item, dict) and 'm3u8' in video_item:
                                    m3u8_url = video_item['m3u8']
                                    logging.info(f"✅ M3U8 URL found in DASH response")
                                    return {
                                        'success': True,
                                        'm3u8_content': m3u8_url,
                                        'method': 'dash_api_extraction',
                                        'episode_info': {}
                                    }
                            
                            # If no M3U8 found, return DASH URL as fallback
                            logging.info("⚠️ No M3U8 in DASH response, returning DASH URL as fallback")
                            return {
                                'success': True,
                                'm3u8_content': dash_url,
                                'method': 'dash_url_fallback',
                                'episode_info': {},
                                'note': 'DASH URL returned as M3U8 fallback'
                            }
                except Exception as e:
                    logging.warning(f"DASH API parsing failed: {e}")
                    return {
                        'success': True,
                        'm3u8_content': dash_url,
                        'method': 'dash_url_fallback',
                        'episode_info': {},
                        'note': 'DASH URL returned as M3U8 fallback'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Could not extract M3U8 content or generate DASH URL',
                    'method': 'professional_scraper'
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