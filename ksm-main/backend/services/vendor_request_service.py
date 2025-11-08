#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Request Service - Business Logic untuk Sistem Vendor Request Management
Service untuk mengelola request pembelian yang relevan dengan vendor
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from models.request_pembelian_models import (
    RequestPembelian, Vendor, VendorCategory, VendorPenawaran,
    RequestPembelianItem, VendorPenawaranItem
)

logger = logging.getLogger(__name__)


class VendorRequestService:
    """Service untuk mengelola request pembelian vendor"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_relevant_requests_for_vendor(self, vendor_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Mendapatkan request pembelian yang relevan dengan vendor berdasarkan kategorinya"""
        try:
            # Get vendor categories
            vendor_categories = self.db.query(VendorCategory).filter(
                VendorCategory.vendor_id == vendor_id
            ).all()
            
            if not vendor_categories:
                logger.warning(f"❌ No categories found for vendor {vendor_id}")
                return []
            
            category_ids = [vc.category_id for vc in vendor_categories if vc.category_id]
            
            # Get requests that match vendor categories
            # Filter out budget information as per requirement
            requests_query = self.db.query(RequestPembelian).filter(
                and_(
                    RequestPembelian.status.in_(['submitted', 'vendor_uploading', 'under_analysis']),
                    RequestPembelian.vendor_upload_deadline > datetime.utcnow()  # Only active requests
                )
            )
            
            # If vendor has specific categories, filter by them
            if category_ids:
                # Join with request items to filter by category
                requests_query = requests_query.join(RequestPembelianItem).filter(
                    RequestPembelianItem.category_id.in_(category_ids)
                )
            
            # Get requests with pagination
            requests = requests_query.order_by(
                desc(RequestPembelian.vendor_upload_deadline)
            ).offset(offset).limit(limit).all()
            
            # Format response without budget information
            formatted_requests = []
            for request in requests:
                request_data = request.to_dict()
                
                # Remove budget information
                request_data.pop('total_budget', None)
                
                # Add additional vendor-specific information
                request_data.update({
                    'is_overdue': request.is_overdue(),
                    'days_remaining': request.days_remaining(),
                    'can_upload': self._can_vendor_upload(vendor_id, request.id),
                    'has_penawaran': self._vendor_has_penawaran(vendor_id, request.id),
                    'penawaran_status': self._get_vendor_penawaran_status(vendor_id, request.id)
                })
                
                formatted_requests.append(request_data)
            
            logger.info(f"✅ Found {len(formatted_requests)} relevant requests for vendor {vendor_id}")
            return formatted_requests
            
        except Exception as e:
            logger.error(f"❌ Error getting relevant requests for vendor: {str(e)}")
            return []
    
    def get_request_details_for_vendor(self, request_id: int, vendor_id: int) -> Optional[Dict[str, Any]]:
        """Mendapatkan detail request pembelian untuk vendor (tanpa budget)"""
        try:
            # Check if vendor has access to this request
            if not self._vendor_has_access_to_request(vendor_id, request_id):
                return None
            
            request = self.db.query(RequestPembelian).filter(
                RequestPembelian.id == request_id
            ).first()
            
            if not request:
                return None
            
            # Get request details
            request_data = request.to_dict()
            
            # Remove budget information
            request_data.pop('total_budget', None)
            
            # Get request items
            items = self.db.query(RequestPembelianItem).filter(
                RequestPembelianItem.request_id == request_id
            ).all()
            
            # Format items without price information
            formatted_items = []
            for item in items:
                item_data = item.to_dict()
                item_data.pop('estimated_price', None)  # Remove price information
                
                # Add barang information if available
                if item.barang_id:
                    from models.stok_barang import Barang, KategoriBarang
                    barang = self.db.query(Barang).filter(Barang.id == item.barang_id).first()
                    if barang:
                        # Get kategori information
                        kategori = self.db.query(KategoriBarang).filter(KategoriBarang.id == barang.kategori_id).first()
                        
                        # Add barang details
                        item_data['nama_barang'] = barang.nama_barang
                        item_data['kategori'] = kategori.nama_kategori if kategori else None
                        item_data['satuan'] = barang.satuan
                        item_data['deskripsi'] = barang.deskripsi
                    else:
                        # Fallback if barang not found
                        item_data['nama_barang'] = f"Barang ID {item.barang_id}"
                        item_data['kategori'] = None
                        item_data['satuan'] = 'pcs'
                        item_data['deskripsi'] = None
                else:
                    # Fallback if no barang_id
                    item_data['nama_barang'] = "Barang Tidak Diketahui"
                    item_data['kategori'] = None
                    item_data['satuan'] = 'pcs'
                    item_data['deskripsi'] = None
                
                formatted_items.append(item_data)
            
            request_data['items'] = formatted_items
            
            # Add vendor-specific information
            request_data.update({
                'is_overdue': request.is_overdue(),
                'days_remaining': request.days_remaining(),
                'can_upload': self._can_vendor_upload(vendor_id, request_id),
                'has_penawaran': self._vendor_has_penawaran(vendor_id, request_id),
                'penawaran_status': self._get_vendor_penawaran_status(vendor_id, request_id)
            })
            
            return request_data
            
        except Exception as e:
            logger.error(f"❌ Error getting request details for vendor: {str(e)}")
            return None
    
    def get_vendor_penawaran_for_request(self, vendor_id: int, request_id: int) -> Optional[Dict[str, Any]]:
        """Mendapatkan penawaran vendor untuk request tertentu"""
        try:
            penawaran = self.db.query(VendorPenawaran).filter(
                and_(
                    VendorPenawaran.vendor_id == vendor_id,
                    VendorPenawaran.request_id == request_id
                )
            ).first()
            
            if not penawaran:
                return None
            
            penawaran_data = penawaran.to_dict()
            
            # Get files
            files = self.db.query(penawaran.files).all()
            penawaran_data['files'] = [file.to_dict() for file in files]
            
            return penawaran_data
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor penawaran: {str(e)}")
            return None
    
    def get_penawaran_by_request(self, vendor_id: int, request_id: int) -> Optional[Dict[str, Any]]:
        """Mendapatkan penawaran vendor untuk request tertentu dengan detail items"""
        try:
            penawaran = self.db.query(VendorPenawaran).filter(
                and_(
                    VendorPenawaran.vendor_id == vendor_id,
                    VendorPenawaran.request_id == request_id
                )
            ).first()
            
            if not penawaran:
                return None
            
            penawaran_data = penawaran.to_dict()
            
            # Get penawaran items
            items = self.db.query(VendorPenawaranItem).filter(
                VendorPenawaranItem.vendor_penawaran_id == penawaran.id
            ).all()
            
            # Format items
            formatted_items = []
            for item in items:
                item_data = item.to_dict()
                formatted_items.append(item_data)
            
            penawaran_data['items'] = formatted_items
            
            # Get files if any
            try:
                from models.request_pembelian_models import VendorPenawaranFile
                files = self.db.query(VendorPenawaranFile).filter(
                    VendorPenawaranFile.vendor_penawaran_id == penawaran.id
                ).all()
                penawaran_data['files'] = [file.to_dict() for file in files]
            except Exception as e:
                logger.warning(f"Could not load files for penawaran {penawaran.id}: {str(e)}")
                penawaran_data['files'] = []
            
            return penawaran_data
            
        except Exception as e:
            logger.error(f"❌ Error getting penawaran by request: {str(e)}")
            return None
    
    def get_vendor_dashboard_data(self, vendor_id: int) -> Dict[str, Any]:
        """Mendapatkan data dashboard vendor"""
        try:
            # Get vendor information
            vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
            if not vendor:
                return {}
            
            # Get statistics
            statistics = self.get_vendor_statistics(vendor_id)
            
            # Get recent requests
            recent_requests = self.get_relevant_requests_for_vendor(vendor_id, limit=5)
            
            # Get recent penawaran
            recent_penawaran = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.vendor_id == vendor_id
            ).order_by(desc(VendorPenawaran.created_at)).limit(5).all()
            
            # Format recent penawaran
            formatted_penawaran = []
            for penawaran in recent_penawaran:
                penawaran_data = penawaran.to_dict()
                # Get request title
                request = self.db.query(RequestPembelian).filter(
                    RequestPembelian.id == penawaran.request_id
                ).first()
                if request:
                    penawaran_data['request_title'] = request.title
                    penawaran_data['request_reference_id'] = request.reference_id
                formatted_penawaran.append(penawaran_data)
            
            return {
                'vendor': vendor.to_dict(),
                'statistics': statistics,
                'recent_requests': recent_requests,
                'recent_penawaran': formatted_penawaran,
                'dashboard_summary': {
                    'total_active_requests': statistics.get('active_requests', 0),
                    'pending_penawaran': statistics.get('pending_penawaran', 0),
                    'success_rate': statistics.get('success_rate', 0),
                    'vendor_status': vendor.status
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor dashboard data: {str(e)}")
            return {}
    
    def get_vendor_statistics(self, vendor_id: int) -> Dict[str, Any]:
        """Mendapatkan statistik vendor"""
        try:
            # Get total penawaran
            total_penawaran = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.vendor_id == vendor_id
            ).count()
            
            # Get penawaran by status
            pending_penawaran = self.db.query(VendorPenawaran).filter(
                and_(
                    VendorPenawaran.vendor_id == vendor_id,
                    VendorPenawaran.status == 'submitted'
                )
            ).count()
            
            under_review_penawaran = self.db.query(VendorPenawaran).filter(
                and_(
                    VendorPenawaran.vendor_id == vendor_id,
                    VendorPenawaran.status == 'under_review'
                )
            ).count()
            
            approved_penawaran = self.db.query(VendorPenawaran).filter(
                and_(
                    VendorPenawaran.vendor_id == vendor_id,
                    VendorPenawaran.status == 'selected'
                )
            ).count()
            
            rejected_penawaran = self.db.query(VendorPenawaran).filter(
                and_(
                    VendorPenawaran.vendor_id == vendor_id,
                    VendorPenawaran.status == 'rejected'
                )
            ).count()
            
            # Get active requests count
            active_requests = len(self.get_relevant_requests_for_vendor(vendor_id, limit=1000))
            
            return {
                'total_penawaran': total_penawaran,
                'pending_penawaran': pending_penawaran,
                'under_review_penawaran': under_review_penawaran,
                'approved_penawaran': approved_penawaran,
                'rejected_penawaran': rejected_penawaran,
                'active_requests': active_requests,
                'success_rate': round((approved_penawaran / total_penawaran * 100) if total_penawaran > 0 else 0, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor statistics: {str(e)}")
            return {
                'total_penawaran': 0,
                'pending_penawaran': 0,
                'under_review_penawaran': 0,
                'approved_penawaran': 0,
                'rejected_penawaran': 0,
                'active_requests': 0,
                'success_rate': 0
            }
    
    def _vendor_has_access_to_request(self, vendor_id: int, request_id: int) -> bool:
        """Check if vendor has access to specific request"""
        try:
            # Check if request exists and is in a state that vendors can access
            request = self.db.query(RequestPembelian).filter(
                and_(
                    RequestPembelian.id == request_id,
                    RequestPembelian.status.in_(['submitted', 'vendor_uploading', 'under_analysis', 'vendor_selected', 'approved', 'rejected'])
                )
            ).first()
            
            if not request:
                return False
            
            # For now, allow all vendors to access requests in these states
            # This can be modified later to implement category-based filtering
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking vendor access to request: {str(e)}")
            return False
    
    def _can_vendor_upload(self, vendor_id: int, request_id: int) -> bool:
        """Check if vendor can upload penawaran for this request"""
        try:
            # Check if vendor already has penawaran
            existing_penawaran = self.db.query(VendorPenawaran).filter(
                and_(
                    VendorPenawaran.vendor_id == vendor_id,
                    VendorPenawaran.request_id == request_id
                )
            ).first()
            
            # Vendor can only upload once per request
            return existing_penawaran is None
            
        except Exception as e:
            logger.error(f"❌ Error checking if vendor can upload: {str(e)}")
            return False
    
    def _vendor_has_penawaran(self, vendor_id: int, request_id: int) -> bool:
        """Check if vendor has submitted penawaran for this request"""
        try:
            penawaran = self.db.query(VendorPenawaran).filter(
                and_(
                    VendorPenawaran.vendor_id == vendor_id,
                    VendorPenawaran.request_id == request_id
                )
            ).first()
            
            return penawaran is not None
            
        except Exception as e:
            logger.error(f"❌ Error checking if vendor has penawaran: {str(e)}")
            return False
    
    def _get_vendor_penawaran_status(self, vendor_id: int, request_id: int) -> Optional[str]:
        """Get vendor penawaran status for this request"""
        try:
            penawaran = self.db.query(VendorPenawaran).filter(
                and_(
                    VendorPenawaran.vendor_id == vendor_id,
                    VendorPenawaran.request_id == request_id
                )
            ).first()
            
            return penawaran.status if penawaran else None
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor penawaran status: {str(e)}")
            return None
    
    def get_vendor_requests_paginated(self, vendor_id: int, page: int = 1, per_page: int = 10, status: str = None, category_filter: str = None) -> Dict[str, Any]:
        """Mendapatkan request pembelian vendor dengan pagination"""
        try:
            # Base query for requests - show all SUBMITTED requests by default
            requests_query = self.db.query(RequestPembelian).filter(
                RequestPembelian.status == 'submitted'
            )
            
            # Apply category filter if specified
            if category_filter == 'my_categories':
                # Get vendor categories
                vendor_categories = self.db.query(VendorCategory).filter(
                    VendorCategory.vendor_id == vendor_id
                ).all()
                
                if vendor_categories:
                    category_ids = [vc.category_id for vc in vendor_categories if vc.category_id]
                    if category_ids:
                        requests_query = requests_query.join(RequestPembelianItem).filter(
                            RequestPembelianItem.category_id.in_(category_ids)
                        )
                else:
                    # If vendor has no categories, return empty
                    return {
                        'requests': [],
                        'pagination': {
                            'page': page,
                            'per_page': per_page,
                            'total': 0,
                            'pages': 0,
                            'has_next': False,
                            'has_prev': False
                        }
                    }
            
            # Apply status filter if provided (override default submitted filter)
            if status:
                requests_query = requests_query.filter(RequestPembelian.status == status)
            
            # Get total count
            total_count = requests_query.count()
            
            # Calculate pagination
            total_pages = (total_count + per_page - 1) // per_page
            offset = (page - 1) * per_page
            
            # Get paginated results
            requests = requests_query.order_by(
                desc(RequestPembelian.created_at)
            ).offset(offset).limit(per_page).all()
            
            # Format response
            formatted_requests = []
            for request in requests:
                request_data = request.to_dict()
                
                # Remove budget information
                request_data.pop('total_budget', None)
                
                # Add vendor-specific information
                request_data.update({
                    'is_overdue': request.is_overdue(),
                    'days_remaining': request.days_remaining(),
                    'can_upload': self._can_vendor_upload(vendor_id, request.id),
                    'has_penawaran': self._vendor_has_penawaran(vendor_id, request.id),
                    'penawaran_status': self._get_vendor_penawaran_status(vendor_id, request.id)
                })
                
                formatted_requests.append(request_data)
            
            return {
                'requests': formatted_requests,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor requests paginated: {str(e)}")
            return {
                'requests': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }
    
    def get_vendor_request(self, vendor_id: int, request_id: int) -> Optional[Dict[str, Any]]:
        """Mendapatkan detail request pembelian untuk vendor"""
        try:
            # Check if vendor has access to this request
            if not self._vendor_has_access_to_request(vendor_id, request_id):
                return None
            
            request = self.db.query(RequestPembelian).filter(
                RequestPembelian.id == request_id
            ).first()
            
            if not request:
                return None
            
            # Get request details
            request_data = request.to_dict()
            
            # Remove budget information
            request_data.pop('total_budget', None)
            
            # Get request items
            items = self.db.query(RequestPembelianItem).filter(
                RequestPembelianItem.request_id == request_id
            ).all()
            
            # Format items without price information
            formatted_items = []
            for item in items:
                item_data = item.to_dict()
                item_data.pop('estimated_price', None)  # Remove price information
                
                # Add barang information if available
                if item.barang_id:
                    from models.stok_barang import Barang, KategoriBarang
                    barang = self.db.query(Barang).filter(Barang.id == item.barang_id).first()
                    if barang:
                        # Get kategori information
                        kategori = self.db.query(KategoriBarang).filter(KategoriBarang.id == barang.kategori_id).first()
                        
                        # Add barang details
                        item_data['nama_barang'] = barang.nama_barang
                        item_data['kategori'] = kategori.nama_kategori if kategori else None
                        item_data['satuan'] = barang.satuan
                        item_data['deskripsi'] = barang.deskripsi
                    else:
                        # Fallback if barang not found
                        item_data['nama_barang'] = f"Barang ID {item.barang_id}"
                        item_data['kategori'] = None
                        item_data['satuan'] = 'pcs'
                        item_data['deskripsi'] = None
                else:
                    # Fallback if no barang_id
                    item_data['nama_barang'] = "Barang Tidak Diketahui"
                    item_data['kategori'] = None
                    item_data['satuan'] = 'pcs'
                    item_data['deskripsi'] = None
                
                formatted_items.append(item_data)
            
            request_data['items'] = formatted_items
            
            # Add vendor-specific information
            request_data.update({
                'is_overdue': request.is_overdue(),
                'days_remaining': request.days_remaining(),
                'can_upload': self._can_vendor_upload(vendor_id, request_id),
                'has_penawaran': self._vendor_has_penawaran(vendor_id, request_id),
                'penawaran_status': self._get_vendor_penawaran_status(vendor_id, request_id)
            })
            
            return request_data
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor request: {str(e)}")
            return None
    
    def create_penawaran_with_items(self, vendor_id: int, request_id: int, penawaran_data: Dict[str, Any], items_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create penawaran dengan detail items"""
        try:
            # Validate input
            if not items_data or len(items_data) == 0:
                raise ValueError("Items data tidak boleh kosong")
            
            # Check if vendor already has penawaran for this request
            existing_penawaran = self.db.query(VendorPenawaran).filter(
                and_(
                    VendorPenawaran.vendor_id == vendor_id,
                    VendorPenawaran.request_id == request_id
                )
            ).first()
            
            if existing_penawaran:
                # If penawaran exists and status is 'submitted', allow update
                if existing_penawaran.status == 'submitted':
                    logger.info(f"🔄 Updating existing penawaran: {existing_penawaran.reference_id}")
                    return self._update_existing_penawaran(existing_penawaran, penawaran_data, items_data)
                else:
                    raise ValueError(f"Penawaran sudah dalam status '{existing_penawaran.status}' dan tidak dapat diupdate")
            
            # Generate reference ID
            reference_id = f"PEN-{datetime.utcnow().strftime('%Y%m%d')}-{vendor_id:04d}-{request_id:04d}"
            
            # Create penawaran header
            penawaran = VendorPenawaran(
                request_id=request_id,
                vendor_id=vendor_id,
                reference_id=reference_id,
                status='submitted',
                total_quoted_price=penawaran_data.get('total_quoted_price'),
                delivery_time_days=penawaran_data.get('delivery_time_days'),
                payment_terms=penawaran_data.get('payment_terms'),
                quality_rating=penawaran_data.get('quality_rating'),
                notes=penawaran_data.get('notes')
            )
            
            self.db.add(penawaran)
            self.db.flush()  # Get the ID
            
            # Create penawaran items
            for item_data in items_data:
                penawaran_item = VendorPenawaranItem(
                    vendor_penawaran_id=penawaran.id,
                    request_item_id=item_data.get('request_item_id'),
                    vendor_unit_price=item_data.get('harga_satuan', 0),
                    vendor_total_price=item_data.get('harga_total', 0),
                    vendor_quantity=item_data.get('quantity', 0),
                    vendor_specifications=item_data.get('spesifikasi', ''),
                    vendor_notes=item_data.get('notes', ''),
                    vendor_merk=item_data.get('merk', '')
                )
                self.db.add(penawaran_item)
            
            # Commit transaction
            self.db.commit()
            
            logger.info(f"✅ Penawaran created successfully: {reference_id}")
            
            # Return penawaran data with items
            result = penawaran.to_dict()
            result['items'] = [item.to_dict() for item in penawaran.items.all()]
            
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating penawaran with items: {str(e)}")
            raise e
    
    def upload_file_to_request(self, vendor_id: int, request_id: int, file, description: str = '') -> Optional[Dict[str, Any]]:
        """Upload file to specific request (placeholder implementation)"""
        try:
            # This is a placeholder implementation
            # In a real implementation, you would handle file upload here
            logger.info(f"📁 File upload requested for vendor {vendor_id}, request {request_id}")
            
            return {
                'id': 1,
                'filename': file.filename if file else 'unknown',
                'description': description,
                'uploaded_at': datetime.utcnow().isoformat(),
                'status': 'uploaded'
            }
            
        except Exception as e:
            logger.error(f"❌ Error uploading file to request: {str(e)}")
            return None
    
    def get_vendor_history_paginated(
        self, 
        vendor_id: int, 
        page: int = 1, 
        per_page: int = 10, 
        status: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """Mendapatkan riwayat aktivitas vendor dengan pagination"""
        try:
            from datetime import datetime
            
            # Get vendor penawaran history
            penawaran_query = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.vendor_id == vendor_id
            )
            
            # Apply status filter if provided (handle 'all' as no filter)
            if status and status != 'all':
                penawaran_query = penawaran_query.filter(VendorPenawaran.status == status)
            
            # Apply date filters if provided
            if start_date:
                try:
                    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                    penawaran_query = penawaran_query.filter(VendorPenawaran.submission_date >= start_datetime)
                except ValueError:
                    logger.warning(f"Invalid start_date format: {start_date}")
            
            if end_date:
                try:
                    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                    # Add 1 day to include the entire end date
                    from datetime import timedelta
                    end_datetime = end_datetime + timedelta(days=1)
                    penawaran_query = penawaran_query.filter(VendorPenawaran.submission_date < end_datetime)
                except ValueError:
                    logger.warning(f"Invalid end_date format: {end_date}")
            
            # Get total count
            total_count = penawaran_query.count()
            logger.info(f"🔍 Found {total_count} penawaran for vendor_id {vendor_id} with filters: status={status}, start_date={start_date}, end_date={end_date}")
            
            # Calculate pagination
            total_pages = (total_count + per_page - 1) // per_page
            offset = (page - 1) * per_page
            
            # Get paginated results
            penawarans = penawaran_query.order_by(
                desc(VendorPenawaran.submission_date)
            ).offset(offset).limit(per_page).all()
            
            # Format response
            formatted_history = []
            for penawaran in penawarans:
                history_item = penawaran.to_dict()
                
                # Get request details
                request = self.db.query(RequestPembelian).filter(
                    RequestPembelian.id == penawaran.request_id
                ).first()
                
                if request:
                    # Get items count for this penawaran
                    items_count = penawaran.items.count()
                    
                    history_item.update({
                        'request_title': request.title,
                        'request_description': request.description or '',
                        'request_reference_id': request.reference_id,
                        'activity_type': 'penawaran',
                        'activity_description': f"Penawaran {penawaran.status} untuk request {request.reference_id}",
                        'files_count': penawaran.files.count(),
                        'items_count': items_count,
                        'has_items': items_count > 0
                    })
                
                formatted_history.append(history_item)
            
            return {
                'history': formatted_history,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor history paginated: {str(e)}")
            return {
                'history': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }
    
    def calculate_vendor_success_rate(self, vendor_id: int) -> float:
        """Hitung success rate vendor berdasarkan penawaran yang selected"""
        try:
            # Get total penawaran count
            total_penawarans = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.vendor_id == vendor_id
            ).count()
            
            if total_penawarans == 0:
                return 0.0
            
            # Get successful penawaran count (selected or partially_selected)
            successful_penawarans = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.vendor_id == vendor_id,
                VendorPenawaran.status.in_(['selected', 'partially_selected'])
            ).count()
            
            # Calculate percentage
            success_rate = (successful_penawarans / total_penawarans) * 100
            
            logger.info(f"📊 Success rate for vendor {vendor_id}: {success_rate:.2f}% ({successful_penawarans}/{total_penawarans})")
            
            return round(success_rate, 2)
            
        except Exception as e:
            logger.error(f"❌ Error calculating vendor success rate: {str(e)}")
            return 0.0
    
    def get_vendor_penawarans_paginated(self, vendor_id: int, page: int = 1, per_page: int = 10, status: str = None) -> Dict[str, Any]:
        """Mendapatkan penawaran vendor dengan pagination"""
        try:
            # Base query for penawarans
            penawaran_query = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.vendor_id == vendor_id
            )
            
            # Apply status filter if provided
            if status:
                penawaran_query = penawaran_query.filter(VendorPenawaran.status == status)
            
            # Get total count
            total_count = penawaran_query.count()
            
            # Calculate pagination
            total_pages = (total_count + per_page - 1) // per_page
            offset = (page - 1) * per_page
            
            # Get paginated results
            penawarans = penawaran_query.order_by(
                desc(VendorPenawaran.created_at)
            ).offset(offset).limit(per_page).all()
            
            # Format response
            formatted_penawarans = []
            for penawaran in penawarans:
                penawaran_data = penawaran.to_dict()
                
                # Get request details
                request = self.db.query(RequestPembelian).filter(
                    RequestPembelian.id == penawaran.request_id
                ).first()
                
                if request:
                    penawaran_data.update({
                        'request_title': request.title,
                        'request_reference_id': request.reference_id
                    })
                
                formatted_penawarans.append(penawaran_data)
            
            return {
                'penawarans': formatted_penawarans,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor penawarans paginated: {str(e)}")
            return {
                'penawarans': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }
    
    def update_penawaran(self, vendor_id: int, penawaran_id: int, update_data: Dict[str, Any]) -> Optional[VendorPenawaran]:
        """Update penawaran data"""
        try:
            penawaran = self.db.query(VendorPenawaran).filter(
                and_(
                    VendorPenawaran.id == penawaran_id,
                    VendorPenawaran.vendor_id == vendor_id
                )
            ).first()
            
            if not penawaran:
                return None
            
            # Update penawaran fields
            for field, value in update_data.items():
                if hasattr(penawaran, field):
                    setattr(penawaran, field, value)
            
            penawaran.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(penawaran)
            
            logger.info(f"✅ Updated penawaran {penawaran.reference_id}")
            return penawaran
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating penawaran: {str(e)}")
            return None
    
    def _update_existing_penawaran(self, existing_penawaran: VendorPenawaran, penawaran_data: Dict[str, Any], items_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update existing penawaran with new data"""
        try:
            # Update penawaran header
            existing_penawaran.total_quoted_price = penawaran_data.get('total_quoted_price')
            existing_penawaran.delivery_time_days = penawaran_data.get('delivery_time_days')
            existing_penawaran.payment_terms = penawaran_data.get('payment_terms')
            existing_penawaran.quality_rating = penawaran_data.get('quality_rating')
            existing_penawaran.notes = penawaran_data.get('notes')
            existing_penawaran.updated_at = datetime.utcnow()
            
            # Delete existing items
            from models.request_pembelian_models import VendorPenawaranItem
            VendorPenawaranItem.query.filter_by(vendor_penawaran_id=existing_penawaran.id).delete()
            
            # Create new items
            for item_data in items_data:
                penawaran_item = VendorPenawaranItem(
                    vendor_penawaran_id=existing_penawaran.id,
                    request_item_id=item_data.get('request_item_id'),
                    vendor_unit_price=item_data.get('vendor_unit_price') or item_data.get('harga_satuan'),
                    vendor_total_price=item_data.get('vendor_total_price') or item_data.get('harga_total'),
                    vendor_quantity=item_data.get('vendor_quantity') or item_data.get('quantity'),
                    vendor_specifications=item_data.get('vendor_specifications') or item_data.get('spesifikasi'),
                    vendor_notes=item_data.get('vendor_notes') or item_data.get('notes'),
                    vendor_merk=item_data.get('vendor_merk') or item_data.get('merk')
                )
                self.db.add(penawaran_item)
            
            # Handle files if provided
            if 'files' in penawaran_data and penawaran_data['files']:
                from models.request_pembelian_models import VendorPenawaranFile
                
                # Delete existing files
                VendorPenawaranFile.query.filter_by(vendor_penawaran_id=existing_penawaran.id).delete()
                
                # Create new files
                for file_data in penawaran_data['files']:
                    penawaran_file = VendorPenawaranFile(
                        vendor_penawaran_id=existing_penawaran.id,
                        reference_id=f"FILE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{existing_penawaran.id}",
                        file_name=file_data.get('file_name'),
                        file_path=file_data.get('file_path'),
                        file_type=file_data.get('file_type'),
                        file_size=file_data.get('file_size'),
                        file_hash=file_data.get('file_hash')
                    )
                    self.db.add(penawaran_file)
            
            self.db.commit()
            self.db.refresh(existing_penawaran)
            
            logger.info(f"✅ Updated existing penawaran: {existing_penawaran.reference_id}")
            
            return {
                'id': existing_penawaran.id,
                'reference_id': existing_penawaran.reference_id,
                'status': existing_penawaran.status,
                'message': 'Penawaran berhasil diupdate'
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating existing penawaran: {str(e)}")
            raise e