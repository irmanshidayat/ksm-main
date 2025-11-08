#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Base Models untuk KSM Main Backend
"""

import pymysql
pymysql.install_as_MySQLdb()

from config.database import db
from datetime import datetime
import base64

class KnowledgeCategory(db.Model):
    """Model untuk kategori knowledge base"""
    __tablename__ = 'knowledge_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('knowledge_categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relasi
    parent = db.relationship('KnowledgeCategory', remote_side=[id], backref='children')
    files = db.relationship('KnowledgeBaseFile', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class KnowledgeTag(db.Model):
    """Model untuk tags knowledge base"""
    __tablename__ = 'knowledge_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), default='#007bff')  # Hex color
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relasi many-to-many dengan file
    files = db.relationship('KnowledgeBaseFile', secondary='file_tags', backref='tags')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class KnowledgeBaseFile(db.Model):
    """Model untuk file knowledge base"""
    __tablename__ = 'knowledge_base_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    file_size = db.Column(db.Integer, nullable=False)
    base64_content = db.Column(db.Text, nullable=False)  # Longtext untuk base64
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('knowledge_categories.id'))
    priority_level = db.Column(db.String(20), default='medium')  # high, medium, low
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relasi
    versions = db.relationship('FileVersion', backref='file', lazy=True, cascade='all, delete-orphan')
    access_users = db.relationship('UserFileAccess', backref='file', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'description': self.description,
            'file_size': self.file_size,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'category_id': self.category_id,
            'priority_level': self.priority_level,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'category': self.category.to_dict() if self.category else None,
            'tags': [tag.to_dict() for tag in self.tags] if self.tags else [],
            'current_version': self.versions[-1].version_number if self.versions else 1
        }
    
    def get_base64_content(self):
        """Mengambil konten base64"""
        return self.base64_content
    
    def set_base64_content(self, file_path):
        """Mengkonversi file ke base64 dan menyimpannya"""
        try:
            with open(file_path, 'rb') as file:
                file_content = file.read()
                self.base64_content = base64.b64encode(file_content).decode('utf-8')
        except Exception as e:
            raise Exception(f"Error converting file to base64: {str(e)}")

class FileVersion(db.Model):
    """Model untuk versioning file"""
    __tablename__ = 'file_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('knowledge_base_files.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    base64_content = db.Column(db.Text, nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    change_description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_id': self.file_id,
            'version_number': self.version_number,
            'filename': self.filename,
            'file_size': self.file_size,
            'change_description': self.change_description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserFileAccess(db.Model):
    """Model untuk akses user ke file"""
    __tablename__ = 'user_file_access'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('knowledge_base_files.id'), nullable=False)
    can_upload = db.Column(db.Boolean, default=False)
    can_edit = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'file_id', name='unique_user_file_access'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'file_id': self.file_id,
            'can_upload': self.can_upload,
            'can_edit': self.can_edit,
            'can_delete': self.can_delete,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Tabel junction untuk many-to-many relationship file-tags
file_tags = db.Table('file_tags',
    db.Column('file_id', db.Integer, db.ForeignKey('knowledge_base_files.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('knowledge_tags.id'), primary_key=True)
)

class User(db.Model):
    """Model untuk user legacy"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120))
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Gmail OAuth fields
    gmail_refresh_token = db.Column(db.Text, nullable=True)
    gmail_access_token = db.Column(db.Text, nullable=True)
    gmail_token_expires_at = db.Column(db.DateTime, nullable=True)
    gmail_connected = db.Column(db.Boolean, default=False)
    
    # Relationships for mobil management (commented out for now)
    # mobil_requests = db.relationship("MobilRequest", back_populates="user")
    # waiting_lists = db.relationship("WaitingList", back_populates="user")
    
    # Relationship untuk vendor
    vendor = db.relationship("Vendor", foreign_keys="[User.vendor_id]", back_populates="user_account")
    
    def to_dict(self):
        # Import lokal untuk menghindari circular import
        try:
            from models.role_management import UserRole, Role  # type: ignore
        except Exception:
            UserRole = None
            Role = None

        roles_list = []
        primary_role_name = None

        if UserRole and Role:
            try:
                assignments = UserRole.query.filter_by(user_id=self.id, is_active=True).order_by(UserRole.is_primary.desc(), UserRole.assigned_at.desc()).all()
                for a in assignments:
                    role_obj = Role.query.get(a.role_id)
                    if role_obj:
                        roles_list.append({
                            'id': role_obj.id,
                            'name': getattr(role_obj, 'name', None),
                            'code': getattr(role_obj, 'code', None),
                            'level': getattr(role_obj, 'level', None),
                            'is_management': getattr(role_obj, 'is_management', None),
                            'department_id': getattr(role_obj, 'department_id', None)
                        })
                        if (a.is_primary and not primary_role_name) or primary_role_name is None:
                            primary_role_name = getattr(role_obj, 'name', None)
            except Exception:
                # Fallback diam-diam ke legacy role jika query gagal
                primary_role_name = None

        if not primary_role_name:
            primary_role_name = self.role  # fallback legacy

        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            # Pertahankan field legacy untuk kompatibilitas
            'role': self.role,
            # Tambahan field baru yang konsisten dengan relasi
            'legacy_role': self.role,
            'primary_role': primary_role_name,
            'roles': roles_list,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class EmailLog(db.Model):
    """Model untuk log email yang dikirim"""
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vendor_email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('sent', 'failed', 'pending'), default='pending')
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    error_message = db.Column(db.Text, nullable=True)
    message_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='email_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vendor_email': self.vendor_email,
            'subject': self.subject,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'error_message': self.error_message,
            'message_id': self.message_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class TelegramSettings(db.Model):
    """Model untuk pengaturan telegram bot"""
    __tablename__ = 'telegram_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    bot_token = db.Column(db.String(255))
    admin_chat_id = db.Column(db.String(50))  # Chat ID untuk admin notifications
    is_active = db.Column(db.Boolean, default=False)
    company_id = db.Column(db.String(100), default='PT. Kian Santang Muliatama')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'bot_token': self.bot_token,
            'admin_chat_id': self.admin_chat_id,
            'is_active': self.is_active,
            'company_id': self.company_id,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class BotStatusHistory(db.Model):
    """Model untuk history status bot"""
    __tablename__ = 'bot_status_history'
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'status': self.status,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
