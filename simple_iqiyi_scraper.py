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
        
        # Method 1: Look for episode selection UI elements
        episode_selectors = [
            'div[class*="episode"]',
            'div[class*="tab"]', 
            'a[class*="episode"]',
            'li[class*="episode"]',
            '.intl-episode-list a',
            '.episode-list a',
            '.tab-list a'
        ]
        
        episode_count = 0
        found_episodes = set()  # To avoid duplicates
        
        for selector in episode_selectors:
            if episode_count >= max_episodes:
                break
                
            episode_elements = soup.select(selector)
            for element in episode_elements:
                if episode_count >= max_episodes:
                    break
                    
                href = element.get('href', '')
                text = element.get_text(strip=True)
                
                if href and text:
                    # Clean up the URL
                    if href.startswith('/'):
                        full_url = f"https://www.iq.com{href}"
                    elif not href.startswith('http'):
                        full_url = f"https://www.iq.com/play/{href}"
                    else:
                        full_url = href
                    
                    # Skip if we already found this URL
                    if full_url in found_episodes:
                        continue
                        
                    # Extract episode number
                    episode_num_match = re.search(r'(\d+)', text)
                    if not episode_num_match:
                        episode_num_match = re.search(r'episode-(\d+)', href)
                    
                    episode_num = episode_num_match.group(1) if episode_num_match else str(episode_count + 1)
                    
                    # Create episode title
                    if re.search(r'\d+', text):
                        episode_title = text
                    else:
                        episode_title = f"Episode {episode_num}"
                    
                    episodes.append({
                        'episode_number': episode_num,
                        'title': episode_title,
                        'url': full_url,
                        'server_1_url': '',  # Empty for Server 1 (M3U8)
                        'server_2_url': full_url,  # Use as embed URL for Server 2
                        'server_3_url': '',  # Server 3 disabled
                        'thumbnail_url': '',
                        'description': '',
                        'duration': '',
                        'release_date': ''
                    })
                    
                    found_episodes.add(full_url)
                    episode_count += 1
        
        # Method 2: If still no episodes, try to find script data
        if not episodes:
            script_tags = soup.find_all('script')
            for script in script_tags:
                script_content = script.get_text() if script.string else ''
                
                # Look for episode data in JavaScript
                if 'episode' in script_content.lower() and 'play' in script_content.lower():
                    # Try to extract URLs from script
                    url_matches = re.findall(r'/play/[a-zA-Z0-9]+', script_content)
                    for i, url_match in enumerate(url_matches[:max_episodes]):
                        full_url = f"https://www.iq.com{url_match}"
                        if full_url not in found_episodes:
                            episodes.append({
                                'episode_number': str(i + 1),
                                'title': f"Episode {i + 1}",
                                'url': full_url,
                                'server_1_url': '',
                                'server_2_url': full_url,
                                'server_3_url': '',
                                'thumbnail_url': '',
                                'description': '',
                                'duration': '',
                                'release_date': ''
                            })
                            found_episodes.add(full_url)
        
        # Method 3: If this is a single episode page, try to find series info
        if not episodes and '/play/' in iqiyi_url:
            # Extract the base ID from URL
            url_match = re.search(r'/play/([a-zA-Z0-9]+)', iqiyi_url)
            if url_match:
                base_id = url_match.group(1)
                
                # Try to generate common episode patterns
                for i in range(1, min(max_episodes + 1, 21)):  # Try up to 20 episodes
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
                
                # Also add the original URL as episode 1 if not already included
                if iqiyi_url not in [ep['url'] for ep in episodes]:
                    episodes.insert(0, {
                        'episode_number': '1',
                        'title': title_text,
                        'url': iqiyi_url,
                        'server_1_url': '',
                        'server_2_url': iqiyi_url,
                        'server_3_url': '',
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
                'method': 'enhanced_simple_scraper'
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