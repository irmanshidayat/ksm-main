#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Role-based Authorization Middleware
Middleware untuk membatasi akses berdasarkan role user dan permissions dinamis
"""

from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from functools import wraps
import logging
from models import User
from domains.role.models.menu_models import Menu, MenuPermission
from models import Role, UserRole
from domains.role.services.user_role_service import UserRoleService

logger = logging.getLogger(__name__)

def check_menu_permission(user_id, menu_path, action='read'):
    """
    Check if user has permission for specific menu and action
    
    Args:
        user_id (int): User ID
        menu_path (str): Menu path (e.g., '/dashboard', '/users')
        action (str): Action to check ('read', 'create', 'update', 'delete')
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    try:
        # Get user roles
        user_roles = UserRole.query.filter_by(user_id=user_id).all()
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
        logger.error(f"Error checking menu permission: {str(e)}")
        return False

def require_permission(menu_path, action='read'):
    """
    Decorator untuk membatasi akses berdasarkan permission dinamis
    
    Args:
        menu_path (str): Path menu yang diperlukan
        action (str): Action yang diperlukan ('read', 'create', 'update', 'delete')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get current user ID from JWT
                current_user_id = get_jwt_identity()
                if not current_user_id:
                    return jsonify({
                        'success': False,
                        'error': 'Token tidak valid',
                        'message': 'Silakan login kembali'
                    }), 401
                
                # Get user from database
                user = User.query.get(current_user_id)
                if not user:
                    return jsonify({
                        'success': False,
                        'error': 'User tidak ditemukan',
                        'message': 'Akun tidak valid'
                    }), 404
                
                # Check if user is active
                if not user.is_active:
                    return jsonify({
                        'success': False,
                        'error': 'Akun tidak aktif',
                        'message': 'Akun Anda telah dinonaktifkan'
                    }), 403
                
                # Check menu permission
                has_permission = check_menu_permission(current_user_id, menu_path, action)
                
                if not has_permission:
                    primary_role_name = UserRoleService.get_primary_role(user.id).name if UserRoleService.get_primary_role(user.id) else user.role
                    logger.warning(f"❌ Permission denied: User {user.username} (role: {primary_role_name}) tried to access {menu_path} with action {action}")
                    return jsonify({
                        'success': False,
                        'error': 'Akses ditolak',
                        'message': f'Anda tidak memiliki izin untuk mengakses halaman ini',
                        'required_permission': f'{menu_path}:{action}',
                        'user_role': primary_role_name
                    }), 403
                
                # Add user info to request context
                request.current_user = user
                request.current_user_id = current_user_id
                
                primary_role_name = UserRoleService.get_primary_role(user.id).name if UserRoleService.get_primary_role(user.id) else user.role
                logger.info(f"✅ Permission granted: User {user.username} (role: {primary_role_name}) accessing {menu_path} with action {action}")
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"❌ Error in permission authorization: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Terjadi kesalahan saat verifikasi akses',
                    'message': 'Silakan coba lagi'
                }), 500
        
        return decorated_function
    return decorator

def require_role(allowed_roles):
    """
    Decorator untuk membatasi akses berdasarkan role
    
    Args:
        allowed_roles (list): List role yang diizinkan mengakses endpoint
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get current user ID from JWT
                current_user_id = get_jwt_identity()
                if not current_user_id:
                    return jsonify({
                        'success': False,
                        'error': 'Token tidak valid',
                        'message': 'Silakan login kembali'
                    }), 401
                
                # Get user from database
                user = User.query.get(current_user_id)
                if not user:
                    return jsonify({
                        'success': False,
                        'error': 'User tidak ditemukan',
                        'message': 'Akun tidak valid'
                    }), 404
                
                # Check if user is active
                if not user.is_active:
                    return jsonify({
                        'success': False,
                        'error': 'Akun tidak aktif',
                        'message': 'Akun Anda telah dinonaktifkan'
                    }), 403
                
                # Check if user role is allowed (via relasi UserRole, fallback ke legacy)
                role_names = []
                try:
                    role_objs = UserRole.query.filter_by(user_id=user.id, is_active=True).all()
                    role_names = [Role.query.get(r.role_id).name for r in role_objs if Role.query.get(r.role_id)]
                except Exception:
                    role_names = []
                role_names_with_legacy = set(role_names + [user.role] if user.role else role_names)

                if not any(r in role_names_with_legacy for r in allowed_roles):
                    primary_role_name = UserRoleService.get_primary_role(user.id).name if UserRoleService.get_primary_role(user.id) else user.role
                    logger.warning(f"❌ Access denied: User {user.username} (role: {primary_role_name}) tried to access endpoint that requires {allowed_roles}")
                    return jsonify({
                        'success': False,
                        'error': 'Akses ditolak',
                        'message': f'Anda tidak memiliki izin untuk mengakses halaman ini. Role yang diizinkan: {", ".join(allowed_roles)}',
                        'user_role': list(role_names_with_legacy),
                        'required_roles': allowed_roles
                    }), 403
                
                # Add user info to request context for use in endpoint
                request.current_user = user
                request.current_user_id = current_user_id
                
                primary_role_name = UserRoleService.get_primary_role(user.id).name if UserRoleService.get_primary_role(user.id) else user.role
                logger.info(f"✅ Access granted: User {user.username} (role: {primary_role_name}) accessing endpoint")
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"❌ Error in role authorization: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Terjadi kesalahan saat verifikasi akses',
                    'message': 'Silakan coba lagi'
                }), 500
        
        return decorated_function
    return decorator

