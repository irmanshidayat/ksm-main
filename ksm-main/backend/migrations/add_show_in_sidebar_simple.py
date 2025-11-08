#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script sederhana untuk menambahkan kolom show_in_sidebar
Menggunakan koneksi database langsung
"""

import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_column():
    """Add show_in_sidebar column directly using SQL"""
    try:
        from sqlalchemy import create_engine, text, inspect
        import pymysql
        
        # Database config - sesuaikan dengan .env Anda
        # Atau ambil dari environment variables
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = int(os.getenv('DB_PORT', 3306))
        db_user = os.getenv('DB_USER', 'root')
        db_password = os.getenv('DB_PASSWORD', '')
        db_name = os.getenv('DB_NAME', 'ksm_main')
        
        # Create connection string
        db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        print("Connecting to database...")
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Check if column exists
            inspector = inspect(engine)
            try:
                columns = [col['name'] for col in inspector.get_columns('menu_permissions')]
                
                if 'show_in_sidebar' in columns:
                    print("Column show_in_sidebar already exists!")
                    return True
            except Exception as e:
                print(f"Warning: Could not check columns: {e}")
            
            print("Adding column show_in_sidebar...")
            
            # Add column
            conn.execute(text("""
                ALTER TABLE menu_permissions 
                ADD COLUMN show_in_sidebar BOOLEAN DEFAULT TRUE NOT NULL
            """))
            conn.commit()
            print("Column added successfully!")
            
            # Update existing records
            conn.execute(text("""
                UPDATE menu_permissions 
                SET show_in_sidebar = TRUE 
                WHERE show_in_sidebar IS NULL
            """))
            conn.commit()
            print("Existing records updated!")
            print("\nMigration completed successfully!")
            return True
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nTrying to read from .env file...")
        
        # Try to read from .env file
        try:
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            if os.path.exists(env_path):
                from dotenv import load_dotenv
                load_dotenv(env_path)
                return add_column()
        except:
            pass
        
        print("\nPlease set environment variables:")
        print("DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME")
        print("\nOr run this SQL directly in MySQL:")
        print("ALTER TABLE menu_permissions ADD COLUMN show_in_sidebar BOOLEAN DEFAULT TRUE NOT NULL;")
        print("UPDATE menu_permissions SET show_in_sidebar = TRUE WHERE show_in_sidebar IS NULL;")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Adding show_in_sidebar column to menu_permissions")
    print("=" * 60)
    success = add_column()
    sys.exit(0 if success else 1)

