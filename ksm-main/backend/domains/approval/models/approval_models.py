#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Approval Models - Best Practices Implementation
Model untuk approval workflow dan escalation system
"""

from datetime import datetime, timedelta
from config.database import db
from sqlalchemy import Index, UniqueConstraint


class ApprovalWorkflow(db.Model):
    """Model untuk approval workflow dengan best practices"""
    __tablename__ = 'approval_workflows'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    module = db.Column(db.String(50), nullable=False)  # user_management, finance, hr, etc.
    action_type = db.Column(db.String(50), nullable=False)  # create_user, approve_expense, etc.
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    steps = db.relationship('ApprovalStep', backref='workflow', lazy='dynamic', cascade='all, delete-orphan')
    requests = db.relationship('ApprovalRequest', backref='workflow', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_approval_workflow_module', 'module'),
        Index('idx_approval_workflow_action', 'action_type'),
        Index('idx_approval_workflow_department', 'department_id'),
        Index('idx_approval_workflow_active', 'is_active'),
        UniqueConstraint('module', 'action_type', 'department_id', name='unique_approval_workflow'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'module': self.module,
            'action_type': self.action_type,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'description': self.description,
            'is_active': self.is_active,
            'steps_count': self.steps.count(),
            'requests_count': self.requests.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }

class ApprovalStep(db.Model):
    """Model untuk step dalam approval workflow"""
    __tablename__ = 'approval_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('approval_workflows.id'), nullable=False)
    step_order = db.Column(db.Integer, nullable=False)
    step_name = db.Column(db.String(100), nullable=False)
    approver_role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    approver_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    approval_type = db.Column(db.String(20), default='single')  # single, multiple, any
    is_required = db.Column(db.Boolean, default=True)
    timeout_hours = db.Column(db.Integer, default=24)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    # approver_role = db.relationship('Role', backref='approval_steps')
    # approver_department = db.relationship('Department', backref='approval_steps')
    actions = db.relationship('ApprovalAction', backref='step', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_approval_step_workflow', 'workflow_id'),
        Index('idx_approval_step_order', 'step_order'),
        Index('idx_approval_step_role', 'approver_role_id'),
        Index('idx_approval_step_department', 'approver_department_id'),
        Index('idx_approval_step_active', 'is_active'),
        UniqueConstraint('workflow_id', 'step_order', name='unique_workflow_step_order'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'step_order': self.step_order,
            'step_name': self.step_name,
            'approver_role_id': self.approver_role_id,
            'approver_role_name': self.approver_role.name if self.approver_role else None,
            'approver_department_id': self.approver_department_id,
            'approver_department_name': self.approver_department.name if self.approver_department else None,
            'approval_type': self.approval_type,
            'is_required': self.is_required,
            'timeout_hours': self.timeout_hours,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ApprovalRequest(db.Model):
    """Model untuk request yang perlu approval"""
    __tablename__ = 'approval_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('approval_workflows.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module = db.Column(db.String(50), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.Integer)  # ID of the resource being approved
    resource_data = db.Column(db.JSON, nullable=False)  # Data yang perlu approval
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, expired, cancelled
    current_step = db.Column(db.Integer, default=1)
    timeout_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    delegation_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # requester = db.relationship('User', backref='approval_requests')
    actions = db.relationship('ApprovalAction', backref='request', lazy='dynamic', cascade='all, delete-orphan')
    escalation_logs = db.relationship('EscalationLog', backref='request', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_approval_request_workflow', 'workflow_id'),
        Index('idx_approval_request_requester', 'requester_id'),
        Index('idx_approval_request_module', 'module'),
        Index('idx_approval_request_action', 'action_type'),
        Index('idx_approval_request_status', 'status'),
        Index('idx_approval_request_created', 'created_at'),
        Index('idx_approval_request_timeout', 'timeout_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'workflow_name': self.workflow.name if self.workflow else None,
            'requester_id': self.requester_id,
            'requester_name': self.requester.username if self.requester else None,
            'module': self.module,
            'action_type': self.action_type,
            'resource_id': self.resource_id,
            'resource_data': self.resource_data,
            'status': self.status,
            'current_step': self.current_step,
            'timeout_at': self.timeout_at.isoformat() if self.timeout_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'rejection_reason': self.rejection_reason,
            'delegation_reason': self.delegation_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'actions_count': self.actions.count(),
            'escalation_count': self.escalation_logs.count(),
            'is_timeout': self.is_timeout(),
            'days_since_created': self.days_since_created()
        }
    
    def is_timeout(self):
        """Check if request is timeout"""
        if self.timeout_at:
            return datetime.utcnow() > self.timeout_at
        return False
    
    def days_since_created(self):
        """Get days since request was created"""
        if self.created_at:
            return (datetime.utcnow() - self.created_at).days
        return 0

class ApprovalAction(db.Model):
    """Model untuk action approval"""
    __tablename__ = 'approval_actions'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('approval_requests.id'), nullable=False)
    step_id = db.Column(db.Integer, db.ForeignKey('approval_steps.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # approve, reject, delegate, comment
    comment = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    # Relationships
    # approver = db.relationship('User', backref='approval_actions')
    
    # Indexes
    __table_args__ = (
        Index('idx_approval_action_request', 'request_id'),
        Index('idx_approval_action_step', 'step_id'),
        Index('idx_approval_action_approver', 'approver_id'),
        Index('idx_approval_action_timestamp', 'timestamp'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'step_id': self.step_id,
            'step_name': self.step.step_name if self.step else None,
            'approver_id': self.approver_id,
            'approver_name': self.approver.username if self.approver else None,
            'action': self.action,
            'comment': self.comment,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }

class EscalationLog(db.Model):
    """Model untuk log escalation"""
    __tablename__ = 'escalation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('approval_requests.id'), nullable=False)
    step_id = db.Column(db.Integer, db.ForeignKey('approval_steps.id'), nullable=False)
    escalated_from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    escalated_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    escalation_reason = db.Column(db.String(100), nullable=False)  # timeout, rejection, manual
    escalation_level = db.Column(db.Integer, default=1)
    escalation_type = db.Column(db.String(20), default='timeout')  # timeout, rejection, manual
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, acknowledged, resolved
    acknowledged_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    # Relationships
    # escalated_from_user = db.relationship('User', foreign_keys=[escalated_from_user_id], backref='escalated_from')
    # escalated_to_user = db.relationship('User', foreign_keys=[escalated_to_user_id], backref='escalated_to')
    
    # Indexes
    __table_args__ = (
        Index('idx_escalation_log_request', 'request_id'),
        Index('idx_escalation_log_step', 'step_id'),
        Index('idx_escalation_log_from_user', 'escalated_from_user_id'),
        Index('idx_escalation_log_to_user', 'escalated_to_user_id'),
        Index('idx_escalation_log_timestamp', 'timestamp'),
        Index('idx_escalation_log_status', 'status'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'step_id': self.step_id,
            'step_name': self.step.step_name if self.step else None,
            'escalated_from_user_id': self.escalated_from_user_id,
            'escalated_from_user_name': self.escalated_from_user.username if self.escalated_from_user else None,
            'escalated_to_user_id': self.escalated_to_user_id,
            'escalated_to_user_name': self.escalated_to_user.username if self.escalated_to_user else None,
            'escalation_reason': self.escalation_reason,
            'escalation_level': self.escalation_level,
            'escalation_type': self.escalation_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'status': self.status,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'notes': self.notes
        }
    
    def acknowledge(self, user_id: int, notes: str = None):
        """Acknowledge escalation"""
        self.status = 'acknowledged'
        self.acknowledged_at = datetime.utcnow()
        if notes:
            self.notes = notes
        db.session.commit()
    
    def resolve(self, user_id: int, notes: str = None):
        """Resolve escalation"""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()
        if notes:
            self.notes = notes
        db.session.commit()

class ApprovalTemplate(db.Model):
    """Model untuk approval template"""
    __tablename__ = 'approval_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    module = db.Column(db.String(50), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    template_data = db.Column(db.JSON, nullable=False)  # Template configuration
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    # department = db.relationship('Department', backref='approval_templates')
    # creator = db.relationship('User', backref='created_approval_templates')
    
    # Indexes
    __table_args__ = (
        Index('idx_approval_template_module', 'module'),
        Index('idx_approval_template_action', 'action_type'),
        Index('idx_approval_template_department', 'department_id'),
        Index('idx_approval_template_active', 'is_active'),
        UniqueConstraint('name', 'department_id', name='unique_approval_template_name'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'module': self.module,
            'action_type': self.action_type,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'template_data': self.template_data,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
