import requests
import re
import json
import logging
from urllib.parse import urljoin, urlparse, parse_qs

def extract_m3u8_from_dash(dash_url):
    """
    Extract M3U8 streaming URL from IQiyi DASH URL
    Returns dict with success status and extracted data
    """
    try:
        logging.info(f"Extracting M3U8 from DASH URL: {dash_url}")
        
        # Headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.iqiyi.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Make request to DASH URL
        response = requests.get(dash_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse the JSON response from IQiyi DASH API
        try:
            data = response.json()
            logging.info("Successfully parsed DASH response as JSON")
            
            # First check for direct M3U8 URL in the JSON response
            if 'm3u8' in data:
                m3u8_url = data['m3u8']
                if m3u8_url and m3u8_url.startswith('http'):
                    logging.info(f"Found M3U8 URL directly in response: {m3u8_url}")
                    return {
                        'success': True,
                        'm3u8_url': m3u8_url,
                        'total_segments': 0,
                        'message': 'M3U8 URL extracted from JSON response'
                    }
            
            # Check for M3U8 URL in nested data structures
            def find_m3u8_in_data(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        if key == 'm3u8' and isinstance(value, str) and value.startswith('http'):
                            logging.info(f"Found M3U8 URL at {current_path}: {value}")
                            return value
                        if isinstance(value, (dict, list)):
                            result = find_m3u8_in_data(value, current_path)
                            if result:
                                return result
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        current_path = f"{path}[{i}]" if path else f"[{i}]"
                        if isinstance(item, (dict, list)):
                            result = find_m3u8_in_data(item, current_path)
                            if result:
                                return result
                return None
            
            m3u8_url = find_m3u8_in_data(data)
            if m3u8_url:
                return {
                    'success': True,
                    'm3u8_url': m3u8_url,
                    'total_segments': 0,
                    'message': 'M3U8 URL found in nested JSON data'
                }
            
            # Extract video streaming URLs from IQiyi DASH response (fallback)
            if data.get('data') and data['data'].get('program') and data['data']['program'].get('video'):
                videos = data['data']['program']['video']
                logging.info(f"Found {len(videos)} video streams")
                
                # Look for the best quality stream
                best_stream = None
                best_bitrate = 0
                
                for video in videos:
                    bitrate = video.get('br', 0)
                    
                    # Check if this video has streaming data
                    if video.get('play') and video['play'].get('ts'):
                        ts_data = video['play']['ts']
                        if ts_data.get('l'):  # Base URL exists
                            logging.info(f"Found stream with bitrate {bitrate}")
                            if bitrate > best_bitrate:
                                best_stream = video
                                best_bitrate = bitrate
                
                if best_stream:
                    # Extract streaming information
                    ts_data = best_stream['play']['ts']
                    base_url = ts_data['l']
                    duration = best_stream.get('duration', 0)
                    segments = duration // 10  # Estimate segments (10 seconds each)
                    
                    logging.info(f"Selected stream: bitrate={best_bitrate}, duration={duration}s")
                    logging.info(f"Base URL: {base_url[:100]}...")
                    
                    # For IQiyi, we return the base streaming URL
                    # The client will handle playback through their player
                    return {
                        'success': True,
                        'm3u8_url': base_url,
                        'total_segments': segments,
                        'bitrate': best_bitrate,
                        'duration': duration,
                        'message': f'IQiyi stream extracted (bitrate: {best_bitrate})'
                    }
            
            # Fallback: Look for direct M3U8 URLs in the response
            content = response.text
            m3u8_patterns = [
                r'https?://[^"\s]+\.m3u8[^"\s]*',
                r'"(https?://[^"]+\.m3u8[^"]*)"',
                r"'(https?://[^']+\.m3u8[^']*)'",
            ]
            
            m3u8_urls = []
            for pattern in m3u8_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                m3u8_urls.extend(matches)
            
            if m3u8_urls:
                unique_urls = list(set(m3u8_urls))
                best_url = unique_urls[0].strip('"\'')
                
                logging.info(f"Fallback: Found M3U8 URL: {best_url}")
                return {
                    'success': True,
                    'm3u8_url': best_url,
                    'total_segments': 0,
                    'message': 'M3U8 URL found via fallback method'
                }
                
        except json.JSONDecodeError:
            logging.warning("Response is not valid JSON, trying text parsing")
            
        # Method 2: Text-based parsing for non-JSON responses
        content = response.text
        
        # Look for JSONP callbacks
        jsonp_patterns = [
            r'QZOutputJson\s*=\s*({.+?});',
            r'callback\s*\(\s*({.+?})\s*\)',
        ]
        
        for pattern in jsonp_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    # Recursively search for streaming URLs
                    stream_url = find_streaming_url_in_dict(data)
                    if stream_url:
                        return {
                            'success': True,
                            'm3u8_url': stream_url,
                            'total_segments': 0,
                            'message': 'Stream URL found in JSONP data'
                        }
                except:
                    continue
        
        # If no M3U8 found, return fallback
        logging.warning("No M3U8 URL found in DASH content")
        return {
            'success': False,
            'error': 'No M3U8 URL found',
            'message': 'Could not extract streaming URL from DASH'
        }
        
    except requests.RequestException as e:
        logging.error(f"Request error when extracting DASH: {e}")
        return {
            'success': False,
            'error': f'Request failed: {str(e)}',
            'message': 'Failed to fetch DASH content'
        }
    except Exception as e:
        logging.error(f"Unexpected error in DASH extraction: {e}")
        return {
            'success': False,
            'error': f'Extraction failed: {str(e)}',
            'message': 'Unexpected error during extraction'
        }

def find_streaming_url_in_dict(data, max_depth=5):
    """
    Recursively search for streaming URLs in nested dictionary/list structures
    """
    if max_depth <= 0:
        return None
        
    if isinstance(data, dict):
        for key, value in data.items():
            # Look for various streaming URL patterns
            if isinstance(value, str) and value.startswith('http'):
                if any(ext in value for ext in ['.m3u8', '.ts', 'stream', 'video']):
                    return value
            elif isinstance(value, (dict, list)):
                result = find_streaming_url_in_dict(value, max_depth - 1)
                if result:
                    return result
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, str) and item.startswith('http'):
                if any(ext in item for ext in ['.m3u8', '.ts', 'stream', 'video']):
                    return item
            elif isinstance(item, (dict, list)):
                result = find_streaming_url_in_dict(item, max_depth - 1)
                if result:
                    return result
    
    return None