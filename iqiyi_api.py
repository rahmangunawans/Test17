import requests
import re
import json
from urllib.parse import urlparse, parse_qs, unquote
import logging
import time
import hashlib
import base64

class IQiyiAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def extract_video_info(self, iqiyi_url):
        """
        Extract video information including M3U8 URLs and subtitles from IQiyi URL
        """
        try:
            logging.info(f"Extracting video info from: {iqiyi_url}")
            
            # Get the page content
            response = self.session.get(iqiyi_url)
            response.raise_for_status()
            html_content = response.text
            
            # Extract video metadata
            metadata = self._extract_metadata(iqiyi_url, html_content)
            if not metadata:
                return {'success': False, 'error': 'Could not extract video metadata'}
            
            logging.info(f"Extracted metadata: {metadata}")
            
            # Try to find M3U8 URLs using multiple methods
            m3u8_urls = []
            
            # Method 1: Direct extraction from HTML
            direct_urls = self._extract_m3u8_urls(html_content)
            m3u8_urls.extend(direct_urls)
            
            # Method 2: Try IQiyi dash API
            if metadata.get('tvId') or metadata.get('vid'):
                dash_urls = self._get_dash_urls(metadata)
                m3u8_urls.extend(dash_urls)
            
            # Method 3: Try alternative API endpoints
            if not m3u8_urls and metadata.get('video_id'):
                api_urls = self._get_m3u8_from_api(metadata['video_id'], iqiyi_url)
                m3u8_urls.extend(api_urls)
            
            # Try to find subtitle URLs
            subtitles = self._extract_subtitles(html_content, metadata)
            
            # Remove duplicates
            m3u8_urls = list(set(m3u8_urls))
            
            return {
                'success': True,
                'video_id': metadata.get('video_id'),
                'tvId': metadata.get('tvId'),
                'vid': metadata.get('vid'),
                'm3u8_urls': m3u8_urls,
                'dash_url': m3u8_urls[0] if m3u8_urls else None,
                'subtitles': subtitles,
                'source_url': iqiyi_url,
                'metadata': metadata
            }
            
        except Exception as e:
            logging.error(f"Error extracting video info: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _extract_metadata(self, url, html_content):
        """Extract comprehensive metadata from URL and HTML content"""
        metadata = {}
        
        # Try to extract video ID from URL first
        url_patterns = [
            (r'/play/([^/?]+)', 'video_id'),
            (r'tvId=([^&]+)', 'tvId'),
            (r'albumId=([^&]+)', 'albumId'),
            (r'qid=([^&]+)', 'qid'),
            (r'vid=([^&]+)', 'vid')
        ]
        
        for pattern, key in url_patterns:
            match = re.search(pattern, url)
            if match:
                metadata[key] = match.group(1)
        
        # Try to extract from HTML content
        html_patterns = [
            (r'"tvId":"([^"]+)"', 'tvId'),
            (r'"albumId":"([^"]+)"', 'albumId'),
            (r'"qid":"([^"]+)"', 'qid'),
            (r'"vid":"([^"]+)"', 'vid'),
            (r'data-player-tvid="([^"]+)"', 'tvId'),
            (r'tvid:\s*"([^"]+)"', 'tvId'),
            (r'"playPageInfo":\s*({[^}]+})', 'playPageInfo'),
            (r'"episode":\s*({[^}]+})', 'episode'),
            (r'window\.Q\s*=\s*({.+?});', 'qData')
        ]
        
        for pattern, key in html_patterns:
            match = re.search(pattern, html_content)
            if match:
                if key in ['playPageInfo', 'episode', 'qData']:
                    try:
                        metadata[key] = json.loads(match.group(1))
                    except:
                        metadata[key] = match.group(1)
                else:
                    metadata[key] = match.group(1)
        
        # If no video_id found, use the first available ID
        if not metadata.get('video_id'):
            for key in ['tvId', 'vid', 'qid', 'albumId']:
                if metadata.get(key):
                    metadata['video_id'] = metadata[key]
                    break
        
        return metadata if metadata else None
    
    def _extract_m3u8_urls(self, html_content):
        """Extract M3U8 URLs from HTML content"""
        m3u8_urls = []
        
        # Common patterns for M3U8 URLs
        patterns = [
            r'"(https?://[^"]*\.m3u8[^"]*)"',
            r"'(https?://[^']*\.m3u8[^']*)'",
            r'url:\s*"(https?://[^"]*\.m3u8[^"]*)"',
            r'src:\s*"(https?://[^"]*\.m3u8[^"]*)"'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                if match not in m3u8_urls:
                    m3u8_urls.append(match)
        
        return m3u8_urls
    
    def _extract_subtitles(self, html_content, metadata):
        """Extract subtitle URLs from HTML content and metadata"""
        subtitles = []
        
        # Patterns for subtitle files
        subtitle_patterns = [
            r'"(https?://[^"]*\.vtt[^"]*)"',
            r'"(https?://[^"]*\.srt[^"]*)"',
            r'"subtitle[^"]*":\s*"(https?://[^"]+)"',
            r'"caption[^"]*":\s*"(https?://[^"]+)"',
            r'"subtitles":\s*\[([^\]]+)\]',
            r'"srt":\s*"([^"]+)"'
        ]
        
        for pattern in subtitle_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                if 'subtitles' in pattern:
                    # Parse subtitle array
                    try:
                        subtitle_data = json.loads(f'[{match}]')
                        for sub in subtitle_data:
                            if isinstance(sub, dict) and 'url' in sub:
                                lang = sub.get('language', sub.get('lang', 'Unknown'))
                                subtitles.append({
                                    'language': lang,
                                    'url': sub['url']
                                })
                    except:
                        continue
                else:
                    # Try to determine language
                    language = 'Unknown'
                    if 'en' in match.lower():
                        language = 'English'
                    elif 'zh' in match.lower() or 'cn' in match.lower():
                        language = 'Chinese'
                    elif 'id' in match.lower():
                        language = 'Indonesian'
                    
                    subtitles.append({
                        'language': language,
                        'url': match
                    })
        
        # Try to get subtitles from metadata
        if metadata.get('playPageInfo') and isinstance(metadata['playPageInfo'], dict):
            play_info = metadata['playPageInfo']
            if 'subtitles' in play_info:
                for sub in play_info['subtitles']:
                    if isinstance(sub, dict) and 'url' in sub:
                        subtitles.append({
                            'language': sub.get('language', 'Unknown'),
                            'url': sub['url']
                        })
        
        return subtitles
    
    def _get_m3u8_from_api(self, video_id, original_url):
        """Try to get M3U8 URLs using IQiyi API endpoints"""
        m3u8_urls = []
        
        # Common IQiyi API endpoints (these might need adjustment)
        api_endpoints = [
            f"https://cache.video.iq.com/jp/{video_id}",
            f"https://cache.video.iq.com/intl/{video_id}",
            f"https://pcw-api.iq.com/api/video/{video_id}",
        ]
        
        for endpoint in api_endpoints:
            try:
                response = self.session.get(endpoint, timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # Look for M3U8 URLs in the response
                        urls = self._extract_m3u8_from_json(data)
                        m3u8_urls.extend(urls)
                    except:
                        # If not JSON, try to parse as text
                        urls = self._extract_m3u8_urls(response.text)
                        m3u8_urls.extend(urls)
            except:
                continue
        
        return m3u8_urls
    
    def _extract_m3u8_from_json(self, data):
        """Extract M3U8 URLs from JSON data"""
        m3u8_urls = []
        
        def search_json(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and '.m3u8' in value:
                        if value.startswith('http'):
                            m3u8_urls.append(value)
                    else:
                        search_json(value)
            elif isinstance(obj, list):
                for item in obj:
                    search_json(item)
        
        search_json(data)
        return m3u8_urls
    
    def _get_dash_urls(self, metadata):
        """Try to get DASH/M3U8 URLs from IQiyi dash API"""
        m3u8_urls = []
        
        tv_id = metadata.get('tvId') or metadata.get('vid')
        if not tv_id:
            return m3u8_urls
            
        try:
            # IQiyi dash API endpoint
            dash_url = f"https://cache.video.iq.com/jp/{tv_id}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.iq.com/',
                'Accept': 'application/json, text/plain, */*'
            }
            
            response = self.session.get(dash_url, headers=headers, timeout=15)
            logging.info(f"Dash API response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logging.info(f"Dash API response: {json.dumps(data, indent=2)[:500]}...")
                    
                    # Look for M3U8 URLs in the response
                    urls = self._extract_m3u8_from_json(data)
                    m3u8_urls.extend(urls)
                    
                    # Also check for 'l' (dash URL) field which is common in IQiyi
                    if 'l' in data:
                        dash_m3u8 = data['l']
                        if isinstance(dash_m3u8, str) and ('.m3u8' in dash_m3u8 or 'dash' in dash_m3u8):
                            m3u8_urls.append(dash_m3u8)
                    
                    # Check for different quality streams
                    if 'data' in data and isinstance(data['data'], dict):
                        for quality, stream_data in data['data'].items():
                            if isinstance(stream_data, dict) and 'l' in stream_data:
                                stream_url = stream_data['l']
                                if '.m3u8' in stream_url or 'dash' in stream_url:
                                    m3u8_urls.append(stream_url)
                    
                except json.JSONDecodeError:
                    # If response is not JSON, try to extract URLs from text
                    urls = self._extract_m3u8_urls(response.text)
                    m3u8_urls.extend(urls)
            
            # Try alternative dash endpoint
            alt_dash_url = f"https://pcw-api.iq.com/api/video/{tv_id}/dash"
            response2 = self.session.get(alt_dash_url, headers=headers, timeout=10)
            
            if response2.status_code == 200:
                try:
                    data2 = response2.json()
                    urls2 = self._extract_m3u8_from_json(data2)
                    m3u8_urls.extend(urls2)
                except:
                    pass
                    
        except Exception as e:
            logging.error(f"Error getting dash URLs: {str(e)}")
        
        return m3u8_urls

def test_iqiyi_api():
    """Test function for IQiyi API"""
    api = IQiyiAPI()
    
    # Test URL yang diberikan
    test_url = "https://www.iq.com/play/super-cube-episode-1-11eihk07dr8?lang=en_us"
    
    print(f"Testing IQiyi API with URL: {test_url}")
    print("-" * 60)
    
    result = api.extract_video_info(test_url)
    
    if result['success']:
        print("✓ Successfully extracted video information!")
        print(f"Video ID: {result.get('video_id', 'N/A')}")
        print(f"M3U8 URLs found: {len(result.get('m3u8_urls', []))}")
        
        for i, url in enumerate(result.get('m3u8_urls', []), 1):
            print(f"  {i}. {url}")
        
        print(f"Subtitles found: {len(result.get('subtitles', []))}")
        for subtitle in result.get('subtitles', []):
            print(f"  - {subtitle['language']}: {subtitle['url']}")
    else:
        print(f"✗ Failed to extract video information: {result.get('error', 'Unknown error')}")
    
    return result

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run test
    test_result = test_iqiyi_api()