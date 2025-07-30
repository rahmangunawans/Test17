import logging
from iqiyi_api_original import iqiyi_api
from typing import Optional, List, Dict

class IqiyiIntegration:
    def __init__(self):
        """Initialize IQiyi integration with original API"""
        self.api = iqiyi_api
        logging.info("IQiyi integration initialized with original API")

    def get_m3u8_url(self, iqiyi_url: str) -> Optional[str]:
        """
        Extract M3U8 streaming URL from IQiyi video page using original API
        
        Args:
            iqiyi_url: IQiyi video URL
            
        Returns:
            M3U8 URL if found, None otherwise
        """
        try:
            logging.info(f"Using original API to extract M3U8 from: {iqiyi_url}")
            
            # Use the original API to get M3U8 URL
            m3u8_url = self.api.get_m3u8_url(iqiyi_url)
            
            if m3u8_url:
                logging.info(f"Successfully extracted M3U8 URL: {m3u8_url}")
                return m3u8_url
            else:
                logging.info("No M3U8 URL found - using iframe fallback")
                return None
            
        except Exception as e:
            logging.error(f"Error extracting M3U8 from IQiyi using original API: {e}")
            return None

    def get_subtitles(self, iqiyi_url: str, subtitle_type: str = "srt") -> List[Dict]:
        """
        Extract subtitles from IQiyi video page using original API
        
        Args:
            iqiyi_url: IQiyi video URL
            subtitle_type: Type of subtitles to extract (srt, vtt, etc.)
            
        Returns:
            List of subtitle dictionaries
        """
        try:
            logging.info(f"Using original API to extract subtitles from: {iqiyi_url}")
            
            # Use the original API to get subtitles
            subtitles = self.api.get_subtitles(iqiyi_url, subtitle_type)
            
            if subtitles:
                logging.info(f"Successfully extracted {len(subtitles)} subtitles")
                return subtitles
            else:
                logging.info("No subtitles found")
                return []
            
        except Exception as e:
            logging.error(f"Error extracting subtitles from IQiyi using original API: {e}")
            return []

# Create global instance
iqiyi_integration = IqiyiIntegration()