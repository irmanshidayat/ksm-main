#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk migrate tabel rag_documents
Menambahkan semua kolom yang diperlukan sesuai model RagDocument
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
    
    # Database configuration
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME', 'KSM_main')
    charset = 'utf8mb4'
    
    mysql_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset={charset}"
    app.config['SQLALCHEMY_DATABASE_URI'] = mysql_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def migrate_rag_documents():
    """Migrate tabel rag_documents - menambahkan semua kolom yang diperlukan"""
    print("🚀 Starting RAG documents migration...")
    
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
                AND TABLE_NAME = 'rag_documents'
            """)).fetchall()
            
            existing_columns = [row[0] for row in result]
            print(f"📊 Existing columns: {existing_columns}")
            
            # Define all required columns based on RagDocument model
            required_columns = {
                'company_id': {
                    'type': 'VARCHAR(100)',
                    'nullable': True,  # Will be set to NOT NULL after populating
                    'index': True,
                    'default_value': None  # Will be populated from companies table
                },
                'app_id': {
                    'type': 'VARCHAR(100)',
                    'nullable': True,
                    'index': True
                },
                'collection': {
                    'type': 'VARCHAR(100)',
                    'nullable': True,
                    'index': True
                },
                'sha256': {
                    'type': 'VARCHAR(64)',
                    'nullable': True,  # Will be set to NOT NULL after populating
                    'default_value': ''  # Temporary default
                },
                'original_name': {
                    'type': 'VARCHAR(255)',
                    'nullable': True,  # Will be set to NOT NULL after populating
                    'default_value': None  # Will be populated from filename
                },
                'title': {
                    'type': 'VARCHAR(255)',
                    'nullable': True
                },
                'description': {
                    'type': 'TEXT',
                    'nullable': True
                },
                'mime': {
                    'type': 'VARCHAR(100)',
                    'nullable': True,
                    'default_value': 'application/pdf'
                },
                'size_bytes': {
                    'type': 'BIGINT',
                    'nullable': True,
                    'default_value': None  # Will be populated from file_size
                },
                'total_pages': {
                    'type': 'INT',
                    'nullable': True
                },
                'language': {
                    'type': 'VARCHAR(20)',
                    'nullable': True
                },
                'status': {
                    'type': 'VARCHAR(20)',
                    'nullable': True,
                    'default_value': 'uploaded'
                },
                'storage_path': {
                    'type': 'VARCHAR(500)',
                    'nullable': True,  # Will be set to NOT NULL after populating
                    'default_value': None  # Will be populated from file_path
                },
                'base64_content': {
                    'type': 'LONGTEXT',
                    'nullable': True
                },
                'qdrant_collection': {
                    'type': 'VARCHAR(100)',
                    'nullable': True
                },
                'vector_count': {
                    'type': 'INT',
                    'nullable': True,
                    'default_value': 0
                },
                'created_by': {
                    'type': 'INT',
                    'nullable': True
                }
            }
            
            # Add missing columns
            migrations = []
            indexes_to_create = []
            
            for col_name, col_config in required_columns.items():
                if col_name not in existing_columns:
                    nullable_clause = '' if col_config.get('nullable', True) else ' NOT NULL'
                    default_clause = ''
                    if col_config.get('default_value') is not None:
                        if isinstance(col_config['default_value'], str):
                            default_clause = f" DEFAULT '{col_config['default_value']}'"
                        else:
                            default_clause = f" DEFAULT {col_config['default_value']}"
                    
                    migration_sql = f"ALTER TABLE rag_documents ADD COLUMN {col_name} {col_config['type']}{nullable_clause}{default_clause}"
                    migrations.append(migration_sql)
                    print(f"➕ Will add {col_name} column")
                    
                    # Add index if needed
                    if col_config.get('index', False):
                        indexes_to_create.append(f"CREATE INDEX idx_rag_documents_{col_name} ON rag_documents({col_name})")
            
            if not migrations:
                print("✅ All columns already exist, checking indexes...")
            else:
                # Execute column migrations
                for migration in migrations:
                    try:
                        print(f"🔄 Executing: {migration}")
                        db.session.execute(db.text(migration))
                        db.session.commit()
                        print(f"✅ Success: {migration}")
                    except Exception as e:
                        print(f"❌ Error executing {migration}: {e}")
                        db.session.rollback()
                        return 1
            
            # Create indexes
            for index_sql in indexes_to_create:
                try:
                    # Check if index already exists
                    index_name = index_sql.split('idx_rag_documents_')[1].split(' ')[0]
                    check_index = db.session.execute(db.text(f"""
                        SELECT COUNT(*) 
                        FROM INFORMATION_SCHEMA.STATISTICS 
                        WHERE TABLE_SCHEMA = 'KSM_main' 
                        AND TABLE_NAME = 'rag_documents' 
                        AND INDEX_NAME = 'idx_rag_documents_{index_name}'
                    """)).scalar()
                    
                    if check_index == 0:
                        print(f"🔄 Creating index: idx_rag_documents_{index_name}")
                        db.session.execute(db.text(index_sql))
                        db.session.commit()
                        print(f"✅ Index created: idx_rag_documents_{index_name}")
                    else:
                        print(f"ℹ️  Index already exists: idx_rag_documents_{index_name}")
                except Exception as e:
                    print(f"⚠️  Warning creating index: {e}")
                    db.session.rollback()
            
            # Check current columns after migration
            result_after = db.session.execute(db.text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'KSM_main' 
                AND TABLE_NAME = 'rag_documents'
            """)).fetchall()
            
            current_columns = [row[0] for row in result_after]
            
            # Populate company_id for existing rows
            if 'company_id' in current_columns:
                try:
                    # Get first company name from companies table
                    company_result = db.session.execute(db.text("""
                        SELECT name FROM companies 
                        WHERE is_active = 1 
                        ORDER BY id ASC 
                        LIMIT 1
                    """)).fetchone()
                    
                    default_company = 'PT. Kian Santang Muliatama'  # Default fallback
                    if company_result:
                        default_company = company_result[0]
                    
                    # Update existing rows with NULL company_id
                    update_result = db.session.execute(db.text("""
                        UPDATE rag_documents 
                        SET company_id = :company_id 
                        WHERE company_id IS NULL
                    """), {'company_id': default_company})
                    
                    rows_updated = update_result.rowcount
                    if rows_updated > 0:
                        db.session.commit()
                        print(f"✅ Updated {rows_updated} rows with company_id: {default_company}")
                    
                    # Now make company_id NOT NULL
                    try:
                        db.session.execute(db.text("""
                            ALTER TABLE rag_documents 
                            MODIFY COLUMN company_id VARCHAR(100) NOT NULL
                        """))
                        db.session.commit()
                        print("✅ Set company_id to NOT NULL")
                    except Exception as e:
                        print(f"⚠️  Warning setting company_id to NOT NULL: {e}")
                        db.session.rollback()
                except Exception as e:
                    print(f"⚠️  Warning populating company_id: {e}")
                    db.session.rollback()
            
            # Populate other fields from old columns if they exist
            try:
                # Map old columns to new columns
                if 'filename' in current_columns and 'original_name' in current_columns:
                    db.session.execute(db.text("""
                        UPDATE rag_documents 
                        SET original_name = filename 
                        WHERE original_name IS NULL AND filename IS NOT NULL
                    """))
                    db.session.commit()
                    print("✅ Populated original_name from filename")
                
                if 'file_path' in current_columns and 'storage_path' in current_columns:
                    db.session.execute(db.text("""
                        UPDATE rag_documents 
                        SET storage_path = file_path 
                        WHERE storage_path IS NULL AND file_path IS NOT NULL
                    """))
                    db.session.commit()
                    print("✅ Populated storage_path from file_path")
                
                if 'file_size' in current_columns and 'size_bytes' in current_columns:
                    db.session.execute(db.text("""
                        UPDATE rag_documents 
                        SET size_bytes = file_size 
                        WHERE size_bytes IS NULL AND file_size IS NOT NULL
                    """))
                    db.session.commit()
                    print("✅ Populated size_bytes from file_size")
                
                # Generate sha256 if missing (use a placeholder for now)
                if 'sha256' in current_columns:
                    db.session.execute(db.text("""
                        UPDATE rag_documents 
                        SET sha256 = CONCAT('temp_', id) 
                        WHERE sha256 IS NULL OR sha256 = ''
                    """))
                    db.session.commit()
                    print("✅ Populated sha256 with temporary values")
                
                # Set NOT NULL constraints for required fields
                not_null_updates = [
                    ("sha256", "VARCHAR(64)"),
                    ("original_name", "VARCHAR(255)"),
                    ("storage_path", "VARCHAR(500)")
                ]
                
                for col_name, col_type in not_null_updates:
                    if col_name in current_columns:
                        try:
                            db.session.execute(db.text(f"""
                                ALTER TABLE rag_documents 
                                MODIFY COLUMN {col_name} {col_type} NOT NULL
                            """))
                            db.session.commit()
                            print(f"✅ Set {col_name} to NOT NULL")
                        except Exception as e:
                            print(f"⚠️  Warning setting {col_name} to NOT NULL: {e}")
                            db.session.rollback()
                        
            except Exception as e:
                print(f"⚠️  Warning populating data: {e}")
                db.session.rollback()
            
            print("🎉 RAG documents migration completed successfully!")
            
            # Show final table structure
            result = db.session.execute(db.text("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'KSM_main' 
                AND TABLE_NAME = 'rag_documents'
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
    exit_code = migrate_rag_documents()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
