#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Permission Management Controller
Controller untuk manajemen permissions dengan CRUD operations yang komprehensif
"""

from flask import request, jsonify
from datetime import datetime
from config.database import db
from models.menu_models import Menu, MenuPermission, PermissionAuditLog
from models.role_management import Role
from utils.logger import get_logger
from utils.validators import validate_request_data
import json

logger = get_logger(__name__)


class PermissionController:
    """Controller untuk manajemen permissions"""
    
    @staticmethod
    def get_menus():
        """Get all menus with hierarchical structure"""
        try:
            menus = Menu.get_menu_tree()
            return jsonify({
                'success': True,
                'data': menus,
                'message': 'Menu berhasil diambil'
            }), 200
        except Exception as e:
            logger.error(f"Error getting menus: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Gagal mengambil data menu'
            }), 500
    
    @staticmethod
    def get_menu_permissions(role_id):
        """Get permissions for specific role"""
        try:
            # Get all menus
            menus = Menu.query.filter_by(is_active=True).order_by(Menu.order_index).all()
            
            # Get existing permissions for this role
            existing_permissions = MenuPermission.query.filter_by(
                role_id=role_id, 
                is_active=True
            ).all()
            
            # Create permission map
            permission_map = {}
            for perm in existing_permissions:
                permission_map[perm.menu_id] = {
                    'can_read': perm.can_read,
                    'can_create': perm.can_create,
                    'can_update': perm.can_update,
                    'can_delete': perm.can_delete
                }
            
            # Build response with all menus and their permissions
            menu_permissions = []
            for menu in menus:
                menu_data = {
                    'menu_id': menu.id,
                    'menu_name': menu.name,
                    'menu_path': menu.path,
                    'menu_icon': menu.icon,
                    'parent_id': menu.parent_id,
                    'order_index': menu.order_index,
                    'permissions': permission_map.get(menu.id, {
                        'can_read': False,
                        'can_create': False,
                        'can_update': False,
                        'can_delete': False
                    })
                }
                menu_permissions.append(menu_data)
            
            return jsonify({
                'success': True,
                'data': menu_permissions,
                'message': 'Permission berhasil diambil'
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting menu permissions: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Gagal mengambil data permission'
            }), 500

    @staticmethod
    def get_level_templates():
        """List semua template level role"""
        try:
            from models.menu_models import RoleLevelTemplate
            templates = RoleLevelTemplate.query.filter_by(is_active=True).order_by(RoleLevelTemplate.level).all()
            return jsonify({
                'success': True,
                'data': [t.to_dict() for t in templates],
                'message': 'Role level templates berhasil diambil'
            }), 200
        except Exception as e:
            logger.error(f"Error getting role level templates: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Gagal mengambil role level templates'
            }), 500

    @staticmethod
    def get_level_template(level: int):
        """Ambil detail template untuk level tertentu"""
        try:
            from models.menu_models import RoleLevelTemplate
            tpl = RoleLevelTemplate.query.filter_by(level=level, is_active=True).first()
            if not tpl:
                return jsonify({
                    'success': True,
                    'data': None,
                    'message': 'Template level tidak ditemukan'
                }), 200
            
            # Filter permissions untuk hanya menampilkan menu yang aktif
            if tpl.permissions and isinstance(tpl.permissions, list):
                active_menu_ids = {m.id for m in Menu.query.filter_by(is_active=True).all()}
                filtered_permissions = [
                    p for p in tpl.permissions 
                    if isinstance(p, dict) and p.get('menu_id') in active_menu_ids
                ]
                tpl_dict = tpl.to_dict()
                tpl_dict['permissions'] = filtered_permissions
            else:
                tpl_dict = tpl.to_dict()
            
            return jsonify({
                'success': True,
                'data': tpl_dict,
                'message': 'Template level berhasil diambil'
            }), 200
        except Exception as e:
            logger.error(f"Error getting role level template: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Gagal mengambil template level'
            }), 500

    @staticmethod
    def upsert_level_template(level: int, payload: dict, current_user_id: int):
        """Buat atau update template level role"""
        try:
            from models.menu_models import RoleLevelTemplate
            name = payload.get('name')
            permissions = payload.get('permissions', [])
            if not isinstance(level, int) or level < 1:
                return jsonify({'success': False, 'error': 'Level tidak valid'}), 400
            if not isinstance(permissions, list):
                return jsonify({'success': False, 'error': 'Format permissions harus array'}), 400
            
            # Filter permissions untuk hanya menyimpan menu yang aktif
            active_menu_ids = {m.id for m in Menu.query.filter_by(is_active=True).all()}
            filtered_permissions = [
                p for p in permissions 
                if isinstance(p, dict) and p.get('menu_id') in active_menu_ids
            ]
            
            tpl = RoleLevelTemplate.query.filter_by(level=level).first()
            if tpl:
                tpl.name = name
                tpl.permissions = filtered_permissions
                tpl.is_active = True
                tpl.updated_at = datetime.utcnow()
            else:
                tpl = RoleLevelTemplate(
                    level=level,
                    name=name,
                    permissions=filtered_permissions,
                    created_by=current_user_id
                )
                db.session.add(tpl)
            db.session.commit()
            return jsonify({'success': True, 'data': tpl.to_dict(), 'message': 'Template level tersimpan'}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error upserting role level template: {str(e)}")
            return jsonify({'success': False, 'error': f'Gagal menyimpan template level'}), 500
    
    @staticmethod
    def update_role_permissions():
        """Update permissions for a role"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['role_id', 'permissions']
            if not validate_request_data(data, required_fields):
                return jsonify({
                    'success': False,
                    'error': 'Field role_id dan permissions diperlukan'
                }), 400
            
            role_id = data['role_id']
            permissions = data['permissions']
            current_user_id = getattr(request, 'current_user_id', None)
            
            # Check if role exists
            role = Role.query.get(role_id)
            if not role:
                return jsonify({
                    'success': False,
                    'error': 'Role tidak ditemukan'
                }), 404
            
            # Get current permissions for audit
            current_permissions = MenuPermission.query.filter_by(
                role_id=role_id, 
                is_active=True
            ).all()
            
            current_permission_map = {}
            for perm in current_permissions:
                current_permission_map[perm.menu_id] = {
                    'can_read': perm.can_read,
                    'can_create': perm.can_create,
                    'can_update': perm.can_update,
                    'can_delete': perm.can_delete
                }
            
            # Process each permission
            updated_permissions = []
            for permission_data in permissions:
                menu_id = permission_data.get('menu_id')
                if not menu_id:
                    continue
                
                # Check if menu exists
                menu = Menu.query.get(menu_id)
                if not menu:
                    continue
                
                # Get or create MenuPermission
                menu_permission = MenuPermission.query.filter_by(
                    menu_id=menu_id,
                    role_id=role_id
                ).first()
                
                if not menu_permission:
                    menu_permission = MenuPermission(
                        menu_id=menu_id,
                        role_id=role_id,
                        granted_by=current_user_id
                    )
                    db.session.add(menu_permission)
                
                # Update permissions
                old_values = {
                    'can_read': menu_permission.can_read,
                    'can_create': menu_permission.can_create,
                    'can_update': menu_permission.can_update,
                    'can_delete': menu_permission.can_delete
                }
                
                # Handle both old and new data structures
                permissions_obj = permission_data.get('permissions', permission_data)
                menu_permission.can_read = permissions_obj.get('can_read', False)
                menu_permission.can_create = permissions_obj.get('can_create', False)
                menu_permission.can_update = permissions_obj.get('can_update', False)
                menu_permission.can_delete = permissions_obj.get('can_delete', False)
                # Handle show_in_sidebar if provided
                if 'show_in_sidebar' in permissions_obj:
                    menu_permission.show_in_sidebar = permissions_obj.get('show_in_sidebar', True)
                menu_permission.granted_at = datetime.utcnow()
                menu_permission.is_active = True

                # Ensure the menu_permission has an ID before creating audit log
                # This will assign a primary key if it's a new object
                db.session.flush()
                
                # Create audit log
                new_values = {
                    'can_read': menu_permission.can_read,
                    'can_create': menu_permission.can_create,
                    'can_update': menu_permission.can_update,
                    'can_delete': menu_permission.can_delete
                }
                
                audit_log = PermissionAuditLog(
                    user_id=current_user_id,
                    action='update',
                    resource_type='menu_permission',
                    resource_id=menu_permission.id,
                    old_values=old_values,
                    new_values=new_values,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit_log)
                
                updated_permissions.append(menu_permission)
            
            # Commit changes
            db.session.commit()
            
            logger.info(f"Updated permissions for role {role_id} by user {current_user_id}")
            
            return jsonify({
                'success': True,
                'data': {
                    'role_id': role_id,
                    'updated_permissions': len(updated_permissions)
                },
                'message': f'Permission berhasil diperbarui untuk {len(updated_permissions)} menu'
            }), 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating role permissions: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Gagal memperbarui permission'
            }), 500
    
    @staticmethod
    def copy_permissions():
        """Copy permissions from one role to another"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['source_role_id', 'target_role_id']
            if not validate_request_data(data, required_fields):
                return jsonify({
                    'success': False,
                    'error': 'Field source_role_id dan target_role_id diperlukan'
                }), 400
            
            source_role_id = data['source_role_id']
            target_role_id = data['target_role_id']
            current_user_id = getattr(request, 'current_user_id', None)
            
            # Check if both roles exist
            source_role = Role.query.get(source_role_id)
            target_role = Role.query.get(target_role_id)
            
            if not source_role or not target_role:
                return jsonify({
                    'success': False,
                    'error': 'Role tidak ditemukan'
                }), 404
            
            # Get source permissions
            source_permissions = MenuPermission.query.filter_by(
                role_id=source_role_id,
                is_active=True
            ).all()
            
            if not source_permissions:
                return jsonify({
                    'success': False,
                    'error': 'Tidak ada permission untuk dicopy'
                }), 400
            
            # Clear existing target permissions
            MenuPermission.query.filter_by(
                role_id=target_role_id,
                is_active=True
            ).update({'is_active': False})
            
            # Copy permissions
            copied_count = 0
            for source_perm in source_permissions:
                # Check if target permission already exists
                target_perm = MenuPermission.query.filter_by(
                    menu_id=source_perm.menu_id,
                    role_id=target_role_id
                ).first()
                
                if not target_perm:
                    target_perm = MenuPermission(
                        menu_id=source_perm.menu_id,
                        role_id=target_role_id,
                        granted_by=current_user_id
                    )
                    db.session.add(target_perm)
                
                # Copy permission values
                target_perm.can_read = source_perm.can_read
                target_perm.can_create = source_perm.can_create
                target_perm.can_update = source_perm.can_update
                target_perm.can_delete = source_perm.can_delete
                target_perm.granted_at = datetime.utcnow()
                target_perm.is_active = True
                
                # Create audit log
                audit_log = PermissionAuditLog(
                    user_id=current_user_id,
                    action='copy',
                    resource_type='menu_permission',
                    resource_id=target_perm.id,
                    old_values=None,
                    new_values={
                        'can_read': target_perm.can_read,
                        'can_create': target_perm.can_create,
                        'can_update': target_perm.can_update,
                        'can_delete': target_perm.can_delete,
                        'copied_from_role_id': source_role_id
                    },
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit_log)
                
                copied_count += 1
            
            # Commit changes
            db.session.commit()
            
            logger.info(f"Copied {copied_count} permissions from role {source_role_id} to {target_role_id} by user {current_user_id}")
            
            return jsonify({
                'success': True,
                'data': {
                    'source_role_id': source_role_id,
                    'target_role_id': target_role_id,
                    'copied_permissions': copied_count
                },
                'message': f'Permission berhasil dicopy dari {source_role.name} ke {target_role.name}'
            }), 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error copying permissions: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Gagal menyalin permission'
            }), 500
    
    @staticmethod
    def get_permission_audit_logs():
        """Get permission audit logs"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            role_id = request.args.get('role_id', type=int)
            
            query = PermissionAuditLog.query
            
            if role_id:
                # Filter by role through menu_permissions
                query = query.join(MenuPermission).filter(MenuPermission.role_id == role_id)
            
            query = query.order_by(PermissionAuditLog.created_at.desc())
            
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            audit_logs = []
            for log in pagination.items:
                audit_logs.append(log.to_dict())
            
            return jsonify({
                'success': True,
                'data': audit_logs,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                },
                'message': 'Audit log berhasil diambil'
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Gagal mengambil audit log'
            }), 500
    
    @staticmethod
    def check_user_permission():
        """Check if current user has permission for specific menu and action"""
        try:
            menu_path = request.args.get('menu_path')
            action = request.args.get('action', 'read')
            current_user_id = getattr(request, 'current_user_id', None)
            
            if not menu_path or not current_user_id:
                return jsonify({
                    'success': False,
                    'error': 'Menu path dan user ID diperlukan'
                }), 400
            
            # Get menu
            menu = Menu.query.filter_by(path=menu_path, is_active=True).first()
            if not menu:
                return jsonify({
                    'success': False,
                    'error': 'Menu tidak ditemukan'
                }), 404
            
            # Check user permission through roles
            from models.role_management import UserRole
            
            user_roles = UserRole.query.filter_by(user_id=current_user_id).all()
            role_ids = [ur.role_id for ur in user_roles]
            
            if not role_ids:
                return jsonify({
                    'success': True,
                    'data': {'has_permission': False},
                    'message': 'User tidak memiliki role'
                }), 200
            
            # Check permission
            permission = MenuPermission.query.filter(
                MenuPermission.menu_id == menu.id,
                MenuPermission.role_id.in_(role_ids),
                MenuPermission.is_active == True
            ).first()
            
            has_permission = False
            if permission:
                has_permission = permission.has_permission(action)
            
            return jsonify({
                'success': True,
                'data': {
                    'has_permission': has_permission,
                    'menu_path': menu_path,
                    'action': action
                },
                'message': 'Permission check berhasil'
            }), 200
            
        except Exception as e:
            logger.error(f"Error checking user permission: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Gagal mengecek permission'
            }), 500

    @staticmethod
    def apply_level_template_to_role(role_id: int, payload: dict, current_user_id: int):
        """Terapkan Role Level Template ke menu permissions sebuah role.
        Jika payload mengandung 'level', gunakan itu; jika tidak, gunakan role.level.
        Lakukan upsert ke tabel MenuPermission tanpa menghapus data role lainnya.
        """
        try:
            from models.menu_models import RoleLevelTemplate

            # Validasi role
            role = Role.query.get(role_id)
            if not role:
                return jsonify({'success': False, 'error': 'Role tidak ditemukan'}), 404

            # Tentukan level target
            target_level = payload.get('level') if isinstance(payload, dict) else None
            if not isinstance(target_level, int):
                target_level = role.level
            if not isinstance(target_level, int) or target_level < 1:
                return jsonify({'success': False, 'error': 'Level tidak valid'}), 400

            # Ambil template level
            tpl = RoleLevelTemplate.query.filter_by(level=target_level, is_active=True).first()
            # Ambil semua menu aktif
            menus = Menu.query.filter_by(is_active=True).order_by(Menu.order_index).all()
            if not menus:
                return jsonify({'success': False, 'error': 'Tidak ada menu aktif untuk diterapkan'}), 400

            template_map = {}
            if tpl and tpl.permissions:
                for item in tpl.permissions:
                    if not isinstance(item, dict):
                        continue
                    menu_id = item.get('menu_id')
                    if not menu_id:
                        continue
                    template_map[menu_id] = item.get('permissions', {}) or {}

            # Fallback default permissions jika template tidak mencakup menu tertentu
            # Untuk konsistensi dengan halaman level template, defaultnya adalah tidak ada akses.
            # Admin dapat memberikan akses penuh melalui template level 1 jika diperlukan.
            fallback_permissions = {
                'can_read': False,
                'can_create': False,
                'can_update': False,
                'can_delete': False,
                'show_in_sidebar': True  # Default true untuk visibility
            }

            updated_count = 0
            granted_menus = 0

            for menu in menus:
                source_permissions = template_map.get(menu.id, {})
                normalized_permissions = {
                    'can_read': bool(source_permissions.get('can_read', fallback_permissions['can_read'])),
                    'can_create': bool(source_permissions.get('can_create', fallback_permissions['can_create'])),
                    'can_update': bool(source_permissions.get('can_update', fallback_permissions['can_update'])),
                    'can_delete': bool(source_permissions.get('can_delete', fallback_permissions['can_delete'])),
                    'show_in_sidebar': source_permissions.get('show_in_sidebar', fallback_permissions['show_in_sidebar']) if 'show_in_sidebar' in source_permissions else fallback_permissions['show_in_sidebar']
                }

                # Upsert MenuPermission
                mp = MenuPermission.query.filter_by(menu_id=menu.id, role_id=role_id).first()
                if not mp:
                    mp = MenuPermission(menu_id=menu.id, role_id=role_id, granted_by=current_user_id)
                    db.session.add(mp)

                old_values = {
                    'can_read': mp.can_read,
                    'can_create': mp.can_create,
                    'can_update': mp.can_update,
                    'can_delete': mp.can_delete,
                    'show_in_sidebar': getattr(mp, 'show_in_sidebar', True)
                }

                mp.can_read = normalized_permissions['can_read']
                mp.can_create = normalized_permissions['can_create']
                mp.can_update = normalized_permissions['can_update']
                mp.can_delete = normalized_permissions['can_delete']
                # Handle show_in_sidebar if column exists
                if hasattr(mp, 'show_in_sidebar'):
                    mp.show_in_sidebar = normalized_permissions['show_in_sidebar']
                mp.granted_at = datetime.utcnow()
                mp.is_active = True

                db.session.flush()

                new_values = {
                    'can_read': mp.can_read,
                    'can_create': mp.can_create,
                    'can_update': mp.can_update,
                    'can_delete': mp.can_delete,
                    'show_in_sidebar': getattr(mp, 'show_in_sidebar', True),
                    'applied_level': target_level
                }

                audit_log = PermissionAuditLog(
                    user_id=current_user_id,
                    action='apply_template',
                    resource_type='menu_permission',
                    resource_id=mp.id,
                    old_values=old_values,
                    new_values=new_values,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit_log)

                updated_count += 1
                if mp.can_read or mp.can_create or mp.can_update or mp.can_delete:
                    granted_menus += 1

            db.session.commit()

            return jsonify({
                'success': True,
                'data': {
                    'role_id': role_id,
                    'level': target_level,
                    'updated_permissions': updated_count,
                    'granted_menus': granted_menus,
                    'total_menus': len(menus)
                },
                'message': f'Template level {target_level} berhasil diterapkan ke role {role.name}'
            }), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error applying level template to role {role_id}: {str(e)}")
            return jsonify({'success': False, 'error': 'Gagal menerapkan template level ke role'}), 500

    @staticmethod
    def update_menu_sidebar_visibility_global(menu_id: int):
        """Update show_in_sidebar untuk semua MenuPermission dengan menu_id tertentu (global untuk semua role)"""
        try:
            from sqlalchemy import inspect
            
            current_user = getattr(request, 'current_user', None)
            if not current_user:
                return jsonify({
                    'success': False,
                    'error': 'User tidak ditemukan'
                }), 400
            
            data = request.get_json()
            show_in_sidebar = data.get('show_in_sidebar', True)
            
            # Check if menu exists
            menu = Menu.query.get(menu_id)
            if not menu:
                return jsonify({
                    'success': False,
                    'error': 'Menu tidak ditemukan'
                }), 404
            
            # Check if show_in_sidebar column exists
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('menu_permissions')]
            has_show_in_sidebar = 'show_in_sidebar' in columns
            
            if not has_show_in_sidebar:
                return jsonify({
                    'success': False,
                    'error': 'Kolom show_in_sidebar belum ada di database. Silakan jalankan migration terlebih dahulu.'
                }), 400
            
            # Get all MenuPermissions for this menu
            menu_permissions = MenuPermission.query.filter_by(
                menu_id=menu_id,
                is_active=True
            ).all()
            
            if not menu_permissions:
                return jsonify({
                    'success': False,
                    'error': 'Tidak ada permission untuk menu ini. Silakan set permission terlebih dahulu.'
                }), 400
            
            # Update all MenuPermissions
            updated_count = 0
            for menu_permission in menu_permissions:
                menu_permission.show_in_sidebar = show_in_sidebar
                menu_permission.granted_at = datetime.utcnow()
                updated_count += 1
            
            db.session.commit()
            
            logger.info(f"Updated global sidebar visibility for menu {menu_id} to {show_in_sidebar} by user {current_user.id}. Updated {updated_count} permissions.")
            
            return jsonify({
                'success': True,
                'data': {
                    'menu_id': menu_id,
                    'menu_name': menu.name,
                    'show_in_sidebar': show_in_sidebar,
                    'updated_permissions': updated_count
                },
                'message': f'Visibility sidebar berhasil diperbarui untuk {updated_count} role'
            }), 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating global menu sidebar visibility: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Gagal memperbarui visibility sidebar global'
            }), 500