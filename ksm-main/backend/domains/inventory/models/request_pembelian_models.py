#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Request Pembelian Models - Database Models untuk Sistem Request Pembelian Barang
Model untuk request pembelian dan item pembelian
"""

from datetime import datetime, timedelta
from config.database import db
from sqlalchemy import Index, UniqueConstraint, DECIMAL
from sqlalchemy.dialects.mysql import ENUM


class RequestPembelian(db.Model):
    """Model untuk request pembelian barang"""
    __tablename__ = 'request_pembelian'
    
    id = db.Column(db.Integer, primary_key=True)
    request_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    reference_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    
    # Status management
    status = db.Column(ENUM(
        'draft', 'submitted', 'vendor_uploading', 'under_analysis', 
        'approved', 'rejected', 'vendor_selected', 'completed'
    ), default='draft', nullable=False)
    
    priority = db.Column(ENUM('low', 'medium', 'high', 'urgent'), default='medium', nullable=False)
    
    # Budget dan timeline
    total_budget = db.Column(DECIMAL(15, 2), nullable=True)
    request_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    required_date = db.Column(db.DateTime, nullable=True)
    vendor_upload_deadline = db.Column(db.DateTime, nullable=True)
    analysis_deadline = db.Column(db.DateTime, nullable=True)
    approval_deadline = db.Column(db.DateTime, nullable=True)
    
    # Deskripsi dan catatan
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('RequestPembelianItem', backref='request', lazy='dynamic', cascade='all, delete-orphan')
    # Vendor relationships - lazy import untuk menghindari circular dependency
    @property
    def vendor_penawarans(self):
        """Lazy load vendor penawarans"""
        try:
            from domains.vendor.models.vendor_models import VendorPenawaran
            return db.session.query(VendorPenawaran).filter_by(request_id=self.id).all()
        except Exception:
            return []
    
    @property
    def analysis_results(self):
        """Lazy load vendor analysis"""
        try:
            from domains.vendor.models.vendor_models import VendorAnalysis
            return db.session.query(VendorAnalysis).filter_by(request_id=self.id).all()
        except Exception:
            return []
    
    # Indexes
    __table_args__ = (
        Index('idx_request_pembelian_user', 'user_id'),
        Index('idx_request_pembelian_department', 'department_id'),
        Index('idx_request_pembelian_status', 'status'),
        Index('idx_request_pembelian_priority', 'priority'),
        Index('idx_request_pembelian_created', 'created_at'),
        Index('idx_request_pembelian_deadline', 'vendor_upload_deadline'),
    )
    
    def to_dict(self):
        # Safely get request_number, fallback to reference_id if not available
        request_number = None
        try:
            request_number = getattr(self, 'request_number', None) or self.reference_id
        except (AttributeError, KeyError):
            request_number = self.reference_id
        
        # Safely get items with error handling
        items_list = []
        items_count = 0
        try:
            items_list = [item.to_dict() for item in self.items.all()]
            items_count = self.items.count()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error loading items for request {self.id}: {str(e)}")
            items_list = []
            items_count = 0
        
        # Safely get vendor penawarans count
        vendor_penawarans_count = 0
        try:
            vendor_penawarans_count = len(self.vendor_penawarans)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error counting vendor penawarans for request {self.id}: {str(e)}")
            vendor_penawarans_count = 0
        
        return {
            'id': self.id,
            'request_number': request_number,
            'reference_id': self.reference_id,
            'user_id': self.user_id,
            'department_id': self.department_id,
            'status': self.status,
            'priority': self.priority,
            'total_budget': float(self.total_budget) if self.total_budget else None,
            'request_date': self.request_date.isoformat() if self.request_date else None,
            'required_date': self.required_date.isoformat() if self.required_date else None,
            'vendor_upload_deadline': self.vendor_upload_deadline.isoformat() if self.vendor_upload_deadline else None,
            'analysis_deadline': self.analysis_deadline.isoformat() if self.analysis_deadline else None,
            'approval_deadline': self.approval_deadline.isoformat() if self.approval_deadline else None,
            'title': self.title,
            'description': self.description,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': items_list,
            'items_count': items_count,
            'vendor_penawarans_count': vendor_penawarans_count,
            'is_overdue': self.is_overdue(),
            'days_remaining': self.days_remaining()
        }
    
    def is_overdue(self):
        """Check if request is overdue"""
        if self.vendor_upload_deadline:
            return datetime.utcnow() > self.vendor_upload_deadline
        return False
    
    def days_remaining(self):
        """Get days remaining until deadline"""
        if self.vendor_upload_deadline:
            delta = self.vendor_upload_deadline - datetime.utcnow()
            return delta.days if delta.days > 0 else 0
        return None


class RequestPembelianItem(db.Model):
    """Model untuk item dalam request pembelian"""
    __tablename__ = 'request_pembelian_items'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request_pembelian.id'), nullable=False)
    barang_id = db.Column(db.Integer, nullable=True)
    
    # Quantity dan harga
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(DECIMAL(15, 2), nullable=True)
    total_price = db.Column(DECIMAL(15, 2), nullable=True)
    
    # Spesifikasi teknis
    specifications = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # barang = db.relationship('Barang', backref='request_items')
    
    # Indexes
    __table_args__ = (
        Index('idx_request_item_request', 'request_id'),
        Index('idx_request_item_barang', 'barang_id'),
    )
    
    def to_dict(self):
        item_data = {
            'id': self.id,
            'request_id': self.request_id,
            'barang_id': self.barang_id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'total_price': float(self.total_price) if self.total_price else None,
            'specifications': self.specifications,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Add barang information if available
        if self.barang_id:
            try:
                from domains.inventory.models.inventory_models import Barang, KategoriBarang
                # Use db.session directly (Flask-SQLAlchemy handles context automatically)
                barang = db.session.query(Barang).filter(Barang.id == self.barang_id).first()
                if barang:
                    # Get kategori information
                    kategori = None
                    if barang.kategori_id:
                        kategori = db.session.query(KategoriBarang).filter(KategoriBarang.id == barang.kategori_id).first()
                    
                    # Add barang details
                    item_data['nama_barang'] = barang.nama_barang
                    item_data['kategori'] = kategori.nama_kategori if kategori else None
                    item_data['satuan'] = barang.satuan
                    item_data['deskripsi'] = barang.deskripsi
                else:
                    # Fallback if barang not found
                    item_data['nama_barang'] = f"Barang ID {self.barang_id}"
                    item_data['kategori'] = None
                    item_data['satuan'] = 'pcs'
                    item_data['deskripsi'] = None
            except Exception as e:
                # Fallback if there's any error (database connection, missing table, etc.)
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error loading barang info for item {self.id}: {str(e)}")
                item_data['nama_barang'] = f"Barang ID {self.barang_id}"
                item_data['kategori'] = None
                item_data['satuan'] = 'pcs'
                item_data['deskripsi'] = None
        else:
            # Fallback if no barang_id
            item_data['nama_barang'] = "Barang Tidak Diketahui"
            item_data['kategori'] = None
            item_data['satuan'] = 'pcs'
            item_data['deskripsi'] = None
        
        return item_data


# Vendor models sudah dipindah ke domains/vendor/models/vendor_models.py
# Import dari vendor domain untuk backward compatibility jika diperlukan
# from domains.vendor.models.vendor_models import (
#     Vendor, VendorCategory, VendorPenawaran, VendorPenawaranFile,
#     VendorPenawaranItem, VendorAnalysis, UploadConfig, FileUploadLog,
#     VendorTemplate, VendorNotification
# )
