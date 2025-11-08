#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification Models - Best Practices Implementation
Model untuk notification system dengan batching dan analytics
"""

from datetime import datetime, timedelta
from config.database import db
from sqlalchemy import Index, UniqueConstraint


class Notification(db.Model):
    """Model untuk notification dengan best practices"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # approval_request, escalation, status_update, etc.
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    data = db.Column(db.JSON)  # Additional data
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent, critical
    action_required = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    is_sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationships - removed to avoid circular dependency
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_user', 'user_id'),
        Index('idx_notification_type', 'type'),
        Index('idx_notification_priority', 'priority'),
        Index('idx_notification_read', 'is_read'),
        Index('idx_notification_sent', 'is_sent'),
        Index('idx_notification_created', 'created_at'),
        Index('idx_notification_expires', 'expires_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'priority': self.priority,
            'action_required': self.action_required,
            'is_read': self.is_read,
            'is_sent': self.is_sent,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'time_since_created': self._get_time_since_created()
        }
    
    def _get_time_since_created(self):
        """Get time since notification was created"""
        if self.created_at:
            delta = datetime.utcnow() - self.created_at
            if delta.days > 0:
                return f"{delta.days} days ago"
            elif delta.seconds > 3600:
                return f"{delta.seconds // 3600} hours ago"
            elif delta.seconds > 60:
                return f"{delta.seconds // 60} minutes ago"
            else:
                return "Just now"
        return None
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_clicked(self):
        """Mark notification as clicked"""
        self.clicked_at = datetime.utcnow()
        db.session.commit()
    
    def is_expired(self):
        """Check if notification is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

class NotificationBatch(db.Model):
    """Model untuk notification batch dengan best practices"""
    __tablename__ = 'notification_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    batch_window_minutes = db.Column(db.Integer, default=15)
    status = db.Column(db.String(20), default='collecting')  # collecting, sent, completed, failed
    item_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='notification_batches')
    items = db.relationship('NotificationBatchItem', backref='batch', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_batch_user', 'user_id'),
        Index('idx_notification_batch_type', 'notification_type'),
        Index('idx_notification_batch_status', 'status'),
        Index('idx_notification_batch_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'batch_window_minutes': self.batch_window_minutes,
            'status': self.status,
            'item_count': self.item_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def is_ready_to_send(self):
        """Check if batch is ready to send"""
        if self.status != 'collecting':
            return False
        
        time_elapsed = datetime.utcnow() - self.created_at
        return time_elapsed.total_seconds() >= (self.batch_window_minutes * 60)

class NotificationBatchItem(db.Model):
    """Model untuk item dalam notification batch"""
    __tablename__ = 'notification_batch_items'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('notification_batches.id'), nullable=False)
    notification_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_batch_item_batch', 'batch_id'),
        Index('idx_notification_batch_item_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'notification_data': self.notification_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class NotificationPreference(db.Model):
    """Model untuk preference notification user"""
    __tablename__ = 'notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=False)
    push_enabled = db.Column(db.Boolean, default=True)
    batch_enabled = db.Column(db.Boolean, default=True)
    webhook_enabled = db.Column(db.Boolean, default=False)
    webhook_url = db.Column(db.String(500))
    quiet_hours_start = db.Column(db.Time)
    quiet_hours_end = db.Column(db.Time)
    timezone = db.Column(db.String(50), default='Asia/Jakarta')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notification_preferences')
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_preference_user', 'user_id'),
        Index('idx_notification_preference_type', 'notification_type'),
        UniqueConstraint('user_id', 'notification_type', name='unique_user_notification_preference'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'email_enabled': self.email_enabled,
            'sms_enabled': self.sms_enabled,
            'push_enabled': self.push_enabled,
            'batch_enabled': self.batch_enabled,
            'webhook_enabled': self.webhook_enabled,
            'webhook_url': self.webhook_url,
            'quiet_hours_start': self.quiet_hours_start.isoformat() if self.quiet_hours_start else None,
            'quiet_hours_end': self.quiet_hours_end.isoformat() if self.quiet_hours_end else None,
            'timezone': self.timezone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_quiet_hours(self):
        """Check if current time is in quiet hours"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = datetime.utcnow().time()
        return self.quiet_hours_start <= now <= self.quiet_hours_end

