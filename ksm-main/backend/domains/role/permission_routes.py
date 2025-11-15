#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Permission Management Routes
API routes untuk permission management dengan comprehensive endpoints
"""

from flask import Blueprint, request, jsonify
from domains.role.controllers.permission_controller import PermissionController
from domains.role.services.permission_service import PermissionService
from shared.middlewares.api_auth import jwt_required_custom
from shared.middlewares.role_auth import require_admin, require_manager
from shared.utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

# Create blueprint
permission_bp = Blueprint('permission_management', __name__)


@permission_bp.route('/menus', methods=['GET'])
@jwt_required_custom
def get_menus():
    """Get all menus with hierarchical structure"""
    return PermissionController.get_menus()


@permission_bp.route('/menus/visibility-matrix', methods=['GET'])
@jwt_required_custom
@require_admin()
def get_menu_visibility_matrix():
    """Get menu visibility matrix (show_in_sidebar) for all roles"""
    try:
        from domains.role.models.menu_models import Menu, MenuPermission
        from domains.role.models.role_models import Role
        from config.database import db
        
        # Get all active menus
        menus = Menu.query.filter_by(is_active=True).order_by(Menu.order_index).all()
        
        # Get all active roles
        roles = Role.query.filter_by(is_active=True).order_by(Role.level, Role.name).all()
        
        # Check if show_in_sidebar column exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('menu_permissions')]
        has_show_in_sidebar = 'show_in_sidebar' in columns
        
        # Get all menu permissions
        menu_permissions = MenuPermission.query.filter_by(is_active=True).all()
        
        # Create permission map: {menu_id: {role_id: {show_in_sidebar: bool}}}
        permission_map: dict = {}
        for perm in menu_permissions:
            if perm.menu_id not in permission_map:
                permission_map[perm.menu_id] = {}
            permission_map[perm.menu_id][perm.role_id] = {
                'show_in_sidebar': getattr(perm, 'show_in_sidebar', True) if has_show_in_sidebar else True
            }
        
        # Build response
        menus_data = []
        for menu in menus:
            menu_data = {
                'menu_id': menu.id,
                'menu_name': menu.name,
                'menu_path': menu.path,
                'menu_icon': menu.icon,
                'parent_id': menu.parent_id,
                'order_index': menu.order_index,
                'roles_visibility': {}
            }
            
            # Add visibility for each role
            for role in roles:
                menu_data['roles_visibility'][role.id] = {
                    'role_id': role.id,
                    'role_name': role.name,
                    'show_in_sidebar': permission_map.get(menu.id, {}).get(role.id, {}).get('show_in_sidebar', True)
                }
            
            menus_data.append(menu_data)
        
        return jsonify({
            'success': True,
            'data': {
                'menus': menus_data,
                'roles': [{'id': r.id, 'name': r.name, 'level': r.level} for r in roles]
            },
            'message': 'Menu visibility matrix berhasil diambil'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting menu visibility matrix: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Gagal mengambil menu visibility matrix'
        }), 500


@permission_bp.route('/menus/registry', methods=['GET'])
@jwt_required_custom
@require_admin()
def get_menu_registry():
    """Get menu registry definitions (single source of truth) without DB mutation"""
    try:
        defs = PermissionService.get_registry_definitions()
        return jsonify({
            'success': True,
            'data': defs,
            'message': 'Menu registry berhasil diambil'
        }), 200
    except Exception as e:
        logger.error(f"Error getting menu registry: {str(e)}")
        return jsonify({'success': False, 'error': 'Gagal mengambil menu registry'}), 500


@permission_bp.route('/menus/init', methods=['POST'])
@jwt_required_custom
@require_admin()
def init_default_menus():
    """Initialize default system menus"""
    try:
        menus = PermissionService.create_default_menus()
        return jsonify({
            'success': True,
            'data': [menu.to_dict() for menu in menus],
            'message': f'Berhasil membuat {len(menus)} menu default'
        }), 200
    except Exception as e:
        logger.error(f"Error initializing default menus: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Gagal membuat menu default'
        }), 500


@permission_bp.route('/menus/fix-parent-ids', methods=['POST'])
@jwt_required_custom
@require_admin()
def fix_menu_parent_ids():
    """Fix parent_id untuk menu yang sudah ada di database"""
    try:
        PermissionService.fix_menu_parent_ids()
        return jsonify({
            'success': True,
            'message': 'Parent ID menu berhasil diperbaiki'
        }), 200
    except Exception as e:
        logger.error(f"Error fixing menu parent_ids: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Gagal memperbaiki parent ID menu'
        }), 500


@permission_bp.route('/roles/<int:role_id>/permissions', methods=['GET'])
@jwt_required_custom
@require_admin()
def get_role_permissions(role_id):
    """Get permissions for specific role"""
    return PermissionController.get_menu_permissions(role_id)


@permission_bp.route('/roles/<int:role_id>/permissions', methods=['PUT'])
@jwt_required_custom
@require_admin()
def update_role_permissions(role_id):
    """Update permissions for a role"""
    return PermissionController.update_role_permissions()


@permission_bp.route('/roles/<int:role_id>/permissions/template', methods=['POST'])
@jwt_required_custom
@require_admin()
def create_role_permission_template(role_id):
    """Create default permissions for a role based on template"""
    try:
        data = request.get_json()
        template_name = data.get('template_name', 'default')
        
        permissions = PermissionService.create_role_permission_template(role_id, template_name)
        
        return jsonify({
            'success': True,
            'data': {
                'role_id': role_id,
                'template_name': template_name,
                'created_permissions': len(permissions)
            },
            'message': f'Template permission berhasil dibuat untuk role'
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating role permission template: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Gagal membuat template permission'
        }), 500


@permission_bp.route('/roles/copy-permissions', methods=['POST'])
@jwt_required_custom
@require_admin()
def copy_permissions():
    """Copy permissions from one role to another"""
    return PermissionController.copy_permissions()


@permission_bp.route('/menu-permissions/<int:menu_id>/<int:role_id>/show-in-sidebar', methods=['PUT'])
@jwt_required_custom
@require_admin()
def update_menu_sidebar_visibility(menu_id, role_id):
    """Update show_in_sidebar for a specific menu-role combination"""
    try:
        from domains.role.models.menu_models import MenuPermission
        from config.database import db
        
        current_user = getattr(request, 'current_user', None)
        if not current_user:
            return jsonify({
                'success': False,
                'error': 'User tidak ditemukan'
            }), 400
        
        data = request.get_json()
        show_in_sidebar = data.get('show_in_sidebar', True)
        
        # Check if show_in_sidebar column exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('menu_permissions')]
        has_show_in_sidebar = 'show_in_sidebar' in columns
        
        if not has_show_in_sidebar:
            return jsonify({
                'success': False,
                'error': 'Kolom show_in_sidebar belum ada di database. Silakan jalankan migration terlebih dahulu.'
            }), 400
        
        # Get or create menu permission
        menu_permission = MenuPermission.query.filter_by(
            menu_id=menu_id,
            role_id=role_id
        ).first()
        
        if not menu_permission:
            # Create new permission if doesn't exist
            menu_permission = MenuPermission(
                menu_id=menu_id,
                role_id=role_id,
                granted_by=current_user.id,
                show_in_sidebar=show_in_sidebar
            )
            db.session.add(menu_permission)
        else:
            menu_permission.show_in_sidebar = show_in_sidebar
            menu_permission.granted_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': menu_permission.to_dict(),
            'message': 'Visibility sidebar berhasil diperbarui'
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating menu sidebar visibility: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Gagal memperbarui visibility sidebar'
        }), 500


@permission_bp.route('/menus/<int:menu_id>/show-in-sidebar-global', methods=['PUT'])
@jwt_required_custom
@require_admin()
def update_menu_sidebar_visibility_global(menu_id):
    """Update show_in_sidebar untuk semua role yang memiliki permission ke menu ini (global)"""
    return PermissionController.update_menu_sidebar_visibility_global(menu_id)


@permission_bp.route('/roles/<int:role_id>/permissions/bulk', methods=['PUT'])
@jwt_required_custom
@require_admin()
def bulk_update_permissions(role_id):
    """Bulk update permissions for a role"""
    try:
        data = request.get_json()
        permission_updates = data.get('permissions', [])
        current_user_id = getattr(request, 'current_user_id', None)
        
        if not permission_updates:
            return jsonify({
                'success': False,
                'error': 'Data permissions diperlukan'
            }), 400
        
        updated_count = PermissionService.bulk_update_permissions(
            role_id, permission_updates, current_user_id
        )
        
        return jsonify({
            'success': True,
            'data': {
                'role_id': role_id,
                'updated_permissions': updated_count
            },
            'message': f'Berhasil memperbarui {updated_count} permissions'
        }), 200
        
    except Exception as e:
        logger.error(f"Error bulk updating permissions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Gagal memperbarui permissions'
        }), 500


@permission_bp.route('/check-permission', methods=['GET'])
@jwt_required_custom
def check_user_permission():
    """Check if current user has permission for specific menu and action"""
    return PermissionController.check_user_permission()


@permission_bp.route('/user-menus', methods=['GET', 'OPTIONS'])
@jwt_required_custom
def get_user_accessible_menus():
    """Get all menus accessible by current user"""
    # Handle preflight CORS (akan ditangani oleh jwt_required_custom decorator)
    # Tapi kita tetap handle di sini untuk memastikan
    if request.method == 'OPTIONS':
        from flask import make_response
        response = make_response('', 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, x-api-key, X-API-Key, Cache-Control, Accept, Origin, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
    try:
        current_user = getattr(request, 'current_user', None)
        
        if not current_user:
            logger.warning("[get_user_accessible_menus] Current user not found in request")
            return jsonify({
                'success': False,
                'error': 'User tidak ditemukan'
            }), 400
        
        logger.info(f"[get_user_accessible_menus] Request from user_id: {current_user.id}, username: {getattr(current_user, 'username', 'Unknown')}")
        
        menus = PermissionService.get_user_accessible_menus(current_user.id)
        
        logger.info(f"[get_user_accessible_menus] Returning {len(menus)} menus for user {current_user.id}")
        if menus:
            logger.info(f"[get_user_accessible_menus] Menu names: {[m.get('name') for m in menus[:5]]}")
        else:
            logger.warning(f"[get_user_accessible_menus] No menus returned for user {current_user.id}")
        
        # Add CORS headers to response
        response = jsonify({
            'success': True,
            'data': menus,
            'message': 'Menu user berhasil diambil'
        })
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 200
        
    except Exception as e:
        logger.error(f"[get_user_accessible_menus] Error getting user accessible menus: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Gagal mengambil menu user: {str(e)}'
        }), 500


@permission_bp.route('/audit-logs', methods=['GET'])
@jwt_required_custom
@require_admin()
def get_permission_audit_logs():
    """Get permission audit logs"""
    return PermissionController.get_permission_audit_logs()


@permission_bp.route('/statistics', methods=['GET'])
@jwt_required_custom
@require_admin()
def get_permission_statistics():
    """Get permission statistics for dashboard"""
    try:
        stats = PermissionService.get_permission_statistics()
        
        if not stats:
            return jsonify({
                'success': False,
                'error': 'Gagal mengambil statistik'
            }), 500
        
        return jsonify({
            'success': True,
            'data': {
                'total_menus': stats['total_menus'],
                'total_roles': stats['total_roles'],
                'total_permissions': stats['total_permissions'],
                'recent_audit_logs': [log.to_dict() for log in stats['recent_audit_logs']]
            },
            'message': 'Statistik permission berhasil diambil'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting permission statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Gagal mengambil statistik permission'
        }), 500


@permission_bp.route('/menus/<int:menu_id>', methods=['PUT'])
@jwt_required_custom
@require_admin()
def update_menu(menu_id):
    """Update menu information"""
    try:
        from domains.role.models.menu_models import Menu
        
        menu_id = request.view_args['menu_id']
        data = request.get_json()
        
        menu = Menu.query.get(menu_id)
        if not menu:
            return jsonify({
                'success': False,
                'error': 'Menu tidak ditemukan'
            }), 404
        
        # Update menu fields
        if 'name' in data:
            menu.name = data['name']
        if 'path' in data:
            menu.path = data['path']
        if 'icon' in data:
            menu.icon = data['icon']
        if 'parent_id' in data:
            menu.parent_id = data['parent_id']
        if 'order_index' in data:
            menu.order_index = data['order_index']
        if 'description' in data:
            menu.description = data['description']
        if 'is_active' in data:
            menu.is_active = data['is_active']
        
        menu.updated_at = datetime.utcnow()
        
        from config.database import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': menu.to_dict(),
            'message': 'Menu berhasil diperbarui'
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating menu: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Gagal memperbarui menu'
        }), 500


@permission_bp.route('/menus/bulk-update-order', methods=['PUT'])
@jwt_required_custom
@require_admin()
def bulk_update_menu_order():
    """Bulk update menu order_index"""
    try:
        from domains.role.models.menu_models import Menu
        from config.database import db
        
        data = request.get_json()
        menu_orders = data.get('menu_orders', [])
        
        if not menu_orders:
            return jsonify({
                'success': False,
                'error': 'Data menu_orders diperlukan'
            }), 400
        
        updated_count = 0
        for item in menu_orders:
            menu_id = item.get('menu_id')
            order_index = item.get('order_index')
            
            if menu_id is None or order_index is None:
                continue
            
            menu = Menu.query.get(menu_id)
            if menu:
                menu.order_index = order_index
                menu.updated_at = datetime.utcnow()
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'updated_count': updated_count
            },
            'message': f'Berhasil memperbarui {updated_count} menu order'
        }), 200
        
    except Exception as e:
        logger.error(f"Error bulk updating menu order: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Gagal memperbarui menu order'
        }), 500


# Role Level Templates
@permission_bp.route('/level-templates', methods=['GET'])
@jwt_required_custom
@require_admin()
def list_role_level_templates():
    return PermissionController.get_level_templates()


@permission_bp.route('/level-templates/<int:level>', methods=['GET'])
@jwt_required_custom
@require_admin()
def get_role_level_template(level):
    return PermissionController.get_level_template(level)


@permission_bp.route('/level-templates/<int:level>', methods=['PUT'])
@jwt_required_custom
@require_admin()
def upsert_role_level_template(level):
    try:
        data = request.get_json()
        current_user_id = getattr(request, 'current_user_id', None)
        return PermissionController.upsert_level_template(level, data or {}, current_user_id)
    except Exception as e:
        logger.error(f"Error upserting role level template: {str(e)}")
        return jsonify({'success': False, 'error': 'Gagal menyimpan template level'}), 500


# Apply level template to a specific role
@permission_bp.route('/roles/<int:role_id>/apply-level-template', methods=['POST'])
@jwt_required_custom
@require_admin()
def apply_level_template_to_role(role_id):
    """Apply Role Level Template to a role's menu permissions"""
    try:
        data = request.get_json(silent=True) or {}
        current_user_id = getattr(request, 'current_user_id', None)
        return PermissionController.apply_level_template_to_role(role_id, data, current_user_id)
    except Exception as e:
        logger.error(f"Error applying level template to role {role_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Gagal menerapkan template level ke role'}), 500


@permission_bp.route('/menus', methods=['POST'])
@jwt_required_custom
@require_admin()
def create_menu():
    """Create new menu"""
    try:
        from domains.role.models.menu_models import Menu
        from config.database import db
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'path']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Field name dan path diperlukan'
            }), 400
        
        # Check if menu with same path already exists
        existing_menu = Menu.query.filter_by(path=data['path']).first()
        if existing_menu:
            return jsonify({
                'success': False,
                'error': 'Menu dengan path tersebut sudah ada'
            }), 400
        
        # Create new menu
        menu = Menu(
            name=data['name'],
            path=data['path'],
            icon=data.get('icon', '📄'),
            parent_id=data.get('parent_id'),
            order_index=data.get('order_index', 0),
            description=data.get('description'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(menu)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': menu.to_dict(),
            'message': 'Menu berhasil dibuat'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating menu: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Gagal membuat menu'
        }), 500


@permission_bp.route('/menus/<int:menu_id>', methods=['DELETE'])
@jwt_required_custom
@require_admin()
def delete_menu():
    """Delete menu (soft delete)"""
    try:
        from domains.role.models.menu_models import Menu
        from config.database import db
        
        menu_id = request.view_args['menu_id']
        
        menu = Menu.query.get(menu_id)
        if not menu:
            return jsonify({
                'success': False,
                'error': 'Menu tidak ditemukan'
            }), 404
        
        # Check if it's a system menu
        if menu.is_system_menu:
            return jsonify({
                'success': False,
                'error': 'Menu sistem tidak dapat dihapus'
            }), 400
        
        # Soft delete
        menu.is_active = False
        menu.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Menu berhasil dihapus'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting menu: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Gagal menghapus menu'
        }), 500


# Error handlers
@permission_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint tidak ditemukan'
    }), 404


@permission_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Terjadi kesalahan internal server'
    }), 500

