# -*- coding: utf8 -*-
import json
import requests
import urllib3
import re
import time
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

    _BID_TAGS = {
        '200': '360P',
        '300': '480P',
        '500': '720P',
        '600': '1080P',
    }

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

    def get_album_info(self) -> Optional[AlbumInfo]:
        """Get comprehensive album information with all episodes"""
        player_data = self.get_player_data()
        if not player_data:
            return None

        try:
            props = player_data.get('props', {})
            page_props = props.get('pageProps', {})
            
            # Get current episode info
            current_episode_data = page_props.get('episodeInfo', {})
            current_episode = self._parse_episode_info(current_episode_data)
            
            # Get all episodes from album
            album_data = page_props.get('albumInfo', {})
            episodes_data = album_data.get('episodes', [])
            
            all_episodes = []
            episodes_only = []
            previews_only = []
            
            for ep_data in episodes_data:
                episode = self._parse_episode_info(ep_data)
                all_episodes.append(episode)
                
                if episode.content_type == "episode":
                    episodes_only.append(episode)
                elif episode.content_type == "preview":
                    previews_only.append(episode)
            
            # Get actors info
            actors = self._parse_actors_info(album_data.get('actors', []))
            
            album_info = AlbumInfo(
                title=album_data.get('title', 'Unknown Title'),
                current_episode=current_episode,
                all_episodes=all_episodes,
                episodes_only=episodes_only,
                previews_only=previews_only,
                actors=actors,
                rating=album_data.get('rating'),
                year=album_data.get('year'),
                country=album_data.get('country'),
                genre=album_data.get('genre', []),
                description=album_data.get('description')
            )
            
            return album_info
            
        except Exception as e:
            print(f"❌ Error parsing album info: {e}")
            return None

    def _parse_episode_info(self, episode_data: Dict[str, Any]) -> EpisodeInfo:
        """Parse episode information from data"""
        title = episode_data.get('title', 'Unknown Episode')
        episode_number = episode_data.get('episode_number') or episode_data.get('order')
        url = episode_data.get('url', '')
        
        # Determine content type
        content_type = "episode"
        if any(word in title.lower() for word in ['preview', 'trailer', 'teaser']):
            content_type = "preview"
        
        return EpisodeInfo(
            title=title,
            episode_number=episode_number,
            url=url,
            content_type=content_type,
            description=episode_data.get('description'),
            duration=episode_data.get('duration'),
            thumbnail=episode_data.get('thumbnail'),
            is_valid=bool(url)
        )

    def _parse_actors_info(self, actors_data: List[Dict[str, Any]]) -> List[ActorInfo]:
        """Parse actors information from data"""
        actors = []
        for actor_data in actors_data:
            actor = ActorInfo(
                name=actor_data.get('name', ''),
                role=actor_data.get('role'),
                character=actor_data.get('character'),
                image_url=actor_data.get('image_url')
            )
            actors.append(actor)
        return actors

# Wrapper functions for backward compatibility with admin.py
def scrape_single_episode(iqiyi_url):
    """Scrape single episode - wrapper for admin compatibility"""
    try:
        api = EnhancedIQiyiAPI(iqiyi_url)
        album_info = api.get_album_info()
        
        if album_info and album_info.current_episode:
            episode = album_info.current_episode
            return {
                'success': True,
                'data': {
                    'episode_number': str(episode.episode_number or 1),
                    'title': episode.title,
                    'url': episode.url,
                    'server_1_url': '',  # Empty for Server 1 (M3U8)
                    'server_2_url': episode.url,  # Use as embed URL for Server 2
                    'server_3_url': '',  # Server 3 disabled
                    'thumbnail_url': episode.thumbnail or '',
                    'description': episode.description or '',
                    'duration': episode.duration or '',
                    'release_date': ''
                },
                'message': 'Single episode scraped successfully'
            }
        else:
            return {
                'success': False,
                'error': 'Failed to extract episode information'
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Scraping failed: {str(e)}'
        }

def scrape_all_episodes_playlist(iqiyi_url, max_episodes=20):
    """Scrape playlist episodes - wrapper for admin compatibility"""
    try:
        api = EnhancedIQiyiAPI(iqiyi_url)
        album_info = api.get_album_info()
        
        if album_info and album_info.all_episodes:
            episodes = []
            for i, episode in enumerate(album_info.episodes_only[:max_episodes]):
                episodes.append({
                    'episode_number': str(episode.episode_number or i + 1),
                    'title': episode.title,
                    'url': episode.url,
                    'server_1_url': '',  # Empty for Server 1 (M3U8)
                    'server_2_url': episode.url,  # Use as embed URL for Server 2
                    'server_3_url': '',  # Server 3 disabled
                    'thumbnail_url': episode.thumbnail or '',
                    'description': episode.description or '',
                    'duration': episode.duration or '',
                    'release_date': ''
                })
            
            return {
                'success': True,
                'total_episodes': len(episodes),
                'valid_episodes': len(episodes),
                'episodes': episodes,
                'message': f"Successfully scraped {len(episodes)} episodes",
                'method': 'enhanced_professional_scraper'
            }
        else:
            # Fallback: try to generate episodes based on URL pattern
            episodes = []
            url_match = re.search(r'/play/([a-zA-Z0-9]+)', iqiyi_url)
            if url_match:
                base_id = url_match.group(1)
                for i in range(1, min(max_episodes + 1, 21)):
                    episode_url = f"https://www.iq.com/play/{base_id}?episode={i}"
                    episodes.append({
                        'episode_number': str(i),
                        'title': f"Episode {i}",
                        'url': episode_url,
                        'server_1_url': '',
                        'server_2_url': episode_url,
                        'server_3_url': '',
                        'thumbnail_url': '',
                        'description': '',
                        'duration': '',
                        'release_date': ''
                    })
                
                return {
                    'success': True,
                    'total_episodes': len(episodes),
                    'valid_episodes': len(episodes),
                    'episodes': episodes,
                    'message': f"Generated {len(episodes)} episodes (fallback method)",
                    'method': 'pattern_generation'
                }
            else:
                return {
                    'success': False,
                    'error': 'No episodes found and cannot generate pattern',
                    'episodes': []
                }
                
    except Exception as e:
        return {
            'success': False,
            'error': f'Scraping failed: {str(e)}',
            'episodes': []
        }

def scrape_iqiyi_basic_info(iqiyi_url, max_episodes=20):
    """Basic info scraper - wrapper for compatibility"""
    return scrape_all_episodes_playlist(iqiyi_url, max_episodes)