#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Role Management Routes - Best Practices Implementation
API routes untuk role management system dengan hierarchy dan permissions
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from middlewares.api_auth import jwt_required_custom, admin_required
from middlewares.role_auth import require_management_role
# Models will be imported dynamically from models_init
from utils.response_standardizer import APIResponse
from controllers.role_management_controller import role_management_controller
import logging
from datetime import datetime, timedelta
from services.user_role_service import UserRoleService

# Create blueprint
role_management_bp = Blueprint('role_management', __name__, url_prefix='/api/role-management')

def get_models():
    """Helper function to get models"""
    from config.models_init import init_models
    return init_models()

@role_management_bp.route('/departments', methods=['GET'])
@jwt_required_custom
def get_departments():
    """Get all departments dengan hierarchy"""
    try:
        models = get_models()
        Department = models['role_management']['Department']
        
        departments = Department.query.filter_by(is_active=True).all()
        departments_data = [dept.to_dict() for dept in departments]
        
        return APIResponse.success(
            data=departments_data,
            message="Departments retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting departments: {e}")
        return APIResponse.error("Failed to get departments")

@role_management_bp.route('/departments', methods=['POST'])
@admin_required
def create_department():
    """Create new department"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Data tidak boleh kosong")
        
        # Validasi required fields
        required_fields = ['name', 'code']
        for field in required_fields:
            if field not in data or not data[field]:
                return APIResponse.error(f"Field {field} harus diisi")
        
        models = get_models()
        Department = models['role_management']['Department']
        
        # Cek apakah code sudah ada
        existing_dept = Department.query.filter_by(code=data['code']).first()
        if existing_dept:
            return APIResponse.error("Department code sudah ada")
        
        # Create department
        new_department = Department(
            name=data['name'],
            code=data['code'],
            description=data.get('description', ''),
            parent_department_id=data.get('parent_department_id'),
            level=data.get('level', 1)
        )
        
        from config.database import db
        db.session.add(new_department)
        db.session.commit()
        
        return APIResponse.success(
            data=new_department.to_dict(),
            message="Department berhasil dibuat"
        )
    except Exception as e:
        logging.error(f"Error creating department: {e}")
        from config.database import db
        db.session.rollback()
        return APIResponse.error("Failed to create department")

@role_management_bp.route('/roles', methods=['GET'])
@jwt_required_custom
def get_roles():
    """Get all roles dengan permissions"""
    try:
        models = get_models()
        Role = models['role_management']['Role']
        RolePermission = models['role_management']['RolePermission']
        
        roles = Role.query.filter_by(is_active=True).all()
        roles_data = []
        
        for role in roles:
            role_dict = role.to_dict()
            # Add permissions
            permissions = RolePermission.query.filter_by(role_id=role.id).all()
            role_dict['permissions'] = [perm.to_dict() for perm in permissions]
            roles_data.append(role_dict)
        
        return APIResponse.success(
            data=roles_data,
            message="Roles retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting roles: {e}")
        return APIResponse.error("Failed to get roles")

@role_management_bp.route('/roles', methods=['POST'])
@admin_required
def create_role():
    """Create new role"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Data tidak boleh kosong")

        success, message, result = role_management_controller.create_role(data)

        if success:
            return jsonify({
                'success': True,
                'data': result,
                'message': message
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
    except Exception as e:
        logging.error(f"Error creating role: {e}")
        from config.database import db
        db.session.rollback()
        return APIResponse.error("Failed to create role")

@role_management_bp.route('/roles/<int:role_id>/permissions', methods=['GET'])
@jwt_required_custom
def get_role_permissions(role_id):
    """Get permissions for specific role"""
    try:
        from sqlalchemy.orm import joinedload
        
        models = get_models()
        Role = models['role_management']['Role']
        RolePermission = models['role_management']['RolePermission']
        
        # Cek apakah role ada
        role = Role.query.get(role_id)
        if not role:
            return APIResponse.error("Role tidak ditemukan")
        
        # Get role permissions dengan eager loading permission untuk menghindari N+1 query
        Permission = models['role_management']['Permission']
        
        # Gunakan join eksplisit untuk memastikan permission ter-load
        from sqlalchemy.orm import joinedload
        role_permissions = RolePermission.query.options(
            joinedload(RolePermission.permission)
        ).filter_by(role_id=role_id, is_active=True).all()
        
        permissions_data = []
        for rp in role_permissions:
            # SELALU load permission secara manual untuk memastikan data lengkap
            perm = None
            if rp.permission_id:
                perm = Permission.query.get(rp.permission_id)
                if not perm:
                    logging.warning(f"Permission dengan ID {rp.permission_id} tidak ditemukan untuk RolePermission {rp.id}")
            
            # Buat item dengan data lengkap
            item = {
                'id': rp.id,
                'role_id': rp.role_id,
                'permission_id': rp.permission_id,
                'granted': rp.granted,
                'granted_by': rp.granted_by,
                'granted_at': rp.granted_at.isoformat() if rp.granted_at else None,
                'expires_at': rp.expires_at.isoformat() if rp.expires_at else None,
                'is_active': rp.is_active
            }
            
            # Tambahkan permission data jika ada
            if perm:
                perm_dict = perm.to_dict()
                item['permission'] = perm_dict
                item['module'] = perm_dict.get('module')
                item['action'] = perm_dict.get('action')
                item['description'] = perm_dict.get('description')
            else:
                # Jika permission tidak ditemukan, set null
                item['permission'] = None
                item['module'] = None
                item['action'] = None
                item['description'] = None
            
            # Debug logging
            logging.info(f"RolePermission {rp.id}: permission_id={rp.permission_id}, has_permission={bool(perm)}, module={item.get('module')}, action={item.get('action')}")
            permissions_data.append(item)
        
        logging.info(f"Returning {len(permissions_data)} role permissions for role {role_id}")
        return APIResponse.success(
            data=permissions_data,
            message="Role permissions retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting role permissions: {e}")
        return APIResponse.error("Failed to get role permissions")

@role_management_bp.route('/roles/<int:role_id>/permissions', methods=['POST'])
@admin_required
def assign_permissions():
    """Assign permissions to role"""
    try:
        role_id = request.view_args['role_id']
        data = request.get_json()
        if not data or 'permissions' not in data:
            return APIResponse.error("Permissions data tidak boleh kosong")
        
        models = get_models()
        Role = models['role_management']['Role']
        RolePermission = models['role_management']['RolePermission']
        
        # Cek apakah role ada
        role = Role.query.get(role_id)
        if not role:
            return APIResponse.error("Role tidak ditemukan")
        
        from config.database import db
        
        # Hapus permissions lama
        RolePermission.query.filter_by(role_id=role_id).delete()
        
        # Tambah permissions baru
        for perm_data in data['permissions']:
            permission = RolePermission(
                role_id=role_id,
                module=perm_data['module'],
                action=perm_data['action'],
                resource_type=perm_data.get('resource_type', '*'),
                conditions=perm_data.get('conditions', {})
            )
            db.session.add(permission)
        
        db.session.commit()
        
        return APIResponse.success(
            message="Permissions berhasil diassign"
        )
    except Exception as e:
        logging.error(f"Error assigning permissions: {e}")
        from config.database import db
        db.session.rollback()
        return APIResponse.error("Failed to assign permissions")

@role_management_bp.route('/users/<int:user_id>/roles', methods=['GET'])
@jwt_required_custom
def get_user_roles(user_id):
    """Get user roles"""
    try:
        
        models = get_models()
        UserRole = models['role_management']['UserRole']
        Role = models['role_management']['Role']
        Department = models['role_management']['Department']
        
        # Hanya tampilkan assignment aktif agar tidak membingungkan UI "Current Roles"
        user_roles = UserRole.query.filter_by(user_id=user_id, is_active=True).all()
        roles_data = []
        
        for user_role in user_roles:
            role_dict = user_role.to_dict()
            # Add role details
            role = Role.query.get(user_role.role_id)
            if role:
                role_dict['role'] = role.to_dict()
                # Add department info
                dept = Department.query.get(role.department_id)
                if dept:
                    role_dict['department'] = dept.to_dict()
            roles_data.append(role_dict)
        
        return APIResponse.success(
            data=roles_data,
            message="User roles retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting user roles: {e}")
        return APIResponse.error("Failed to get user roles")

@role_management_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@jwt_required_custom
@require_management_role()
def assign_user_role(user_id):
    """Assign role to user"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Data tidak boleh kosong")
        
        # Validasi required fields
        required_fields = ['role_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return APIResponse.error(f"Field {field} harus diisi")
        
        # Gunakan service agar bisa re-activate assignment non-aktif tanpa duplikasi
        result = UserRoleService.assign_role(
            user_id=user_id,
            role_id=int(data['role_id']),
            assigned_by=get_jwt_identity(),
            is_primary=bool(data.get('is_primary', False)),
            expires_at=data.get('expires_at')
        )
        return APIResponse.success(data=result.to_dict(), message="Role berhasil diassign ke user")
    except Exception as e:
        logging.error(f"Error assigning user role: {e}")
        return APIResponse.error("Failed to assign user role")

@role_management_bp.route('/users/<int:user_id>/roles', methods=['PUT'])
@jwt_required_custom
@require_management_role()
def replace_user_roles(user_id):
    """Ganti seluruh daftar roles aktif user agar sesuai payload."""
    try:
        data = request.get_json() or {}
        role_ids = data.get('roles', [])
        primary_role_id = data.get('primary_role_id')
        if not isinstance(role_ids, list):
            return APIResponse.error("Field roles harus berupa array")

        result = UserRoleService.replace_user_roles(
            user_id=user_id,
            new_role_ids=[int(r) for r in role_ids],
            primary_role_id=int(primary_role_id) if primary_role_id else None,
            assigned_by=get_jwt_identity()
        )
        return APIResponse.success(data=result, message="User roles updated")
    except Exception as e:
        logging.error(f"Error replacing user roles: {e}")
        return APIResponse.error("Failed to update user roles")

@role_management_bp.route('/users/<int:user_id>/roles/<int:role_id>/primary', methods=['PATCH'])
@jwt_required_custom
@require_management_role()
def set_primary_user_role(user_id, role_id):
    try:
        ok = UserRoleService.set_primary_role(user_id=user_id, role_id=role_id)
        if not ok:
            return APIResponse.error("Role tidak ditemukan/aktif untuk user")
        return APIResponse.success(message="Primary role updated")
    except Exception as e:
        logging.error(f"Error setting primary role: {e}")
        return APIResponse.error("Failed to set primary role")

@role_management_bp.route('/users/<int:user_id>/roles/<int:role_id>', methods=['DELETE'])
@jwt_required_custom
@require_management_role()
def deactivate_user_role(user_id, role_id):
    try:
        ok = UserRoleService.deactivate_user_role(user_id=user_id, role_id=role_id)
        if not ok:
            return APIResponse.error("Assignment tidak ditemukan")
        return APIResponse.success(message="Role dinonaktifkan")
    except Exception as e:
        logging.error(f"Error deactivating user role: {e}")
        return APIResponse.error("Failed to deactivate user role")

@role_management_bp.route('/users/<int:user_id>/roles/assignments/<int:user_role_id>', methods=['DELETE'])
@jwt_required_custom
@require_management_role()
def revoke_user_role_assignment(user_id, user_role_id):
    """Revoke assignment berdasarkan ID assignment (user_role_id)."""
    try:
        result = UserRoleService.revoke_user_role_by_assignment(user_id=user_id, user_role_id=user_role_id)
        if not result.get('ok'):
            error_msg = result.get('error', 'Gagal menghapus assignment')
            # Khusus pesan admin terakhir
            status_code = 400 if 'admin terakhir' in error_msg.lower() else 404 if 'tidak ditemukan' in error_msg.lower() else 400
            return jsonify({ 'success': False, 'message': error_msg }), status_code
        return jsonify({
            'success': True,
            'message': 'Role berhasil dihapus dari user',
            'data': {
                'user_id': result['user_id'],
                'user_role_id': result['user_role_id'],
                'role_id': result['role_id']
            }
        }), 200
    except Exception as e:
        logging.error(f"Error revoking user role assignment: {e}")
        return APIResponse.error("Failed to revoke user role assignment")

@role_management_bp.route('/users/<int:user_id>/permissions', methods=['GET'])
@jwt_required_custom
def get_user_permissions(user_id):
    """Get user effective permissions"""
    try:
        
        models = get_models()
        UserRole = models['role_management']['UserRole']
        RolePermission = models['role_management']['RolePermission']
        
        # Get user roles
        user_roles = UserRole.query.filter_by(user_id=user_id).all()
        permissions = []
        
        for user_role in user_roles:
            # Get role permissions
            role_permissions = RolePermission.query.filter_by(role_id=user_role.role_id).all()
            for perm in role_permissions:
                permissions.append(perm.to_dict())
        
        # Remove duplicates
        unique_permissions = []
        seen = set()
        for perm in permissions:
            key = (perm['module'], perm['action'], perm['resource_type'])
            if key not in seen:
                seen.add(key)
                unique_permissions.append(perm)
        
        return APIResponse.success(
            data=unique_permissions,
            message="User permissions retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting user permissions: {e}")
        return APIResponse.error("Failed to get user permissions")

@role_management_bp.route('/check-permission', methods=['POST'])
@jwt_required_custom
def check_permission():
    """Check if user has specific permission"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Data tidak boleh kosong")
        
        required_fields = ['user_id', 'module', 'action']
        for field in required_fields:
            if field not in data or not data[field]:
                return APIResponse.error(f"Field {field} harus diisi")
        
        user_id = data['user_id']
        module = data['module']
        action = data['action']
        resource_type = data.get('resource_type', '*')
        
        models = get_models()
        UserRole = models['role_management']['UserRole']
        
        # Check permission
        has_permission = UserRole.check_user_permission(
            user_id, module, action, resource_type
        )
        
        return APIResponse.success(
            data={'has_permission': has_permission},
            message="Permission check completed"
        )
    except Exception as e:
        logging.error(f"Error checking permission: {e}")
        return APIResponse.error("Failed to check permission")

@role_management_bp.route('/cross-department-access', methods=['GET'])
@jwt_required_custom
def get_cross_department_access():
    """Get cross department access rules"""
    try:
        models = get_models()
        CrossDepartmentAccess = models['role_management']['CrossDepartmentAccess']
        
        access_rules = CrossDepartmentAccess.query.filter_by(is_active=True).all()
        rules_data = [rule.to_dict() for rule in access_rules]
        
        return APIResponse.success(
            data=rules_data,
            message="Cross department access rules retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting cross department access: {e}")
        return APIResponse.error("Failed to get cross department access")

@role_management_bp.route('/cross-department-access', methods=['POST'])
@admin_required
def create_cross_department_access():
    """Create cross department access rule"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Data tidak boleh kosong")
        
        # Validasi required fields
        required_fields = ['source_department_id', 'target_department_id', 'access_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return APIResponse.error(f"Field {field} harus diisi")
        
        models = get_models()
        CrossDepartmentAccess = models['role_management']['CrossDepartmentAccess']
        
        # Create access rule
        new_access = CrossDepartmentAccess(
            source_department_id=data['source_department_id'],
            target_department_id=data['target_department_id'],
            access_type=data['access_type'],
            permissions=data.get('permissions', []),
            conditions=data.get('conditions', {})
        )
        
        from config.database import db
        db.session.add(new_access)
        db.session.commit()
        
        return APIResponse.success(
            data=new_access.to_dict(),
            message="Cross department access rule berhasil dibuat"
        )
    except Exception as e:
        logging.error(f"Error creating cross department access: {e}")
        from config.database import db
        db.session.rollback()
        return APIResponse.error("Failed to create cross department access")

# ===== NEW ENHANCED ENDPOINTS =====

@role_management_bp.route('/departments-direct', methods=['GET'])
@jwt_required_custom
def get_departments_direct():
    """Get all departments - direct endpoint for frontend"""
    try:
        models = get_models()
        Department = models['role_management']['Department']
        
        departments = Department.query.filter_by(is_active=True).all()
        departments_data = [dept.to_dict() for dept in departments]
        
        return jsonify({
            'success': True,
            'data': departments_data,
            'message': 'Departments retrieved successfully'
        })
    except Exception as e:
        logging.error(f"Error getting departments: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get departments'
        }), 500

@role_management_bp.route('/departments-direct', methods=['POST'])
@admin_required
def create_department_direct():
    """Create new department - direct endpoint"""
    try:
        data = request.get_json()
        success, message, result = role_management_controller.create_department(data)
        
        if success:
            return jsonify({
                'success': True,
                'data': result,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
    except Exception as e:
        logging.error(f"Error creating department: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create department'
        }), 500

@role_management_bp.route('/roles-direct', methods=['GET'])
@jwt_required_custom
def get_roles_direct():
    """Get all roles - direct endpoint for frontend"""
    try:
        models = get_models()
        Role = models['role_management']['Role']
        
        roles = Role.query.filter_by(is_active=True).all()
        roles_data = [role.to_dict() for role in roles]
        
        return jsonify({
            'success': True,
            'data': roles_data,
            'message': 'Roles retrieved successfully'
        })
    except Exception as e:
        logging.error(f"Error getting roles: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get roles'
        }), 500

@role_management_bp.route('/roles-direct', methods=['POST'])
@admin_required
def create_role_direct():
    """Create new role - direct endpoint"""
    try:
        data = request.get_json()
        success, message, result = role_management_controller.create_role(data)
        
        if success:
            return jsonify({
                'success': True,
                'data': result,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
    except Exception as e:
        logging.error(f"Error creating role: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create role'
        }), 500

@role_management_bp.route('/roles/<int:role_id>', methods=['GET'])
@jwt_required_custom
def get_role_detail(role_id):
    """Get role detail by ID"""
    try:
        success, message, result = role_management_controller.get_role_detail(role_id)
        
        if success:
            return jsonify({
                'success': True,
                'data': result,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 404
    except Exception as e:
        logging.error(f"Error getting role detail: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get role detail'
        }), 500

@role_management_bp.route('/roles/<int:role_id>', methods=['PUT'])
@admin_required
def update_role(role_id):
    """Update role by ID"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Data tidak boleh kosong'
            }), 400
        
        success, message, result = role_management_controller.update_role(role_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'data': result,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
    except Exception as e:
        logging.error(f"Error updating role: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update role'
        }), 500

