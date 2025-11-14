#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Attachment Model - Model untuk menyimpan metadata file attachment email
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from config.database import db

class EmailAttachment(db.Model):
    __tablename__ = 'email_attachments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # File information
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=False)
    file_extension = Column(String(10), nullable=True)
    
    # Relationship to request pembelian (optional)
    request_pembelian_id = Column(Integer, ForeignKey('request_pembelian.id'), nullable=True)
    
    # User who uploaded the file
    uploaded_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Email information (optional - for tracking which email this was attached to)
    email_subject = Column(String(255), nullable=True)
    email_recipient = Column(String(255), nullable=True)
    
    # Status
    status = Column(String(50), default='active')  # active, deleted, expired
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    uploaded_by_user = relationship('User', backref='uploaded_attachments')
    request_pembelian = relationship('RequestPembelian', backref='email_attachments')
    
    def __repr__(self):
        return f'<EmailAttachment {self.original_filename}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_mb': round(self.file_size / (1024 * 1024), 2),
            'mime_type': self.mime_type,
            'file_extension': self.file_extension,
            'request_pembelian_id': self.request_pembelian_id,
            'uploaded_by_user_id': self.uploaded_by_user_id,
            'email_subject': self.email_subject,
            'email_recipient': self.email_recipient,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }
    
    @staticmethod
    def get_file_size_mb(file_size_bytes):
        """Convert bytes to MB"""
        return round(file_size_bytes / (1024 * 1024), 2)
    
    @staticmethod
    def get_allowed_extensions():
        """Get list of allowed file extensions"""
        return [
            # Documents
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
            # Archives
            '.zip', '.rar', '.7z', '.tar', '.gz',
            # Text files
            '.txt', '.csv', '.rtf',
            # CAD files
            '.dwg', '.dxf', '.step', '.stp',
            # Other common formats
            '.json', '.xml', '.yaml', '.yml'
        ]
    
    @staticmethod
    def get_max_file_size_mb():
        """Get maximum file size in MB"""
        return 50  # 50MB max file size
    
    @staticmethod
    def is_allowed_file_type(filename):
        """Check if file type is allowed"""
        if not filename:
            return False
        
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        return file_ext in EmailAttachment.get_allowed_extensions()
    
    @staticmethod
    def is_file_size_valid(file_size_bytes):
        """Check if file size is within limits"""
        max_size_bytes = EmailAttachment.get_max_file_size_mb() * 1024 * 1024
        return file_size_bytes <= max_size_bytes

