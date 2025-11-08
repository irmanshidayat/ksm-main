#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Role Management Controller - Best Practices Implementation
Controller untuk mengelola role management dengan business logic
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from config.database import db
from models.role_management import (
    Department, Role, Permission, RolePermission, UserRole, 
    PermissionTemplate, WorkflowTemplate, WorkflowInstance, AuditLog
)
from services.permission_service import permission_service, PermissionService
from services.workflow_service import workflow_service
from services.audit_service import audit_service
from utils.response_standardizer import APIResponse

logger = logging.getLogger(__name__)

class RoleManagementController:
    """Controller untuk role management operations"""
    
    def __init__(self):
        self.permission_service = permission_service
        self.workflow_service = workflow_service
        self.audit_service = audit_service
    
    def create_department(self, data: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """Create new department with business logic"""
        try:
            # Validate required fields
            required_fields = ['name', 'code']
            for field in required_fields:
                if field not in data or not data[field]:
                    return False, f"Field {field} harus diisi", None
            
            # Check if department code already exists
            existing_dept = Department.query.filter_by(code=data['code']).first()
            if existing_dept:
                return False, "Department code sudah ada", None
            
            # Get current user for audit
            current_user_id = get_jwt_identity()
            
            # Create department
            department = Department(
                name=data['name'],
                code=data['code'],
                description=data.get('description', ''),
                parent_department_id=data.get('parent_department_id'),
                level=data.get('level', 1)
            )
            
            db.session.add(department)
            db.session.commit()
            
            # Log audit
            self.audit_service.log_department_creation(
                current_user_id, department.to_dict()
            )
            
            return True, "Department berhasil dibuat", department.to_dict()
            
        except Exception as e:
            logger.error(f"❌ Error creating department: {e}")
            db.session.rollback()
            return False, f"Gagal membuat department: {str(e)}", None
    
    def create_role(self, data: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """Create new role with business logic"""
        try:
            # Normalisasi dan validasi data dasar
            raw_name = (data.get('name') or '').strip()
            if not raw_name:
                return False, "Field name harus diisi", None

            raw_department = data.get('department_id')
            try:
                department_id = int(raw_department)
                if department_id <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                return False, "Department tidak valid", None

            raw_level = data.get('level', 1)
            try:
                level = int(raw_level)
                if level < 1:
                    level = 1
            except (TypeError, ValueError):
                level = 1

            raw_is_management = data.get('is_management', False)
            if isinstance(raw_is_management, str):
                is_management = raw_is_management.lower() in ['true', '1', 'yes']
            else:
                is_management = bool(raw_is_management)

            description = (data.get('description') or '').strip()

            raw_code = data.get('code')
            if isinstance(raw_code, str):
                raw_code = raw_code.strip()
            if not raw_code:
                generated = raw_name.upper().replace(' ', '_')
                code = generated[:50] if len(generated) > 50 else generated
            else:
                code = raw_code.upper().replace(' ', '_')

            # Check if department exists
            department = Department.query.get(department_id)
            if not department:
                return False, "Department tidak ditemukan", None
            
            # Check if role name already exists in department
            existing_role = Role.query.filter_by(
                name=raw_name,
                department_id=department_id
            ).first()
            if existing_role:
                return False, "Role sudah ada di department ini", None
            
            # Get current user for audit
            current_user_id = get_jwt_identity()
            
            # Create role
            role = Role(
                name=raw_name,
                code=code,
                description=description,
                department_id=department_id,
                level=level,
                is_management=is_management
            )
            
            db.session.add(role)
            db.session.commit()
            
            # Apply default menu permissions from Role Level Template (if exists)
            try:
                from models.menu_models import RoleLevelTemplate, MenuPermission
                tpl = RoleLevelTemplate.query.filter_by(level=role.level, is_active=True).first()
                if tpl and tpl.permissions:
                    # Clear any existing menu permissions for safety (new role shouldn't have any)
                    # and then create according to template
                    for item in tpl.permissions:
                        menu_id = item.get('menu_id')
                        perms = item.get('permissions', {})
                        if not menu_id:
                            continue
                        mp = MenuPermission.query.filter_by(menu_id=menu_id, role_id=role.id).first()
                        if not mp:
                            mp = MenuPermission(menu_id=menu_id, role_id=role.id, granted_by=current_user_id)
                            db.session.add(mp)
                        mp.can_read = bool(perms.get('can_read', False))
                        mp.can_create = bool(perms.get('can_create', False))
                        mp.can_update = bool(perms.get('can_update', False))
                        mp.can_delete = bool(perms.get('can_delete', False))
                        mp.granted_at = datetime.utcnow()
                        mp.is_active = True
                    db.session.commit()
            except Exception as e:
                logger.error(f"⚠️ Failed to apply role level template permissions: {e}")
                db.session.rollback()
                # Do not fail role creation due to template issues

            # Log audit
            self.audit_service.log_action(
                current_user_id, 'CREATE', 'ROLE', role.id,
                new_values=role.to_dict()
            )
            
            return True, "Role berhasil dibuat", role.to_dict()
            
        except Exception as e:
            logger.error(f"❌ Error creating role: {e}")
            db.session.rollback()
            return False, f"Gagal membuat role: {str(e)}", None
    
    def get_role_detail(self, role_id: int) -> Tuple[bool, str, Optional[Dict]]:
        """Get role detail with permissions and statistics"""
        try:
            # Get role
            role = Role.query.get(role_id)
            if not role:
                return False, "Role tidak ditemukan", None
            
            # Get role permissions
            permissions = RolePermission.query.filter_by(role_id=role_id).all()
            permissions_data = [perm.to_dict() for perm in permissions]
            
            # Get users count with this role
            users_count = UserRole.query.filter_by(
                role_id=role_id, 
                is_active=True
            ).count()
            
            # Get department info
            department = Department.query.get(role.department_id)
            department_name = department.name if department else None
            
            # Build role detail
            role_detail = role.to_dict()
            role_detail.update({
                'permissions': permissions_data,
                'permissions_count': len(permissions_data),
                'users_count': users_count,
                'department_name': department_name
            })
            
            return True, "Role detail retrieved successfully", role_detail
            
        except Exception as e:
            logger.error(f"❌ Error getting role detail: {e}")
            return False, f"Gagal mengambil detail role: {str(e)}", None
    
    def update_role(self, role_id: int, data: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """Update role with business logic"""
        try:
            # Get role
            role = Role.query.get(role_id)
            if not role:
                return False, "Role tidak ditemukan", None
            
            # Check if role is system role (cannot be modified)
            if role.is_system_role:
                return False, "System role tidak dapat dimodifikasi", None
            
            # Get current user for audit
            current_user_id = get_jwt_identity()
            
            # Check if current user has permission to update roles
            if not PermissionService.check_user_permission(
                current_user_id, 'roles', 'update'
            ):
                return False, "Anda tidak memiliki permission untuk update role", None
            
            # Store old values for audit
            old_values = role.to_dict()
            
            # Update role fields
            if 'name' in data:
                # Check if new name already exists in department
                existing_role = Role.query.filter(
                    Role.name == data['name'],
                    Role.department_id == role.department_id,
                    Role.id != role_id
                ).first()
                if existing_role:
                    return False, "Nama role sudah ada di department ini", None
                role.name = data['name']
            
            if 'code' in data:
                # Check if new code already exists
                existing_role = Role.query.filter(
                    Role.code == data['code'],
                    Role.id != role_id
                ).first()
                if existing_role:
                    return False, "Kode role sudah ada", None
                role.code = data['code']
            
            if 'description' in data:
                role.description = data['description']
            
            if 'department_id' in data:
                # Check if new department exists
                department = Department.query.get(data['department_id'])
                if not department:
                    return False, "Department tidak ditemukan", None
                
                # Check if role name already exists in new department
                existing_role = Role.query.filter(
                    Role.name == role.name,
                    Role.department_id == data['department_id'],
                    Role.id != role_id
                ).first()
                if existing_role:
                    return False, "Nama role sudah ada di department yang baru", None
                
                role.department_id = data['department_id']
            
            if 'level' in data:
                role.level = data['level']
            
            if 'is_management' in data:
                role.is_management = data['is_management']
            
            # Update timestamp
            role.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log audit
            self.audit_service.log_action(
                current_user_id, 'UPDATE', 'ROLE', role_id,
                old_values=old_values,
                new_values=role.to_dict()
            )
            
            return True, "Role berhasil diperbarui", role.to_dict()
            
        except Exception as e:
            logger.error(f"❌ Error updating role: {e}")
            db.session.rollback()
            return False, f"Gagal memperbarui role: {str(e)}", None
    
    def delete_role(self, role_id: int) -> Tuple[bool, str]:
        """Delete role with business logic (soft delete)"""
        try:
            # Get role
            role = Role.query.get(role_id)
            if not role:
                return False, "Role tidak ditemukan"
            
            # Check if role is system role (cannot be deleted)
            if role.is_system_role:
                return False, "System role tidak dapat dihapus"
            
            # Check if role has active users
            active_users = UserRole.query.filter_by(
                role_id=role_id, 
                is_active=True
            ).count()
            
            if active_users > 0:
                return False, f"Role tidak dapat dihapus karena masih memiliki {active_users} user aktif"
            
            # Get current user for audit
            current_user_id = get_jwt_identity()
            
            # Check if current user has permission to delete roles
            if not PermissionService.check_user_permission(
                current_user_id, 'roles', 'delete'
            ):
                return False, "Anda tidak memiliki permission untuk delete role"
            
            # Store old values for audit
            old_values = role.to_dict()
            
            # Soft delete - set is_active to False
            role.is_active = False
            role.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log audit
            self.audit_service.log_action(
                current_user_id, 'DELETE', 'ROLE', role_id,
                old_values=old_values
            )
            
            return True, "Role berhasil dihapus"
            
        except Exception as e:
            logger.error(f"❌ Error deleting role: {e}")
            db.session.rollback()
            return False, f"Gagal menghapus role: {str(e)}"
    
    def assign_role_to_user(self, user_id: int, role_id: int, 
                           expires_at: datetime = None) -> Tuple[bool, str]:
        """Assign role to user with business logic"""
        try:
            # Check if user exists
            from models.knowledge_base import User
            user = User.query.get(user_id)
            if not user:
                return False, "User tidak ditemukan"
            
            # Check if role exists
            role = Role.query.get(role_id)
            if not role:
                return False, "Role tidak ditemukan"
            
            # Check if user already has this role
            existing_user_role = UserRole.query.filter_by(
                user_id=user_id,
                role_id=role_id
            ).first()
            if existing_user_role and existing_user_role.is_active:
                return False, "User sudah memiliki role ini"
            
            # Get current user for audit
            current_user_id = get_jwt_identity()
            
            # Check if current user has permission to assign this role
            if not PermissionService.check_user_permission(
                current_user_id, 'roles', 'assign'
            ):
                return False, "Anda tidak memiliki permission untuk assign role"
            
            # Create or update user role
            if existing_user_role:
                existing_user_role.is_active = True
                existing_user_role.assigned_at = datetime.utcnow()
                existing_user_role.expires_at = expires_at
                existing_user_role.assigned_by = current_user_id
            else:
                user_role = UserRole(
                    user_id=user_id,
                    role_id=role_id,
                    assigned_by=current_user_id,
                    expires_at=expires_at
                )
                db.session.add(user_role)
            
            db.session.commit()
            
            # Log audit
            self.audit_service.log_role_assignment(
                current_user_id, user_id, role_id, role.name
            )
            
            return True, "Role berhasil diassign ke user"
            
        except Exception as e:
            logger.error(f"❌ Error assigning role to user: {e}")
            db.session.rollback()
            return False, f"Gagal assign role: {str(e)}"
    
    def revoke_role_from_user(self, user_id: int, role_id: int) -> Tuple[bool, str]:
        """Revoke role from user with business logic"""
        try:
            # Check if user role exists
            user_role = UserRole.query.filter_by(
                user_id=user_id,
                role_id=role_id,
                is_active=True
            ).first()
            if not user_role:
                return False, "User tidak memiliki role ini"
            
            # Get current user for audit
            current_user_id = get_jwt_identity()
            
            # Check if current user has permission to revoke this role
            if not PermissionService.check_user_permission(
                current_user_id, 'roles', 'revoke'
            ):
                return False, "Anda tidak memiliki permission untuk revoke role"
            
            # Get role name for audit
            role = Role.query.get(role_id)
            role_name = role.name if role else f"Role ID {role_id}"
            
            # Revoke role
            user_role.is_active = False
            db.session.commit()
            
            # Log audit
            self.audit_service.log_role_revocation(
                current_user_id, user_id, role_id, role_name
            )
            
            return True, "Role berhasil direvoke dari user"
            
        except Exception as e:
            logger.error(f"❌ Error revoking role from user: {e}")
            db.session.rollback()
            return False, f"Gagal revoke role: {str(e)}"
    
    def assign_permission_to_role(self, role_id: int, permission_id: int, 
                                 granted: bool = True, expires_at: datetime = None) -> Tuple[bool, str]:
        """Assign permission to role with business logic"""
        try:
            # Check if role exists
            role = Role.query.get(role_id)
            if not role:
                return False, "Role tidak ditemukan"
            
            # Check if permission exists
            permission = Permission.query.get(permission_id)
            if not permission:
                return False, "Permission tidak ditemukan"
            
            # Get current user for audit
            current_user_id = get_jwt_identity()
            
            # Check if current user has permission to manage permissions
            if not PermissionService.check_user_permission(
                current_user_id, 'permissions', 'manage'
            ):
                return False, "Anda tidak memiliki permission untuk manage permissions"
            
            # Assign permission
            success = self.permission_service.assign_permission_to_role(
                role_id, permission_id, granted, expires_at, current_user_id
            )
            
            if success:
                # Log audit
                self.audit_service.log_permission_change(
                    current_user_id, role_id, permission_id, granted
                )
                return True, "Permission berhasil diassign ke role"
            else:
                return False, "Gagal assign permission ke role"
            
        except Exception as e:
            logger.error(f"❌ Error assigning permission to role: {e}")
            return False, f"Gagal assign permission: {str(e)}"
    
    def get_user_permissions(self, user_id: int) -> Tuple[bool, str, List[Dict]]:
        """Get user effective permissions"""
        try:
            permissions = self.permission_service.get_user_permissions(user_id)
            return True, "User permissions retrieved successfully", permissions
            
        except Exception as e:
            logger.error(f"❌ Error getting user permissions: {e}")
            return False, f"Gagal mengambil user permissions: {str(e)}", []
    
    def check_user_permission(self, user_id: int, module: str, action: str, 
                             scope: str = 'own', resource_id: int = None) -> Tuple[bool, str, bool]:
        """Check if user has specific permission"""
        try:
            has_permission = PermissionService.check_user_permission(
                user_id, module, action, scope, resource_id
            )
            return True, "Permission check completed", has_permission
            
        except Exception as e:
            logger.error(f"❌ Error checking user permission: {e}")
            return False, f"Gagal check permission: {str(e)}", False
    
    def create_permission_template(self, data: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """Create permission template with business logic"""
        try:
            # Validate required fields
            required_fields = ['name', 'permissions']
            for field in required_fields:
                if field not in data or not data[field]:
                    return False, f"Field {field} harus diisi", None
            
            # Get current user for audit
            current_user_id = get_jwt_identity()
            
            # Check if current user has permission to create templates
            if not PermissionService.check_user_permission(
                current_user_id, 'permissions', 'manage'
            ):
                return False, "Anda tidak memiliki permission untuk create template", None
            
            # Create template
            template = self.permission_service.create_permission_template(
                data['name'],
                data.get('description', ''),
                data['permissions'],
                current_user_id
            )
            
            if template:
                # Log audit
                self.audit_service.log_action(
                    current_user_id, 'CREATE', 'PERMISSION',
                    template.id, new_values=template.to_dict()
                )
                return True, "Permission template berhasil dibuat", template.to_dict()
            else:
                return False, "Gagal membuat permission template", None
            
        except Exception as e:
            logger.error(f"❌ Error creating permission template: {e}")
            return False, f"Gagal membuat template: {str(e)}", None
    
    def apply_permission_template(self, template_id: int, role_id: int) -> Tuple[bool, str]:
        """Apply permission template to role"""
        try:
            # Get current user for audit
            current_user_id = get_jwt_identity()
            
            # Check if current user has permission to manage permissions
            if not PermissionService.check_user_permission(
                current_user_id, 'permissions', 'manage'
            ):
                return False, "Anda tidak memiliki permission untuk apply template"
            
            # Apply template
            success = self.permission_service.apply_permission_template(
                template_id, role_id, current_user_id
            )
            
            if success:
                # Log audit
                self.audit_service.log_action(
                    current_user_id, 'UPDATE', 'ROLE', role_id,
                    additional_info={'operation': 'apply_permission_template', 'template_id': template_id}
                )
                return True, "Permission template berhasil diapply ke role"
            else:
                return False, "Gagal apply permission template"
            
        except Exception as e:
            logger.error(f"❌ Error applying permission template: {e}")
            return False, f"Gagal apply template: {str(e)}"
    
    def start_workflow(self, template_id: int, resource_type: str, 
                      resource_id: int = None, data: Dict = None) -> Tuple[bool, str, Optional[Dict]]:
        """Start workflow instance"""
        try:
            # Get current user for audit
            current_user_id = get_jwt_identity()
            
            # Start workflow
            workflow = self.workflow_service.start_workflow(
                template_id, current_user_id, resource_type, resource_id, data
            )
            
            if workflow:
                # Log audit
                self.audit_service.log_workflow_action(
                    current_user_id, workflow.id, 'CREATE', workflow.to_dict()
                )
                return True, "Workflow berhasil dimulai", workflow.to_dict()
            else:
                return False, "Gagal memulai workflow", None
            
        except Exception as e:
            logger.error(f"❌ Error starting workflow: {e}")
            return False, f"Gagal memulai workflow: {str(e)}", None
    
    def approve_workflow(self, workflow_id: int, comments: str = None) -> Tuple[bool, str]:
        """Approve workflow step"""
        try:
            # Get current user for audit
            current_user_id = get_jwt_identity()
            
            # Approve workflow
            success = self.workflow_service.approve_workflow_step(
                workflow_id, current_user_id, comments
            )
            
            if success:
                # Log audit
                self.audit_service.log_workflow_action(
                    current_user_id, workflow_id, 'APPROVE', 
                    {'comments': comments}
                )
                return True, "Workflow step berhasil diapprove"
            else:
                return False, "Gagal approve workflow step"
            
        except Exception as e:
            logger.error(f"❌ Error approving workflow: {e}")
            return False, f"Gagal approve workflow: {str(e)}"
    
    def reject_workflow(self, workflow_id: int, reason: str) -> Tuple[bool, str]:
        """Reject workflow step"""
        try:
            # Get current user for audit
            current_user_id = get_jwt_identity()
            
            # Reject workflow
            success = self.workflow_service.reject_workflow_step(
                workflow_id, current_user_id, reason
            )
            
            if success:
                # Log audit
                self.audit_service.log_workflow_action(
                    current_user_id, workflow_id, 'REJECT', 
                    {'reason': reason}
                )
                return True, "Workflow step berhasil direject"
            else:
                return False, "Gagal reject workflow step"
            
        except Exception as e:
            logger.error(f"❌ Error rejecting workflow: {e}")
            return False, f"Gagal reject workflow: {str(e)}"
    
    def get_user_workflow_history(self, user_id: int, limit: int = 50) -> Tuple[bool, str, List[Dict]]:
        """Get user workflow history"""
        try:
            workflows = self.workflow_service.get_user_workflow_history(user_id, limit)
            return True, "Workflow history retrieved successfully", workflows
            
        except Exception as e:
            logger.error(f"❌ Error getting workflow history: {e}")
            return False, f"Gagal mengambil workflow history: {str(e)}", []
    
    def get_pending_approvals(self, user_id: int) -> Tuple[bool, str, List[Dict]]:
        """Get pending approvals for user"""
        try:
            approvals = self.workflow_service.get_user_pending_approvals(user_id)
            return True, "Pending approvals retrieved successfully", approvals
            
        except Exception as e:
            logger.error(f"❌ Error getting pending approvals: {e}")
            return False, f"Gagal mengambil pending approvals: {str(e)}", []
    
    def get_audit_logs(self, search_params: Dict) -> Tuple[bool, str, List[Dict]]:
        """Get audit logs with search parameters"""
        try:
            logs = self.audit_service.search_audit_logs(search_params)
            return True, "Audit logs retrieved successfully", logs
            
        except Exception as e:
            logger.error(f"❌ Error getting audit logs: {e}")
            return False, f"Gagal mengambil audit logs: {str(e)}", []
    
    def get_audit_statistics(self, days: int = 30) -> Tuple[bool, str, Dict]:
        """Get audit statistics"""
        try:
            stats = self.audit_service.get_audit_statistics(days)
            return True, "Audit statistics retrieved successfully", stats
            
        except Exception as e:
            logger.error(f"❌ Error getting audit statistics: {e}")
            return False, f"Gagal mengambil audit statistics: {str(e)}", {}
    
    def get_security_alerts(self, days: int = 7) -> Tuple[bool, str, List[Dict]]:
        """Get security alerts"""
        try:
            alerts = self.audit_service.get_security_alerts(days)
            return True, "Security alerts retrieved successfully", alerts
            
        except Exception as e:
            logger.error(f"❌ Error getting security alerts: {e}")
            return False, f"Gagal mengambil security alerts: {str(e)}", []

# Export singleton instance
role_management_controller = RoleManagementController()
