#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Budget Models - Database Models untuk Sistem Budget Integration
Model untuk budget tracking, transactions, dan analysis configuration
"""

from datetime import datetime
from config.database import db
from sqlalchemy import Index, UniqueConstraint, DECIMAL
from sqlalchemy.dialects.mysql import ENUM


class BudgetTracking(db.Model):
    """Model untuk tracking budget per departemen"""
    __tablename__ = 'budget_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    budget_year = db.Column(db.Integer, nullable=False)
    budget_category = db.Column(db.String(100), nullable=False)
    
    # Budget amounts
    allocated_budget = db.Column(DECIMAL(15, 2), nullable=False, default=0)
    used_budget = db.Column(DECIMAL(15, 2), nullable=False, default=0)
    remaining_budget = db.Column(DECIMAL(15, 2), nullable=False, default=0)
    
    # Status dan metadata
    status = db.Column(ENUM('active', 'inactive', 'exceeded'), default='active', nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('BudgetTransaction', backref='budget_tracking', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_budget_tracking_department', 'department_id'),
        Index('idx_budget_tracking_year', 'budget_year'),
        Index('idx_budget_tracking_category', 'budget_category'),
        Index('idx_budget_tracking_status', 'status'),
        UniqueConstraint('department_id', 'budget_year', 'budget_category', name='unique_budget_tracking'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'department_id': self.department_id,
            'budget_year': self.budget_year,
            'budget_category': self.budget_category,
            'allocated_budget': float(self.allocated_budget),
            'used_budget': float(self.used_budget),
            'remaining_budget': float(self.remaining_budget),
            'status': self.status,
            'notes': self.notes,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'usage_percentage': self.get_usage_percentage(),
            'is_over_budget': self.is_over_budget()
        }
    
    def get_usage_percentage(self):
        """Calculate budget usage percentage"""
        if self.allocated_budget > 0:
            return round((self.used_budget / self.allocated_budget) * 100, 2)
        return 0
    
    def is_over_budget(self):
        """Check if budget is exceeded"""
        return self.used_budget > self.allocated_budget
    
    def update_remaining_budget(self):
        """Update remaining budget"""
        self.remaining_budget = self.allocated_budget - self.used_budget
        if self.remaining_budget < 0:
            self.status = 'exceeded'
        db.session.commit()


class BudgetTransaction(db.Model):
    """Model untuk transaksi budget"""
    __tablename__ = 'budget_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    budget_tracking_id = db.Column(db.Integer, db.ForeignKey('budget_tracking.id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('request_pembelian.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    
    # Transaction details
    transaction_type = db.Column(ENUM('allocation', 'usage', 'adjustment', 'refund'), nullable=False)
    amount = db.Column(DECIMAL(15, 2), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Reference information
    reference_number = db.Column(db.String(100), nullable=True)
    reference_type = db.Column(db.String(50), nullable=True)  # purchase_request, manual_adjustment, etc.
    
    # Status dan metadata
    status = db.Column(ENUM('pending', 'approved', 'rejected', 'cancelled'), default='pending', nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_budget_transaction_budget', 'budget_tracking_id'),
        Index('idx_budget_transaction_request', 'request_id'),
        Index('idx_budget_transaction_department', 'department_id'),
        Index('idx_budget_transaction_type', 'transaction_type'),
        Index('idx_budget_transaction_status', 'status'),
        Index('idx_budget_transaction_date', 'transaction_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'budget_tracking_id': self.budget_tracking_id,
            'request_id': self.request_id,
            'department_id': self.department_id,
            'transaction_type': self.transaction_type,
            'amount': float(self.amount),
            'description': self.description,
            'reference_number': self.reference_number,
            'reference_type': self.reference_type,
            'status': self.status,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AnalysisConfig(db.Model):
    """Model untuk konfigurasi analisis vendor"""
    __tablename__ = 'analysis_config'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Scoring weights
    price_weight = db.Column(DECIMAL(3, 2), default=0.40, nullable=False)
    quality_weight = db.Column(DECIMAL(3, 2), default=0.25, nullable=False)
    delivery_weight = db.Column(DECIMAL(3, 2), default=0.20, nullable=False)
    reputation_weight = db.Column(DECIMAL(3, 2), default=0.10, nullable=False)
    payment_weight = db.Column(DECIMAL(3, 2), default=0.05, nullable=False)
    
    # Analysis settings
    ml_enabled = db.Column(db.Boolean, default=True, nullable=False)
    auto_analysis_enabled = db.Column(db.Boolean, default=True, nullable=False)
    min_vendor_count = db.Column(db.Integer, default=2, nullable=False)
    max_analysis_days = db.Column(db.Integer, default=3, nullable=False)
    
    # Thresholds
    min_score_threshold = db.Column(DECIMAL(5, 2), default=50.00, nullable=False)
    price_variance_threshold = db.Column(DECIMAL(5, 2), default=30.00, nullable=False)
    quality_threshold = db.Column(DECIMAL(5, 2), default=70.00, nullable=False)
    
    # Status dan metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_config_active', 'is_active'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'price_weight': float(self.price_weight),
            'quality_weight': float(self.quality_weight),
            'delivery_weight': float(self.delivery_weight),
            'reputation_weight': float(self.reputation_weight),
            'payment_weight': float(self.payment_weight),
            'ml_enabled': self.ml_enabled,
            'auto_analysis_enabled': self.auto_analysis_enabled,
            'min_vendor_count': self.min_vendor_count,
            'max_analysis_days': self.max_analysis_days,
            'min_score_threshold': float(self.min_score_threshold),
            'price_variance_threshold': float(self.price_variance_threshold),
            'quality_threshold': float(self.quality_threshold),
            'is_active': self.is_active,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    def validate_weights(self):
        """Validate that weights sum to 1.0"""
        total_weight = (
            self.price_weight + 
            self.quality_weight + 
            self.delivery_weight + 
            self.reputation_weight + 
            self.payment_weight
        )
        return abs(total_weight - 1.0) < 0.01  # Allow small floating point errors


class RequestTimelineConfig(db.Model):
    """Model untuk konfigurasi timeline request"""
    __tablename__ = 'request_timeline_config'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Value ranges
    min_value = db.Column(DECIMAL(15, 2), nullable=False)
    max_value = db.Column(DECIMAL(15, 2), nullable=True)
    
    # Timeline settings
    vendor_upload_days = db.Column(db.Integer, nullable=False)
    analysis_days = db.Column(db.Integer, nullable=False)
    approval_days = db.Column(db.Integer, nullable=False)
    
    # Status dan metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_timeline_config_value', 'min_value', 'max_value'),
        Index('idx_timeline_config_active', 'is_active'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'min_value': float(self.min_value),
            'max_value': float(self.max_value) if self.max_value else None,
            'vendor_upload_days': self.vendor_upload_days,
            'analysis_days': self.analysis_days,
            'approval_days': self.approval_days,
            'is_active': self.is_active,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_timeline_for_value(cls, value):
        """Get timeline configuration for a specific value"""
        config = cls.query.filter(
            cls.is_active == True,
            cls.min_value <= value,
            (cls.max_value.is_(None)) | (cls.max_value >= value)
        ).order_by(cls.min_value.desc()).first()
        
        return config


