#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compatibility Routes - Endpoint untuk compatibility dan testing
Memindahkan endpoint dari app.py untuk struktur yang lebih clean
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging
from config.database import db
from config.config import Config

logger = logging.getLogger(__name__)

# Create blueprint
compatibility_bp = Blueprint('compatibility', __name__)

# ===== COMPATIBILITY ENDPOINTS =====

@compatibility_bp.route('/attendance/tasks/statistics', methods=['GET'])
def compat_attendance_tasks_statistics():
    """Compatibility alias for attendance tasks statistics"""
    try:
        from domains.task.controllers.daily_task_controller import DailyTaskController
        controller = DailyTaskController()
        return controller.get_statistics()
    except Exception as e:
        logger.error(f"Error in compat_attendance_tasks_statistics: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to route statistics',
            'error': str(e)
        }), 500

@compatibility_bp.route('/attendance/tasks/department-stats', methods=['GET'])
def compat_attendance_tasks_department_stats():
    """Compatibility alias for department stats"""
    try:
        return jsonify({
            'success': True,
            'data': []
        }), 200
    except Exception as e:
        logger.error(f"Error in compat_attendance_tasks_department_stats: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to route department stats',
            'error': str(e)
        }), 500

@compatibility_bp.route('/attendance/tasks/user-stats', methods=['GET'])
def compat_attendance_tasks_user_stats():
    """Compatibility alias for user stats"""
    try:
        return jsonify({
            'success': True,
            'data': []
        }), 200
    except Exception as e:
        logger.error(f"Error in compat_attendance_tasks_user_stats: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to route user stats',
            'error': str(e)
        }), 500

@compatibility_bp.route('/api/users-new/<int:user_id>', methods=['DELETE', 'OPTIONS'])
def users_new_delete(user_id: int):
    """Compatibility DELETE endpoint for users-new to perform soft delete"""
    if request.method == 'OPTIONS':
        logger.info(f"[USERS-NEW][OPTIONS] /api/users-new/{user_id}")
        return '', 200

    try:
        logger.info(f"[USERS-NEW][DELETE] Start user_id={user_id}")

        # Import models
        from models import User

        user = User.query.get(user_id)
        if not user:
            logger.warning(f"[USERS-NEW][DELETE] User {user_id} tidak ditemukan")
            return jsonify({'success': False, 'error': 'User tidak ditemukan'}), 404

        # Soft delete
        user.is_active = False
        db.session.commit()
        logger.info(f"[USERS-NEW][DELETE] Success user_id={user_id}")
        return ('', 204)
    except Exception as e:
        logger.error(f"[USERS-NEW][DELETE] Error: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'success': False, 'error': 'Terjadi kesalahan saat menonaktifkan user'}), 500

@compatibility_bp.route('/api/users-direct', methods=['GET', 'OPTIONS'])
def users_direct_endpoint():
    """Deprecated testing endpoint. Nonaktif untuk mencegah redundansi."""
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        'success': False,
        'error': 'Endpoint /api/users-direct sudah tidak digunakan. Gunakan endpoint resmi /api/auth/users atau /api/users.'
    }), 410

@compatibility_bp.route('/api/role-management/departments-direct', methods=['GET', 'OPTIONS'])
def departments_direct_endpoint():
    """Direct departments endpoint tanpa blueprint untuk testing"""
    if request.method == 'OPTIONS':
        logger.info("Departments direct OPTIONS request received")
        return '', 200
    
    try:
        # Import models
        from models import Department
        from sqlalchemy import text
        
        # Test database connection
        db.session.execute(text('SELECT 1'))
        
        # Query departments from database
        departments = Department.query.filter_by(is_active=True).all()
        departments_data = []
        
        for dept in departments:
            try:
                dept_dict = {
                    'id': dept.id,
                    'name': dept.name,
                    'code': dept.code,
                    'description': dept.description,
                    'parent_department_id': dept.parent_department_id,
                    'level': dept.level,
                    'is_active': dept.is_active,
                    'created_at': dept.created_at.isoformat() if dept.created_at else None,
                    'updated_at': dept.updated_at.isoformat() if dept.updated_at else None
                }
                departments_data.append(dept_dict)
                
            except Exception as dept_error:
                logger.warning(f"Error serializing department {getattr(dept, 'id', 'unknown')}: {dept_error}")
                continue
        
        return jsonify({
            'success': True,
            'data': departments_data,
            'count': len(departments_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting departments: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan saat mengambil data departments',
            'details': str(e)
        }), 500

@compatibility_bp.route('/api/role-management/roles-direct', methods=['GET', 'OPTIONS'])
def roles_direct_endpoint():
    """Direct roles endpoint tanpa blueprint untuk testing"""
    if request.method == 'OPTIONS':
        logger.info("Roles direct OPTIONS request received")
        return '', 200
    
    try:
        from models import Role
        from sqlalchemy import text
        
        # Test database connection
        db.session.execute(text('SELECT 1'))
        
        # Query roles from database
        roles = Role.query.filter_by(is_active=True).all()
        roles_data = []
        
        for role in roles:
            try:
                role_dict = {
                    'id': role.id,
                    'name': role.name,
                    'code': role.code,
                    'description': role.description,
                    'level': role.level,
                    'is_active': role.is_active,
                    'created_at': role.created_at.isoformat() if role.created_at else None,
                    'updated_at': role.updated_at.isoformat() if role.updated_at else None
                }
                roles_data.append(role_dict)
                
            except Exception as role_error:
                logger.warning(f"Error serializing role {getattr(role, 'id', 'unknown')}: {role_error}")
                continue
        
        return jsonify({
            'success': True,
            'data': roles_data,
            'count': len(roles_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting roles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan saat mengambil data roles',
            'details': str(e)
        }), 500

@compatibility_bp.route('/favicon.ico')
def favicon():
    """Handle favicon request"""
    return '', 204  # No Content

@compatibility_bp.route('/')
def root():
    """Root endpoint untuk health check"""
    return jsonify({
        'success': True,
        'message': 'KSM Main Backend API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }), 200

