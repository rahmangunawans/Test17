#!/usr/bin/env python3
"""
Debug script to test IQiyi M3U8 extraction
"""

import sys
import os
sys.path.append('.')

from iqiyi_scrapers.extractors.iqiyi_play_extractor import extract_m3u8_from_iqiyi_play_url
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

def test_iqiyi_extraction():
    """Test IQiyi extraction with debug output"""
    test_url = "https://www.iq.com/play/super-cube-episode-1-11eihk07dr8?lang=en_us"
    
    print(f"🧪 Testing IQiyi extraction with: {test_url}")
    
    result = extract_m3u8_from_iqiyi_play_url(test_url)
    
    print("\n" + "="*50)
    print("EXTRACTION RESULT:")
    print("="*50)
    print(f"Success: {result.get('success')}")
    print(f"Method: {result.get('method')}")
    print(f"Error: {result.get('error')}")
    
    if result.get('success') and result.get('m3u8_content'):
        m3u8_content = result['m3u8_content']
        print(f"M3U8 Length: {len(m3u8_content)} characters")
        print(f"M3U8 Preview: {m3u8_content[:200]}...")
    
    return result

if __name__ == '__main__':
    test_iqiyi_extraction()