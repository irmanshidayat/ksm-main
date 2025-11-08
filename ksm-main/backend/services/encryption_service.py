#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Encryption Service - Best Practices Implementation
Sistem encryption key management dengan backup dan recovery yang komprehensif
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import secrets
from flask import current_app
from sqlalchemy import and_, or_

logger = logging.getLogger(__name__)

class EncryptionService:
    """Service untuk encryption dengan best practices"""
    
    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.backend = default_backend()
    
    def _get_or_create_master_key(self):
        """Get atau create master encryption key"""
        master_key = os.getenv('ENCRYPTION_MASTER_KEY')
        if not master_key:
            master_key = Fernet.generate_key().decode()
            os.environ['ENCRYPTION_MASTER_KEY'] = master_key
            logger.warning("⚠️ Master encryption key generated. Please save it securely!")
        
        return master_key.encode()
    
    @staticmethod
    def generate_secure_key():
        """Generate secure encryption key"""
        return Fernet.generate_key()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: bytes, iterations: int = 100000) -> bytes:
        """Derive key dari password dengan PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    @staticmethod
    def encrypt_data(data: str, key: bytes) -> dict:
        """Encrypt data dengan key yang diberikan"""
        try:
            # Generate random salt
            salt = os.urandom(16)
            
            # Encrypt data
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data.encode())
            
            return {
                'encrypted_data': base64.urlsafe_b64encode(encrypted_data).decode(),
                'salt': base64.urlsafe_b64encode(salt).decode(),
                'algorithm': 'Fernet',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Error encrypting data: {str(e)}")
            raise
    
    @staticmethod
    def decrypt_data(encrypted_data: str, key: bytes) -> str:
        """Decrypt data dengan key yang diberikan"""
        try:
            # Decode encrypted data
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Decrypt data
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_bytes)
            
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"❌ Error decrypting data: {str(e)}")
            raise
    
    def encrypt_with_master_key(self, data: str) -> dict:
        """Encrypt data dengan master key"""
        return self.encrypt_data(data, self.master_key)
    
    def decrypt_with_master_key(self, encrypted_data: str) -> str:
        """Decrypt data dengan master key"""
        return self.decrypt_data(encrypted_data, self.master_key)

class KeyManagementService:
    """Service untuk key management dengan best practices"""
    
    def __init__(self):
        self.encryption_service = EncryptionService()
    
    def create_department_key(self, department_id: int, key_type: str = 'department') -> dict:
        """Create encryption key untuk department"""
        try:
            # Generate new key
            new_key = EncryptionService.generate_secure_key()
            
            # Encrypt key dengan master key
            encrypted_key_info = self.encryption_service.encrypt_with_master_key(
                base64.urlsafe_b64encode(new_key).decode()
            )
            
            # Create key record
            from models.role_management import EncryptionKey
            key_record = EncryptionKey(
                key_id=f"dept_{department_id}_v1",
                department_id=department_id,
                key_type=key_type,
                encrypted_key=encrypted_key_info['encrypted_data'],
                key_version=1,
                expires_at=datetime.utcnow() + timedelta(days=90)
            )
            
            # Save to database
            from models.role_management import db
            db.session.add(key_record)
            db.session.commit()
            
            # Create backup
            self.create_key_backup(key_record.key_id, 'initial')
            
            logger.info(f"✅ Created encryption key for department {department_id}")
            
            return {
                'key_id': key_record.key_id,
                'department_id': department_id,
                'key_version': 1,
                'expires_at': key_record.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating department key: {str(e)}")
            raise
    
    def rotate_department_key(self, department_id: int, reason: str = 'scheduled') -> dict:
        """Rotate encryption key untuk department"""
        try:
            from models.role_management import EncryptionKey, KeyRotationLog, db
            
            # Get current active key
            current_key = EncryptionKey.query.filter_by(
                department_id=department_id,
                is_active=True
            ).first()
            
            if not current_key:
                raise Exception("No active key found for department")
            
            # Generate new key
            new_key = EncryptionService.generate_secure_key()
            
            # Encrypt new key dengan master key
            encrypted_key_info = self.encryption_service.encrypt_with_master_key(
                base64.urlsafe_b64encode(new_key).decode()
            )
            
            # Create new key record
            new_key_record = EncryptionKey(
                key_id=f"dept_{department_id}_v{current_key.key_version + 1}",
                department_id=department_id,
                key_type=current_key.key_type,
                encrypted_key=encrypted_key_info['encrypted_data'],
                key_version=current_key.key_version + 1,
                expires_at=datetime.utcnow() + timedelta(days=90)
            )
            db.session.add(new_key_record)
            
            # Create rotation log
            rotation_log = KeyRotationLog(
                key_id=new_key_record.key_id,
                old_key_version=current_key.key_version,
                new_key_version=new_key_record.key_version,
                rotation_reason=reason,
                rotated_by=self._get_current_user_id(),
                status='in_progress'
            )
            db.session.add(rotation_log)
            
            # Mark old key as inactive
            current_key.is_active = False
            current_key.last_rotated = datetime.utcnow()
            
            db.session.commit()
            
            # Re-encrypt existing data
            self._re_encrypt_department_data(department_id, current_key, new_key_record)
            
            # Update rotation log
            rotation_log.status = 'completed'
            rotation_log.affected_records = self._count_affected_records(department_id)
            db.session.commit()
            
            # Create backup for new key
            self.create_key_backup(new_key_record.key_id, 'rotation')
            
            logger.info(f"✅ Successfully rotated key for department {department_id}")
            
            return {
                'old_key_id': current_key.key_id,
                'new_key_id': new_key_record.key_id,
                'rotation_reason': reason,
                'affected_records': rotation_log.affected_records
            }
            
        except Exception as e:
            logger.error(f"❌ Error rotating department key: {str(e)}")
            if 'db' in locals():
                db.session.rollback()
            raise
    
    def _re_encrypt_department_data(self, department_id: int, old_key_record, new_key_record):
        """Re-encrypt existing data dengan key baru"""
        try:
            from models.role_management import EncryptedData, db
            
            # Get all encrypted data for department
            encrypted_data_list = EncryptedData.query.filter_by(
                department_id=department_id
            ).all()
            
            re_encrypted_count = 0
            
            for encrypted_data in encrypted_data_list:
                try:
                    # Decrypt with old key
                    old_key = self._get_decrypted_key(old_key_record)
                    decrypted_data = EncryptionService.decrypt_data(
                        encrypted_data.encrypted_content, old_key
                    )
                    
                    # Encrypt with new key
                    new_key = self._get_decrypted_key(new_key_record)
                    new_encrypted_info = EncryptionService.encrypt_data(decrypted_data, new_key)
                    
                    # Update encrypted data
                    encrypted_data.encrypted_content = new_encrypted_info['encrypted_data']
                    encrypted_data.encryption_version = f"v{new_key_record.key_version}"
                    encrypted_data.updated_at = datetime.utcnow()
                    
                    re_encrypted_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to re-encrypt data {encrypted_data.id}: {str(e)}")
                    continue
            
            db.session.commit()
            logger.info(f"✅ Re-encrypted {re_encrypted_count} records for department {department_id}")
            
        except Exception as e:
            logger.error(f"❌ Error re-encrypting department data: {str(e)}")
            raise
    
    def _get_decrypted_key(self, key_record) -> bytes:
        """Get decrypted key dari key record"""
        try:
            encrypted_key = key_record.encrypted_key
            decrypted_key_str = self.encryption_service.decrypt_with_master_key(encrypted_key)
            return base64.urlsafe_b64decode(decrypted_key_str.encode())
        except Exception as e:
            logger.error(f"❌ Error decrypting key {key_record.key_id}: {str(e)}")
            raise
    
    def _count_affected_records(self, department_id: int) -> int:
        """Count affected records untuk department"""
        try:
            from models.role_management import EncryptedData
            return EncryptedData.query.filter_by(department_id=department_id).count()
        except Exception as e:
            logger.error(f"❌ Error counting affected records: {str(e)}")
            return 0
    
    def _get_current_user_id(self) -> int:
        """Get current user ID (implementasi sesuai dengan auth system)"""
        # TODO: Implementasi sesuai dengan auth system yang ada
        return 1  # Placeholder
    
    def create_key_backup(self, key_id: str, backup_type: str = 'full') -> dict:
        """Create backup untuk encryption key"""
        try:
            from models.role_management import EncryptionKey, KeyBackup, db
            
            # Get key to backup
            key = EncryptionKey.query.filter_by(key_id=key_id).first()
            if not key:
                raise Exception("Key not found")
            
            # Create backup data
            backup_data = {
                'key_id': key.key_id,
                'department_id': key.department_id,
                'key_type': key.key_type,
                'encrypted_key': key.encrypted_key,
                'key_version': key.key_version,
                'created_at': key.created_at.isoformat(),
                'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                'backup_type': backup_type,
                'backup_timestamp': datetime.utcnow().isoformat()
            }
            
            # Encrypt backup dengan master key
            encrypted_backup = self.encryption_service.encrypt_with_master_key(
                json.dumps(backup_data)
            )
            
            # Create backup hash
            backup_hash = hashlib.sha256(
                encrypted_backup['encrypted_data'].encode()
            ).hexdigest()
            
            # Store backup
            backup = KeyBackup(
                key_id=key_id,
                backup_type=backup_type,
                backup_location=f"backup/{key_id}_{backup_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                encrypted_backup=encrypted_backup['encrypted_data'],
                backup_hash=backup_hash,
                expires_at=datetime.utcnow() + timedelta(days=365)  # 1 tahun retention
            )
            db.session.add(backup)
            db.session.commit()
            
            # Verify backup
            self.verify_key_backup(backup.id)
            
            logger.info(f"✅ Created backup for key {key_id}")
            
            return {
                'backup_id': backup.id,
                'key_id': key_id,
                'backup_type': backup_type,
                'backup_hash': backup_hash
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating key backup: {str(e)}")
            raise
    
    def verify_key_backup(self, backup_id: int) -> bool:
        """Verify backup integrity"""
        try:
            from models.role_management import KeyBackup, db
            
            backup = KeyBackup.query.get(backup_id)
            if not backup:
                raise Exception("Backup not found")
            
            # Decrypt backup
            decrypted_backup = self.encryption_service.decrypt_with_master_key(
                backup.encrypted_backup
            )
            
            # Verify hash
            current_hash = hashlib.sha256(
                backup.encrypted_backup.encode()
            ).hexdigest()
            
            if current_hash != backup.backup_hash:
                raise Exception("Backup hash mismatch")
            
            # Parse and validate data
            backup_data = json.loads(decrypted_backup)
            required_fields = ['key_id', 'department_id', 'key_type', 'encrypted_key']
            for field in required_fields:
                if field not in backup_data:
                    raise Exception(f"Missing required field: {field}")
            
            # Mark as verified
            backup.is_verified = True
            backup.verification_hash = current_hash
            db.session.commit()
            
            logger.info(f"✅ Verified backup {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying backup {backup_id}: {str(e)}")
            if 'backup' in locals():
                backup.is_verified = False
                db.session.commit()
            return False
    
    def recover_key(self, backup_id: int, recovery_reason: str) -> dict:
        """Recover key dari backup"""
        try:
            from models.role_management import KeyBackup, EncryptionKey, KeyRecoveryLog, db
            
            backup = KeyBackup.query.get(backup_id)
            if not backup:
                raise Exception("Backup not found")
            
            if not backup.is_verified:
                raise Exception("Backup not verified")
            
            # Decrypt backup
            decrypted_backup = self.encryption_service.decrypt_with_master_key(
                backup.encrypted_backup
            )
            backup_data = json.loads(decrypted_backup)
            
            # Check if key already exists
            existing_key = EncryptionKey.query.filter_by(
                key_id=backup_data['key_id']
            ).first()
            
            if existing_key and existing_key.is_active:
                raise Exception("Active key already exists")
            
            # Create recovered key
            recovered_key = EncryptionKey(
                key_id=backup_data['key_id'],
                department_id=backup_data['department_id'],
                key_type=backup_data['key_type'],
                encrypted_key=backup_data['encrypted_key'],
                key_version=backup_data['key_version'],
                created_at=datetime.fromisoformat(backup_data['created_at']),
                expires_at=datetime.fromisoformat(backup_data['expires_at']) if backup_data['expires_at'] else None,
                is_active=True
            )
            db.session.add(recovered_key)
            
            # Create recovery log
            recovery_log = KeyRecoveryLog(
                key_id=backup_data['key_id'],
                recovery_type='restore',
                recovered_by=self._get_current_user_id(),
                recovery_reason=recovery_reason,
                recovery_status='success'
            )
            db.session.add(recovery_log)
            
            db.session.commit()
            
            logger.info(f"✅ Successfully recovered key {backup_data['key_id']}")
            
            return {
                'key_id': backup_data['key_id'],
                'department_id': backup_data['department_id'],
                'recovery_reason': recovery_reason,
                'recovered_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error recovering key: {str(e)}")
            if 'db' in locals():
                db.session.rollback()
            raise
    
    def get_key_rotation_schedule(self, department_id: int) -> dict:
        """Get key rotation schedule untuk department"""
        try:
            from models.role_management import EncryptionKey, Department
            
            # Get department
            department = Department.query.get(department_id)
            if not department:
                raise Exception("Department not found")
            
            # Get current key
            current_key = EncryptionKey.query.filter_by(
                department_id=department_id,
                is_active=True
            ).first()
            
            if not current_key:
                return {
                    'department_id': department_id,
                    'department_name': department.name,
                    'has_active_key': False,
                    'next_rotation': None
                }
            
            # Calculate next rotation
            next_rotation = current_key.expires_at - timedelta(days=7)  # 7 days before expiry
            
            return {
                'department_id': department_id,
                'department_name': department.name,
                'has_active_key': True,
                'current_key_id': current_key.key_id,
                'current_key_version': current_key.key_version,
                'expires_at': current_key.expires_at.isoformat(),
                'next_rotation': next_rotation.isoformat(),
                'days_until_rotation': (next_rotation - datetime.utcnow()).days
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting key rotation schedule: {str(e)}")
            raise

class DataEncryptionService:
    """Service untuk data encryption dengan best practices"""
    
    def __init__(self):
        self.key_management = KeyManagementService()
    
    def encrypt_department_data(self, data: str, department_id: int) -> dict:
        """Encrypt data untuk department"""
        try:
            from models.role_management import EncryptionKey, EncryptedData, db
            
            # Get department key
            key_record = EncryptionKey.query.filter_by(
                department_id=department_id,
                is_active=True
            ).first()
            
            if not key_record:
                raise Exception(f"No active key found for department {department_id}")
            
            # Get decrypted key
            key = self.key_management._get_decrypted_key(key_record)
            
            # Encrypt data
            encrypted_info = EncryptionService.encrypt_data(data, key)
            
            # Store encrypted data
            encrypted_data = EncryptedData(
                data_type='department_data',
                department_id=department_id,
                encrypted_content=encrypted_info['encrypted_data'],
                salt=encrypted_info['salt'],
                encryption_version=f"v{key_record.key_version}",
                expires_at=datetime.utcnow() + timedelta(days=365)
            )
            db.session.add(encrypted_data)
            db.session.commit()
            
            return {
                'encrypted_data_id': encrypted_data.id,
                'department_id': department_id,
                'encryption_version': encrypted_data.encryption_version,
                'expires_at': encrypted_data.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error encrypting department data: {str(e)}")
            raise
    
    def decrypt_department_data(self, encrypted_data_id: int) -> str:
        """Decrypt data untuk department"""
        try:
            from models.role_management import EncryptedData, EncryptionKey, db
            
            # Get encrypted data
            encrypted_data = EncryptedData.query.get(encrypted_data_id)
            if not encrypted_data:
                raise Exception("Encrypted data not found")
            
            # Get department key
            key_record = EncryptionKey.query.filter_by(
                department_id=encrypted_data.department_id,
                is_active=True
            ).first()
            
            if not key_record:
                raise Exception(f"No active key found for department {encrypted_data.department_id}")
            
            # Get decrypted key
            key = self.key_management._get_decrypted_key(key_record)
            
            # Decrypt data
            decrypted_data = EncryptionService.decrypt_data(
                encrypted_data.encrypted_content, key
            )
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"❌ Error decrypting department data: {str(e)}")
            raise
