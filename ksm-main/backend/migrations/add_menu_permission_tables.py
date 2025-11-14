#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Migration Script
Migration untuk tabel menus, menu_permissions, dan permission_audit_logs
"""

import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db
from models.menu_models import Menu, MenuPermission, PermissionAuditLog
from models import Role
from shared.utils.logger import get_logger

logger = get_logger(__name__)


def create_menu_tables():
    """Create menu-related tables"""
    try:
        logger.info("Creating menu tables...")
        
        # Create tables
        db.create_all()
        
        logger.info("Menu tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating menu tables: {str(e)}")
        return False


def seed_default_menus():
    """Seed default system menus"""
    try:
        logger.info("Seeding default menus...")
        
        # Check if menus already exist
        existing_menus = Menu.query.count()
        if existing_menus > 0:
            logger.info(f"Menus already exist ({existing_menus} menus). Skipping seed.")
            return True
        
        # Create default menus
        default_menus = [
            {
                'name': 'Dashboard',
                'path': '/dashboard',
                'icon': '📊',
                'parent_id': None,
                'order_index': 1,
                'description': 'Halaman utama dashboard',
                'is_system_menu': True
            },
            {
                'name': 'Telegram Bot',
                'path': '/telegram-bot',
                'icon': '🤖',
                'parent_id': None,
                'order_index': 2,
                'description': 'Manajemen Telegram Bot',
                'is_system_menu': True
            },
            {
                'name': 'User Management',
                'path': '/users',
                'icon': '👥',
                'parent_id': None,
                'order_index': 3,
                'description': 'Manajemen pengguna',
                'is_system_menu': True
            },
            {
                'name': 'Role Management',
                'path': '/roles',
                'icon': '🔐',
                'parent_id': None,
                'order_index': 4,
                'description': 'Manajemen role dan permission',
                'is_system_menu': True
            },
            {
                'name': 'Approval Management',
                'path': '/approval-management',
                'icon': '✅',
                'parent_id': None,
                'order_index': 5,
                'description': 'Manajemen persetujuan',
                'is_system_menu': True
            },
            {
                'name': 'Notifications',
                'path': '/notifications',
                'icon': '🔔',
                'parent_id': None,
                'order_index': 6,
                'description': 'Manajemen notifikasi',
                'is_system_menu': True
            },
            {
                'name': 'Agent Status',
                'path': '/agent-status',
                'icon': '🤖',
                'parent_id': None,
                'order_index': 7,
                'description': 'Status Agent AI',
                'is_system_menu': True
            },
            {
                'name': 'Qdrant Knowledge Base',
                'path': '/qdrant-knowledge-base',
                'icon': '🧠',
                'parent_id': None,
                'order_index': 8,
                'description': 'Knowledge Base Qdrant',
                'is_system_menu': True
            },
            {
                'name': 'Request Pembelian',
                'path': '/request-pembelian',
                'icon': '🛒',
                'parent_id': None,
                'order_index': 9,
                'description': 'Manajemen Request Pembelian',
                'is_system_menu': True
            },
            # Additional Admin Menus
            {
                'name': 'Enhanced Notion Tasks',
                'path': '/enhanced-notion-tasks',
                'icon': '📝',
                'parent_id': None,
                'order_index': 11,
                'description': 'Enhanced Notion Tasks Management',
                'is_system_menu': True
            },
            {
                'name': 'Database Discovery',
                'path': '/database-discovery',
                'icon': '🔍',
                'parent_id': None,
                'order_index': 12,
                'description': 'Database Discovery Tools',
                'is_system_menu': True
            },
            {
                'name': 'Enhanced Database',
                'path': '/enhanced-database',
                'icon': '🗄️',
                'parent_id': None,
                'order_index': 13,
                'description': 'Enhanced Database Management',
                'is_system_menu': True
            },
            {
                'name': 'Remind Exp Docs',
                'path': '/remind-exp-docs',
                'icon': '⏰',
                'parent_id': None,
                'order_index': 14,
                'description': 'Remind Expired Documents',
                'is_system_menu': True
            },
            {
                'name': 'Attendance Management',
                'path': '/attendance',
                'icon': '⏰',
                'parent_id': None,
                'order_index': 15,
                'description': 'Attendance Management System',
                'is_system_menu': True
            },
            {
                'name': 'Mobil Management',
                'path': '/mobil',
                'icon': '🚗',
                'parent_id': None,
                'order_index': 16,
                'description': 'Mobil Management System',
                'is_system_menu': True
            },
            {
                'name': 'Stok Barang Management',
                'path': '/stok-barang',
                'icon': '📦',
                'parent_id': None,
                'order_index': 17,
                'description': 'Stok Barang Management System',
                'is_system_menu': True
            }
        ]
        
        created_menus = []
        request_pembelian_id = None
        
        # Create main menus first
        for menu_data in default_menus:
            menu = Menu(**menu_data)
            db.session.add(menu)
            db.session.flush()  # Get the ID
            
            created_menus.append(menu)
            
            # Store request-pembelian ID for submenus
            if menu_data['path'] == '/request-pembelian':
                request_pembelian_id = menu.id
        
        # Create request-pembelian submenus
        submenus = [
            {
                'name': 'Dashboard Request',
                'path': '/request-pembelian/dashboard',
                'icon': '📊',
                'parent_id': request_pembelian_id,
                'order_index': 1,
                'description': 'Dashboard Request Pembelian',
                'is_system_menu': True
            },
            {
                'name': 'Daftar Request',
                'path': '/request-pembelian/daftar-request',
                'icon': '📋',
                'parent_id': request_pembelian_id,
                'order_index': 2,
                'description': 'Daftar Request Pembelian',
                'is_system_menu': True
            },
            {
                'name': 'Vendor Penawaran Approval',
                'path': '/request-pembelian/vendor-penawaran',
                'icon': '📋',
                'parent_id': request_pembelian_id,
                'order_index': 3,
                'description': 'Approval Penawaran Vendor',
                'is_system_menu': True
            },
            {
                'name': 'Upload Penawaran Vendor',
                'path': '/request-pembelian/upload-penawaran',
                'icon': '📄',
                'parent_id': request_pembelian_id,
                'order_index': 4,
                'description': 'Upload Penawaran Vendor',
                'is_system_menu': True
            },
            {
                'name': 'Daftar Barang Vendor',
                'path': '/request-pembelian/daftar-barang-vendor',
                'icon': '📦',
                'parent_id': request_pembelian_id,
                'order_index': 5,
                'description': 'Daftar Barang Vendor',
                'is_system_menu': True
            },
            {
                'name': 'Analisis Vendor',
                'path': '/request-pembelian/analisis-vendor',
                'icon': '🔍',
                'parent_id': request_pembelian_id,
                'order_index': 6,
                'description': 'Analisis Vendor',
                'is_system_menu': True
            },
            {
                'name': 'Laporan Pembelian',
                'path': '/request-pembelian/laporan-pembelian',
                'icon': '📊',
                'parent_id': request_pembelian_id,
                'order_index': 7,
                'description': 'Laporan Pembelian',
                'is_system_menu': True
            }
        ]
        
        for submenu_data in submenus:
            submenu = Menu(**submenu_data)
            db.session.add(submenu)
            created_menus.append(submenu)
        
        db.session.commit()
        
        logger.info(f"Successfully seeded {len(created_menus)} default menus")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding default menus: {str(e)}")
        return False


def create_default_role_permissions():
    """Create default permissions for existing roles"""
    try:
        logger.info("Creating default role permissions...")
        
        # Get all roles
        roles = Role.query.filter_by(is_active=True).all()
        if not roles:
            logger.info("No roles found. Skipping permission creation.")
            return True
        
        # Get all menus
        menus = Menu.query.filter_by(is_active=True).all()
        if not menus:
            logger.info("No menus found. Skipping permission creation.")
            return True
        
        created_permissions = 0
        
        for role in roles:
            # Define permission templates based on role name
            role_name_lower = role.name.lower()
            
            if 'admin' in role_name_lower:
                # Admin gets all permissions
                for menu in menus:
                    permission = MenuPermission(
                        menu_id=menu.id,
                        role_id=role.id,
                        can_read=True,
                        can_create=True,
                        can_update=True,
                        can_delete=True,
                        granted_at=datetime.utcnow()
                    )
                    db.session.add(permission)
                    created_permissions += 1
            
            elif 'manager' in role_name_lower:
                # Manager gets read/create/update permissions for most menus
                for menu in menus:
                    can_read = True
                    can_create = menu.path not in ['/roles', '/agent-status', '/qdrant-knowledge-base']
                    can_update = menu.path not in ['/roles', '/agent-status', '/qdrant-knowledge-base']
                    can_delete = False
                    
                    permission = MenuPermission(
                        menu_id=menu.id,
                        role_id=role.id,
                        can_read=can_read,
                        can_create=can_create,
                        can_update=can_update,
                        can_delete=can_delete,
                        granted_at=datetime.utcnow()
                    )
                    db.session.add(permission)
                    created_permissions += 1
            
            else:
                # Staff gets limited permissions
                for menu in menus:
                    can_read = menu.path in ['/dashboard', '/notifications', '/request-pembelian']
                    can_create = menu.path in ['/request-pembelian']
                    can_update = menu.path in ['/request-pembelian']
                    can_delete = False
                    
                    permission = MenuPermission(
                        menu_id=menu.id,
                        role_id=role.id,
                        can_read=can_read,
                        can_create=can_create,
                        can_update=can_update,
                        can_delete=can_delete,
                        granted_at=datetime.utcnow()
                    )
                    db.session.add(permission)
                    created_permissions += 1
        
        db.session.commit()
        
        logger.info(f"Successfully created {created_permissions} default permissions")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating default role permissions: {str(e)}")
        return False


def run_migration():
    """Run complete migration"""
    try:
        logger.info("Starting permission management migration...")
        
        # Step 1: Create tables
        if not create_menu_tables():
            logger.error("Failed to create menu tables")
            return False
        
        # Step 2: Seed default menus
        if not seed_default_menus():
            logger.error("Failed to seed default menus")
            return False
        
        # Step 3: Create default role permissions
        if not create_default_role_permissions():
            logger.error("Failed to create default role permissions")
            return False
        
        logger.info("Permission management migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False


if __name__ == '__main__':
    # This script can be run directly
    from app import create_app
    
    app = create_app()
    with app.app_context():
        success = run_migration()
        if success:
            print("✅ Migration completed successfully!")
        else:
            print("❌ Migration failed!")
            sys.exit(1)
