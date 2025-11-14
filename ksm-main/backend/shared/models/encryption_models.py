#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Encryption Models - Best Practices Implementation
Model untuk encryption key management dan data encryption
"""

from datetime import datetime, timedelta
from config.database import db
from sqlalchemy import Index, UniqueConstraint


class EncryptionKey(db.Model):
    """Model untuk encryption keys dengan best practices"""
    __tablename__ = 'encryption_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.String(100), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    key_type = db.Column(db.String(20), nullable=False)  # master, department, user
    encrypted_key = db.Column(db.Text, nullable=False)  # Key yang dienkripsi dengan master key
    key_version = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    last_rotated = db.Column(db.DateTime)
    rotation_count = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    department = db.relationship('Department', backref='encryption_keys')
    creator = db.relationship('User', backref='created_encryption_keys')
    
    # Indexes
    __table_args__ = (
        Index('idx_encryption_key_id', 'key_id'),
        Index('idx_encryption_key_department', 'department_id'),
        Index('idx_encryption_key_active', 'is_active'),
        Index('idx_encryption_key_expires', 'expires_at'),
        Index('idx_encryption_key_type', 'key_type'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'key_id': self.key_id,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'key_type': self.key_type,
            'key_version': self.key_version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'last_rotated': self.last_rotated.isoformat() if self.last_rotated else None,
            'rotation_count': self.rotation_count,
            'created_by': self.created_by,
            'days_until_expiry': (self.expires_at - datetime.utcnow()).days if self.expires_at else None
        }
    
    def is_expired(self):
        """Check if key is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def is_near_expiry(self, days_threshold=7):
        """Check if key is near expiry"""
        if self.expires_at:
            return (self.expires_at - datetime.utcnow()).days <= days_threshold
        return False