class NotificationAnalytics(db.Model):
    """Model untuk analytics notification"""
    __tablename__ = 'notification_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notifications.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    
    # Delivery metrics
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    action_taken_at = db.Column(db.DateTime)
    
    # Performance metrics
    delivery_time_seconds = db.Column(db.Integer)
    read_time_seconds = db.Column(db.Integer)
    response_time_seconds = db.Column(db.Integer)
    
    # Status
    delivery_status = db.Column(db.String(20), default='sent')  # sent, delivered, failed
    read_status = db.Column(db.String(20), default='unread')  # read, unread
    action_status = db.Column(db.String(20), default='none')  # clicked, ignored, none
    
    # Context
    device_type = db.Column(db.String(20))  # desktop, mobile, tablet
    browser = db.Column(db.String(50))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    notification = db.relationship('Notification', backref='analytics')
    user = db.relationship('User', backref='notification_analytics')
    department = db.relationship('Department', backref='notification_analytics')
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_analytics_notification', 'notification_id'),
        Index('idx_notification_analytics_user', 'user_id'),
        Index('idx_notification_analytics_type', 'notification_type'),
        Index('idx_notification_analytics_department', 'department_id'),
        Index('idx_notification_analytics_sent', 'sent_at'),
        Index('idx_notification_analytics_read', 'read_at'),
        Index('idx_notification_analytics_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'department_id': self.department_id,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'action_taken_at': self.action_taken_at.isoformat() if self.action_taken_at else None,
            'delivery_time_seconds': self.delivery_time_seconds,
            'read_time_seconds': self.read_time_seconds,
            'response_time_seconds': self.response_time_seconds,
            'delivery_status': self.delivery_status,
            'read_status': self.read_status,
            'action_status': self.action_status,
            'device_type': self.device_type,
            'browser': self.browser,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class NotificationMetrics(db.Model):
    """Model untuk aggregated metrics"""
    __tablename__ = 'notification_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    
    # Counts
    total_sent = db.Column(db.Integer, default=0)
    total_delivered = db.Column(db.Integer, default=0)
    total_read = db.Column(db.Integer, default=0)
    total_clicked = db.Column(db.Integer, default=0)
    total_actions = db.Column(db.Integer, default=0)
    
    # Rates
    delivery_rate = db.Column(db.Float, default=0.0)
    read_rate = db.Column(db.Float, default=0.0)
    click_rate = db.Column(db.Float, default=0.0)
    action_rate = db.Column(db.Float, default=0.0)
    
    # Averages
    avg_delivery_time = db.Column(db.Float, default=0.0)
    avg_read_time = db.Column(db.Float, default=0.0)
    avg_response_time = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    department = db.relationship('Department', backref='notification_metrics')
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_metrics_date', 'date'),
        Index('idx_notification_metrics_type', 'notification_type'),
        Index('idx_notification_metrics_department', 'department_id'),
        UniqueConstraint('date', 'notification_type', 'department_id', name='unique_notification_metrics'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'notification_type': self.notification_type,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'total_sent': self.total_sent,
            'total_delivered': self.total_delivered,
            'total_read': self.total_read,
            'total_clicked': self.total_clicked,
            'total_actions': self.total_actions,
            'delivery_rate': self.delivery_rate,
            'read_rate': self.read_rate,
            'click_rate': self.click_rate,
            'action_rate': self.action_rate,
            'avg_delivery_time': self.avg_delivery_time,
            'avg_read_time': self.avg_read_time,
            'avg_response_time': self.avg_response_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserActivity(db.Model):
    """Model untuk user activity tracking"""
    __tablename__ = 'user_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # login, logout, page_view, action
    activity_data = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='activities')
    
    # Indexes
    __table_args__ = (
        Index('idx_user_activity_user', 'user_id'),
        Index('idx_user_activity_type', 'activity_type'),
        Index('idx_user_activity_timestamp', 'timestamp'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'activity_data': self.activity_data,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
