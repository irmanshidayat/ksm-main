#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script untuk menambahkan relasi vendor-user
Menambahkan kolom vendor_id ke tabel users dan user_id ke tabel vendors
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db
import app
import logging

logger = logging.getLogger(__name__)

def migrate_add_vendor_user_relationship():
    """Menambahkan relasi vendor-user ke database"""
    try:
        # Gunakan app yang sudah ada
        with app.app.app_context():
            # Tambahkan kolom vendor_id ke tabel users
            with db.engine.connect() as connection:
                connection.execute(db.text("""
                    ALTER TABLE users 
                    ADD COLUMN vendor_id INT NULL,
                    ADD CONSTRAINT fk_users_vendor_id 
                    FOREIGN KEY (vendor_id) REFERENCES vendors(id) 
                    ON DELETE SET NULL
                """))
                connection.commit()
            logger.info("✅ Added vendor_id column to users table")
            
            # Tambahkan kolom user_id ke tabel vendors
            with db.engine.connect() as connection:
                connection.execute(db.text("""
                    ALTER TABLE vendors 
                    ADD COLUMN user_id INT NULL,
                    ADD CONSTRAINT fk_vendors_user_id 
                    FOREIGN KEY (user_id) REFERENCES users(id) 
                    ON DELETE SET NULL
                """))
                connection.commit()
            logger.info("✅ Added user_id column to vendors table")
            
            logger.info("✅ Migration completed successfully")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        db.session.rollback()
        raise e

if __name__ == "__main__":
    migrate_add_vendor_user_relationship()
