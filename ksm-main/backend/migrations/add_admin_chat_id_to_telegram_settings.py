#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration Script: Add admin_chat_id to telegram_settings table
Date: 2025-10-23
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.knowledge_base import TelegramSettings
from sqlalchemy import text

def migrate_up():
    """Add admin_chat_id column to telegram_settings"""
    try:
        with app.app_context():
            # Check if column already exists
            result = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name='telegram_settings' 
                AND column_name='admin_chat_id'
            """))
            
            exists = result.scalar() > 0
            
            if not exists:
                print("Adding admin_chat_id column to telegram_settings...")
                
                # Add column
                db.session.execute(text("""
                    ALTER TABLE telegram_settings 
                    ADD COLUMN admin_chat_id VARCHAR(50) AFTER bot_token
                """))
                
                # Add created_at if not exists
                result = db.session.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name='telegram_settings' 
                    AND column_name='created_at'
                """))
                
                if result.scalar() == 0:
                    db.session.execute(text("""
                        ALTER TABLE telegram_settings 
                        ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    """))
                
                db.session.commit()
                print("✅ Migration completed successfully!")
                
                # Update with default values from .env
                print("\nUpdating with default values...")
                db.session.execute(text("""
                    UPDATE telegram_settings 
                    SET admin_chat_id = '2054126414',
                        bot_token = '8264344936:AAHBfdR91MnivmVYVKvQGhRYAzjKZYz4MoY',
                        is_active = 1
                    WHERE company_id = 'PT. Kian Santang Muliatama'
                """))
                db.session.commit()
                print("✅ Default values updated!")
                
            else:
                print("⚠️  Column admin_chat_id already exists. Skipping migration.")
                
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        db.session.rollback()
        raise

def migrate_down():
    """Remove admin_chat_id column from telegram_settings"""
    try:
        with app.app_context():
            print("Removing admin_chat_id column from telegram_settings...")
            
            db.session.execute(text("""
                ALTER TABLE telegram_settings 
                DROP COLUMN IF EXISTS admin_chat_id
            """))
            
            db.session.commit()
            print("✅ Rollback completed successfully!")
            
    except Exception as e:
        print(f"❌ Rollback failed: {str(e)}")
        db.session.rollback()
        raise

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migration: Add admin_chat_id to telegram_settings')
    parser.add_argument('action', choices=['up', 'down'], help='Migration action (up or down)')
    
    args = parser.parse_args()
    
    if args.action == 'up':
        migrate_up()
    elif args.action == 'down':
        migrate_down()

