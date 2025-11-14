#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification Scheduler - Background Task untuk Notifikasi Otomatis
Scheduler untuk mengirim notifikasi deadline dan status update secara otomatis
"""

import time
import logging
from datetime import datetime, timedelta
from threading import Thread, Timer
from sqlalchemy.orm import sessionmaker

from config.database import db
from domains.vendor.services.vendor_notification_service import VendorNotificationService

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """Scheduler untuk notifikasi otomatis vendor menggunakan threading.Timer"""
    
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        self.deadline_timer = None
        self.cleanup_timer = None
    
    def start(self):
        """Mulai scheduler"""
        if self.running:
            logger.warning("[WARNING] Notification scheduler already running")
            return
        
        self.running = True
        
        # Schedule tasks using Timer
        self._schedule_deadline_check()
        self._schedule_cleanup()
        
        logger.info("[SUCCESS] Notification scheduler started")
    
    def stop(self):
        """Hentikan scheduler"""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel timers
        if self.deadline_timer:
            self.deadline_timer.cancel()
        if self.cleanup_timer:
            self.cleanup_timer.cancel()
        
        logger.info("🛑 Notification scheduler stopped")
    
    def _schedule_deadline_check(self):
        """Schedule deadline check every hour"""
        if not self.running:
            return
        
        try:
            from flask import current_app
            with current_app.app_context():
                self.check_deadline_warnings()
        except Exception as e:
            logger.error(f"[ERROR] Error in deadline check: {str(e)}")
        
        # Schedule next check in 1 hour
        self.deadline_timer = Timer(3600, self._schedule_deadline_check)
        self.deadline_timer.daemon = True
        self.deadline_timer.start()
    
    def _schedule_cleanup(self):
        """Schedule cleanup every 6 hours"""
        if not self.running:
            return
        
        try:
            from flask import current_app
            with current_app.app_context():
                self.cleanup_old_notifications()
        except Exception as e:
            logger.error(f"[ERROR] Error in cleanup: {str(e)}")
        
        # Schedule next cleanup in 6 hours
        self.cleanup_timer = Timer(21600, self._schedule_cleanup)
        self.cleanup_timer.daemon = True
        self.cleanup_timer.start()
    
    def check_deadline_warnings(self):
        """Cek dan kirim notifikasi peringatan deadline"""
        try:
            logger.info("[NOTIF] Checking deadline warnings...")
            
            notification_service = VendorNotificationService(db.session)
            notifications_created = notification_service.create_deadline_warning_notifications()
            
            if notifications_created > 0:
                logger.info(f"[SUCCESS] Created {notifications_created} deadline warning notifications")
            else:
                logger.info("[INFO] No deadline warnings needed")
                
        except Exception as e:
            logger.error(f"[ERROR] Error checking deadline warnings: {str(e)}")
    
    def cleanup_old_notifications(self):
        """Hapus notifikasi lama"""
        try:
            logger.info("[CLEANUP] Cleaning up old notifications...")
            
            notification_service = VendorNotificationService(db.session)
            deleted_count = notification_service.cleanup_old_notifications(days_old=30)
            
            if deleted_count > 0:
                logger.info(f"[SUCCESS] Cleaned up {deleted_count} old notifications")
            else:
                logger.info("[INFO] No old notifications to clean up")
                
        except Exception as e:
            logger.error(f"[ERROR] Error cleaning up old notifications: {str(e)}")
    
    def send_immediate_notification(self, vendor_id: int, title: str, message: str, 
                                  notification_type: str, related_request_id: int = None,
                                  related_penawaran_id: int = None):
        """Kirim notifikasi langsung (untuk testing atau manual trigger)"""
        try:
            notification_service = VendorNotificationService(db.session)
            notification = notification_service.create_notification(
                vendor_id=vendor_id,
                title=title,
                message=message,
                notification_type=notification_type,
                related_request_id=related_request_id,
                related_penawaran_id=related_penawaran_id
            )
            
            if notification:
                logger.info(f"[SUCCESS] Immediate notification sent to vendor {vendor_id}: {title}")
                return True
            else:
                logger.error(f"[ERROR] Failed to send immediate notification to vendor {vendor_id}")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] Error sending immediate notification: {str(e)}")
            return False
    
    def get_scheduler_status(self):
        """Dapatkan status scheduler"""
        return {
            'running': self.running,
            'deadline_timer_active': self.deadline_timer is not None and self.deadline_timer.is_alive(),
            'cleanup_timer_active': self.cleanup_timer is not None and self.cleanup_timer.is_alive(),
            'scheduled_jobs': 2 if self.running else 0
        }


# Global scheduler instance
notification_scheduler = NotificationScheduler()


def start_notification_scheduler():
    """Start notification scheduler (dipanggil dari app.py)"""
    notification_scheduler.start()


def stop_notification_scheduler():
    """Stop notification scheduler (dipanggil saat shutdown)"""
    notification_scheduler.stop()


def get_scheduler_status():
    """Get scheduler status"""
    return notification_scheduler.get_scheduler_status()
