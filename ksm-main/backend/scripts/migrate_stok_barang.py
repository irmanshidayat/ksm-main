#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk migrate tabel stok_barang
Mengubah struktur dari format lama ke format baru sesuai model
"""

import os
import sys
from datetime import datetime

# Add parent directory to path untuk import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db
from flask import Flask

def create_app():
    """Create Flask app untuk database operations"""
    app = Flask(__name__)
    
    # Import config untuk mendapatkan environment detection
    from config.config import detect_environment, get_env_config
    
    # Detect environment
    env_mode = detect_environment()
    env_config = get_env_config()
    
    # Database configuration - menggunakan logic yang sama dengan init_database()
    db_user = os.getenv('DB_USER', 'root')
    # Handle DB_PASSWORD: jika empty string atau None, gunakan default berdasarkan environment
    db_password_raw = os.getenv('DB_PASSWORD')
    if db_password_raw is None or db_password_raw.strip() == '':
        # Jika tidak ter-set atau empty, gunakan default dari env_config
        # Docker mode: default password adalah 'admin123'
        # Local/XAMPP mode: default password adalah '' (kosong)
        db_password = env_config.get('DB_PASSWORD', 'admin123' if env_mode == 'docker' else '')
        if env_mode == 'docker':
            print(f"ℹ️  DB_PASSWORD not set in .env, using default: 'admin123' for Docker mode")
    else:
        db_password = db_password_raw
    
    db_host = os.getenv('DB_HOST') or env_config.get('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT') or str(env_config.get('DB_PORT', 3306))
    db_name = os.getenv('DB_NAME', 'KSM_main')
    charset = 'utf8mb4'
    
    mysql_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset={charset}"
    app.config['SQLALCHEMY_DATABASE_URI'] = mysql_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def migrate_stok_barang():
    """Migrate tabel stok_barang - menambahkan kolom yang diperlukan sesuai model"""
    print("🚀 Starting Stok Barang migration...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test database connection
            db.session.execute(db.text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Check existing columns
            result = db.session.execute(db.text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'KSM_main' 
                AND TABLE_NAME = 'stok_barang'
            """)).fetchall()
            
            existing_columns = [row[0] for row in result]
            print(f"📊 Existing columns: {existing_columns}")
            
            # Define required columns based on StokBarang model
            required_columns = {
                'barang_id': {
                    'type': 'INT',
                    'nullable': False,
                    'unique': True,
                    'foreign_key': 'barang(id)'
                },
                'jumlah_stok': {
                    'type': 'INT',
                    'nullable': False,
                    'default': 0
                },
                'stok_minimum': {
                    'type': 'INT',
                    'nullable': False,
                    'default': 0
                },
                'stok_maksimum': {
                    'type': 'INT',
                    'nullable': True
                },
                'last_updated': {
                    'type': 'DATETIME',
                    'nullable': True,
                    'default': 'CURRENT_TIMESTAMP'
                }
            }
            
            # Add missing columns
            migrations = []
            
            for col_name, col_config in required_columns.items():
                if col_name not in existing_columns:
                    # Untuk barang_id dengan UNIQUE constraint, tambahkan sebagai nullable dulu
                    if col_name == 'barang_id' and col_config.get('unique', False):
                        # Tambahkan nullable dulu, lalu populate, baru set NOT NULL dan UNIQUE
                        nullable_clause = ' NULL'
                        default_clause = ''
                        unique_clause = ''
                    else:
                        nullable_clause = '' if col_config.get('nullable', True) else ' NOT NULL'
                        default_clause = ''
                        if col_config.get('default') is not None:
                            if isinstance(col_config['default'], str):
                                if col_config['default'] == 'CURRENT_TIMESTAMP':
                                    default_clause = ' DEFAULT CURRENT_TIMESTAMP'
                                else:
                                    default_clause = f" DEFAULT '{col_config['default']}'"
                            else:
                                default_clause = f" DEFAULT {col_config['default']}"
                        unique_clause = ' UNIQUE' if col_config.get('unique', False) else ''
                    
                    migration_sql = f"ALTER TABLE stok_barang ADD COLUMN {col_name} {col_config['type']}{nullable_clause}{default_clause}{unique_clause}"
                    migrations.append({
                        'sql': migration_sql,
                        'col_name': col_name,
                        'has_fk': 'foreign_key' in col_config,
                        'needs_post_update': col_name == 'barang_id' and col_config.get('unique', False)
                    })
                    print(f"➕ Will add {col_name} column")
            
            if not migrations:
                print("✅ All columns already exist, checking data migration...")
            else:
                # Execute column migrations
                for migration in migrations:
                    try:
                        print(f"🔄 Executing: {migration['sql']}")
                        db.session.execute(db.text(migration['sql']))
                        db.session.commit()
                        print(f"✅ Success: {migration['col_name']}")
                        
                        # Post-update untuk barang_id: set default values, lalu set NOT NULL dan UNIQUE
                        if migration.get('needs_post_update'):
                            try:
                                # Set default value untuk rows yang NULL (gunakan id sebagai default sementara)
                                db.session.execute(db.text("""
                                    UPDATE stok_barang 
                                    SET barang_id = id 
                                    WHERE barang_id IS NULL
                                """))
                                db.session.commit()
                                print(f"✅ Populated {migration['col_name']} with default values")
                                
                                # Set NOT NULL
                                db.session.execute(db.text(f"""
                                    ALTER TABLE stok_barang 
                                    MODIFY COLUMN {migration['col_name']} INT NOT NULL
                                """))
                                db.session.commit()
                                print(f"✅ Set {migration['col_name']} to NOT NULL")
                                
                                # Add UNIQUE constraint
                                db.session.execute(db.text(f"""
                                    ALTER TABLE stok_barang 
                                    ADD UNIQUE INDEX idx_stok_barang_{migration['col_name']} ({migration['col_name']})
                                """))
                                db.session.commit()
                                print(f"✅ Added UNIQUE constraint to {migration['col_name']}")
                            except Exception as e:
                                print(f"⚠️  Warning post-updating {migration['col_name']}: {e}")
                                db.session.rollback()
                        
                        # Add foreign key if needed
                        if migration['has_fk']:
                            try:
                                fk_name = f"fk_stok_barang_{migration['col_name']}"
                                # Check if foreign key already exists
                                fk_exists = db.session.execute(db.text(f"""
                                    SELECT COUNT(*) 
                                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                                    WHERE TABLE_SCHEMA = 'KSM_main' 
                                    AND TABLE_NAME = 'stok_barang' 
                                    AND CONSTRAINT_NAME = '{fk_name}'
                                """)).scalar()
                                
                                if fk_exists == 0:
                                    fk_sql = f"ALTER TABLE stok_barang ADD CONSTRAINT {fk_name} FOREIGN KEY ({migration['col_name']}) REFERENCES barang(id)"
                                    db.session.execute(db.text(fk_sql))
                                    db.session.commit()
                                    print(f"✅ Foreign key created: {fk_name}")
                                else:
                                    print(f"ℹ️  Foreign key already exists: {fk_name}")
                            except Exception as e:
                                print(f"⚠️  Warning creating foreign key: {e}")
                                db.session.rollback()
                    except Exception as e:
                        print(f"❌ Error executing {migration['sql']}: {e}")
                        db.session.rollback()
                        # Continue with other migrations
                        continue
            
            # Check current columns after migration
            result_after = db.session.execute(db.text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'KSM_main' 
                AND TABLE_NAME = 'stok_barang'
            """)).fetchall()
            
            current_columns = [row[0] for row in result_after]
            
            # Migrate data from old structure to new structure if needed
            # Check if old columns exist (nama_barang, jumlah) and new columns exist (barang_id, jumlah_stok)
            if 'nama_barang' in current_columns and 'jumlah' in current_columns:
                if 'barang_id' in current_columns and 'jumlah_stok' in current_columns:
                    try:
                        # Check if there's data in old format
                        old_data_count = db.session.execute(db.text("""
                            SELECT COUNT(*) FROM stok_barang 
                            WHERE nama_barang IS NOT NULL AND barang_id IS NULL
                        """)).scalar()
                        
                        if old_data_count > 0:
                            print(f"⚠️  Found {old_data_count} rows with old structure")
                            print("⚠️  Manual data migration may be required")
                            print("⚠️  Old structure: nama_barang, jumlah")
                            print("⚠️  New structure: barang_id, jumlah_stok")
                            print("⚠️  Please migrate data manually or create barang records first")
                    except Exception as e:
                        print(f"⚠️  Warning checking old data: {e}")
            
            # Populate jumlah_stok from jumlah if both exist
            if 'jumlah' in current_columns and 'jumlah_stok' in current_columns:
                try:
                    update_result = db.session.execute(db.text("""
                        UPDATE stok_barang 
                        SET jumlah_stok = jumlah 
                        WHERE jumlah_stok IS NULL OR jumlah_stok = 0 AND jumlah IS NOT NULL
                    """))
                    rows_updated = update_result.rowcount
                    if rows_updated > 0:
                        db.session.commit()
                        print(f"✅ Updated {rows_updated} rows: populated jumlah_stok from jumlah")
                except Exception as e:
                    print(f"⚠️  Warning populating jumlah_stok: {e}")
                    db.session.rollback()
            
            print("🎉 Stok Barang migration completed successfully!")
            
            # Show final table structure
            result = db.session.execute(db.text("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'KSM_main' 
                AND TABLE_NAME = 'stok_barang'
                ORDER BY ORDINAL_POSITION
            """)).fetchall()
            
            print("\n📋 Final table structure:")
            for row in result:
                print(f"  - {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error in migration: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return 1

def main():
    """Main function"""
    exit_code = migrate_stok_barang()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