@role_management_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@admin_required
def delete_role(role_id):
    """Delete role by ID"""
    try:
        success, message = role_management_controller.delete_role(role_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
    except Exception as e:
        logging.error(f"Error deleting role: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete role'
        }), 500

@role_management_bp.route('/permissions', methods=['GET'])
@jwt_required_custom
def get_permissions():
    """Get all available permissions"""
    try:
        models = get_models()
        Permission = models['role_management']['Permission']
        
        permissions = Permission.query.filter_by(is_active=True).all()
        permissions_data = [perm.to_dict() for perm in permissions]
        
        return APIResponse.success(
            data=permissions_data,
            message="Permissions retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting permissions: {e}")
        return APIResponse.error("Failed to get permissions")

@role_management_bp.route('/users/<int:user_id>/permissions', methods=['GET'])
@jwt_required_custom
def get_user_permissions_endpoint(user_id):
    """Get user effective permissions"""
    try:
        success, message, permissions = role_management_controller.get_user_permissions(user_id)
        
        if success:
            return APIResponse.success(
                data=permissions,
                message=message
            )
        else:
            return APIResponse.error(message)
    except Exception as e:
        logging.error(f"Error getting user permissions: {e}")
        return APIResponse.error("Failed to get user permissions")

@role_management_bp.route('/check-permission', methods=['POST'])
@jwt_required_custom
def check_permission_endpoint():
    """Check if user has specific permission"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Data tidak boleh kosong")
        
        required_fields = ['user_id', 'module', 'action']
        for field in required_fields:
            if field not in data or not data[field]:
                return APIResponse.error(f"Field {field} harus diisi")
        
        success, message, has_permission = role_management_controller.check_user_permission(
            data['user_id'],
            data['module'],
            data['action'],
            data.get('scope', 'own'),
            data.get('resource_id')
        )
        
        if success:
            return APIResponse.success(
                data={'has_permission': has_permission},
                message=message
            )
        else:
            return APIResponse.error(message)
    except Exception as e:
        logging.error(f"Error checking permission: {e}")
        return APIResponse.error("Failed to check permission")

@role_management_bp.route('/permission-templates', methods=['GET'])
@jwt_required_custom
def get_permission_templates():
    """Get permission templates"""
    try:
        models = get_models()
        PermissionTemplate = models['role_management']['PermissionTemplate']
        
        templates = PermissionTemplate.query.filter_by(is_active=True).all()
        templates_data = [template.to_dict() for template in templates]
        
        return APIResponse.success(
            data=templates_data,
            message="Permission templates retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting permission templates: {e}")
        return APIResponse.error("Failed to get permission templates")

@role_management_bp.route('/permission-templates', methods=['POST'])
@admin_required
def create_permission_template():
    """Create permission template"""
    try:
        data = request.get_json()
        success, message, result = role_management_controller.create_permission_template(data)
        
        if success:
            return APIResponse.success(
                data=result,
                message=message
            )
        else:
            return APIResponse.error(message)
    except Exception as e:
        logging.error(f"Error creating permission template: {e}")
        return APIResponse.error("Failed to create permission template")

@role_management_bp.route('/permission-templates/<int:template_id>/apply', methods=['POST'])
@admin_required
def apply_permission_template(template_id):
    """Apply permission template to role"""
    try:
        data = request.get_json()
        if not data or 'role_id' not in data:
            return APIResponse.error("Role ID harus diisi")
        
        success, message = role_management_controller.apply_permission_template(
            template_id, data['role_id']
        )
        
        if success:
            return APIResponse.success(message=message)
        else:
            return APIResponse.error(message)
    except Exception as e:
        logging.error(f"Error applying permission template: {e}")
        return APIResponse.error("Failed to apply permission template")

@role_management_bp.route('/workflows', methods=['GET'])
@jwt_required_custom
def get_workflow_templates():
    """Get workflow templates"""
    try:
        models = get_models()
        WorkflowTemplate = models['role_management']['WorkflowTemplate']
        
        templates = WorkflowTemplate.query.filter_by(is_active=True).all()
        templates_data = [template.to_dict() for template in templates]
        
        return APIResponse.success(
            data=templates_data,
            message="Workflow templates retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting workflow templates: {e}")
        return APIResponse.error("Failed to get workflow templates")

@role_management_bp.route('/workflows', methods=['POST'])
@admin_required
def create_workflow_template():
    """Create workflow template"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Data tidak boleh kosong")
        
        required_fields = ['name', 'steps']
        for field in required_fields:
            if field not in data or not data[field]:
                return APIResponse.error(f"Field {field} harus diisi")
        
        models = get_models()
        WorkflowTemplate = models['role_management']['WorkflowTemplate']
        
        template = WorkflowTemplate(
            name=data['name'],
            description=data.get('description', ''),
            department_id=data.get('department_id'),
            steps=data['steps'],
            created_by=get_jwt_identity()
        )
        
        from config.database import db
        db.session.add(template)
        db.session.commit()
        
        return APIResponse.success(
            data=template.to_dict(),
            message="Workflow template berhasil dibuat"
        )
    except Exception as e:
        logging.error(f"Error creating workflow template: {e}")
        from config.database import db
        db.session.rollback()
        return APIResponse.error("Failed to create workflow template")