class KeyRotationLog(db.Model):
    """Model untuk log key rotation dengan best practices"""
    __tablename__ = 'key_rotation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.String(100), nullable=False)
    old_key_version = db.Column(db.Integer)
    new_key_version = db.Column(db.Integer)
    rotation_reason = db.Column(db.String(100), nullable=False)  # scheduled, security_breach, manual
    rotated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    rotated_at = db.Column(db.DateTime, default=datetime.utcnow)
    affected_records = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, failed
    error_message = db.Column(db.Text)
    duration_seconds = db.Column(db.Integer)  # Time taken for rotation
    
    # Relationships
    rotator = db.relationship('User', backref='key_rotations')
    
    # Indexes
    __table_args__ = (
        Index('idx_rotation_log_key', 'key_id'),
        Index('idx_rotation_log_rotated_by', 'rotated_by'),
        Index('idx_rotation_log_rotated_at', 'rotated_at'),
        Index('idx_rotation_log_status', 'status'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'key_id': self.key_id,
            'old_key_version': self.old_key_version,
            'new_key_version': self.new_key_version,
            'rotation_reason': self.rotation_reason,
            'rotated_by': self.rotated_by,
            'rotated_by_name': self.rotator.username if self.rotator else None,
            'rotated_at': self.rotated_at.isoformat() if self.rotated_at else None,
            'affected_records': self.affected_records,
            'status': self.status,
            'error_message': self.error_message,
            'duration_seconds': self.duration_seconds
        }

class KeyBackup(db.Model):
    """Model untuk backup encryption keys dengan best practices"""
    __tablename__ = 'key_backups'
    
    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.String(100), nullable=False)
    backup_type = db.Column(db.String(20), nullable=False)  # full, incremental, differential
    backup_location = db.Column(db.String(500), nullable=False)  # Path atau cloud location
    encrypted_backup = db.Column(db.Text, nullable=False)  # Encrypted backup data
    backup_hash = db.Column(db.String(64), nullable=False)  # SHA-256 hash untuk integrity
    backup_size = db.Column(db.Integer)  # Size in bytes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_verified = db.Column(db.Boolean, default=False)
    verification_hash = db.Column(db.String(64))
    verified_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    creator = db.relationship('User', backref='created_key_backups')
    
    # Indexes
    __table_args__ = (
        Index('idx_key_backup_key', 'key_id'),
        Index('idx_key_backup_type', 'backup_type'),
        Index('idx_key_backup_created', 'created_at'),
        Index('idx_key_backup_expires', 'expires_at'),
        Index('idx_key_backup_verified', 'is_verified'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'key_id': self.key_id,
            'backup_type': self.backup_type,
            'backup_location': self.backup_location,
            'backup_hash': self.backup_hash,
            'backup_size': self.backup_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_verified': self.is_verified,
            'verification_hash': self.verification_hash,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'created_by': self.created_by,
            'days_until_expiry': (self.expires_at - datetime.utcnow()).days if self.expires_at else None
        }
    
    def is_expired(self):
        """Check if backup is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

class KeyRecoveryLog(db.Model):
    """Model untuk log key recovery dengan best practices"""
    __tablename__ = 'key_recovery_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.String(100), nullable=False)
    backup_id = db.Column(db.Integer, db.ForeignKey('key_backups.id'))
    recovery_type = db.Column(db.String(20), nullable=False)  # restore, emergency, test
    recovered_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    recovery_reason = db.Column(db.Text, nullable=False)
    recovery_status = db.Column(db.String(20), default='in_progress')  # success, failed, partial
    recovered_at = db.Column(db.DateTime, default=datetime.utcnow)
    verification_status = db.Column(db.String(20), default='pending')  # verified, failed, pending
    error_message = db.Column(db.Text)
    duration_seconds = db.Column(db.Integer)  # Time taken for recovery
    
    # Relationships
    backup = db.relationship('KeyBackup', backref='recovery_logs')
    recoverer = db.relationship('User', backref='key_recoveries')
    
    # Indexes
    __table_args__ = (
        Index('idx_recovery_log_key', 'key_id'),
        Index('idx_recovery_log_backup', 'backup_id'),
        Index('idx_recovery_log_recovered_by', 'recovered_by'),
        Index('idx_recovery_log_recovered_at', 'recovered_at'),
        Index('idx_recovery_log_status', 'recovery_status'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'key_id': self.key_id,
            'backup_id': self.backup_id,
            'recovery_type': self.recovery_type,
            'recovered_by': self.recovered_by,
            'recovered_by_name': self.recoverer.username if self.recoverer else None,
            'recovery_reason': self.recovery_reason,
            'recovery_status': self.recovery_status,
            'recovered_at': self.recovered_at.isoformat() if self.recovered_at else None,
            'verification_status': self.verification_status,
            'error_message': self.error_message,
            'duration_seconds': self.duration_seconds
        }

class EncryptedData(db.Model):
    """Model untuk encrypted data dengan best practices"""
    __tablename__ = 'encrypted_data'
    
    id = db.Column(db.Integer, primary_key=True)
    data_type = db.Column(db.String(50), nullable=False)  # customer_data, financial_data, etc.
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    encrypted_content = db.Column(db.Text, nullable=False)  # Encrypted data
    salt = db.Column(db.String(100), nullable=False)  # Salt untuk decryption
    encryption_version = db.Column(db.String(10), default='1.0')
    encryption_algorithm = db.Column(db.String(20), default='Fernet')
    data_size = db.Column(db.Integer)  # Original data size in bytes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Optional expiration
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    last_accessed_at = db.Column(db.DateTime)
    access_count = db.Column(db.Integer, default=0)
    
    # Relationships
    department = db.relationship('Department', backref='encrypted_data')
    creator = db.relationship('User', backref='created_encrypted_data')
    
    # Indexes
    __table_args__ = (
        Index('idx_encrypted_data_type', 'data_type'),
        Index('idx_encrypted_data_department', 'department_id'),
        Index('idx_encrypted_data_created', 'created_at'),
        Index('idx_encrypted_data_expires', 'expires_at'),
        Index('idx_encrypted_data_accessed', 'last_accessed_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'data_type': self.data_type,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'encryption_version': self.encryption_version,
            'encryption_algorithm': self.encryption_algorithm,
            'data_size': self.data_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_by': self.created_by,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'access_count': self.access_count,
            'days_until_expiry': (self.expires_at - datetime.utcnow()).days if self.expires_at else None
        }
    
    def is_expired(self):
        """Check if encrypted data is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def update_access_info(self):
        """Update access information"""
        self.last_accessed_at = datetime.utcnow()
        self.access_count += 1
        db.session.commit()

class DataEncryptionPolicy(db.Model):
    """Model untuk policy encryption data dengan best practices"""
    __tablename__ = 'data_encryption_policies'
    
    id = db.Column(db.Integer, primary_key=True)
    data_type = db.Column(db.String(50), nullable=False)
    classification_level = db.Column(db.String(20), nullable=False)  # public, internal, confidential, restricted
    encryption_required = db.Column(db.Boolean, default=False)
    encryption_algorithm = db.Column(db.String(20), default='AES-256')
    key_rotation_days = db.Column(db.Integer, default=90)
    data_retention_days = db.Column(db.Integer)  # Data retention policy
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    creator = db.relationship('User', backref='created_encryption_policies')
    
    # Indexes
    __table_args__ = (
        Index('idx_encryption_policy_type', 'data_type'),
        Index('idx_encryption_policy_classification', 'classification_level'),
        Index('idx_encryption_policy_active', 'is_active'),
        UniqueConstraint('data_type', 'classification_level', name='unique_encryption_policy'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'data_type': self.data_type,
            'classification_level': self.classification_level,
            'encryption_required': self.encryption_required,
            'encryption_algorithm': self.encryption_algorithm,
            'key_rotation_days': self.key_rotation_days,
            'data_retention_days': self.data_retention_days,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
