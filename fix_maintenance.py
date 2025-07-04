#!/usr/bin/env python3
"""
Script to fix maintenance mode setting in the database
"""

import logging
from app import app, db
from models import SystemSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_maintenance_mode():
    """Fix maintenance mode setting in the database"""
    with app.app_context():
        try:
            # Create all tables first
            db.create_all()
            logger.info("✓ All tables created successfully")
            
            # Add/update system settings with correct keys
            settings_data = [
                ('maintenance_enabled', 'false', 'boolean', 'Enable or disable maintenance mode'),
                ('maintenance_message', 'AniFlix is currently under maintenance. Please check back later.', 'text', 'Message displayed during maintenance mode'),
                ('site_logo_url', '', 'url', 'URL for the site logo'),
                ('site_logo_alt', 'AniFlix Pro', 'text', 'Alt text for the site logo'),
                ('site_title', 'AniFlix Pro', 'text', 'Site title displayed in browser'),
                ('site_description', 'Premium anime streaming platform', 'text', 'Site description')
            ]
            
            for key, value, setting_type, description in settings_data:
                SystemSettings.set_setting(key, value, setting_type, description)
                logger.info(f"✓ Setting '{key}' updated successfully")
            
            logger.info("✓ All system settings updated successfully")
            logger.info("✓ Maintenance mode disabled")
            
        except Exception as e:
            logger.error(f"Error fixing maintenance mode: {e}")
            raise

if __name__ == "__main__":
    fix_maintenance_mode()