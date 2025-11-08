#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Selection Service - Business Logic untuk Sistem Vendor Selection
Service untuk mengelola seleksi dan approval item penawaran vendor
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, distinct
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from models.request_pembelian_models import (
    RequestPembelian, Vendor, VendorPenawaran, VendorPenawaranItem,
    RequestPembelianItem, VendorNotification
)

logger = logging.getLogger(__name__)


class VendorSelectionService:
    """Service untuk mengelola seleksi dan approval item penawaran vendor"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_reference_ids_with_penawarans(self, page: int = 1, per_page: int = 10, 
                                        filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mendapatkan daftar reference_id beserta summary penawaran"""
        try:
            if filters is None:
                filters = {}
            
            # Base query untuk semua request yang eligible untuk vendor selection
            # Termasuk draft yang sudah memiliki penawaran vendor
            base_query = self.db.query(RequestPembelian).filter(
                RequestPembelian.status.in_(['draft', 'submitted', 'vendor_uploading', 'under_analysis', 'vendor_selected', 'completed'])
            )
            
            # Apply filters
            if filters.get('status'):
                base_query = base_query.filter(RequestPembelian.status == filters['status'])
            
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                base_query = base_query.filter(
                    or_(
                        RequestPembelian.reference_id.ilike(search_term),
                        RequestPembelian.title.ilike(search_term)
                    )
                )
            
            # Get total count
            total = base_query.distinct().count()
            
            # Get paginated results
            offset = (page - 1) * per_page
            requests = base_query.distinct().order_by(desc(RequestPembelian.created_at)).offset(offset).limit(per_page).all()
            
            # Build response data
            reference_data = []
            for request in requests:
                # Get vendor count and item count for this reference
                vendor_count = self.db.query(VendorPenawaran).filter(
                    VendorPenawaran.request_id == request.id
                ).count()
                
                item_count = self.db.query(VendorPenawaranItem).join(
                    VendorPenawaran, VendorPenawaranItem.vendor_penawaran_id == VendorPenawaran.id
                ).filter(VendorPenawaran.request_id == request.id).count()
                
                selected_count = self.db.query(VendorPenawaranItem).join(
                    VendorPenawaran, VendorPenawaranItem.vendor_penawaran_id == VendorPenawaran.id
                ).filter(
                    and_(
                        VendorPenawaran.request_id == request.id,
                        VendorPenawaranItem.is_selected == True
                    )
                ).count()
                
                # Calculate total value of selected items
                selected_items = self.db.query(VendorPenawaranItem).join(
                    VendorPenawaran, VendorPenawaranItem.vendor_penawaran_id == VendorPenawaran.id
                ).filter(
                    and_(
                        VendorPenawaran.request_id == request.id,
                        VendorPenawaranItem.is_selected == True
                    )
                ).all()
                
                total_value = sum(float(item.vendor_total_price or 0) for item in selected_items)
                
                reference_data.append({
                    'reference_id': request.reference_id,
                    'request_id': request.id,
                    'title': request.title,
                    'status': request.status,
                    'vendor_count': vendor_count,
                    'item_count': item_count,
                    'selected_count': selected_count,
                    'total_value': total_value,
                    'created_at': request.created_at.isoformat() if request.created_at else None,
                    'required_date': request.required_date.isoformat() if request.required_date else None
                })
            
            # Calculate pagination info
            total_pages = (total + per_page - 1) // per_page
            
            return {
                'success': True,
                'data': reference_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting reference IDs with penawarans: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': [],
                'pagination': {}
            }
    
    def get_penawaran_items_by_reference(self, reference_id: str) -> Dict[str, Any]:
        """Detail items dari semua vendor per reference_id"""
        try:
            # Get request by reference_id
            request = self.db.query(RequestPembelian).filter(
                RequestPembelian.reference_id == reference_id
            ).first()
            
            if not request:
                return {
                    'success': False,
                    'message': 'Reference ID tidak ditemukan'
                }
            
            # Get all penawarans for this request
            penawarans = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.request_id == request.id
            ).all()
            
            # Group items by vendor
            vendor_groups = []
            for penawaran in penawarans:
                # Get vendor info
                vendor = self.db.query(Vendor).filter(Vendor.id == penawaran.vendor_id).first()
                
                # Get items for this penawaran
                items = self.db.query(VendorPenawaranItem).filter(
                    VendorPenawaranItem.vendor_penawaran_id == penawaran.id
                ).all()
                
                # Build item data with request item info
                item_data = []
                for item in items:
                    # Get request item info
                    request_item = None
                    request_item_name = 'Nama Barang Tidak Diketahui'
                    if item.request_item_id:
                        request_item = self.db.query(RequestPembelianItem).filter(
                            RequestPembelianItem.id == item.request_item_id
                        ).first()
                        
                        # Get actual barang name if request_item exists
                        if request_item:
                            try:
                                from models.stok_barang import Barang
                                barang = self.db.query(Barang).filter(Barang.id == request_item.barang_id).first()
                                if barang:
                                    request_item_name = barang.nama_barang
                                else:
                                    request_item_name = f"Barang ID {request_item.barang_id}"
                            except Exception as e:
                                logger.warning(f"Error getting barang name for request_item {request_item.id}: {e}")
                                request_item_name = f"Item {request_item.id}"
                    
                    item_data.append({
                        'id': item.id,
                        'vendor_penawaran_id': item.vendor_penawaran_id,
                        'request_item_id': item.request_item_id,
                        'vendor_unit_price': float(item.vendor_unit_price or 0),
                        'vendor_total_price': float(item.vendor_total_price or 0),
                        'vendor_quantity': item.vendor_quantity or 0,
                        'vendor_specifications': item.vendor_specifications,
                        'vendor_notes': item.vendor_notes,
                        'is_selected': item.is_selected,
                        'selected_by_user_id': item.selected_by_user_id,
                        'selected_at': item.selected_at.isoformat() if item.selected_at else None,
                        'selection_notes': item.selection_notes,
                        'created_at': item.created_at.isoformat() if item.created_at else None,
                        # Request item info
                        'request_item_name': request_item_name,
                        'request_quantity': request_item.quantity if request_item else 0,
                        'request_specifications': request_item.specifications if request_item else None
                    })
                
                vendor_groups.append({
                    'vendor_id': vendor.id if vendor else None,
                    'vendor_name': vendor.company_name if vendor else 'Vendor Tidak Diketahui',
                    'vendor_contact': vendor.contact_person if vendor else None,
                    'vendor_email': vendor.email if vendor else None,
                    'penawaran_id': penawaran.id,
                    'penawaran_status': penawaran.status,
                    'total_quoted_price': float(penawaran.total_quoted_price or 0),
                    'delivery_time_days': penawaran.delivery_time_days,
                    'payment_terms': penawaran.payment_terms,
                    'submission_date': penawaran.submission_date.isoformat() if penawaran.submission_date else None,
                    'items': item_data
                })
            
            return {
                'success': True,
                'data': {
                    'reference_id': reference_id,
                    'request_id': request.id,
                    'title': request.title,
                    'status': request.status,
                    'vendor_groups': vendor_groups
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting penawaran items by reference {reference_id}: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def select_vendor_items(self, item_selections: List[Dict], user_id: int, 
                          notes: str = None) -> Dict[str, Any]:
        """
        Batch selection items dari vendor dengan support quantity split
        
        item_selections format:
        [
            {"item_id": 1, "selected_quantity": 2, "action": "select"},
            {"item_id": 2, "selected_quantity": 3, "action": "select"}
        ]
        """
        try:
            if not item_selections:
                return {
                    'success': False,
                    'message': 'Item selections tidak boleh kosong'
                }
            
            # Extract item IDs for validation
            item_ids = [selection['item_id'] for selection in item_selections]
            
            # Get items
            items = self.db.query(VendorPenawaranItem).filter(
                VendorPenawaranItem.id.in_(item_ids)
            ).all()
            
            if not items:
                return {
                    'success': False,
                    'message': 'Items tidak ditemukan'
                }
            
            # Validate quantity split
            validation_result = self._validate_quantity_split(item_selections, items)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': validation_result['message']
                }
            
            # Update items
            updated_count = 0
            for selection in item_selections:
                item_id = selection['item_id']
                selected_quantity = selection.get('selected_quantity', 0)
                action = selection.get('action', 'select')
                
                # Find the item
                item = next((i for i in items if i.id == item_id), None)
                if not item:
                    continue
                
                if action == 'select':
                    item.is_selected = True
                    item.selected_quantity = selected_quantity
                    item.selected_by_user_id = user_id
                    item.selected_at = datetime.utcnow()
                    item.selection_notes = notes
                elif action == 'unselect':
                    item.is_selected = False
                    item.selected_quantity = None
                    item.selected_by_user_id = None
                    item.selected_at = None
                    item.selection_notes = None
                
                item.updated_at = datetime.utcnow()
                updated_count += 1
            
            self.db.commit()
            
            logger.info(f"✅ Updated {updated_count} vendor items by user {user_id}")
            
            return {
                'success': True,
                'message': f'Berhasil update {updated_count} items',
                'updated_count': updated_count
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating vendor items: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def _validate_quantity_split(self, item_selections: List[Dict], items: List[VendorPenawaranItem]) -> Dict[str, Any]:
        """Validasi quantity split untuk memastikan tidak melebihi request quantity"""
        try:
            # Group selections by request_item_id
            request_item_quantities = {}
            
            for selection in item_selections:
                item_id = selection['item_id']
                selected_quantity = selection.get('selected_quantity', 0)
                action = selection.get('action', 'select')
                
                # Find the item
                item = next((i for i in items if i.id == item_id), None)
                if not item or not item.request_item_id:
                    continue
                
                request_item_id = item.request_item_id
                
                if request_item_id not in request_item_quantities:
                    request_item_quantities[request_item_id] = {
                        'total_selected': 0,
                        'request_quantity': 0,
                        'item_name': f'Item {request_item_id}'
                    }
                
                if action == 'select':
                    request_item_quantities[request_item_id]['total_selected'] += selected_quantity
                
                # Get request quantity (only need to do this once per request_item_id)
                if request_item_quantities[request_item_id]['request_quantity'] == 0:
                    request_item = self.db.query(RequestPembelianItem).filter(
                        RequestPembelianItem.id == request_item_id
                    ).first()
                    if request_item:
                        request_item_quantities[request_item_id]['request_quantity'] = request_item.quantity
                        request_item_quantities[request_item_id]['item_name'] = f'Item {request_item_id}'
            
            # Validate each request item
            for request_item_id, data in request_item_quantities.items():
                if data['total_selected'] > data['request_quantity']:
                    return {
                        'valid': False,
                        'message': f"Total quantity yang dipilih ({data['total_selected']}) melebihi quantity yang direquest ({data['request_quantity']}) untuk {data['item_name']}"
                    }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"❌ Error validating quantity split: {str(e)}")
            return {
                'valid': False,
                'message': f'Error validasi quantity: {str(e)}'
            }
    
    def approve_selected_items(self, reference_id: str, user_id: int, 
                             notes: str = None) -> Dict[str, Any]:
        """Finalize approval items yang sudah selected"""
        try:
            # Get request by reference_id
            request = self.db.query(RequestPembelian).filter(
                RequestPembelian.reference_id == reference_id
            ).first()
            
            if not request:
                return {
                    'success': False,
                    'message': 'Reference ID tidak ditemukan'
                }
            
            # Check if there are selected items
            selected_items = self.db.query(VendorPenawaranItem).join(
                VendorPenawaran, VendorPenawaranItem.vendor_penawaran_id == VendorPenawaran.id
            ).filter(
                and_(
                    VendorPenawaran.request_id == request.id,
                    VendorPenawaranItem.is_selected == True
                )
            ).all()
            
            if not selected_items:
                return {
                    'success': False,
                    'message': 'Tidak ada items yang dipilih untuk di-approve'
                }
            
            # Update request status
            request.status = 'vendor_selected'
            request.updated_at = datetime.utcnow()
            if notes:
                request.notes = notes
            
            # Update penawaran status for selected items
            selected_penawaran_ids = list(set([item.vendor_penawaran_id for item in selected_items]))
            for penawaran_id in selected_penawaran_ids:
                penawaran = self.db.query(VendorPenawaran).filter(
                    VendorPenawaran.id == penawaran_id
                ).first()
                if penawaran:
                    # Check if all items in this penawaran are selected
                    all_items = self.db.query(VendorPenawaranItem).filter(
                        VendorPenawaranItem.vendor_penawaran_id == penawaran_id
                    ).all()
                    
                    selected_items_in_penawaran = self.db.query(VendorPenawaranItem).filter(
                        and_(
                            VendorPenawaranItem.vendor_penawaran_id == penawaran_id,
                            VendorPenawaranItem.is_selected == True
                        )
                    ).all()
                    
                    # Set status based on whether all items are selected
                    if len(selected_items_in_penawaran) == len(all_items):
                        penawaran.status = 'selected'
                    else:
                        penawaran.status = 'partially_selected'
                    
                    penawaran.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Create vendor orders from approved items
            from services.vendor_order_service import VendorOrderService
            order_service = VendorOrderService(self.db)
            order_result = order_service.create_orders_from_approval(
                reference_id=reference_id,
                selected_items=selected_items,
                created_by_user_id=user_id
            )
            
            if not order_result['success']:
                logger.error(f"❌ Failed to create vendor orders: {order_result['message']}")
                # Don't fail the entire approval process if order creation fails
                # But log the error for debugging
            else:
                logger.info(f"✅ Successfully created {order_result.get('orders_created', 0)} vendor orders")
            
            # Send notifications to selected vendors (legacy method - will be replaced by order notifications)
            try:
                self.notify_selected_vendors(reference_id, selected_items)
            except Exception as e:
                logger.warning(f"⚠️ Failed to send notifications: {str(e)}")
                # Don't fail the approval if notifications fail
            
            logger.info(f"✅ Approved selected items for reference {reference_id} by user {user_id}")
            
            return {
                'success': True,
                'message': f'Berhasil approve {len(selected_items)} items dari {len(selected_penawaran_ids)} vendor',
                'approved_items_count': len(selected_items),
                'approved_vendors_count': len(selected_penawaran_ids),
                'orders_created': order_result.get('orders_created', 0),
                'vendors_notified': order_result.get('vendors_notified', 0),
                'order_creation_result': order_result  # Include full order creation result
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error approving selected items for reference {reference_id}: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def notify_selected_vendors(self, reference_id: str, selected_items: List[VendorPenawaranItem]) -> None:
        """Kirim notifikasi ke vendor yang itemnya terpilih"""
        try:
            # Get request info
            request = self.db.query(RequestPembelian).filter(
                RequestPembelian.reference_id == reference_id
            ).first()
            
            if not request:
                return
            
            # Group items by vendor
            vendor_items = {}
            for item in selected_items:
                penawaran = self.db.query(VendorPenawaran).filter(
                    VendorPenawaran.id == item.vendor_penawaran_id
                ).first()
                
                if penawaran:
                    vendor_id = penawaran.vendor_id
                    if vendor_id not in vendor_items:
                        vendor_items[vendor_id] = []
                    vendor_items[vendor_id].append(item)
            
            # Send notification to each vendor
            for vendor_id, items in vendor_items.items():
                vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
                if not vendor:
                    continue
                
                # Calculate total value for this vendor
                total_value = sum(float(item.vendor_total_price or 0) for item in items)
                
                # Create notification
                notification = VendorNotification(
                    request_id=request.id,
                    vendor_id=vendor_id,
                    notification_type='request_available',  # Reuse existing type
                    subject=f'Item Penawaran Terpilih - {reference_id}',
                    message=f'Item penawaran Anda untuk request {reference_id} telah terpilih. Total nilai: Rp {total_value:,.0f}. Silakan hubungi kami untuk proses selanjutnya.',
                    status='sent',
                    sent_at=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                
                self.db.add(notification)
            
            self.db.commit()
            logger.info(f"✅ Sent notifications to {len(vendor_items)} vendors for reference {reference_id}")
            
        except Exception as e:
            logger.error(f"❌ Error notifying selected vendors for reference {reference_id}: {str(e)}")
    
    def get_selection_statistics(self) -> Dict[str, Any]:
        """Get statistics untuk dashboard"""
        try:
            # Total requests with penawarans
            total_requests = self.db.query(RequestPembelian).join(
                VendorPenawaran, RequestPembelian.id == VendorPenawaran.request_id
            ).distinct().count()
            
            # Requests by status
            status_counts = {}
            for status in ['submitted', 'vendor_uploading', 'under_analysis', 'vendor_selected', 'completed']:
                count = self.db.query(RequestPembelian).join(
                    VendorPenawaran, RequestPembelian.id == VendorPenawaran.request_id
                ).filter(RequestPembelian.status == status).distinct().count()
                status_counts[status] = count
            
            # Total vendors with penawarans
            total_vendors = self.db.query(Vendor).join(
                VendorPenawaran, Vendor.id == VendorPenawaran.vendor_id
            ).distinct().count()
            
            # Total items selected
            total_selected_items = self.db.query(VendorPenawaranItem).filter(
                VendorPenawaranItem.is_selected == True
            ).count()
            
            return {
                'success': True,
                'data': {
                    'total_requests': total_requests,
                    'status_counts': status_counts,
                    'total_vendors': total_vendors,
                    'total_selected_items': total_selected_items
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting selection statistics: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
