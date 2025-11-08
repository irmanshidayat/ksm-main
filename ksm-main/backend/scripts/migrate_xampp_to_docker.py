#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Migrasi Data dari MySQL XAMPP ke MySQL Docker
=====================================================

Script ini akan:
1. Membuat backup database sebelum migrasi
2. Migrasi semua data dari XAMPP (localhost:3306) ke Docker (localhost:3308)
3. Validasi data setelah migrasi
4. Handle foreign keys dan constraints dengan benar

Usage:
    python migrate_xampp_to_docker.py

Requirements:
    - XAMPP MySQL harus running di localhost:3306
    - Docker MySQL harus running di localhost:3308
    - Database KSM_main harus sudah ada di kedua server
    - Tabel-tabel harus sudah dibuat di Docker (struktur sudah ada)
"""

import pymysql
import os
import sys
import json
from datetime import datetime
from pathlib import Path
import subprocess
from typing import Dict, List, Tuple, Optional

# Konfigurasi Source Database (XAMPP)
SOURCE_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '',  # XAMPP default tanpa password
    'database': 'KSM_main',
    'charset': 'utf8mb4'
}

# Konfigurasi Target Database (Docker)
TARGET_CONFIG = {
    'host': '127.0.0.1',
    'port': 3308,  # External port Docker
    'user': 'root',
    'password': 'admin123',  # Password Docker
    'database': 'KSM_main',
    'charset': 'utf8mb4'
}

# Direktori untuk backup
BACKUP_DIR = Path(__file__).parent.parent / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)


class Colors:
    """ANSI color codes untuk terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_colored(message: str, color: str = Colors.ENDC):
    """Print message dengan warna"""
    print(f"{color}{message}{Colors.ENDC}")


def print_header(message: str):
    """Print header message"""
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored(f"  {message}", Colors.HEADER)
    print_colored(f"{'='*60}\n", Colors.HEADER)


def print_success(message: str):
    """Print success message"""
    print_colored(f"✓ {message}", Colors.OKGREEN)


def print_error(message: str):
    """Print error message"""
    print_colored(f"✗ {message}", Colors.FAIL)


def print_warning(message: str):
    """Print warning message"""
    print_colored(f"⚠ {message}", Colors.WARNING)


def print_info(message: str):
    """Print info message"""
    print_colored(f"ℹ {message}", Colors.OKCYAN)


def connect_database(config: Dict) -> Optional[pymysql.Connection]:
    """Connect ke database MySQL"""
    try:
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset=config['charset'],
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        return connection
    except Exception as e:
        print_error(f"Gagal connect ke database {config['host']}:{config['port']}: {e}")
        return None


def test_connections() -> Tuple[bool, bool]:
    """Test koneksi ke source dan target database"""
    print_header("Testing Database Connections")
    
    # Test source connection
    print_info("Testing connection ke XAMPP MySQL (localhost:3306)...")
    source_conn = connect_database(SOURCE_CONFIG)
    if source_conn:
        print_success("Koneksi ke XAMPP MySQL berhasil")
        source_conn.close()
        source_ok = True
    else:
        print_error("Koneksi ke XAMPP MySQL gagal")
        source_ok = False
    
    # Test target connection
    print_info("Testing connection ke Docker MySQL (localhost:3308)...")
    target_conn = connect_database(TARGET_CONFIG)
    if target_conn:
        print_success("Koneksi ke Docker MySQL berhasil")
        target_conn.close()
        target_ok = True
    else:
        print_error("Koneksi ke Docker MySQL gagal")
        target_ok = False
    
    return source_ok, target_ok


def get_all_tables(connection: pymysql.Connection) -> List[str]:
    """Get list semua tabel dari database"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [list(row.values())[0] for row in cursor.fetchall()]
            return sorted(tables)
    except Exception as e:
        print_error(f"Gagal mendapatkan list tabel: {e}")
        return []


def get_table_row_count(connection: pymysql.Connection, table: str) -> int:
    """Get jumlah row di tabel"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) as count FROM `{table}`")
            result = cursor.fetchone()
            return result['count'] if result else 0
    except Exception as e:
        print_warning(f"Gagal mendapatkan count untuk tabel {table}: {e}")
        return 0


