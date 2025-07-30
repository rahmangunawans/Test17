#!/usr/bin/env python3
import requests
import json
import re

def extract_streaming_urls(dash_url):
    """Extract M3U8 and streaming URLs from IQiyi DASH response"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.iqiyi.com/',
        'Origin': 'https://www.iqiyi.com'
    }
    
    try:
        response = requests.get(dash_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}", "success": False}
            
        data = response.json()
        
        streaming_urls = []
        
        # Extract from program.video array
        program = data.get('data', {}).get('program', {})
        videos = program.get('video', [])
        
        for video in videos:
            quality = video.get('scn', video.get('br', 'unknown'))
            duration = video.get('duration', 0)
            
            # Check different URL fields
            m3u8_url = video.get('m3u8Url') or video.get('m3u8url') or video.get('m3u8')
            mp4_url = video.get('l') or video.get('url') or video.get('mp4Url')
            mpd_url = video.get('mpdUrl') or video.get('mpd')
            
            # Try to construct streaming URLs from fragments
            if video.get('fs'):
                for fragment in video['fs']:
                    if fragment.get('l'):
                        streaming_urls.append({
                            'type': 'mp4',
                            'url': fragment['l'],
                            'quality': quality,
                            'duration': duration
                        })
            
            # Add found URLs
            if m3u8_url:
                streaming_urls.append({
                    'type': 'm3u8',
                    'url': m3u8_url,
                    'quality': quality,
                    'duration': duration
                })
            
            if mp4_url:
                streaming_urls.append({
                    'type': 'mp4', 
                    'url': mp4_url,
                    'quality': quality,
                    'duration': duration
                })
                
            if mpd_url:
                streaming_urls.append({
                    'type': 'dash',
                    'url': mpd_url,
                    'quality': quality,
                    'duration': duration
                })
        
        # Extract from audio if available
        audios = program.get('audio', [])
        for audio in audios:
            audio_url = audio.get('l') or audio.get('url')
            if audio_url:
                streaming_urls.append({
                    'type': 'audio',
                    'url': audio_url,
                    'quality': audio.get('br', 'unknown'),
                    'duration': audio.get('duration', 0)
                })
        
        # Look for any URLs in the response that might be streaming links
        response_text = json.dumps(data)
        url_pattern = r'https?://[^\s",}]+\.(?:m3u8|mp4|ts|mpd)'
        found_urls = re.findall(url_pattern, response_text)
        
        for url in found_urls:
            if url not in [item['url'] for item in streaming_urls]:
                file_type = url.split('.')[-1].lower()
                streaming_urls.append({
                    'type': file_type,
                    'url': url,
                    'quality': 'auto',
                    'duration': 0
                })
        
        return {
            'success': True,
            'total_videos': len(videos),
            'total_urls': len(streaming_urls),
            'streaming_urls': streaming_urls,
            'raw_response_size': len(response.text)
        }
        
    except Exception as e:
        return {"error": str(e), "success": False}

def test_dash_extraction():
    """Test the DASH URL extraction with the provided URL"""
    
    dash_url = "https://cache.video.iqiyi.com/dash?tvid=3672014441006600&bid=200&ds=1&vid=abe2c4788688b54418ebe6a4119bf1a5&src=01010031010018000000&vt=0&rs=1&uid=0&ori=pcw&ps=0&k_uid=2fd9b5561adc2e07eba6960e9e8af27d&pt=0&d=1&s=&lid=&slid=0&cf=&ct=&authKey=8dd13a158a58dcab691025c319a3ed07&k_tag=1&ost=0&ppt=0&dfp=&prio=%7B%22ff%22%3A%22f4v%22%2C%22code%22%3A2%7D&k_err_retries=0&up=&su=2&applang=en_us&sver=2&X-USER-MODE=&qd_v=2in&tm=1753905729397&k_ft1=2748779069572&k_ft4=1572868&k_ft7=4&k_ft5=16777217&bop=%7B%22version%22%3A%2210.0%22%2C%22dfp%22%3A%22%22%2C%22b_ft1%22%3A0%7D&ut=0&vf=e6f593c9623fd9a449bef482b4642f8c"
    
    print("=== Testing DASH URL Extraction ===")
    print(f"URL: {dash_url[:80]}...")
    
    result = extract_streaming_urls(dash_url)
    
    if result['success']:
        print(f"\n✅ Extraction successful!")
        print(f"Total videos found: {result['total_videos']}")
        print(f"Total streaming URLs: {result['total_urls']}")
        print(f"Response size: {result['raw_response_size']} characters")
        
        print("\n--- Streaming URLs ---")
        for i, url_info in enumerate(result['streaming_urls'], 1):
            print(f"{i}. Type: {url_info['type']}")
            print(f"   Quality: {url_info['quality']}")
            print(f"   Duration: {url_info['duration']}s")
            print(f"   URL: {url_info['url'][:100]}...")
            print()
    else:
        print(f"❌ Extraction failed: {result['error']}")

if __name__ == "__main__":
    test_dash_extraction()