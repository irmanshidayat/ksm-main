#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Authentication Service - Business Logic untuk Sistem Vendor Authentication
Service untuk mengelola vendor login, user integration, dan authentication
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, Dict, Any
from datetime import datetime
import logging
from werkzeug.security import generate_password_hash, check_password_hash

from domains.auth.models.auth_models import User
from domains.vendor.models.vendor_models import Vendor, VendorCategory, VendorPenawaran, VendorPenawaranFile
from domains.auth.services.jwt_service import JWTService

logger = logging.getLogger(__name__)


class VendorAuthService:
    """Service untuk mengelola vendor authentication"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_vendor_user_account(self, vendor: Vendor, password: str) -> User:
        """Membuat user account untuk vendor"""
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                or_(User.username == vendor.email, User.email == vendor.email)
            ).first()
            
            if existing_user:
                raise Exception("User account sudah ada untuk email ini")
            
            # Create user account
            user = User(
                username=vendor.email,  # Email sebagai username
                email=vendor.email,
                password_hash=generate_password_hash(password),
                role='vendor',
                is_active=True,
                vendor_id=vendor.id
            )
            
            self.db.add(user)
            self.db.flush()  # Get ID without committing
            
            # Update vendor dengan user_id
            vendor.user_id = user.id
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"✅ Created user account for vendor: {vendor.company_name} (ID: {vendor.id})")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating vendor user account: {str(e)}")
            raise Exception(f"Gagal membuat user account vendor: {str(e)}")
    
    def authenticate_vendor(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate vendor dengan email dan password"""
        try:
            # Find user by email (username)
            user = self.db.query(User).filter(
                and_(
                    User.username == email,
                    User.role == 'vendor',
                    User.is_active == True
                )
            ).first()
            
            if not user:
                logger.warning(f"❌ Vendor login failed: User {email} not found")
                return None
            
            # Verify password
            if not check_password_hash(user.password_hash, password):
                logger.warning(f"❌ Vendor login failed: Invalid password for {email}")
                return None
            
            # Get vendor information
            vendor = self.db.query(Vendor).filter(Vendor.id == user.vendor_id).first()
            if not vendor:
                logger.error(f"❌ Vendor not found for user {email}")
                return None
            
            # Check vendor status - allow pending vendors to login for self-registration
            if vendor.status not in ['approved', 'pending']:
                logger.warning(f"❌ Vendor login failed: Vendor {email} status is {vendor.status}")
                return None
            
            # Create JWT tokens
            token_data = JWTService.create_tokens(
                user_id=str(user.id),
                username=user.username,
                role=user.role
            )
            
            # Log token usage
            JWTService.log_token_usage(user.id, user.username, 'vendor_login')
            
            # Update last login
            user.last_login = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"✅ Vendor login successful: {vendor.company_name} ({email})")
            
            return {
                'user': user.to_dict(),
                'vendor': vendor.to_dict(),
                'tokens': token_data,
                'permissions': self._get_vendor_permissions()
            }
            
        except Exception as e:
            logger.error(f"❌ Error authenticating vendor: {str(e)}")
            return None
    
    def get_vendor_by_user_id(self, user_id: int) -> Optional[Vendor]:
        """Mendapatkan vendor berdasarkan user_id"""
        try:
            user = self.db.query(User).filter(
                and_(
                    User.id == user_id,
                    User.role == 'vendor',
                    User.is_active == True
                )
            ).first()
            
            if not user or not user.vendor_id:
                return None
            
            vendor = self.db.query(Vendor).filter(Vendor.id == user.vendor_id).first()
            return vendor
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor by user_id: {str(e)}")
            return None
    
    def get_vendor_categories(self, vendor_id: int) -> list:
        """Mendapatkan kategori vendor"""
        try:
            categories = self.db.query(VendorCategory).filter(
                VendorCategory.vendor_id == vendor_id
            ).all()
            
            return [category.to_dict() for category in categories]
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor categories: {str(e)}")
            return []
    
    def get_vendor_penawaran_history(self, vendor_id: int, limit: int = 50) -> list:
        """Mendapatkan riwayat penawaran vendor"""
        try:
            penawarans = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.vendor_id == vendor_id
            ).order_by(VendorPenawaran.created_at.desc()).limit(limit).all()
            
            return [penawaran.to_dict() for penawaran in penawarans]
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor penawaran history: {str(e)}")
            return []
    
    def get_vendor_penawaran_history_paginated(self, vendor_id: int, page: int = 1, limit: int = 10, status_filter: str = 'all') -> dict:
        """Mendapatkan riwayat penawaran vendor dengan pagination dan filtering"""
        try:
            from domains.vendor.models.vendor_models import VendorPenawaran
            from domains.inventory.models.request_pembelian_models import RequestPembelian
            from sqlalchemy import func
            
            # Base query
            query = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.vendor_id == vendor_id
            )
            
            # Apply status filter
            if status_filter != 'all':
                query = query.filter(VendorPenawaran.status == status_filter)
            
            # Get total count
            total_count = query.count()
            
            # Calculate pagination
            total_pages = (total_count + limit - 1) // limit
            offset = (page - 1) * limit
            
            # Get paginated results
            penawarans = query.order_by(VendorPenawaran.created_at.desc()).offset(offset).limit(limit).all()
            
            # Format results with additional data
            formatted_penawarans = []
            for penawaran in penawarans:
                penawaran_dict = penawaran.to_dict()
                
                # Get request details
                request = self.db.query(RequestPembelian).filter(
                    RequestPembelian.id == penawaran.request_id
                ).first()
                
                if request:
                    penawaran_dict.update({
                        'request_title': request.title,
                        'request_description': request.description,
                        'reference_id': request.reference_id
                    })
                
                # Get files count
                files_count = self.db.query(VendorPenawaranFile).filter(
                    VendorPenawaranFile.penawaran_id == penawaran.id
                ).count()
                penawaran_dict['files_count'] = files_count
                
                formatted_penawarans.append(penawaran_dict)
            
            # Calculate success rate
            success_count = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.vendor_id == vendor_id,
                VendorPenawaran.status == 'selected'
            ).count()
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            return {
                'penawaran': formatted_penawarans,
                'total_count': total_count,
                'total_pages': total_pages,
                'success_rate': round(success_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor penawaran history paginated: {str(e)}")
            return {
                'penawaran': [],
                'total_count': 0,
                'total_pages': 0,
                'success_rate': 0
            }
    
    def update_vendor_profile(self, vendor_id: int, profile_data: Dict[str, Any]) -> Optional[Vendor]:
        """Update profil vendor"""
        try:
            vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
            if not vendor:
                return None
            
            # Update allowed fields
            allowed_fields = [
                'contact_person', 'phone', 'address', 
                'business_license', 'tax_id', 'bank_account'
            ]
            
            for field in allowed_fields:
                if field in profile_data:
                    setattr(vendor, field, profile_data[field])
            
            vendor.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(vendor)
            
            logger.info(f"✅ Updated vendor profile: {vendor.company_name} (ID: {vendor.id})")
            return vendor
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating vendor profile: {str(e)}")
            return None
    
    def _get_vendor_permissions(self) -> list:
        """Mendapatkan permissions untuk vendor"""
        return [
            'upload_file',
            'view_own_files',
            'view_own_penawaran',
            'update_profile',
            'view_requests',
            'download_templates'
        ]
    
    def validate_vendor_access(self, user_id: int, vendor_id: int) -> bool:
        """Validasi apakah user memiliki akses ke vendor"""
        try:
            user = self.db.query(User).filter(
                and_(
                    User.id == user_id,
                    User.role == 'vendor',
                    User.vendor_id == vendor_id,
                    User.is_active == True
                )
            ).first()
            
            return user is not None
            
        except Exception as e:
            logger.error(f"❌ Error validating vendor access: {str(e)}")
            return False