def require_admin():
    """Decorator untuk membatasi akses hanya untuk admin"""
    return require_role(['admin'])

def require_manager():
    """Decorator untuk membatasi akses untuk manager dan admin"""
    return require_role(['admin', 'manager'])

def require_admin_or_manager():
    """Decorator untuk membatasi akses untuk admin dan manager"""
    return require_role(['admin', 'manager'])

def require_vendor():
    """Decorator untuk membatasi akses hanya untuk vendor"""
    return require_role(['vendor'])

def require_admin_or_user():
    """Decorator untuk membatasi akses untuk admin dan user (bukan vendor)"""
    return require_role(['admin', 'user'])

def require_any_role():
    """Decorator untuk membatasi akses untuk semua role yang aktif"""
    return require_role(['admin', 'user', 'vendor', 'manager', 'staff'])

def require_management_role():
    """Decorator untuk membatasi akses untuk role management (admin, manager)"""
    return require_role(['admin', 'manager'])

# Alias untuk backward compatibility
admin_required = require_admin
manager_required = require_manager

def block_vendor():
    """
    Decorator khusus untuk memblokir akses vendor
    Digunakan untuk endpoint yang tidak boleh diakses vendor
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Skip vendor blocking for OPTIONS requests (CORS preflight)
                if request.method == 'OPTIONS':
                    from flask import make_response
                    response = make_response('', 200)
                    response.headers['Access-Control-Allow-Origin'] = '*'
                    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, x-api-key, X-API-Key, Cache-Control, Accept, Origin, X-Requested-With'
                    response.headers['Access-Control-Allow-Credentials'] = 'true'
                    return response
                
                # Get current user ID from JWT
                current_user_id = get_jwt_identity()
                if not current_user_id:
                    return jsonify({
                        'success': False,
                        'error': 'Token tidak valid',
                        'message': 'Silakan login kembali'
                    }), 401
                
                # Get user from database
                user = User.query.get(current_user_id)
                if not user:
                    return jsonify({
                        'success': False,
                        'error': 'User tidak ditemukan',
                        'message': 'Akun tidak valid'
                    }), 404
                
                # Check if user is vendor
                primary_role_name = UserRoleService.get_primary_role(user.id).name if UserRoleService.get_primary_role(user.id) else user.role
                if primary_role_name == 'vendor' or user.role == 'vendor':
                    logger.warning(f"❌ Vendor access blocked: User {user.username} (vendor) tried to access admin-only endpoint")
                    return jsonify({
                        'success': False,
                        'error': 'Akses ditolak untuk vendor',
                        'message': 'Halaman ini hanya dapat diakses oleh admin dan user. Silakan gunakan menu vendor yang tersedia.',
                        'user_role': primary_role_name,
                        'redirect_url': '/vendor/dashboard'
                    }), 403
                
                # Add user info to request context
                request.current_user = user
                request.current_user_id = current_user_id
                
                logger.info(f"✅ Access granted: User {user.username} (role: {primary_role_name}) accessing admin endpoint")
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"❌ Error in vendor blocking: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Terjadi kesalahan saat verifikasi akses',
                    'message': 'Silakan coba lagi'
                }), 500
        
        return decorated_function
    return decorator
