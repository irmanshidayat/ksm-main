#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Migration Script untuk Gmail Integration
Menjalankan migration untuk menambah field Gmail ke tabel users
"""

import os
import sys
import logging
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config.database import db, init_database
from models.knowledge_base import User, EmailLog
from flask import Flask

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run Gmail integration migration"""
    try:
        # Initialize Flask app
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql://root:@localhost:3306/KSM_main')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize database
        db.init_app(app)
        
        with app.app_context():
            logger.info("🚀 Starting Gmail integration migration...")
            
            # Check if Gmail fields already exist
            inspector = db.inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('users')]
            
            gmail_columns = ['gmail_refresh_token', 'gmail_access_token', 'gmail_token_expires_at', 'gmail_connected']
            missing_columns = [col for col in gmail_columns if col not in existing_columns]
            
            if missing_columns:
                logger.info(f"📝 Adding missing Gmail columns: {missing_columns}")
                
                # Add Gmail columns to users table
                if 'gmail_refresh_token' not in existing_columns:
                    with db.engine.connect() as conn:
                        conn.execute(db.text("ALTER TABLE users ADD COLUMN gmail_refresh_token TEXT"))
                    logger.info("✅ Added gmail_refresh_token column")
                
                if 'gmail_access_token' not in existing_columns:
                    with db.engine.connect() as conn:
                        conn.execute(db.text("ALTER TABLE users ADD COLUMN gmail_access_token TEXT"))
                    logger.info("✅ Added gmail_access_token column")
                
                if 'gmail_token_expires_at' not in existing_columns:
                    with db.engine.connect() as conn:
                        conn.execute(db.text("ALTER TABLE users ADD COLUMN gmail_token_expires_at DATETIME"))
                    logger.info("✅ Added gmail_token_expires_at column")
                
                if 'gmail_connected' not in existing_columns:
                    with db.engine.connect() as conn:
                        conn.execute(db.text("ALTER TABLE users ADD COLUMN gmail_connected BOOLEAN DEFAULT FALSE"))
                    logger.info("✅ Added gmail_connected column")
                
                # Update existing users to set gmail_connected = FALSE
                with db.engine.connect() as conn:
                    conn.execute(db.text("UPDATE users SET gmail_connected = FALSE WHERE gmail_connected IS NULL"))
                logger.info("✅ Updated existing users with gmail_connected = FALSE")
                
                # Add indexes
                try:
                    with db.engine.connect() as conn:
                        conn.execute(db.text("CREATE INDEX idx_gmail_connected ON users(gmail_connected)"))
                    logger.info("✅ Added index on gmail_connected")
                except Exception as e:
                    logger.warning(f"⚠️ Index idx_gmail_connected might already exist: {e}")
                
                try:
                    with db.engine.connect() as conn:
                        conn.execute(db.text("CREATE INDEX idx_gmail_token_expires ON users(gmail_token_expires_at)"))
                    logger.info("✅ Added index on gmail_token_expires_at")
                except Exception as e:
                    logger.warning(f"⚠️ Index idx_gmail_token_expires might already exist: {e}")
            else:
                logger.info("✅ All Gmail columns already exist")
            
            # Check if email_logs table exists
            if 'email_logs' not in inspector.get_table_names():
                logger.info("📝 Creating email_logs table...")
                
                # Create email_logs table
                with db.engine.connect() as conn:
                    conn.execute(db.text("""
                        CREATE TABLE email_logs (
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            user_id INT NOT NULL,
                            vendor_email VARCHAR(255) NOT NULL,
                            subject TEXT NOT NULL,
                            status ENUM('sent', 'failed', 'pending') DEFAULT 'pending',
                            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            error_message TEXT,
                            message_id VARCHAR(255),
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                            INDEX idx_user_id (user_id),
                            INDEX idx_vendor_email (vendor_email),
                            INDEX idx_status (status),
                            INDEX idx_sent_at (sent_at)
                        )
                    """))
                logger.info("✅ Created email_logs table")
            else:
                logger.info("✅ email_logs table already exists")
            
            logger.info("🎉 Gmail integration migration completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
