#!/usr/bin/env python3
"""
IQiyi DASH URL processor for AniFlix
Extracts M3U8 streaming URLs from IQiyi DASH responses
"""
import requests
import json
import re
import logging

def extract_m3u8_from_dash(dash_url):
    """
    Extract M3U8 streaming URL from IQiyi DASH URL
    
    Args:
        dash_url (str): IQiyi DASH URL
        
    Returns:
        dict: {success: bool, m3u8_url: str, error: str}
    """
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.iqiyi.com/',
        'Origin': 'https://www.iqiyi.com'
    }
    
    try:
        logging.info(f"Extracting M3U8 from DASH URL: {dash_url[:100]}...")
        
        response = requests.get(dash_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}: {response.text[:200]}',
                'm3u8_url': None
            }
            
        data = response.json()
        logging.info(f"DASH response received: {len(response.text)} characters")
        
        # Extract from program.video array
        program = data.get('data', {}).get('program', {})
        videos = program.get('video', [])
        
        for video in videos:
            # Look for M3U8 content in various fields
            m3u8_content = video.get('m3u8') or video.get('m3u8Url') or video.get('m3u8url')
            
            if m3u8_content and '#EXTM3U' in str(m3u8_content):
                # This is actual M3U8 playlist content, convert to proper URL
                if m3u8_content.startswith('#EXTM3U'):
                    # Extract the first .ts URL to construct base M3U8 URL
                    ts_urls = re.findall(r'https://[^\s\n]+\.ts', m3u8_content)
                    if ts_urls:
                        # Use the first TS URL as our streaming source
                        first_ts_url = ts_urls[0]
                        logging.info(f"Found M3U8 playlist with {len(ts_urls)} segments")
                        
                        # Return the M3U8 content as data URL for direct playback
                        m3u8_data_url = f"data:application/vnd.apple.mpegurl;base64,{m3u8_content.encode('utf-8').hex()}"
                        
                        return {
                            'success': True,
                            'm3u8_url': first_ts_url,  # Use first TS URL for now
                            'error': None,
                            'playlist_content': m3u8_content,
                            'total_segments': len(ts_urls)
                        }
                else:
                    # Direct M3U8 URL
                    return {
                        'success': True,
                        'm3u8_url': m3u8_content,
                        'error': None
                    }
        
        # Look for any .ts URLs in the response as fallback
        response_text = json.dumps(data)
        ts_urls = re.findall(r'https://[^\s",}]+\.ts', response_text)
        
        if ts_urls:
            logging.info(f"Found {len(ts_urls)} TS segments in response")
            return {
                'success': True,
                'm3u8_url': ts_urls[0],  # Use first TS URL
                'error': None,
                'fallback_segments': ts_urls[:5]  # Include first 5 for reference
            }
        
        # No streaming URLs found
        return {
            'success': False,
            'error': 'No M3U8 or TS URLs found in DASH response',
            'm3u8_url': None
        }
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return {
            'success': False,
            'error': f'Request failed: {str(e)}',
            'm3u8_url': None
        }
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        return {
            'success': False,
            'error': f'Invalid JSON response: {str(e)}',
            'm3u8_url': None
        }
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return {
            'success': False,
            'error': f'Extraction failed: {str(e)}',
            'm3u8_url': None
        }

def test_dash_extraction():
    """Test function for DASH URL extraction"""
    
    test_url = "https://cache.video.iqiyi.com/dash?tvid=3672014441006600&bid=200&ds=1&vid=abe2c4788688b54418ebe6a4119bf1a5&src=01010031010018000000&vt=0&rs=1&uid=0&ori=pcw&ps=0&k_uid=2fd9b5561adc2e07eba6960e9e8af27d&pt=0&d=1&s=&lid=&slid=0&cf=&ct=&authKey=8dd13a158a58dcab691025c319a3ed07&k_tag=1&ost=0&ppt=0&dfp=&prio=%7B%22ff%22%3A%22f4v%22%2C%22code%22%3A2%7D&k_err_retries=0&up=&su=2&applang=en_us&sver=2&X-USER-MODE=&qd_v=2in&tm=1753905729397&k_ft1=2748779069572&k_ft4=1572868&k_ft7=4&k_ft5=16777217&bop=%7B%22version%22%3A%2210.0%22%2C%22dfp%22%3A%22%22%2C%22b_ft1%22%3A0%7D&ut=0&vf=e6f593c9623fd9a449bef482b4642f8c"
    
    print("=== Testing IQiyi DASH M3U8 Extraction ===")
    result = extract_m3u8_from_dash(test_url)
    
    if result['success']:
        print("✅ Extraction successful!")
        print(f"M3U8 URL: {result['m3u8_url']}")
        if 'total_segments' in result:
            print(f"Total segments: {result['total_segments']}")
        if 'fallback_segments' in result:
            print(f"Fallback segments: {len(result['fallback_segments'])}")
    else:
        print(f"❌ Extraction failed: {result['error']}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_dash_extraction()