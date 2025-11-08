#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Request Pembelian Models - Database Models untuk Sistem Request Pembelian Barang
Model untuk request pembelian, vendor penawaran, dan analisis vendor
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
    vendor_penawarans = db.relationship('VendorPenawaran', backref='request', lazy='dynamic', cascade='all, delete-orphan')
    analysis_results = db.relationship('VendorAnalysis', backref='request', lazy='dynamic', cascade='all, delete-orphan')
    
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
            vendor_penawarans_count = self.vendor_penawarans.count()
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
                from models.stok_barang import Barang, KategoriBarang
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


class Vendor(db.Model):
    """Model untuk data vendor"""
    __tablename__ = 'vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    business_license = db.Column(db.String(100), nullable=True)
    tax_id = db.Column(db.String(50), nullable=True)
    bank_account = db.Column(db.String(100), nullable=True)
    
    # KTP Direktur/Penanggung Jawab
    ktp_director_name = db.Column(db.String(255), nullable=True)
    ktp_director_number = db.Column(db.String(50), nullable=True)
    ktp_director_file_path = db.Column(db.String(500), nullable=True)
    ktp_director_file_name = db.Column(db.String(255), nullable=True)
    ktp_director_file_size = db.Column(db.BigInteger, nullable=True)
    ktp_director_upload_date = db.Column(db.DateTime, nullable=True)
    
    # Vendor attachment files
    akta_perusahaan_file_path = db.Column(db.String(500), nullable=True)
    akta_perusahaan_file_name = db.Column(db.String(255), nullable=True)
    akta_perusahaan_file_size = db.Column(db.BigInteger, nullable=True)
    akta_perusahaan_upload_date = db.Column(db.DateTime, nullable=True)
    
    nib_file_path = db.Column(db.String(500), nullable=True)
    nib_file_name = db.Column(db.String(255), nullable=True)
    nib_file_size = db.Column(db.BigInteger, nullable=True)
    nib_upload_date = db.Column(db.DateTime, nullable=True)
    
    npwp_file_path = db.Column(db.String(500), nullable=True)
    npwp_file_name = db.Column(db.String(255), nullable=True)
    npwp_file_size = db.Column(db.BigInteger, nullable=True)
    npwp_upload_date = db.Column(db.DateTime, nullable=True)
    
    company_profile_file_path = db.Column(db.String(500), nullable=True)
    company_profile_file_name = db.Column(db.String(255), nullable=True)
    company_profile_file_size = db.Column(db.BigInteger, nullable=True)
    company_profile_upload_date = db.Column(db.DateTime, nullable=True)
    
    surat_keagenan_file_path = db.Column(db.String(500), nullable=True)
    surat_keagenan_file_name = db.Column(db.String(255), nullable=True)
    surat_keagenan_file_size = db.Column(db.BigInteger, nullable=True)
    surat_keagenan_upload_date = db.Column(db.DateTime, nullable=True)
    
    tkdn_file_path = db.Column(db.String(500), nullable=True)
    tkdn_file_name = db.Column(db.String(255), nullable=True)
    tkdn_file_size = db.Column(db.BigInteger, nullable=True)
    tkdn_upload_date = db.Column(db.DateTime, nullable=True)
    
    surat_pernyataan_manufaktur_file_path = db.Column(db.String(500), nullable=True)
    surat_pernyataan_manufaktur_file_name = db.Column(db.String(255), nullable=True)
    surat_pernyataan_manufaktur_file_size = db.Column(db.BigInteger, nullable=True)
    surat_pernyataan_manufaktur_upload_date = db.Column(db.DateTime, nullable=True)
    
    # Vendor category dan status
    vendor_category = db.Column(ENUM('general', 'specialized', 'preferred', 'supplier', 'contractor', 'agent_tunggal', 'distributor', 'jasa', 'produk', 'custom'), default='general', nullable=False)
    custom_category = db.Column(db.String(255), nullable=True, comment='Kategori custom yang dimasukkan manual')
    vendor_type = db.Column(ENUM('internal', 'partner'), default='internal', nullable=False)
    business_model = db.Column(ENUM('supplier', 'reseller', 'both'), default='supplier', nullable=False)
    status = db.Column(ENUM('pending', 'approved', 'rejected', 'suspended'), default='pending', nullable=False)
    
    # User account reference
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    approved_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    penawarans = db.relationship('VendorPenawaran', backref='vendor', lazy='dynamic', cascade='all, delete-orphan')
    categories = db.relationship('VendorCategory', backref='vendor', lazy='dynamic', cascade='all, delete-orphan')
    user_account = db.relationship('User', backref='vendor_profile', foreign_keys="[Vendor.user_id]")
    
    # Indexes
    __table_args__ = (
        Index('idx_vendor_email', 'email'),
        Index('idx_vendor_status', 'status'),
        Index('idx_vendor_category', 'vendor_category'),
        Index('idx_vendor_type', 'vendor_type'),
        Index('idx_vendor_business_model', 'business_model'),
        Index('idx_vendor_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'business_license': self.business_license,
            'tax_id': self.tax_id,
            'bank_account': self.bank_account,
            'ktp_director_name': self.ktp_director_name,
            'ktp_director_number': self.ktp_director_number,
            'ktp_director_file_path': self.ktp_director_file_path,
            'ktp_director_file_name': self.ktp_director_file_name,
            'ktp_director_file_size': self.ktp_director_file_size,
            'ktp_director_upload_date': self.ktp_director_upload_date.isoformat() if self.ktp_director_upload_date else None,
            'akta_perusahaan_file_path': self.akta_perusahaan_file_path,
            'akta_perusahaan_file_name': self.akta_perusahaan_file_name,
            'akta_perusahaan_file_size': self.akta_perusahaan_file_size,
            'akta_perusahaan_upload_date': self.akta_perusahaan_upload_date.isoformat() if self.akta_perusahaan_upload_date else None,
            'nib_file_path': self.nib_file_path,
            'nib_file_name': self.nib_file_name,
            'nib_file_size': self.nib_file_size,
            'nib_upload_date': self.nib_upload_date.isoformat() if self.nib_upload_date else None,
            'npwp_file_path': self.npwp_file_path,
            'npwp_file_name': self.npwp_file_name,
            'npwp_file_size': self.npwp_file_size,
            'npwp_upload_date': self.npwp_upload_date.isoformat() if self.npwp_upload_date else None,
            'company_profile_file_path': self.company_profile_file_path,
            'company_profile_file_name': self.company_profile_file_name,
            'company_profile_file_size': self.company_profile_file_size,
            'company_profile_upload_date': self.company_profile_upload_date.isoformat() if self.company_profile_upload_date else None,
            'surat_keagenan_file_path': self.surat_keagenan_file_path,
            'surat_keagenan_file_name': self.surat_keagenan_file_name,
            'surat_keagenan_file_size': self.surat_keagenan_file_size,
            'surat_keagenan_upload_date': self.surat_keagenan_upload_date.isoformat() if self.surat_keagenan_upload_date else None,
            'tkdn_file_path': self.tkdn_file_path,
            'tkdn_file_name': self.tkdn_file_name,
            'tkdn_file_size': self.tkdn_file_size,
            'tkdn_upload_date': self.tkdn_upload_date.isoformat() if self.tkdn_upload_date else None,
            'surat_pernyataan_manufaktur_file_path': self.surat_pernyataan_manufaktur_file_path,
            'surat_pernyataan_manufaktur_file_name': self.surat_pernyataan_manufaktur_file_name,
            'surat_pernyataan_manufaktur_file_size': self.surat_pernyataan_manufaktur_file_size,
            'surat_pernyataan_manufaktur_upload_date': self.surat_pernyataan_manufaktur_upload_date.isoformat() if self.surat_pernyataan_manufaktur_upload_date else None,
            'vendor_category': self.vendor_category,
            'custom_category': self.custom_category,
            'vendor_type': self.vendor_type,
            'business_model': self.business_model,
            'status': self.status,
            'user_id': self.user_id,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'approved_date': self.approved_date.isoformat() if self.approved_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'penawarans_count': self.penawarans.count()
        }


class VendorCategory(db.Model):
    """Model untuk kategori vendor"""
    __tablename__ = 'vendor_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    category_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_vendor_category_vendor', 'vendor_id'),
        Index('idx_vendor_category_category', 'category_id'),
        UniqueConstraint('vendor_id', 'category_id', name='unique_vendor_category'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'vendor_id': self.vendor_id,
            'category_id': self.category_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class VendorPenawaran(db.Model):
    """Model untuk penawaran vendor"""
    __tablename__ = 'vendor_penawaran'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request_pembelian.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    reference_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Status penawaran
    status = db.Column(ENUM('submitted', 'under_review', 'selected', 'partially_selected', 'rejected'), default='submitted', nullable=False)
    
    # Harga dan timeline
    total_quoted_price = db.Column(DECIMAL(15, 2), nullable=True)
    delivery_time_days = db.Column(db.Integer, nullable=True)
    payment_terms = db.Column(db.String(255), nullable=True)
    
    # Rating dan catatan
    quality_rating = db.Column(db.Integer, nullable=True)  # 1-5 scale
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    files = db.relationship('VendorPenawaranFile', backref='penawaran', lazy='dynamic', cascade='all, delete-orphan')
    analysis = db.relationship('VendorAnalysis', backref='penawaran', lazy='dynamic', cascade='all, delete-orphan')
    items = db.relationship('VendorPenawaranItem', backref='penawaran', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_vendor_penawaran_request', 'request_id'),
        Index('idx_vendor_penawaran_vendor', 'vendor_id'),
        Index('idx_vendor_penawaran_status', 'status'),
        Index('idx_vendor_penawaran_submission', 'submission_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'vendor_id': self.vendor_id,
            'reference_id': self.reference_id,
            'status': self.status,
            'total_quoted_price': float(self.total_quoted_price) if self.total_quoted_price else None,
            'delivery_time_days': self.delivery_time_days,
            'payment_terms': self.payment_terms,
            'quality_rating': self.quality_rating,
            'notes': self.notes,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'files_count': self.files.count(),
            'has_analysis': self.analysis.count() > 0
        }


class VendorPenawaranFile(db.Model):
    """Model untuk file penawaran vendor"""
    __tablename__ = 'vendor_penawaran_files'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_penawaran_id = db.Column(db.Integer, db.ForeignKey('vendor_penawaran.id'), nullable=False)
    reference_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # File information
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    file_hash = db.Column(db.String(64), nullable=True)  # SHA256 hash
    
    # Upload information
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_penawaran_file_penawaran', 'vendor_penawaran_id'),
        Index('idx_penawaran_file_type', 'file_type'),
        Index('idx_penawaran_file_upload', 'upload_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'vendor_penawaran_id': self.vendor_penawaran_id,
            'reference_id': self.reference_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class VendorPenawaranItem(db.Model):
    """Model untuk item detail dalam penawaran vendor"""
    __tablename__ = 'vendor_penawaran_items'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_penawaran_id = db.Column(db.Integer, db.ForeignKey('vendor_penawaran.id'), nullable=False)
    request_item_id = db.Column(db.Integer, db.ForeignKey('request_pembelian_items.id'), nullable=True)
    
    # Informasi barang dari vendor
    vendor_unit_price = db.Column(DECIMAL(15, 2), nullable=True)
    vendor_total_price = db.Column(DECIMAL(15, 2), nullable=True)
    vendor_quantity = db.Column(db.Integer, nullable=True)
    vendor_specifications = db.Column(db.Text, nullable=True)
    vendor_notes = db.Column(db.Text, nullable=True)
    vendor_merk = db.Column(db.String(255), nullable=True)
    kategori = db.Column(db.String(255), nullable=True)
    
    # Selection status
    is_selected = db.Column(db.Boolean, default=False)
    selected_quantity = db.Column(db.Integer, nullable=True)  # Quantity yang dipilih untuk split
    selected_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    selected_at = db.Column(db.DateTime, nullable=True)
    selection_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    request_item = db.relationship('RequestPembelianItem', backref='vendor_penawaran_items')
    selected_by_user = db.relationship('User', backref='selected_penawaran_items')
    
    # Indexes
    __table_args__ = (
        Index('idx_vendor_penawaran_item_penawaran', 'vendor_penawaran_id'),
        Index('idx_vendor_penawaran_item_request', 'request_item_id'),
        Index('idx_vendor_penawaran_item_selected', 'is_selected'),
        Index('idx_vendor_penawaran_item_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'vendor_penawaran_id': self.vendor_penawaran_id,
            'request_item_id': self.request_item_id,
            'vendor_unit_price': float(self.vendor_unit_price) if self.vendor_unit_price else None,
            'vendor_total_price': float(self.vendor_total_price) if self.vendor_total_price else None,
            'vendor_quantity': self.vendor_quantity,
            'vendor_specifications': self.vendor_specifications,
            'vendor_notes': self.vendor_notes,
            'vendor_merk': self.vendor_merk,
            'kategori': self.kategori,
            'is_selected': self.is_selected,
            'selected_quantity': self.selected_quantity or self.vendor_quantity,
            'remaining_quantity': self.vendor_quantity - (self.selected_quantity or 0) if self.selected_quantity else self.vendor_quantity,
            'selected_by_user_id': self.selected_by_user_id,
            'selected_at': self.selected_at.isoformat() if self.selected_at else None,
            'selection_notes': self.selection_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class VendorAnalysis(db.Model):
    """Model untuk hasil analisis vendor"""
    __tablename__ = 'vendor_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request_pembelian.id'), nullable=False)
    vendor_penawaran_id = db.Column(db.Integer, db.ForeignKey('vendor_penawaran.id'), nullable=False)
    
    # Scoring components
    price_score = db.Column(DECIMAL(5, 2), nullable=True)
    quality_score = db.Column(DECIMAL(5, 2), nullable=True)
    delivery_score = db.Column(DECIMAL(5, 2), nullable=True)
    reputation_score = db.Column(DECIMAL(5, 2), nullable=True)
    payment_score = db.Column(DECIMAL(5, 2), nullable=True)
    total_score = db.Column(DECIMAL(5, 2), nullable=True)
    
    # Recommendation
    recommendation_level = db.Column(ENUM('strongly_recommend', 'recommend', 'consider', 'not_recommend'), nullable=True)
    
    # Analysis method dan report
    analysis_method = db.Column(ENUM('automated', 'simplified', 'manual'), default='automated', nullable=False)
    analysis_report = db.Column(db.Text, nullable=True)
    
    # Timestamps
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_vendor_analysis_request', 'request_id'),
        Index('idx_vendor_analysis_penawaran', 'vendor_penawaran_id'),
        Index('idx_vendor_analysis_score', 'total_score'),
        Index('idx_vendor_analysis_recommendation', 'recommendation_level'),
        Index('idx_vendor_analysis_date', 'analysis_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'vendor_penawaran_id': self.vendor_penawaran_id,
            'price_score': float(self.price_score) if self.price_score else None,
            'quality_score': float(self.quality_score) if self.quality_score else None,
            'delivery_score': float(self.delivery_score) if self.delivery_score else None,
            'reputation_score': float(self.reputation_score) if self.reputation_score else None,
            'payment_score': float(self.payment_score) if self.payment_score else None,
            'total_score': float(self.total_score) if self.total_score else None,
            'recommendation_level': self.recommendation_level,
            'analysis_method': self.analysis_method,
            'analysis_report': self.analysis_report,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UploadConfig(db.Model):
    """Model untuk konfigurasi upload file"""
    __tablename__ = 'upload_config'
    
    id = db.Column(db.Integer, primary_key=True)
    max_files_per_vendor = db.Column(db.Integer, default=5, nullable=False)
    max_size_per_file_mb = db.Column(db.Integer, default=10, nullable=False)
    allowed_formats = db.Column(db.Text, nullable=True)  # JSON array of allowed formats
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'max_files_per_vendor': self.max_files_per_vendor,
            'max_size_per_file_mb': self.max_size_per_file_mb,
            'allowed_formats': self.allowed_formats,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FileUploadLog(db.Model):
    """Model untuk log upload file"""
    __tablename__ = 'file_upload_log'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('request_pembelian.id'), nullable=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    upload_status = db.Column(ENUM('success', 'failed', 'virus_detected'), nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_upload_log_vendor', 'vendor_id'),
        Index('idx_upload_log_request', 'request_id'),
        Index('idx_upload_log_status', 'upload_status'),
        Index('idx_upload_log_date', 'upload_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'vendor_id': self.vendor_id,
            'request_id': self.request_id,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_path': self.file_path,
            'upload_status': self.upload_status,
            'error_message': self.error_message,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }


class VendorTemplate(db.Model):
    """Model untuk template vendor"""
    __tablename__ = 'vendor_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(ENUM('excel', 'pdf', 'word'), nullable=False)
    category = db.Column(ENUM('proposal', 'company_profile', 'technical_spec', 'cover_letter', 'checklist'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    download_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_vendor_template_type', 'file_type'),
        Index('idx_vendor_template_category', 'category'),
        Index('idx_vendor_template_active', 'is_active'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'category': self.category,
            'is_active': self.is_active,
            'download_count': self.download_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class VendorNotification(db.Model):
    """Model untuk notifikasi vendor"""
    __tablename__ = 'vendor_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request_pembelian.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    
    # Notification content
    notification_type = db.Column(ENUM('request_available', 'upload_reminder', 'upload_confirmation', 'analysis_complete', 'request_cancelled'), nullable=False)
    status = db.Column(ENUM('sent', 'delivered', 'failed', 'read'), nullable=False)
    subject = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=True)
    
    # Timestamps
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=True)
    
    # Additional columns for compatibility
    title = db.Column(db.String(255), nullable=True)
    type = db.Column(ENUM('deadline_warning', 'status_update', 'new_request', 'system', 'other'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    related_request_id = db.Column(db.Integer, db.ForeignKey('request_pembelian.id'), nullable=True)
    related_penawaran_id = db.Column(db.Integer, db.ForeignKey('vendor_penawaran.id'), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_vendor_notification_vendor', 'vendor_id'),
        Index('idx_vendor_notification_type', 'type'),
        Index('idx_vendor_notification_read', 'is_read'),
        Index('idx_vendor_notification_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'vendor_id': self.vendor_id,
            'notification_type': self.notification_type,
            'status': self.status,
            'subject': self.subject,
            'message': self.message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # Compatibility fields
            'title': self.title or self.subject,
            'type': self.type,
            'is_read': self.is_read or (self.status == 'read'),
            'related_request_id': self.related_request_id,
            'related_penawaran_id': self.related_penawaran_id
        }