@role_management_bp.route('/workflow-instances', methods=['POST'])
@jwt_required_custom
def start_workflow():
    """Start workflow instance"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Data tidak boleh kosong")
        
        required_fields = ['template_id', 'resource_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return APIResponse.error(f"Field {field} harus diisi")
        
        success, message, result = role_management_controller.start_workflow(
            data['template_id'],
            data['resource_type'],
            data.get('resource_id'),
            data.get('data')
        )
        
        if success:
            return APIResponse.success(
                data=result,
                message=message
            )
        else:
            return APIResponse.error(message)
    except Exception as e:
        logging.error(f"Error starting workflow: {e}")
        return APIResponse.error("Failed to start workflow")

@role_management_bp.route('/workflow-instances/<int:workflow_id>/approve', methods=['POST'])
@jwt_required_custom
def approve_workflow(workflow_id):
    """Approve workflow step"""
    try:
        data = request.get_json() or {}
        comments = data.get('comments')
        
        success, message = role_management_controller.approve_workflow(workflow_id, comments)
        
        if success:
            return APIResponse.success(message=message)
        else:
            return APIResponse.error(message)
    except Exception as e:
        logging.error(f"Error approving workflow: {e}")
        return APIResponse.error("Failed to approve workflow")

@role_management_bp.route('/workflow-instances/<int:workflow_id>/reject', methods=['POST'])
@jwt_required_custom
def reject_workflow(workflow_id):
    """Reject workflow step"""
    try:
        data = request.get_json()
        if not data or 'reason' not in data:
            return APIResponse.error("Reason harus diisi")
        
        success, message = role_management_controller.reject_workflow(workflow_id, data['reason'])
        
        if success:
            return APIResponse.success(message=message)
        else:
            return APIResponse.error(message)
    except Exception as e:
        logging.error(f"Error rejecting workflow: {e}")
        return APIResponse.error("Failed to reject workflow")

@role_management_bp.route('/workflow-instances/pending', methods=['GET'])
@jwt_required_custom
def get_pending_approvals():
    """Get pending approvals for current user"""
    try:
        current_user_id = get_jwt_identity()
        success, message, approvals = role_management_controller.get_pending_approvals(current_user_id)
        
        if success:
            return APIResponse.success(
                data=approvals,
                message=message
            )
        else:
            return APIResponse.error(message)
    except Exception as e:
        logging.error(f"Error getting pending approvals: {e}")
        return APIResponse.error("Failed to get pending approvals")

@role_management_bp.route('/workflow-instances/history', methods=['GET'])
@jwt_required_custom
def get_workflow_history():
    """Get workflow history for current user"""
    try:
        current_user_id = get_jwt_identity()
        limit = request.args.get('limit', 50, type=int)
        
        success, message, history = role_management_controller.get_user_workflow_history(current_user_id, limit)
        
        if success:
            return APIResponse.success(
                data=history,
                message=message
            )
        else:
            return APIResponse.error(message)
    except Exception as e:
        logging.error(f"Error getting workflow history: {e}")
        return APIResponse.error("Failed to get workflow history")

@role_management_bp.route('/audit-logs', methods=['GET'])
@admin_required
def get_audit_logs():
    """Get audit logs with search parameters"""
    try:
        search_params = {
            'user_id': request.args.get('user_id', type=int),
            'action': request.args.get('action'),
            'resource_type': request.args.get('resource_type'),
            'resource_id': request.args.get('resource_id', type=int),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'ip_address': request.args.get('ip_address'),
            'limit': request.args.get('limit', 100, type=int)
        }
        
        # Remove None values
        search_params = {k: v for k, v in search_params.items() if v is not None}
        
        success, message, logs = role_management_controller.get_audit_logs(search_params)
        
        if success:
            return APIResponse.success(
                data=logs,
                message=message
            )
        else:
            return APIResponse.error(message)
    except Exception as e:
        logging.error(f"Error getting audit logs: {e}")
        return APIResponse.error("Failed to get audit logs")

@role_management_bp.route('/audit-statistics', methods=['GET'])
@admin_required
def get_audit_statistics():
    """Get audit statistics"""
    try:
        days = request.args.get('days', 30, type=int)
        success, message, stats = role_management_controller.get_audit_statistics(days)
        
        if success:
            return APIResponse.success(
                data=stats,
                message=message
            )
        else:
            return APIResponse.error(message)
    except Exception as e:
        logging.error(f"Error getting audit statistics: {e}")
        return APIResponse.error("Failed to get audit statistics")

@role_management_bp.route('/security-alerts', methods=['GET'])
@admin_required
def get_security_alerts():
    """Get security alerts"""
    try:
        days = request.args.get('days', 7, type=int)
        success, message, alerts = role_management_controller.get_security_alerts(days)
        
        if success:
            return APIResponse.success(
                data=alerts,
                message=message
            )
        else:
            return APIResponse.error(message)
    except Exception as e:
        logging.error(f"Error getting security alerts: {e}")
        return APIResponse.error("Failed to get security alerts")
