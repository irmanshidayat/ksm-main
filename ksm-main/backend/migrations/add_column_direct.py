#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script sederhana untuk menambahkan kolom show_in_sidebar
Menggunakan koneksi database langsung tanpa import app
"""

import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_column():
    """Add show_in_sidebar column directly using SQL"""
    try:
        from sqlalchemy import create_engine, text
        from config.config import get_database_config
        
        # Get database config
        config = get_database_config()
        
        # Create connection string
        if config.get('type') == 'mysql':
            db_url = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        else:
            db_url = f"sqlite:///{config.get('database', 'ksm_main.db')}"
        
        print("Connecting to database...")
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Check if column exists
            from sqlalchemy import inspect
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('menu_permissions')]
            
            if 'show_in_sidebar' in columns:
                print("Column show_in_sidebar already exists!")
                return True
            
            print("Adding column show_in_sidebar...")
            
            # Add column
            if config.get('type') == 'mysql':
                conn.execute(text("""
                    ALTER TABLE menu_permissions 
                    ADD COLUMN show_in_sidebar BOOLEAN DEFAULT TRUE NOT NULL
                """))
            else:
                # SQLite doesn't support adding NOT NULL column directly
                conn.execute(text("""
                    ALTER TABLE menu_permissions 
                    ADD COLUMN show_in_sidebar BOOLEAN DEFAULT 1
                """))
            
            conn.commit()
            print("Column added successfully!")
            
            # Update existing records
            if config.get('type') == 'mysql':
                conn.execute(text("""
                    UPDATE menu_permissions 
                    SET show_in_sidebar = TRUE 
                    WHERE show_in_sidebar IS NULL
                """))
            else:
                conn.execute(text("""
                    UPDATE menu_permissions 
                    SET show_in_sidebar = 1 
                    WHERE show_in_sidebar IS NULL
                """))
            
            conn.commit()
            print("Existing records updated!")
            print("\nMigration completed successfully!")
            return True
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Adding show_in_sidebar column to menu_permissions")
    print("=" * 60)
    success = add_column()
    sys.exit(0 if success else 1)

