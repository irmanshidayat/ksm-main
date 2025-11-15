#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Order Models - Database Models untuk Sistem Vendor Orders
Model untuk tracking pesanan vendor dengan status management lengkap
"""

from datetime import datetime
from config.database import db
from sqlalchemy import Index, DECIMAL
from sqlalchemy.dialects.mysql import ENUM


class VendorOrder(db.Model):
    """Model untuk tracking pesanan vendor dengan status management"""
    __tablename__ = 'vendor_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Order Identification
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    vendor_penawaran_item_id = db.Column(db.Integer, db.ForeignKey('vendor_penawaran_items.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('request_pembelian.id'), nullable=False)
    reference_id = db.Column(db.String(50), nullable=False, index=True)
    
    # Order Details (denormalized for performance)
    item_name = db.Column(db.String(255), nullable=False)
    ordered_quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(DECIMAL(15, 2), nullable=False)
    total_price = db.Column(DECIMAL(15, 2), nullable=False)
    specifications = db.Column(db.Text, nullable=True)
    
    # Status Tracking
    status = db.Column(ENUM(
        'pending_confirmation', 
        'confirmed', 
        'processing', 
        'shipped', 
        'delivered', 
        'completed', 
        'cancelled'
    ), default='pending_confirmation', nullable=False)
    
    # Confirmation Tracking
    confirmed_at = db.Column(db.DateTime, nullable=True)
    confirmed_by_vendor = db.Column(db.Boolean, default=False)
    
    # Processing Tracking
    processing_started_at = db.Column(db.DateTime, nullable=True)
    shipped_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Delivery Information
    tracking_number = db.Column(db.String(100), nullable=True)
    estimated_delivery_date = db.Column(db.DateTime, nullable=True)
    actual_delivery_date = db.Column(db.DateTime, nullable=True)
    delivery_notes = db.Column(db.Text, nullable=True)
    
    # Notes
    vendor_notes = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    vendor_penawaran_item = db.relationship('VendorPenawaranItem', backref='vendor_orders')
    vendor = db.relationship('Vendor', backref='orders')
    request = db.relationship('RequestPembelian', backref='vendor_orders')
    created_by_user = db.relationship('User', backref='created_vendor_orders')
    
    # Indexes
    __table_args__ = (
        Index('idx_vendor_orders_vendor', 'vendor_id'),
        Index('idx_vendor_orders_request', 'request_id'),
        Index('idx_vendor_orders_reference', 'reference_id'),
        Index('idx_vendor_orders_status', 'status'),
        Index('idx_vendor_orders_penawaran_item', 'vendor_penawaran_item_id'),
        Index('idx_vendor_orders_created', 'created_at'),
        Index('idx_vendor_orders_updated', 'updated_at'),
        Index('idx_vendor_orders_confirmed', 'confirmed_at'),
        Index('idx_vendor_orders_delivery', 'estimated_delivery_date'),
        Index('idx_vendor_orders_vendor_status', 'vendor_id', 'status'),
        Index('idx_vendor_orders_request_status', 'request_id', 'status'),
        Index('idx_vendor_orders_created_by_status', 'created_by_user_id', 'status'),
    )
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'vendor_penawaran_item_id': self.vendor_penawaran_item_id,
            'vendor_id': self.vendor_id,
            'request_id': self.request_id,
            'reference_id': self.reference_id,
            'item_name': self.item_name,
            'ordered_quantity': self.ordered_quantity,
            'unit_price': float(self.unit_price) if self.unit_price else 0,
            'total_price': float(self.total_price) if self.total_price else 0,
            'specifications': self.specifications,
            'status': self.status,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'confirmed_by_vendor': self.confirmed_by_vendor,
            'processing_started_at': self.processing_started_at.isoformat() if self.processing_started_at else None,
            'shipped_at': self.shipped_at.isoformat() if self.shipped_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'tracking_number': self.tracking_number,
            'estimated_delivery_date': self.estimated_delivery_date.isoformat() if self.estimated_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            'delivery_notes': self.delivery_notes,
            'vendor_notes': self.vendor_notes,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by_user_id': self.created_by_user_id,
            # Related data
            'vendor': self.vendor.to_dict() if self.vendor else None,
            'request': {
                'id': self.request.id,
                'reference_id': self.request.reference_id,
                'title': self.request.title,
                'status': self.request.status
            } if self.request else None,
            'vendor_penawaran_item': self.vendor_penawaran_item.to_dict() if self.vendor_penawaran_item else None
        }
    
    def get_status_display(self):
        """Get human readable status"""
        status_map = {
            'pending_confirmation': 'Menunggu Konfirmasi',
            'confirmed': 'Dikonfirmasi',
            'processing': 'Diproses',
            'shipped': 'Dikirim',
            'delivered': 'Diterima',
            'completed': 'Selesai',
            'cancelled': 'Dibatalkan'
        }
        return status_map.get(self.status, self.status)
    
    def get_status_color(self):
        """Get status color for UI"""
        color_map = {
            'pending_confirmation': '#f6ad55',  # Orange
            'confirmed': '#4299e1',             # Blue
            'processing': '#9f7aea',            # Purple
            'shipped': '#38b2ac',               # Teal
            'delivered': '#48bb78',             # Green
            'completed': '#68d391',             # Light Green
            'cancelled': '#f56565'              # Red
        }
        return color_map.get(self.status, '#a0aec0')
    
    def get_timeline_events(self):
        """Get timeline events for tracking"""
        events = []
        
        # Order created
        events.append({
            'status': 'created',
            'title': 'Pesanan Dibuat',
            'description': f'Pesanan {self.order_number} telah dibuat',
            'timestamp': self.created_at,
            'icon': '📦'
        })
        
        # Confirmation
        if self.confirmed_at:
            events.append({
                'status': 'confirmed',
                'title': 'Dikonfirmasi Vendor',
                'description': 'Vendor telah mengkonfirmasi pesanan',
                'timestamp': self.confirmed_at,
                'icon': '✅'
            })
        
        # Processing
        if self.processing_started_at:
            events.append({
                'status': 'processing',
                'title': 'Diproses',
                'description': 'Pesanan sedang diproses',
                'timestamp': self.processing_started_at,
                'icon': '⚙️'
            })
        
        # Shipped
        if self.shipped_at:
            events.append({
                'status': 'shipped',
                'title': 'Dikirim',
                'description': f'Pesanan telah dikirim{(" - Tracking: " + self.tracking_number) if self.tracking_number else ""}',
                'timestamp': self.shipped_at,
                'icon': '🚚'
            })
        
        # Delivered
        if self.delivered_at:
            events.append({
                'status': 'delivered',
                'title': 'Diterima',
                'description': 'Pesanan telah diterima',
                'timestamp': self.delivered_at,
                'icon': '📥'
            })
        
        # Completed
        if self.completed_at:
            events.append({
                'status': 'completed',
                'title': 'Selesai',
                'description': 'Pesanan telah selesai',
                'timestamp': self.completed_at,
                'icon': '🎉'
            })
        
        # Sort by timestamp
        events.sort(key=lambda x: x['timestamp'] or datetime.min)
        return events
    
    def can_vendor_update_status(self):
        """Check if vendor can update status"""
        return self.status in ['confirmed', 'processing', 'shipped']
    
    def can_admin_update_status(self):
        """Check if admin can update status"""
        return self.status in ['pending_confirmation', 'confirmed', 'processing', 'shipped', 'delivered']
    
    def get_next_possible_statuses(self):
        """Get next possible statuses based on current status"""
        status_flow = {
            'pending_confirmation': ['confirmed', 'cancelled'],
            'confirmed': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled'],
            'shipped': ['delivered', 'cancelled'],
            'delivered': ['completed'],
            'completed': [],
            'cancelled': []
        }
        return status_flow.get(self.status, [])
    
    def __repr__(self):
        return f'<VendorOrder {self.order_number}: {self.item_name} - {self.status}>'


class VendorOrderStatusHistory(db.Model):
    """Model untuk tracking history perubahan status vendor order"""
    __tablename__ = 'vendor_order_status_history'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_order_id = db.Column(db.Integer, db.ForeignKey('vendor_orders.id'), nullable=False)
    old_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    vendor_order = db.relationship('VendorOrder', backref='status_history')
    changed_by_user = db.relationship('User', backref='vendor_order_status_changes')
    
    # Indexes
    __table_args__ = (
        Index('idx_vendor_order_history_order', 'vendor_order_id'),
        Index('idx_vendor_order_history_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'vendor_order_id': self.vendor_order_id,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'changed_by_user_id': self.changed_by_user_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

