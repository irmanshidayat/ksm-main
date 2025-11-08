#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Migrasi Tabel yang Gagal - dengan Handling Khusus
========================================================

Script ini menangani tabel-tabel yang gagal di-migrate karena:
1. Kolom required yang tidak ada di source
2. Perbedaan enum values
3. Constraint NOT NULL

Usage:
    python migrate_failed_tables.py
"""

import pymysql
import sys
from datetime import datetime
from pathlib import Path

# Import dari script utama
sys.path.insert(0, str(Path(__file__).parent))
from migrate_xampp_to_docker import (
    SOURCE_CONFIG, TARGET_CONFIG, connect_database,
    print_colored, print_header, print_success, print_error, 
    print_warning, print_info, Colors, get_table_columns,
    get_table_row_count, truncate_table, disable_foreign_key_checks,
    enable_foreign_key_checks
)


def migrate_rag_documents(source_conn, target_conn):
    """Migrasi rag_documents dengan mapping kolom"""
    print_info("Migrating rag_documents...")
    try:
        truncate_table(target_conn, 'rag_documents')
        
        # Get kolom yang ada di target
        target_columns = get_table_columns(target_conn, 'rag_documents')
        source_columns = get_table_columns(source_conn, 'rag_documents')
        
        # Mapping kolom dari source ke target
        column_mapping = {}
        if 'original_name' in source_columns and 'filename' in target_columns:
            column_mapping['filename'] = 'original_name'
        if 'storage_path' in source_columns and 'file_path' in target_columns:
            column_mapping['file_path'] = 'storage_path'
        if 'mime' in source_columns and 'file_type' in target_columns:
            column_mapping['file_type'] = 'mime'
        if 'size_bytes' in source_columns and 'file_size' in target_columns:
            column_mapping['file_size'] = 'size_bytes'
        if 'base64_content' in source_columns and 'content' in target_columns:
            column_mapping['content'] = 'base64_content'
        
        # Get common columns
        common_cols = [col for col in target_columns if col in source_columns or col in column_mapping]
        
        # Build SELECT query
        select_cols = []
        for col in common_cols:
            if col in column_mapping:
                select_cols.append(f"`{column_mapping[col]}` as `{col}`")
            else:
                select_cols.append(f"`{col}`")
        
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT {', '.join(select_cols)} FROM `rag_documents`")
            rows = cursor.fetchall()
        
        if not rows:
            print_info("  Tabel rag_documents: Kosong")
            return True, 0
        
        # Insert dengan default untuk kolom yang tidak ada
        inserted = 0
        with target_conn.cursor() as cursor:
            for row in rows:
                values = []
                placeholders = []
                
                for col in target_columns:
                    if col in row:
                        values.append(row[col])
                        placeholders.append('%s')
                    elif col == 'filename' and 'original_name' in source_columns:
                        # Use original_name as filename
                        values.append(row.get('original_name', 'unknown'))
                        placeholders.append('%s')
                    elif col == 'file_path' and 'storage_path' in source_columns:
                        values.append(row.get('storage_path', ''))
                        placeholders.append('%s')
                    elif col == 'is_processed':
                        values.append(False)
                        placeholders.append('%s')
                    elif col in ['created_at', 'updated_at']:
                        values.append(datetime.now())
                        placeholders.append('%s')
                    else:
                        values.append(None)
                        placeholders.append('%s')
                
                insert_query = f"INSERT INTO `rag_documents` ({', '.join([f'`{col}`' for col in target_columns])}) VALUES ({', '.join(placeholders)})"
                cursor.execute(insert_query, values)
                inserted += 1
            
            target_conn.commit()
        
        print_success(f"  rag_documents: {inserted} rows migrated")
        return True, inserted
    except Exception as e:
        print_error(f"  rag_documents: Error - {e}")
        target_conn.rollback()
        return False, 0


def migrate_users(source_conn, target_conn):
    """Migrasi users dengan handling kolom email dan role enum"""
    print_info("Migrating users...")
    try:
        truncate_table(target_conn, 'users')
        
        source_columns = get_table_columns(source_conn, 'users')
        target_columns = get_table_columns(target_conn, 'users')
        
        # Get valid role enum values dari target
        valid_roles = ['admin', 'user', 'vendor']  # Default values
        
        # Get data dari source
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM `users`")
            rows = cursor.fetchall()
        
        if not rows:
            print_info("  Tabel users: Kosong")
            return True, 0
        
        inserted = 0
        with target_conn.cursor() as cursor:
            for row in rows:
                values = []
                cols_to_insert = []
                
                for col in target_columns:
                    if col in row and row[col] is not None:
                        val = row[col]
                        # Handle role enum - map to valid values
                        if col == 'role':
                            val_lower = str(val).lower() if val else 'user'
                            if val_lower not in valid_roles:
                                val = 'user'  # Default to user
                            else:
                                val = val_lower
                        values.append(val)
                        cols_to_insert.append(col)
                    elif col == 'email' and 'username' in row:
                        # Use username as email if email not available
                        values.append(row.get('username', '') + '@ksm.local')
                        cols_to_insert.append(col)
                    elif col == 'full_name' and 'username' in row:
                        values.append(row.get('username', ''))
                        cols_to_insert.append(col)
                    elif col in ['created_at', 'updated_at']:
                        values.append(datetime.now())
                        cols_to_insert.append(col)
                
                if 'email' not in cols_to_insert:
                    continue  # Skip jika email tidak bisa dibuat
                
                placeholders = ', '.join(['%s'] * len(values))
                cols_str = ', '.join([f"`{col}`" for col in cols_to_insert])
                insert_query = f"INSERT INTO `users` ({cols_str}) VALUES ({placeholders})"
                
                try:
                    cursor.execute(insert_query, values)
                    inserted += 1
                except Exception as e:
                    print_warning(f"  Skip row karena error: {e}")
                    continue
            
            target_conn.commit()
        
        print_success(f"  users: {inserted} rows migrated")
        return True, inserted
    except Exception as e:
        print_error(f"  users: Error - {e}")
        target_conn.rollback()
        return False, 0


def migrate_request_pembelian(source_conn, target_conn):
    """Migrasi request_pembelian dengan mapping enum status"""
    print_info("Migrating request_pembelian...")
    try:
        truncate_table(target_conn, 'request_pembelian')
        
        # Get kolom yang common
        source_columns = get_table_columns(source_conn, 'request_pembelian')
        target_columns = get_table_columns(target_conn, 'request_pembelian')
        
        # Valid status values di target
        valid_statuses = ['draft', 'submitted', 'vendor_uploading', 'under_analysis', 
                         'approved', 'rejected', 'vendor_selected', 'completed']
        
        common_cols = [col for col in source_columns if col in target_columns]
        
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT {', '.join([f'`{col}`' for col in common_cols])} FROM `request_pembelian`")
            rows = cursor.fetchall()
        
        if not rows:
            print_info("  Tabel request_pembelian: Kosong")
            return True, 0
        
        inserted = 0
        with target_conn.cursor() as cursor:
            for row in rows:
                values = []
                cols_to_insert = []
                
                for col in target_columns:
                    if col in row:
                        val = row[col]
                        # Handle status enum - map invalid values to 'draft'
                        if col == 'status':
                            if not val or val == '':
                                val = 'draft'
                            else:
                                val_str = str(val).lower().strip()
                                # Debug: print nilai yang tidak valid
                                if val_str not in valid_statuses:
                                    print_warning(f"    Invalid status value: '{val}' (original: '{row[col]}'), mapping to 'draft'")
                                    val = 'draft'  # Default value
                                else:
                                    val = val_str
                        values.append(val)
                        cols_to_insert.append(col)
                    elif col in ['created_at', 'updated_at']:
                        values.append(datetime.now())
                        cols_to_insert.append(col)
                
                placeholders = ', '.join(['%s'] * len(values))
                cols_str = ', '.join([f"`{col}`" for col in cols_to_insert])
                insert_query = f"INSERT INTO `request_pembelian` ({cols_str}) VALUES ({placeholders})"
                
                try:
                    cursor.execute(insert_query, values)
                    inserted += 1
                except Exception as e:
                    print_warning(f"  Skip row karena error: {e}")
                    continue
            
            target_conn.commit()
        
        print_success(f"  request_pembelian: {inserted} rows migrated")
        return True, inserted
    except Exception as e:
        print_error(f"  request_pembelian: Error - {e}")
        target_conn.rollback()
        return False, 0


def migrate_vendors(source_conn, target_conn):
    """Migrasi vendors dengan mapping enum vendor_category"""
    print_info("Migrating vendors...")
    try:
        truncate_table(target_conn, 'vendors')
        
        source_columns = get_table_columns(source_conn, 'vendors')
        target_columns = get_table_columns(target_conn, 'vendors')
        
        # Valid vendor_category values
        valid_categories = ['general', 'specialized', 'preferred', 'supplier', 'contractor', 
                           'agent_tunggal', 'distributor', 'jasa', 'produk', 'custom']
        
        common_cols = [col for col in source_columns if col in target_columns]
        
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT {', '.join([f'`{col}`' for col in common_cols])} FROM `vendors`")
            rows = cursor.fetchall()
        
        if not rows:
            print_info("  Tabel vendors: Kosong")
            return True, 0
        
        inserted = 0
        with target_conn.cursor() as cursor:
            for row in rows:
                values = []
                cols_to_insert = []
                
                for col in target_columns:
                    if col in row:
                        val = row[col]
                        # Handle vendor_category enum - map to 'general' if invalid
                        if col == 'vendor_category':
                            if not val or val == '':
                                val = 'general'
                            else:
                                val_str = str(val).lower().strip()
                                if val_str not in valid_categories:
                                    val = 'general'  # Default value (required, tidak boleh NULL)
                                else:
                                    val = val_str
                        # Handle status enum untuk vendors
                        elif col == 'status':
                            if not val or val == '':
                                val = 'pending'
                            else:
                                val_str = str(val).lower().strip()
                                valid_vendor_statuses = ['pending', 'approved', 'rejected', 'suspended']
                                if val_str not in valid_vendor_statuses:
                                    val = 'pending'  # Default value
                                else:
                                    val = val_str
                        values.append(val)
                        cols_to_insert.append(col)
                    elif col in ['created_at', 'updated_at']:
                        values.append(datetime.now())
                        cols_to_insert.append(col)
                
                placeholders = ', '.join(['%s'] * len(values))
                cols_str = ', '.join([f"`{col}`" for col in cols_to_insert])
                insert_query = f"INSERT INTO `vendors` ({cols_str}) VALUES ({placeholders})"
                
                try:
                    cursor.execute(insert_query, values)
                    inserted += 1
                except Exception as e:
                    print_warning(f"  Skip row karena error: {e}")
                    continue
            
            target_conn.commit()
        
        print_success(f"  vendors: {inserted} rows migrated")
        return True, inserted
    except Exception as e:
        print_error(f"  vendors: Error - {e}")
        target_conn.rollback()
        return False, 0


def migrate_vendor_penawaran(source_conn, target_conn):
    """Migrasi vendor_penawaran dengan mapping enum status"""
    print_info("Migrating vendor_penawaran...")
    try:
        truncate_table(target_conn, 'vendor_penawaran')
        
        source_columns = get_table_columns(source_conn, 'vendor_penawaran')
        target_columns = get_table_columns(target_conn, 'vendor_penawaran')
        
        # Valid status values
        valid_statuses = ['submitted', 'under_review', 'selected', 'partially_selected', 'rejected']
        
        common_cols = [col for col in source_columns if col in target_columns]
        
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT {', '.join([f'`{col}`' for col in common_cols])} FROM `vendor_penawaran`")
            rows = cursor.fetchall()
        
        if not rows:
            print_info("  Tabel vendor_penawaran: Kosong")
            return True, 0
        
        inserted = 0
        with target_conn.cursor() as cursor:
            for row in rows:
                values = []
                cols_to_insert = []
                
                for col in target_columns:
                    if col in row:
                        val = row[col]
                        # Handle status enum - map invalid values to 'submitted'
                        if col == 'status':
                            if not val or val == '':
                                val = 'submitted'
                            else:
                                val_str = str(val).lower().strip()
                                if val_str not in valid_statuses:
                                    val = 'submitted'  # Default value
                                else:
                                    val = val_str
                        values.append(val)
                        cols_to_insert.append(col)
                    elif col in ['created_at', 'updated_at']:
                        values.append(datetime.now())
                        cols_to_insert.append(col)
                
                placeholders = ', '.join(['%s'] * len(values))
                cols_str = ', '.join([f"`{col}`" for col in cols_to_insert])
                insert_query = f"INSERT INTO `vendor_penawaran` ({cols_str}) VALUES ({placeholders})"
                
                try:
                    cursor.execute(insert_query, values)
                    inserted += 1
                except Exception as e:
                    print_warning(f"  Skip row karena error: {e}")
                    continue
            
            target_conn.commit()
        
        print_success(f"  vendor_penawaran: {inserted} rows migrated")
        return True, inserted
    except Exception as e:
        print_error(f"  vendor_penawaran: Error - {e}")
        target_conn.rollback()
        return False, 0


def migrate_vendor_notifications(source_conn, target_conn):
    """Migrasi vendor_notifications dengan handling request_id"""
    print_info("Migrating vendor_notifications...")
    try:
        truncate_table(target_conn, 'vendor_notifications')
        
        source_columns = get_table_columns(source_conn, 'vendor_notifications')
        target_columns = get_table_columns(target_conn, 'vendor_notifications')
        
        # Check if request_id exists in source
        has_request_id = 'request_id' in source_columns
        
        if not has_request_id:
            print_warning("  request_id tidak ada di source, akan skip tabel ini")
            return True, 0
        
        common_cols = [col for col in source_columns if col in target_columns]
        
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT {', '.join([f'`{col}`' for col in common_cols])} FROM `vendor_notifications` WHERE request_id IS NOT NULL")
            rows = cursor.fetchall()
        
        if not rows:
            print_info("  Tabel vendor_notifications: Tidak ada data dengan request_id")
            return True, 0
        
        inserted = 0
        with target_conn.cursor() as cursor:
            batch_size = 1000
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                values_list = []
                
                for row in batch:
                    values = [row[col] for col in common_cols]
                    values_list.append(values)
                
                placeholders = ', '.join(['%s'] * len(common_cols))
                cols_str = ', '.join([f"`{col}`" for col in common_cols])
                insert_query = f"INSERT INTO `vendor_notifications` ({cols_str}) VALUES ({placeholders})"
                
                cursor.executemany(insert_query, values_list)
                inserted += len(batch)
            
            target_conn.commit()
        
        print_success(f"  vendor_notifications: {inserted} rows migrated")
        return True, inserted
    except Exception as e:
        print_error(f"  vendor_notifications: Error - {e}")
        target_conn.rollback()
        return False, 0


def migrate_stok_barang(source_conn, target_conn):
    """Migrasi stok_barang dengan mapping kolom"""
    print_info("Migrating stok_barang...")
    try:
        truncate_table(target_conn, 'stok_barang')
        
        source_columns = get_table_columns(source_conn, 'stok_barang')
        target_columns = get_table_columns(target_conn, 'stok_barang')
        
        # Get data dari source dengan join ke tabel barang jika ada
        # Cek apakah ada relasi ke tabel barang
        has_barang_id = 'barang_id' in source_columns
        
        if has_barang_id:
            # Cek apakah tabel barang ada dan punya kolom yang diperlukan
            try:
                with source_conn.cursor() as test_cursor:
                    test_cursor.execute("SHOW TABLES LIKE 'barang'")
                    has_barang_table = test_cursor.fetchone() is not None
                    
                    if has_barang_table:
                        # Cek kolom di tabel barang
                        test_cursor.execute("DESCRIBE `barang`")
                        barang_columns = [row['Field'] for row in test_cursor.fetchall()]
                        has_nama = 'nama_barang' in barang_columns
                        has_kategori_id = 'kategori_id' in barang_columns
                        
                        if has_nama:
                            # Cek kolom yang ada di tabel barang
                            has_harga = 'harga_satuan' in barang_columns
                            has_supplier = 'supplier' in barang_columns
                            has_lokasi = 'lokasi' in barang_columns
                            has_satuan = 'satuan' in barang_columns
                            
                            # Tabel barang di target tidak punya supplier dan lokasi, gunakan default
                            harga_col = 'b.harga_per_unit' if 'harga_per_unit' in barang_columns else ('b.harga_satuan' if has_harga else '0')
                            supplier_col = "''"  # Tidak ada di tabel barang
                            lokasi_col = "''"  # Tidak ada di tabel barang
                            satuan_col = 'b.satuan' if has_satuan else "'pcs'"
                            
                            # Join dengan tabel barang
                            if has_kategori_id:
                                query = f"""
                                    SELECT 
                                        COALESCE(b.nama_barang, 'Unknown') as nama_barang,
                                        COALESCE(k.nama_kategori, 'Uncategorized') as kategori,
                                        COALESCE(sb.jumlah_stok, 0) as jumlah,
                                        COALESCE({satuan_col}, 'pcs') as satuan,
                                        COALESCE({harga_col}, 0) as harga_satuan,
                                        COALESCE({supplier_col}, '') as supplier,
                                        COALESCE({lokasi_col}, '') as lokasi,
                                        NOW() as created_at,
                                        NOW() as updated_at
                                    FROM stok_barang sb
                                    LEFT JOIN barang b ON sb.barang_id = b.id
                                    LEFT JOIN kategori_barang k ON b.kategori_id = k.id
                                """
                            else:
                                query = f"""
                                    SELECT 
                                        COALESCE(b.nama_barang, 'Unknown') as nama_barang,
                                        COALESCE(b.kategori, 'Uncategorized') as kategori,
                                        COALESCE(sb.jumlah_stok, 0) as jumlah,
                                        COALESCE({satuan_col}, 'pcs') as satuan,
                                        COALESCE({harga_col}, 0) as harga_satuan,
                                        COALESCE({supplier_col}, '') as supplier,
                                        COALESCE({lokasi_col}, '') as lokasi,
                                        NOW() as created_at,
                                        NOW() as updated_at
                                    FROM stok_barang sb
                                    LEFT JOIN barang b ON sb.barang_id = b.id
                                """
                        else:
                            # Fallback: gunakan kolom yang ada
                            common_cols = [col for col in source_columns if col in target_columns]
                            query = f"SELECT {', '.join([f'`{col}`' for col in common_cols])} FROM `stok_barang`"
                    else:
                        # Tabel barang tidak ada, gunakan kolom yang ada
                        common_cols = [col for col in source_columns if col in target_columns]
                        query = f"SELECT {', '.join([f'`{col}`' for col in common_cols])} FROM `stok_barang`"
            except Exception as e:
                print_warning(f"  Error checking barang table: {e}, using direct columns")
                common_cols = [col for col in source_columns if col in target_columns]
                query = f"SELECT {', '.join([f'`{col}`' for col in common_cols])} FROM `stok_barang`"
        else:
            # Jika tidak ada relasi, gunakan kolom yang ada
            common_cols = [col for col in source_columns if col in target_columns]
            query = f"SELECT {', '.join([f'`{col}`' for col in common_cols])} FROM `stok_barang`"
        
        with source_conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
        
        if not rows:
            print_info("  Tabel stok_barang: Kosong")
            return True, 0
        
        inserted = 0
        with target_conn.cursor() as cursor:
            for row in rows:
                values = []
                cols_to_insert = []
                
                for col in target_columns:
                    if col in row and row[col] is not None:
                        values.append(row[col])
                        cols_to_insert.append(col)
                    elif col == 'nama_barang':
                        # Use default if not available
                        values.append('Unknown')
                        cols_to_insert.append(col)
                    elif col in ['created_at', 'updated_at']:
                        values.append(datetime.now())
                        cols_to_insert.append(col)
                
                # Ensure required fields
                if 'nama_barang' not in cols_to_insert:
                    values.insert(0, 'Unknown')
                    cols_to_insert.insert(0, 'nama_barang')
                
                placeholders = ', '.join(['%s'] * len(values))
                cols_str = ', '.join([f"`{col}`" for col in cols_to_insert])
                insert_query = f"INSERT INTO `stok_barang` ({cols_str}) VALUES ({placeholders})"
                
                try:
                    cursor.execute(insert_query, values)
                    inserted += 1
                except Exception as e:
                    print_warning(f"  Skip row karena error: {e}")
                    continue
            
            target_conn.commit()
        
        print_success(f"  stok_barang: {inserted} rows migrated")
        return True, inserted
    except Exception as e:
        print_error(f"  stok_barang: Error - {e}")
        target_conn.rollback()
        return False, 0


def main():
    """Main function untuk retry migrasi tabel yang gagal"""
    print_header("Retry Migration untuk Tabel yang Gagal")
    
    # Connect to databases
    source_conn = connect_database(SOURCE_CONFIG)
    target_conn = connect_database(TARGET_CONFIG)
    
    if not source_conn or not target_conn:
        print_error("Gagal membuka koneksi database")
        sys.exit(1)
    
    try:
        disable_foreign_key_checks(target_conn)
        
        # List tabel yang akan di-retry
        failed_tables = [
            ('rag_documents', migrate_rag_documents),
            ('users', migrate_users),
            ('request_pembelian', migrate_request_pembelian),
            ('vendors', migrate_vendors),
            ('vendor_penawaran', migrate_vendor_penawaran),
            ('vendor_notifications', migrate_vendor_notifications),
            ('stok_barang', migrate_stok_barang),
        ]
        
        print_header("Migrating Failed Tables")
        total_migrated = 0
        success_count = 0
        
        for table_name, migrate_func in failed_tables:
            print_info(f"\n[{failed_tables.index((table_name, migrate_func)) + 1}/{len(failed_tables)}] Processing {table_name}...")
            success, count = migrate_func(source_conn, target_conn)
            if success:
                total_migrated += count
                success_count += 1
        
        enable_foreign_key_checks(target_conn)
        
        # Validation
        print_header("Validation")
        all_valid = True
        for table_name, _ in failed_tables:
            source_count = get_table_row_count(source_conn, table_name)
            target_count = get_table_row_count(target_conn, table_name)
            
            if source_count == target_count:
                print_success(f"  {table_name}: {source_count} rows ✓")
            else:
                print_warning(f"  {table_name}: Source={source_count}, Target={target_count}")
                all_valid = False
        
        # Summary
        print_header("Summary")
        print_success(f"Tables migrated: {success_count}/{len(failed_tables)}")
        print_success(f"Total rows migrated: {total_migrated}")
        
        if all_valid:
            print_success("\n✓ Semua tabel berhasil di-migrate!")
        else:
            print_warning("\n⚠ Beberapa tabel masih memiliki perbedaan row count")
        
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        target_conn.rollback()
    finally:
        source_conn.close()
        target_conn.close()
        print_info("\nKoneksi database ditutup.")


if __name__ == "__main__":
    main()

