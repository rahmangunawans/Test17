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
        
        # Parse the response to find M3U8 URLs
        content = response.text
        
        # Method 1: Look for direct M3U8 URLs in the content
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
            # Remove duplicates and clean URLs
            unique_urls = list(set(m3u8_urls))
            best_url = unique_urls[0]  # Take the first one
            
            # Clean the URL (remove quotes, etc.)
            best_url = best_url.strip('"\'')
            
            logging.info(f"Found M3U8 URL: {best_url}")
            
            # Try to get segment count from M3U8 playlist
            try:
                m3u8_response = requests.get(best_url, headers=headers, timeout=15)
                if m3u8_response.status_code == 200:
                    segments = len(re.findall(r'#EXTINF:', m3u8_response.text))
                    logging.info(f"M3U8 playlist has {segments} segments")
                else:
                    segments = 0
            except:
                segments = 0
            
            return {
                'success': True,
                'm3u8_url': best_url,
                'total_segments': segments,
                'message': 'M3U8 URL extracted successfully'
            }
        
        # Method 2: Look for JSON data containing streaming URLs
        json_patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
            r'window\.__NUXT__\s*=\s*({.+?});',
            r'data\s*:\s*({.+?})',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    # Recursively search for M3U8 URLs in JSON
                    m3u8_url = find_m3u8_in_dict(data)
                    if m3u8_url:
                        return {
                            'success': True,
                            'm3u8_url': m3u8_url,
                            'total_segments': 0,
                            'message': 'M3U8 URL found in JSON data'
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

def find_m3u8_in_dict(data, max_depth=5):
    """
    Recursively search for M3U8 URLs in nested dictionary/list structures
    """
    if max_depth <= 0:
        return None
        
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and '.m3u8' in value and value.startswith('http'):
                return value
            elif isinstance(value, (dict, list)):
                result = find_m3u8_in_dict(value, max_depth - 1)
                if result:
                    return result
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, str) and '.m3u8' in item and item.startswith('http'):
                return item
            elif isinstance(item, (dict, list)):
                result = find_m3u8_in_dict(item, max_depth - 1)
                if result:
                    return result
    
    return None