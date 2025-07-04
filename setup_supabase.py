#!/usr/bin/env python3
"""
Quick setup script for Supabase database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def setup_supabase():
    """Setup Supabase database with required tables and settings"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✓ Tables created")
            
            # Create system settings directly using SQL
            from sqlalchemy import text
            
            # Insert default system settings
            settings = [
                ('maintenance_enabled', 'false', 'boolean', 'Enable or disable maintenance mode'),
                ('maintenance_message', 'AniFlix is currently under maintenance. Please check back later.', 'text', 'Message displayed during maintenance mode'),
                ('site_logo_url', '', 'url', 'URL for the site logo'),
                ('site_logo_alt', 'AniFlix Pro', 'text', 'Alt text for the site logo'),
                ('site_title', 'AniFlix Pro', 'text', 'Site title displayed in browser'),
                ('site_description', 'Premium anime streaming platform', 'text', 'Site description')
            ]
            
            for key, value, setting_type, description in settings:
                # Use raw SQL to avoid model issues
                sql = text("""
                INSERT INTO system_settings (setting_key, setting_value, setting_type, description, created_at, updated_at)
                VALUES (:key, :value, :type, :desc, NOW(), NOW())
                ON CONFLICT (setting_key) DO UPDATE SET
                    setting_value = EXCLUDED.setting_value,
                    updated_at = NOW()
                """)
                db.session.execute(sql, {
                    'key': key,
                    'value': value,
                    'type': setting_type,
                    'desc': description
                })
            
            db.session.commit()
            print("✓ System settings configured")
            print("✓ Maintenance mode disabled")
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    return True

if __name__ == "__main__":
    success = setup_supabase()
    if success:
        print("✓ Supabase setup complete")
    else:
        print("✗ Supabase setup failed")