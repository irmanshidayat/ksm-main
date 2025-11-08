#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration Script untuk Attendance Tables
Membuat tabel-tabel untuk sistem absensi karyawan
"""

import os
import sys
import logging
from datetime import datetime

# Add parent directory to path untuk import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db, init_database
from flask import Flask
from models.attendance_models import (
    AttendanceRecord, AttendanceLeave, OvertimeRequest, AttendanceSettings
)
from models.knowledge_base import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_attendance_tables():
    """Buat semua tabel attendance"""
    try:
        # Initialize Flask app
        app = Flask(__name__)
        
        # Initialize database
        init_database(app)
        
        with app.app_context():
            logger.info("🚀 Starting attendance tables creation...")
            
            # Test database connection
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text('SELECT 1'))
                logger.info("✅ Database connection successful")
            except Exception as conn_error:
                logger.error(f"❌ Database connection failed: {conn_error}")
                return False
            
            # Create all tables
            logger.info("📋 Creating attendance tables...")
            db.create_all()
            
            # Create indexes manually untuk memastikan
            logger.info("🔍 Creating indexes...")
            try:
                # Indexes untuk AttendanceRecord
                db.engine.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_attendance_user_date 
                    ON attendance_records (user_id, clock_in)
                """))
                
                db.engine.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_attendance_date 
                    ON attendance_records (clock_in)
                """))
                
                db.engine.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_attendance_status 
                    ON attendance_records (status)
                """))
                
                db.engine.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_attendance_approved 
                    ON attendance_records (is_approved)
                """))
                
                # Indexes untuk AttendanceLeave
                db.engine.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_leave_user 
                    ON attendance_leaves (user_id)
                """))
                
                db.engine.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_leave_dates 
                    ON attendance_leaves (start_date, end_date)
                """))
                
                db.engine.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_leave_status 
                    ON attendance_leaves (status)
                """))
                
                db.engine.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_leave_type 
                    ON attendance_leaves (leave_type)
                """))
                
                # Indexes untuk OvertimeRequest
                db.engine.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_overtime_user 
                    ON overtime_requests (user_id)
                """))
                
                db.engine.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_overtime_attendance 
                    ON overtime_requests (attendance_id)
                """))
                
                db.engine.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_overtime_status 
                    ON overtime_requests (status)
                """))
                
                # Indexes untuk AttendanceSettings
                db.engine.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_attendance_settings_company 
                    ON attendance_settings (company_id)
                """))
                
                logger.info("✅ Indexes created successfully")
                
            except Exception as index_error:
                logger.warning(f"⚠️ Some indexes might already exist: {index_error}")
            
            # Insert default attendance settings
            logger.info("⚙️ Creating default attendance settings...")
            existing_settings = AttendanceSettings.query.first()
            if not existing_settings:
                default_settings = AttendanceSettings(
                    company_id='PT. Kian Santang Muliatama',
                    work_start_time=datetime.strptime('08:00', '%H:%M').time(),
                    work_end_time=datetime.strptime('17:00', '%H:%M').time(),
                    grace_period_minutes=30,
                    overtime_enabled=True,
                    overtime_rate_multiplier=1.5,
                    location_validation_enabled=False,
                    photo_required=True,
                    max_photo_size_mb=5,
                    reminder_enabled=True,
                    reminder_time=datetime.strptime('07:30', '%H:%M').time()
                )
                db.session.add(default_settings)
                db.session.commit()
                logger.info("✅ Default attendance settings created")
            else:
                logger.info("ℹ️ Attendance settings already exist")
            
            # Verify tables creation
            logger.info("🔍 Verifying tables creation...")
            
            # Check AttendanceRecord table
            attendance_count = db.session.execute(db.text("SELECT COUNT(*) FROM attendance_records")).scalar()
            logger.info(f"📊 AttendanceRecord table: {attendance_count} records")
            
            # Check AttendanceLeave table
            leave_count = db.session.execute(db.text("SELECT COUNT(*) FROM attendance_leaves")).scalar()
            logger.info(f"📊 AttendanceLeave table: {leave_count} records")
            
            # Check OvertimeRequest table
            overtime_count = db.session.execute(db.text("SELECT COUNT(*) FROM overtime_requests")).scalar()
            logger.info(f"📊 OvertimeRequest table: {overtime_count} records")
            
            # Check AttendanceSettings table
            settings_count = db.session.execute(db.text("SELECT COUNT(*) FROM attendance_settings")).scalar()
            logger.info(f"📊 AttendanceSettings table: {settings_count} records")
            
            logger.info("🎉 Attendance tables creation completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error creating attendance tables: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

def verify_foreign_keys():
    """Verifikasi foreign key constraints"""
    try:
        app = Flask(__name__)
        init_database(app)
        
        with app.app_context():
            logger.info("🔗 Verifying foreign key constraints...")
            
            # Check foreign keys
            foreign_keys = db.session.execute(db.text("""
                SELECT 
                    TABLE_NAME,
                    COLUMN_NAME,
                    CONSTRAINT_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME
                FROM 
                    INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE 
                    REFERENCED_TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME IN ('attendance_records', 'attendance_leaves', 'overtime_requests')
                ORDER BY TABLE_NAME, COLUMN_NAME
            """)).fetchall()
            
            if foreign_keys:
                logger.info("✅ Foreign key constraints found:")
                for fk in foreign_keys:
                    logger.info(f"   {fk[0]}.{fk[1]} -> {fk[3]}.{fk[4]}")
            else:
                logger.warning("⚠️ No foreign key constraints found")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error verifying foreign keys: {str(e)}")
        return False

def create_sample_data():
    """Buat sample data untuk testing (optional)"""
    try:
        app = Flask(__name__)
        init_database(app)
        
        with app.app_context():
            logger.info("📝 Creating sample data...")
            
            # Cek apakah ada user untuk testing
            test_user = User.query.filter_by(username='admin').first()
            if not test_user:
                logger.warning("⚠️ No test user found, skipping sample data creation")
                return True
            
            # Cek apakah sudah ada sample data
            existing_attendance = AttendanceRecord.query.first()
            if existing_attendance:
                logger.info("ℹ️ Sample data already exists, skipping")
                return True
            
            # Buat sample attendance record
            from datetime import datetime, timedelta
            
            sample_attendance = AttendanceRecord(
                user_id=test_user.id,
                clock_in=datetime.now() - timedelta(hours=8),
                clock_in_latitude=-6.2088,
                clock_in_longitude=106.8456,
                clock_in_address='Jakarta, Indonesia',
                clock_in_photo='data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...',  # Sample base64
                clock_out=datetime.now(),
                clock_out_latitude=-6.2088,
                clock_out_longitude=106.8456,
                clock_out_address='Jakarta, Indonesia',
                clock_out_photo='data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...',  # Sample base64
                work_duration_minutes=480,  # 8 hours
                status='present',
                notes='Sample attendance record'
            )
            
            db.session.add(sample_attendance)
            db.session.commit()
            
            logger.info("✅ Sample data created successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error creating sample data: {str(e)}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("ATTENDANCE TABLES MIGRATION SCRIPT")
    print("=" * 60)
    
    # Create tables
    success = create_attendance_tables()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        # Verify foreign keys
        verify_foreign_keys()
        
        # Ask user if they want sample data
        try:
            create_sample = input("\n🤔 Do you want to create sample data? (y/n): ").lower().strip()
            if create_sample in ['y', 'yes']:
                create_sample_data()
        except KeyboardInterrupt:
            print("\n👋 Migration completed without sample data")
        
        print("\n📋 Next steps:")
        print("1. Update app.py to register attendance blueprint")
        print("2. Install new dependencies: pip install openpyxl reportlab Pillow")
        print("3. Test the attendance endpoints")
        print("4. Create frontend components")
        
    else:
        print("\n" + "=" * 60)
        print("❌ MIGRATION FAILED!")
        print("=" * 60)
        print("Please check the error messages above and fix the issues.")
        sys.exit(1)
