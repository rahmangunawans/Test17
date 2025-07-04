#!/usr/bin/env python3
"""
Script to create admin user and disable maintenance mode
"""

from app import app, db
from sqlalchemy import text
from werkzeug.security import generate_password_hash

def setup_admin_and_disable_maintenance():
    """Create admin user and disable maintenance mode"""
    with app.app_context():
        try:
            # First, create all tables
            db.create_all()
            print("✅ Tables created")
            
            # Create system_settings table and disable maintenance
            settings_sql = text("""
            INSERT INTO system_settings (setting_key, setting_value, setting_type, description, created_at, updated_at)
            VALUES 
                ('maintenance_enabled', 'false', 'boolean', 'Enable or disable maintenance mode', NOW(), NOW()),
                ('site_title', 'AniFlix Pro', 'text', 'Site title', NOW(), NOW()),
                ('site_description', 'Premium anime streaming platform', 'text', 'Site description', NOW(), NOW()),
                ('site_logo_url', '', 'url', 'Logo URL', NOW(), NOW()),
                ('site_logo_alt', 'AniFlix Pro', 'text', 'Logo alt text', NOW(), NOW()),
                ('maintenance_message', 'AniFlix is currently under maintenance. Please check back later.', 'text', 'Maintenance message', NOW(), NOW())
            ON CONFLICT (setting_key) DO UPDATE SET 
                setting_value = EXCLUDED.setting_value,
                updated_at = NOW()
            """)
            db.session.execute(settings_sql)
            
            # Create admin user
            admin_email = "admin@aniflix.com"
            admin_password = "admin123"
            password_hash = generate_password_hash(admin_password)
            
            admin_sql = text("""
            INSERT INTO "user" (username, email, password_hash, is_admin, created_at)
            VALUES ('admin', :email, :password_hash, true, NOW())
            ON CONFLICT (email) DO UPDATE SET 
                password_hash = EXCLUDED.password_hash,
                is_admin = true
            """)
            db.session.execute(admin_sql, {
                'email': admin_email,
                'password_hash': password_hash
            })
            
            db.session.commit()
            
            print("✅ Maintenance mode disabled!")
            print("✅ Admin user created:")
            print(f"   Email: {admin_email}")
            print(f"   Password: {admin_password}")
            print("✅ You can now login as admin!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    setup_admin_and_disable_maintenance()