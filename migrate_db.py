#!/usr/bin/env python3
"""
Database migration script to add new columns to Content model
"""
import os
import sys
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)

def migrate_database():
    try:
        # Get DATABASE_URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logging.error("DATABASE_URL not found")
            return False
            
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if content table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'content'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                logging.info("Content table doesn't exist. Creating from models...")
                # Import and create tables using SQLAlchemy
                from app import app, db
                with app.app_context():
                    db.create_all()
                    logging.info("All tables created successfully")
                return True
            
            # Table exists, check for new columns
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'content'
            """))
            existing_columns = [row[0] for row in result]
            
            new_columns = ['total_episodes', 'studio', 'status']
            missing_columns = [col for col in new_columns if col not in existing_columns]
            
            if missing_columns:
                logging.info(f"Adding missing columns: {missing_columns}")
                trans = conn.begin()
                try:
                    if 'total_episodes' in missing_columns:
                        conn.execute(text('ALTER TABLE content ADD COLUMN total_episodes INTEGER'))
                        logging.info("Added total_episodes column")
                    
                    if 'studio' in missing_columns:
                        conn.execute(text('ALTER TABLE content ADD COLUMN studio VARCHAR(200)'))
                        logging.info("Added studio column")
                    
                    if 'status' in missing_columns:
                        conn.execute(text("ALTER TABLE content ADD COLUMN status VARCHAR(20) DEFAULT 'unknown'"))
                        logging.info("Added status column")
                    
                    trans.commit()
                    logging.info("Migration completed successfully")
                    return True
                except Exception as e:
                    trans.rollback()
                    logging.error(f"Migration failed: {e}")
                    return False
            else:
                logging.info("All columns already exist")
                return True
                
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)