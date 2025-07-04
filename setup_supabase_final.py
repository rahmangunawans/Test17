#!/usr/bin/env python3
"""
Setup script for Supabase database - final configuration
"""

from app import app, db
from models import SystemSettings
import logging

logging.basicConfig(level=logging.INFO)

def setup_supabase_database():
    """Setup Supabase database with all required tables and settings"""
    with app.app_context():
        try:
            print("Setting up Supabase database...")
            
            # Create all tables
            db.create_all()
            print("✅ All database tables created successfully")
            
            # Configure system settings to disable maintenance mode
            settings_to_create = [
                ('maintenance_enabled', 'false', 'boolean', 'Enable or disable maintenance mode'),
                ('site_title', 'AniFlix Pro', 'text', 'Site title displayed in browser'),
                ('site_description', 'Premium anime streaming platform', 'text', 'Site description'),
                ('site_logo_url', '', 'url', 'URL for the site logo'),
                ('site_logo_alt', 'AniFlix Pro', 'text', 'Alt text for the site logo'),
                ('maintenance_message', 'AniFlix is currently under maintenance. Please check back later.', 'text', 'Message displayed during maintenance mode')
            ]
            
            for key, value, setting_type, description in settings_to_create:
                SystemSettings.set_setting(key, value, setting_type, description)
                print(f"✅ Setting '{key}' configured")
            
            print("✅ Supabase database setup completed successfully!")
            print("✅ Maintenance mode has been disabled")
            print("✅ AniFlix application is ready to use with Supabase database")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up Supabase database: {e}")
            return False

if __name__ == "__main__":
    success = setup_supabase_database()
    if success:
        print("\n🎉 Supabase setup completed! Your AniFlix application is now running with Supabase database.")
    else:
        print("\n❌ Supabase setup failed. Please check the error messages above.")