#!/usr/bin/env python3
"""
Database migration script to add SystemSettings table
"""

import logging
from app import app, db
from models import SystemSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_system_settings():
    """Create SystemSettings table and add default settings"""
    with app.app_context():
        try:
            # Create the SystemSettings table
            db.create_all()
            logger.info("✓ SystemSettings table created successfully")
            
            # Add default system settings
            default_settings = [
                {
                    'key': 'maintenance_enabled',
                    'value': 'false',
                    'type': 'boolean',
                    'description': 'Enable or disable maintenance mode'
                },
                {
                    'key': 'maintenance_message',
                    'value': 'AniFlix is currently under maintenance. Please check back later.',
                    'type': 'text',
                    'description': 'Message displayed during maintenance mode'
                },
                {
                    'key': 'site_logo_url',
                    'value': '',
                    'type': 'url',
                    'description': 'URL for the site logo'
                },
                {
                    'key': 'site_logo_alt',
                    'value': 'AniFlix',
                    'type': 'text',
                    'description': 'Alt text for the site logo'
                },
                {
                    'key': 'site_title',
                    'value': 'AniFlix',
                    'type': 'text',
                    'description': 'Site title displayed in browser'
                },
                {
                    'key': 'site_description',
                    'value': 'Your premium anime and movie streaming platform',
                    'type': 'text',
                    'description': 'Site description for SEO'
                }
            ]
            
            for setting in default_settings:
                existing_setting = SystemSettings.query.filter_by(setting_key=setting['key']).first()
                if not existing_setting:
                    SystemSettings.set_setting(
                        setting['key'],
                        setting['value'],
                        setting['type'],
                        setting['description']
                    )
                    logger.info(f"✓ Added default setting: {setting['key']}")
                else:
                    logger.info(f"- Setting already exists: {setting['key']}")
            
            logger.info("✓ SystemSettings migration completed successfully")
            
        except Exception as e:
            logger.error(f"✗ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate_system_settings()