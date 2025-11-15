#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk membuat admin user jika belum ada
"""

import sys
import os

# Tambahkan path backend ke sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from config.database import db
from models import User
from werkzeug.security import generate_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_user():
    """Membuat admin user jika belum ada"""
    with app.app_context():
        try:
            # Cek apakah admin sudah ada berdasarkan username
            admin_user = User.query.filter_by(username='admin').first()
            
            if admin_user:
                # Update email jika berbeda
                if admin_user.email != 'admin@KSM.com':
                    logger.info(f"📝 Admin user sudah ada tapi email berbeda: {admin_user.email}")
                    logger.info(f"   Mengupdate email menjadi admin@KSM.com...")
                    admin_user.email = 'admin@KSM.com'
                    db.session.commit()
                    logger.info(f"✅ Email berhasil diupdate!")
                
                # Update password jika perlu (reset ke admin123)
                from werkzeug.security import check_password_hash
                if not check_password_hash(admin_user.password_hash, 'admin123'):
                    logger.info(f"📝 Mengupdate password menjadi admin123...")
                    admin_user.password_hash = generate_password_hash('admin123')
                    db.session.commit()
                    logger.info(f"✅ Password berhasil diupdate!")
                
                # Pastikan role adalah admin
                if admin_user.role != 'admin':
                    logger.info(f"📝 Mengupdate role menjadi admin...")
                    admin_user.role = 'admin'
                    db.session.commit()
                    logger.info(f"✅ Role berhasil diupdate!")
                
                logger.info(f"✅ Admin user siap digunakan:")
                logger.info(f"   Username: {admin_user.username}")
                logger.info(f"   Email: {admin_user.email}")
                logger.info(f"   Password: admin123")
                logger.info(f"   Role: {admin_user.role}")
                return admin_user
            
            # Cek apakah email admin@KSM.com sudah digunakan oleh user lain
            existing_email = User.query.filter_by(email='admin@KSM.com').first()
            if existing_email and existing_email.username != 'admin':
                logger.warning(f"⚠️  Email admin@KSM.com sudah digunakan oleh user: {existing_email.username}")
                logger.info(f"   Mengupdate email user tersebut...")
                existing_email.email = f"{existing_email.username}@KSM.com"
                db.session.commit()
            
            # Buat admin user baru
            logger.info("📝 Membuat admin user baru...")
            admin_password = generate_password_hash('admin123')
            
            admin_user = User(
                username='admin',
                email='admin@KSM.com',
                password_hash=admin_password,
                role='admin',
                is_active=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            logger.info("✅ Admin user berhasil dibuat!")
            logger.info(f"   Username: admin")
            logger.info(f"   Email: admin@KSM.com")
            logger.info(f"   Password: admin123")
            logger.info(f"   Role: admin")
            
            return admin_user
            
        except Exception as e:
            logger.error(f"❌ Error saat membuat admin user: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    try:
        create_admin_user()
        logger.info("🎉 Script selesai dijalankan!")
    except Exception as e:
        logger.error(f"❌ Script gagal: {str(e)}")
        sys.exit(1)

