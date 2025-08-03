#!/usr/bin/env python3
"""
Test improved scraper dengan URL episode Lazarus
"""

from iqiyi_scrapers.scrapers.enhanced_iqiyi_scraper import EnhancedIQiyiScraper

def test_lazarus_episode():
    """Test scraper dengan episode URL Lazarus"""
    url = "https://www.iq.com/play/lazarus-episode-1-1l0n170m0qc?lang=en_us"
    
    print(f"🧪 Testing improved scraper with: {url}")
    
    scraper = EnhancedIQiyiScraper(url)
    episodes = scraper.extract_all_episodes(max_episodes=5)
    
    print(f"\n📊 Results:")
    print(f"Episodes found: {len(episodes)}")
    
    for i, episode in enumerate(episodes, 1):
        print(f"\n📺 Episode {i}:")
        print(f"  Title: {episode.title}")
        print(f"  Episode Number: {episode.episode_number}")
        print(f"  URL: {episode.url}")
        print(f"  Content Type: {episode.content_type}")
        print(f"  Valid: {episode.is_valid}")

if __name__ == "__main__":
    test_lazarus_episode()