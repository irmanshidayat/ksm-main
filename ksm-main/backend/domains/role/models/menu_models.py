#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Menu Management Models - Dynamic Menu Structure
Sistem menu dinamis dengan permission-based access control
"""

from datetime import datetime
from config.database import db
from sqlalchemy import Index, UniqueConstraint
import json


class Menu(db.Model):
    """Model untuk struktur menu dinamis dengan best practices"""
    __tablename__ = 'menus'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(50), default='📄')
    parent_id = db.Column(db.Integer, db.ForeignKey('menus.id'))
    order_index = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    is_system_menu = db.Column(db.Boolean, default=False)  # System menus cannot be deleted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('Menu', remote_side=[id], backref='sub_menus')
    menu_permissions = db.relationship('MenuPermission', backref='menu', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_menu_path', 'path'),
        Index('idx_menu_parent', 'parent_id'),
        Index('idx_menu_order', 'order_index'),
        Index('idx_menu_active', 'is_active'),
        UniqueConstraint('path', name='unique_menu_path'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'path': self.path,
            'icon': self.icon,
            'parent_id': self.parent_id,
            'order_index': self.order_index,
            'description': self.description,
            'is_active': self.is_active,
            'is_system_menu': self.is_system_menu,
            'sub_menus': [sub.to_dict() for sub in self.sub_menus if sub.is_active],
            'permissions_count': self.menu_permissions.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_menu_tree(cls):
        """Get hierarchical menu tree"""
        def build_tree(parent_id=None):
            menus = cls.query.filter_by(parent_id=parent_id, is_active=True).order_by(cls.order_index).all()
            result = []
            for menu in menus:
                menu_dict = menu.to_dict()
                menu_dict['sub_menus'] = build_tree(menu.id)
                result.append(menu_dict)
            return result
        
        return build_tree()
    
    @classmethod
    def get_user_accessible_menus(cls, user_id):
        """Get menus accessible by specific user based on their roles"""
        from domains.auth.models import User
        from domains.role.models import UserRole
        
        # Get user roles
        user_roles = db.session.query(UserRole.role_id).filter_by(user_id=user_id).all()
        role_ids = [role.role_id for role in user_roles]
        
        if not role_ids:
            return []
        
        # Get accessible menus through role permissions
        accessible_menus = db.session.query(cls).join(MenuPermission).filter(
            MenuPermission.role_id.in_(role_ids),
            MenuPermission.granted == True,
            cls.is_active == True
        ).order_by(cls.order_index).all()
        
        return [menu.to_dict() for menu in accessible_menus]


class MenuPermission(db.Model):
    """Model untuk mapping menu-permission dengan role"""
    __tablename__ = 'menu_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    can_read = db.Column(db.Boolean, default=False)
    can_create = db.Column(db.Boolean, default=False)
    can_update = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    show_in_sidebar = db.Column(db.Boolean, default=True)  # Control visibility in sidebar
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Optional expiration
    is_active = db.Column(db.Boolean, default=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_menu_permission_menu', 'menu_id'),
        Index('idx_menu_permission_role', 'role_id'),
        Index('idx_menu_permission_active', 'is_active'),
        UniqueConstraint('menu_id', 'role_id', name='unique_menu_role_permission'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'menu_id': self.menu_id,
            'menu_name': self.menu.name if self.menu else None,
            'role_id': self.role_id,
            'role_name': self.role.name if self.role else None,
            'can_read': self.can_read,
            'can_create': self.can_create,
            'can_update': self.can_update,
            'can_delete': self.can_delete,
            'show_in_sidebar': getattr(self, 'show_in_sidebar', True),
            'granted_by': self.granted_by,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active
        }
    
    def has_permission(self, action):
        """Check if has specific permission"""
        action_map = {
            'read': self.can_read,
            'create': self.can_create,
            'update': self.can_update,
            'delete': self.can_delete
        }
        return action_map.get(action, False)
    
    def set_permission(self, action, value):
        """Set specific permission"""
        if action == 'read':
            self.can_read = value
        elif action == 'create':
            self.can_create = value
        elif action == 'update':
            self.can_update = value
        elif action == 'delete':
            self.can_delete = value


class PermissionAuditLog(db.Model):
    """Model untuk audit trail permission changes"""
    __tablename__ = 'permission_audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # 'grant', 'revoke', 'update'
    resource_type = db.Column(db.String(50), nullable=False)  # 'menu_permission', 'role_permission'
    resource_id = db.Column(db.Integer, nullable=False)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class RoleLevelTemplate(db.Model):
    """Template default menu permissions per level role"""
    __tablename__ = 'role_level_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100))
    permissions = db.Column(db.JSON, nullable=False)  # Array of { menu_id, permissions: {can_read,can_create,can_update,can_delete} }
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_role_level_template_level', 'level'),
        Index('idx_role_level_template_active', 'is_active'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'name': self.name,
            'permissions': self.permissions,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

