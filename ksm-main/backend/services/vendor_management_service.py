#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Management Service - Business Logic untuk Sistem Vendor Management
Service untuk mengelola vendor registration, approval, dan file upload
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
import hashlib
import logging
from werkzeug.utils import secure_filename

from models.request_pembelian_models import (
    Vendor, VendorCategory, VendorPenawaran, VendorPenawaranFile, 
    UploadConfig, FileUploadLog
)
from models.request_pembelian_models import VendorNotification
from models.stok_barang import KategoriBarang

logger = logging.getLogger(__name__)


class VendorManagementService:
    """Service untuk mengelola vendor management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.upload_config = self._get_upload_config()
    
    # ===== VENDOR REGISTRATION =====
    
    def register_vendor(self, vendor_data: Dict[str, Any]) -> Vendor:
        """Register vendor baru"""
        try:
            # Check if email already exists
            existing_vendor = self.db.query(Vendor).filter(Vendor.email == vendor_data['email']).first()
            if existing_vendor:
                raise Exception("Email vendor sudah terdaftar")
            
            # Create vendor
            vendor = Vendor(
                company_name=vendor_data['company_name'],
                contact_person=vendor_data['contact_person'],
                email=vendor_data['email'],
                phone=vendor_data.get('phone'),
                address=vendor_data.get('address'),
                business_license=vendor_data.get('business_license'),
                tax_id=vendor_data.get('tax_id'),
                bank_account=vendor_data.get('bank_account'),
                vendor_category=vendor_data.get('vendor_category', 'general'),
                vendor_type=vendor_data.get('vendor_type', 'internal'),
                business_model=vendor_data.get('business_model', 'supplier'),
                status=vendor_data.get('status', 'pending')
            )
            
            self.db.add(vendor)
            self.db.flush()  # Get ID without committing
            
            # Add categories if provided
            if 'categories' in vendor_data:
                for category_id in vendor_data['categories']:
                    vendor_category = VendorCategory(
                        vendor_id=vendor.id,
                        category_id=category_id
                    )
                    self.db.add(vendor_category)
            
            self.db.commit()
            self.db.refresh(vendor)
            
            logger.info(f"✅ Registered vendor: {vendor.company_name} (ID: {vendor.id})")
            return vendor
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error registering vendor: {str(e)}")
            raise Exception(f"Gagal register vendor: {str(e)}")
    
    def get_vendor_by_id(self, vendor_id: int) -> Optional[Vendor]:
        """Mendapatkan vendor berdasarkan ID"""
        return self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
    
    def get_vendor_by_email(self, email: str) -> Optional[Vendor]:
        """Mendapatkan vendor berdasarkan email"""
        return self.db.query(Vendor).filter(Vendor.email == email).first()
    
    def get_vendor_by_user_id(self, user_id: int) -> Optional[Vendor]:
        """Mendapatkan vendor berdasarkan user_id"""
        return self.db.query(Vendor).filter(Vendor.user_id == user_id).first()
    
    def get_vendors_by_type(self, vendor_type: str) -> List[Vendor]:
        """Mendapatkan vendor berdasarkan type (internal/partner)"""
        return self.db.query(Vendor).filter(Vendor.vendor_type == vendor_type).all()
    
    def get_vendors_by_business_model(self, business_model: str) -> List[Vendor]:
        """Mendapatkan vendor berdasarkan business model (supplier/reseller/both)"""
        return self.db.query(Vendor).filter(Vendor.business_model == business_model).all()
    
    def get_all_vendors(self, filters: Dict[str, Any] = None) -> List[Vendor]:
        """Mendapatkan semua vendor dengan filter"""
        query = self.db.query(Vendor)
        
        if filters:
            if 'status' in filters and filters['status']:
                query = query.filter(Vendor.status == filters['status'])
            
            if 'vendor_category' in filters and filters['vendor_category']:
                query = query.filter(Vendor.vendor_category == filters['vendor_category'])
            
            if 'vendor_type' in filters and filters['vendor_type']:
                query = query.filter(Vendor.vendor_type == filters['vendor_type'])
            
            if 'business_model' in filters and filters['business_model']:
                query = query.filter(Vendor.business_model == filters['business_model'])
            
            if 'search' in filters and filters['search']:
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Vendor.company_name.ilike(search_term),
                        Vendor.contact_person.ilike(search_term),
                        Vendor.email.ilike(search_term)
                    )
                )
        
        return query.order_by(desc(Vendor.created_at)).all()
    
    def get_vendors_paginated(self, page: int = 1, per_page: int = 10, status: str = None, search: str = None) -> Dict[str, Any]:
        """Mendapatkan vendor dengan pagination"""
        try:
            query = self.db.query(Vendor)
            
            # Apply filters
            if status:
                query = query.filter(Vendor.status == status)
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Vendor.company_name.ilike(search_term),
                        Vendor.contact_person.ilike(search_term),
                        Vendor.email.ilike(search_term)
                    )
                )
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            vendors = query.order_by(desc(Vendor.created_at)).offset(offset).limit(per_page).all()
            
            # Convert to dict
            vendors_data = [vendor.to_dict() for vendor in vendors]
            
            return {
                'vendors': vendors_data,
                'pagination': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'pages': (total + per_page - 1) // per_page,
                    'has_next': page * per_page < total,
                    'has_prev': page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting paginated vendors: {str(e)}")
            return {
                'vendors': [],
                'pagination': {
                    'total': 0,
                    'page': page,
                    'per_page': per_page,
                    'pages': 0,
                    'has_next': False,
                    'has_prev': False,
                    'error': str(e)
                }
            }
    
    def update_vendor(self, vendor_id: int, update_data: Dict[str, Any]) -> Optional[Vendor]:
        """Update vendor information"""
        try:
            vendor = self.get_vendor_by_id(vendor_id)
            if not vendor:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(vendor, field) and field not in ['id', 'created_at', 'registration_date']:
                    setattr(vendor, field, value)
            
            vendor.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(vendor)
            
            logger.info(f"✅ Updated vendor: {vendor.company_name}")
            return vendor
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating vendor: {str(e)}")
            raise Exception(f"Gagal update vendor: {str(e)}")
    
    # ===== VENDOR APPROVAL =====
    
    def approve_vendor(self, vendor_id: int, approved_by: int, notes: str = None) -> Optional[Vendor]:
        """Approve vendor"""
        try:
            vendor = self.get_vendor_by_id(vendor_id)
            if not vendor:
                return None
            
            if vendor.status != 'pending':
                raise Exception("Vendor sudah diproses")
            
            vendor.status = 'approved'
            vendor.approved_date = datetime.utcnow()
            vendor.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(vendor)
            
            # Send approval notification
            self._send_vendor_notification(vendor, 'approved', notes)
            
            logger.info(f"✅ Approved vendor: {vendor.company_name}")
            return vendor
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error approving vendor: {str(e)}")
            raise Exception(f"Gagal approve vendor: {str(e)}")
    
    def reject_vendor(self, vendor_id: int, rejected_by: int, reason: str) -> Optional[Vendor]:
        """Reject vendor"""
        try:
            vendor = self.get_vendor_by_id(vendor_id)
            if not vendor:
                return None
            
            if vendor.status != 'pending':
                raise Exception("Vendor sudah diproses")
            
            vendor.status = 'rejected'
            vendor.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(vendor)
            
            # Send rejection notification
            self._send_vendor_notification(vendor, 'rejected', reason)
            
            logger.info(f"✅ Rejected vendor: {vendor.company_name}")
            return vendor
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error rejecting vendor: {str(e)}")
            raise Exception(f"Gagal reject vendor: {str(e)}")
    
    def suspend_vendor(self, vendor_id: int, suspended_by: int, reason: str) -> Optional[Vendor]:
        """Suspend vendor"""
        try:
            vendor = self.get_vendor_by_id(vendor_id)
            if not vendor:
                return None
            
            vendor.status = 'suspended'
            vendor.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(vendor)
            
            # Send suspension notification
            self._send_vendor_notification(vendor, 'suspended', reason)
            
            logger.info(f"✅ Suspended vendor: {vendor.company_name}")
            return vendor
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error suspending vendor: {str(e)}")
            raise Exception(f"Gagal suspend vendor: {str(e)}")
    
    # ===== VENDOR CATEGORIES =====
    
    def add_vendor_category(self, vendor_id: int, category_id: int) -> Optional[VendorCategory]:
        """Tambah kategori untuk vendor"""
        try:
            vendor = self.get_vendor_by_id(vendor_id)
            if not vendor:
                return None
            
            # Check if category already exists
            existing = self.db.query(VendorCategory).filter(
                VendorCategory.vendor_id == vendor_id,
                VendorCategory.category_id == category_id
            ).first()
            
            if existing:
                raise Exception("Kategori sudah ada untuk vendor ini")
            
            vendor_category = VendorCategory(
                vendor_id=vendor_id,
                category_id=category_id
            )
            
            self.db.add(vendor_category)
            self.db.commit()
            self.db.refresh(vendor_category)
            
            logger.info(f"✅ Added category to vendor: {vendor.company_name}")
            return vendor_category
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error adding vendor category: {str(e)}")
            raise Exception(f"Gagal tambah kategori vendor: {str(e)}")
    
    def remove_vendor_category(self, vendor_id: int, category_id: int) -> bool:
        """Hapus kategori dari vendor"""
        try:
            vendor_category = self.db.query(VendorCategory).filter(
                VendorCategory.vendor_id == vendor_id,
                VendorCategory.category_id == category_id
            ).first()
            
            if not vendor_category:
                return False
            
            self.db.delete(vendor_category)
            self.db.commit()
            
            logger.info(f"✅ Removed category from vendor: {vendor_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error removing vendor category: {str(e)}")
            raise Exception(f"Gagal hapus kategori vendor: {str(e)}")
    
    def get_vendor_categories(self, vendor_id: int) -> List[VendorCategory]:
        """Mendapatkan kategori vendor"""
        return self.db.query(VendorCategory).filter(VendorCategory.vendor_id == vendor_id).all()
    
    # ===== FILE UPLOAD =====
    
    def upload_penawaran_file(self, vendor_id: int, request_id: int, file, file_data: Dict[str, Any]) -> Optional[VendorPenawaranFile]:
        """Upload file penawaran vendor"""
        try:
            vendor = self.get_vendor_by_id(vendor_id)
            if not vendor:
                raise Exception("Vendor tidak ditemukan")
            
            if vendor.status != 'approved':
                raise Exception("Vendor belum disetujui")
            
            # Validate file
            if not self._validate_file(file):
                raise Exception("File tidak valid")
            
            # Check upload limits
            if not self._check_upload_limits(vendor_id, request_id):
                raise Exception("Batas upload file terlampaui")
            
            # Generate reference ID
            reference_id = self._generate_file_reference_id()
            
            # Save file
            file_path = self._save_file(file, vendor_id, request_id, reference_id)
            
            # Create vendor penawaran if not exists
            penawaran = self._get_or_create_penawaran(vendor_id, request_id)
            
            # Create file record
            file_record = VendorPenawaranFile(
                vendor_penawaran_id=penawaran.id,
                reference_id=reference_id,
                file_name=secure_filename(file.filename),
                file_path=file_path,
                file_type=file.content_type,
                file_size=len(file.read())
            )
            
            file.seek(0)  # Reset file pointer
            
            self.db.add(file_record)
            self.db.commit()
            self.db.refresh(file_record)
            
            # Log upload
            self._log_file_upload(vendor_id, request_id, file_record, 'success')
            
            logger.info(f"✅ Uploaded file: {file_record.file_name} for vendor: {vendor.company_name}")
            return file_record
            
        except Exception as e:
            self.db.rollback()
            self._log_file_upload(vendor_id, request_id, None, 'failed', str(e))
            logger.error(f"❌ Error uploading file: {str(e)}")
            raise Exception(f"Gagal upload file: {str(e)}")
    
    def get_penawaran_files(self, vendor_id: int, request_id: int) -> List[VendorPenawaranFile]:
        """Mendapatkan file penawaran vendor"""
        penawaran = self.db.query(VendorPenawaran).filter(
            VendorPenawaran.vendor_id == vendor_id,
            VendorPenawaran.request_id == request_id
        ).first()
        
        if not penawaran:
            return []
        
        return self.db.query(VendorPenawaranFile).filter(
            VendorPenawaranFile.vendor_penawaran_id == penawaran.id
        ).all()
    
    def delete_penawaran_file(self, file_id: int, vendor_id: int) -> bool:
        """Hapus file penawaran"""
        try:
            file_record = self.db.query(VendorPenawaranFile).filter(
                VendorPenawaranFile.id == file_id
            ).first()
            
            if not file_record:
                return False
            
            # Check if vendor owns this file
            penawaran = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.id == file_record.vendor_penawaran_id,
                VendorPenawaran.vendor_id == vendor_id
            ).first()
            
            if not penawaran:
                raise Exception("File tidak ditemukan atau tidak memiliki akses")
            
            # Delete physical file
            if os.path.exists(file_record.file_path):
                os.remove(file_record.file_path)
            
            # Delete database record
            self.db.delete(file_record)
            self.db.commit()
            
            logger.info(f"✅ Deleted file: {file_record.file_name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error deleting file: {str(e)}")
            raise Exception(f"Gagal hapus file: {str(e)}")
    
    def get_file_by_id(self, file_id: int) -> Optional[VendorPenawaranFile]:
        """Mendapatkan file berdasarkan ID"""
        return self.db.query(VendorPenawaranFile).filter(
            VendorPenawaranFile.id == file_id
        ).first()
    
    # ===== VENDOR PENAWARAN =====
    
    def create_penawaran(self, vendor_id: int, request_id: int, penawaran_data: Dict[str, Any]) -> Optional[VendorPenawaran]:
        """Buat penawaran vendor"""
        try:
            vendor = self.get_vendor_by_id(vendor_id)
            if not vendor:
                raise Exception("Vendor tidak ditemukan")
            
            if vendor.status != 'approved':
                raise Exception("Vendor belum disetujui")
            
            # Check if penawaran already exists
            existing = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.vendor_id == vendor_id,
                VendorPenawaran.request_id == request_id
            ).first()
            
            if existing:
                raise Exception("Penawaran sudah ada untuk request ini")
            
            # Generate reference ID
            reference_id = self._generate_penawaran_reference_id()
            
            penawaran = VendorPenawaran(
                request_id=request_id,
                vendor_id=vendor_id,
                reference_id=reference_id,
                total_quoted_price=penawaran_data.get('total_quoted_price'),
                delivery_time_days=penawaran_data.get('delivery_time_days'),
                payment_terms=penawaran_data.get('payment_terms'),
                quality_rating=penawaran_data.get('quality_rating'),
                notes=penawaran_data.get('notes', ''),
                status='submitted'
            )
            
            self.db.add(penawaran)
            self.db.commit()
            self.db.refresh(penawaran)
            
            logger.info(f"✅ Created penawaran: {reference_id} for vendor: {vendor.company_name}")
            return penawaran
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating penawaran: {str(e)}")
            raise Exception(f"Gagal buat penawaran: {str(e)}")
    
    def update_penawaran(self, penawaran_id: int, vendor_id: int, update_data: Dict[str, Any]) -> Optional[VendorPenawaran]:
        """Update penawaran vendor"""
        try:
            penawaran = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.id == penawaran_id,
                VendorPenawaran.vendor_id == vendor_id
            ).first()
            
            if not penawaran:
                return None
            
            if penawaran.status not in ['submitted']:
                raise Exception("Penawaran tidak dapat diupdate")
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(penawaran, field) and field not in ['id', 'created_at', 'reference_id']:
                    setattr(penawaran, field, value)
            
            penawaran.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(penawaran)
            
            logger.info(f"✅ Updated penawaran: {penawaran.reference_id}")
            return penawaran
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating penawaran: {str(e)}")
            raise Exception(f"Gagal update penawaran: {str(e)}")
    
    def get_penawaran_by_vendor(self, vendor_id: int, request_id: int) -> Optional[VendorPenawaran]:
        """Mendapatkan penawaran vendor untuk request tertentu"""
        return self.db.query(VendorPenawaran).filter(
            VendorPenawaran.vendor_id == vendor_id,
            VendorPenawaran.request_id == request_id
        ).first()
    
    def get_vendor_penawarans(self, vendor_id: int, status: str = None) -> List[VendorPenawaran]:
        """Mendapatkan semua penawaran vendor"""
        query = self.db.query(VendorPenawaran).filter(VendorPenawaran.vendor_id == vendor_id)
        
        if status:
            query = query.filter(VendorPenawaran.status == status)
        
        return query.order_by(desc(VendorPenawaran.created_at)).all()
    
    # ===== HELPER METHODS =====
    
    def _get_upload_config(self) -> UploadConfig:
        """Get upload configuration"""
        config = self.db.query(UploadConfig).first()
        if not config:
            # Create default config
            config = UploadConfig(
                max_files_per_vendor=5,
                max_size_per_file_mb=10,
                allowed_formats='["pdf", "doc", "docx", "xls", "xlsx", "jpg", "png"]'
            )
            self.db.add(config)
            self.db.commit()
        return config
    
    def _validate_file(self, file) -> bool:
        """Validate uploaded file"""
        if not file or not file.filename:
            return False
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size = self.upload_config.max_size_per_file_mb * 1024 * 1024
        if file_size > max_size:
            return False
        
        # Check file extension
        import json
        allowed_formats = json.loads(self.upload_config.allowed_formats)
        file_ext = file.filename.split('.')[-1].lower()
        
        return file_ext in allowed_formats
    
    def _check_upload_limits(self, vendor_id: int, request_id: int) -> bool:
        """Check upload limits"""
        penawaran = self._get_or_create_penawaran(vendor_id, request_id)
        file_count = self.db.query(VendorPenawaranFile).filter(
            VendorPenawaranFile.vendor_penawaran_id == penawaran.id
        ).count()
        
        return file_count < self.upload_config.max_files_per_vendor
    
    def _save_file(self, file, vendor_id: int, request_id: int, reference_id: str) -> str:
        """Save file to disk"""
        # Create directory structure
        upload_dir = f"uploads/vendor_penawaran/{datetime.now().year}/{datetime.now().month:02d}/{vendor_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate filename
        file_ext = file.filename.split('.')[-1].lower()
        filename = f"{reference_id}.{file_ext}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        file.save(file_path)
        
        return file_path
    
    def _get_or_create_penawaran(self, vendor_id: int, request_id: int) -> VendorPenawaran:
        """Get or create vendor penawaran"""
        penawaran = self.db.query(VendorPenawaran).filter(
            VendorPenawaran.vendor_id == vendor_id,
            VendorPenawaran.request_id == request_id
        ).first()
        
        if not penawaran:
            reference_id = self._generate_penawaran_reference_id()
            penawaran = VendorPenawaran(
                request_id=request_id,
                vendor_id=vendor_id,
                reference_id=reference_id,
                status='submitted'
            )
            self.db.add(penawaran)
            self.db.commit()
            self.db.refresh(penawaran)
        
        return penawaran
    
    def _generate_file_reference_id(self) -> str:
        """Generate unique file reference ID"""
        timestamp = datetime.now().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"FILE-{timestamp}-{unique_id}"
    
    def _generate_penawaran_reference_id(self) -> str:
        """Generate unique penawaran reference ID"""
        timestamp = datetime.now().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"PEN-{timestamp}-{unique_id}"
    
    def _log_file_upload(self, vendor_id: int, request_id: int, file_record: VendorPenawaranFile, status: str, error_message: str = None):
        """Log file upload"""
        try:
            log = FileUploadLog(
                vendor_id=vendor_id,
                request_id=request_id,
                file_name=file_record.file_name if file_record else 'unknown',
                file_size=file_record.file_size if file_record else 0,
                file_path=file_record.file_path if file_record else '',
                upload_status=status,
                error_message=error_message
            )
            
            self.db.add(log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"❌ Error logging file upload: {str(e)}")
    
    def _send_vendor_notification(self, vendor: Vendor, notification_type: str, message: str = None):
        """Send notification to vendor"""
        try:
            notification = VendorNotification(
                vendor_id=vendor.id,
                notification_type=notification_type,
                subject=f"Status Vendor: {notification_type.title()}",
                message=message or f"Status vendor Anda telah diubah menjadi {notification_type}",
                status='sent'
            )
            
            self.db.add(notification)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"❌ Error sending vendor notification: {str(e)}")
    
    # ===== STATISTICS =====
    
    def get_vendor_statistics(self) -> Dict[str, Any]:
        """Get vendor statistics"""
        try:
            vendors = self.db.query(Vendor).all()
            
            stats = {
                'total_vendors': len(vendors),
                'by_status': {},
                'by_category': {},
                'approved_vendors': 0,
                'pending_vendors': 0,
                'rejected_vendors': 0,
                'suspended_vendors': 0
            }
            
            for vendor in vendors:
                # Status count
                status = vendor.status
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # Category count
                category = vendor.vendor_category
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
                
                # Specific counts
                if status == 'approved':
                    stats['approved_vendors'] += 1
                elif status == 'pending':
                    stats['pending_vendors'] += 1
                elif status == 'rejected':
                    stats['rejected_vendors'] += 1
                elif status == 'suspended':
                    stats['suspended_vendors'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor statistics: {str(e)}")
            raise Exception(f"Gagal mendapatkan statistik vendor: {str(e)}")
    
    # ===== KTP FILE UPLOAD =====
    
    def upload_ktp_file(self, vendor_id: int, ktp_data: Dict[str, Any], file) -> bool:
        """Upload KTP file untuk vendor"""
        try:
            vendor = self.get_vendor_by_id(vendor_id)
            if not vendor:
                raise Exception("Vendor tidak ditemukan")
            
            # Validate file
            if not self._validate_ktp_file(file):
                raise Exception("File KTP tidak valid")
            
            # Save file
            file_path = self._save_ktp_file(file, vendor_id)
            
            # Update vendor record
            vendor.ktp_director_name = ktp_data.get('ktp_director_name')
            vendor.ktp_director_number = ktp_data.get('ktp_director_number')
            vendor.ktp_director_file_path = file_path
            vendor.ktp_director_file_name = secure_filename(file.filename)
            vendor.ktp_director_file_size = len(file.read())
            vendor.ktp_director_upload_date = datetime.utcnow()
            
            file.seek(0)  # Reset file pointer
            
            self.db.commit()
            
            logger.info(f"✅ KTP file uploaded for vendor {vendor_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error uploading KTP file: {str(e)}")
            raise e
    
    def _validate_ktp_file(self, file) -> bool:
        """Validate KTP file"""
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
        max_size = 5 * 1024 * 1024  # 5MB
        
        if file.content_type not in allowed_types:
            return False
        
        # Check file size without consuming the file content
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()  # Get file size
        file.seek(0)  # Reset to beginning
        
        if file_size > max_size:
            return False
        
        return True
    
    def _save_ktp_file(self, file, vendor_id: int) -> str:
        """Save KTP file to disk"""
        upload_dir = f"uploads/vendor_ktp/{datetime.now().year}/{datetime.now().month:02d}/{vendor_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_ext = file.filename.split('.')[-1].lower()
        filename = f"ktp_{vendor_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
        file_path = os.path.join(upload_dir, filename)
        
        file.save(file_path)
        return file_path
    
    # ===== VENDOR ATTACHMENT FILES UPLOAD =====
    
    def upload_vendor_attachments(self, vendor_id: int, attachment_files: Dict[str, Any]) -> bool:
        """Upload multiple attachment files untuk vendor"""
        try:
            logger.info(f"🔍 Starting attachment upload service for vendor {vendor_id}")
            logger.info(f"📦 Attachment files received: {list(attachment_files.keys())}")
            
            vendor = self.get_vendor_by_id(vendor_id)
            if not vendor:
                raise Exception("Vendor tidak ditemukan")
            
            # Process each attachment file
            for attachment_type, file_data in attachment_files.items():
                logger.info(f"📄 Processing {attachment_type}")
                
                if file_data and file_data.get('file'):
                    file = file_data['file']
                    logger.info(f"📁 File info: {file.filename}, {file.content_type}")
                    
                    # Validate file
                    if not self._validate_attachment_file(file):
                        logger.error(f"❌ File {attachment_type} validation failed")
                        raise Exception(f"File {attachment_type} tidak valid")
                    
                    # Save file
                    file_path = self._save_attachment_file(file, vendor_id, attachment_type)
                    logger.info(f"💾 File saved to: {file_path}")
                    
                    # Update vendor record based on attachment type
                    self._update_vendor_attachment_field(vendor, attachment_type, file, file_path)
                    logger.info(f"✅ {attachment_type} field updated")
                else:
                    logger.warning(f"⚠️ No file data for {attachment_type}")
            
            self.db.commit()
            logger.info(f"✅ Attachment files uploaded for vendor {vendor_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error uploading attachment files: {str(e)}")
            raise e
    
    def _validate_attachment_file(self, file) -> bool:
        """Validate attachment file"""
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
        max_size = 10 * 1024 * 1024  # 10MB
        
        logger.info(f"🔍 Validating file: {file.filename}, type: {file.content_type}")
        
        if file.content_type not in allowed_types:
            logger.error(f"❌ Invalid file type: {file.content_type}, allowed: {allowed_types}")
            return False
        
        # Check file size without consuming the file content
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()  # Get file size
        file.seek(0)  # Reset to beginning
        
        logger.info(f"📏 File size: {file_size} bytes, max allowed: {max_size} bytes")
        
        if file_size > max_size:
            logger.error(f"❌ File too large: {file_size} > {max_size}")
            return False
        
        logger.info(f"✅ File validation passed")
        return True
    
    def _save_attachment_file(self, file, vendor_id: int, attachment_type: str) -> str:
        """Save attachment file to disk"""
        upload_dir = f"uploads/vendor_attachments/{datetime.now().year}/{datetime.now().month:02d}/{vendor_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_ext = file.filename.split('.')[-1].lower()
        filename = f"{attachment_type}_{vendor_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
        file_path = os.path.join(upload_dir, filename)
        
        file.save(file_path)
        return file_path
    
    def _update_vendor_attachment_field(self, vendor, attachment_type: str, file, file_path: str):
        """Update vendor record with attachment file info"""
        logger.info(f"🔧 Updating vendor field for {attachment_type}")
        
        current_time = datetime.utcnow()
        # Get file size without consuming the file content
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()  # Get file size
        file.seek(0)  # Reset to beginning
        
        logger.info(f"📊 File size: {file_size}, filename: {file.filename}")
        
        if attachment_type == 'akta_perusahaan':
            vendor.akta_perusahaan_file_path = file_path
            vendor.akta_perusahaan_file_name = secure_filename(file.filename)
            vendor.akta_perusahaan_file_size = file_size
            vendor.akta_perusahaan_upload_date = current_time
            logger.info(f"✅ Updated akta_perusahaan fields")
            
        elif attachment_type == 'nib':
            vendor.nib_file_path = file_path
            vendor.nib_file_name = secure_filename(file.filename)
            vendor.nib_file_size = file_size
            vendor.nib_upload_date = current_time
            logger.info(f"✅ Updated nib fields")
            
        elif attachment_type == 'npwp':
            vendor.npwp_file_path = file_path
            vendor.npwp_file_name = secure_filename(file.filename)
            vendor.npwp_file_size = file_size
            vendor.npwp_upload_date = current_time
            logger.info(f"✅ Updated npwp fields")
            
        elif attachment_type == 'company_profile':
            vendor.company_profile_file_path = file_path
            vendor.company_profile_file_name = secure_filename(file.filename)
            vendor.company_profile_file_size = file_size
            vendor.company_profile_upload_date = current_time
            logger.info(f"✅ Updated company_profile fields")
            
        elif attachment_type == 'surat_keagenan':
            vendor.surat_keagenan_file_path = file_path
            vendor.surat_keagenan_file_name = secure_filename(file.filename)
            vendor.surat_keagenan_file_size = file_size
            vendor.surat_keagenan_upload_date = current_time
            logger.info(f"✅ Updated surat_keagenan fields")
            
        elif attachment_type == 'tkdn':
            vendor.tkdn_file_path = file_path
            vendor.tkdn_file_name = secure_filename(file.filename)
            vendor.tkdn_file_size = file_size
            vendor.tkdn_upload_date = current_time
            logger.info(f"✅ Updated tkdn fields")
            
        elif attachment_type == 'surat_pernyataan_manufaktur':
            vendor.surat_pernyataan_manufaktur_file_path = file_path
            vendor.surat_pernyataan_manufaktur_file_name = secure_filename(file.filename)
            vendor.surat_pernyataan_manufaktur_file_size = file_size
            vendor.surat_pernyataan_manufaktur_upload_date = current_time
            logger.info(f"✅ Updated surat_pernyataan_manufaktur fields")
        else:
            logger.warning(f"⚠️ Unknown attachment type: {attachment_type}")