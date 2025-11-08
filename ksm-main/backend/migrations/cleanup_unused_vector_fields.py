#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script untuk membersihkan field vector database yang tidak digunakan
Menghapus: faiss_vector_id, chromadb_vector_id, chromadb_collection
Menyimpan: qdrant_vector_id, qdrant_collection (yang aktif digunakan)

Best Practice Migration:
1. Backup database sebelum migration
2. Test di staging environment
3. Rollback plan tersedia
"""

import os
import sys
from sqlalchemy import text
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db, engine

def backup_data():
    """Backup data yang akan dihapus untuk rollback"""
    try:
        with engine.connect() as conn:
            # Backup data yang akan dihapus
            backup_data = conn.execute(text("""
                SELECT id, chunk_id, faiss_vector_id, chromadb_vector_id, chromadb_collection
                FROM rag_chunk_embeddings 
                WHERE faiss_vector_id IS NOT NULL 
                   OR chromadb_vector_id IS NOT NULL 
                   OR chromadb_collection IS NOT NULL
            """)).fetchall()
            
            # Simpan backup ke file
            backup_file = f"backup_vector_fields_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            with open(backup_file, 'w') as f:
                f.write("-- Backup data sebelum cleanup vector fields\n")
                f.write("-- Generated: " + datetime.now().isoformat() + "\n\n")
                
                for row in backup_data:
                    f.write(f"-- ID: {row[0]}, Chunk: {row[1]}\n")
                    f.write(f"UPDATE rag_chunk_embeddings SET ")
                    updates = []
                    if row[2]:  # faiss_vector_id
                        updates.append(f"faiss_vector_id = '{row[2]}'")
                    if row[3]:  # chromadb_vector_id
                        updates.append(f"chromadb_vector_id = '{row[3]}'")
                    if row[4]:  # chromadb_collection
                        updates.append(f"chromadb_collection = '{row[4]}'")
                    f.write(", ".join(updates))
                    f.write(f" WHERE id = {row[0]};\n\n")
            
            print(f"✅ Backup data tersimpan di: {backup_file}")
            return backup_file
            
    except Exception as e:
        print(f"❌ Backup gagal: {e}")
        raise

def check_data_integrity():
    """Cek integritas data sebelum migration"""
    try:
        with engine.connect() as conn:
            # Cek total records
            total_records = conn.execute(text("""
                SELECT COUNT(*) FROM rag_chunk_embeddings
            """)).fetchone()[0]
            
            # Cek records dengan qdrant data
            qdrant_records = conn.execute(text("""
                SELECT COUNT(*) FROM rag_chunk_embeddings 
                WHERE qdrant_vector_id IS NOT NULL
            """)).fetchone()[0]
            
            # Cek records yang akan terpengaruh
            affected_records = conn.execute(text("""
                SELECT COUNT(*) FROM rag_chunk_embeddings 
                WHERE faiss_vector_id IS NOT NULL 
                   OR chromadb_vector_id IS NOT NULL 
                   OR chromadb_collection IS NOT NULL
            """)).fetchone()[0]
            
            print(f"📊 Data Integrity Check:")
            print(f"   Total records: {total_records}")
            print(f"   Records dengan Qdrant data: {qdrant_records}")
            print(f"   Records yang akan terpengaruh: {affected_records}")
            
            if qdrant_records == 0:
                print("⚠️  WARNING: Tidak ada data Qdrant yang ditemukan!")
                return False
                
            return True
            
    except Exception as e:
        print(f"❌ Data integrity check gagal: {e}")
        return False

def upgrade():
    """Remove unused vector database fields"""
    try:
        print("🚀 Starting database cleanup migration...")
        
        # Step 1: Backup data
        backup_file = backup_data()
        
        # Step 2: Check data integrity
        if not check_data_integrity():
            print("❌ Data integrity check failed. Aborting migration.")
            return False
        
        # Step 3: Remove unused columns
        with engine.connect() as conn:
            # Remove chromadb_vector_id column
            try:
                conn.execute(text("""
                    ALTER TABLE rag_chunk_embeddings 
                    DROP COLUMN IF EXISTS chromadb_vector_id
                """))
                print("✅ Removed chromadb_vector_id column")
            except Exception as e:
                print(f"ℹ️ chromadb_vector_id column removal: {e}")
            
            # Remove chromadb_collection column
            try:
                conn.execute(text("""
                    ALTER TABLE rag_chunk_embeddings 
                    DROP COLUMN IF EXISTS chromadb_collection
                """))
                print("✅ Removed chromadb_collection column")
            except Exception as e:
                print(f"ℹ️ chromadb_collection column removal: {e}")
            
            # Remove faiss_vector_id column (legacy, not used)
            try:
                conn.execute(text("""
                    ALTER TABLE rag_chunk_embeddings 
                    DROP COLUMN IF EXISTS faiss_vector_id
                """))
                print("✅ Removed faiss_vector_id column")
            except Exception as e:
                print(f"ℹ️ faiss_vector_id column removal: {e}")
            
            conn.commit()
            print("🎉 Database cleanup migration completed successfully!")
            print(f"📁 Backup file: {backup_file}")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

def downgrade():
    """Restore removed columns (rollback)"""
    try:
        print("🔄 Starting rollback migration...")
        
        with engine.connect() as conn:
            # Restore faiss_vector_id column
            conn.execute(text("""
                ALTER TABLE rag_chunk_embeddings 
                ADD COLUMN faiss_vector_id INT NULL
            """))
            print("✅ Restored faiss_vector_id column")
            
            # Restore chromadb_vector_id column
            conn.execute(text("""
                ALTER TABLE rag_chunk_embeddings 
                ADD COLUMN chromadb_vector_id VARCHAR(100) NULL
            """))
            print("✅ Restored chromadb_vector_id column")
            
            # Restore chromadb_collection column
            conn.execute(text("""
                ALTER TABLE rag_chunk_embeddings 
                ADD COLUMN chromadb_collection VARCHAR(100) NULL
            """))
            print("✅ Restored chromadb_collection column")
            
            conn.commit()
            print("🎉 Rollback migration completed successfully!")
            print("ℹ️  Note: Data values need to be restored manually from backup file")
            
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Cleanup unused vector database fields')
    parser.add_argument('action', choices=['upgrade', 'downgrade', 'check'], 
                       help='Migration action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'upgrade':
        upgrade()
    elif args.action == 'downgrade':
        downgrade()
    elif args.action == 'check':
        check_data_integrity()
