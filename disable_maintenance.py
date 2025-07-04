#!/usr/bin/env python3
"""
Script to disable maintenance mode directly in Supabase database
"""

from app import app, db
from sqlalchemy import text

def disable_maintenance():
    """Disable maintenance mode directly in database"""
    with app.app_context():
        try:
            # Create system_settings table if it doesn't exist
            create_table_sql = text("""
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
            db.session.execute(create_table_sql)
            
            # Insert/update maintenance setting
            maintenance_sql = text("""
            INSERT INTO system_settings (setting_key, setting_value, setting_type, description)
            VALUES ('maintenance_enabled', 'false', 'boolean', 'Enable or disable maintenance mode')
            ON CONFLICT (setting_key) DO UPDATE SET 
                setting_value = 'false',
                updated_at = CURRENT_TIMESTAMP
            """)
            db.session.execute(maintenance_sql)
            
            # Add other required settings
            other_settings = [
                ('site_title', 'AniFlix Pro', 'text', 'Site title'),
                ('site_description', 'Premium anime streaming platform', 'text', 'Site description'),
                ('site_logo_url', '', 'url', 'Logo URL'),
                ('site_logo_alt', 'AniFlix Pro', 'text', 'Logo alt text'),
                ('maintenance_message', 'AniFlix is currently under maintenance. Please check back later.', 'text', 'Maintenance message')
            ]
            
            for key, value, setting_type, desc in other_settings:
                setting_sql = text("""
                INSERT INTO system_settings (setting_key, setting_value, setting_type, description)
                VALUES (:key, :value, :type, :desc)
                ON CONFLICT (setting_key) DO UPDATE SET 
                    setting_value = EXCLUDED.setting_value,
                    updated_at = CURRENT_TIMESTAMP
                """)
                db.session.execute(setting_sql, {
                    'key': key, 'value': value, 'type': setting_type, 'desc': desc
                })
            
            db.session.commit()
            print("✅ Maintenance mode berhasil dinonaktifkan!")
            print("✅ Sistem setting lainnya telah dikonfigurasi!")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    disable_maintenance()