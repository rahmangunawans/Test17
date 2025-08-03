"""
Simple IQiyi Scraper untuk Auto Scrape Admin Panel
Scraper sederhana untuk mengambil informasi episode dari IQiyi tanpa M3U8 extraction
"""

import requests
import re
from bs4 import BeautifulSoup
import json
import logging

def scrape_iqiyi_basic_info(iqiyi_url, max_episodes=20):
    """
    Scrape basic episode information from IQiyi URL
    Tidak mengekstrak M3U8 - hanya informasi episode dasar
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        logging.info(f"📡 Scraping basic info from: {iqiyi_url}")
        response = requests.get(iqiyi_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic page info
        title = soup.find('title')
        title_text = title.text.strip() if title else "Unknown Title"
        
        # Look for episode patterns in the page
        episodes = []
        
        # Try to find episode links or patterns
        episode_links = soup.find_all('a', href=re.compile(r'/play/'))
        
        episode_count = 0
        for link in episode_links:
            if episode_count >= max_episodes:
                break
                
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if href and text and any(keyword in text.lower() for keyword in ['episode', 'ep', '第', '话', '集']):
                # Extract episode number if possible
                episode_num_match = re.search(r'(\d+)', text)
                episode_num = episode_num_match.group(1) if episode_num_match else str(episode_count + 1)
                
                full_url = href if href.startswith('http') else f"https://www.iq.com{href}"
                
                episodes.append({
                    'episode_number': episode_num,
                    'title': text,
                    'url': full_url,
                    'server_1_url': '',  # Empty for Server 1 (M3U8)
                    'server_2_url': full_url,  # Use as embed URL for Server 2
                    'server_3_url': '',  # Server 3 disabled
                    'thumbnail_url': '',
                    'description': '',
                    'duration': '',
                    'release_date': ''
                })
                episode_count += 1
        
        # If no episodes found, try alternative method
        if not episodes:
            # Check if this is a single episode page
            if '/play/' in iqiyi_url:
                episode_num_match = re.search(r'episode-(\d+)', iqiyi_url)
                episode_num = episode_num_match.group(1) if episode_num_match else "1"
                
                episodes.append({
                    'episode_number': episode_num,
                    'title': title_text,
                    'url': iqiyi_url,
                    'server_1_url': '',  # Empty for Server 1 (M3U8)
                    'server_2_url': iqiyi_url,  # Use as embed URL for Server 2
                    'server_3_url': '',  # Server 3 disabled
                    'thumbnail_url': '',
                    'description': '',
                    'duration': '',
                    'release_date': ''
                })
        
        if episodes:
            return {
                'success': True,
                'total_episodes': len(episodes),
                'valid_episodes': len(episodes),
                'episodes': episodes,
                'message': f"Successfully scraped {len(episodes)} episodes (basic info only)",
                'method': 'simple_scraper'
            }
        else:
            return {
                'success': False,
                'error': 'No episodes found on this page',
                'episodes': [],
                'suggestion': 'Make sure the URL is a valid IQiyi series or episode page'
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timeout - IQiyi servers too slow',
            'suggestion': 'Try again later'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Connection error - Cannot reach IQiyi servers',
            'suggestion': 'Check internet connection'
        }
    except Exception as e:
        logging.error(f"Simple scraper error: {str(e)}")
        return {
            'success': False,
            'error': f'Scraping failed: {str(e)}',
            'suggestion': 'Try with a different URL or try again later'
        }

def scrape_single_episode(iqiyi_url):
    """Scrape single episode - wrapper untuk konsistensi"""
    result = scrape_iqiyi_basic_info(iqiyi_url, max_episodes=1)
    
    if result['success'] and result['episodes']:
        return {
            'success': True,
            'data': result['episodes'][0],
            'message': 'Single episode scraped successfully'
        }
    else:
        return {
            'success': False,
            'error': result.get('error', 'Failed to scrape single episode')
        }

def scrape_all_episodes_playlist(iqiyi_url, max_episodes=20):
    """Scrape playlist episodes - wrapper untuk konsistensi"""
    return scrape_iqiyi_basic_info(iqiyi_url, max_episodes=max_episodes)