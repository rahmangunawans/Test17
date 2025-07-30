# -*- coding: utf8 -*-
import json
import requests
import urllib3
import re
from bs4 import BeautifulSoup
import logging

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class IQiyiIntegration:
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1'
        }
        self.session = requests.Session()
        self.session.verify = False
        logging.info("IQiyi integration initialized")

    def request(self, method, url, **kwargs):
        try:
            kwargs.setdefault('headers', self.headers)
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            logging.error(f'Error making request to {url}: {str(e)}')
            return None
        
    def get_player_data(self, url):
        """Extract player data from IQiyi page"""
        response = self.request('get', url)
        if not response:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
        
        if not script_tag:
            logging.error("No __NEXT_DATA__ script tag found")
            return None
            
        try:
            json_data = script_tag.string.strip()
            data = json.loads(json_data)
            return data
        except Exception as e:
            logging.error(f"Error parsing JSON data: {e}")
            return None
    
    def get_episode_list(self, url):
        """Get all episodes from an IQiyi series"""
        data = self.get_player_data(url)
        if not data:
            return []
            
        episodes = []
        try:
            cache_playlist = data['props']['initialState']['play']['cachePlayList']['1']
            for i, episode in enumerate(cache_playlist):
                episode_data = {
                    'episode_number': i + 1,
                    'title': episode.get('subTitle', f'Episode {i + 1}'),
                    'url': f"https://www.iq.com{episode.get('albumPlayUrl', '')}"
                }
                episodes.append(episode_data)
        except KeyError as e:
            logging.error(f"Error extracting episode list: {e}")
            
        return episodes
    
    def get_subtitles(self, url, subtitle_type="srt"):
        """Get subtitles for an episode"""
        try:
            # For now, return empty list as IQiyi requires complex authentication
            # This will show "No subtitles found" message
            logging.info("IQiyi subtitle extraction not available")
            return []
        except Exception as e:
            logging.error(f"Error extracting subtitles: {e}")
            return []
    
    def get_dash_params(self, url):
        """Extract DASH parameters from page"""
        data = self.get_player_data(url)
        if not data:
            return None
            
        try:
            log = data['props']['initialProps']['pageProps']['prePlayerData']['ssrlog']
            url_pattern = r'http://intel-cache\.video\.qiyi\.domain/dash\?([^\s]+)'
            urls = re.findall(url_pattern, log)
            
            if urls:
                return urls[0]
        except KeyError as e:
            logging.error(f"Error extracting DASH params: {e}")
            
        return None
    
    def get_m3u8_url(self, url):
        """Get M3U8 streaming URL for an episode"""
        try:
            # For now, return None as IQiyi requires complex authentication
            # This will trigger the iframe fallback
            logging.info("IQiyi M3U8 extraction not available - using iframe fallback")
            return None
        except Exception as e:
            logging.error(f"Error extracting M3U8 URL: {e}")
            return None
    
    def get_actors(self, url):
        """Get actor list from series"""
        data = self.get_player_data(url)
        if not data:
            return []
            
        actors = []
        try:
            actor_arr = data['props']['initialState']['album']['videoAlbumInfo']['actorArr']
            for actor in actor_arr:
                actors.append(actor.get('name', 'Unknown'))
        except KeyError as e:
            logging.error(f"Error extracting actors: {e}")
            
        return actors
    
    def extract_content_info(self, url):
        """Extract comprehensive content information from IQiyi URL"""
        data = self.get_player_data(url)
        if not data:
            return None
            
        try:
            album_info = data['props']['initialState']['album']['videoAlbumInfo']
            
            content_info = {
                'title': album_info.get('name', 'Unknown Title'),
                'description': album_info.get('description', ''),
                'thumbnail_url': album_info.get('picUrl', ''),
                'year': album_info.get('year', ''),
                'genre': [genre.get('name', '') for genre in album_info.get('genreList', [])],
                'actors': [actor.get('name', '') for actor in album_info.get('actorArr', [])],
                'episodes': self.get_episode_list(url),
                'content_type': 'anime'  # Default to anime, can be adjusted
            }
            
            return content_info
        except Exception as e:
            logging.error(f"Error extracting content info: {e}")
            return None

# Initialize IQiyi integration
iqiyi_integration = IQiyiIntegration()