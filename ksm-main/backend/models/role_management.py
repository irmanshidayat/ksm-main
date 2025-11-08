#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Role Management Models - Best Practices Implementation
Sistem role hierarchy dan permission management yang komprehensif
"""

from datetime import datetime, timedelta
from config.database import db
from sqlalchemy import Index, UniqueConstraint
import json


class Department(db.Model):
    """Model untuk departemen dengan best practices"""
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.Text)
    parent_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    level = db.Column(db.Integer, default=1)  # Hierarchy level
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('Department', remote_side=[id], backref='sub_departments')
    roles = db.relationship('Role', backref='department', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        Index('idx_department_code', 'code'),
        Index('idx_department_parent', 'parent_department_id'),
        Index('idx_department_active', 'is_active'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'parent_department_id': self.parent_department_id,
            'level': self.level,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_hierarchy_tree(cls):
        """Get department hierarchy tree"""
        def build_tree(parent_id=None, level=0):
            departments = cls.query.filter_by(
                parent_department_id=parent_id,
                is_active=True
            ).order_by(cls.name).all()
            
            tree = []
            for dept in departments:
                dept_dict = dept.to_dict()
                dept_dict['level'] = level
                dept_dict['sub_departments'] = build_tree(dept.id, level + 1)
                tree.append(dept_dict)
            
            return tree
        
        return build_tree()

class Role(db.Model):
    """Model untuk role dengan best practices"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    level = db.Column(db.Integer, nullable=False)  # Hierarchy level (1-10)
    description = db.Column(db.Text)
    is_management = db.Column(db.Boolean, default=False)  # Management role flag
    is_system_role = db.Column(db.Boolean, default=False)  # System roles cannot be deleted
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    permissions = db.relationship('RolePermission', backref='role', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_role_code', 'code'),
        Index('idx_role_department', 'department_id'),
        Index('idx_role_level', 'level'),
        Index('idx_role_active', 'is_active'),
        UniqueConstraint('name', 'department_id', name='unique_role_name_per_department'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'level': self.level,
            'description': self.description,
            'is_management': self.is_management,
            'is_system_role': self.is_system_role,
            'is_active': self.is_active,
            'permissions_count': self.permissions.count(),
            'users_count': UserRole.query.filter_by(role_id=self.id).count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def has_permission(self, module, action, resource_type=None):
        """Check if role has specific permission"""
        query = self.permissions.join(Permission).filter(
            Permission.module == module,
            Permission.action == action
        )
        
        if resource_type:
            query = query.filter(Permission.resource_type == resource_type)
        
        return query.filter(RolePermission.granted == True).first() is not None
    
    def can_manage_role(self, target_role):
        """Check if this role can manage target role"""
        if self.is_system_role and not target_role.is_system_role:
            return True
        
        if self.department_id == target_role.department_id and self.level > target_role.level:
            return True
        
        return False

class Permission(db.Model):
    """Model untuk permission dengan best practices"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(50))
    description = db.Column(db.Text)
    is_system_permission = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    role_permissions = db.relationship('RolePermission', backref='permission', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_permission_module', 'module'),
        Index('idx_permission_action', 'action'),
        Index('idx_permission_resource', 'resource_type'),
        Index('idx_permission_active', 'is_active'),
        UniqueConstraint('module', 'action', 'resource_type', name='unique_permission'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'module': self.module,
            'action': self.action,
            'resource_type': self.resource_type,
            'description': self.description,
            'is_system_permission': self.is_system_permission,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RolePermission(db.Model):
    """Model untuk mapping role-permission dengan best practices"""
    __tablename__ = 'role_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    granted = db.Column(db.Boolean, default=True)
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Optional expiration
    is_active = db.Column(db.Boolean, default=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_role_permission_role', 'role_id'),
        Index('idx_role_permission_permission', 'permission_id'),
        Index('idx_role_permission_active', 'is_active'),
        UniqueConstraint('role_id', 'permission_id', name='unique_role_permission'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'role_id': self.role_id,
            'permission_id': self.permission_id,
            'permission': self.permission.to_dict() if self.permission else None,
            'granted': self.granted,
            'granted_by': self.granted_by,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active
        }

class UserRole(db.Model):
    """Model untuk mapping user-role dengan best practices"""
    __tablename__ = 'user_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Optional expiration
    is_active = db.Column(db.Boolean, default=True)
    is_primary = db.Column(db.Boolean, default=False)  # Primary role for user
    
    # Relationships - removed to avoid circular dependency
    
    # Indexes
    __table_args__ = (
        Index('idx_user_role_user', 'user_id'),
        Index('idx_user_role_role', 'role_id'),
        Index('idx_user_role_active', 'is_active'),
        Index('idx_user_role_primary', 'is_primary'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'assigned_by': self.assigned_by,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_primary': self.is_primary
        }
    
    def is_expired(self):
        """Check if role assignment is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

class CrossDepartmentAccess(db.Model):
    """Model untuk cross-department access dengan best practices"""
    __tablename__ = 'cross_department_access'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    requesting_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    target_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    access_type = db.Column(db.String(50), nullable=False)  # read, write, approve
    resource_type = db.Column(db.String(50))  # payroll, budget, customer_data
    reason = db.Column(db.Text, nullable=False)
    business_justification = db.Column(db.Text)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, nullable=False)  # Mandatory expiration
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - removed to avoid circular dependency
    
    # Indexes
    __table_args__ = (
        Index('idx_cross_access_user', 'user_id'),
        Index('idx_cross_access_requesting', 'requesting_department_id'),
        Index('idx_cross_access_target', 'target_department_id'),
        Index('idx_cross_access_active', 'is_active'),
        Index('idx_cross_access_expires', 'expires_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'requesting_department_id': self.requesting_department_id,
            'target_department_id': self.target_department_id,
            'access_type': self.access_type,
            'resource_type': self.resource_type,
            'reason': self.reason,
            'business_justification': self.business_justification,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def is_expired(self):
        """Check if cross-department access is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if access is valid (active and not expired)"""
        return self.is_active and not self.is_expired()

class AccessRequest(db.Model):
    """Model untuk access request dengan best practices"""
    __tablename__ = 'access_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    access_type = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(50))
    reason = db.Column(db.Text, nullable=False)
    business_justification = db.Column(db.Text, nullable=False)
    requested_duration = db.Column(db.Integer, nullable=False)  # in days
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, expired
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - removed to avoid circular dependency
    
    # Indexes
    __table_args__ = (
        Index('idx_access_request_requester', 'requester_id'),
        Index('idx_access_request_target', 'target_department_id'),
        Index('idx_access_request_status', 'status'),
        Index('idx_access_request_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'requester_id': self.requester_id,
            'target_department_id': self.target_department_id,
            'access_type': self.access_type,
            'resource_type': self.resource_type,
            'reason': self.reason,
            'business_justification': self.business_justification,
            'requested_duration': self.requested_duration,
            'status': self.status,
            'approver_id': self.approver_id,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def approve(self, approver_id, expires_at=None):
        """Approve access request"""
        self.status = 'approved'
        self.approver_id = approver_id
        self.approved_at = datetime.utcnow()
        
        if expires_at:
            self.expires_at = expires_at
        else:
            self.expires_at = datetime.utcnow() + timedelta(days=self.requested_duration)
        
        # Create cross-department access
        cross_access = CrossDepartmentAccess(
            user_id=self.requester_id,
            requesting_department_id=self.requester.department_id,
            target_department_id=self.target_department_id,
            access_type=self.access_type,
            resource_type=self.resource_type,
            reason=self.reason,
            business_justification=self.business_justification,
            approved_by=approver_id,
            approved_at=datetime.utcnow(),
            expires_at=self.expires_at
        )
        db.session.add(cross_access)
        db.session.commit()
        
        return cross_access
    
    def reject(self, approver_id, rejection_reason):
        """Reject access request"""
        self.status = 'rejected'
        self.approver_id = approver_id
        self.approved_at = datetime.utcnow()
        self.rejection_reason = rejection_reason
        db.session.commit()

class PermissionTemplate(db.Model):
    """Model untuk permission templates dengan best practices"""
    __tablename__ = 'permission_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    permissions = db.Column(db.JSON, nullable=False)  # Array of permission objects
    is_system_template = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_permission_template_name', 'name'),
        Index('idx_permission_template_active', 'is_active'),
        Index('idx_permission_template_system', 'is_system_template'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'permissions': self.permissions,
            'is_system_template': self.is_system_template,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_system_templates(cls):
        """Get all system permission templates"""
        return cls.query.filter_by(is_system_template=True, is_active=True).all()
    
    @classmethod
    def get_custom_templates(cls):
        """Get all custom permission templates"""
        return cls.query.filter_by(is_system_template=False, is_active=True).all()

class WorkflowTemplate(db.Model):
    """Model untuk workflow templates dengan best practices"""
    __tablename__ = 'workflow_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    steps = db.Column(db.JSON, nullable=False)  # Array of workflow steps
    is_system_template = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    department = db.relationship('Department', backref='workflow_templates')
    
    # Indexes
    __table_args__ = (
        Index('idx_workflow_template_name', 'name'),
        Index('idx_workflow_template_department', 'department_id'),
        Index('idx_workflow_template_active', 'is_active'),
        Index('idx_workflow_template_system', 'is_system_template'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'steps': self.steps,
            'is_system_template': self.is_system_template,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_department(cls, department_id):
        """Get workflow templates for specific department"""
        return cls.query.filter_by(
            department_id=department_id, 
            is_active=True
        ).all()
    
    @classmethod
    def get_system_templates(cls):
        """Get all system workflow templates"""
        return cls.query.filter_by(is_system_template=True, is_active=True).all()

class AuditLog(db.Model):
    """Model untuk audit logs dengan best practices"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # CREATE, UPDATE, DELETE, ASSIGN, REVOKE
    resource_type = db.Column(db.String(50), nullable=False)  # USER, ROLE, PERMISSION, DEPARTMENT
    resource_id = db.Column(db.Integer)
    old_values = db.Column(db.JSON)  # Previous values
    new_values = db.Column(db.JSON)  # New values
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    additional_info = db.Column(db.JSON)  # Additional context
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_log_user', 'user_id'),
        Index('idx_audit_log_action', 'action'),
        Index('idx_audit_log_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_log_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'additional_info': self.additional_info,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def log_action(cls, user_id, action, resource_type, resource_id=None, 
                   old_values=None, new_values=None, ip_address=None, 
                   user_agent=None, additional_info=None):
        """Create audit log entry"""
        audit_log = cls(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_info=additional_info
        )
        db.session.add(audit_log)
        db.session.commit()
        return audit_log
    
    @classmethod
    def get_user_activity(cls, user_id, limit=50):
        """Get user activity logs"""
        return cls.query.filter_by(user_id=user_id)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit).all()
    
    @classmethod
    def get_resource_history(cls, resource_type, resource_id, limit=50):
        """Get resource change history"""
        return cls.query.filter_by(
            resource_type=resource_type, 
            resource_id=resource_id
        ).order_by(cls.created_at.desc()).limit(limit).all()

class WorkflowInstance(db.Model):
    """Model untuk workflow instances dengan best practices"""
    __tablename__ = 'workflow_instances'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_template_id = db.Column(db.Integer, db.ForeignKey('workflow_templates.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # ROLE_ASSIGNMENT, PERMISSION_REQUEST, etc.
    resource_id = db.Column(db.Integer)
    current_step = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, expired
    data = db.Column(db.JSON)  # Workflow data
    approvers = db.Column(db.JSON)  # List of approvers for each step
    approvals = db.Column(db.JSON)  # Approval history
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    workflow_template = db.relationship('WorkflowTemplate', backref='instances')
    requester = db.relationship('User', backref='workflow_requests')
    
    # Indexes
    __table_args__ = (
        Index('idx_workflow_instance_template', 'workflow_template_id'),
        Index('idx_workflow_instance_requester', 'requester_id'),
        Index('idx_workflow_instance_status', 'status'),
        Index('idx_workflow_instance_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'workflow_template_id': self.workflow_template_id,
            'workflow_template_name': self.workflow_template.name if self.workflow_template else None,
            'requester_id': self.requester_id,
            'requester_name': self.requester.username if self.requester else None,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'current_step': self.current_step,
            'status': self.status,
            'data': self.data,
            'approvers': self.approvers,
            'approvals': self.approvals,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def approve_step(self, approver_id, comments=None):
        """Approve current workflow step"""
        if not self.approvals:
            self.approvals = []
        
        approval = {
            'step': self.current_step,
            'approver_id': approver_id,
            'approved_at': datetime.utcnow().isoformat(),
            'comments': comments
        }
        self.approvals.append(approval)
        
        # Move to next step
        self.current_step += 1
        
        # Check if workflow is complete
        if self.current_step >= len(self.workflow_template.steps):
            self.status = 'approved'
            self.completed_at = datetime.utcnow()
        
        db.session.commit()
        return True
    
    def reject_step(self, approver_id, reason):
        """Reject workflow step"""
        if not self.approvals:
            self.approvals = []
        
        rejection = {
            'step': self.current_step,
            'approver_id': approver_id,
            'rejected_at': datetime.utcnow().isoformat(),
            'reason': reason
        }
        self.approvals.append(rejection)
        
        self.status = 'rejected'
        self.completed_at = datetime.utcnow()
        
        db.session.commit()
        return True