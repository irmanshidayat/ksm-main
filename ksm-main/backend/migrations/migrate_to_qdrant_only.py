#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration Script: Migrate to Qdrant-only Vector Store
Menghapus field FAISS dan ChromaDB, hanya menggunakan Qdrant
"""

import os
import sys
import pymysql
from datetime import datetime

def migrate_to_qdrant_only():
    """Migrate database to use only Qdrant vector store"""
    
    print("🚀 Starting migration to Qdrant-only vector store...")
    print(f"⏰ Migration started at: {datetime.now()}")
    
    try:
        # Connect to database
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='KSM_main',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            print("\n📊 Checking current table structure...")
            
            # Check current structure
            cursor.execute("DESCRIBE rag_chunk_embeddings")
            columns = cursor.fetchall()
            print("Current columns:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
            
            # Check if qdrant fields already exist
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'KSM_main' 
                AND TABLE_NAME = 'rag_chunk_embeddings' 
                AND COLUMN_NAME IN ('qdrant_vector_id', 'qdrant_collection')
            """)
            existing_qdrant_fields = [row[0] for row in cursor.fetchall()]
            
            # Check if old fields exist
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'KSM_main' 
                AND TABLE_NAME = 'rag_chunk_embeddings' 
                AND COLUMN_NAME IN ('faiss_vector_id', 'chromadb_vector_id', 'chromadb_collection')
            """)
            existing_old_fields = [row[0] for row in cursor.fetchall()]
            
            print(f"\nExisting Qdrant fields: {existing_qdrant_fields}")
            print(f"Existing old fields: {existing_old_fields}")
            
            # Step 1: Add Qdrant fields if they don't exist
            if 'qdrant_vector_id' not in existing_qdrant_fields:
                print("\n➕ Adding qdrant_vector_id column...")
                cursor.execute("""
                    ALTER TABLE rag_chunk_embeddings 
                    ADD COLUMN qdrant_vector_id VARCHAR(100) NULL
                """)
                print("✅ Added qdrant_vector_id column")
            else:
                print("ℹ️ qdrant_vector_id column already exists")
            
            if 'qdrant_collection' not in existing_qdrant_fields:
                print("\n➕ Adding qdrant_collection column...")
                cursor.execute("""
                    ALTER TABLE rag_chunk_embeddings 
                    ADD COLUMN qdrant_collection VARCHAR(100) NULL
                """)
                print("✅ Added qdrant_collection column")
            else:
                print("ℹ️ qdrant_collection column already exists")
            
            # Step 2: Migrate data from old fields to new fields (if any data exists)
            print("\n🔄 Migrating data from old fields to Qdrant fields...")
            
            # Check if there's any data in old fields
            cursor.execute("""
                SELECT COUNT(*) FROM rag_chunk_embeddings 
                WHERE faiss_vector_id IS NOT NULL 
                   OR chromadb_vector_id IS NOT NULL 
                   OR chromadb_collection IS NOT NULL
            """)
            old_data_count = cursor.fetchone()[0]
            
            if old_data_count > 0:
                print(f"📦 Found {old_data_count} records with old field data")
                
                # Migrate chromadb data to qdrant (if exists)
                if 'chromadb_vector_id' in existing_old_fields:
                    cursor.execute("""
                        UPDATE rag_chunk_embeddings 
                        SET qdrant_vector_id = chromadb_vector_id 
                        WHERE chromadb_vector_id IS NOT NULL 
                        AND qdrant_vector_id IS NULL
                    """)
                    migrated_chromadb = cursor.rowcount
                    print(f"✅ Migrated {migrated_chromadb} chromadb_vector_id to qdrant_vector_id")
                
                if 'chromadb_collection' in existing_old_fields:
                    cursor.execute("""
                        UPDATE rag_chunk_embeddings 
                        SET qdrant_collection = chromadb_collection 
                        WHERE chromadb_collection IS NOT NULL 
                        AND qdrant_collection IS NULL
                    """)
                    migrated_collection = cursor.rowcount
                    print(f"✅ Migrated {migrated_collection} chromadb_collection to qdrant_collection")
            else:
                print("ℹ️ No data found in old fields to migrate")
            
            # Step 3: Remove old fields
            print("\n🗑️ Removing old vector store fields...")
            
            if 'chromadb_collection' in existing_old_fields:
                cursor.execute("""
                    ALTER TABLE rag_chunk_embeddings 
                    DROP COLUMN chromadb_collection
                """)
                print("✅ Removed chromadb_collection column")
            
            if 'chromadb_vector_id' in existing_old_fields:
                cursor.execute("""
                    ALTER TABLE rag_chunk_embeddings 
                    DROP COLUMN chromadb_vector_id
                """)
                print("✅ Removed chromadb_vector_id column")
            
            if 'faiss_vector_id' in existing_old_fields:
                cursor.execute("""
                    ALTER TABLE rag_chunk_embeddings 
                    DROP COLUMN faiss_vector_id
                """)
                print("✅ Removed faiss_vector_id column")
            
            # Commit changes
            connection.commit()
            
            # Step 4: Verify final structure
            print("\n🔍 Verifying final table structure...")
            cursor.execute("DESCRIBE rag_chunk_embeddings")
            final_columns = cursor.fetchall()
            print("Final columns:")
            for col in final_columns:
                print(f"  - {col[0]} ({col[1]})")
            
            # Check data integrity
            cursor.execute("SELECT COUNT(*) FROM rag_chunk_embeddings")
            total_records = cursor.fetchone()[0]
            print(f"\n📊 Total records in rag_chunk_embeddings: {total_records}")
            
            cursor.execute("""
                SELECT COUNT(*) FROM rag_chunk_embeddings 
                WHERE qdrant_vector_id IS NOT NULL
            """)
            qdrant_records = cursor.fetchone()[0]
            print(f"📊 Records with qdrant_vector_id: {qdrant_records}")
            
        connection.close()
        
        print(f"\n🎉 Migration completed successfully at: {datetime.now()}")
        print("✅ Database now uses only Qdrant vector store fields")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def rollback_migration():
    """Rollback migration (restore old fields)"""
    
    print("🔄 Rolling back migration...")
    
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='KSM_main',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Restore old fields
            print("➕ Restoring old fields...")
            
            # Restore faiss_vector_id
            cursor.execute("""
                ALTER TABLE rag_chunk_embeddings 
                ADD COLUMN faiss_vector_id INT NULL
            """)
            print("✅ Restored faiss_vector_id column")
            
            # Restore chromadb_vector_id
            cursor.execute("""
                ALTER TABLE rag_chunk_embeddings 
                ADD COLUMN chromadb_vector_id VARCHAR(100) NULL
            """)
            print("✅ Restored chromadb_vector_id column")
            
            # Restore chromadb_collection
            cursor.execute("""
                ALTER TABLE rag_chunk_embeddings 
                ADD COLUMN chromadb_collection VARCHAR(100) NULL
            """)
            print("✅ Restored chromadb_collection column")
            
            connection.commit()
        
        connection.close()
        print("✅ Rollback completed successfully")
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        success = rollback_migration()
    else:
        success = migrate_to_qdrant_only()
    
    sys.exit(0 if success else 1)
