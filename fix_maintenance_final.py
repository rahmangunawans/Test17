#!/usr/bin/env python3
"""
Final fix for maintenance mode - disable it permanently
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def fix_maintenance_permanently():
    """Fix maintenance mode permanently by direct database operation"""
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("No DATABASE_URL found in environment")
            return False
        
        # Create direct database connection
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create system_settings table if it doesn't exist
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS system_settings (
            id SERIAL PRIMARY KEY,
            setting_key VARCHAR(100) UNIQUE NOT NULL,
            setting_value TEXT,
            setting_type VARCHAR(20) DEFAULT 'text',
            description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        session.execute(text(create_table_sql))
        session.commit()
        print("✓ System settings table created/verified")
        
        # Insert or update maintenance_enabled setting
        upsert_sql = """
        INSERT INTO system_settings (setting_key, setting_value, setting_type, description)
        VALUES ('maintenance_enabled', 'false', 'boolean', 'Enable or disable maintenance mode')
        ON CONFLICT (setting_key) 
        DO UPDATE SET setting_value = 'false', updated_at = CURRENT_TIMESTAMP;
        """
        session.execute(text(upsert_sql))
        session.commit()
        print("✓ Maintenance mode disabled successfully")
        
        # Verify the setting
        result = session.execute(text("SELECT setting_value FROM system_settings WHERE setting_key = 'maintenance_enabled'")).fetchone()
        if result:
            print(f"✓ Verified: maintenance_enabled = {result[0]}")
        else:
            print("✗ Could not verify setting")
            
        session.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing maintenance mode permanently...")
    if fix_maintenance_permanently():
        print("✅ Maintenance mode has been disabled!")
        print("🎉 Application should now be accessible to all users")
    else:
        print("❌ Failed to disable maintenance mode")
        sys.exit(1)