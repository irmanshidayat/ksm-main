#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Request Pembelian Service - Business Logic untuk Sistem Request Pembelian Barang
Service untuk mengelola request pembelian, status management, dan integrasi dengan sistem lain
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from models import (
    RequestPembelian, RequestPembelianItem, VendorPenawaran, 
    VendorPenawaranFile, VendorAnalysis, Vendor, VendorCategory
)
from models import BudgetTracking, BudgetTransaction, RequestTimelineConfig
from models import Barang, StokBarang
from models import Department
from domains.approval.models.approval_models import ApprovalWorkflow, ApprovalRequest

logger = logging.getLogger(__name__)


class RequestPembelianService:
    """Service untuk mengelola request pembelian"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ===== REQUEST PEMBELIAN CRUD =====
    
    def create_request(self, request_data: Dict[str, Any]) -> RequestPembelian:
        """Membuat request pembelian baru"""
        try:
            # Generate reference ID and request number
            reference_id = self._generate_reference_id()
            request_number = self._generate_request_number()
            
            # Calculate timeline
            timeline = self._calculate_timeline(request_data.get('total_budget', 0))
            
            # Create request
            request = RequestPembelian(
                reference_id=reference_id,
                request_number=request_number,
                user_id=request_data['user_id'],
                department_id=request_data['department_id'],
                title=request_data['title'],
                description=request_data.get('description', ''),
                total_budget=request_data.get('total_budget'),
                required_date=request_data.get('required_date'),
                priority=request_data.get('priority', 'medium'),
                status='draft',
                vendor_upload_deadline=timeline['vendor_upload_deadline'],
                analysis_deadline=timeline['analysis_deadline'],
                approval_deadline=timeline['approval_deadline']
            )
            
            self.db.add(request)
            self.db.flush()  # Get ID without committing
            
            # Add items if provided
            if 'items' in request_data:
                for item_data in request_data['items']:
                    # Handle mapping from frontend format to database format
                    # Frontend sends: nama_barang, quantity, satuan, spesifikasi, estimated_price
                    # Database expects: barang_id, quantity, unit_price, total_price, specifications, notes
                    quantity = item_data.get('quantity', 1)
                    unit_price = item_data.get('estimated_price') or item_data.get('unit_price')
                    total_price = (unit_price * quantity) if unit_price else None
                    
                    item = RequestPembelianItem(
                        request_id=request.id,
                        barang_id=item_data.get('barang_id'),  # May be None if new item
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price,
                        specifications=item_data.get('spesifikasi') or item_data.get('specifications', ''),
                        notes=item_data.get('notes', '')
                    )
                    self.db.add(item)
            
            self.db.commit()
            self.db.refresh(request)
            
            logger.info(f"✅ Created request pembelian: {reference_id} (ID: {request.id})")
            return request
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating request pembelian: {str(e)}")
            raise Exception(f"Gagal membuat request pembelian: {str(e)}")
    
    def get_request_by_id(self, request_id: int) -> Optional[RequestPembelian]:
        """Mendapatkan request berdasarkan ID"""
        return self.db.query(RequestPembelian).filter(RequestPembelian.id == request_id).first()
    
    def get_request_by_reference(self, reference_id: str) -> Optional[RequestPembelian]:
        """Mendapatkan request berdasarkan reference ID"""
        return self.db.query(RequestPembelian).filter(RequestPembelian.reference_id == reference_id).first()
    
    def get_requests_by_user(self, user_id: int, status: str = None) -> List[RequestPembelian]:
        """Mendapatkan request berdasarkan user"""
        query = self.db.query(RequestPembelian).filter(RequestPembelian.user_id == user_id)
        
        if status:
            query = query.filter(RequestPembelian.status == status)
        
        return query.order_by(desc(RequestPembelian.created_at)).all()
    
    def get_requests_by_department(self, department_id: int, status: str = None) -> List[RequestPembelian]:
        """Mendapatkan request berdasarkan departemen"""
        query = self.db.query(RequestPembelian).filter(RequestPembelian.department_id == department_id)
        
        if status:
            query = query.filter(RequestPembelian.status == status)
        
        return query.order_by(desc(RequestPembelian.created_at)).all()
    
    def get_all_requests(self, filters: Dict[str, Any] = None, page: int = None, per_page: int = None) -> List[RequestPembelian]:
        """Mendapatkan semua request dengan filter dan pagination"""
        query = self.db.query(RequestPembelian)
        
        if filters:
            if 'status' in filters and filters['status']:
                if isinstance(filters['status'], list):
                    # Multiple status filter
                    query = query.filter(RequestPembelian.status.in_(filters['status']))
                else:
                    # Single status filter
                    query = query.filter(RequestPembelian.status == filters['status'])
            
            if 'priority' in filters and filters['priority']:
                query = query.filter(RequestPembelian.priority == filters['priority'])
            
            if 'department_id' in filters and filters['department_id']:
                query = query.filter(RequestPembelian.department_id == filters['department_id'])
            
            if 'user_id' in filters and filters['user_id']:
                query = query.filter(RequestPembelian.user_id == filters['user_id'])
            
            if 'date_from' in filters and filters['date_from']:
                query = query.filter(RequestPembelian.created_at >= filters['date_from'])
            
            if 'date_to' in filters and filters['date_to']:
                query = query.filter(RequestPembelian.created_at <= filters['date_to'])
            
            if 'search' in filters and filters['search']:
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        RequestPembelian.reference_id.ilike(search_term),
                        RequestPembelian.title.ilike(search_term),
                        RequestPembelian.description.ilike(search_term)
                    )
                )
        
        # Apply pagination if provided
        if page and per_page:
            offset = (page - 1) * per_page
            return query.order_by(desc(RequestPembelian.created_at)).offset(offset).limit(per_page).all()
        else:
            return query.order_by(desc(RequestPembelian.created_at)).all()
    
    def update_request(self, request_id: int, update_data: Dict[str, Any]) -> Optional[RequestPembelian]:
        """Update request pembelian"""
        try:
            request = self.get_request_by_id(request_id)
            if not request:
                return None
            
            # Check if request can be updated
            if request.status not in ['draft', 'submitted']:
                raise Exception("Request tidak dapat diupdate karena sudah diproses")
            
            # Handle items separately (if provided)
            items_data = update_data.pop('items', None)
            
            # Update fields (excluding items which is handled separately)
            for field, value in update_data.items():
                if hasattr(request, field) and field not in ['id', 'created_at', 'reference_id', 'items']:
                    setattr(request, field, value)
            
            # Update items if provided
            if items_data is not None:
                # Delete existing items
                self.db.query(RequestPembelianItem).filter(
                    RequestPembelianItem.request_id == request_id
                ).delete()
                
                # Create new items from provided data
                for item_data in items_data:
                    # Handle mapping from frontend format to database format
                    # Frontend sends: nama_barang, quantity, satuan, spesifikasi, estimated_price
                    # Database expects: barang_id, quantity, unit_price, total_price, specifications, notes
                    quantity = item_data.get('quantity', 1)
                    unit_price = item_data.get('estimated_price') or item_data.get('unit_price')
                    total_price = (unit_price * quantity) if unit_price else None
                    
                    item = RequestPembelianItem(
                        request_id=request.id,
                        barang_id=item_data.get('barang_id'),  # May be None if new item
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price,
                        specifications=item_data.get('spesifikasi') or item_data.get('specifications', ''),
                        notes=item_data.get('notes', '')
                    )
                    self.db.add(item)
            
            request.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(request)
            
            logger.info(f"✅ Updated request pembelian: {request.reference_id}")
            return request
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating request pembelian: {str(e)}")
            raise Exception(f"Gagal update request pembelian: {str(e)}")
    
    def delete_request(self, request_id: int) -> bool:
        """Hapus request pembelian (soft delete)"""
        try:
            request = self.get_request_by_id(request_id)
            if not request:
                return False
            
            # Check if request can be deleted
            if request.status not in ['draft']:
                raise Exception("Request tidak dapat dihapus karena sudah diproses")
            
            self.db.delete(request)
            self.db.commit()
            
            logger.info(f"✅ Deleted request pembelian: {request.reference_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error deleting request pembelian: {str(e)}")
            raise Exception(f"Gagal hapus request pembelian: {str(e)}")
    
    # ===== STATUS MANAGEMENT =====
    
    def submit_request(self, request_id: int) -> Optional[RequestPembelian]:
        """Submit request untuk approval"""
        try:
            request = self.get_request_by_id(request_id)
            if not request:
                return None
            
            if request.status != 'draft':
                raise Exception("Request sudah disubmit atau diproses")
            
            # Validate request
            if not request.items.count():
                raise Exception("Request harus memiliki minimal 1 item")
            
            # Update status
            request.status = 'submitted'
            request.updated_at = datetime.utcnow()
            
            # Create approval request
            self._create_approval_request(request)
            
            self.db.commit()
            self.db.refresh(request)
            
            logger.info(f"✅ Submitted request pembelian: {request.reference_id}")
            return request
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error submitting request pembelian: {str(e)}")
            raise Exception(f"Gagal submit request pembelian: {str(e)}")
    
    def start_vendor_upload(self, request_id: int) -> Optional[RequestPembelian]:
        """Mulai periode upload vendor"""
        try:
            request = self.get_request_by_id(request_id)
            if not request:
                return None
            
            if request.status != 'submitted':
                raise Exception("Request harus dalam status submitted")
            
            # Update status
            request.status = 'vendor_uploading'
            request.updated_at = datetime.utcnow()
            
            # Send notifications to vendors
            self._notify_vendors(request)
            
            self.db.commit()
            self.db.refresh(request)
            
            logger.info(f"✅ Started vendor upload for request: {request.reference_id}")
            return request
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error starting vendor upload: {str(e)}")
            raise Exception(f"Gagal mulai upload vendor: {str(e)}")
    
    def start_analysis(self, request_id: int) -> Optional[RequestPembelian]:
        """Mulai analisis vendor"""
        try:
            request = self.get_request_by_id(request_id)
            if not request:
                return None
            
            if request.status != 'vendor_uploading':
                raise Exception("Request harus dalam status vendor_uploading")
            
            # Check if there are vendor submissions
            if not request.vendor_penawarans.count():
                raise Exception("Belum ada penawaran vendor")
            
            # Update status
            request.status = 'under_analysis'
            request.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(request)
            
            logger.info(f"✅ Started analysis for request: {request.reference_id}")
            return request
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error starting analysis: {str(e)}")
            raise Exception(f"Gagal mulai analisis: {str(e)}")
    
    def approve_request(self, request_id: int, approved_by: int, notes: str = None) -> Optional[RequestPembelian]:
        """Approve request setelah analisis"""
        try:
            request = self.get_request_by_id(request_id)
            if not request:
                return None
            
            if request.status != 'under_analysis':
                raise Exception("Request harus dalam status under_analysis")
            
            # Update status
            request.status = 'approved'
            request.updated_at = datetime.utcnow()
            
            if notes:
                request.notes = notes
            
            self.db.commit()
            self.db.refresh(request)
            
            logger.info(f"✅ Approved request pembelian: {request.reference_id}")
            return request
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error approving request pembelian: {str(e)}")
            raise Exception(f"Gagal approve request pembelian: {str(e)}")
    
    def reject_request(self, request_id: int, rejected_by: int, reason: str) -> Optional[RequestPembelian]:
        """Reject request"""
        try:
            request = self.get_request_by_id(request_id)
            if not request:
                return None
            
            # Update status
            request.status = 'rejected'
            request.notes = reason
            request.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(request)
            
            logger.info(f"✅ Rejected request pembelian: {request.reference_id}")
            return request
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error rejecting request pembelian: {str(e)}")
            raise Exception(f"Gagal reject request pembelian: {str(e)}")
    
    # ===== ITEM MANAGEMENT =====
    
    def add_item(self, request_id: int, item_data: Dict[str, Any]) -> Optional[RequestPembelianItem]:
        """Tambah item ke request"""
        try:
            request = self.get_request_by_id(request_id)
            if not request:
                return None
            
            if request.status not in ['draft', 'submitted']:
                raise Exception("Request tidak dapat diupdate")
            
            item = RequestPembelianItem(
                request_id=request_id,
                barang_id=item_data['barang_id'],
                quantity=item_data['quantity'],
                unit_price=item_data.get('unit_price'),
                total_price=item_data.get('total_price'),
                specifications=item_data.get('specifications', ''),
                notes=item_data.get('notes', '')
            )
            
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            
            # Update total budget
            self._update_total_budget(request_id)
            
            logger.info(f"✅ Added item to request: {request.reference_id}")
            return item
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error adding item: {str(e)}")
            raise Exception(f"Gagal tambah item: {str(e)}")
    
    def update_item(self, item_id: int, update_data: Dict[str, Any]) -> Optional[RequestPembelianItem]:
        """Update item dalam request"""
        try:
            item = self.db.query(RequestPembelianItem).filter(RequestPembelianItem.id == item_id).first()
            if not item:
                return None
            
            request = self.get_request_by_id(item.request_id)
            if request.status not in ['draft', 'submitted']:
                raise Exception("Request tidak dapat diupdate")
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(item, field) and field not in ['id', 'request_id', 'created_at']:
                    setattr(item, field, value)
            
            item.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(item)
            
            # Update total budget
            self._update_total_budget(item.request_id)
            
            logger.info(f"✅ Updated item: {item_id}")
            return item
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating item: {str(e)}")
            raise Exception(f"Gagal update item: {str(e)}")
    
    def remove_item(self, item_id: int) -> bool:
        """Hapus item dari request"""
        try:
            item = self.db.query(RequestPembelianItem).filter(RequestPembelianItem.id == item_id).first()
            if not item:
                return False
            
            request = self.get_request_by_id(item.request_id)
            if request.status not in ['draft', 'submitted']:
                raise Exception("Request tidak dapat diupdate")
            
            self.db.delete(item)
            self.db.commit()
            
            # Update total budget
            self._update_total_budget(item.request_id)
            
            logger.info(f"✅ Removed item: {item_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error removing item: {str(e)}")
            raise Exception(f"Gagal hapus item: {str(e)}")
    
    # ===== HELPER METHODS =====
    
    def _generate_reference_id(self) -> str:
        """Generate unique reference ID"""
        timestamp = datetime.now().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"REQ-{timestamp}-{unique_id}"
    
    def _generate_request_number(self) -> str:
        """Generate human-readable request number, unik per waktu"""
        # Format: PR-YYYYMMDD-HHMMSS-XXXX (4 char dari UUID)
        return f"PR-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"
    
    def _calculate_timeline(self, total_budget: float) -> Dict[str, datetime]:
        """Calculate timeline berdasarkan budget"""
        now = datetime.utcnow()
        
        # Get timeline configuration
        config = RequestTimelineConfig.get_timeline_for_value(total_budget)
        
        if config:
            vendor_upload_days = config.vendor_upload_days
            analysis_days = config.analysis_days
            approval_days = config.approval_days
        else:
            # Default timeline
            vendor_upload_days = 7
            analysis_days = 2
            approval_days = 1
        
        return {
            'vendor_upload_deadline': now + timedelta(days=vendor_upload_days),
            'analysis_deadline': now + timedelta(days=vendor_upload_days + analysis_days),
            'approval_deadline': now + timedelta(days=vendor_upload_days + analysis_days + approval_days)
        }
    
    def _update_total_budget(self, request_id: int):
        """Update total budget berdasarkan items"""
        request = self.get_request_by_id(request_id)
        if not request:
            return
        
        total = 0
        for item in request.items:
            if item.total_price:
                total += float(item.total_price)
        
        request.total_budget = total
        self.db.commit()
    
    def _create_approval_request(self, request: RequestPembelian):
        """Create approval request untuk workflow"""
        try:
            # Find approval workflow for purchase request
            workflow = self.db.query(ApprovalWorkflow).filter(
                ApprovalWorkflow.module == 'purchase_request',
                ApprovalWorkflow.action_type == 'create_request',
                ApprovalWorkflow.department_id == request.department_id,
                ApprovalWorkflow.is_active == True
            ).first()
            
            if workflow:
                approval_request = ApprovalRequest(
                    workflow_id=workflow.id,
                    requester_id=request.user_id,
                    module='purchase_request',
                    action_type='create_request',
                    resource_id=request.id,
                    resource_data=request.to_dict(),
                    status='pending'
                )
                
                self.db.add(approval_request)
                logger.info(f"✅ Created approval request for: {request.reference_id}")
            
        except Exception as e:
            logger.error(f"❌ Error creating approval request: {str(e)}")
    
    def _notify_vendors(self, request: RequestPembelian):
        """Send notification ke vendors"""
        try:
            # Get approved vendors
            vendors = self.db.query(Vendor).filter(Vendor.status == 'approved').all()
            
            for vendor in vendors:
                # Create notification record
                notification = VendorNotification(
                    request_id=request.id,
                    vendor_id=vendor.id,
                    notification_type='request_available',
                    subject=f'Request Pembelian Baru: {request.title}',
                    message=f'Ada request pembelian baru yang bisa Anda bid. Deadline: {request.vendor_upload_deadline}',
                    status='sent'
                )
                
                self.db.add(notification)
            
            self.db.commit()
            logger.info(f"✅ Sent notifications to {len(vendors)} vendors")
            
        except Exception as e:
            logger.error(f"❌ Error notifying vendors: {str(e)}")
    
    # ===== INTEGRATION WITH STOK BARANG =====
    
    def generate_request_from_stok(self, department_id: int, user_id: int) -> Optional[RequestPembelian]:
        """Generate request otomatis berdasarkan stok minimum"""
        try:
            # Find items with stock below minimum
            low_stock_items = self.db.query(StokBarang).join(Barang).filter(
                StokBarang.jumlah_stok <= StokBarang.stok_minimum
            ).all()
            
            if not low_stock_items:
                return None
            
            # Create request
            request_data = {
                'user_id': user_id,
                'department_id': department_id,
                'title': f'Request Otomatis - Stok Minimum ({datetime.now().strftime("%d/%m/%Y")})',
                'description': 'Request otomatis berdasarkan stok minimum',
                'priority': 'medium',
                'items': []
            }
            
            total_budget = 0
            for stok in low_stock_items:
                # Calculate quantity needed (minimum + buffer)
                needed_quantity = (stok.stok_minimum * 2) - stok.jumlah_stok
                
                item_data = {
                    'barang_id': stok.barang_id,
                    'quantity': needed_quantity,
                    'unit_price': stok.barang.harga_per_unit,
                    'specifications': f'Stok minimum: {stok.stok_minimum}, Stok saat ini: {stok.jumlah_stok}'
                }
                
                if stok.barang.harga_per_unit:
                    item_data['total_price'] = needed_quantity * stok.barang.harga_per_unit
                    total_budget += item_data['total_price']
                
                request_data['items'].append(item_data)
            
            request_data['total_budget'] = total_budget
            
            # Create request
            request = self.create_request(request_data)
            
            logger.info(f"✅ Generated auto request from stok: {request.reference_id}")
            return request
            
        except Exception as e:
            logger.error(f"❌ Error generating request from stok: {str(e)}")
            raise Exception(f"Gagal generate request dari stok: {str(e)}")
    
    # ===== STATISTICS =====
    
    def get_request_statistics(self, department_id: int = None, date_from: datetime = None, date_to: datetime = None) -> Dict[str, Any]:
        """Get statistics untuk request pembelian"""
        try:
            query = self.db.query(RequestPembelian)
            
            if department_id:
                query = query.filter(RequestPembelian.department_id == department_id)
            
            if date_from:
                query = query.filter(RequestPembelian.created_at >= date_from)
            
            if date_to:
                query = query.filter(RequestPembelian.created_at <= date_to)
            
            requests = query.all()
            
            stats = {
                'total_requests': len(requests),
                'by_status': {},
                'by_priority': {},
                'total_budget': 0,
                'average_budget': 0,
                'overdue_requests': 0
            }
            
            total_budget = 0
            overdue_count = 0
            
            for request in requests:
                # Status count
                status = request.status
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # Priority count
                priority = request.priority
                stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
                
                # Budget
                if request.total_budget:
                    total_budget += float(request.total_budget)
                
                # Overdue
                if request.is_overdue():
                    overdue_count += 1
            
            stats['total_budget'] = total_budget
            stats['average_budget'] = total_budget / len(requests) if requests else 0
            stats['overdue_requests'] = overdue_count
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting request statistics: {str(e)}")
            raise Exception(f"Gagal mendapatkan statistik: {str(e)}")
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Mendapatkan statistik untuk dashboard"""
        try:
            # Get all requests
            total_requests = self.db.query(RequestPembelian).count()
            
            # Get requests by status
            pending_requests = self.db.query(RequestPembelian).filter(
                RequestPembelian.status.in_(['draft', 'submitted', 'vendor_uploading', 'under_analysis'])
            ).count()
            
            approved_requests = self.db.query(RequestPembelian).filter(
                RequestPembelian.status == 'approved'
            ).count()
            
            rejected_requests = self.db.query(RequestPembelian).filter(
                RequestPembelian.status == 'rejected'
            ).count()
            
            # Get total budget
            total_budget_result = self.db.query(func.sum(RequestPembelian.total_budget)).filter(
                RequestPembelian.total_budget.isnot(None)
            ).scalar()
            total_budget = float(total_budget_result) if total_budget_result else 0
            
            # Get vendors count
            vendors_count = self.db.query(Vendor).count()
            
            return {
                'total_requests': total_requests,
                'pending_requests': pending_requests,
                'approved_requests': approved_requests,
                'rejected_requests': rejected_requests,
                'total_budget': total_budget,
                'vendors_count': vendors_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting dashboard stats: {str(e)}")
            raise Exception(f"Gagal mendapatkan statistik dashboard: {str(e)}")