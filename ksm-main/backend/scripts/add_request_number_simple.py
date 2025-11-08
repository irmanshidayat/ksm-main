#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple script to add request_number column to request_pembelian table
"""

import pymysql
import os

# Database connection
db_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '',  # XAMPP default
    'database': 'KSM_main',
    'charset': 'utf8mb4'
}

try:
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    print("[OK] Connected to database")
    
    # Check if column exists
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'KSM_main' 
        AND TABLE_NAME = 'request_pembelian' 
        AND COLUMN_NAME = 'request_number'
    """)
    col_exists = cursor.fetchone()[0] > 0
    
    if col_exists:
        print("[INFO] Column request_number already exists")
    else:
        print("[RUN] Adding request_number column...")
        # Add column
        cursor.execute("""
            ALTER TABLE request_pembelian 
            ADD COLUMN request_number VARCHAR(50) NULL
        """)
        conn.commit()
        print("[OK] Column added")
        
        # Create index
        try:
            cursor.execute("""
                CREATE INDEX idx_request_number ON request_pembelian(request_number)
            """)
            conn.commit()
            print("[OK] Index created")
        except Exception as e:
            print(f"[WARN] Index creation warning: {e}")
            conn.rollback()
    
    # Populate request_number from reference_id if NULL
    cursor.execute("""
        UPDATE request_pembelian
        SET request_number = reference_id
        WHERE request_number IS NULL AND reference_id IS NOT NULL
    """)
    updated = cursor.rowcount
    conn.commit()
    if updated > 0:
        print(f"[OK] Populated {updated} records from reference_id")
    
    # Generate request_number for remaining NULL values
    cursor.execute("""
        UPDATE request_pembelian
        SET request_number = CONCAT('PR-', DATE_FORMAT(COALESCE(created_at, NOW()), '%Y%m%d'), '-', LPAD(id, 4, '0'))
        WHERE request_number IS NULL
    """)
    generated = cursor.rowcount
    conn.commit()
    if generated > 0:
        print(f"[OK] Generated request_number for {generated} records")
    
    # Check if we can set NOT NULL
    cursor.execute("SELECT COUNT(*) FROM request_pembelian WHERE request_number IS NULL")
    null_count = cursor.fetchone()[0]
    
    if null_count == 0:
        try:
            cursor.execute("""
                ALTER TABLE request_pembelian 
                MODIFY COLUMN request_number VARCHAR(50) NOT NULL
            """)
            conn.commit()
            print("[OK] Set request_number to NOT NULL")
        except Exception as e:
            print(f"[WARN] Could not set NOT NULL: {e}")
            conn.rollback()
    else:
        print(f"[WARN] Cannot set NOT NULL: {null_count} NULL values remain")
    
    print("\n[OK] Migration completed successfully!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"[ERROR] Error: {e}")
    if 'conn' in locals():
        conn.rollback()
        conn.close()
    exit(1)

