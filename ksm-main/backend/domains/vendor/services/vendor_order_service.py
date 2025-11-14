#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Order Service - Business Logic untuk Sistem Vendor Orders
Service untuk mengelola pesanan vendor dengan status tracking lengkap
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import uuid

from domains.vendor.models.vendor_order_models import VendorOrder
from domains.vendor.models import (
    VendorPenawaranItem, VendorPenawaran, Vendor, VendorNotification
)
from domains.inventory.models import RequestPembelian
from domains.vendor.services.vendor_notification_service import VendorNotificationService

logger = logging.getLogger(__name__)


class VendorOrderService:
    """Service untuk mengelola pesanan vendor dengan status tracking"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = VendorNotificationService(db)
    
    def _generate_order_number(self) -> str:
        """Generate unique order number dengan format ORD-YYYYMMDD-XXXXXX"""
        max_retries = 10
        for attempt in range(max_retries):
            try:
                # Generate order number
                timestamp = datetime.now().strftime('%Y%m%d')
                unique_id = str(uuid.uuid4())[:6].upper()
                order_number = f"ORD-{timestamp}-{unique_id}"
                
                # Check if order number already exists
                existing_order = self.db.query(VendorOrder).filter(
                    VendorOrder.order_number == order_number
                ).first()
                
                if not existing_order:
                    logger.info(f"✅ Generated unique order number: {order_number}")
                    return order_number
                else:
                    logger.warning(f"⚠️ Order number collision detected: {order_number}, retrying...")
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Error generating order number (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to generate unique order number after {max_retries} attempts")
                continue
        
        # Fallback: use timestamp + random if all retries failed
        fallback_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"
        logger.warning(f"⚠️ Using fallback order number: {fallback_number}")
        return fallback_number
    
    def create_orders_from_approval(self, reference_id: str, selected_items: List[VendorPenawaranItem], 
                                   created_by_user_id: int) -> Dict[str, Any]:
        """Membuat vendor orders dari selected items saat admin approve - 1 vendor = 1 order"""
        try:
            if not selected_items:
                return {
                    'success': False,
                    'message': 'Tidak ada items yang dipilih'
                }
            
            # Get request info
            request = self.db.query(RequestPembelian).filter(
                RequestPembelian.reference_id == reference_id
            ).first()
            
            if not request:
                return {
                    'success': False,
                    'message': 'Request tidak ditemukan'
                }
            
            # Group selected items by vendor
            items_by_vendor = {}
            for item in selected_items:
                # Get vendor_id from the penawaran relationship
                penawaran = self.db.query(VendorPenawaran).filter(
                    VendorPenawaran.id == item.vendor_penawaran_id
                ).first()
                
                if not penawaran:
                    logger.warning(f"⚠️ Penawaran dengan ID {item.vendor_penawaran_id} tidak ditemukan, skip item {item.id}")
                    continue
                    
                vendor_id = penawaran.vendor_id
                if vendor_id not in items_by_vendor:
                    items_by_vendor[vendor_id] = []
                items_by_vendor[vendor_id].append(item)
            
            created_orders = []
            orders_by_vendor = {}
            
            # Create one order per vendor
            for vendor_id, vendor_items in items_by_vendor.items():
                try:
                    # Get vendor info
                    vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
                    if not vendor:
                        logger.warning(f"⚠️ Vendor dengan ID {vendor_id} tidak ditemukan, skip items")
                        continue
                    
                    # Calculate totals for all items from this vendor
                    total_quantity = 0
                    total_price = 0
                    items_details = []
                    
                    for item in vendor_items:
                        quantity = item.selected_quantity or item.vendor_quantity or 0
                        unit_price = float(item.vendor_unit_price or 0)
                        item_total = quantity * unit_price
                        
                        total_quantity += quantity
                        total_price += item_total
                        
                        # Store item details for JSON
                        items_details.append({
                            'vendor_penawaran_item_id': item.id,
                            'item_name': item.vendor_specifications or f"Item {item.id}",
                            'quantity': quantity,
                            'unit_price': unit_price,
                            'total_price': item_total,
                            'specifications': item.vendor_specifications
                        })
                    
                    # Generate unique order number
                    order_number = self._generate_order_number()
                    
                    # Create order for this vendor
                    order = VendorOrder(
                        order_number=order_number,
                        vendor_penawaran_item_id=vendor_items[0].id,  # Primary item ID
                        vendor_id=vendor_id,
                        request_id=request.id,
                        reference_id=reference_id,
                        item_name=f"Pesanan {len(vendor_items)} item dari {vendor.company_name}",
                        ordered_quantity=total_quantity,
                        unit_price=total_price / total_quantity if total_quantity > 0 else 0,
                        total_price=total_price,
                        specifications=f"Pesanan gabungan {len(vendor_items)} item dari vendor {vendor.company_name}",
                        status='pending_confirmation',
                        created_by_user_id=created_by_user_id
                    )
                    
                    self.db.add(order)
                    self.db.flush()  # Get the ID
                    
                    # Store items details as JSON in a custom field (we'll add this to model)
                    # For now, we'll store in specifications field
                    import json
                    order.specifications = json.dumps({
                        'items_count': len(vendor_items),
                        'vendor_name': vendor.company_name,
                        'items_details': items_details
                    }, indent=2)
                    
                    created_orders.append(order)
                    
                    # Group by vendor for notifications
                    orders_by_vendor[vendor_id] = {
                        'vendor': vendor,
                        'orders': [order],
                        'items_count': len(vendor_items),
                        'total_value': total_price
                    }
                    
                    logger.info(f"✅ Created order {order_number} for vendor {vendor.company_name} with {len(vendor_items)} items")
                    
                except Exception as e:
                    logger.error(f"❌ Error creating order for vendor {vendor_id}: {str(e)}")
                    # Continue with other vendors even if one fails
                    continue
            
            if not created_orders:
                return {
                    'success': False,
                    'message': 'Gagal membuat pesanan untuk semua vendor'
                }
            
            self.db.commit()
            
            # Send notifications to vendors
            notifications_sent = 0
            for vendor_id, vendor_data in orders_by_vendor.items():
                try:
                    vendor = vendor_data['vendor']
                    orders = vendor_data['orders']
                    items_count = vendor_data['items_count']
                    total_value = vendor_data['total_value']
                    
                    # Create notification
                    notification = self.notification_service.create_order_notification(
                        vendor_id=vendor_id,
                        order_number=orders[0].order_number,
                        notification_type='order_approved'
                    )
                    
                    if notification:
                        # Update notification with order details
                        notification.message = f"Pesanan {orders[0].order_number} telah disetujui. {items_count} item dengan total nilai: Rp {total_value:,.0f}. Silakan konfirmasi dan mulai proses pengiriman."
                        notification.related_request_id = request.id
                        self.db.commit()
                        notifications_sent += 1
                        logger.info(f"✅ Sent notification to vendor {vendor.company_name} for order {orders[0].order_number}")
                    else:
                        logger.warning(f"⚠️ Failed to create notification for vendor {vendor_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Error sending notification to vendor {vendor_id}: {str(e)}")
                    # Continue with other vendors even if one notification fails
                    continue
            
            logger.info(f"✅ Created {len(created_orders)} vendor orders for reference {reference_id}")
            
            return {
                'success': True,
                'message': f'Berhasil membuat {len(created_orders)} pesanan vendor',
                'orders_created': len(created_orders),
                'vendors_notified': notifications_sent,
                'orders': [order.to_dict() for order in created_orders]
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating orders from approval: {str(e)}")
            return {
                'success': False,
                'message': f'Gagal membuat pesanan vendor: {str(e)}'
            }
    
    def get_vendor_orders(self, vendor_id: int, page: int = 1, per_page: int = 10, 
                         status_filter: str = None, search: str = None, 
                         sort_by: str = 'created_at', sort_dir: str = 'desc') -> Dict[str, Any]:
        """Mendapatkan daftar pesanan vendor dengan pagination dan filter"""
        try:
            query = self.db.query(VendorOrder).filter(
                VendorOrder.vendor_id == vendor_id
            )
            
            # Apply filters
            if status_filter and status_filter != 'all':
                query = query.filter(VendorOrder.status == status_filter)
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        VendorOrder.order_number.ilike(search_term),
                        VendorOrder.item_name.ilike(search_term),
                        VendorOrder.reference_id.ilike(search_term)
                    )
                )
            
            # Apply sorting
            sort_column = getattr(VendorOrder, sort_by, VendorOrder.created_at)
            if sort_dir.lower() == 'asc':
                query = query.order_by(sort_column)
            else:
                query = query.order_by(desc(sort_column))
            
            # Get total count
            total = query.count()
            
            # Get paginated results
            offset = (page - 1) * per_page
            orders = query.offset(offset).limit(per_page).all()
            
            # Calculate pagination info
            total_pages = (total + per_page - 1) // per_page
            
            return {
                'success': True,
                'data': [order.to_dict() for order in orders],
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
            logger.error(f"❌ Error getting vendor orders: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': [],
                'pagination': {}
            }
    
    def get_order_detail(self, order_id: int, vendor_id: int = None) -> Dict[str, Any]:
        """Mendapatkan detail pesanan"""
        try:
            query = self.db.query(VendorOrder).filter(VendorOrder.id == order_id)
            
            # If vendor_id provided, ensure vendor can only see their own orders
            if vendor_id:
                query = query.filter(VendorOrder.vendor_id == vendor_id)
            
            order = query.first()
            
            if not order:
                return {
                    'success': False,
                    'message': 'Pesanan tidak ditemukan'
                }
            
            # Get timeline events
            timeline_events = order.get_timeline_events()
            
            return {
                'success': True,
                'data': {
                    'order': order.to_dict(),
                    'timeline': timeline_events,
                    'can_vendor_update': order.can_vendor_update_status(),
                    'can_admin_update': order.can_admin_update_status(),
                    'next_possible_statuses': order.get_next_possible_statuses()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting order detail: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def confirm_order(self, order_id: int, vendor_id: int, vendor_notes: str = None) -> Dict[str, Any]:
        """Vendor konfirmasi pesanan"""
        try:
            order = self.db.query(VendorOrder).filter(
                and_(
                    VendorOrder.id == order_id,
                    VendorOrder.vendor_id == vendor_id,
                    VendorOrder.status == 'pending_confirmation'
                )
            ).first()
            
            if not order:
                return {
                    'success': False,
                    'message': 'Pesanan tidak ditemukan atau sudah dikonfirmasi'
                }
            
            # Update order status
            order.status = 'confirmed'
            order.confirmed_at = datetime.utcnow()
            order.confirmed_by_vendor = True
            order.vendor_notes = vendor_notes
            order.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Send notification to admin
            self.notification_service.create_admin_order_notification(
                order_number=order.order_number,
                vendor_name=order.vendor.company_name,
                notification_type='vendor_confirmed_order',
                order_id=order_id
            )
            
            logger.info(f"✅ Order {order.order_number} confirmed by vendor {vendor_id}")
            
            return {
                'success': True,
                'message': 'Pesanan berhasil dikonfirmasi',
                'order': order.to_dict()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error confirming order: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def update_order_status(self, order_id: int, new_status: str, updated_by_user_id: int,
                           vendor_id: int = None, tracking_number: str = None, 
                           estimated_delivery_date: str = None, notes: str = None) -> Dict[str, Any]:
        """Update status pesanan (vendor atau admin)"""
        try:
            query = self.db.query(VendorOrder).filter(VendorOrder.id == order_id)
            
            # If vendor_id provided, ensure vendor can only update their own orders
            if vendor_id:
                query = query.filter(VendorOrder.vendor_id == vendor_id)
            
            order = query.first()
            
            if not order:
                return {
                    'success': False,
                    'message': 'Pesanan tidak ditemukan'
                }
            
            # Validate status transition
            if new_status not in order.get_next_possible_statuses():
                return {
                    'success': False,
                    'message': f'Status {new_status} tidak valid untuk status saat ini {order.status}'
                }
            
            old_status = order.status
            order.status = new_status
            order.updated_at = datetime.utcnow()
            
            # Update specific fields based on status
            now = datetime.utcnow()
            if new_status == 'processing':
                order.processing_started_at = now
            elif new_status == 'shipped':
                order.shipped_at = now
                if tracking_number:
                    order.tracking_number = tracking_number
            elif new_status == 'delivered':
                order.delivered_at = now
                order.actual_delivery_date = now
            elif new_status == 'completed':
                order.completed_at = now
            
            # Update additional fields
            if estimated_delivery_date:
                try:
                    order.estimated_delivery_date = datetime.fromisoformat(estimated_delivery_date.replace('Z', '+00:00'))
                except:
                    pass  # Invalid date format, skip
            
            if notes:
                if vendor_id:
                    order.vendor_notes = notes
                else:
                    order.admin_notes = notes
            
            self.db.commit()
            
            # Send notifications
            if vendor_id:
                # Vendor updated status - notify admin
                self.notification_service.create_admin_order_notification(
                    order_number=order.order_number,
                    vendor_name=order.vendor.company_name,
                    notification_type='vendor_updated_status',
                    order_id=order_id
                )
            else:
                # Admin updated status - notify vendor
                self.notification_service.create_order_notification(
                    vendor_id=order.vendor_id,
                    order_number=order.order_number,
                    notification_type='order_status_update'
                )
            
            logger.info(f"✅ Order {order.order_number} status updated from {old_status} to {new_status}")
            
            return {
                'success': True,
                'message': f'Status pesanan berhasil diupdate ke {order.get_status_display()}',
                'order': order.to_dict()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating order status: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_order_statistics(self, vendor_id: int) -> Dict[str, Any]:
        """Mendapatkan statistik pesanan vendor"""
        try:
            # Total orders
            total_orders = self.db.query(VendorOrder).filter(
                VendorOrder.vendor_id == vendor_id
            ).count()
            
            # Orders by status
            status_counts = {}
            for status in ['pending_confirmation', 'confirmed', 'processing', 'shipped', 'delivered', 'completed', 'cancelled']:
                count = self.db.query(VendorOrder).filter(
                    and_(
                        VendorOrder.vendor_id == vendor_id,
                        VendorOrder.status == status
                    )
                ).count()
                status_counts[status] = count
            
            # Total value
            total_value = self.db.query(func.sum(VendorOrder.total_price)).filter(
                VendorOrder.vendor_id == vendor_id
            ).scalar() or 0
            
            # Pending confirmation count (for badge)
            pending_confirmation_count = status_counts.get('pending_confirmation', 0)
            
            return {
                'success': True,
                'data': {
                    'total_orders': total_orders,
                    'status_counts': status_counts,
                    'total_value': float(total_value),
                    'pending_confirmation_count': pending_confirmation_count
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting order statistics: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': {
                    'total_orders': 0,
                    'status_counts': {},
                    'total_value': 0,
                    'pending_confirmation_count': 0
                }
            }
    
    def get_all_orders_for_admin(self, page: int = 1, per_page: int = 10, 
                                status_filter: str = None, vendor_filter: int = None,
                                search: str = None) -> Dict[str, Any]:
        """Mendapatkan semua pesanan untuk admin monitoring"""
        try:
            query = self.db.query(VendorOrder)
            
            # Apply filters
            if status_filter and status_filter != 'all':
                query = query.filter(VendorOrder.status == status_filter)
            
            if vendor_filter:
                query = query.filter(VendorOrder.vendor_id == vendor_filter)
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        VendorOrder.order_number.ilike(search_term),
                        VendorOrder.item_name.ilike(search_term),
                        VendorOrder.reference_id.ilike(search_term),
                        VendorOrder.vendor.has(Vendor.company_name.ilike(search_term))
                    )
                )
            
            # Get total count
            total = query.count()
            
            # Get paginated results
            offset = (page - 1) * per_page
            orders = query.order_by(desc(VendorOrder.created_at)).offset(offset).limit(per_page).all()
            
            # Calculate pagination info
            total_pages = (total + per_page - 1) // per_page
            
            return {
                'success': True,
                'data': [order.to_dict() for order in orders],
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
            logger.error(f"❌ Error getting all orders for admin: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': [],
                'pagination': {}
            }
    
    def get_recent_orders_for_vendor(self, vendor_id: int, minutes: int = 5) -> Dict[str, Any]:
        """Get recent orders untuk SSE updates"""
        try:
            from datetime import timedelta
            
            # Get orders from last N minutes
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            orders = self.db.query(VendorOrder).filter(
                and_(
                    VendorOrder.vendor_id == vendor_id,
                    VendorOrder.updated_at >= cutoff_time
                )
            ).order_by(desc(VendorOrder.updated_at)).all()
            
            return {
                'success': True,
                'data': [order.to_dict() for order in orders]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting recent orders: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': []
            }
    
    def get_vendor_orders_for_export(self, vendor_id: int, status_filter: str = None, 
                                   search: str = None) -> Dict[str, Any]:
        """Get orders untuk export (tanpa pagination)"""
        try:
            query = self.db.query(VendorOrder).filter(
                VendorOrder.vendor_id == vendor_id
            )
            
            # Apply filters
            if status_filter and status_filter != 'all':
                query = query.filter(VendorOrder.status == status_filter)
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        VendorOrder.order_number.ilike(search_term),
                        VendorOrder.item_name.ilike(search_term),
                        VendorOrder.reference_id.ilike(search_term)
                    )
                )
            
            # Get all orders (no pagination for export)
            orders = query.order_by(desc(VendorOrder.created_at)).all()
            
            return {
                'success': True,
                'data': [order.to_dict() for order in orders]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting orders for export: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': []
            }
    
    def update_order_status_with_history(self, order_id: int, new_status: str, 
                                       updated_by_user_id: int, notes: str = None) -> Dict[str, Any]:
        """Update order status dengan tracking history"""
        try:
            # Get order
            order = self.db.query(VendorOrder).filter(VendorOrder.id == order_id).first()
            if not order:
                return {
                    'success': False,
                    'message': 'Pesanan tidak ditemukan'
                }
            
            old_status = order.status
            order.status = new_status
            order.updated_at = datetime.utcnow()
            
            # Create status history entry
            try:
                from domains.vendor.models.vendor_order_models import VendorOrderStatusHistory
                history = VendorOrderStatusHistory(
                    order_id=order_id,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by_user_id=updated_by_user_id,
                    notes=notes,
                    changed_at=datetime.utcnow()
                )
                self.db.add(history)
            except Exception as e:
                logger.warning(f"Could not create status history: {str(e)}")
            
            self.db.commit()
            
            logger.info(f"✅ Updated order {order_id} status: {old_status} -> {new_status}")
            
            return {
                'success': True,
                'message': f'Status pesanan berhasil diupdate ke {new_status}',
                'order': order.to_dict()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating order status with history: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_order_status_history(self, order_id: int) -> Dict[str, Any]:
        """Get status history untuk order"""
        try:
            from models.vendor_order_models import VendorOrderStatusHistory
            
            history = self.db.query(VendorOrderStatusHistory).filter(
                VendorOrderStatusHistory.order_id == order_id
            ).order_by(desc(VendorOrderStatusHistory.changed_at)).all()
            
            return {
                'success': True,
                'data': [h.to_dict() for h in history]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting order status history: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': []
            }

    def send_order_reminders(self, days_threshold: int = 2) -> int:
        """Kirim reminder untuk pesanan yang belum dikonfirmasi"""
        try:
            threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
            
            pending_orders = self.db.query(VendorOrder).filter(
                and_(
                    VendorOrder.status == 'pending_confirmation',
                    VendorOrder.created_at <= threshold_date
                )
            ).all()
            
            reminders_sent = 0
            
            for order in pending_orders:
                notification = self.notification_service.create_order_notification(
                    vendor_id=order.vendor_id,
                    order_number=order.order_number,
                    notification_type='order_reminder'
                )
                
                if notification:
                    reminders_sent += 1
            
            logger.info(f"✅ Sent {reminders_sent} order reminders")
            return reminders_sent
            
        except Exception as e:
            logger.error(f"❌ Error sending order reminders: {str(e)}")
            return 0
