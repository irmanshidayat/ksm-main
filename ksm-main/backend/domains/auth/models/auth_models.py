#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auth Models untuk KSM Main Backend
Model untuk authentication dan user management
"""

import pymysql
pymysql.install_as_MySQLdb()

from config.database import db
from datetime import datetime

class User(db.Model):
    """Model untuk user"""
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
    
    # Relationship untuk vendor - menggunakan lazy import untuk menghindari circular dependency
    @property
    def vendor(self):
        """Lazy load vendor relationship"""
        try:
            from domains.vendor.models.vendor_models import Vendor
            return db.session.query(Vendor).filter_by(id=self.vendor_id).first()
        except Exception:
            return None
    
    def to_dict(self):
        # Import lokal untuk menghindari circular import
        try:
            from domains.role.models.role_models import UserRole, Role  # type: ignore
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

