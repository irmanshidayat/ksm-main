#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script migrasi untuk tabel request_pembelian
- Menambahkan kolom vendor_upload_deadline jika belum ada
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from config.database import db


def create_app():
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


def migrate_request_pembelian():
    print("🚀 Starting Request Pembelian migration...")
    app = create_app()
    with app.app_context():
        try:
            db.session.execute(db.text("SELECT 1"))
            print("✅ Database connection successful")

            # Ambil semua kolom saat ini
            current_cols = [row[0] for row in db.session.execute(db.text(
                """
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'KSM_main' AND TABLE_NAME = 'request_pembelian'
                """
            )).fetchall()]

            # Daftar kolom yang diperlukan sesuai model (minimal agar read endpoints jalan)
            planned_alters = []

            # request_number - harus ditambahkan sebelum reference_id karena bisa digunakan sebagai fallback
            if 'request_number' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN request_number VARCHAR(50) NULL")
                planned_alters.append("CREATE INDEX IF NOT EXISTS idx_request_number ON request_pembelian(request_number)")

            # reference_id
            if 'reference_id' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN reference_id VARCHAR(50) NULL")
                planned_alters.append("CREATE INDEX IF NOT EXISTS idx_request_reference_id ON request_pembelian(reference_id)")

            # user_id, department_id (nullable dulu)
            if 'user_id' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN user_id INT NULL")
            if 'department_id' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN department_id INT NULL")

            # priority
            if 'priority' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN priority ENUM('low','medium','high','urgent') NOT NULL DEFAULT 'medium'")

            # total_budget
            if 'total_budget' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN total_budget DECIMAL(15,2) NULL")

            # request_date, required_date
            if 'request_date' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN request_date DATETIME NULL")
            if 'required_date' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN required_date DATETIME NULL")

            # vendor_upload_deadline, analysis_deadline, approval_deadline
            if 'vendor_upload_deadline' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN vendor_upload_deadline DATETIME NULL")
            if 'analysis_deadline' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN analysis_deadline DATETIME NULL")
            if 'approval_deadline' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN approval_deadline DATETIME NULL")

            # notes
            if 'notes' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN notes TEXT NULL")

            # created_at, updated_at
            if 'created_at' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN created_at DATETIME NULL")
            if 'updated_at' not in current_cols:
                planned_alters.append("ALTER TABLE request_pembelian ADD COLUMN updated_at DATETIME NULL")

            # status: pastikan enum mendukung nilai baru
            planned_alters.append(
                "ALTER TABLE request_pembelian MODIFY COLUMN status ENUM('draft','submitted','vendor_uploading','under_analysis','approved','rejected','vendor_selected','completed') NOT NULL DEFAULT 'draft'"
            )

            # Eksekusi ALTERs
            for sql in planned_alters:
                try:
                    print(f"🔄 Executing: {sql}")
                    db.session.execute(db.text(sql))
                    db.session.commit()
                    print("✅ Success")
                except Exception as e:
                    print(f"⚠️  Skip/Warning: {e}")
                    db.session.rollback()

            # Migrasi data dari kolom lama jika tersedia
            try:
                # Populate request_number dari reference_id jika request_number NULL
                if 'request_number' in current_cols and 'reference_id' in current_cols:
                    db.session.execute(db.text(
                        """
                        UPDATE request_pembelian
                        SET request_number = reference_id
                        WHERE request_number IS NULL AND reference_id IS NOT NULL
                        """
                    ))
                    db.session.commit()
                    print("✅ Populated request_number from reference_id")
                
                # reference_id dari request_number (jika kolom request_number sudah ada sebelumnya)
                if 'request_number' in current_cols and 'reference_id' in current_cols:
                    db.session.execute(db.text(
                        """
                        UPDATE request_pembelian
                        SET reference_id = request_number
                        WHERE reference_id IS NULL AND request_number IS NOT NULL
                        """
                    ))
                    db.session.commit()
                    print("✅ Populated reference_id from request_number")
                
                # Generate request_number jika masih NULL (untuk data yang tidak punya keduanya)
                if 'request_number' in current_cols:
                    db.session.execute(db.text(
                        """
                        UPDATE request_pembelian
                        SET request_number = CONCAT('PR-', DATE_FORMAT(created_at, '%Y%m%d'), '-', LPAD(id, 4, '0'))
                        WHERE request_number IS NULL
                        """
                    ))
                    db.session.commit()
                    print("✅ Generated request_number for existing records")
                
                # Generate reference_id jika masih NULL
                if 'reference_id' in current_cols:
                    db.session.execute(db.text(
                        """
                        UPDATE request_pembelian
                        SET reference_id = CONCAT('REQ-', DATE_FORMAT(created_at, '%Y%m%d'), '-', LPAD(id, 4, '0'))
                        WHERE reference_id IS NULL
                        """
                    ))
                    db.session.commit()
                    print("✅ Generated reference_id for existing records")

                # total_budget dari total_amount
                if 'total_amount' in current_cols:
                    db.session.execute(db.text(
                        """
                        UPDATE request_pembelian
                        SET total_budget = total_amount
                        WHERE (total_budget IS NULL OR total_budget = 0) AND total_amount IS NOT NULL
                        """
                    ))
                    db.session.commit()
                    print("✅ Populated total_budget from total_amount")

                # created_at/updated_at default jika NULL
                db.session.execute(db.text(
                    """
                    UPDATE request_pembelian
                    SET created_at = COALESCE(created_at, NOW()),
                        updated_at = COALESCE(updated_at, NOW()),
                        request_date = COALESCE(request_date, created_at)
                    """
                ))
                db.session.commit()
                print("✅ Normalized timestamps")
            except Exception as e:
                print(f"⚠️  Data migration warning: {e}")
                db.session.rollback()

            # Set NOT NULL dan UNIQUE untuk request_number dan reference_id setelah data di-populate
            try:
                # Refresh current_cols setelah ALTERs
                current_cols_after = [row[0] for row in db.session.execute(db.text(
                    """
                    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = 'KSM_main' AND TABLE_NAME = 'request_pembelian'
                    """
                )).fetchall()]
                
                if 'request_number' in current_cols_after:
                    # Cek apakah ada NULL values
                    null_count = db.session.execute(db.text(
                        "SELECT COUNT(*) FROM request_pembelian WHERE request_number IS NULL"
                    )).scalar()
                    if null_count == 0:
                        # Pastikan unique constraint dan NOT NULL
                        try:
                            db.session.execute(db.text(
                                "ALTER TABLE request_pembelian MODIFY COLUMN request_number VARCHAR(50) NOT NULL"
                            ))
                            db.session.commit()
                            print("✅ Set request_number to NOT NULL")
                        except Exception as e:
                            print(f"⚠️  Could not set request_number to NOT NULL: {e}")
                            db.session.rollback()
                
                if 'reference_id' in current_cols_after:
                    null_count = db.session.execute(db.text(
                        "SELECT COUNT(*) FROM request_pembelian WHERE reference_id IS NULL"
                    )).scalar()
                    if null_count == 0:
                        try:
                            db.session.execute(db.text(
                                "ALTER TABLE request_pembelian MODIFY COLUMN reference_id VARCHAR(50) NOT NULL"
                            ))
                            db.session.commit()
                            print("✅ Set reference_id to NOT NULL")
                        except Exception as e:
                            print(f"⚠️  Could not set reference_id to NOT NULL: {e}")
                            db.session.rollback()
            except Exception as e:
                print(f"⚠️  Post-migration constraint warning: {e}")
                db.session.rollback()

            return 0
        except Exception as e:
            print(f"❌ Error in request_pembelian migration: {e}")
            db.session.rollback()
            return 1


def main():
    sys.exit(migrate_request_pembelian())


if __name__ == "__main__":
    main()


