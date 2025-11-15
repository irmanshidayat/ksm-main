#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Notification Service - Business Logic untuk Sistem Vendor Notifications
Service untuk mengelola notifikasi deadline dan status penawaran vendor
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from domains.vendor.models.vendor_models import (
    Vendor, VendorNotification, VendorPenawaran
)
from domains.inventory.models.request_pembelian_models import RequestPembelian

logger = logging.getLogger(__name__)


class VendorNotificationService:
    """Service untuk mengelola notifikasi vendor"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_notification(self, vendor_id: int, title: str, message: str, 
                          notification_type: str, related_request_id: int = None,
                          related_penawaran_id: int = None) -> Optional[VendorNotification]:
        """Membuat notifikasi baru untuk vendor"""
        try:
            notification = VendorNotification(
                vendor_id=vendor_id,
                subject=title,  # Use subject column for title
                message=message,
                notification_type=notification_type,  # Use notification_type column
                related_request_id=related_request_id,
                related_penawaran_id=related_penawaran_id,
                status='sent',  # Set default status
                sent_at=datetime.utcnow()
            )
            
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            
            logger.info(f"✅ Notification created for vendor {vendor_id}: {title}")
            return notification
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating notification: {str(e)}")
            return None
    
    def get_vendor_notifications(self, vendor_id: int, limit: int = 50, 
                               unread_only: bool = False) -> List[Dict[str, Any]]:
        """Mendapatkan notifikasi vendor"""
        try:
            query = self.db.query(VendorNotification).filter(
                VendorNotification.vendor_id == vendor_id
            )
            
            if unread_only:
                query = query.filter(VendorNotification.status != 'read')
            
            notifications = query.order_by(
                desc(VendorNotification.created_at)
            ).limit(limit).all()
            
            return [notification.to_dict() for notification in notifications]
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor notifications: {str(e)}")
            return []
    
    def get_vendor_notifications_paginated(self, vendor_id: int, page: int = 1, 
                                         per_page: int = 10, unread_only: bool = False) -> Dict[str, Any]:
        """Mendapatkan notifikasi vendor dengan pagination"""
        try:
            query = self.db.query(VendorNotification).filter(
                VendorNotification.vendor_id == vendor_id
            )
            
            if unread_only:
                query = query.filter(VendorNotification.status != 'read')
            
            # Get total count
            total = query.count()
            
            # Get paginated results
            notifications = query.order_by(
                desc(VendorNotification.created_at)
            ).offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'notifications': [notification.to_dict() for notification in notifications],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page,
                    'has_next': page * per_page < total,
                    'has_prev': page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting paginated vendor notifications: {str(e)}")
            return {
                'notifications': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }
    
    def mark_notification_as_read(self, notification_id: int, vendor_id: int) -> bool:
        """Tandai notifikasi sebagai sudah dibaca"""
        try:
            notification = self.db.query(VendorNotification).filter(
                and_(
                    VendorNotification.id == notification_id,
                    VendorNotification.vendor_id == vendor_id
                )
            ).first()
            
            if not notification:
                return False
            
            notification.status = 'read'
            notification.read_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"✅ Notification {notification_id} marked as read")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error marking notification as read: {str(e)}")
            return False
    
    def mark_notification_read(self, vendor_id: int, notification_id: int) -> bool:
        """Alias untuk mark_notification_as_read untuk kompatibilitas"""
        return self.mark_notification_as_read(notification_id, vendor_id)
    
    def mark_all_notifications_read(self, vendor_id: int) -> int:
        """Alias untuk mark_all_notifications_as_read untuk kompatibilitas"""
        try:
            notifications = self.db.query(VendorNotification).filter(
                and_(
                    VendorNotification.vendor_id == vendor_id,
                    VendorNotification.status != 'read'
                )
            ).all()
            
            count = 0
            for notification in notifications:
                notification.status = 'read'
                notification.read_at = datetime.utcnow()
                count += 1
            
            self.db.commit()
            
            logger.info(f"✅ {count} notifications marked as read for vendor {vendor_id}")
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error marking all notifications as read: {str(e)}")
            return 0
    
    def mark_all_notifications_as_read(self, vendor_id: int) -> bool:
        """Tandai semua notifikasi vendor sebagai sudah dibaca"""
        try:
            notifications = self.db.query(VendorNotification).filter(
                and_(
                    VendorNotification.vendor_id == vendor_id,
                    VendorNotification.status != 'read'
                )
            ).all()
            
            for notification in notifications:
                notification.status = 'read'
                notification.read_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"✅ All notifications marked as read for vendor {vendor_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error marking all notifications as read: {str(e)}")
            return False
    
    def get_unread_count(self, vendor_id: int) -> int:
        """Mendapatkan jumlah notifikasi yang belum dibaca"""
        try:
            count = self.db.query(VendorNotification).filter(
                and_(
                    VendorNotification.vendor_id == vendor_id,
                    VendorNotification.status != 'read'
                )
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error getting unread count: {str(e)}")
            return 0
    
    def create_deadline_warning_notifications(self) -> int:
        """Membuat notifikasi peringatan deadline untuk semua vendor"""
        try:
            # Get requests yang deadline dalam 24 jam ke depan
            deadline_threshold = datetime.utcnow() + timedelta(hours=24)
            
            # Query dengan error handling untuk kolom reference_id
            try:
                requests = self.db.query(RequestPembelian).filter(
                    and_(
                        RequestPembelian.status.in_(['submitted', 'vendor_uploading']),
                        RequestPembelian.vendor_upload_deadline <= deadline_threshold,
                        RequestPembelian.vendor_upload_deadline > datetime.utcnow()
                    )
                ).all()
            except Exception as db_error:
                # Jika kolom reference_id tidak ada, gunakan query tanpa reference_id
                if 'reference_id' in str(db_error):
                    logger.warning(f"⚠️ Kolom reference_id tidak ditemukan, menggunakan query alternatif")
                    # Query hanya dengan kolom yang pasti ada
                    requests = self.db.query(RequestPembelian).filter(
                        and_(
                            RequestPembelian.status.in_(['submitted', 'vendor_uploading']),
                            RequestPembelian.vendor_upload_deadline <= deadline_threshold,
                            RequestPembelian.vendor_upload_deadline > datetime.utcnow()
                        )
                    ).with_entities(
                        RequestPembelian.id,
                        RequestPembelian.title,
                        RequestPembelian.vendor_upload_deadline,
                        RequestPembelian.status
                    ).all()
                    # Convert ke format yang bisa digunakan dengan proper object
                    class RequestWrapper:
                        def __init__(self, id, title, vendor_upload_deadline, status):
                            self.id = id
                            self.title = title
                            self.vendor_upload_deadline = vendor_upload_deadline
                            self.status = status
                            self.reference_id = f"REQ-{id}"  # Fallback reference_id
                    
                    requests = [RequestWrapper(r.id, r.title, r.vendor_upload_deadline, r.status) for r in requests]
                else:
                    raise
            
            notifications_created = 0
            
            for request in requests:
                # Get vendors yang relevan dengan request ini
                # (Ini akan menggunakan logic yang sama dengan VendorRequestService)
                vendors = self._get_relevant_vendors_for_request(request.id)
                
                for vendor in vendors:
                    # Check if vendor already has penawaran for this request
                    existing_penawaran = self.db.query(VendorPenawaran).filter(
                        and_(
                            VendorPenawaran.vendor_id == vendor.id,
                            VendorPenawaran.request_id == request.id
                        )
                    ).first()
                    
                    if not existing_penawaran:
                        # Calculate hours remaining
                        hours_remaining = int((request.vendor_upload_deadline - datetime.utcnow()).total_seconds() / 3600)
                        
                        title = f"⏰ Deadline Upload Mendekat"
                        message = f"Request #{request.reference_id} - {request.title} akan berakhir dalam {hours_remaining} jam. Segera upload penawaran Anda!"
                        
                        notification = self.create_notification(
                            vendor_id=vendor.id,
                            title=title,
                            message=message,
                            notification_type='upload_reminder',
                            related_request_id=request.id
                        )
                        
                        if notification:
                            notifications_created += 1
            
            logger.info(f"[SUCCESS] Created {notifications_created} deadline warning notifications")
            return notifications_created
            
        except Exception as e:
            logger.error(f"❌ Error creating deadline warning notifications: {str(e)}")
            return 0
    
    def create_status_update_notifications(self, penawaran_id: int, old_status: str, new_status: str) -> bool:
        """Membuat notifikasi update status penawaran"""
        try:
            penawaran = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.id == penawaran_id
            ).first()
            
            if not penawaran:
                return False
            
            # Determine notification content based on status change
            if new_status == 'under_review':
                title = "Penawaran Sedang Ditinjau"
                message = f"Penawaran #{penawaran.reference_id} sedang dalam proses peninjauan oleh tim procurement."
                notification_type = 'analysis_complete'
            elif new_status == 'selected':
                title = "Penawaran Dipilih!"
                message = f"Selamat! Penawaran #{penawaran.reference_id} telah dipilih sebagai pemenang."
                notification_type = 'analysis_complete'
            elif new_status == 'rejected':
                title = "Penawaran Tidak Dipilih"
                message = f"Penawaran #{penawaran.reference_id} tidak dipilih untuk request ini."
                notification_type = 'analysis_complete'
            else:
                return True  # No notification needed for other status changes
            
            notification = self.create_notification(
                vendor_id=penawaran.vendor_id,
                title=title,
                message=message,
                notification_type=notification_type,
                related_request_id=penawaran.request_id,
                related_penawaran_id=penawaran.id
            )
            
            return notification is not None
            
        except Exception as e:
            logger.error(f"❌ Error creating status update notification: {str(e)}")
            return False
    
    def create_new_request_notifications(self, request_id: int) -> int:
        """Membuat notifikasi request baru untuk vendor yang relevan"""
        try:
            request = self.db.query(RequestPembelian).filter(
                RequestPembelian.id == request_id
            ).first()
            
            if not request:
                return 0
            
            # Get relevant vendors
            vendors = self._get_relevant_vendors_for_request(request_id)
            
            notifications_created = 0
            
            for vendor in vendors:
                title = "Request Pembelian Baru"
                message = f"Request pembelian baru: #{request.reference_id} - {request.title}. Deadline upload: {request.vendor_upload_deadline.strftime('%d %B %Y %H:%M')}"
                
                notification = self.create_notification(
                    vendor_id=vendor.id,
                    title=title,
                    message=message,
                    notification_type='request_available',
                    related_request_id=request_id
                )
                
                if notification:
                    notifications_created += 1
            
            logger.info(f"✅ Created {notifications_created} new request notifications")
            return notifications_created
            
        except Exception as e:
            logger.error(f"❌ Error creating new request notifications: {str(e)}")
            return 0
    
    def cleanup_old_notifications(self, days_old: int = 30) -> int:
        """Hapus notifikasi lama untuk menjaga performa database"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_notifications = self.db.query(VendorNotification).filter(
                and_(
                    VendorNotification.created_at < cutoff_date,
                    VendorNotification.status == 'read'
                )
            ).all()
            
            deleted_count = 0
            for notification in old_notifications:
                self.db.delete(notification)
                deleted_count += 1
            
            self.db.commit()
            
            logger.info(f"[SUCCESS] Cleaned up {deleted_count} old notifications")
            return deleted_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error cleaning up old notifications: {str(e)}")
            return 0
    
    def _get_relevant_vendors_for_request(self, request_id: int) -> List[Vendor]:
        """Mendapatkan vendor yang relevan dengan request (helper method)"""
        try:
            # This is a simplified version - in real implementation,
            # you would join with request items and vendor categories
            # For now, we'll get all approved vendors
            vendors = self.db.query(Vendor).filter(
                Vendor.status == 'approved'
            ).all()
            
            return vendors
            
        except Exception as e:
            logger.error(f"❌ Error getting relevant vendors: {str(e)}")
            return []
    
    def create_order_notification(self, vendor_id: int, order_number: str, 
                                 notification_type: str, order_id: int = None) -> Optional[VendorNotification]:
        """Membuat notifikasi untuk order/pesanan vendor"""
        try:
            # Determine notification content based on type
            if notification_type == 'order_approved':
                title = f"Pesanan Disetujui - {order_number}"
                message = f"Pesanan {order_number} telah disetujui. Silakan konfirmasi dan mulai proses pengiriman."
            elif notification_type == 'order_status_update':
                title = f"Update Status Pesanan - {order_number}"
                message = f"Status pesanan {order_number} telah diperbarui. Silakan cek detail pesanan."
            elif notification_type == 'order_reminder':
                title = f"Reminder Konfirmasi Pesanan - {order_number}"
                message = f"Pesanan {order_number} masih menunggu konfirmasi Anda. Silakan segera konfirmasi."
            else:
                title = f"Update Pesanan - {order_number}"
                message = f"Ada update untuk pesanan {order_number}. Silakan cek detail pesanan."
            
            notification = self.create_notification(
                vendor_id=vendor_id,
                title=title,
                message=message,
                notification_type=notification_type,
                related_request_id=None,  # Will be set based on order
                related_penawaran_id=None
            )
            
            return notification
            
        except Exception as e:
            logger.error(f"❌ Error creating order notification: {str(e)}")
            return None
    
    def create_admin_order_notification(self, order_number: str, vendor_name: str, 
                                       notification_type: str, order_id: int = None) -> bool:
        """Membuat notifikasi untuk admin tentang update order vendor"""
        try:
            # Get admin users (you might want to filter by role)
            from domains.auth.models.auth_models import User
            admin_users = self.db.query(User).filter(
                User.role.in_(['admin', 'super_admin', 'manager'])
            ).all()
            
            notifications_created = 0
            
            for admin in admin_users:
                if notification_type == 'vendor_confirmed_order':
                    title = f"Vendor Konfirmasi Pesanan - {order_number}"
                    message = f"Vendor {vendor_name} telah mengkonfirmasi pesanan {order_number}."
                elif notification_type == 'vendor_updated_status':
                    title = f"Vendor Update Status - {order_number}"
                    message = f"Vendor {vendor_name} telah memperbarui status pesanan {order_number}."
                else:
                    title = f"Update Pesanan Vendor - {order_number}"
                    message = f"Ada update dari vendor {vendor_name} untuk pesanan {order_number}."
                
                # Create notification for admin (using regular notification system)
                from domains.notification.models.notification_models import Notification
                admin_notification = Notification(
                    user_id=admin.id,
                    type='vendor_order_update',
                    title=title,
                    message=message,
                    data={'order_number': order_number, 'vendor_name': vendor_name},
                    priority='normal',
                    action_required=False
                )
                
                self.db.add(admin_notification)
                notifications_created += 1
            
            self.db.commit()
            logger.info(f"✅ Created {notifications_created} admin notifications for order {order_number}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating admin order notification: {str(e)}")
            return False
    
    def get_notification_statistics(self, vendor_id: int) -> Dict[str, Any]:
        """Mendapatkan statistik notifikasi vendor"""
        try:
            total_notifications = self.db.query(VendorNotification).filter(
                VendorNotification.vendor_id == vendor_id
            ).count()
            
            unread_notifications = self.db.query(VendorNotification).filter(
                and_(
                    VendorNotification.vendor_id == vendor_id,
                    VendorNotification.status != 'read'
                )
            ).count()
            
            # Get notifications by type
            deadline_warnings = self.db.query(VendorNotification).filter(
                and_(
                    VendorNotification.vendor_id == vendor_id,
                    VendorNotification.notification_type == 'upload_reminder'
                )
            ).count()
            
            status_updates = self.db.query(VendorNotification).filter(
                and_(
                    VendorNotification.vendor_id == vendor_id,
                    VendorNotification.notification_type == 'analysis_complete'
                )
            ).count()
            
            new_requests = self.db.query(VendorNotification).filter(
                and_(
                    VendorNotification.vendor_id == vendor_id,
                    VendorNotification.notification_type == 'request_available'
                )
            ).count()
            
            # Add order notifications
            order_notifications = self.db.query(VendorNotification).filter(
                and_(
                    VendorNotification.vendor_id == vendor_id,
                    VendorNotification.notification_type.in_(['order_approved', 'order_status_update', 'order_reminder'])
                )
            ).count()
            
            return {
                'total_notifications': total_notifications,
                'unread_notifications': unread_notifications,
                'deadline_warnings': deadline_warnings,
                'status_updates': status_updates,
                'new_requests': new_requests,
                'order_notifications': order_notifications
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting notification statistics: {str(e)}")
            return {
                'total_notifications': 0,
                'unread_notifications': 0,
                'deadline_warnings': 0,
                'status_updates': 0,
                'new_requests': 0,
                'order_notifications': 0
            }
