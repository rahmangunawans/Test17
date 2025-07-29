"""
AniList Integration for AniFlix
Provides functions to search and retrieve anime/manga data from AniList API
"""

import AnilistPython
import logging
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
            
            # Get studio information (not available in this API format, set empty)
            studio = ''
            
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
            
            return {
                'title': title,
                'description': description,
                'genre': genre_str,
                'year': year,
                'rating': rating,
                'content_type': content_type,
                'thumbnail_url': thumbnail_url,
                'trailer_url': '',  # AniList doesn't provide trailer URLs
                'studio': studio,
                'total_episodes': total_episodes,
                'status': status,
                'anilist_id': None,  # ID not provided in this API format
                'anilist_url': ''  # Cannot generate URL without ID
            }
        
        except Exception as e:
            logging.error(f"Error formatting anime data: {str(e)}")
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

# Global instance
anilist_service = AnilistService()