#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit Models - Best Practices Implementation
Model untuk audit trail system dengan compliance dan monitoring
"""

from datetime import datetime, timedelta
from config.database import db
from sqlalchemy import Index, UniqueConstraint


class UserActivityLog(db.Model):
    """Model untuk user activity log dengan best practices"""
    __tablename__ = 'user_activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(100), nullable=False)  # login, logout, create, update, delete, view
    resource_type = db.Column(db.String(50))  # user, department, role, permission, etc.
    resource_id = db.Column(db.Integer)  # ID of the resource
    old_values = db.Column(db.JSON)  # Data sebelum perubahan
    new_values = db.Column(db.JSON)  # Data setelah perubahan
    additional_data = db.Column(db.JSON)  # Additional context data
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    session_id = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', backref='activity_logs')
    
    # Indexes
    __table_args__ = (
        Index('idx_user_activity_user', 'user_id'),
        Index('idx_user_activity_type', 'activity_type'),
        Index('idx_user_activity_resource', 'resource_type'),
        Index('idx_user_activity_timestamp', 'timestamp'),
        Index('idx_user_activity_ip', 'ip_address'),
        Index('idx_user_activity_session', 'session_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'activity_type': self.activity_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'additional_data': self.additional_data,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'success': self.success,
            'error_message': self.error_message
        }

class SystemEventLog(db.Model):
    """Model untuk system event log dengan best practices"""
    __tablename__ = 'system_event_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(100), nullable=False)  # startup, shutdown, error, warning, info
    event_category = db.Column(db.String(50), nullable=False)  # system, database, api, security, etc.
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='info')  # critical, high, medium, low, info
    additional_data = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    
    # Indexes
    __table_args__ = (
        Index('idx_system_event_type', 'event_type'),
        Index('idx_system_event_category', 'event_category'),
        Index('idx_system_event_severity', 'severity'),
        Index('idx_system_event_timestamp', 'timestamp'),
        Index('idx_system_event_success', 'success'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'description': self.description,
            'severity': self.severity,
            'additional_data': self.additional_data,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'success': self.success,
            'error_message': self.error_message
        }

class SecurityEventLog(db.Model):
    """Model untuk security event log dengan best practices"""
    __tablename__ = 'security_event_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(100), nullable=False)  # failed_login, privilege_escalation, data_breach, etc.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='medium')  # critical, high, medium, low
    additional_data = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', backref='security_event_logs')
    
    # Indexes
    __table_args__ = (
        Index('idx_security_event_type', 'event_type'),
        Index('idx_security_event_user', 'user_id'),
        Index('idx_security_event_severity', 'severity'),
        Index('idx_security_event_timestamp', 'timestamp'),
        Index('idx_security_event_ip', 'ip_address'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'description': self.description,
            'severity': self.severity,
            'additional_data': self.additional_data,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'success': self.success,
            'error_message': self.error_message
        }

class DataChangeLog(db.Model):
    """Model untuk data change log dengan best practices"""
    __tablename__ = 'data_change_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    change_type = db.Column(db.String(20), nullable=False)  # insert, update, delete
    old_values = db.Column(db.JSON)  # Data sebelum perubahan
    new_values = db.Column(db.JSON)  # Data setelah perubahan
    additional_data = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', backref='data_change_logs')
    
    # Indexes
    __table_args__ = (
        Index('idx_data_change_user', 'user_id'),
        Index('idx_data_change_table', 'table_name'),
        Index('idx_data_change_record', 'record_id'),
        Index('idx_data_change_type', 'change_type'),
        Index('idx_data_change_timestamp', 'timestamp'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'change_type': self.change_type,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'additional_data': self.additional_data,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'success': self.success,
            'error_message': self.error_message
        }

class AccessLog(db.Model):
    """Model untuk access log dengan best practices"""
    __tablename__ = 'access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    resource_type = db.Column(db.String(50))  # user, department, role, permission, etc.
    resource_id = db.Column(db.Integer)  # ID of the resource
    access_type = db.Column(db.String(50))  # read, write, delete, execute, etc.
    success = db.Column(db.Boolean, default=True)
    failure_reason = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='access_logs')
    
    # Indexes
    __table_args__ = (
        Index('idx_access_log_user', 'user_id'),
        Index('idx_access_log_resource', 'resource_type'),
        Index('idx_access_log_type', 'access_type'),
        Index('idx_access_log_success', 'success'),
        Index('idx_access_log_timestamp', 'timestamp'),
        Index('idx_access_log_ip', 'ip_address'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'access_type': self.access_type,
            'success': self.success,
            'failure_reason': self.failure_reason,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class SecurityAlert(db.Model):
    """Model untuk security alert dengan best practices"""
    __tablename__ = 'security_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(100), nullable=False)  # multiple_failed_logins, suspicious_access, etc.
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='medium')  # critical, high, medium, low
    additional_data = db.Column(db.JSON)
    status = db.Column(db.String(20), default='active')  # active, acknowledged, resolved, false_positive
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    acknowledged_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    acknowledger = db.relationship('User', foreign_keys=[acknowledged_by], backref='acknowledged_alerts')
    resolver = db.relationship('User', foreign_keys=[resolved_by], backref='resolved_alerts')
    
    # Indexes
    __table_args__ = (
        Index('idx_security_alert_type', 'alert_type'),
        Index('idx_security_alert_severity', 'severity'),
        Index('idx_security_alert_status', 'status'),
        Index('idx_security_alert_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'description': self.description,
            'severity': self.severity,
            'additional_data': self.additional_data,
            'status': self.status,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_by_name': self.acknowledger.username if self.acknowledger else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_by': self.resolved_by,
            'resolved_by_name': self.resolver.username if self.resolver else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def acknowledge(self, user_id: int):
        """Acknowledge security alert"""
        self.status = 'acknowledged'
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def resolve(self, user_id: int, resolution_notes: str = None):
        """Resolve security alert"""
        self.status = 'resolved'
        self.resolved_by = user_id
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = resolution_notes
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def mark_false_positive(self, user_id: int, notes: str = None):
        """Mark security alert as false positive"""
        self.status = 'false_positive'
        self.resolved_by = user_id
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = notes
        self.updated_at = datetime.utcnow()
        db.session.commit()

class ComplianceReport(db.Model):
    """Model untuk compliance report dengan best practices"""
    __tablename__ = 'compliance_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(50), nullable=False)  # gdpr, sox, pci, iso27001, etc.
    report_name = db.Column(db.String(200), nullable=False)
    report_period_start = db.Column(db.DateTime, nullable=False)
    report_period_end = db.Column(db.DateTime, nullable=False)
    report_data = db.Column(db.JSON, nullable=False)  # Report content
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='generated')  # generated, reviewed, approved, archived
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    review_notes = db.Column(db.Text)
    approval_notes = db.Column(db.Text)
    
    # Relationships
    generator = db.relationship('User', foreign_keys=[generated_by], backref='generated_compliance_reports')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_compliance_reports')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_compliance_reports')
    
    # Indexes
    __table_args__ = (
        Index('idx_compliance_report_type', 'report_type'),
        Index('idx_compliance_report_period', 'report_period_start'),
        Index('idx_compliance_report_status', 'status'),
        Index('idx_compliance_report_generated', 'generated_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'report_type': self.report_type,
            'report_name': self.report_name,
            'report_period_start': self.report_period_start.isoformat() if self.report_period_start else None,
            'report_period_end': self.report_period_end.isoformat() if self.report_period_end else None,
            'report_data': self.report_data,
            'generated_by': self.generated_by,
            'generated_by_name': self.generator.username if self.generator else None,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'status': self.status,
            'reviewed_by': self.reviewed_by,
            'reviewed_by_name': self.reviewer.username if self.reviewer else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'approved_by': self.approved_by,
            'approved_by_name': self.approver.username if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'review_notes': self.review_notes,
            'approval_notes': self.approval_notes
        }
    
    def review(self, user_id: int, review_notes: str = None):
        """Review compliance report"""
        self.status = 'reviewed'
        self.reviewed_by = user_id
        self.reviewed_at = datetime.utcnow()
        self.review_notes = review_notes
        db.session.commit()
    
    def approve(self, user_id: int, approval_notes: str = None):
        """Approve compliance report"""
        self.status = 'approved'
        self.approved_by = user_id
        self.approved_at = datetime.utcnow()
        self.approval_notes = approval_notes
        db.session.commit()
    
    def archive(self, user_id: int):
        """Archive compliance report"""
        self.status = 'archived'
        self.approved_by = user_id
        self.approved_at = datetime.utcnow()
        db.session.commit()

class AuditConfiguration(db.Model):
    """Model untuk audit configuration dengan best practices"""
    __tablename__ = 'audit_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    config_type = db.Column(db.String(50), nullable=False)  # retention_policy, alert_threshold, etc.
    config_name = db.Column(db.String(100), nullable=False)
    config_value = db.Column(db.JSON, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    creator = db.relationship('User', backref='created_audit_configurations')
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_config_type', 'config_type'),
        Index('idx_audit_config_name', 'config_name'),
        Index('idx_audit_config_active', 'is_active'),
        UniqueConstraint('config_type', 'config_name', name='unique_audit_config'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'config_type': self.config_type,
            'config_name': self.config_name,
            'config_value': self.config_value,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
