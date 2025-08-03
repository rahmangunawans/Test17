#!/usr/bin/env python3
"""
Advanced IQiyi Episode Scraper - Mencoba berbagai metode untuk mendapatkan semua episode
"""

import requests
import json
from bs4 import BeautifulSoup
import urllib3
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class EpisodeData:
    title: str
    episode_number: int
    url: str
    description: str = ""
    thumbnail: str = ""

class AdvancedIQiyiScraper:
    """Advanced scraper yang mencoba berbagai metode untuk mendapatkan episode list"""
    
    def __init__(self, url: str):
        self.url = url
        self.session = requests.Session()
        self.session.verify = False
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'upgrade-insecure-requests': '1'
        }
    
    def extract_all_episodes_advanced(self) -> List[EpisodeData]:
        """Mencoba berbagai metode untuk mendapatkan semua episode"""
        print("🚀 Starting advanced episode extraction...")
        
        # Method 1: Coba cari episode dengan pattern URL generation
        episodes = self._method_url_pattern_generation()
        if episodes:
            print(f"✅ Method 1 (URL Pattern) found {len(episodes)} episodes")
            return episodes
        
        # Method 2: Coba extract dari initial data dengan deep search
        episodes = self._method_deep_data_search()
        if episodes:
            print(f"✅ Method 2 (Deep Search) found {len(episodes)} episodes")
            return episodes
        
        # Method 3: Coba API calls dengan berbagai endpoint
        episodes = self._method_api_exploration()
        if episodes:
            print(f"✅ Method 3 (API Exploration) found {len(episodes)} episodes")
            return episodes
        
        # Method 4: HTML pattern analysis
        episodes = self._method_html_pattern_analysis()
        if episodes:
            print(f"✅ Method 4 (HTML Pattern) found {len(episodes)} episodes")
            return episodes
        
        print("❌ All methods failed to extract multiple episodes")
        return []
    
    def _method_url_pattern_generation(self) -> List[EpisodeData]:
        """Method 1: Generate episode URLs berdasarkan pattern yang terdeteksi"""
        print("🔍 Method 1: URL Pattern Generation")
        
        try:
            # Extract album info dulu
            album_info = self._get_album_info()
            if not album_info:
                return []
            
            total_episodes = album_info.get('total', 0)
            series_name = album_info.get('name', '')
            
            if total_episodes <= 1:
                return []
            
            print(f"   Series: {series_name}")
            print(f"   Total Episodes: {total_episodes}")
            
            # Analyze current URL pattern
            # https://www.iq.com/play/lazarus-episode-1-1l0n170m0qc?lang=en_us
            url_match = re.search(r'/play/([^-]+)-episode-(\d+)-([^?]+)', self.url)
            if not url_match:
                print("   ❌ Could not parse URL pattern")
                return []
            
            series_slug = url_match.group(1)  # lazarus
            current_episode = int(url_match.group(2))  # 1
            video_id_base = url_match.group(3)  # 1l0n170m0qc
            
            print(f"   Detected pattern: {series_slug}-episode-X-{video_id_base}")
            
            episodes = []
            
            # Generate URLs untuk semua episode
            for ep_num in range(1, min(total_episodes + 1, 21)):  # Limit to 20 episodes for safety
                if ep_num == current_episode:
                    # Use current URL for known episode
                    episode_url = self.url.split('?')[0]
                else:
                    # Generate URL for other episodes
                    # Pattern yang umum di IQiyi
                    possible_patterns = [
                        f"https://www.iq.com/play/{series_slug}-episode-{ep_num}-{video_id_base}",
                        f"https://www.iq.com/play/{series_slug}-episode-{ep_num:02d}-{video_id_base}",
                        f"https://www.iq.com/play/{series_slug}-{ep_num}-{video_id_base}",
                    ]
                    
                    episode_url = None
                    for pattern in possible_patterns:
                        if self._test_episode_url(pattern):
                            episode_url = pattern
                            break
                    
                    if not episode_url:
                        print(f"   ❌ Could not find valid URL for episode {ep_num}")
                        continue
                
                # Extract episode info
                episode_info = self._extract_episode_info(episode_url, ep_num)
                if episode_info:
                    episodes.append(episode_info)
                    print(f"   ✅ Episode {ep_num}: {episode_info.title}")
            
            return episodes
            
        except Exception as e:
            print(f"   ❌ Error in URL pattern method: {e}")
            return []
    
    def _method_deep_data_search(self) -> List[EpisodeData]:
        """Method 2: Deep search dalam data structure"""
        print("🔍 Method 2: Deep Data Search")
        
        try:
            response = self.session.get(self.url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Search semua script tags
            script_tags = soup.find_all('script')
            
            for i, script in enumerate(script_tags):
                if not script.string:
                    continue
                
                # Look for episode data patterns
                if any(keyword in script.string for keyword in ['episode', 'Episode', '集', 'avlist', 'playList']):
                    print(f"   🔍 Checking script tag {i+1}")
                    
                    # Try to extract JSON data
                    json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', script.string)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            episodes = self._search_episodes_in_data(data)
                            if episodes:
                                return episodes
                        except:
                            continue
            
            print("   ❌ No episode data found in scripts")
            return []
            
        except Exception as e:
            print(f"   ❌ Error in deep search method: {e}")
            return []
    
    def _method_api_exploration(self) -> List[EpisodeData]:
        """Method 3: Explore berbagai API endpoints"""
        print("🔍 Method 3: API Exploration")
        
        album_info = self._get_album_info()
        if not album_info:
            return []
        
        album_id = album_info.get('albumId', '')
        if not album_id:
            return []
        
        # API endpoints yang mungkin
        api_endpoints = [
            f"https://pcw-api.iq.com/api/v2/episodelist/{album_id}",
            f"https://pcw-api.iq.com/episodelist/{album_id}?lang=en_us",
            f"https://intl-api.iq.com/api/episodelist/{album_id}",
            f"https://www.iq.com/api/v1/album/{album_id}/episodes",
            f"https://www.iq.com/xhr/album/{album_id}/episodes",
            f"https://cache-video.iq.com/jp/api/v2/albuminfo/{album_id}",
            f"https://cache-video.iq.com/jp/api/v2/episodelist/{album_id}",
        ]
        
        headers_api = {
            **self.headers,
            'accept': 'application/json, text/plain, */*',
            'referer': self.url,
            'x-requested-with': 'XMLHttpRequest'
        }
        
        for endpoint in api_endpoints:
            try:
                print(f"   Testing: {endpoint}")
                response = self.session.get(endpoint, headers=headers_api, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        episodes = self._search_episodes_in_data(data)
                        if episodes:
                            print(f"   ✅ Found episodes in API: {endpoint}")
                            return episodes
                    except:
                        continue
                        
            except Exception as e:
                continue
        
        print("   ❌ No working API endpoints found")
        return []
    
    def _method_html_pattern_analysis(self) -> List[EpisodeData]:
        """Method 4: Analyze HTML untuk episode patterns"""
        print("🔍 Method 4: HTML Pattern Analysis")
        
        try:
            response = self.session.get(self.url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Search untuk element yang mungkin berisi episode info
            selectors = [
                'a[href*="episode"]',
                'a[href*="play"]',
                '[class*="episode"]',
                '[class*="Episode"]',
                '[data-episode]',
                '.episode-item',
                '.episode-list',
                '.playlist-item'
            ]
            
            episodes = []
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"   Found {len(elements)} elements with selector: {selector}")
                    
                    for elem in elements:
                        href = elem.get('href', '')
                        text = elem.get_text().strip()
                        
                        if href and 'episode' in href:
                            # Try to extract episode number
                            ep_match = re.search(r'episode[-_]?(\d+)', href, re.I)
                            if ep_match:
                                ep_num = int(ep_match.group(1))
                                
                                if href.startswith('/'):
                                    href = f"https://www.iq.com{href}"
                                
                                episode = EpisodeData(
                                    title=text or f"Episode {ep_num}",
                                    episode_number=ep_num,
                                    url=href
                                )
                                episodes.append(episode)
            
            # Remove duplicates
            unique_episodes = []
            seen_episodes = set()
            
            for ep in episodes:
                if ep.episode_number not in seen_episodes:
                    seen_episodes.add(ep.episode_number)
                    unique_episodes.append(ep)
            
            if unique_episodes:
                unique_episodes.sort(key=lambda x: x.episode_number)
                print(f"   ✅ Found {len(unique_episodes)} unique episodes")
                return unique_episodes
            
            print("   ❌ No valid episodes found in HTML")
            return []
            
        except Exception as e:
            print(f"   ❌ Error in HTML analysis: {e}")
            return []
    
    def _get_album_info(self) -> Optional[Dict]:
        """Get album info dari current URL"""
        try:
            response = self.session.get(self.url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            
            if script_tag:
                player_data = json.loads(script_tag.string)
                props = player_data.get('props', {})
                initial_state = props.get('initialState', {})
                play = initial_state.get('play', {})
                return play.get('albumInfo', {})
            
            return None
            
        except Exception:
            return None
    
    def _test_episode_url(self, url: str) -> bool:
        """Test apakah episode URL valid"""
        try:
            response = self.session.head(url, headers=self.headers, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _extract_episode_info(self, url: str, episode_num: int) -> Optional[EpisodeData]:
        """Extract info dari episode URL"""
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to get title from page
            title_selectors = ['title', 'h1', '.video-title', '.episode-title']
            title = f"Episode {episode_num}"
            
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem:
                    title = elem.get_text().strip()
                    break
            
            return EpisodeData(
                title=title,
                episode_number=episode_num,
                url=url
            )
            
        except:
            return None
    
    def _search_episodes_in_data(self, data: Dict) -> List[EpisodeData]:
        """Search episode data dalam nested dictionary"""
        episodes = []
        
        def recursive_search(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    
                    # Look for episode-related keys
                    if key.lower() in ['episodes', 'episodelist', 'avlist', 'playlist'] and isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                episode = self._parse_episode_data(item)
                                if episode:
                                    episodes.append(episode)
                    else:
                        recursive_search(value, new_path)
                        
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    recursive_search(item, f"{path}[{i}]")
        
        recursive_search(data)
        return episodes
    
    def _parse_episode_data(self, data: Dict) -> Optional[EpisodeData]:
        """Parse episode data dari dictionary"""
        try:
            # Look for common episode fields
            title = data.get('name') or data.get('title') or data.get('episodeTitle', '')
            url = data.get('url') or data.get('playUrl') or data.get('link', '')
            episode_num = data.get('episode') or data.get('episodeNumber') or data.get('order', 0)
            
            if not title and not url:
                return None
            
            # Extract episode number from title if not found
            if not episode_num and title:
                ep_match = re.search(r'(?:episode|ep|第)\s*(\d+)', title, re.I)
                if ep_match:
                    episode_num = int(ep_match.group(1))
            
            if episode_num:
                return EpisodeData(
                    title=title or f"Episode {episode_num}",
                    episode_number=int(episode_num),
                    url=url,
                    description=data.get('description', ''),
                    thumbnail=data.get('thumbnail', '')
                )
            
            return None
            
        except:
            return None

def scrape_episodes_advanced(url: str) -> Dict:
    """Main function untuk advanced episode scraping"""
    try:
        scraper = AdvancedIQiyiScraper(url)
        episodes = scraper.extract_all_episodes_advanced()
        
        if episodes:
            episodes_list = []
            for ep in episodes:
                episodes_list.append({
                    'title': ep.title,
                    'episode_number': ep.episode_number,
                    'url': ep.url,
                    'description': ep.description,
                    'thumbnail_url': ep.thumbnail,
                    'is_valid': True
                })
            
            return {
                'success': True,
                'total_episodes': len(episodes_list),
                'episodes': episodes_list,
                'message': f'Advanced scraper extracted {len(episodes_list)} episodes successfully'
            }
        else:
            return {
                'success': False,
                'error': 'Advanced scraper could not extract multiple episodes'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Advanced scraper error: {str(e)}'
        }

if __name__ == "__main__":
    # Test dengan Lazarus URL
    test_url = "https://www.iq.com/play/lazarus-episode-1-1l0n170m0qc?lang=en_us"
    result = scrape_episodes_advanced(test_url)
    
    print("\n🏁 Advanced Scraper Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))