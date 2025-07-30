# -*- coding: utf8 -*-
import json
import requests
import urllib3
import re
from bs4 import BeautifulSoup

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class IQiyiDownloader:
    def __init__(self, url):
        self.url = url
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.verify = False

    def request(self, method, url, **kwargs):
        try:
            kwargs.setdefault('headers', self.headers)
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f'Error making request to {url}: {str(e)}')
            return None

    def get_player_data(self):
        response = self.request('get', self.url)
        if not response:
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find script tag with id '__NEXT_DATA__'
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
        if script_tag and script_tag.string:
            json_data = script_tag.string.strip()
            try:
                data = json.loads(json_data)
                return data
            except json.JSONDecodeError:
                return None
        return None

    def Subtitle(self, type="srt"):
        """Extract subtitles from IQiyi video page"""
        try:
            data = self.get_player_data()
            if not data:
                return []

            names = []
            try:
                link = data['props']['initialProps']['pageProps']['prePlayerData']['dash']['data']['dm']
                subtitles_data = data['props']['initialProps']['pageProps']['prePlayerData']['dash']['data']['program']['stl']
                
                for i in subtitles_data:
                    if type == "srt" and 'srt' in i:
                        downloads = link + i['srt']
                    elif type == "xml" and 'xml' in i:
                        downloads = link + i['xml']
                    elif type == "webvtt" and 'webvtt' in i:
                        downloads = link + i['webvtt']
                    else:
                        continue
                    
                    sub = {
                        'language': i.get('_name', 'unknown'),
                        'url': downloads,
                        'format': type
                    }
                    names.append(sub)
            except (KeyError, TypeError):
                pass
            
            return names
        except Exception as e:
            print(f"Error extracting subtitles: {e}")
            return []

    def dash(self):
        """Extract dash URL parameters"""
        try:
            data = self.get_player_data()
            if not data:
                return None

            log = data['props']['initialProps']['pageProps']['prePlayerData']['ssrlog']
            url_pattern = r'http://intel-cache\.video\.qiyi\.domain/dash\?([^\s]+)'
            urls = re.findall(url_pattern, log)
            
            if urls:
                return urls[0]
        except (KeyError, TypeError):
            pass
        return None

    def get_m3u8(self):
        """Extract M3U8 URL from IQiyi video page"""
        try:
            dash_params = self.dash()
            if not dash_params:
                return None

            url = 'https://cache.video.iqiyi.com/dash?' + dash_params
            response = self.request('get', url)
            
            if response:
                data = json.loads(response.text)
                if data.get('code') == 'A00000':
                    video = data['data']['program']['video']
                    for item in video:
                        if 'm3u8' in item:
                            return item['m3u8']
        except Exception as e:
            print(f"Error getting M3U8: {e}")
        
        return None

# API wrapper class for compatibility
class IqiyiAPI:
    def __init__(self):
        pass

    def get_m3u8_url(self, video_url):
        """Get M3U8 streaming URL from iQiyi video URL"""
        try:
            downloader = IQiyiDownloader(video_url)
            return downloader.get_m3u8()
        except Exception as e:
            print(f"Error getting M3U8 URL: {e}")
            return None

    def get_subtitles(self, video_url, subtitle_type="srt"):
        """Get subtitles from iQiyi video URL"""
        try:
            downloader = IQiyiDownloader(video_url)
            return downloader.Subtitle(subtitle_type)
        except Exception as e:
            print(f"Error getting subtitles: {e}")
            return []

# Create a global instance
iqiyi_api = IqiyiAPI()