"""
AniList Integration for AniFlix
Provides functions to search and retrieve anime/manga data from AniList API
"""

import AnilistPython
import logging
import requests
from typing import Dict, List, Optional, Any

class AnilistService:
    def __init__(self):
        """Initialize the AniList client"""
        try:
            self.anilist = AnilistPython.Anilist()
            logging.info("AniList integration initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize AniList integration: {str(e)}")
            self.anilist = None
    
    def search_anime(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for anime on AniList and return formatted results
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
        
        Returns:
            List of dictionaries containing anime information
        """
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
                        formatted_result = self._format_anime_data(anime_data)
                        if formatted_result and formatted_result not in results:
                            results.append(formatted_result)
                            if len(results) >= limit:
                                break
                                
                except Exception as search_error:
                    logging.debug(f"Search variation '{search_query}' failed: {str(search_error)}")
                    continue
            
            return results
            
        except Exception as e:
            logging.error(f"Error searching anime '{query}': {str(e)}")
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
            
            return self._format_anime_data(anime_data)
            
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
    
    def _format_anime_data(self, anime_data: Any) -> Dict[str, Any]:
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
            
            return {
                'title': title,
                'description': description,
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

# Global instance
anilist_service = AnilistService()