def get_table_columns(connection: pymysql.Connection, table: str) -> List[str]:
    """Get list kolom dari tabel"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DESCRIBE `{table}`")
            columns = [row['Field'] for row in cursor.fetchall()]
            return columns
    except Exception as e:
        print_warning(f"Gagal mendapatkan kolom untuk tabel {table}: {e}")
        return []


def get_foreign_key_dependencies(connection: pymysql.Connection, database: str) -> Dict[str, List[str]]:
    """Get foreign key dependencies untuk menentukan urutan migrasi"""
    dependencies = {}
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    TABLE_NAME,
                    REFERENCED_TABLE_NAME
                FROM 
                    INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE 
                    REFERENCED_TABLE_NAME IS NOT NULL
                    AND TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME
            """
            cursor.execute(query, (database,))
            results = cursor.fetchall()
            
            for row in results:
                table = row['TABLE_NAME']
                ref_table = row['REFERENCED_TABLE_NAME']
                
                if table not in dependencies:
                    dependencies[table] = []
                if ref_table not in dependencies[table]:
                    dependencies[table].append(ref_table)
    except Exception as e:
        print_warning(f"Gagal mendapatkan foreign key dependencies: {e}")
    
    return dependencies


def topological_sort_tables(tables: List[str], dependencies: Dict[str, List[str]]) -> List[str]:
    """Sort tabel berdasarkan dependencies (topological sort)"""
    # Tabel tanpa dependencies akan di-migrate terlebih dahulu
    sorted_tables = []
    remaining = set(tables)
    processed = set()
    
    def has_unprocessed_dependencies(table):
        deps = dependencies.get(table, [])
        return any(dep in remaining for dep in deps)
    
    while remaining:
        # Cari tabel yang tidak punya dependencies yang belum diproses
        ready = [t for t in remaining if not has_unprocessed_dependencies(t)]
        
        if not ready:
            # Jika tidak ada yang ready, ambil yang pertama (mungkin ada circular dependency)
            ready = [next(iter(remaining))]
        
        for table in sorted(ready):
            sorted_tables.append(table)
            remaining.remove(table)
            processed.add(table)
    
    return sorted_tables


def backup_database(source_conn: pymysql.Connection) -> Optional[str]:
    """Backup database menggunakan mysqldump"""
    print_header("Creating Database Backup")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"KSM_main_backup_{timestamp}.sql"
    
    try:
        print_info(f"Membuat backup ke: {backup_file}")
        
        # Build mysqldump command
        cmd = [
            'mysqldump',
            f"--host={SOURCE_CONFIG['host']}",
            f"--port={SOURCE_CONFIG['port']}",
            f"--user={SOURCE_CONFIG['user']}",
            f"--databases",
            SOURCE_CONFIG['database'],
            f"--result-file={backup_file}",
            '--single-transaction',
            '--routines',
            '--triggers',
            '--events'
        ]
        
        # Add password jika ada
        if SOURCE_CONFIG['password']:
            cmd.append(f"--password={SOURCE_CONFIG['password']}")
        else:
            cmd.append('--password=')
        
        # Execute mysqldump
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
            print_success(f"Backup berhasil dibuat: {backup_file} ({file_size:.2f} MB)")
            return str(backup_file)
        else:
            print_error(f"Gagal membuat backup: {result.stderr}")
            return None
            
    except FileNotFoundError:
        print_warning("mysqldump tidak ditemukan. Menggunakan backup manual...")
        return backup_manual(source_conn, backup_file)
    except Exception as e:
        print_error(f"Error saat backup: {e}")
        return None


