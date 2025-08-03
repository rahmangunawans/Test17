#!/usr/bin/env python3
"""
Professional IQiyi Scraper - Integrating best practices from reference implementation
"""

import requests
import json
from bs4 import BeautifulSoup
import urllib3
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class SubtitleInfo:
    """Professional subtitle information structure"""
    language: str
    subtitle_type: str  # srt, xml, webvtt
    url: str
    language_code: Optional[str] = None

@dataclass
class EpisodeInfo:
    """Professional episode information structure"""
    title: str
    episode_number: Optional[int]
    url: str
    content_type: str  # "episode", "preview", "trailer", "unknown"
    description: Optional[str] = None
    duration: Optional[str] = None
    thumbnail: Optional[str] = None
    dash_url: Optional[str] = None
    subtitles: Optional[List[SubtitleInfo]] = None
    is_valid: bool = False

class ProfessionalIQiyiScraper:
    """Professional IQiyi scraper with comprehensive episode extraction"""
    
    def __init__(self, url: str):
        self.url = url
        self.session = requests.Session()
        self.session.verify = False
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
        }
        self._player_data = None

    def _request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """Enhanced request method with better error handling"""
        try:
            kwargs.setdefault('headers', self.headers)
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f'❌ Error making request to {url}: {str(e)}')
            return None

    def get_player_data(self) -> Optional[Dict[str, Any]]:
        """Get and cache player data from the page"""
        if self._player_data:
            return self._player_data

        print("🔍 Fetching player data...")
        response = self._request('get', self.url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})

        if not script_tag:
            print("❌ No __NEXT_DATA__ script tag found")
            return None

        try:
            json_data = script_tag.string.strip()
            self._player_data = json.loads(json_data)
            print("✅ Player data loaded successfully")
            return self._player_data
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON data: {e}")
            return None

    def dash(self):
        """Original dash method from reference implementation"""
        data = self.get_player_data()
        if not data:
            return None

        try:
            log = data['props']['initialProps']['pageProps']['prePlayerData']['ssrlog']
            url_pattern = r'http://intel-cache\.video\.qiyi\.domain/dash\?([^\s]+)'
            urls = re.findall(url_pattern, log)

            if urls:
                return urls[0]
            return None

        except Exception as e:
            print(f"❌ Error in dash method: {e}")
            return None

    def get_m3u8(self) -> Optional[str]:
        """Get M3U8 content from DASH API"""
        dash_query = self.dash()
        if not dash_query:
            return None

        url = f'https://cache.video.iqiyi.com/dash?{dash_query}'
        response = self._request('get', url)

        if response:
            try:
                data = response.json()
                if data.get('code') == 'A00000':
                    video = data['data']['program']['video']
                    for item in video:
                        if 'm3u8' in item:
                            return item['m3u8']
            except Exception as e:
                print(f"❌ Error parsing DASH response: {e}")
        return None

    def _extract_episode_dash_url(self, episode_url: str) -> Optional[str]:
        """Extract DASH URL for a specific episode"""
        try:
            episode_api = ProfessionalIQiyiScraper(episode_url)
            episode_dash_query = episode_api.dash()

            if episode_dash_query:
                return f"https://cache.video.iqiyi.com/dash?{episode_dash_query}"
            else:
                return None

        except Exception as e:
            return None

    def _detect_content_type(self, episode_data: Dict[str, Any]) -> str:
        """Detect if content is episode, preview, or trailer"""
        title = episode_data.get('subTitle', '').lower()
        name = episode_data.get('name', '').lower()

        # Check for preview indicators
        preview_keywords = ['preview', 'trailer', 'teaser', 'promo', 'sneak peek', '预告', '花絮', '预览']
        for keyword in preview_keywords:
            if keyword in title or keyword in name:
                return "preview"

        # Check for episode indicators
        episode_keywords = ['episode', 'ep', '集', 'part']
        for keyword in episode_keywords:
            if keyword in title or keyword in name:
                return "episode"

        # Check episode number pattern
        if re.search(r'\b(episode|ep|第)\s*\d+', title) or re.search(r'\b\d+\s*(集|话)', title):
            return "episode"

        return "episode"  # Default to episode if unclear

    def _extract_description(self, episode_data: Dict[str, Any]) -> Optional[str]:
        """Extract description from episode data with comprehensive fallbacks"""
        description_fields = [
            'description', 'desc', 'summary', 'brief', 'shortDesc', 'longDesc', 'content', 
            'synopsis', 'plot', 'storyline', 'playDesc', 'episodeDesc', 'albumDesc', 
            'tvDesc', 'videoDesc', 'briefDesc', 'introduce', 'playIntroduce', 'videoIntroduce',
            'subTitle', 'name', 'title', 'text', 'info', 'details', 'about'
        ]

        # Try direct fields
        for field in description_fields:
            if field in episode_data and episode_data[field]:
                desc = str(episode_data[field]).strip()
                if desc and desc.lower() not in ['null', 'none', '', 'undefined'] and len(desc) > 3:
                    return desc

        # Try nested objects
        for key, value in episode_data.items():
            if isinstance(value, dict):
                for field in description_fields:
                    if field in value and value[field]:
                        desc = str(value[field]).strip()
                        if desc and desc.lower() not in ['null', 'none', '', 'undefined'] and len(desc) > 3:
                            return desc

        return None

    def _extract_thumbnail(self, episode_data: Dict[str, Any]) -> Optional[str]:
        """Extract thumbnail with multiple fallbacks"""
        thumbnail_fields = [
            'thumbnail', 'poster', 'image', 'cover', 'pic', 'img', 'picUrl', 'imageUrl',
            'posterUrl', 'coverUrl', 'thumbUrl', 'previewImage', 'snapshot', 'vpic', 'rseat',
            'imgUrl', 'picPath', 'imagePath', 'coverImage', 'posterImage', 'thumbImage',
            'previewImg', 'coverPic', 'albumImg', 'episodeImg', 'showImg', 'screencap'
        ]

        # Search direct fields
        for field in thumbnail_fields:
            if episode_data.get(field):
                thumbnail = str(episode_data.get(field)).strip()
                if thumbnail and thumbnail not in ['null', 'none', '']:
                    if any(thumbnail.startswith(prefix) for prefix in ['http://', 'https://', '//', '/', 'data:']):
                        return thumbnail

        # Search nested objects
        for key, value in episode_data.items():
            if isinstance(value, dict):
                for field in thumbnail_fields:
                    if field in value and value[field]:
                        thumbnail = str(value[field]).strip()
                        if thumbnail and thumbnail not in ['null', 'none', '']:
                            if any(thumbnail.startswith(prefix) for prefix in ['http://', 'https://', '//', '/', 'data:']):
                                return thumbnail

        return None

    def get_enhanced_episodes_with_comprehensive_data(self) -> List[EpisodeInfo]:
        """Get comprehensive episode information using both standard and advanced methods"""
        print("🎬 Extracting episodes with comprehensive data...")
        
        # First try the standard playlist method
        standard_episodes = self._get_standard_playlist_episodes()
        
        if len(standard_episodes) > 1:
            print(f"✅ Standard method found {len(standard_episodes)} episodes")
            return standard_episodes
        
        # If standard method fails, try advanced URL pattern generation
        print("🚀 Standard method insufficient, trying advanced URL pattern generation...")
        advanced_episodes = self._get_advanced_pattern_episodes()
        
        if len(advanced_episodes) > 1:
            print(f"✅ Advanced method found {len(advanced_episodes)} episodes")
            return advanced_episodes
        
        # If all else fails, return single episode
        return standard_episodes if standard_episodes else []

    def _get_standard_playlist_episodes(self) -> List[EpisodeInfo]:
        """Get episodes from standard playlist data"""
        data = self.get_player_data()
        if not data:
            return []

        episodes = []
        try:
            episode_data = data['props']['initialState']['play']['cachePlayList']['1']
            print(f"📺 Processing {len(episode_data)} episodes from playlist...")

            for i, episode in enumerate(episode_data, 1):
                episode_title = episode.get('subTitle', f'Episode {i}')
                content_type = self._detect_content_type(episode)

                # Fix URL construction
                album_url = episode.get('albumPlayUrl', '')
                if album_url.startswith('//'):
                    full_url = f"https:{album_url}"
                elif album_url.startswith('/'):
                    full_url = f"https://www.iq.com{album_url}"
                else:
                    full_url = album_url

                # Extract DASH URL and validate
                dash_url = self._extract_episode_dash_url(full_url)
                is_valid = bool(dash_url)

                # Extract description and thumbnail
                description = self._extract_description(episode)
                thumbnail = self._extract_thumbnail(episode)

                episodes.append(EpisodeInfo(
                    title=episode_title,
                    episode_number=i,
                    url=full_url,
                    content_type=content_type,
                    description=description,
                    thumbnail=thumbnail,
                    dash_url=dash_url,
                    is_valid=is_valid
                ))

            return episodes

        except Exception as e:
            print(f"❌ Error in standard playlist method: {e}")
            return []

    def _get_advanced_pattern_episodes(self) -> List[EpisodeInfo]:
        """Get episodes using URL pattern generation (from advanced scraper)"""
        try:
            # Get album info
            data = self.get_player_data()
            if not data:
                return []

            album_info = data.get('props', {}).get('initialState', {}).get('play', {}).get('albumInfo', {})
            total_episodes = album_info.get('total', 0)
            series_name = album_info.get('name', '')

            if total_episodes <= 1:
                return []

            print(f"   Series: {series_name}")
            print(f"   Total Episodes: {total_episodes}")

            # Analyze current URL pattern
            url_match = re.search(r'/play/([^-]+)-episode-(\d+)-([^?]+)', self.url)
            if not url_match:
                print("   ❌ Could not parse URL pattern")
                return []

            series_slug = url_match.group(1)  # lazarus
            current_episode = int(url_match.group(2))  # 1
            video_id_base = url_match.group(3)  # 1l0n170m0qc

            episodes = []

            # Generate URLs for all episodes
            for ep_num in range(1, min(total_episodes + 1, 21)):  # Limit to 20 for safety
                if ep_num == current_episode:
                    episode_url = self.url.split('?')[0]
                else:
                    episode_url = f"https://www.iq.com/play/{series_slug}-episode-{ep_num}-{video_id_base}"

                # Extract DASH URL for validation
                dash_url = self._extract_episode_dash_url(episode_url)
                is_valid = bool(dash_url)

                episode_info = EpisodeInfo(
                    title=f"{series_name} Episode {ep_num}",
                    episode_number=ep_num,
                    url=episode_url,
                    content_type="episode",
                    description=f"Episode {ep_num} of {series_name}",
                    dash_url=dash_url,
                    is_valid=is_valid
                )

                episodes.append(episode_info)
                print(f"   ✅ Episode {ep_num}: Generated URL")

            return episodes

        except Exception as e:
            print(f"❌ Error in advanced pattern method: {e}")
            return []

