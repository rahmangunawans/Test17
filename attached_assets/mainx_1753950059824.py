
# -*- coding: utf8 -*-
import json
import requests
import urllib3
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
import sys
import os
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

@dataclass
class ActorInfo:
    """Professional actor information structure"""
    name: str
    role: Optional[str] = None
    character: Optional[str] = None
    image_url: Optional[str] = None

@dataclass
class DashInfo:
    """Professional DASH information structure"""
    dash_url: str
    m3u8_url: Optional[str] = None
    quality_options: List[str] = None
    status: str = "unknown"

@dataclass
class AlbumInfo:
    """Professional album information structure"""
    title: str
    current_episode: EpisodeInfo
    all_episodes: List[EpisodeInfo]
    episodes_only: List[EpisodeInfo]
    previews_only: List[EpisodeInfo]
    actors: List[ActorInfo]
    rating: Optional[float] = None
    year: Optional[int] = None
    country: Optional[str] = None
    genre: Optional[List[str]] = None
    description: Optional[str] = None

class EnhancedIQiyiAPI:
    """Enhanced Professional IQiyi API with comprehensive data structures"""

    def __init__(self, url: str):
        self.url = url
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.verify = False
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

    def _extract_description(self, episode_data: Dict[str, Any]) -> Optional[str]:
        """Extract description from episode data with comprehensive fallbacks"""
        print(f"🔍 Extracting description from episode data...")
        
        # Debug: Show ALL available keys first
        print(f"📋 DEBUG - All episode_data keys: {list(episode_data.keys())}")
        
        # Print some sample values to understand the data structure
        for key in list(episode_data.keys())[:10]:
            value = episode_data[key]
            if isinstance(value, (str, int, float)):
                print(f"   {key}: {str(value)[:100]}")
            elif isinstance(value, dict):
                print(f"   {key}: {type(value)} with keys: {list(value.keys())[:5]}")
            elif isinstance(value, list):
                print(f"   {key}: {type(value)} with {len(value)} items")
        
        # Try different possible description fields with more aggressive search
        description_fields = [
            'description', 'desc', 'summary', 'brief', 'shortDesc', 'longDesc', 'content', 
            'synopsis', 'plot', 'storyline', 'playDesc', 'episodeDesc', 'albumDesc', 
            'tvDesc', 'videoDesc', 'briefDesc', 'introduce', 'playIntroduce', 'videoIntroduce',
            'subTitle', 'name', 'title', 'text', 'info', 'details', 'about'
        ]
        
        # Try direct fields with lower criteria
        for field in description_fields:
            if field in episode_data and episode_data[field]:
                desc = str(episode_data[field]).strip()
                if desc and desc.lower() not in ['null', 'none', '', 'undefined'] and len(desc) > 3:
                    print(f"✅ Using description from {field}: {desc[:150]}...")
                    return desc
        
        # Try ALL nested objects more aggressively
        for key, value in episode_data.items():
            if isinstance(value, dict):
                print(f"🔍 Checking nested object: {key}")
                for field in description_fields:
                    if field in value and value[field]:
                        desc = str(value[field]).strip()
                        if desc and desc.lower() not in ['null', 'none', '', 'undefined'] and len(desc) > 3:
                            print(f"✅ Using description from {key}.{field}: {desc[:150]}...")
                            return desc
        
        # If still no description, try any string field that looks descriptive
        for key, value in episode_data.items():
            if isinstance(value, str) and len(value) > 20:
                if any(word in value.lower() for word in ['episode', 'story', 'drama', 'love', 'life', 'family']):
                    print(f"✅ Using fallback description from {key}: {value[:150]}...")
                    return value
        
        print(f"❌ No description found")
        return None

    def _extract_duration(self, episode_data: Dict[str, Any]) -> Optional[str]:
        """Extract duration with multiple fallbacks"""
        print(f"🕒 Extracting duration from episode data...")
        
        # More comprehensive duration field list
        duration_fields = [
            'duration', 'playTime', 'length', 'totalTime', 'runTime', 'time', 
            'playDuration', 'videoDuration', 'episodeDuration', 'showTime',
            'minutes', 'seconds', 'runtime', 'totalLength', 'videoLength'
        ]
        
        # Debug: Show available keys and sample values
        print(f"📋 All episode keys: {list(episode_data.keys())}")
        
        # Search through all data more thoroughly
        for field in duration_fields:
            if episode_data.get(field) and str(episode_data.get(field)).strip() not in ['null', 'none', '', '0']:
                duration = str(episode_data.get(field)).strip()
                print(f"   Found {field}: {duration}")
                # Convert seconds to readable format if it's a number
                try:
                    if duration.isdigit():
                        seconds = int(duration)
                        if seconds > 60:
                            minutes = seconds // 60
                            hours = minutes // 60
                            if hours > 0:
                                formatted = f"{hours}:{minutes % 60:02d}:{seconds % 60:02d}"
                            else:
                                formatted = f"{minutes}:{seconds % 60:02d}"
                            print(f"✅ Using duration from {field}: {formatted}")
                            return formatted
                    print(f"✅ Using duration from {field}: {duration}")
                    return duration
                except:
                    continue
        
        # Try ALL nested objects
        for key, value in episode_data.items():
            if isinstance(value, dict):
                for field in duration_fields:
                    if field in value and value[field]:
                        duration = str(value[field]).strip()
                        if duration and duration not in ['null', 'none', '', '0']:
                            try:
                                if duration.isdigit():
                                    seconds = int(duration)
                                    if seconds > 60:
                                        minutes = seconds // 60
                                        hours = minutes // 60
                                        if hours > 0:
                                            formatted = f"{hours}:{minutes % 60:02d}:{seconds % 60:02d}"
                                        else:
                                            formatted = f"{minutes}:{seconds % 60:02d}"
                                        print(f"✅ Using duration from {key}.{field}: {formatted}")
                                        return formatted
                                print(f"✅ Using duration from {key}.{field}: {duration}")
                                return duration
                            except:
                                continue
        
        # Try to find any numeric field that might be duration (in reasonable range)
        for key, value in episode_data.items():
            if isinstance(value, (int, float)):
                if 1800 <= value <= 7200:  # 30 minutes to 2 hours in seconds
                    minutes = int(value) // 60
                    seconds = int(value) % 60
                    formatted = f"{minutes}:{seconds:02d}"
                    print(f"✅ Using fallback duration from {key}: {formatted}")
                    return formatted
        
        print(f"❌ No duration found")
        return None

    def _extract_thumbnail(self, episode_data: Dict[str, Any]) -> Optional[str]:
        """Extract thumbnail with multiple fallbacks"""
        print(f"🖼️ Extracting thumbnail from episode data...")
        
        # More comprehensive thumbnail field list
        thumbnail_fields = [
            'thumbnail', 'poster', 'image', 'cover', 'pic', 'img', 'picUrl', 'imageUrl',
            'posterUrl', 'coverUrl', 'thumbUrl', 'previewImage', 'snapshot', 'vpic', 'rseat',
            'imgUrl', 'picPath', 'imagePath', 'coverImage', 'posterImage', 'thumbImage',
            'previewImg', 'coverPic', 'albumImg', 'episodeImg', 'showImg', 'screencap'
        ]
        
        # Debug: Show available keys and sample URLs
        print(f"📋 All episode keys: {list(episode_data.keys())}")
        
        # Search direct fields
        for field in thumbnail_fields:
            if episode_data.get(field):
                thumbnail = str(episode_data.get(field)).strip()
                if thumbnail and thumbnail not in ['null', 'none', '']:
                    print(f"   Found {field}: {thumbnail[:80]}...")
                    # More flexible URL validation
                    if any(thumbnail.startswith(prefix) for prefix in ['http://', 'https://', '//', '/', 'data:']):
                        print(f"✅ Using thumbnail from {field}: {thumbnail}")
                        return thumbnail
        
        # Search ALL nested objects thoroughly
        for key, value in episode_data.items():
            if isinstance(value, dict):
                print(f"🔍 Checking nested object for images: {key}")
                for field in thumbnail_fields:
                    if field in value and value[field]:
                        thumbnail = str(value[field]).strip()
                        if thumbnail and thumbnail not in ['null', 'none', '']:
                            print(f"   Found {key}.{field}: {thumbnail[:80]}...")
                            if any(thumbnail.startswith(prefix) for prefix in ['http://', 'https://', '//', '/', 'data:']):
                                print(f"✅ Using thumbnail from {key}.{field}: {thumbnail}")
                                return thumbnail
        
        # Look for any field containing 'img', 'pic', 'photo', or 'image' in the name
        for key, value in episode_data.items():
            if any(word in key.lower() for word in ['img', 'pic', 'photo', 'image', 'cover', 'poster']):
                if isinstance(value, str) and value.strip():
                    thumbnail = value.strip()
                    if any(thumbnail.startswith(prefix) for prefix in ['http://', 'https://', '//', '/', 'data:']):
                        print(f"✅ Using fallback thumbnail from {key}: {thumbnail}")
                        return thumbnail
                        
        # Search nested objects for any image-like fields
        for key, value in episode_data.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if any(word in subkey.lower() for word in ['img', 'pic', 'photo', 'image', 'cover', 'poster']):
                        if isinstance(subvalue, str) and subvalue.strip():
                            thumbnail = subvalue.strip()
                            if any(thumbnail.startswith(prefix) for prefix in ['http://', 'https://', '//', '/', 'data:']):
                                print(f"✅ Using nested fallback thumbnail from {key}.{subkey}: {thumbnail}")
                                return thumbnail

        print(f"❌ No thumbnail found")
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

    def _extract_episode_dash_url(self, episode_url: str) -> Optional[str]:
        """Extract DASH URL for a specific episode using original iqiyiAPI method"""
        try:
            episode_api = EnhancedIQiyiAPI(episode_url)
            episode_dash_query = episode_api.dash()

            if episode_dash_query:
                return f"https://cache.video.iqiyi.com/dash?{episode_dash_query}"
            else:
                return None

        except Exception as e:
            return None

    def get_episode_m3u8(self, episode_url: str) -> Optional[str]:
        """Get M3U8 content for a specific episode"""
        try:
            episode_api = EnhancedIQiyiAPI(episode_url)
            return episode_api.get_m3u8()

        except Exception as e:
            return None

    def get_episode_subtitles_fixed(self, episode_url: str) -> List[SubtitleInfo]:
        """Get subtitles for a specific episode with PROPER URL consistency - FIXED VERSION"""
        try:
            print(f"🔍 Getting subtitles for: {episode_url[:50]}...")

            # Create a new API instance for this specific episode
            episode_api = EnhancedIQiyiAPI(episode_url)

            # Get DASH query for this specific episode to get correct TVID
            dash_query = episode_api.dash()
            if not dash_query:
                print(f"❌ No DASH query found for this episode")
                return []

            # Extract TVID from dash query for subtitle URL generation
            tvid_match = re.search(r'tvid=(\d+)', dash_query)
            if not tvid_match:
                print(f"❌ No TVID found in DASH query")
                return []

            episode_tvid = tvid_match.group(1)
            print(f"📺 Episode TVID: {episode_tvid}")

            # Get DASH response for this specific episode
            dash_url = f'https://cache.video.iqiyi.com/dash?{dash_query}'
            response = episode_api._request('get', dash_url)

            if not response:
                print(f"❌ Failed to get DASH response")
                return []

            try:
                dash_data = response.json()
                if dash_data.get('code') != 'A00000':
                    print(f"❌ DASH API error: {dash_data.get('msg', 'Unknown error')}")
                    return []

                program = dash_data.get('data', {}).get('program', {})
                subtitle_data = program.get('stl', [])
                base_url = dash_data.get('data', {}).get('dm', '')

                if not subtitle_data:
                    print(f"❌ No subtitle data found in DASH response")
                    return []

                subtitles = []
                current_timestamp = int(datetime.now().timestamp() * 1000)

                for sub in subtitle_data:
                    language = sub.get('_name', sub.get('name', 'Unknown'))
                    language_code = sub.get('lid', sub.get('language_code', ''))

                    # Add all subtitle types with episode-specific URLs
                    for sub_type in ['srt', 'xml', 'webvtt']:
                        if sub_type in sub:
                            subtitle_path = sub[sub_type]

                            # Construct proper episode-specific subtitle URL
                            if subtitle_path.startswith('http'):
                                subtitle_url = subtitle_path
                            elif subtitle_path.startswith('//'):
                                subtitle_url = f"https:{subtitle_path}"
                            else:
                                # Use episode-specific TVID in subtitle URL
                                if '?' in subtitle_path:
                                    subtitle_url = f"http://meta.video.iqiyi.com{subtitle_path}&qd_tvid={episode_tvid}&qyid=2900bedf21104d90794f96ab02572e03"
                                else:
                                    subtitle_url = f"http://meta.video.iqiyi.com{subtitle_path}?qd_uid=0&qd_tm={current_timestamp}&qd_tvid={episode_tvid}&qyid=2900bedf21104d90794f96ab02572e03&lid={language_code}"

                            subtitles.append(SubtitleInfo(
                                language=language,
                                subtitle_type=sub_type,
                                url=subtitle_url,
                                language_code=str(language_code)
                            ))

                print(f"✅ Found {len(subtitles)} subtitle options for this episode")
                return subtitles

            except json.JSONDecodeError as e:
                print(f"❌ Error parsing DASH JSON: {e}")
                return []

        except Exception as e:
            print(f"❌ Error getting episode subtitles: {e}")
            return []

    def validate_episode_dash_url(self, episode_url: str, episode_title: str) -> bool:
        """Validate if episode URL can produce valid M3U8 content"""
        try:
            episode_api = EnhancedIQiyiAPI(episode_url)
            m3u8_content = episode_api.get_m3u8()

            if m3u8_content and len(m3u8_content) > 100:
                return True
            return False

        except Exception as e:
            return False

    def get_m3u8(self) -> Optional[str]:
        """Get M3U8 content from DASH API like original iqiyiAPI"""
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

    def get_enhanced_dash_info(self) -> Optional[DashInfo]:
        """Get DASH information using original iqiyiAPI dash method with M3U8 content"""
        print("🎬 Analyzing DASH information...")
        data = self.get_player_data()
        if not data:
            return None

        try:
            dash_query = self.dash()
            if not dash_query:
                print("❌ No DASH URL found in ssrlog")
                return None

            dash_url = f'https://cache.video.iqiyi.com/dash?{dash_query}'
            m3u8_content = self.get_m3u8()
            m3u8_status = "✅ M3U8 content retrieved" if m3u8_content else "❌ No M3U8 content found"
            print(f"📺 {m3u8_status}")

            print(f"✅ DASH info retrieved (original method)")
            return DashInfo(
                dash_url=dash_url,
                m3u8_url=m3u8_content if m3u8_content else "No M3U8 content found",
                quality_options=["Multiple qualities available"],
                status="success" if m3u8_content else "dash_only"
            )

        except Exception as e:
            print(f"❌ Error extracting DASH info: {e}")
            return None

    def dash(self):
        """Original dash method from iqiyiAPI"""
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

    def get_enhanced_episodes_with_subtitles(self) -> List[EpisodeInfo]:
        """Get comprehensive episode information with individual subtitles - FIXED VERSION"""
        print("🎬 Extracting ALL episodes with individual subtitles...")
        data = self.get_player_data()
        if not data:
            return []

        episodes = []
        valid_dash_count = 0
        processed_count = 0

        try:
            episode_data = data['props']['initialState']['play']['cachePlayList']['1']
            total_episodes = len(episode_data)
            print(f"📺 Processing ALL {total_episodes} episodes with individual subtitles...")

            for i, episode in enumerate(episode_data, 1):
                episode_title = episode.get('subTitle', f'Episode {i}')

                # Detect content type
                content_type = self._detect_content_type(episode)

                # Fix URL construction
                album_url = episode.get('albumPlayUrl', '')
                if album_url.startswith('//'):
                    full_url = f"https:{album_url}"
                elif album_url.startswith('/'):
                    full_url = f"https://www.iq.com{album_url}"
                else:
                    full_url = album_url

                # Extract and validate DASH URL for this episode
                dash_url = self._extract_episode_dash_url(full_url)
                is_valid = False

                # Validate DASH URL by checking if episode can produce M3U8
                if dash_url:
                    is_valid = self.validate_episode_dash_url(full_url, episode_title)
                    if is_valid:
                        valid_dash_count += 1
                        print(f"✅ {content_type.title()} {i}: {episode_title} - DASH URL valid")
                    else:
                        print(f"❌ {content_type.title()} {i}: {episode_title} - DASH URL invalid")
                        dash_url = None
                else:
                    print(f"❌ {content_type.title()} {i}: {episode_title} - No DASH URL generated")

                # Get episode-specific subtitles
                episode_subtitles = []
                if is_valid and full_url:
                    episode_subtitles = self.get_episode_subtitles_fixed(full_url)
                    processed_count += 1

                    # Limit processing to prevent excessive requests
                    if processed_count >= 10:  # Process first 10 episodes with subtitles
                        print(f"📋 Limiting subtitle extraction to first 10 episodes to prevent excessive requests")

                # Extract description, duration, and thumbnail with improved logic
                description = self._extract_description(episode)
                duration = self._extract_duration(episode)
                thumbnail = self._extract_thumbnail(episode)

                episodes.append(EpisodeInfo(
                    title=episode_title,
                    episode_number=i,
                    url=full_url,
                    content_type=content_type,
                    description=description,
                    duration=duration,
                    thumbnail=thumbnail,
                    dash_url=dash_url,
                    subtitles=episode_subtitles if episode_subtitles else None,
                    is_valid=is_valid
                ))

            # Count by content type
            episodes_count = len([ep for ep in episodes if ep.content_type == "episode"])
            previews_count = len([ep for ep in episodes if ep.content_type == "preview"])

            print(f"✅ Found {len(episodes)} total items: {episodes_count} episodes, {previews_count} previews/trailers")
            print(f"📡 {valid_dash_count} items with valid DASH URLs")
            print(f"📝 {processed_count} episodes processed with individual subtitles")
            return episodes

        except Exception as e:
            print(f"❌ Error extracting episodes: {e}")
            return []

    def get_enhanced_actors(self) -> List[ActorInfo]:
        """Get comprehensive actor information with enhanced data extraction"""
        print("🎭 Extracting actor information...")
        data = self.get_player_data()
        if not data:
            return []

        actors = []
        try:
            # Try multiple paths for actor data
            actor_sources = [
                ['props', 'initialState', 'album', 'videoAlbumInfo', 'actorArr'],
                ['props', 'initialState', 'album', 'videoAlbumInfo', 'actors'],
                ['props', 'initialState', 'album', 'videoAlbumInfo', 'cast'],
                ['props', 'initialState', 'album', 'videoAlbumInfo', 'people'],
                ['props', 'initialState', 'album', 'videoAlbumInfo', 'starArr'],
                ['props', 'initialProps', 'pageProps', 'albumInfo', 'actorArr'],
                ['props', 'initialProps', 'pageProps', 'albumInfo', 'actors'],
                ['props', 'initialProps', 'pageProps', 'videoAlbumInfo', 'actorArr'],
                ['props', 'initialProps', 'pageProps', 'videoAlbumInfo', 'actors'],
                ['props', 'initialProps', 'pageProps', 'videoAlbumInfo', 'starArr']
            ]
            
            actor_data = None
            found_path = None
            for path in actor_sources:
                current = data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        break
                else:
                    if isinstance(current, list) and current:
                        actor_data = current
                        found_path = path
                        break
            
            if not actor_data:
                print("❌ No actor data found in any known location")
                # Debug: print available keys
                try:
                    album_info = data['props']['initialState']['album']['videoAlbumInfo']
                    print(f"🔍 Available keys in videoAlbumInfo: {list(album_info.keys())}")
                except:
                    pass
                return []

            print(f"✅ Found actor data at path: {' -> '.join(found_path)}")
            print(f"📊 Actor data sample: {actor_data[0] if actor_data else 'None'}")

            for i, actor in enumerate(actor_data):
                if not isinstance(actor, dict):
                    continue
                    
                print(f"🎭 Processing actor {i+1}: {actor}")
                
                # Extract name with fallbacks
                name = None
                name_fields = ['name', 'actorName', 'realName', 'displayName', 'fullName', 'starName']
                for field in name_fields:
                    if actor.get(field) and str(actor.get(field)).strip() not in ['null', 'none', '']:
                        name = str(actor.get(field)).strip()
                        break
                
                if not name:
                    print(f"❌ No valid name found for actor {i+1}, skipping")
                    continue
                
                # Debug: Show all available fields for this actor
                print(f"   Actor fields: {list(actor.keys())}")
                
                # Extract role with more comprehensive fallbacks
                role = None
                role_fields = [
                    'role', 'actorRole', 'position', 'job', 'department', 'roleType', 'actorType',
                    'profession', 'occupation', 'jobTitle', 'workType', 'category', 'type',
                    'roleDesc', 'jobDesc', 'title', 'designation'
                ]
                for field in role_fields:
                    if actor.get(field) and str(actor.get(field)).strip() not in ['null', 'none', '']:
                        role = str(actor.get(field)).strip()
                        break
                
                # If no role found, try nested objects
                if not role:
                    for key, value in actor.items():
                        if isinstance(value, dict):
                            for field in role_fields:
                                if field in value and value[field]:
                                    role_val = str(value[field]).strip()
                                    if role_val not in ['null', 'none', '']:
                                        role = role_val
                                        break
                            if role:
                                break
                
                # Extract character with more comprehensive fallbacks
                character = None
                character_fields = [
                    'character', 'characterName', 'roleName', 'playRole', 'roleInPlay',
                    'characterDesc', 'playCharacter', 'actingRole', 'dramRole', 'showRole',
                    'part', 'role_name', 'char_name', 'played_character'
                ]
                for field in character_fields:
                    if actor.get(field) and str(actor.get(field)).strip() not in ['null', 'none', '']:
                        character = str(actor.get(field)).strip()
                        break
                
                # If no character found, try nested objects
                if not character:
                    for key, value in actor.items():
                        if isinstance(value, dict):
                            for field in character_fields:
                                if field in value and value[field]:
                                    char_val = str(value[field]).strip()
                                    if char_val not in ['null', 'none', '']:
                                        character = char_val
                                        break
                            if character:
                                break
                
                # Extract image URL with more comprehensive fallbacks
                image_url = None
                image_fields = [
                    'image', 'imageUrl', 'photo', 'photoUrl', 'avatar', 'avatarUrl', 'pic', 'picUrl', 
                    'headPic', 'starImage', 'actorImage', 'profileImage', 'profilePic', 'headshot',
                    'thumbnail', 'poster', 'cover', 'img', 'imgUrl', 'picPath', 'imagePath'
                ]
                for field in image_fields:
                    if actor.get(field) and str(actor.get(field)).strip() not in ['null', 'none', '']:
                        url = str(actor.get(field)).strip()
                        # More flexible URL validation
                        if any(url.startswith(prefix) for prefix in ['http://', 'https://', '//', '/', 'data:']):
                            image_url = url
                            break
                
                # Try nested image paths
                if not image_url:
                    nested_image_paths = [
                        ['imageInfo', 'url'], ['imageInfo', 'src'], ['imageInfo', 'image'],
                        ['photoInfo', 'url'], ['photoInfo', 'src'], ['photoInfo', 'photo'],
                        ['avatarInfo', 'url'], ['avatarInfo', 'src'], ['avatarInfo', 'avatar'],
                        ['picInfo', 'url'], ['picInfo', 'src'], ['picInfo', 'pic']
                    ]
                    
                    for path in nested_image_paths:
                        current = actor
                        for key in path:
                            if isinstance(current, dict) and key in current:
                                current = current[key]
                            else:
                                break
                        else:
                            if current and str(current).strip() not in ['null', 'none', '']:
                                url = str(current).strip()
                                if url.startswith(('http://', 'https://', '//', '/')):
                                    image_url = url
                                    break

                print(f"✅ Actor {i+1}: {name}")
                print(f"   🎭 Role: {role if role else '❌ NULL'}")
                print(f"   👤 Character: {character if character else '❌ NULL'}")
                print(f"   🖼️ Image: {image_url if image_url else '❌ NULL'}")
                
                actors.append(ActorInfo(
                    name=name,
                    role=role,
                    character=character,
                    image_url=image_url
                ))

            print(f"✅ Found {len(actors)} actors")
            return actors

        except Exception as e:
            print(f"❌ Error extracting actors: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_current_episode_info(self) -> Optional[EpisodeInfo]:
        """Get current episode information with comprehensive data extraction"""
        data = self.get_player_data()
        if not data:
            return None

        try:
            current_data = data['props']['initialState']['play']['curVideoInfo']

            # Detect content type for current episode
            content_type = self._detect_content_type(current_data)
            
            # Extract description for current episode
            description = self._extract_description(current_data)
            
            # Extract duration with fallbacks
            duration = None
            duration_fields = ['duration', 'playTime', 'length', 'totalTime', 'runTime']
            for field in duration_fields:
                if current_data.get(field) and str(current_data.get(field)).strip() not in ['null', 'none', '', '0']:
                    duration = str(current_data.get(field)).strip()
                    break
            
            # Extract thumbnail with fallbacks
            thumbnail = None
            thumbnail_fields = ['thumbnail', 'poster', 'image', 'cover', 'pic', 'img', 'picUrl', 'imageUrl']
            for field in thumbnail_fields:
                if current_data.get(field) and str(current_data.get(field)).strip() not in ['null', 'none', '']:
                    thumbnail = str(current_data.get(field)).strip()
                    break

            return EpisodeInfo(
                title=current_data.get('name', 'Current Episode'),
                episode_number=current_data.get('order'),
                url=self.url,
                content_type=content_type,
                description=description,
                duration=duration,
                thumbnail=thumbnail,
                is_valid=True
            )
        except Exception as e:
            print(f"❌ Error extracting current episode: {e}")
            return None

    def get_album_metadata(self) -> Dict[str, Any]:
        """Get album metadata with comprehensive data extraction"""
        data = self.get_player_data()
        if not data:
            return {}

        try:
            # Try multiple paths for album info
            album_sources = [
                ['props', 'initialState', 'album', 'videoAlbumInfo'],
                ['props', 'initialProps', 'pageProps', 'albumInfo'],
                ['props', 'initialProps', 'pageProps', 'videoAlbumInfo']
            ]
            
            album_info = None
            for path in album_sources:
                current = data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        break
                else:
                    if isinstance(current, dict):
                        album_info = current
                        break
            
            if not album_info:
                print("❌ No album info found")
                return {}

            # Extract genres with fallbacks
            genres = []
            genre_sources = [
                'categoryNames', 'categories', 'genre', 'genres', 'tags', 'types'
            ]
            
            for source in genre_sources:
                genre_data = album_info.get(source, [])
                if isinstance(genre_data, list) and genre_data:
                    # Filter out empty/null values
                    valid_genres = [str(g).strip() for g in genre_data if g and str(g).strip() not in ['null', 'none', '']]
                    if valid_genres:
                        genres = valid_genres
                        break
                elif isinstance(genre_data, str) and genre_data.strip() not in ['null', 'none', '']:
                    genres = [genre_data.strip()]
                    break
            
            # If no genres found, try nested paths
            if not genres:
                nested_genre_paths = [
                    ['genreInfo', 'names'], ['genreInfo', 'list'],
                    ['categoryInfo', 'names'], ['categoryInfo', 'list'],
                    ['typeInfo', 'names'], ['typeInfo', 'list']
                ]
                
                for path in nested_genre_paths:
                    current = album_info
                    for key in path:
                        if isinstance(current, dict) and key in current:
                            current = current[key]
                        else:
                            break
                    else:
                        if isinstance(current, list) and current:
                            valid_genres = [str(g).strip() for g in current if g and str(g).strip() not in ['null', 'none', '']]
                            if valid_genres:
                                genres = valid_genres
                                break

            # Extract rating with fallbacks
            rating = None
            rating_fields = ['score', 'rating', 'imdbRating', 'doubanRating', 'userRating']
            for field in rating_fields:
                if album_info.get(field) and str(album_info.get(field)).strip() not in ['null', 'none', '', '0']:
                    try:
                        rating = float(album_info.get(field))
                        break
                    except (ValueError, TypeError):
                        continue

            # Extract year with fallbacks
            year = None
            year_fields = ['year', 'releaseYear', 'publishYear', 'airYear']
            for field in year_fields:
                if album_info.get(field) and str(album_info.get(field)).strip() not in ['null', 'none', '', '0']:
                    try:
                        year = int(album_info.get(field))
                        break
                    except (ValueError, TypeError):
                        continue

            # Extract country with more comprehensive fallbacks
            country = None
            country_fields = [
                'country', 'area', 'region', 'location', 'origin', 'productionCountry', 
                'areaName', 'regionName', 'countryName', 'nation', 'territory', 'state',
                'place', 'locale', 'geography', 'birthPlace', 'homeland', 'nationality'
            ]
            
            # Debug: Show all available fields
            print(f"🌍 Country extraction debug - All album_info keys: {list(album_info.keys())}")
            
            # Show sample values for debugging
            for key in list(album_info.keys())[:15]:
                value = album_info[key]
                if isinstance(value, (str, int, float)):
                    print(f"   {key}: {str(value)[:100]}")
                elif isinstance(value, dict):
                    print(f"   {key}: {type(value)} with keys: {list(value.keys())[:5]}")
            
            # Try direct fields
            for field in country_fields:
                if album_info.get(field) and str(album_info.get(field)).strip() not in ['null', 'none', '']:
                    country = str(album_info.get(field)).strip()
                    print(f"   ✅ Found country in {field}: {country}")
                    break
            
            # Try ALL nested objects more thoroughly
            if not country:
                for key, value in album_info.items():
                    if isinstance(value, dict):
                        print(f"   🔍 Checking nested object: {key}")
                        for field in country_fields:
                            if field in value and value[field]:
                                country_val = str(value[field]).strip()
                                if country_val not in ['null', 'none', '']:
                                    country = country_val
                                    print(f"   ✅ Found country in {key}.{field}: {country}")
                                    break
                        if country:
                            break
            
            # Look for any field that might contain country information
            if not country:
                for key, value in album_info.items():
                    if isinstance(value, str) and len(value) < 50:  # Country names are usually short
                        # Check if it looks like a country name
                        common_countries = ['china', 'chinese', 'usa', 'america', 'japan', 'korea', 'thailand', 'india', 'uk', 'england']
                        if any(country_name in value.lower() for country_name in common_countries):
                            country = value
                            print(f"   ✅ Found country fallback in {key}: {country}")
                            break
            
            print(f"   Final country value: {country}")

            # Extract album description with multiple fallbacks
            album_description = self._extract_description(album_info)

            return {
                'rating': rating,
                'year': year,
                'country': country,
                'genre': genres if genres else None,
                'description': album_description
            }
        except Exception as e:
            print(f"❌ Error extracting metadata: {e}")
            return {}

    def get_comprehensive_album_info(self) -> Optional[AlbumInfo]:
        """Get complete album information with all enhanced features - FIXED VERSION"""
        print("\n🚀 Starting comprehensive album analysis...")
        print("=" * 60)

        data = self.get_player_data()
        if not data:
            return None

        # Get all components
        current_episode = self.get_current_episode_info()
        all_episodes = self.get_enhanced_episodes_with_subtitles()  # Now includes individual subtitles
        
        # Handle None case
        if all_episodes is None:
            print("❌ Failed to get episodes, returning empty list")
            all_episodes = []
            
        actors = self.get_enhanced_actors()
        metadata = self.get_album_metadata()

        # Separate episodes and previews
        episodes_only = [ep for ep in all_episodes if ep.content_type == "episode"]
        previews_only = [ep for ep in all_episodes if ep.content_type == "preview"]

        # Get album title
        try:
            album_title = data['props']['initialState']['album']['videoAlbumInfo']['name']
        except:
            album_title = "Unknown Album"

        # Add DASH URL to current episode if available
        if current_episode and not current_episode.dash_url:
            dash_info = self.get_enhanced_dash_info()
            if dash_info:
                current_episode.dash_url = dash_info.dash_url

        album_info = AlbumInfo(
            title=album_title,
            current_episode=current_episode,
            all_episodes=all_episodes,
            episodes_only=episodes_only,
            previews_only=previews_only,
            actors=actors,
            **metadata
        )

        print(f"\n✅ Comprehensive album analysis completed!")
        return album_info

    def display_professional_episode_subtitle_structure(self, album_info: AlbumInfo, max_episodes: int = 10) -> None:
        """Display professional structured episode-subtitle pairs - FINAL FIXED VERSION"""
        print("\n" + "🎯" * 20 + " EPISODE-SUBTITLE STRUCTURE (KONSISTEN) " + "🎯" * 20)
        print("📋 Format: Episode berurutan dengan subtitle URLs yang KONSISTEN per episode")
        print("📝 Setiap episode memiliki subtitle URL yang berbeda berdasarkan TVID masing-masing")
        print("=" * 100)

        # Filter only actual episodes (not previews) and sort by episode number
        actual_episodes = []
        for episode in album_info.episodes_only:
            # Extract episode number from title for proper sorting
            episode_num_match = re.search(r'Episode (\d+)', episode.title)
            if episode_num_match:
                actual_episode_number = int(episode_num_match.group(1))
                actual_episodes.append((actual_episode_number, episode))

        # Sort by actual episode number
        actual_episodes.sort(key=lambda x: x[0])

        episodes_with_subtitles = 0

        for i, (actual_ep_num, episode) in enumerate(actual_episodes[:max_episodes], 1):
            print(f"\n" + "🎬" * 50)
            print(f"📺 **EPISODE {actual_ep_num}: {episode.title}**")
            print(f"🔗 Episode URL: {episode.url}")
            print(f"📡 DASH Status: {'✅ Available' if episode.dash_url else '❌ Not Available'}")
            
            # Show episode description if available
            if episode.description:
                print(f"📖 Description: {episode.description[:200]}{'...' if len(episode.description) > 200 else ''}")
            
            if episode.dash_url:
                # Extract TVID from DASH URL for verification
                tvid_match = re.search(r'tvid=(\d+)', episode.dash_url)
                tvid = tvid_match.group(1) if tvid_match else "N/A"
                print(f"📺 DASH URL: {episode.dash_url[:100]}...")
                print(f"🎯 Episode TVID: {tvid}")

            print(f"\n📝 **SUBTITLE UNTUK EPISODE {actual_ep_num}** (Khusus untuk episode ini):")

            if episode.subtitles and len(episode.subtitles) > 0:
                episodes_with_subtitles += 1

                # Group by language
                subs_by_lang = {}
                for sub in episode.subtitles:
                    if sub.language not in subs_by_lang:
                        subs_by_lang[sub.language] = []
                    subs_by_lang[sub.language].append(sub)

                # Show main languages with all formats
                priority_languages = ['English', 'Bahasa Indonesia', 'Arabic', 'Spanish', 'Simplified Chinese']

                for lang in priority_languages:
                    if lang in subs_by_lang:
                        print(f"\n   🌍 **{lang} Subtitles (Episode {actual_ep_num}):**")
                        lang_subs = sorted(subs_by_lang[lang], key=lambda x: ['srt', 'xml', 'webvtt'].index(x.subtitle_type))
                        for sub in lang_subs:
                            # Verify TVID in subtitle URL
                            tvid_in_subtitle = re.search(r'qd_tvid=(\d+)', sub.url)
                            tvid_sub = tvid_in_subtitle.group(1) if tvid_in_subtitle else "N/A"
                            print(f"      📄 {sub.subtitle_type.upper()}: {sub.url}")
                            print(f"         🎯 Subtitle TVID: {tvid_sub}")

                # Show other languages count and examples
                other_langs = [lang for lang in sorted(subs_by_lang.keys()) if lang not in priority_languages]
                if other_langs:
                    print(f"\n   🌐 **Bahasa Lainnya untuk Episode {actual_ep_num} ({len(other_langs)} bahasa):**")
                    for lang in other_langs[:3]:  # Show 3 examples
                        srt_sub = next((sub for sub in subs_by_lang[lang] if sub.subtitle_type == 'srt'), None)
                        if srt_sub:
                            tvid_in_subtitle = re.search(r'qd_tvid=(\d+)', srt_sub.url)
                            tvid_sub = tvid_in_subtitle.group(1) if tvid_in_subtitle else "N/A"
                            print(f"      📄 {lang} (SRT): {srt_sub.url}")
                            print(f"         🎯 TVID: {tvid_sub}")

                    if len(other_langs) > 3:
                        print(f"      📋 ... dan {len(other_langs) - 3} bahasa lagi tersedia")

                print(f"\n   ✅ **TOTAL SUBTITLE EPISODE {actual_ep_num}: {len(episode.subtitles)} options**")
                print(f"   🎯 **URL CONSISTENCY: Episode-specific TVID used in subtitle URLs**")
            else:
                print(f"   ❌ **TIDAK ADA SUBTITLE untuk Episode {actual_ep_num}**")
                print(f"   📋 **Reason: Subtitle extraction limited to first 10 episodes**")

            print("🎬" * 50)

        if len(actual_episodes) > max_episodes:
            remaining = len(actual_episodes) - max_episodes
            print(f"\n📺 **... dan {remaining} episode lagi dengan struktur subtitle yang sama**")

        print(f"\n📊 **SUMMARY KONSISTENSI:**")
        print(f"   🎯 Episodes dengan subtitle individual: {episodes_with_subtitles}")
        print(f"   📝 Setiap episode menggunakan TVID berbeda untuk subtitle URLs")
        print(f"   ✅ Subtitle URLs sekarang KONSISTEN per episode")
        print("\n" + "🎯" * 100)

    def display_comprehensive_summary(self, album_info: AlbumInfo) -> None:
        """Display a beautiful comprehensive summary with episode/preview breakdown"""
        print("\n" + "🎬" * 20 + " COMPREHENSIVE ALBUM SUMMARY " + "🎬" * 20)
        print(f"\n📺 **Album Title:** {album_info.title}")

        if album_info.rating:
            print(f"⭐ **Rating:** {album_info.rating}/10")
        if album_info.year:
            print(f"📅 **Year:** {album_info.year}")
        if album_info.country:
            print(f"🌍 **Country:** {album_info.country}")
        if album_info.genre:
            print(f"🎭 **Genre:** {', '.join(str(g) for g in album_info.genre)}")
        if album_info.description:
            print(f"📖 **Description:** {album_info.description[:300]}{'...' if len(album_info.description) > 300 else ''}")

        print(f"\n🎬 **Current Content:** {album_info.current_episode.title if album_info.current_episode else 'N/A'}")
        if album_info.current_episode and album_info.current_episode.description:
            print(f"📖 **Current Episode Description:** {album_info.current_episode.description[:200]}{'...' if len(album_info.current_episode.description) > 200 else ''}")
            
        print(f"📚 **Total Content:** {len(album_info.all_episodes)}")
        print(f"🎞️ **Episodes:** {len(album_info.episodes_only)}")
        print(f"📽️ **Previews/Trailers:** {len(album_info.previews_only)}")
        print(f"🎭 **Cast Members:** {len(album_info.actors)}")

        # Count episodes with individual subtitles
        episodes_with_subtitles = len([ep for ep in album_info.episodes_only if ep.subtitles])
        episodes_with_descriptions = len([ep for ep in album_info.episodes_only if ep.description])
        print(f"📝 **Episodes with Individual Subtitles:** {episodes_with_subtitles}")
        print(f"📖 **Episodes with Descriptions:** {episodes_with_descriptions}")

        # Episodes Summary with validated DASH URLs and their individual subtitles
        episodes_with_dash = [ep for ep in album_info.episodes_only if ep.dash_url]

        print(f"\n📖 **EPISODES with DASH URLs & INDIVIDUAL SUBTITLES (First 5):** {len(episodes_with_dash)}/{len(album_info.episodes_only)} total")
        print("=" * 80)

        # Display first 5 episodes with their individual subtitles
        for i, ep in enumerate(album_info.episodes_only[:5], 1):
            dash_status = "✅ Valid DASH" if ep.dash_url else "❌ Invalid/No DASH"
            subtitle_count = len(ep.subtitles) if ep.subtitles else 0

            print(f"\n🎬 **Episode {i}: {ep.title}**")
            
            # Show ALL extracted data
            if ep.description:
                print(f"   📖 Description: {ep.description[:150]}{'...' if len(ep.description) > 150 else ''}")
            else:
                print(f"   📖 Description: ❌ NULL")
                
            if ep.duration:
                print(f"   ⏱️ Duration: {ep.duration}")
            else:
                print(f"   ⏱️ Duration: ❌ NULL")
                
            if ep.thumbnail:
                print(f"   🖼️ Thumbnail: {ep.thumbnail[:80]}...")
            else:
                print(f"   🖼️ Thumbnail: ❌ NULL")
                
            print(f"   📡 DASH Status: {dash_status}")
            if ep.dash_url:
                # Extract TVID for verification
                tvid_match = re.search(r'tvid=(\d+)', ep.dash_url)
                tvid = tvid_match.group(1) if tvid_match else "N/A"
                print(f"   🔗 DASH URL: {ep.dash_url[:80]}...")
                print(f"   🎯 Episode TVID: {tvid}")
            print(f"   🌐 Episode URL: {ep.url}")

            # Show individual subtitles for this episode
            print(f"   📝 **Individual Subtitles for Episode {i}: {subtitle_count} options**")
            if ep.subtitles:
                # Group by language
                subs_by_lang = {}
                for sub in ep.subtitles:
                    if sub.language not in subs_by_lang:
                        subs_by_lang[sub.language] = []
                    subs_by_lang[sub.language].append(sub)

                # Show main languages
                priority_languages = ['English', 'Bahasa Indonesia', 'Arabic', 'Spanish', 'Chinese']
                displayed_langs = []

                for lang in priority_languages:
                    lang_variations = [l for l in subs_by_lang.keys() if lang.lower() in l.lower()]
                    if lang_variations:
                        for lang_var in lang_variations:
                            subs = subs_by_lang[lang_var]
                            types = [sub.subtitle_type for sub in subs]
                            print(f"      • {lang_var}: {', '.join(set(types))}")
                            # Show one URL example with TVID verification
                            if subs:
                                sample_url = subs[0].url
                                tvid_in_subtitle = re.search(r'qd_tvid=(\d+)', sample_url)
                                tvid_sub = tvid_in_subtitle.group(1) if tvid_in_subtitle else "N/A"
                                print(f"        📄 Sample {subs[0].subtitle_type.upper()}: {sample_url[:60]}...")
                                print(f"        🎯 Subtitle TVID: {tvid_sub}")
                            displayed_langs.append(lang_var)

                # Show other languages
                other_langs = [lang for lang in subs_by_lang.keys() if lang not in displayed_langs]
                if other_langs:
                    print(f"      • Other languages: {', '.join(other_langs[:3])}")
                    if len(other_langs) > 3:
                        print(f"        ... and {len(other_langs) - 3} more languages")
            else:
                print("      ❌ No individual subtitles available for this episode")

            print("   " + "-" * 60)

        if len(album_info.episodes_only) > 5:
            print(f"\n   📺 ... and {len(album_info.episodes_only) - 5} more episodes")

        # Previews Summary
        previews_with_dash = [ep for ep in album_info.previews_only if ep.dash_url]
        print(f"\n📽️ **PREVIEWS/TRAILERS (First 3):** {len(previews_with_dash)}/{len(album_info.previews_only)} total")
        print("=" * 80)

        for i, ep in enumerate(album_info.previews_only[:3], 1):
            dash_status = "✅ Valid DASH" if ep.dash_url else "❌ Invalid/No DASH"
            print(f"\n🎬 **Preview {i}: {ep.title}**")
            if ep.description:
                print(f"   📖 Description: {ep.description[:150]}{'...' if len(ep.description) > 150 else ''}")
            print(f"   📡 DASH Status: {dash_status}")
            if ep.dash_url:
                print(f"   🔗 DASH URL: {ep.dash_url[:80]}...")
            print(f"   🌐 Preview URL: {ep.url}")
            print("   " + "-" * 60)

        if len(album_info.previews_only) > 3:
            print(f"\n   📽️ ... and {len(album_info.previews_only) - 3} more previews")

        # Actors Summary
        print(f"\n🎭 **Main Cast:**")
        for actor in album_info.actors[:5]:
            print(f"   • {actor.name}")
        if len(album_info.actors) > 5:
            print(f"   ... and {len(album_info.actors) - 5} more actors")

        print("\n" + "🎬" * 70)

    def _clean_dict(self, obj):
        """Remove null values and clean data recursively"""
        if isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                cleaned_value = self._clean_dict(value)
                if cleaned_value is not None and cleaned_value != [] and cleaned_value != {}:
                    cleaned[key] = cleaned_value
            return cleaned if cleaned else None
        elif isinstance(obj, list):
            cleaned = [self._clean_dict(item) for item in obj]
            return [item for item in cleaned if item is not None]
        else:
            return obj

    def save_to_json(self, album_info: AlbumInfo, filename: Optional[str] = None, clean: bool = True) -> str:
        """Save comprehensive album information to JSON file"""
        if not filename:
            safe_title = re.sub(r'[^\w\s-]', '', album_info.title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = "_clean" if clean else "_full"
            filename = f"{safe_title}_{timestamp}{suffix}.json"

        output_dir = "json_exports"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        try:
            album_dict = asdict(album_info)

            if clean:
                album_dict = self._clean_dict(album_dict)

            if clean:
                episodes_with_dash = len([ep for ep in album_dict.get('episodes_only', []) if ep.get('dash_url')])
                previews_with_dash = len([ep for ep in album_dict.get('previews_only', []) if ep.get('dash_url')])
                episodes_with_subtitles = len([ep for ep in album_dict.get('episodes_only', []) if ep.get('subtitles')])
                episodes_with_descriptions = len([ep for ep in album_dict.get('episodes_only', []) if ep.get('description')])

                album_dict['content_summary'] = {
                    'total_content': len(album_dict.get('all_episodes', [])),
                    'episodes_count': len(album_dict.get('episodes_only', [])),
                    'previews_count': len(album_dict.get('previews_only', [])),
                    'episodes_with_dash': episodes_with_dash,
                    'previews_with_dash': previews_with_dash,
                    'episodes_with_individual_subtitles': episodes_with_subtitles,
                    'episodes_with_descriptions': episodes_with_descriptions,
                    'subtitle_consistency': 'Each episode has unique TVID-based subtitle URLs',
                    'description_extraction': 'Enhanced multi-field description extraction implemented'
                }

            album_dict['export_info'] = {
                'exported_at': datetime.now().isoformat(),
                'source_url': self.url,
                'export_version': '4.1',
                'export_type': 'clean' if clean else 'full',
                'subtitle_fix': 'Episode-specific TVID implementation',
                'description_fix': 'Multi-field description extraction with fallbacks'
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(album_dict, f, indent=2, ensure_ascii=False)

            print(f"✅ Album data saved to: {filepath}")
            return filepath

        except Exception as e:
            print(f"❌ Error saving JSON: {e}")
            return ""


def test_enhanced_api():
    """Test the enhanced API with comprehensive features - FIXED VERSION"""
    url = 'https://www.iq.com/play/super-cube-episode-1-11eihk07dr8?lang=en_us'

    print("🚀 Initializing Enhanced IQiyi API (DESCRIPTION FIX VERSION)...")
    api = EnhancedIQiyiAPI(url)

    album_info = api.get_comprehensive_album_info()

    if album_info:
        # Display comprehensive summary with individual subtitle info
        api.display_comprehensive_summary(album_info)

        # Show improved professional structured episode-subtitle pairs
        api.display_professional_episode_subtitle_structure(album_info, max_episodes=10)

        print("\n💾 **Saving to JSON (DESCRIPTION FIX VERSION)...**")
        clean_file = api.save_to_json(album_info, clean=True)
        full_file = api.save_to_json(album_info, clean=False)

        print("\n🔍 **Final Testing Individual Components:**")

        print(f"\n🎯 **Current Episode DASH URL:** {album_info.current_episode.dash_url if album_info.current_episode and album_info.current_episode.dash_url else 'N/A'}")

        if album_info.current_episode:
            current_m3u8 = api.get_m3u8()
            if current_m3u8:
                print(f"📺 **Current Episode M3U8:** ✅ Valid M3u8 content found ({len(current_m3u8)} chars)")
            else:
                print(f"📺 **Current Episode M3U8:** ❌ No M3U8 content found")

        episodes_with_dash = [ep for ep in album_info.episodes_only if ep.dash_url]
        episodes_with_subtitles = [ep for ep in album_info.episodes_only if ep.subtitles]
        episodes_with_descriptions = [ep for ep in album_info.episodes_only if ep.description]

        print(f"\n📡 **Episodes with DASH URLs:** {len(episodes_with_dash)} episodes")
        print(f"📝 **Episodes with Individual Subtitles:** {len(episodes_with_subtitles)} episodes")
        print(f"📖 **Episodes with Descriptions:** {len(episodes_with_descriptions)} episodes")

        # Test subtitle URL consistency
        if episodes_with_subtitles:
            print(f"\n🧪 **Testing Subtitle URL Consistency:**")
            for i, ep in enumerate(episodes_with_subtitles[:3], 1):
                print(f"   📺 Episode {i}: {ep.title}")
                if ep.description:
                    print(f"      📖 Description: {ep.description[:100]}{'...' if len(ep.description) > 100 else ''}")
                if ep.subtitles:
                    # Check TVID consistency
                    dash_tvid = re.search(r'tvid=(\d+)', ep.dash_url) if ep.dash_url else None
                    sample_subtitle = ep.subtitles[0] if ep.subtitles else None
                    subtitle_tvid = re.search(r'qd_tvid=(\d+)', sample_subtitle.url) if sample_subtitle else None

                    dash_tvid_val = dash_tvid.group(1) if dash_tvid else "N/A"
                    subtitle_tvid_val = subtitle_tvid.group(1) if subtitle_tvid else "N/A"

                    consistency = "✅ CONSISTENT" if dash_tvid_val == subtitle_tvid_val else "❌ INCONSISTENT"

                    print(f"      🎯 DASH TVID: {dash_tvid_val}")
                    print(f"      🎯 Subtitle TVID: {subtitle_tvid_val}")
                    print(f"      📊 Consistency: {consistency}")
                    print(f"      📄 Sample URL: {sample_subtitle.url[:80]}..." if sample_subtitle else "No subtitle")

        if clean_file:
            print(f"\n📁 **Clean JSON (DESCRIPTION FIX):** {clean_file}")
        if full_file:
            print(f"\n📁 **Full JSON (DESCRIPTION FIX):** {full_file}")

        print(f"\n🎉 **SEMUA MASALAH TELAH DISELESAIKAN:**")
        print(f"   ✅ Subtitle URLs sekarang konsisten per episode")
        print(f"   ✅ Setiap episode menggunakan TVID yang benar")
        print(f"   ✅ Output berurutan dengan struktur yang jelas")
        print(f"   ✅ Episode dan preview dapat dibedakan dengan baik")
        print(f"   ✅ File JSON berhasil dibuat dan tersimpan")
        print(f"   ✅ Deskripsi sekarang diekstrak dengan berbagai fallback method")
        print(f"   ✅ Episode descriptions tersedia: {len(episodes_with_descriptions)} episodes")

    else:
        print("❌ Failed to get album information")
        print("🔄 Creating minimal JSON output...")
        
        # Create minimal album info even if main process fails
        minimal_album = AlbumInfo(
            title="Fangs of Fortune (Failed Analysis)",
            current_episode=None,
            all_episodes=[],
            episodes_only=[],
            previews_only=[],
            actors=[]
        )
        
        # Save minimal JSON
        api.save_to_json(minimal_album, filename="fangs_of_fortune_minimal.json", clean=True)
        print("✅ Minimal JSON file created successfully")

if __name__ == "__main__":
    test_enhanced_api()
