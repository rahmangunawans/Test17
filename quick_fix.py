#!/usr/bin/env python3
"""
Quick fix for maintenance mode - direct database approach
"""

import psycopg2
import os

def fix_maintenance_direct():
    """Fix maintenance mode using direct database connection"""
    try:
        # Get Supabase connection details
        supabase_password = "FpBcsaV9sOVXVZHsI4AkZsJDCBUDKFXDhgJEYXGZBTIWPRWXBZNMZBXJWUKZOYHBQHKJOFKQPGKUHJZUIKJIKJFGDRTYUP"
        conn_string = f"postgresql://postgres.heotmyzuxabzfobirhnm:{supabase_password}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
        
        print("Connecting to Supabase...")
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()
        
        # Create system_settings table if not exists
        cur.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            id SERIAL PRIMARY KEY,
            setting_key VARCHAR(100) UNIQUE NOT NULL,
            setting_value TEXT,
            setting_type VARCHAR(20) DEFAULT 'text',
            description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Insert/update maintenance setting to false
        cur.execute("""
        INSERT INTO system_settings (setting_key, setting_value, setting_type, description)
        VALUES ('maintenance_enabled', 'false', 'boolean', 'Enable or disable maintenance mode')
        ON CONFLICT (setting_key) DO UPDATE SET 
            setting_value = 'false',
            updated_at = CURRENT_TIMESTAMP
        """)
        
        # Add other required settings
        settings = [
            ('site_title', 'AniFlix Pro', 'text', 'Site title'),
            ('site_description', 'Premium anime streaming platform', 'text', 'Site description'),
            ('site_logo_url', '', 'url', 'Logo URL'),
            ('site_logo_alt', 'AniFlix Pro', 'text', 'Logo alt text'),
            ('maintenance_message', 'AniFlix is currently under maintenance. Please check back later.', 'text', 'Maintenance message')
        ]
        
        for key, value, setting_type, desc in settings:
            cur.execute("""
            INSERT INTO system_settings (setting_key, setting_value, setting_type, description)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (setting_key) DO UPDATE SET 
                setting_value = EXCLUDED.setting_value,
                updated_at = CURRENT_TIMESTAMP
            """, (key, value, setting_type, desc))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("✅ Maintenance mode berhasil dinonaktifkan!")
        print("✅ System settings telah dikonfigurasi!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    fix_maintenance_direct()