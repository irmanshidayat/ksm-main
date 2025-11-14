#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Migration Script
Migration untuk menambahkan kolom show_in_sidebar di tabel menu_permissions
"""

import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db
from domains.role.models.menu_models import MenuPermission
from shared.utils.logger import get_logger

logger = get_logger(__name__)


def add_show_in_sidebar_column():
    """Add show_in_sidebar column to menu_permissions table"""
    try:
        logger.info("Adding show_in_sidebar column to menu_permissions table...")
        
        # Check if column already exists
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('menu_permissions')]
        
        if 'show_in_sidebar' in columns:
            logger.info("Column show_in_sidebar already exists, skipping migration")
            return True
        
        # Add column with default value True
        with db.engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE menu_permissions 
                ADD COLUMN show_in_sidebar BOOLEAN DEFAULT TRUE NOT NULL
            """))
            conn.commit()
        
        # Update existing records to have show_in_sidebar = True (default)
        with db.engine.connect() as conn:
            conn.execute(text("""
                UPDATE menu_permissions 
                SET show_in_sidebar = TRUE 
                WHERE show_in_sidebar IS NULL
            """))
            conn.commit()
        
        logger.info("Successfully added show_in_sidebar column to menu_permissions table")
        return True
        
    except Exception as e:
        logger.error(f"Error adding show_in_sidebar column: {str(e)}")
        return False


def run_migration():
    """Run migration"""
    try:
        logger.info("Starting show_in_sidebar migration...")
        
        if not add_show_in_sidebar_column():
            logger.error("Failed to add show_in_sidebar column")
            return False
        
        logger.info("show_in_sidebar migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        success = run_migration()
        if success:
            print("Migration completed successfully!")
        else:
            print("Migration failed!")
            sys.exit(1)