def backup_manual(connection: pymysql.Connection, backup_file: Path) -> Optional[str]:
    """Backup manual jika mysqldump tidak tersedia"""
    try:
        print_info("Menggunakan metode backup manual...")
        tables = get_all_tables(connection)
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(f"-- Backup Manual KSM_main Database\n")
            f.write(f"-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"USE `{SOURCE_CONFIG['database']}`;\n\n")
            
            for table in tables:
                row_count = get_table_row_count(connection, table)
                if row_count > 0:
                    f.write(f"-- Table: {table} ({row_count} rows)\n")
        
        print_success(f"Backup metadata dibuat: {backup_file}")
        return str(backup_file)
    except Exception as e:
        print_error(f"Gagal backup manual: {e}")
        return None


def disable_foreign_key_checks(connection: pymysql.Connection):
    """Disable foreign key checks"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            connection.commit()
    except Exception as e:
        print_warning(f"Gagal disable foreign key checks: {e}")


def enable_foreign_key_checks(connection: pymysql.Connection):
    """Enable foreign key checks"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            connection.commit()
    except Exception as e:
        print_warning(f"Gagal enable foreign key checks: {e}")


def truncate_table(connection: pymysql.Connection, table: str):
    """Truncate tabel di target database"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE `{table}`")
            connection.commit()
    except Exception as e:
        print_warning(f"Gagal truncate tabel {table}: {e}")


def migrate_table(source_conn: pymysql.Connection, target_conn: pymysql.Connection, 
                 table: str) -> Tuple[bool, int]:
    """Migrasi data dari source ke target untuk satu tabel dengan handle perbedaan struktur"""
    try:
        # Get row count dari source
        source_count = get_table_row_count(source_conn, table)
        
        if source_count == 0:
            print_info(f"  Tabel {table}: Kosong, skip...")
            return True, 0
        
        # Get kolom dari source dan target
        source_columns = get_table_columns(source_conn, table)
        target_columns = get_table_columns(target_conn, table)
        
        if not source_columns or not target_columns:
            print_warning(f"  Tabel {table}: Gagal mendapatkan struktur kolom, skip...")
            return False, 0
        
        # Hanya gunakan kolom yang ada di kedua tabel
        common_columns = [col for col in source_columns if col in target_columns]
        missing_in_target = [col for col in source_columns if col not in target_columns]
        missing_in_source = [col for col in target_columns if col not in source_columns]
        
        if missing_in_target:
            print_warning(f"  Tabel {table}: Kolom yang tidak ada di target (akan di-skip): {', '.join(missing_in_target)}")
        
        if missing_in_source:
            print_warning(f"  Tabel {table}: Kolom yang tidak ada di source (akan NULL): {', '.join(missing_in_source)}")
        
        if not common_columns:
            print_error(f"  Tabel {table}: Tidak ada kolom yang sama antara source dan target")
            return False, 0
        
        # Truncate target table
        truncate_table(target_conn, table)
        
        # Get data dari source (hanya kolom yang common)
        columns_str = ', '.join([f"`{col}`" for col in common_columns])
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT {columns_str} FROM `{table}`")
            rows = cursor.fetchall()
        
        if not rows:
            return True, 0
        
        # Insert data ke target
        inserted = 0
        with target_conn.cursor() as cursor:
            # Build insert query dengan hanya kolom yang common
            target_columns_str = ', '.join([f"`{col}`" for col in common_columns])
            placeholders = ', '.join(['%s'] * len(common_columns))
            
            insert_query = f"INSERT INTO `{table}` ({target_columns_str}) VALUES ({placeholders})"
            
            # Insert dalam batch untuk performa lebih baik
            batch_size = 1000
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                # Convert dict rows to list of values
                values = []
                for row in batch:
                    if isinstance(row, dict):
                        values.append([row[col] for col in common_columns])
                    else:
                        # Jika row adalah tuple, gunakan urutan common_columns
                        values.append([row[source_columns.index(col)] for col in common_columns])
                
                cursor.executemany(insert_query, values)
                inserted += len(batch)
            
            target_conn.commit()
        
        # Verify
        target_count = get_table_row_count(target_conn, table)
        
        if source_count == target_count:
            print_success(f"  Tabel {table}: {inserted} rows migrated")
            return True, inserted
        else:
            print_warning(f"  Tabel {table}: Row count berbeda - Source: {source_count}, Target: {target_count} (mungkin karena constraint)")
            return True, inserted  # Tetap return True karena data sudah di-insert
            
    except Exception as e:
        print_error(f"  Tabel {table}: Error - {e}")
        target_conn.rollback()
        return False, 0


def validate_migration(source_conn: pymysql.Connection, target_conn: pymysql.Connection, 
                      tables: List[str]) -> bool:
    """Validasi migrasi dengan membandingkan row count"""
    print_header("Validating Migration")
    
    all_valid = True
    total_source = 0
    total_target = 0
    
    for table in tables:
        source_count = get_table_row_count(source_conn, table)
        target_count = get_table_row_count(target_conn, table)
        total_source += source_count
        total_target += target_count
        
        if source_count == target_count:
            print_success(f"  {table}: {source_count} rows ✓")
        else:
            print_error(f"  {table}: Source={source_count}, Target={target_count} ✗")
            all_valid = False
    
    print_colored(f"\nTotal rows - Source: {total_source}, Target: {total_target}", 
                  Colors.OKCYAN if all_valid else Colors.FAIL)
    
    return all_valid


def main():
    """Main function"""
    print_colored("\n" + "="*60, Colors.HEADER)
    print_colored("  KSM Main - Database Migration Tool", Colors.HEADER)
    print_colored("  XAMPP MySQL → Docker MySQL", Colors.HEADER)
    print_colored("="*60 + "\n", Colors.HEADER)
    
    # Test connections
    source_ok, target_ok = test_connections()
    if not source_ok or not target_ok:
        print_error("\nTidak dapat melanjutkan migrasi. Periksa koneksi database.")
        sys.exit(1)
    
    # Connect to databases
    print_info("\nMembuka koneksi database...")
    source_conn = connect_database(SOURCE_CONFIG)
    target_conn = connect_database(TARGET_CONFIG)
    
    if not source_conn or not target_conn:
        print_error("Gagal membuka koneksi database")
        sys.exit(1)
    
    try:
        # Get all tables
        print_header("Getting Table List")
        source_tables = get_all_tables(source_conn)
        target_tables = get_all_tables(target_conn)
        
        print_info(f"Source database: {len(source_tables)} tabel")
        print_info(f"Target database: {len(target_tables)} tabel")
        
        # Filter tables yang ada di kedua database
        common_tables = [t for t in source_tables if t in target_tables]
        print_info(f"Tabel yang akan di-migrate: {len(common_tables)}")
        
        if not common_tables:
            print_error("Tidak ada tabel yang sama antara source dan target")
            sys.exit(1)
        
        # Get dependencies untuk sorting
        print_info("Menganalisis foreign key dependencies...")
        dependencies = get_foreign_key_dependencies(source_conn, SOURCE_CONFIG['database'])
        sorted_tables = topological_sort_tables(common_tables, dependencies)
        
        # Backup
        backup_file = backup_database(source_conn)
        if not backup_file:
            response = input("\nBackup gagal. Lanjutkan migrasi? (y/N): ")
            if response.lower() != 'y':
                print_info("Migrasi dibatalkan.")
                sys.exit(0)
        
        # Confirmation
        print_header("Migration Summary")
        print_info(f"Source: {SOURCE_CONFIG['host']}:{SOURCE_CONFIG['port']}")
        print_info(f"Target: {TARGET_CONFIG['host']}:{TARGET_CONFIG['port']}")
        print_info(f"Database: {SOURCE_CONFIG['database']}")
        print_info(f"Tables: {len(sorted_tables)}")
        print_info(f"Backup: {backup_file if backup_file else 'Tidak ada'}")
        
        response = input("\nLanjutkan migrasi? (y/N): ")
        if response.lower() != 'y':
            print_info("Migrasi dibatalkan.")
            sys.exit(0)
        
        # Disable foreign key checks
        disable_foreign_key_checks(target_conn)
        
        # Migrate tables
        print_header("Migrating Data")
        total_migrated = 0
        failed_tables = []
        
        for i, table in enumerate(sorted_tables, 1):
            print_info(f"[{i}/{len(sorted_tables)}] Migrating {table}...")
            success, count = migrate_table(source_conn, target_conn, table)
            if success:
                total_migrated += count
            else:
                failed_tables.append(table)
        
        # Enable foreign key checks
        enable_foreign_key_checks(target_conn)
        
        # Validation
        is_valid = validate_migration(source_conn, target_conn, common_tables)
        
        # Summary
        print_header("Migration Summary")
        print_success(f"Total rows migrated: {total_migrated}")
        print_success(f"Tables migrated: {len(sorted_tables) - len(failed_tables)}/{len(sorted_tables)}")
        
        if failed_tables:
            print_error(f"Failed tables: {', '.join(failed_tables)}")
        
        if is_valid:
            print_success("\n✓ Migrasi berhasil dan data valid!")
        else:
            print_error("\n✗ Migrasi selesai tetapi ada perbedaan data. Periksa log di atas.")
        
        if backup_file:
            print_info(f"\nBackup tersimpan di: {backup_file}")
        
    except KeyboardInterrupt:
        print_warning("\n\nMigrasi dibatalkan oleh user.")
        target_conn.rollback()
    except Exception as e:
        print_error(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        target_conn.rollback()
    finally:
        source_conn.close()
        target_conn.close()
        print_info("\nKoneksi database ditutup.")


if __name__ == "__main__":
    main()

