#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Permission Management Service
Service untuk business logic permission management dengan best practices
"""

from datetime import datetime, timedelta
from config.database import db
from domains.role.models.menu_models import Menu, MenuPermission, PermissionAuditLog
from domains.role.models.role_models import Role
from shared.utils.logger import get_logger
import json

# Centralized registry definitions to avoid duplication across features
DEFAULT_MENU_DEFINITIONS = [
    # Main Menu Items
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
        'icon': '🧩',
        'parent_id': None,
        'order_index': 4,
        'description': 'Manajemen role',
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
        'name': 'Notifikasi',
        'path': '/notifications',
        'icon': '🔔',
        'parent_id': None,
        'order_index': 5,
        'description': 'Manajemen notifikasi',
        'is_system_menu': True
    },
    {
        'name': 'Knowledge Base',
        'path': '/qdrant-knowledge-base',
        'icon': '📚',
        'parent_id': None,
        'order_index': 7,
        'description': 'Knowledge Base Qdrant',
        'is_system_menu': True
    },
    {
        'name': 'Remind Exp Docs',
        'path': '/remind-exp-docs',
        'icon': '📅',
        'parent_id': None,
        'order_index': 8,
        'description': 'Remind Expired Documents',
        'is_system_menu': True
    },
    {
        'name': 'Agent Status',
        'path': '/agent-status',
        'icon': '🛰️',
        'parent_id': None,
        'order_index': 10,
        'description': 'Status layanan Agent AI',
        'is_system_menu': True
    },
    {
        'name': 'Enhanced Notion Tasks',
        'path': '/enhanced-notion-tasks',
        'icon': '🗒️',
        'parent_id': None,
        'order_index': 11,
        'description': 'Peningkatan integrasi Notion Tasks',
        'is_system_menu': True
    },
    {
        'name': 'Database Discovery',
        'path': '/database-discovery',
        'icon': '🧭',
        'parent_id': None,
        'order_index': 12,
        'description': 'Eksplorasi database',
        'is_system_menu': True
    },
    {
        'name': 'Enhanced Database',
        'path': '/enhanced-database',
        'icon': '🗄️',
        'parent_id': None,
        'order_index': 13,
        'description': 'Fitur lanjutan database',
        'is_system_menu': True
    },

    # Section: Absensi Karyawan
    {
        'name': 'Absensi Karyawan',
        'path': '/attendance',
        'icon': '⏰',
        'parent_id': None,
        'order_index': 20,
        'description': 'Manajemen Absensi Karyawan',
        'is_system_menu': True
    },
    {
        'name': 'Dashboard Absensi',
        'path': '/attendance/dashboard',
        'icon': '📊',
        'parent_id': None,  # Will be linked to /attendance if exists
        'order_index': 1,
        'description': 'Dashboard Absensi',
        'is_system_menu': True
    },
    {
        'name': 'Clock In/Out',
        'path': '/attendance/clock-in',
        'icon': '⏰',
        'parent_id': None,
        'order_index': 2,
        'description': 'Clock In/Out',
        'is_system_menu': True
    },
    {
        'name': 'Riwayat Absensi',
        'path': '/attendance/history',
        'icon': '📋',
        'parent_id': None,
        'order_index': 3,
        'description': 'Riwayat Absensi',
        'is_system_menu': True
    },
    {
        'name': 'Pengajuan Izin',
        'path': '/attendance/leave-request',
        'icon': '📝',
        'parent_id': None,
        'order_index': 4,
        'description': 'Pengajuan Izin',
        'is_system_menu': True
    },
    {
        'name': 'Laporan Absensi',
        'path': '/attendance/report',
        'icon': '📈',
        'parent_id': None,
        'order_index': 5,
        'description': 'Laporan Absensi',
        'is_system_menu': True
    },
    {
        'name': 'Task Harian',
        'path': '/attendance/daily-task',
        'icon': '✅',
        'parent_id': None,
        'order_index': 6,
        'description': 'Task Harian',
        'is_system_menu': True
    },
    {
        'name': 'Performance Task',
        'path': '/attendance/task-dashboard',
        'icon': '📊',
        'parent_id': None,
        'order_index': 7,
        'description': 'Performance Task',
        'is_system_menu': True
    },

    # Section: Mobil Management
    {
        'name': 'Mobil Management',
        'path': '/mobil',
        'icon': '🚗',
        'parent_id': None,
        'order_index': 30,
        'description': 'Manajemen Mobil',
        'is_system_menu': True
    },
    {
        'name': 'Dashboard Mobil',
        'path': '/mobil/dashboard',
        'icon': '📊',
        'parent_id': None,
        'order_index': 1,
        'description': 'Dashboard Mobil',
        'is_system_menu': True
    },
    {
        'name': 'Kalender Mobil',
        'path': '/mobil/calendar',
        'icon': '📅',
        'parent_id': None,
        'order_index': 2,
        'description': 'Kalender Mobil',
        'is_system_menu': True
    },
    {
        'name': 'Request Mobil',
        'path': '/mobil/request',
        'icon': '📝',
        'parent_id': None,
        'order_index': 3,
        'description': 'Request Mobil',
        'is_system_menu': True
    },

    # Section: Stok Barang
    {
        'name': 'Stok Barang',
        'path': '/stok-barang',
        'icon': '📦',
        'parent_id': None,
        'order_index': 40,
        'description': 'Manajemen Stok Barang',
        'is_system_menu': True
    },
    {
        'name': 'Dashboard Stok',
        'path': '/stok-barang/dashboard',
        'icon': '📊',
        'parent_id': None,
        'order_index': 1,
        'description': 'Dashboard Stok',
        'is_system_menu': True
    },
    {
        'name': 'Daftar Barang',
        'path': '/stok-barang/daftar-barang',
        'icon': '📋',
        'parent_id': None,
        'order_index': 2,
        'description': 'Daftar Barang',
        'is_system_menu': True
    },
    {
        'name': 'Barang Masuk',
        'path': '/stok-barang/barang-masuk',
        'icon': '📥',
        'parent_id': None,
        'order_index': 3,
        'description': 'Barang Masuk',
        'is_system_menu': True
    },
    {
        'name': 'Barang Keluar',
        'path': '/stok-barang/barang-keluar',
        'icon': '📤',
        'parent_id': None,
        'order_index': 4,
        'description': 'Barang Keluar',
        'is_system_menu': True
    },
    {
        'name': 'Category',
        'path': '/stok-barang/category',
        'icon': '📂',
        'parent_id': None,
        'order_index': 5,
        'description': 'Category',
        'is_system_menu': True
    },

    # Section: Request Pembelian
    {
        'name': 'Request Pembelian',
        'path': '/request-pembelian',
        'icon': '🛒',
        'parent_id': None,
        'order_index': 50,
        'description': 'Manajemen Request Pembelian',
        'is_system_menu': True
    },
    {
        'name': 'Dashboard Request',
        'path': '/request-pembelian/dashboard',
        'icon': '📊',
        'parent_id': None,
        'order_index': 1,
        'description': 'Dashboard Request',
        'is_system_menu': True
    },
    {
        'name': 'Daftar Request',
        'path': '/request-pembelian/daftar-request',
        'icon': '📋',
        'parent_id': None,
        'order_index': 2,
        'description': 'Daftar Request',
        'is_system_menu': True
    },
    {
        'name': 'Vendor Penawaran Approval',
        'path': '/request-pembelian/vendor-penawaran',
        'icon': '📋',
        'parent_id': None,
        'order_index': 3,
        'description': 'Vendor Penawaran Approval',
        'is_system_menu': True
    },
    {
        'name': 'Upload Penawaran Vendor',
        'path': '/request-pembelian/upload-penawaran',
        'icon': '📄',
        'parent_id': None,
        'order_index': 4,
        'description': 'Upload Penawaran Vendor',
        'is_system_menu': True
    },
    {
        'name': 'Daftar Barang Vendor',
        'path': '/request-pembelian/daftar-barang-vendor',
        'icon': '📦',
        'parent_id': None,
        'order_index': 5,
        'description': 'Daftar Barang Vendor',
        'is_system_menu': True
    },
    {
        'name': 'Analisis Vendor',
        'path': '/request-pembelian/analisis-vendor',
        'icon': '🔍',
        'parent_id': None,
        'order_index': 6,
        'description': 'Analisis Vendor',
        'is_system_menu': True
    },
    {
        'name': 'Laporan Pembelian',
        'path': '/request-pembelian/laporan-pembelian',
        'icon': '📊',
        'parent_id': None,
        'order_index': 7,
        'description': 'Laporan Pembelian',
        'is_system_menu': True
    }
]

logger = get_logger(__name__)


class PermissionService:
    """Service untuk business logic permission management"""
    
    @staticmethod
    def create_default_menus():
        """Create default system menus"""
        try:
            default_menus = list(DEFAULT_MENU_DEFINITIONS)
            
            created_menus = []
            parent_menu_ids = {}
            
            for menu_data in default_menus:
                # Check if menu already exists
                existing_menu = Menu.query.filter_by(path=menu_data['path']).first()
                if existing_menu:
                    logger.info(f"Menu {menu_data['name']} already exists")
                    # Store parent menu IDs for submenu assignment
                    if menu_data['path'] in ['/attendance', '/mobil', '/stok-barang', '/request-pembelian']:
                        parent_menu_ids[menu_data['path']] = existing_menu.id
                    continue
                
                # Create menu
                menu = Menu(**menu_data)
                db.session.add(menu)
                db.session.flush()  # Get the ID
                
                created_menus.append(menu)
                
                # Store parent menu IDs for submenu assignment
                if menu_data['path'] in ['/attendance', '/mobil', '/stok-barang', '/request-pembelian']:
                    parent_menu_ids[menu_data['path']] = menu.id
            
            # Update parent_id for submenus
            for menu_data in default_menus:
                if menu_data['path'].startswith('/attendance/') and '/attendance' in parent_menu_ids:
                    menu = Menu.query.filter_by(path=menu_data['path']).first()
                    if menu:
                        menu.parent_id = parent_menu_ids['/attendance']
                elif menu_data['path'].startswith('/mobil/') and '/mobil' in parent_menu_ids:
                    menu = Menu.query.filter_by(path=menu_data['path']).first()
                    if menu:
                        menu.parent_id = parent_menu_ids['/mobil']
                elif menu_data['path'].startswith('/stok-barang/') and '/stok-barang' in parent_menu_ids:
                    menu = Menu.query.filter_by(path=menu_data['path']).first()
                    if menu:
                        menu.parent_id = parent_menu_ids['/stok-barang']
                elif menu_data['path'].startswith('/request-pembelian/') and '/request-pembelian' in parent_menu_ids:
                    menu = Menu.query.filter_by(path=menu_data['path']).first()
                    if menu:
                        menu.parent_id = parent_menu_ids['/request-pembelian']
            
            db.session.commit()
            
            # Fix parent_id untuk menu yang sudah ada (setelah commit)
            PermissionService.fix_menu_parent_ids()
            
            logger.info(f"Created {len(created_menus)} default menus")
            return created_menus
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating default menus: {str(e)}")
            raise e

    @staticmethod
    def fix_menu_parent_ids():
        """Fix parent_id untuk menu yang sudah ada di database"""
        try:
            # Get parent menu IDs
            parent_menu_ids = {}
            parent_paths = ['/attendance', '/mobil', '/stok-barang', '/request-pembelian']
            
            for path in parent_paths:
                parent_menu = Menu.query.filter_by(path=path).first()
                if parent_menu:
                    parent_menu_ids[path] = parent_menu.id
            
            # Update parent_id for attendance submenus
            if '/attendance' in parent_menu_ids:
                attendance_submenus = Menu.query.filter(
                    Menu.path.like('/attendance/%'),
                    Menu.path != '/attendance'
                ).all()
                for menu in attendance_submenus:
                    if menu.parent_id != parent_menu_ids['/attendance']:
                        menu.parent_id = parent_menu_ids['/attendance']
                        logger.info(f"Updated parent_id for menu {menu.name} ({menu.path})")
            
            # Update parent_id for mobil submenus
            if '/mobil' in parent_menu_ids:
                mobil_submenus = Menu.query.filter(
                    Menu.path.like('/mobil/%'),
                    Menu.path != '/mobil'
                ).all()
                for menu in mobil_submenus:
                    if menu.parent_id != parent_menu_ids['/mobil']:
                        menu.parent_id = parent_menu_ids['/mobil']
                        logger.info(f"Updated parent_id for menu {menu.name} ({menu.path})")
            
            # Update parent_id for stok-barang submenus
            if '/stok-barang' in parent_menu_ids:
                stok_submenus = Menu.query.filter(
                    Menu.path.like('/stok-barang/%'),
                    Menu.path != '/stok-barang'
                ).all()
                for menu in stok_submenus:
                    if menu.parent_id != parent_menu_ids['/stok-barang']:
                        menu.parent_id = parent_menu_ids['/stok-barang']
                        logger.info(f"Updated parent_id for menu {menu.name} ({menu.path})")
            
            # Update parent_id for request-pembelian submenus
            if '/request-pembelian' in parent_menu_ids:
                request_submenus = Menu.query.filter(
                    Menu.path.like('/request-pembelian/%'),
                    Menu.path != '/request-pembelian'
                ).all()
                for menu in request_submenus:
                    if menu.parent_id != parent_menu_ids['/request-pembelian']:
                        menu.parent_id = parent_menu_ids['/request-pembelian']
                        logger.info(f"Updated parent_id for menu {menu.name} ({menu.path})")
            
            db.session.commit()
            logger.info("Fixed parent_id for all submenus")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error fixing menu parent_ids: {str(e)}")
            raise e

    @staticmethod
    def get_registry_definitions():
        """Return registry menu definitions without touching database."""
        try:
            return json.loads(json.dumps(DEFAULT_MENU_DEFINITIONS))
        except Exception:
            # Fallback shallow copy
            return list(DEFAULT_MENU_DEFINITIONS)
    
    @staticmethod
    def create_role_permission_template(role_id, template_name='default'):
        """Create default permissions for a role based on template"""
        try:
            role = Role.query.get(role_id)
            if not role:
                raise ValueError("Role tidak ditemukan")
            
            # Define permission templates
            templates = {
                'admin': {
                    'dashboard': {'read': True, 'create': True, 'update': True, 'delete': True},
                    'telegram-bot': {'read': True, 'create': True, 'update': True, 'delete': True},
                    'users': {'read': True, 'create': True, 'update': True, 'delete': True},
                    'roles': {'read': True, 'create': True, 'update': True, 'delete': True},
                    'approval-management': {'read': True, 'create': True, 'update': True, 'delete': True},
                    'notifications': {'read': True, 'create': True, 'update': True, 'delete': True},
                    'agent-status': {'read': True, 'create': True, 'update': True, 'delete': True},
                    'qdrant-knowledge-base': {'read': True, 'create': True, 'update': True, 'delete': True},
                    'remind-exp-docs': {'read': True, 'create': True, 'update': True, 'delete': True},
                    'attendance': {'read': True, 'create': True, 'update': True, 'delete': True},
                    'mobil': {'read': True, 'create': True, 'update': True, 'delete': True},
                    'stok-barang': {'read': True, 'create': True, 'update': True, 'delete': True},
                    'request-pembelian': {'read': True, 'create': True, 'update': True, 'delete': True}
                },
                'manager': {
                    'dashboard': {'read': True, 'create': False, 'update': False, 'delete': False},
                    'telegram-bot': {'read': True, 'create': False, 'update': False, 'delete': False},
                    'users': {'read': True, 'create': True, 'update': True, 'delete': False},
                    'roles': {'read': True, 'create': False, 'update': False, 'delete': False},
                    'approval-management': {'read': True, 'create': True, 'update': True, 'delete': False},
                    'notifications': {'read': True, 'create': True, 'update': True, 'delete': False},
                    'agent-status': {'read': True, 'create': False, 'update': False, 'delete': False},
                    'qdrant-knowledge-base': {'read': True, 'create': False, 'update': False, 'delete': False},
                    'remind-exp-docs': {'read': True, 'create': False, 'update': False, 'delete': False},
                    'attendance': {'read': True, 'create': True, 'update': True, 'delete': False},
                    'mobil': {'read': True, 'create': True, 'update': True, 'delete': False},
                    'stok-barang': {'read': True, 'create': True, 'update': True, 'delete': False},
                    'request-pembelian': {'read': True, 'create': True, 'update': True, 'delete': False}
                },
                'staff': {
                    'dashboard': {'read': True, 'create': False, 'update': False, 'delete': False},
                    'telegram-bot': {'read': False, 'create': False, 'update': False, 'delete': False},
                    'users': {'read': False, 'create': False, 'update': False, 'delete': False},
                    'roles': {'read': False, 'create': False, 'update': False, 'delete': False},
                    'approval-management': {'read': False, 'create': False, 'update': False, 'delete': False},
                    'notifications': {'read': True, 'create': False, 'update': False, 'delete': False},
                    'agent-status': {'read': False, 'create': False, 'update': False, 'delete': False},
                    'qdrant-knowledge-base': {'read': False, 'create': False, 'update': False, 'delete': False},
                    'remind-exp-docs': {'read': False, 'create': False, 'update': False, 'delete': False},
                    'attendance': {'read': True, 'create': True, 'update': True, 'delete': False},
                    'mobil': {'read': True, 'create': True, 'update': True, 'delete': False},
                    'stok-barang': {'read': True, 'create': True, 'update': True, 'delete': False},
                    'request-pembelian': {'read': True, 'create': True, 'update': True, 'delete': False}
                },
                'default': {
                    'dashboard': {'read': True, 'create': False, 'update': False, 'delete': False},
                    'notifications': {'read': True, 'create': False, 'update': False, 'delete': False}
                }
            }
            
            # Get template based on role name or use default
            template = templates.get(role.name.lower(), templates['default'])
            
            # Get all menus
            menus = Menu.query.filter_by(is_active=True).all()
            
            created_permissions = []
            for menu in menus:
                # Extract menu key from path
                menu_key = menu.path.strip('/').split('/')[0]
                if not menu_key:
                    menu_key = 'dashboard'
                
                # Get permissions for this menu
                menu_permissions = template.get(menu_key, {'read': False, 'create': False, 'update': False, 'delete': False})
                
                # Check if permission already exists
                existing_permission = MenuPermission.query.filter_by(
                    menu_id=menu.id,
                    role_id=role_id
                ).first()
                
                if existing_permission:
                    # Update existing permission
                    existing_permission.can_read = menu_permissions['read']
                    existing_permission.can_create = menu_permissions['create']
                    existing_permission.can_update = menu_permissions['update']
                    existing_permission.can_delete = menu_permissions['delete']
                    existing_permission.is_active = True
                    existing_permission.granted_at = datetime.utcnow()
                else:
                    # Create new permission
                    permission = MenuPermission(
                        menu_id=menu.id,
                        role_id=role_id,
                        can_read=menu_permissions['read'],
                        can_create=menu_permissions['create'],
                        can_update=menu_permissions['update'],
                        can_delete=menu_permissions['delete'],
                        granted_at=datetime.utcnow()
                    )
                    db.session.add(permission)
                    created_permissions.append(permission)
            
            db.session.commit()
            
            logger.info(f"Created {len(created_permissions)} permissions for role {role.name}")
            return created_permissions
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating role permission template: {str(e)}")
            raise e
    
    @staticmethod
    def check_user_permission(user_id, module, action, scope='own', resource_id=None):
        """Check if user has specific permission for module and action"""
        try:
            from domains.role.models.role_models import UserRole
            from models import User
            
            # Admin override berbasis assignment aktif, bukan legacy field
            from domains.role.models.role_models import Role as R, UserRole as UR
            active_admin = db.session.query(UR).join(R, R.id == UR.role_id) \
                .filter(UR.user_id == user_id, UR.is_active == True, R.is_active == True, R.name.ilike('admin')) \
                .first()
            if active_admin:
                return True
            
            # Get user roles
            user_roles = UserRole.query.filter_by(user_id=user_id, is_active=True).all()
            role_ids = [ur.role_id for ur in user_roles]
            
            if not role_ids:
                return False
            
            # For now, we'll implement a simple permission check
            # In a more complex system, this would check against specific permission tables
            
            # Check if user has any role that allows the action
            # This is a simplified implementation - in production you'd have a proper permission matrix
            if module in ['roles', 'permissions', 'departments'] and action in ['create', 'read', 'update', 'delete']:
                # For role management operations, check if user has management role
                from domains.role.models.role_models import Role
                management_roles = Role.query.filter(
                    Role.id.in_(role_ids),
                    Role.is_management == True,
                    Role.is_active == True
                ).all()
                
                if management_roles:
                    return True
            
            # Default: allow read operations for all authenticated users
            if action == 'read':
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking user permission: {str(e)}")
            return False
    
    @staticmethod
    def check_user_menu_permission(user_id, menu_path, action='read'):
        """Check if user has permission for specific menu and action"""
        try:
            from domains.role.models.role_models import UserRole
            
            # Get user roles
            user_roles = UserRole.query.filter_by(user_id=user_id, is_active=True).all()
            role_ids = [ur.role_id for ur in user_roles]
            
            if not role_ids:
                return False
            
            # Get menu
            menu = Menu.query.filter_by(path=menu_path, is_active=True).first()
            if not menu:
                return False
            
            # Check permission
            permission = MenuPermission.query.filter(
                MenuPermission.menu_id == menu.id,
                MenuPermission.role_id.in_(role_ids),
                MenuPermission.is_active == True
            ).first()
            
            if not permission:
                return False
            
            return permission.has_permission(action)
            
        except Exception as e:
            logger.error(f"Error checking user menu permission: {str(e)}")
            return False
    
    @staticmethod
    def get_user_accessible_menus(user_id):
        """Get all menus accessible by user"""
        try:
            from domains.role.models.role_models import UserRole
            from models import User
            
            logger.info(f"[get_user_accessible_menus] Starting for user_id: {user_id}")
            
            # Check if show_in_sidebar column exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('menu_permissions')]
            has_show_in_sidebar = 'show_in_sidebar' in columns
            logger.info(f"[get_user_accessible_menus] show_in_sidebar column exists: {has_show_in_sidebar}")
            
            # Get user roles (termasuk admin role jika ada)
            user_roles = UserRole.query.filter_by(user_id=user_id, is_active=True).all()
            role_ids = [ur.role_id for ur in user_roles]
            logger.info(f"[get_user_accessible_menus] User {user_id} has {len(user_roles)} active roles: {role_ids}")
            
            if not role_ids:
                logger.warning(f"[get_user_accessible_menus] User {user_id} has no active roles, returning empty menu list")
                return []
            
            # Semua user (termasuk admin) harus melihat menu berdasarkan role mereka sendiri
            # Admin tidak bypass - mereka juga harus mematuhi show_in_sidebar filter
            query = db.session.query(Menu).join(MenuPermission).filter(
                MenuPermission.role_id.in_(role_ids),
                MenuPermission.can_read == True,
                MenuPermission.is_active == True,
                Menu.is_active == True
            )
            
            # Filter by show_in_sidebar if column exists (berlaku untuk semua user termasuk admin)
            if has_show_in_sidebar:
                query = query.filter(MenuPermission.show_in_sidebar == True)
                logger.info(f"[get_user_accessible_menus] Applied show_in_sidebar=True filter")
            
            accessible_menus = query.order_by(Menu.order_index).all()
            
            logger.info(f"[get_user_accessible_menus] User {user_id} with roles {role_ids} has access to {len(accessible_menus)} menus (filtered by show_in_sidebar={has_show_in_sidebar})")
            
            if len(accessible_menus) == 0:
                logger.warning(f"[get_user_accessible_menus] No menus found for user {user_id}. Checking possible causes...")
                # Debug: Check total menus in database
                total_menus = Menu.query.filter_by(is_active=True).count()
                logger.info(f"[get_user_accessible_menus] Total active menus in database: {total_menus}")
                # Debug: Check permissions for this user's roles
                total_permissions = MenuPermission.query.filter(
                    MenuPermission.role_id.in_(role_ids),
                    MenuPermission.is_active == True
                ).count()
                logger.info(f"[get_user_accessible_menus] Total permissions for roles {role_ids}: {total_permissions}")
                # Debug: Check permissions with can_read=True
                read_permissions = MenuPermission.query.filter(
                    MenuPermission.role_id.in_(role_ids),
                    MenuPermission.can_read == True,
                    MenuPermission.is_active == True
                ).count()
                logger.info(f"[get_user_accessible_menus] Permissions with can_read=True: {read_permissions}")
                if has_show_in_sidebar:
                    sidebar_permissions = MenuPermission.query.filter(
                        MenuPermission.role_id.in_(role_ids),
                        MenuPermission.can_read == True,
                        MenuPermission.is_active == True,
                        MenuPermission.show_in_sidebar == True
                    ).count()
                    logger.info(f"[get_user_accessible_menus] Permissions with show_in_sidebar=True: {sidebar_permissions}")
            
            # Build hierarchical structure
            menu_dict = {}
            root_menus = []
            
            for menu in accessible_menus:
                menu_dict[menu.id] = menu.to_dict()
                menu_dict[menu.id]['sub_menus'] = []
            
            for menu in accessible_menus:
                if menu.parent_id and menu.parent_id in menu_dict:
                    menu_dict[menu.parent_id]['sub_menus'].append(menu_dict[menu.id])
                else:
                    root_menus.append(menu_dict[menu.id])
            
            logger.info(f"[get_user_accessible_menus] User {user_id} has access to {len(root_menus)} root menus")
            if root_menus:
                logger.info(f"[get_user_accessible_menus] Root menu names: {[m.get('name') for m in root_menus]}")
            
            return root_menus
            
        except Exception as e:
            logger.error(f"[get_user_accessible_menus] Error getting user accessible menus for user {user_id}: {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    def bulk_update_permissions(role_id, permission_updates, current_user_id):
        """Bulk update permissions for a role"""
        try:
            role = Role.query.get(role_id)
            if not role:
                raise ValueError("Role tidak ditemukan")
            
            updated_count = 0
            
            for update_data in permission_updates:
                menu_id = update_data.get('menu_id')
                if not menu_id:
                    continue
                
                # Get or create permission
                permission = MenuPermission.query.filter_by(
                    menu_id=menu_id,
                    role_id=role_id
                ).first()
                
                if not permission:
                    permission = MenuPermission(
                        menu_id=menu_id,
                        role_id=role_id,
                        granted_by=current_user_id
                    )
                    db.session.add(permission)
                
                # Update permissions
                permission.can_read = update_data.get('can_read', False)
                permission.can_create = update_data.get('can_create', False)
                permission.can_update = update_data.get('can_update', False)
                permission.can_delete = update_data.get('can_delete', False)
                permission.granted_at = datetime.utcnow()
                permission.is_active = True
                
                updated_count += 1
            
            db.session.commit()
            
            logger.info(f"Bulk updated {updated_count} permissions for role {role.name}")
            return updated_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error bulk updating permissions: {str(e)}")
            raise e
    
    @staticmethod
    def get_permission_statistics():
        """Get permission statistics for dashboard"""
        try:
            stats = {
                'total_menus': Menu.query.filter_by(is_active=True).count(),
                'total_roles': Role.query.filter_by(is_active=True).count(),
                'total_permissions': MenuPermission.query.filter_by(is_active=True).count(),
                'recent_audit_logs': PermissionAuditLog.query.order_by(
                    PermissionAuditLog.created_at.desc()
                ).limit(10).all()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting permission statistics: {str(e)}")
            return None
    
    @staticmethod
    def initialize_default_permissions():
        """Initialize default permissions and menus for the system"""
        try:
            logger.info("[INIT] Initializing default permissions...")
            
            # Create default menus
            created_menus = PermissionService.create_default_menus()
            logger.info(f"[SUCCESS] Created {len(created_menus)} default menus")
            
            # Create default roles if they don't exist
            from domains.role.models.role_models import Role, Department
            
            default_roles = [
                {
                    'name': 'Admin',
                    'code': 'ADMIN',
                    'description': 'Administrator dengan akses penuh',
                    'level': 1,
                    'is_management': True,
                    'is_active': True
                },
                {
                    'name': 'Manager',
                    'code': 'MANAGER',
                    'description': 'Manager dengan akses terbatas',
                    'level': 2,
                    'is_management': True,
                    'is_active': True
                },
                {
                    'name': 'Staff',
                    'code': 'STAFF',
                    'description': 'Staff dengan akses dasar',
                    'level': 3,
                    'is_management': False,
                    'is_active': True
                }
            ]
            
            created_roles = []
            for role_data in default_roles:
                existing_role = Role.query.filter_by(name=role_data['name']).first()
                if not existing_role:
                    role = Role(**role_data)
                    db.session.add(role)
                    db.session.flush()  # Get the ID
                    created_roles.append(role)
                    logger.info(f"[SUCCESS] Created role: {role.name}")
                else:
                    created_roles.append(existing_role)
                    logger.info(f"[INFO] Role {role_data['name']} already exists")
            
            db.session.commit()
            
            # Create default permissions for each role
            for role in created_roles:
                try:
                    created_permissions = PermissionService.create_role_permission_template(role.id)
                    logger.info(f"[SUCCESS] Created permissions for role: {role.name}")
                except Exception as perm_error:
                    logger.warning(f"[WARNING] Could not create permissions for role {role.name}: {perm_error}")
            
            logger.info("[SUCCESS] Default permissions initialization completed")
            return {
                'menus_created': len(created_menus),
                'roles_created': len([r for r in created_roles if r.id]),
                'status': 'success'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"[ERROR] Error initializing default permissions: {str(e)}")
            raise e

# Export singleton instance
permission_service = PermissionService()