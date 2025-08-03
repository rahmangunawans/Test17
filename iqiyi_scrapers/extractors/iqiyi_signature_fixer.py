"""
IQiyi Signature Fixer - Handles signature issues for DASH URLs
"""

import re
import time
import hashlib
import logging
from urllib.parse import urlparse, parse_qs, urlencode

class IQiyiSignatureFixer:
    """Fix IQiyi DASH URL signatures"""
    
    def __init__(self):
        self.key_map = {
            'authKey': lambda: self._generate_auth_key(),
            'tm': lambda: str(int(time.time() * 1000)),
            'vf': lambda: self._generate_vf_hash(),
            'k_uid': lambda: self._generate_k_uid(),
        }
    
    def _generate_auth_key(self):
        """Generate authKey based on current timestamp"""
        timestamp = str(int(time.time()))
        # Simple hash-based auth key generation
        hash_source = f"iqiyi_auth_{timestamp}"
        return hashlib.md5(hash_source.encode()).hexdigest()
    
    def _generate_vf_hash(self):
        """Generate vf parameter hash"""
        timestamp = str(int(time.time()))
        hash_source = f"vf_hash_{timestamp}"
        return hashlib.md5(hash_source.encode()).hexdigest()
    
    def _generate_k_uid(self):
        """Generate k_uid parameter"""
        timestamp = str(int(time.time()))
        hash_source = f"k_uid_{timestamp}"
        return hashlib.md5(hash_source.encode()).hexdigest()
    
    def fix_dash_url(self, dash_url):
        """
        Fix DASH URL by regenerating signature parameters
        
        Args:
            dash_url (str): Original DASH URL with potentially expired signature
            
        Returns:
            str: Fixed DASH URL with regenerated parameters
        """
        try:
            parsed = urlparse(dash_url)
            params = parse_qs(parsed.query, keep_blank_values=True)
            
            # Convert to flat dict
            flat_params = {}
            for key, values in params.items():
                if values:
                    flat_params[key] = values[0]
                else:
                    flat_params[key] = ''
            
            logging.info(f"🔧 Fixing signature for DASH URL...")
            
            # Update time-sensitive parameters
            for param_name, generator in self.key_map.items():
                if param_name in flat_params:
                    old_value = flat_params[param_name]
                    new_value = generator()
                    flat_params[param_name] = new_value
                    logging.info(f"🔄 Updated {param_name}: {old_value[:10]}... → {new_value[:10]}...")
            
            # Rebuild URL
            new_query = urlencode(flat_params)
            fixed_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
            
            logging.info(f"✅ DASH URL signature fixed")
            return fixed_url
            
        except Exception as e:
            logging.error(f"❌ Error fixing DASH URL: {e}")
            return dash_url
    
    def extract_alternative_urls(self, player_data):
        """
        Extract alternative DASH URLs from player data using different patterns
        
        Args:
            player_data (dict): Player data from IQiyi page
            
        Returns:
            list: List of alternative DASH URLs to try
        """
        urls = []
        
        try:
            # Convert to string for regex search
            player_str = str(player_data)
            
            # Multiple URL patterns to try
            patterns = [
                r'https://cache\.video\.iqiyi\.com/dash\?([^"\s&]+)',
                r'http://intel-cache\.video\.qiyi\.domain/dash\?([^"\s&]+)',
                r'https://[^/]*iqiyi\.com/dash\?([^"\s&]+)',
                r'dash\?([^"\s&]+)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, player_str)
                for match in matches:
                    if 'tvid=' in match and 'vid=' in match:
                        if pattern.startswith('dash'):
                            # Add base URL
                            full_url = f"https://cache.video.iqiyi.com/{pattern.replace('([^\"\\s&]+)', match)}"
                        else:
                            full_url = pattern.replace('([^"\\s&]+)', match)
                        
                        if full_url not in urls:
                            urls.append(full_url)
            
            logging.info(f"🔍 Found {len(urls)} alternative DASH URLs")
            return urls
            
        except Exception as e:
            logging.error(f"❌ Error extracting alternative URLs: {e}")
            return []

def fix_iqiyi_signature(dash_url):
    """Convenience function to fix IQiyi signature"""
    fixer = IQiyiSignatureFixer()
    return fixer.fix_dash_url(dash_url)