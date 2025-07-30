#!/usr/bin/env python3
import requests
import json

def test_dash_url():
    """Test the DASH URL response from IQiyi to understand the format"""
    
    url = "https://cache.video.iqiyi.com/dash?tvid=3672014441006600&bid=200&ds=1&vid=abe2c4788688b54418ebe6a4119bf1a5&src=01010031010018000000&vt=0&rs=1&uid=0&ori=pcw&ps=0&k_uid=2fd9b5561adc2e07eba6960e9e8af27d&pt=0&d=1&s=&lid=&slid=0&cf=&ct=&authKey=8dd13a158a58dcab691025c319a3ed07&k_tag=1&ost=0&ppt=0&dfp=&prio=%7B%22ff%22%3A%22f4v%22%2C%22code%22%3A2%7D&k_err_retries=0&up=&su=2&applang=en_us&sver=2&X-USER-MODE=&qd_v=2in&tm=1753905729397&k_ft1=2748779069572&k_ft4=1572868&k_ft7=4&k_ft5=16777217&bop=%7B%22version%22%3A%2210.0%22%2C%22dfp%22%3A%22%22%2C%22b_ft1%22%3A0%7D&ut=0&vf=e6f593c9623fd9a449bef482b4642f8c"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.iqiyi.com/',
        'Origin': 'https://www.iqiyi.com'
    }
    
    try:
        print("Testing DASH URL...")
        print(f"URL: {url[:100]}...")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
        print(f"Content-Length: {response.headers.get('content-length', 'Unknown')}")
        print("\n--- Response Headers ---")
        for key, value in response.headers.items():
            print(f"{key}: {value}")
        
        print("\n--- Response Content ---")
        content = response.text
        print(f"Response length: {len(content)} characters")
        print("First 500 characters:")
        print(content[:500])
        
        # Try to parse as JSON
        try:
            json_data = response.json()
            print("\n--- JSON Structure ---")
            print(json.dumps(json_data, indent=2)[:1000])
            
            # Look for M3U8 URLs
            def find_m3u8_urls(obj, path=""):
                urls = []
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        new_path = f"{path}.{key}" if path else key
                        if isinstance(value, str) and ('.m3u8' in value or 'hls' in value.lower()):
                            urls.append((new_path, value))
                        urls.extend(find_m3u8_urls(value, new_path))
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        urls.extend(find_m3u8_urls(item, f"{path}[{i}]"))
                return urls
            
            m3u8_urls = find_m3u8_urls(json_data)
            if m3u8_urls:
                print("\n--- Found M3U8 URLs ---")
                for path, url in m3u8_urls:
                    print(f"{path}: {url}")
            else:
                print("\n--- No M3U8 URLs found ---")
                
        except json.JSONDecodeError:
            print("Response is not valid JSON")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_dash_url()