def scrape_episodes_professional(url: str, max_episodes: int = 100) -> dict:
    """
    Professional episode scraping with comprehensive fallback methods
    """
    try:
        scraper = ProfessionalIQiyiScraper(url)
        episodes = scraper.get_enhanced_episodes_with_comprehensive_data()
        
        if episodes:
            episodes_list = []
            for episode in episodes:
                episodes_list.append({
                    'title': episode.title,
                    'episode_number': episode.episode_number,
                    'url': episode.url,
                    'description': episode.description or '',
                    'duration': episode.duration or '',
                    'thumbnail_url': episode.thumbnail or '',
                    'dash_url': episode.dash_url or '',
                    'is_valid': episode.is_valid
                })
            
            # Count valid episodes
            valid_episodes = len([ep for ep in episodes_list if ep['is_valid']])
            
            return {
                'success': True,
                'total_episodes': len(episodes_list),
                'valid_episodes': valid_episodes,
                'episodes': episodes_list,
                'message': f'Professional scraper extracted {len(episodes_list)} episodes ({valid_episodes} with valid DASH URLs)'
            }
        else:
            return {
                'success': False,
                'error': 'Professional scraper could not extract episodes using any method'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Professional scraper error: {str(e)}'
        }

if __name__ == "__main__":
    # Test dengan Lazarus URL
    test_url = "https://www.iq.com/play/lazarus-episode-1-1l0n170m0qc?lang=en_us"
    result = scrape_episodes_professional(test_url)
    
    print("\n🏁 Professional Scraper Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))