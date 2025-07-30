import requests
import re
import json
from urllib.parse import urlparse, parse_qs, unquote
import logging
import time

def advanced_iqiyi_test():
    """Advanced IQiyi scraping test with detailed analysis"""
    
    test_url = "https://www.iq.com/play/super-cube-episode-1-11eihk07dr8?lang=en_us"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    print("🔍 Analyzing IQiyi page structure...")
    print(f"URL: {test_url}")
    print("-" * 80)
    
    try:
        # Get the main page
        response = session.get(test_url)
        response.raise_for_status()
        html_content = response.text
        
        print(f"✓ Page loaded successfully ({len(html_content)} chars)")
        
        # Save HTML for analysis
        with open('iqiyi_page.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("✓ Page saved to iqiyi_page.html for analysis")
        
        # Look for JavaScript objects that might contain video info
        print("\n🔍 Searching for JavaScript data objects...")
        
        js_patterns = [
            (r'window\.Q\s*=\s*({.+?});', 'window.Q'),
            (r'window\.__INITIAL_STATE__\s*=\s*({.+?});', 'window.__INITIAL_STATE__'),
            (r'window\.playData\s*=\s*({.+?});', 'window.playData'),
            (r'window\.videoData\s*=\s*({.+?});', 'window.videoData'),
            (r'"playPageInfo":\s*({.+?})', 'playPageInfo'),
            (r'"episode":\s*({.+?})', 'episode'),
            (r'"tvId":"([^"]+)"', 'tvId'),
            (r'"vid":"([^"]+)"', 'vid'),
            (r'"albumId":"([^"]+)"', 'albumId'),
        ]
        
        found_data = {}
        for pattern, name in js_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            if matches:
                print(f"  ✓ Found {name}: {len(matches)} matches")
                if name in ['tvId', 'vid', 'albumId']:
                    found_data[name] = matches[0]
                else:
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(matches[0])
                        found_data[name] = parsed
                        print(f"    - Parsed JSON successfully")
                    except:
                        found_data[name] = matches[0][:200] + "..." if len(matches[0]) > 200 else matches[0]
                        print(f"    - Stored as text (not valid JSON)")
        
        # Look for API endpoints mentioned in the page
        print("\n🔍 Searching for API endpoints...")
        api_patterns = [
            r'(https?://[^"\s]*api[^"\s]*)',
            r'(https?://[^"\s]*cache[^"\s]*)',
            r'(https?://[^"\s]*video[^"\s]*)',
            r'(https?://[^"\s]*\.m3u8[^"\s]*)',
            r'(https?://[^"\s]*dash[^"\s]*)'
        ]
        
        all_urls = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, html_content)
            all_urls.update(matches)
        
        if all_urls:
            print(f"  ✓ Found {len(all_urls)} potential API URLs:")
            for url in sorted(all_urls)[:10]:  # Show first 10
                print(f"    - {url}")
        
        # Try to find video IDs
        print(f"\n📋 Found video identifiers:")
        for key, value in found_data.items():
            if key in ['tvId', 'vid', 'albumId']:
                print(f"  {key}: {value}")
        
        # Test direct API calls with found IDs
        if 'tvId' in found_data or 'vid' in found_data:
            print(f"\n🚀 Testing API endpoints...")
            
            video_id = found_data.get('tvId') or found_data.get('vid')
            test_urls = [
                f"https://cache.video.iq.com/jp/{video_id}",
                f"https://pcw-api.iq.com/api/video/{video_id}",
                f"https://pcw-api.iq.com/api/video/{video_id}/dash",
                f"https://cache.video.iq.com/intl/{video_id}",
            ]
            
            for test_api_url in test_urls:
                try:
                    print(f"  Testing: {test_api_url}")
                    api_response = session.get(test_api_url, timeout=10)
                    print(f"    Status: {api_response.status_code}")
                    
                    if api_response.status_code == 200:
                        try:
                            api_data = api_response.json()
                            print(f"    ✓ JSON response ({len(str(api_data))} chars)")
                            
                            # Save the response
                            filename = f"api_response_{video_id}_{test_api_url.split('/')[-1]}.json"
                            with open(filename, 'w') as f:
                                json.dump(api_data, f, indent=2)
                            print(f"    ✓ Saved to {filename}")
                            
                            # Quick check for M3U8 URLs
                            api_text = json.dumps(api_data)
                            m3u8_count = api_text.count('.m3u8')
                            if m3u8_count > 0:
                                print(f"    🎯 Found {m3u8_count} M3U8 references!")
                                
                        except:
                            print(f"    Response is not JSON, length: {len(api_response.text)}")
                            if '.m3u8' in api_response.text:
                                print(f"    🎯 Found M3U8 references in text response!")
                    else:
                        print(f"    ❌ Failed with status {api_response.status_code}")
                        
                except Exception as e:
                    print(f"    ❌ Error: {str(e)}")
                
                time.sleep(1)  # Be respectful to the API
        
        print(f"\n✅ Analysis complete! Check the saved files for detailed data.")
        return found_data
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = advanced_iqiyi_test()