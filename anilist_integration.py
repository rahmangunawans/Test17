"""
Anime Data Integration for AniFlix
Provides functions to search and retrieve anime/manga data from AniList and MyAnimeList APIs
"""

import AnilistPython
import logging
import requests
from typing import Dict, List, Optional, Any
import time

class AnimeDataService:
    def __init__(self):
        """Initialize both AniList and MyAnimeList clients"""
        # Initialize AniList
        try:
            self.anilist = AnilistPython.Anilist()
            logging.info("AniList integration initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize AniList integration: {str(e)}")
            self.anilist = None
        
        # MyAnimeList will use direct HTTP requests to v4 API
        self.mal_base_url = "https://api.jikan.moe/v4"
        logging.info("MyAnimeList (Jikan v4) integration initialized successfully")
    
    def search_anime(self, query: str, source: str = "anilist", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for anime on specified source and return formatted results
        
        Args:
            query: Search query string
            source: Data source ("anilist" or "myanimelist")
            limit: Maximum number of results to return
        
        Returns:
            List of dictionaries containing anime information
        """
        if source == "myanimelist":
            return self._search_myanimelist(query, limit)
        else:
            return self._search_anilist(query, limit)
    
    def _search_anilist(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search anime using AniList API"""
        if not self.anilist:
            return []
        
        try:
            results = []
            
            # Try multiple variations of the search query for better results
            search_variations = [
                query.strip(),
                query.strip().title(),
                query.strip().lower()
            ]
            
            # Remove duplicates while preserving order
            search_variations = list(dict.fromkeys(search_variations))
            
            for search_query in search_variations[:2]:  # Limit to first 2 variations
                try:
                    # Search anime by name
                    anime_data = self.anilist.get_anime(search_query, manual_select=False)
                    
                    if anime_data and isinstance(anime_data, dict):
                        # Format the result for our application
                        formatted_result = self._format_anilist_data(anime_data)
                        if formatted_result and formatted_result not in results:
                            results.append(formatted_result)
                            if len(results) >= limit:
                                break
                                
                except Exception as search_error:
                    logging.debug(f"AniList search variation '{search_query}' failed: {str(search_error)}")
                    continue
            
            return results
            
        except Exception as e:
            logging.error(f"Error searching anime on AniList '{query}': {str(e)}")
            return []
    
    def _search_myanimelist(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search anime using MyAnimeList (Jikan v4) API"""
        try:
            # Clean and prepare query
            if not query or not query.strip():
                logging.warning("Empty query provided to MyAnimeList search")
                return []
                
            clean_query = query.strip()
            
            # Make direct HTTP request to Jikan v4 API
            url = f"{self.mal_base_url}/anime"
            params = {
                'q': clean_query,
                'limit': min(limit, 25),  # API max is 25
                'order_by': 'popularity',
                'sort': 'desc'
            }
            
            headers = {
                'User-Agent': 'AniFlix/1.0 (contact@aniflix.com)'
            }
            
            logging.info(f"Searching MyAnimeList for: '{clean_query}' with params: {params}")
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            logging.info(f"MyAnimeList API response: {response.status_code}")
            
            if response.status_code == 429:  # Rate limited
                logging.warning("MyAnimeList API rate limited, waiting 2 seconds...")
                time.sleep(2)
                response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code != 200:
                logging.error(f"MyAnimeList API error: {response.status_code}, Response: {response.text[:200]}")
                return []
            
            search_results = response.json()
            
            if not search_results or 'data' not in search_results:
                logging.warning(f"No data found in MyAnimeList response for query: '{clean_query}'")
                return []
            
            data_results = search_results['data']
            logging.info(f"Found {len(data_results)} results from MyAnimeList")
            
            results = []
            for anime_data in data_results[:limit]:
                formatted_result = self._format_myanimelist_data(anime_data)
                if formatted_result:
                    results.append(formatted_result)
            
            logging.info(f"Successfully formatted {len(results)} MyAnimeList results")
            return results
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error searching MyAnimeList for '{query}': {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Error searching anime on MyAnimeList '{query}': {str(e)}")
            return []
    
    def search_anime_by_id(self, anilist_id: int) -> Optional[Dict[str, Any]]:
        """
        Get anime by AniList ID
        
        Args:
            anilist_id: AniList anime ID
        
        Returns:
            Dictionary containing anime information or None
        """
        if not self.anilist:
            return None
        
        try:
            anime_data = self.anilist.get_anime_with_id(anilist_id)
            
            if not anime_data:
                return None
            
            return self._format_anilist_data(anime_data)
            
        except Exception as e:
            logging.error(f"Error getting anime with ID {anilist_id}: {str(e)}")
            return None
    
    def search_manga(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search for manga on AniList (can be used for manhwa/donghua source material)
        
        Args:
            query: Search query string
        
        Returns:
            Dictionary containing manga information or None
        """
        if not self.anilist:
            return None
        
        try:
            manga_data = self.anilist.get_manga(query, manual_select=False)
            
            if not manga_data:
                return None
            
            return self._format_manga_data(manga_data)
            
        except Exception as e:
            logging.error(f"Error searching manga '{query}': {str(e)}")
            return None
    
    def _format_anilist_data(self, anime_data: Any) -> Dict[str, Any]:
        """
        Format AniList anime data for our application
        
        Args:
            anime_data: Raw anime data from AniList (can be dict or other format)
        
        Returns:
            Formatted dictionary for our Content model
        """
        try:
            # Handle different data formats from AniList
            if isinstance(anime_data, str):
                logging.error(f"Received string data instead of dict: {anime_data}")
                return {}
            
            if not isinstance(anime_data, dict):
                logging.error(f"Unexpected data type: {type(anime_data)}")
                return {}
            
            # Determine content type based on format
            content_type = 'anime'  # Default
            anime_format = anime_data.get('format', '').lower()
            
            if 'movie' in anime_format or anime_format == 'film':
                content_type = 'movie'
            elif any(keyword in str(anime_data.get('name_english', '')).lower() or 
                    keyword in str(anime_data.get('name_romaji', '')).lower() 
                    for keyword in ['chinese', 'donghua']):
                content_type = 'donghua'
            
            # Get title (prefer English, fallback to Romaji)
            title = anime_data.get('name_english') or anime_data.get('name_romaji') or 'Unknown Title'
            
            # Format genres
            genres = anime_data.get('genres', [])
            genre_str = ', '.join(genres) if genres else ''
            
            # Get description and clean it
            description = anime_data.get('desc', '').replace('<br>', '\n').replace('<i>', '').replace('</i>', '').replace('<br><br>', '\n\n')
            # Remove extra whitespace and newlines
            description = ' '.join(description.split())
            if len(description) > 1000:
                description = description[:997] + '...'
            
            # Get episodes count (use airing_episodes field)
            episodes = anime_data.get('airing_episodes')
            total_episodes = episodes if episodes and episodes > 0 else None
            
            # Determine status from airing_status
            status = 'unknown'
            anilist_status = anime_data.get('airing_status', '').lower()
            if 'finished' in anilist_status or 'completed' in anilist_status:
                status = 'completed'
            elif 'releasing' in anilist_status or 'ongoing' in anilist_status or 'airing' in anilist_status:
                status = 'ongoing'
            
            # Get studio information from available data
            studio = ''
            # Try to extract studio from different possible fields
            if 'studios' in anime_data and anime_data['studios']:
                if isinstance(anime_data['studios'], list):
                    studio = anime_data['studios'][0] if anime_data['studios'] else ''
                else:
                    studio = str(anime_data['studios'])
            elif 'studio' in anime_data:
                studio = str(anime_data['studio']) if anime_data['studio'] else ''
            elif 'producer' in anime_data:
                studio = str(anime_data['producer']) if anime_data['producer'] else ''
            
            # If still no studio, try to get it from a different source
            if not studio:
                studio = self._find_studio_info(title)
            
            # Get year from starting_time (format: "4/7/2013")
            year = None
            start_time = anime_data.get('starting_time', '')
            if start_time:
                try:
                    # Extract year from date string like "4/7/2013"
                    year_str = start_time.split('/')[-1]
                    year = int(year_str) if year_str.isdigit() else None
                except:
                    year = None
            
            # Get rating (convert from 0-100 to 0-10 scale)
            average_score = anime_data.get('average_score')
            rating = round(average_score / 10, 1) if average_score else None
            
            # Get cover image
            cover_image = anime_data.get('cover_image')
            thumbnail_url = cover_image if cover_image else ''
            
            # Try to find trailer URL
            trailer_url = self._find_trailer_url(title)
            
            # Try to get character information from AniList
            character_overview = self._get_character_overview_anilist(anime_data, title, content_type)

            return {
                'title': title,
                'description': description,
                'character_overview': character_overview,
                'genre': genre_str,
                'year': year,
                'rating': rating,
                'content_type': content_type,
                'thumbnail_url': thumbnail_url,
                'trailer_url': trailer_url,
                'studio': studio,
                'total_episodes': total_episodes,
                'status': status,
                'anilist_id': None,  # ID not provided in this API format
                'anilist_url': ''  # Cannot generate URL without ID
            }
        
        except Exception as e:
            logging.error(f"Error formatting anime data: {str(e)}")
            return {}
    
    def _find_trailer_url(self, title: str) -> str:
        """
        Try to find YouTube trailer URL for the anime using web scraping
        
        Args:
            title: Anime title
            
        Returns:
            YouTube embed URL or empty string if not found
        """
        try:
            import re
            import urllib.parse
            
            # Clean title for search
            search_title = title.replace(':', '').replace('-', ' ').strip()
            
            # Try to search for trailers using multiple approaches
            search_queries = [
                f"{search_title} trailer",
                f"{search_title} official trailer", 
                f"{search_title} anime trailer",
                f"{search_title} PV"
            ]
            
            for query in search_queries[:2]:  # Limit to first 2 queries
                try:
                    # Create YouTube search URL
                    encoded_query = urllib.parse.quote_plus(query)
                    search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
                    
                    # Use requests to get search results
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    response = requests.get(search_url, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        # Look for video IDs in the response
                        video_pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
                        matches = re.findall(video_pattern, response.text)
                        
                        if matches:
                            # Return the first video as embed URL
                            video_id = matches[0]
                            return f"https://www.youtube.com/embed/{video_id}"
                            
                except Exception as search_error:
                    logging.debug(f"Trailer search failed for '{query}': {str(search_error)}")
                    continue
                    
            # If web scraping fails, provide a manual search URL that opens in new tab
            encoded_title = urllib.parse.quote_plus(f"{search_title} trailer")
            return f"https://www.youtube.com/results?search_query={encoded_title}"
            
        except Exception as e:
            logging.debug(f"Error finding trailer for '{title}': {str(e)}")
            return ''
    
    def _find_studio_info(self, title: str) -> str:
        """
        Try to find studio information for the anime
        
        Args:
            title: Anime title
            
        Returns:
            Studio name or empty string if not found
        """
        try:
            # Common studio mappings for popular anime
            studio_mappings = {
                'attack on titan': 'Madhouse, Pierrot',
                'shingeki no kyojin': 'Madhouse, Pierrot',
                'demon slayer': 'Ufotable',
                'kimetsu no yaiba': 'Ufotable',
                'naruto': 'Pierrot',
                'one piece': 'Toei Animation',
                'death note': 'Madhouse',
                'fullmetal alchemist': 'Bones',
                'dragon ball': 'Toei Animation',
                'bleach': 'Pierrot',
                'hunter x hunter': 'Madhouse',
                'my hero academia': 'Bones',
                'boku no hero academia': 'Bones',
                'jujutsu kaisen': 'MAPPA',
                'chainsaw man': 'MAPPA',
                'spy x family': 'Wit Studio, CloverWorks',
                'onigiri': 'Pierrot Plus',
                'mob psycho': 'Bones',
                'one punch man': 'Madhouse, J.C.Staff',
                'tokyo ghoul': 'Pierrot',
                'violet evergarden': 'Kyoto Animation',
                'your name': 'CoMix Wave Films'
            }
            
            # Check for known mappings
            title_lower = title.lower().strip()
            for key, studio in studio_mappings.items():
                if key in title_lower or title_lower in key:
                    return studio
            
            return ''  # No studio information found
            
        except Exception as e:
            logging.debug(f"Error finding studio for '{title}': {str(e)}")
            return ''
    
    def _format_myanimelist_data(self, anime_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format MyAnimeList anime data for our application
        
        Args:
            anime_data: Raw anime data from MyAnimeList API
            
        Returns:
            Formatted dictionary for our Content model
        """
        try:
            # Get title (prefer English, fallback to original)
            title = anime_data.get('title_english') or anime_data.get('title') or 'Unknown Title'
            
            # Get content type
            content_type = 'anime'
            anime_type = anime_data.get('type', '').lower()
            if 'movie' in anime_type:
                content_type = 'movie'
            
            # Format genres
            genres = anime_data.get('genres', [])
            genre_list = [genre.get('name', '') for genre in genres if isinstance(genre, dict)]
            genre_str = ', '.join(genre_list) if genre_list else ''
            
            # Get description and clean it
            synopsis = anime_data.get('synopsis', '') or ''
            description = synopsis.replace('[Written by MAL Rewrite]', '').strip() if synopsis else ''
            if description and len(description) > 1000:
                description = description[:997] + '...'
            
            # Get episodes count
            episodes = anime_data.get('episodes')
            total_episodes = episodes if episodes and episodes > 0 else None
            
            # Determine status
            status = 'unknown'
            mal_status = anime_data.get('status', '').lower()
            if 'finished' in mal_status or 'completed' in mal_status:
                status = 'completed'
            elif 'airing' in mal_status or 'ongoing' in mal_status:
                status = 'ongoing'
            
            # Get studio information
            studios = anime_data.get('studios', [])
            studio_list = [studio.get('name', '') for studio in studios if isinstance(studio, dict)]
            studio = ', '.join(studio_list) if studio_list else ''
            
            # If no studio from API, try to get from mapping
            if not studio:
                studio = self._find_studio_info(title)
            
            # Get year from aired date
            year = None
            aired = anime_data.get('aired', {})
            if aired and 'from' in aired and aired['from']:
                try:
                    from datetime import datetime
                    aired_date = aired['from']
                    if isinstance(aired_date, str):
                        year = int(aired_date[:4])
                    elif isinstance(aired_date, dict) and 'year' in aired_date:
                        year = aired_date['year']
                except:
                    year = None
            
            # Get rating
            score = anime_data.get('score')
            rating = score if score else None
            
            # Get images
            images = anime_data.get('images', {})
            jpg_images = images.get('jpg', {}) if images else {}
            thumbnail_url = jpg_images.get('large_image_url') or jpg_images.get('image_url') or ''
            
            # Try to find trailer URL
            trailer_url = self._find_trailer_url(title)
            
            # Try to get character information from MyAnimeList
            character_overview = self._get_character_overview_mal(anime_data, title, content_type)

            return {
                'title': title,
                'description': description,
                'character_overview': character_overview,
                'genre': genre_str,
                'year': year,
                'rating': rating,
                'content_type': content_type,
                'thumbnail_url': thumbnail_url,
                'trailer_url': trailer_url,
                'studio': studio,
                'total_episodes': total_episodes,
                'status': status,
                'anilist_id': None,  # MyAnimeList doesn't provide AniList IDs
                'anilist_url': '',
                'mal_id': anime_data.get('mal_id'),
                'mal_url': anime_data.get('url', '')
            }
            
        except Exception as e:
            logging.error(f"Error formatting MyAnimeList data: {str(e)}")
            return {}
    
    def _format_manga_data(self, manga_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format AniList manga data (for donghua source material reference)
        
        Args:
            manga_data: Raw manga data from AniList
        
        Returns:
            Formatted dictionary with manga information
        """
        try:
            title = manga_data.get('name_english') or manga_data.get('name_romaji') or 'Unknown Title'
            
            genres = manga_data.get('genres', [])
            genre_str = ', '.join(genres) if genres else ''
            
            description = manga_data.get('desc', '').replace('<br>', '\n').replace('<i>', '').replace('</i>', '')
            if len(description) > 1000:
                description = description[:997] + '...'
            
            start_date = manga_data.get('starting_time', {})
            year = start_date.get('year') if start_date else None
            
            average_score = manga_data.get('average_score')
            rating = round(average_score / 10, 1) if average_score else None
            
            cover_image = manga_data.get('cover_image')
            thumbnail_url = cover_image if cover_image else ''
            
            return {
                'title': title,
                'description': description,
                'genre': genre_str,
                'year': year,
                'rating': rating,
                'thumbnail_url': thumbnail_url,
                'anilist_id': manga_data.get('id'),
                'anilist_url': f"https://anilist.co/manga/{manga_data.get('id')}" if manga_data.get('id') else ''
            }
        
        except Exception as e:
            logging.error(f"Error formatting manga data: {str(e)}")
            return {}

    def _get_character_overview_anilist(self, anime_data: Dict[str, Any], title: str, content_type: str) -> str:
        """
        Get character overview information from AniList data
        
        Args:
            anime_data: Raw anime data from AniList
            title: Anime title
            content_type: Type of content (anime, movie, donghua)
            
        Returns:
            Character overview string with main character information
        """
        try:
            # Try to get character information if available
            characters_info = []
            
            # AniList API might have character data in different formats
            if 'characters' in anime_data and anime_data['characters']:
                characters = anime_data['characters']
                if isinstance(characters, list):
                    for char in characters[:5]:  # Limit to top 5 characters
                        if isinstance(char, dict):
                            char_name = char.get('name', {}).get('full', '') or char.get('name', '')
                            char_role = char.get('role', '')
                            if char_name:
                                role_text = f" ({char_role})" if char_role else ""
                                characters_info.append(f"{char_name}{role_text}")
            
            # If we have character data, format it properly
            if characters_info:
                char_list = ", ".join(characters_info)
                if content_type == 'movie':
                    return f"Main characters: {char_list}. These characters drive the story and development in this film."
                else:
                    return f"Main characters: {char_list}. These characters develop throughout the series with complex relationships and story arcs."
            
            # Fallback: try to extract character mentions from description
            description = anime_data.get('desc', '')
            if description:
                # Look for character name patterns in description
                character_mentions = self._extract_character_mentions(description)
                if character_mentions:
                    char_list = ", ".join(character_mentions[:3])  # Top 3 mentions
                    return f"Key characters mentioned: {char_list}. {title} features these characters in important roles throughout the story."
            
            # Final fallback with meaningful content
            if content_type == 'movie':
                return f"{title} features a cast of characters whose interactions and development drive the film's narrative forward."
            else:
                return f"{title} showcases diverse characters with unique personalities and backgrounds, each contributing to the overall story through their relationships and individual growth arcs."
                
        except Exception as e:
            logging.error(f"Error getting character overview for '{title}': {str(e)}")
            return f"{title} features memorable characters that contribute to an engaging storyline."
    
    def _get_character_overview_mal(self, anime_data: Dict[str, Any], title: str, content_type: str) -> str:
        """
        Get character overview information from MyAnimeList data
        
        Args:
            anime_data: Raw anime data from MyAnimeList
            title: Anime title
            content_type: Type of content (anime, movie, donghua)
            
        Returns:
            Character overview string with main character information
        """
        try:
            # MyAnimeList API structure might have character info
            characters_info = []
            
            # Try to get character data from MAL API response
            if 'characters' in anime_data and anime_data['characters']:
                characters = anime_data['characters']
                if isinstance(characters, list):
                    for char in characters[:5]:  # Limit to top 5 characters
                        if isinstance(char, dict):
                            char_name = char.get('name', '')
                            char_role = char.get('role', '')
                            if char_name:
                                role_text = f" ({char_role})" if char_role else ""
                                characters_info.append(f"{char_name}{role_text}")
            
            # If we have character data, format it properly
            if characters_info:
                char_list = ", ".join(characters_info)
                if content_type == 'movie':
                    return f"Main characters: {char_list}. These characters are central to the film's plot and emotional impact."
                else:
                    return f"Main characters: {char_list}. The series follows these characters through their personal journeys and interconnected storylines."
            
            # Try to extract from synopsis
            synopsis = anime_data.get('synopsis', '')
            if synopsis:
                character_mentions = self._extract_character_mentions(synopsis)
                if character_mentions:
                    char_list = ", ".join(character_mentions[:3])
                    return f"Featured characters: {char_list}. {title} explores their stories and character development throughout the narrative."
            
            # Get genres to create more specific character description
            genres = anime_data.get('genres', [])
            genre_names = [g.get('name', '') for g in genres if isinstance(g, dict)] if genres else []
            
            # Create genre-specific character descriptions
            if any(genre in ['Action', 'Adventure', 'Shounen'] for genre in genre_names):
                return f"{title} features dynamic characters who face challenges and grow stronger through their adventures and battles."
            elif any(genre in ['Romance', 'Drama', 'Slice of Life'] for genre in genre_names):
                return f"{title} presents relatable characters dealing with personal relationships, emotions, and everyday life situations."
            elif any(genre in ['Fantasy', 'Magic', 'Supernatural'] for genre in genre_names):
                return f"{title} showcases characters with unique abilities and backgrounds in a world filled with magic and supernatural elements."
            else:
                if content_type == 'movie':
                    return f"{title} brings together memorable characters whose individual stories converge in this cinematic experience."
                else:
                    return f"{title} features well-developed characters, each with distinct personalities and motivations that drive the series forward."
                
        except Exception as e:
            logging.error(f"Error getting MAL character overview for '{title}': {str(e)}")
            return f"{title} features engaging characters that bring depth and personality to the story."
    
    def _extract_character_mentions(self, text: str) -> List[str]:
        """
        Extract potential character names from description text
        
        Args:
            text: Description text to analyze
            
        Returns:
            List of potential character names
        """
        try:
            import re
            
            # Remove HTML tags and clean text
            clean_text = re.sub(r'<[^>]+>', '', text)
            
            # Look for capitalized words that might be character names
            # This is a simple heuristic approach
            potential_names = []
            
            # Pattern for potential names (capitalized words, excluding common words)
            words = clean_text.split()
            skip_words = {'The', 'A', 'An', 'And', 'Or', 'But', 'In', 'On', 'At', 'To', 'For', 'Of', 'With', 'By', 'From', 'Up', 'About', 'Into', 'Through', 'During', 'Before', 'After', 'Above', 'Below', 'Between', 'Among', 'Since', 'Until', 'While', 'Because', 'Although', 'However', 'Therefore', 'Meanwhile', 'Furthermore', 'Moreover', 'Nevertheless'}
            
            for i, word in enumerate(words):
                # Clean word from punctuation
                clean_word = re.sub(r'[^\w]', '', word)
                
                # Check if it's a potential character name
                if (len(clean_word) >= 3 and 
                    clean_word[0].isupper() and 
                    clean_word not in skip_words and
                    not clean_word.isupper()):  # Avoid all-caps words
                    
                    # Check if next word is also capitalized (compound names like "Naruto Uzumaki")
                    if i + 1 < len(words):
                        next_word = re.sub(r'[^\w]', '', words[i + 1])
                        if (len(next_word) >= 2 and 
                            next_word[0].isupper() and 
                            next_word not in skip_words):
                            potential_names.append(f"{clean_word} {next_word}")
                            continue
                    
                    potential_names.append(clean_word)
            
            # Remove duplicates and return top candidates
            unique_names = list(dict.fromkeys(potential_names))  # Preserve order
            return unique_names[:5]  # Return top 5 potential names
            
        except Exception as e:
            logging.error(f"Error extracting character mentions: {str(e)}")
            return []

# Global instance
anime_data_service = AnimeDataService()

# Backward compatibility
anilist_service = anime_data_service