#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk menambahkan kolom show_in_sidebar ke tabel menu_permissions
Jalankan script ini untuk menambahkan kolom secara otomatis
"""

import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config.database import db
from sqlalchemy import text, inspect

def add_show_in_sidebar_column():
    """Add show_in_sidebar column to menu_permissions table"""
    try:
        app = create_app()
        with app.app_context():
            # Check if column already exists
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('menu_permissions')]
            
            if 'show_in_sidebar' in columns:
                print("✓ Kolom show_in_sidebar sudah ada di database")
                return True
            
            print("Menambahkan kolom show_in_sidebar ke tabel menu_permissions...")
            
            # Add column with default value True
            with db.engine.connect() as conn:
                # MySQL syntax
                conn.execute(text("""
                    ALTER TABLE menu_permissions 
                    ADD COLUMN show_in_sidebar BOOLEAN DEFAULT TRUE NOT NULL
                """))
                conn.commit()
            
            print("✓ Kolom show_in_sidebar berhasil ditambahkan")
            
            # Update existing records to have show_in_sidebar = True (default)
            with db.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE menu_permissions 
                    SET show_in_sidebar = TRUE 
                    WHERE show_in_sidebar IS NULL
                """))
                conn.commit()
            
            print("✓ Data existing berhasil diupdate dengan nilai default")
            print("\n✅ Migration berhasil!")
            return True
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Migration: Menambahkan kolom show_in_sidebar")
    print("=" * 60)
    success = add_show_in_sidebar_column()
    if not success:
        sys.exit(1)

