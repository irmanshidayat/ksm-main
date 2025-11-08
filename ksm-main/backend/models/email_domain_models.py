#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Domain Models untuk KSM Main Backend
"""

import pymysql
pymysql.install_as_MySQLdb()

from config.database import db
from datetime import datetime
import base64
import os
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

class UserEmailDomain(db.Model):
    """Model untuk konfigurasi email domain per user"""
    __tablename__ = 'user_email_domains'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    domain_name = db.Column(db.String(100), nullable=False)  # company.com
    smtp_server = db.Column(db.String(255), nullable=False)   # smtp.company.com
    smtp_port = db.Column(db.Integer, nullable=False)        # 587
    username = db.Column(db.String(255), nullable=False)     # user@company.com
    password = db.Column(db.String(500), nullable=False)      # encrypted
    from_name = db.Column(db.String(255), nullable=False)    # Company Name
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relasi
    user = db.relationship('User', backref='email_domains')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'domain_name': self.domain_name,
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'username': self.username,
            'from_name': self.from_name,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_decrypted_password(self):
        """Decrypt password untuk digunakan"""
        try:
            encryption_key = os.getenv('EMAIL_DOMAIN_ENCRYPTION_KEY')
            
            # Log untuk debugging (tanpa menampilkan key lengkap)
            if not encryption_key:
                logger.error("❌ EMAIL_DOMAIN_ENCRYPTION_KEY tidak ditemukan di environment variables")
                logger.error("   Pastikan EMAIL_DOMAIN_ENCRYPTION_KEY sudah di-set di .env atau docker-compose.yml")
                return None
            
            # Validasi format encryption key
            if len(encryption_key) < 32:
                logger.error(f"❌ EMAIL_DOMAIN_ENCRYPTION_KEY terlalu pendek (minimal 32 karakter)")
                return None
            
            # Convert string key to bytes
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()
            
            # Validasi bahwa key adalah valid Fernet key
            try:
                fernet = Fernet(encryption_key)
            except ValueError as ve:
                logger.error(f"❌ EMAIL_DOMAIN_ENCRYPTION_KEY tidak valid (bukan Fernet key): {str(ve)}")
                logger.error("   Pastikan key adalah base64-encoded 32-byte key (44 karakter)")
                return None
            
            # Decrypt password
            try:
                decrypted_password = fernet.decrypt(self.password.encode()).decode()
                logger.debug(f"✅ Password berhasil didekripsi untuk domain {self.domain_name}")
                return decrypted_password
            except InvalidToken as it:
                logger.error(f"❌ Gagal mendekripsi password: Token tidak valid")
                logger.error(f"   Kemungkinan encryption key berbeda dengan yang digunakan saat enkripsi")
                logger.error(f"   Domain: {self.domain_name}, Error: {str(it)}")
                return None
            except Exception as de:
                logger.error(f"❌ Error saat dekripsi password: {str(de)}")
                logger.error(f"   Domain: {self.domain_name}, Error type: {type(de).__name__}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Unexpected error saat mendekripsi password: {str(e)}")
            logger.error(f"   Domain: {self.domain_name}, Error type: {type(e).__name__}")
            return None
    
    @staticmethod
    def encrypt_password(password: str) -> str:
        """Encrypt password untuk disimpan"""
        try:
            encryption_key = os.getenv('EMAIL_DOMAIN_ENCRYPTION_KEY')
            
            if not encryption_key:
                # Generate key jika belum ada (Opsi 3: Auto-generate)
                encryption_key_bytes = Fernet.generate_key()
                encryption_key = encryption_key_bytes.decode()
                
                # Set ke environment variable untuk session saat ini
                os.environ['EMAIL_DOMAIN_ENCRYPTION_KEY'] = encryption_key
                
                logger.warning("="*70)
                logger.warning("⚠️  EMAIL_DOMAIN_ENCRYPTION_KEY TIDAK DITEMUKAN")
                logger.warning("="*70)
                logger.warning("✅ Sistem telah AUTO-GENERATE key baru (Opsi 3)")
                logger.warning("")
                logger.warning("📋 KEY YANG DI-GENERATE:")
                logger.warning(f"   {encryption_key}")
                logger.warning("")
                logger.warning("📝 INSTRUKSI:")
                logger.warning("   1. Copy key di atas")
                logger.warning("   2. Tambahkan ke file .env atau docker-compose.yml:")
                logger.warning(f"      EMAIL_DOMAIN_ENCRYPTION_KEY={encryption_key}")
                logger.warning("")
                logger.warning("   Atau jalankan script helper:")
                logger.warning("      python scripts/generate_email_domain_encryption_key.py")
                logger.warning("")
                logger.warning("⚠️  PENTING:")
                logger.warning("   - Key ini HANYA berlaku untuk session saat ini")
                logger.warning("   - Setelah restart, key akan hilang jika tidak ditambahkan ke .env")
                logger.warning("   - Password yang sudah dienkripsi dengan key lama tidak bisa didekripsi dengan key baru!")
                logger.warning("="*70)
            
            # Convert string key to bytes
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()
            
            # Validasi bahwa key adalah valid Fernet key
            try:
                fernet = Fernet(encryption_key)
            except ValueError as ve:
                logger.error(f"❌ EMAIL_DOMAIN_ENCRYPTION_KEY tidak valid: {str(ve)}")
                logger.error("   Password akan disimpan tanpa enkripsi (TIDAK AMAN!)")
                return password  # Return plain password if encryption fails
            
            encrypted_password = fernet.encrypt(password.encode()).decode()
            logger.debug("✅ Password berhasil dienkripsi")
            return encrypted_password
        except Exception as e:
            logger.error(f"❌ Error encrypting password: {str(e)}")
            logger.error("   Password akan disimpan tanpa enkripsi (TIDAK AMAN!)")
            return password  # Return plain password if encryption fails
    
    def set_password(self, password: str):
        """Set encrypted password"""
        self.password = self.encrypt_password(password)
    
    def validate_config(self) -> dict:
        """Validate email domain configuration"""
        errors = []
        
        if not self.domain_name:
            errors.append("Domain name is required")
        
        if not self.smtp_server:
            errors.append("SMTP server is required")
        
        if not self.smtp_port or self.smtp_port < 1 or self.smtp_port > 65535:
            errors.append("Valid SMTP port is required")
        
        if not self.username or '@' not in self.username:
            errors.append("Valid email username is required")
        
        if not self.from_name:
            errors.append("From name is required")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
