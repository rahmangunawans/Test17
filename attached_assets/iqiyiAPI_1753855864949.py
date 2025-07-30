# -*- coding: utf8 -*-
import json
import requests
import urllib3
import re
import requests
import os
import subprocess
import tempfile
import shutil
from sys import stdout
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed


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
        soup = BeautifulSoup(response.text, 'html.parser')
        # Mengambil isi JSON dari elemen <script>
        # Menemukan elemen <script> dengan id '__NEXT_DATA__'
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
        # Mengambil isi JSON dari elemen <script>
        json_data = script_tag.string.strip()
        data = json.loads(json_data)
        return data
    
    def get_actorArr(self):
        data = self.get_player_data()
        names = []
        for i in data['props']['initialState']['album']['videoAlbumInfo']['actorArr']:
            name_cast = i['name']
            names.append(name_cast)
        return names
    
    def get_all_playlist(self):
        data = self.get_player_data()
        names = []
        # print(data['props']['initialState']['play']['cachePlayList']['1'])
        for i in data['props']['initialState']['play']['cachePlayList']['1']:
            name_cast = {'Title':i['subTitle'], 'Link':i['albumPlayUrl']}
            names.append(name_cast)
        return names

    
    def Subtitle(self, type="srt"):
        #video
        # audio
        # stl
        names = []
        data = self.get_player_data()
        link = data['props']['initialProps']['pageProps']['prePlayerData']['dash']['data']['dm']
        for i in data['props']['initialProps']['pageProps']['prePlayerData']['dash']['data']['program']['stl']:
            if type == "srt":
                Downloads = link + i['srt']
            if type == "xml":
                Downloads = link  + i['xml']
            if type == "webvtt":
                Downloads = link  + i['webvtt']
            sub = i['_name'], Downloads
            names.append(sub)
        return names
    

    def dash(self):
        data = self.get_player_data()
        log = data['props']['initialProps']['pageProps']['prePlayerData']['ssrlog']
        # print(log)

        url_pattern = r'http://intel-cache\.video\.qiyi\.domain/dash\?([^\s]+)'
        urls = re.findall(url_pattern, log)
        # Menampilkan URL yang ditemukan
        for url in urls:
            return url
    
    def get_m3u8(self):
        url = 'https://cache.video.iqiyi.com/dash?'+ self.dash()
        response = self.request('get', url).text
        if response:
            data = json.loads(response)
            if data.get('code') == 'A00000':
                video = data['data']['program']['video']
                for item in video:
                    if 'm3u8' in item:
                        return item['m3u8']
        return None
    
    def download_segment(self, url, filepath):
        try:
            response = self.request('get', url, stream=True)
            if response and response.status_code == 200:
                content_length = int(response.headers['content-length'])
                stdout.write('File size: %0.2fMB\n' % (content_length / 1024 / 1024))
                with open(filepath, 'wb') as f:
                    chunk_size = 1024
                    size = 0
                    for data in response.iter_content(chunk_size=chunk_size):
                        f.write(data)
                        f.flush()
                        size += len(data)
                        stdout.write('Download progress: %.2f%%\r' % float(size / content_length * 100))
                        if size / content_length == 1:
                            print('\n')
                return True
            return False
        except Exception as e:
            print(f"Error downloading segment {url}: {e}")
            return False

    def process_m3u8(self, title, m3u8_content):
        if not m3u8_content or '#EXTM3U' not in m3u8_content:
            print("Invalid m3u8 content")
            return False

        output_dir = os.path.join(os.getcwd(), "downloads", title)
        os.makedirs(output_dir, exist_ok=True)

        ts_urls = [line for line in m3u8_content.split('\n') if line.strip() and '.ts' in line]
        if not ts_urls:
            print("No .ts URLs found")
            return False

        print(f"\nDownloading {len(ts_urls)} segments...")
        ts_files = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i, url in enumerate(ts_urls, 1):
                ts_file = os.path.join(output_dir, f"{i:03d}.ts")
                ts_files.append(ts_file)
                futures.append(
                    executor.submit(self.download_segment, url, ts_file)
                )

            completed = 0
            for future in as_completed(futures):
                completed += 1
                stdout.write(f'\rProgress: {completed}/{len(ts_urls)} segments downloaded')
                stdout.flush()

        print("\nDownload completed!")

        output_file = os.path.join(output_dir, f"{title}.mp4")
        if self.combine_videos_python(ts_files, output_file):
            print(f"\nVideo saved as: {output_file}")
            for ts_file in ts_files:
                try:
                    os.remove(ts_file)
                except:
                    pass
            return True
        return False

    def combine_videos_python(self, ts_files, output_file):
        try:
            with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as temp_file:
                for ts_file in ts_files:
                    with open(ts_file, 'rb') as f:
                        shutil.copyfileobj(f, temp_file)

                temp_file.seek(0)
                with open(output_file, 'wb') as f:
                    shutil.copyfileobj(temp_file, f)

            return True
        except Exception as e:
            print(f"Error combining videos: {e}")
            return False

    def download_video(self):
        print(f"Downloading video from: {self.url}")
        m3u8_content = self.get_m3u8()
        if not m3u8_content:
            print("Failed to get M3U8 content")
            return False
        self.process_m3u8('Fangs of Fortune Episode 27', m3u8_content)
        return True

    
    

#  Example Generate Subtitle
def generate_Subtitle():
    ''' 
    'Simplified Chinese', 'http://meta.video.iqiyi.com/20241113/ee/0a/0e638a260e591cc0db25fc2866068390.srt?qd_uid=0&qd_tm=1731601534609&qd_tvid=1373007121394700&qyid=581f9e44e9e9dfbd7639efe15a421526&lid=1')
    ('Traditional Chinese', 'http://meta.video.iqiyi.com/20241113/8b/ce/b485232e3d45749965e708f744121a6d.srt?qd_uid=0&qd_tm=1731601534609&qd_tvid=1373007121394700&qyid=581f9e44e9e9dfbd7639efe15a421526&lid=2')'''
    
    url = 'https://www.iq.com/play/fangs-of-fortune-episode-28-cphfhfinog?lang=en_us'
    iq = IQiyiDownloader(url=url)
    subtitle = iq.Subtitle(type="srt") #srt, xml, webvtt
    for i in subtitle:
        print(i)

def generate_playlist():
    ''' {'Title': 'Fangs of Fortune Episode 1', 'Link': '//www.iq.com/play/fangs-of-fortune-episode-1-rz7c6zo49o?lang=en_us'}
        {'Title': 'Fangs of Fortune Episode 2', 'Link': '//www.iq.com/play/fangs-of-fortune-episode-2-xu2nlnfk50?lang=en_us'}
        {'Title': 'Fangs of Fortune Episode 3', 'Link': '//www.iq.com/play/fangs-of-fortune-episode-3-1nueeywdmgg?lang=en_us'} '''
    
    url = 'https://www.iq.com/play/fangs-of-fortune-episode-28-cphfhfinog?lang=en_us'
    iq = IQiyiDownloader(url=url)
    playlist = iq.get_all_playlist() 
    for i in playlist:
        print(i)

def generate_actor():
    url = 'https://www.iq.com/play/fangs-of-fortune-episode-28-cphfhfinog?lang=en_us'
    iq = IQiyiDownloader(url=url)
    playlist = iq.get_actorArr()
    for i in playlist:
        print(i)
    

def generate_download():
    url = 'https://www.iq.com/play/fangs-of-fortune-episode-27-jlpasi0uys?lang=en_us'
    iq = IQiyiDownloader(url=url)
    download = iq.download_video()
    print(download)

generate_download()