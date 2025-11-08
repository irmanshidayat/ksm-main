#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Approval Service - Business Logic untuk Sistem Vendor Approval Management
Service untuk mengelola approval workflow yang berbeda untuk vendor internal dan mitra
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from models.request_pembelian_models import Vendor, VendorNotification
from models.notification_models import Notification

logger = logging.getLogger(__name__)


class VendorApprovalService:
    """Service untuk mengelola approval workflow vendor"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_approval_requirements(self, vendor_type: str, business_model: str) -> Dict[str, Any]:
        """Mendapatkan requirements approval berdasarkan vendor type dan business model"""
        requirements = {
            'internal': {
                'supplier': {
                    'required_documents': ['business_license', 'tax_id'],
                    'approval_levels': ['admin'],
                    'legal_review': False,
                    'financial_review': False,
                    'compliance_check': False
                }
            },
            'partner': {
                'supplier': {
                    'required_documents': ['business_license', 'tax_id', 'bank_account'],
                    'approval_levels': ['admin', 'legal'],
                    'legal_review': True,
                    'financial_review': True,
                    'compliance_check': True
                },
                'reseller': {
                    'required_documents': ['business_license', 'tax_id', 'bank_account', 'reseller_agreement'],
                    'approval_levels': ['admin', 'legal', 'finance'],
                    'legal_review': True,
                    'financial_review': True,
                    'compliance_check': True,
                    'reseller_agreement_required': True
                },
                'both': {
                    'required_documents': ['business_license', 'tax_id', 'bank_account', 'reseller_agreement'],
                    'approval_levels': ['admin', 'legal', 'finance'],
                    'legal_review': True,
                    'financial_review': True,
                    'compliance_check': True,
                    'reseller_agreement_required': True
                }
            }
        }
        
        return requirements.get(vendor_type, {}).get(business_model, requirements['internal']['supplier'])
    
    def validate_vendor_approval_requirements(self, vendor_id: int) -> Dict[str, Any]:
        """Validasi requirements untuk approval vendor"""
        try:
            vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
            if not vendor:
                return {
                    'success': False,
                    'message': 'Vendor tidak ditemukan'
                }
            
            requirements = self.get_approval_requirements(vendor.vendor_type, vendor.business_model)
            missing_requirements = []
            
            # Check required documents
            if 'business_license' in requirements['required_documents'] and not vendor.business_license:
                missing_requirements.append('Nomor NIB')
            
            if 'tax_id' in requirements['required_documents'] and not vendor.tax_id:
                missing_requirements.append('NPWP')
            
            if 'bank_account' in requirements['required_documents'] and not vendor.bank_account:
                missing_requirements.append('Nomor Rekening')
            
            # Check reseller agreement for reseller/both business models
            if requirements.get('reseller_agreement_required', False):
                # This would need to be implemented based on your document storage system
                # For now, we'll assume it's handled separately
                pass
            
            return {
                'success': True,
                'requirements_met': len(missing_requirements) == 0,
                'missing_requirements': missing_requirements,
                'requirements': requirements
            }
            
        except Exception as e:
            logger.error(f"❌ Error validating vendor approval requirements: {str(e)}")
            return {
                'success': False,
                'message': f'Gagal validasi requirements: {str(e)}'
            }
    
    def create_approval_workflow(self, vendor_id: int, created_by_user_id: int) -> Dict[str, Any]:
        """Membuat approval workflow untuk vendor"""
        try:
            vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
            if not vendor:
                return {
                    'success': False,
                    'message': 'Vendor tidak ditemukan'
                }
            
            requirements = self.get_approval_requirements(vendor.vendor_type, vendor.business_model)
            
            # Create notifications for each approval level
            notifications = []
            
            for level in requirements['approval_levels']:
                notification = Notification(
                    user_id=created_by_user_id,  # This should be mapped to actual approver user IDs
                    title=f"Vendor Approval Required - {vendor.company_name}",
                    message=f"Vendor {vendor.company_name} ({vendor.vendor_type}/{vendor.business_model}) memerlukan approval dari {level}",
                    type='vendor_approval',
                    priority='medium',
                    data={
                        'vendor_id': vendor_id,
                        'vendor_type': vendor.vendor_type,
                        'business_model': vendor.business_model,
                        'approval_level': level,
                        'requirements': requirements
                    }
                )
                self.db.add(notification)
                notifications.append(notification)
            
            # Create vendor notification
            vendor_notification = VendorNotification(
                vendor_id=vendor_id,
                title="Approval Workflow Started",
                message=f"Approval workflow telah dimulai untuk vendor {vendor.company_name}",
                type='approval_workflow',
                status='pending'
            )
            self.db.add(vendor_notification)
            
            self.db.commit()
            
            logger.info(f"✅ Created approval workflow for vendor {vendor.company_name} (ID: {vendor_id})")
            return {
                'success': True,
                'message': 'Approval workflow berhasil dibuat',
                'notifications_created': len(notifications),
                'requirements': requirements
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating approval workflow: {str(e)}")
            return {
                'success': False,
                'message': f'Gagal membuat approval workflow: {str(e)}'
            }
    
    def approve_vendor(self, vendor_id: int, approved_by_user_id: int, approval_level: str, notes: str = None) -> Dict[str, Any]:
        """Approve vendor pada level tertentu"""
        try:
            vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
            if not vendor:
                return {
                    'success': False,
                    'message': 'Vendor tidak ditemukan'
                }
            
            requirements = self.get_approval_requirements(vendor.vendor_type, vendor.business_model)
            
            # Check if this approval level is required
            if approval_level not in requirements['approval_levels']:
                return {
                    'success': False,
                    'message': f'Approval level {approval_level} tidak diperlukan untuk vendor ini'
                }
            
            # Update vendor status based on approval level
            if approval_level == 'admin':
                vendor.status = 'approved'
                vendor.approved_date = datetime.utcnow()
            elif approval_level in ['legal', 'finance']:
                # For partner vendors, we might need multiple approvals
                # This is a simplified implementation
                pass
            
            # Create notification
            notification = Notification(
                user_id=approved_by_user_id,
                title=f"Vendor Approved - {vendor.company_name}",
                message=f"Vendor {vendor.company_name} telah di-approve oleh {approval_level}",
                type='vendor_approved',
                priority='low',
                data={
                    'vendor_id': vendor_id,
                    'approval_level': approval_level,
                    'notes': notes
                }
            )
            self.db.add(notification)
            
            # Create vendor notification
            vendor_notification = VendorNotification(
                vendor_id=vendor_id,
                title=f"Approved by {approval_level}",
                message=f"Vendor telah di-approve oleh {approval_level}",
                type='approval_update',
                status='approved'
            )
            self.db.add(vendor_notification)
            
            self.db.commit()
            
            logger.info(f"✅ Vendor {vendor.company_name} approved by {approval_level}")
            return {
                'success': True,
                'message': f'Vendor berhasil di-approve oleh {approval_level}',
                'vendor_status': vendor.status
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error approving vendor: {str(e)}")
            return {
                'success': False,
                'message': f'Gagal approve vendor: {str(e)}'
            }
    
    def get_pending_approvals(self, approval_level: str = None) -> List[Dict[str, Any]]:
        """Mendapatkan daftar vendor yang pending approval"""
        try:
            query = self.db.query(Vendor).filter(Vendor.status == 'pending')
            
            if approval_level:
                # Filter based on approval level requirements
                # This is a simplified implementation
                pass
            
            vendors = query.all()
            
            result = []
            for vendor in vendors:
                requirements = self.get_approval_requirements(vendor.vendor_type, vendor.business_model)
                validation = self.validate_vendor_approval_requirements(vendor.id)
                
                result.append({
                    'vendor': vendor.to_dict(),
                    'requirements': requirements,
                    'validation': validation
                })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting pending approvals: {str(e)}")
            return []
