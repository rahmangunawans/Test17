"""
IQiyi Scrapers Package

This package contains all IQiyi-related scraping functionality organized by purpose:

- extractors/: Core extraction modules for M3U8, DASH, and player data
- scrapers/: Different scraping strategies and fallback methods  
- utils/: Helper scripts for database operations and episode management
- legacy/: Deprecated or alternative implementations
"""

from .extractors.enhanced_iqiyi_extractor import EnhancedIQiyiExtractor
from .scrapers.iqiyi_scraper import scrape_iqiyi_episode, scrape_iqiyi_playlist
from .scrapers.iqiyi_m3u8_scraper import IQiyiM3U8Scraper

__version__ = "1.0.0"
__all__ = ["EnhancedIQiyiExtractor", "scrape_iqiyi_episode", "scrape_iqiyi_playlist", "IQiyiM3U8Scraper"]