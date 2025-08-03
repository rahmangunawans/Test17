#!/usr/bin/env python3
"""
Test enhanced function dengan URL episode Lazarus
"""

from iqiyi_scrapers.scrapers.enhanced_iqiyi_scraper import scrape_all_episodes_playlist

def test_enhanced_function():
    """Test enhanced function dengan episode URL Lazarus"""
    url = "https://www.iq.com/play/lazarus-episode-1-1l0n170m0qc?lang=en_us"
    
    print(f"🧪 Testing enhanced function with: {url}")
    
    result = scrape_all_episodes_playlist(url, max_episodes=5)
    
    print(f"\n📊 Function Result:")
    print(f"Success: {result.get('success')}")
    print(f"Total Episodes: {result.get('total_episodes')}")
    print(f"Valid Episodes: {result.get('valid_episodes')}")
    print(f"Message: {result.get('message')}")
    
    if result.get('success') and result.get('episodes'):
        episodes = result['episodes']
        print(f"\n📺 Episodes Details:")
        for i, episode in enumerate(episodes, 1):
            print(f"  Episode {i}: {episode['title']} (Episode #{episode['episode_number']})")

if __name__ == "__main__":
    test_enhanced_function()