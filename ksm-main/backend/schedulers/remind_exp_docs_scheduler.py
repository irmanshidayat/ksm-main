from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from config.database import db
from services.remind_exp_docs_service import RemindExpDocsService
from controllers.telegram_controller import TelegramController
from utils.logger import get_logger
from datetime import datetime, date, timedelta
import requests
import json
import os
from flask import current_app

logger = get_logger(__name__)

class RemindExpDocsScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.service = RemindExpDocsService()
        self.telegram_controller = TelegramController()
        self.is_running = False
        self.app = None  # Will be set when starting scheduler
        
        # Load configuration from environment variables
        self.notification_time = os.getenv('REMIND_EXP_NOTIFICATION_TIME', '09:00')
        self.days_ahead = int(os.getenv('REMIND_EXP_DAYS_AHEAD', '30'))
        self.urgent_days = int(os.getenv('REMIND_EXP_URGENT_DAYS', '7'))
        self.notifications_enabled = os.getenv('REMIND_EXP_NOTIFICATIONS_ENABLED', 'true').lower() == 'true'
        self.scheduler_enabled = os.getenv('REMIND_EXP_SCHEDULER_ENABLED', 'true').lower() == 'true'
        self.weekdays_only = os.getenv('REMIND_EXP_WEEKDAYS_ONLY', 'true').lower() == 'true'
        
        # Parse notification time
        try:
            hour, minute = self.notification_time.split(':')
            self.notification_hour = int(hour)
            self.notification_minute = int(minute)
        except:
            self.notification_hour = 9
            self.notification_minute = 0
    
    def set_app(self, app):
        """Set Flask app instance untuk app context"""
        self.app = app
    
    def start_scheduler(self):
        """Memulai scheduler untuk notifikasi reminder"""
        try:
            if not self.is_running and self.scheduler_enabled and self.notifications_enabled:
                logger.info(f"Starting Remind Exp Docs scheduler with notification time: {self.notification_time}")
                
                # Jalankan setiap hari pada waktu yang dikonfigurasi
                self.scheduler.add_job(
                    func=self.check_expiring_documents,
                    trigger=CronTrigger(hour=self.notification_hour, minute=self.notification_minute),
                    id='remind_exp_docs_daily_check',
                    name='Daily Expiring Documents Check',
                    replace_existing=True
                )
                
                # Jalankan setiap hari 2 jam setelah notifikasi utama untuk dokumen urgent
                urgent_hour = (self.notification_hour + 2) % 24
                self.scheduler.add_job(
                    func=self.check_urgent_expiring_documents,
                    trigger=CronTrigger(hour=urgent_hour, minute=self.notification_minute),
                    id='remind_exp_docs_urgent_check',
                    name='Urgent Expiring Documents Check',
                    replace_existing=True
                )
                
                # Jalankan setiap hari 4 jam setelah notifikasi utama untuk update status
                update_hour = (self.notification_hour + 4) % 24
                self.scheduler.add_job(
                    func=self.update_expired_status,
                    trigger=CronTrigger(hour=update_hour, minute=self.notification_minute),
                    id='remind_exp_docs_status_update',
                    name='Update Expired Documents Status',
                    replace_existing=True
                )
                
                self.scheduler.start()
                self.is_running = True
                logger.info("Remind Exp Docs Scheduler started successfully")
                
        except Exception as e:
            logger.error(f"Error starting remind exp docs scheduler: {str(e)}")
    
    def stop_scheduler(self):
        """Menghentikan scheduler"""
        try:
            if self.is_running:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("Remind Exp Docs Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping remind exp docs scheduler: {str(e)}")
    
    def check_expiring_documents(self):
        """Cek dokumen yang akan expired dan kirim notifikasi"""
        # Use stored app instance
        if not self.app:
            logger.error("App instance not set. Call set_app() first.")
            return
        
        with self.app.app_context():
            try:
                logger.info(f"Starting daily expiring documents check for {self.days_ahead} days...")
                
                # Check if notifications are enabled
                if not self.notifications_enabled:
                    logger.info("Remind Exp Docs notifications are disabled")
                    return
                
                # Check if it's weekday only and today is weekend
                if self.weekdays_only and datetime.now().weekday() >= 5:  # Saturday = 5, Sunday = 6
                    logger.info("Skipping notification on weekend (weekdays_only=true)")
                    return
                
                # Ambil dokumen yang akan expired berdasarkan konfigurasi
                expiring_documents = self.service.get_expiring_documents(db.session, self.days_ahead)
                
                if not expiring_documents:
                    logger.info(f"No expiring documents found in {self.days_ahead} days")
                    return
                
                # Buat pesan notifikasi
                message = self._create_expiring_documents_message(expiring_documents, self.days_ahead)
                
                # Kirim notifikasi ke Telegram
                self._send_telegram_notification(message)
                
                logger.info(f"Expiring documents notification sent for {len(expiring_documents)} documents")
                
            except Exception as e:
                logger.error(f"Error in check_expiring_documents: {str(e)}")
            finally:
                pass
    
    def check_urgent_expiring_documents(self):
        """Cek dokumen yang akan expired dalam beberapa hari dan kirim notifikasi urgent"""
        # Use stored app instance
        if not self.app:
            logger.error("App instance not set. Call set_app() first.")
            return
        
        with self.app.app_context():
            try:
                logger.info(f"Starting urgent expiring documents check for {self.urgent_days} days...")
                
                # Check if notifications are enabled
                if not self.notifications_enabled:
                    logger.info("Remind Exp Docs notifications are disabled")
                    return
                
                # Check if it's weekday only and today is weekend
                if self.weekdays_only and datetime.now().weekday() >= 5:  # Saturday = 5, Sunday = 6
                    logger.info("Skipping urgent notification on weekend (weekdays_only=true)")
                    return
                
                # Ambil dokumen yang akan expired berdasarkan konfigurasi urgent
                urgent_documents = self.service.get_expiring_documents(db.session, self.urgent_days)
                
                if not urgent_documents:
                    logger.info(f"No urgent expiring documents found in {self.urgent_days} days")
                    return
                
                # Buat pesan notifikasi urgent
                message = self._create_urgent_expiring_documents_message(urgent_documents)
                
                # Kirim notifikasi ke Telegram
                self._send_telegram_notification(message)
                
                logger.info(f"Urgent expiring documents notification sent for {len(urgent_documents)} documents")
                
            except Exception as e:
                logger.error(f"Error in check_urgent_expiring_documents: {str(e)}")
            finally:
                pass
    
    def update_expired_status(self):
        """Update status dokumen yang sudah expired"""
        # Use stored app instance
        if not self.app:
            logger.error("App instance not set. Call set_app() first.")
            return
        
        with self.app.app_context():
            try:
                logger.info("Starting expired status update...")
                
                # Update status dokumen yang sudah expired
                updated_count = self.service.update_expired_status(db.session)
                
                if updated_count > 0:
                    # Kirim notifikasi jika ada dokumen yang expired
                    message = f"⚠️ *UPDATE STATUS DOKUMEN*\n\n"
                    message += f"📋 {updated_count} dokumen telah diupdate status menjadi EXPIRED\n"
                    message += f"🕐 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                    message += "Silakan periksa sistem untuk detail lebih lanjut."
                    
                    self._send_telegram_notification(message)
                    
                    logger.info(f"Updated {updated_count} documents to expired status")
                else:
                    logger.info("No documents to update to expired status")
                
            except Exception as e:
                logger.error(f"Error in update_expired_status: {str(e)}")
            finally:
                pass
    
    def _create_expiring_documents_message(self, documents, days_ahead):
        """Buat pesan notifikasi untuk dokumen yang akan expired"""
        try:
            message = f"📋 *REMINDER DOKUMEN AKAN EXPIRED*\n\n"
            message += f"🔔 Ditemukan {len(documents)} dokumen yang akan expired dalam {days_ahead} hari\n\n"
            
            for i, doc in enumerate(documents[:10], 1):  # Maksimal 10 dokumen
                days_remaining = (doc.expiry_date - date.today()).days
                message += f"{i}. *{doc.document_name}*\n"
                message += f"   📅 Expired: {doc.expiry_date.strftime('%d/%m/%Y')}\n"
                message += f"   ⏰ Sisa: {days_remaining} hari\n"
                if doc.document_number:
                    message += f"   📄 No: {doc.document_number}\n"
                if doc.issuer:
                    message += f"   🏢 Penerbit: {doc.issuer}\n"
                message += "\n"
            
            if len(documents) > 10:
                message += f"... dan {len(documents) - 10} dokumen lainnya\n\n"
            
            message += f"🕐 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            message += "Silakan periksa sistem untuk detail lengkap."
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating expiring documents message: {str(e)}")
            return "Error creating notification message"
    
    def _create_urgent_expiring_documents_message(self, documents):
        """Buat pesan notifikasi urgent untuk dokumen yang akan expired"""
        try:
            message = f"🚨 *URGENT: DOKUMEN AKAN EXPIRED*\n\n"
            message += f"⚠️ Ditemukan {len(documents)} dokumen yang akan expired dalam 7 hari!\n\n"
            
            for i, doc in enumerate(documents, 1):
                days_remaining = (doc.expiry_date - date.today()).days
                urgency_icon = "🔴" if days_remaining <= 3 else "🟡"
                
                message += f"{urgency_icon} {i}. *{doc.document_name}*\n"
                message += f"   📅 Expired: {doc.expiry_date.strftime('%d/%m/%Y')}\n"
                message += f"   ⏰ Sisa: {days_remaining} hari\n"
                if doc.document_number:
                    message += f"   📄 No: {doc.document_number}\n"
                if doc.issuer:
                    message += f"   🏢 Penerbit: {doc.issuer}\n"
                message += "\n"
            
            message += f"🕐 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            message += "⚠️ SEGERA TINDAK LANJUTI!"
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating urgent expiring documents message: {str(e)}")
            return "Error creating urgent notification message"
    
    def _send_telegram_notification(self, message):
        """Kirim notifikasi ke Telegram"""
        try:
            # Gunakan telegram controller yang sudah ada
            result = self.telegram_controller.send_message_to_admin(message)
            
            if result.get('success'):
                logger.info("Telegram notification sent successfully")
            else:
                logger.error(f"Failed to send Telegram notification: {result.get('message')}")
                
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {str(e)}")
    
    def manual_check_expiring_documents(self, days_ahead=30):
        """Manual check untuk testing"""
        try:
            documents = self.service.get_expiring_documents(db.session, days_ahead)
            
            if documents:
                message = self._create_expiring_documents_message(documents, days_ahead)
                self._send_telegram_notification(message)
                return f"Manual check completed: {len(documents)} documents found"
            else:
                return "Manual check completed: No expiring documents found"
                
        except Exception as e:
            logger.error(f"Error in manual check: {str(e)}")
            return f"Error in manual check: {str(e)}"
        finally:
            pass
    
    def test_telegram_connection(self):
        """Test koneksi Telegram untuk testing"""
        try:
            # Test pengiriman pesan sederhana
            test_message = "🧪 *TEST TELEGRAM CONNECTION*\n\n"
            test_message += f"📅 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            test_message += "✅ Koneksi Telegram berfungsi dengan baik!"
            
            result = self._send_telegram_notification(test_message)
            return result
            
        except Exception as e:
            logger.error(f"Error testing telegram connection: {str(e)}")
            return f"Error testing telegram connection: {str(e)}"
    
    def create_test_scenarios(self):
        """Buat skenario test untuk notifikasi"""
        try:
            test_scenarios = {
                'normal_reminder': {
                    'days_ahead': 30,
                    'message_type': 'normal',
                    'description': 'Test normal reminder untuk dokumen yang akan expired dalam 30 hari'
                },
                'urgent_reminder': {
                    'days_ahead': 7,
                    'message_type': 'urgent',
                    'description': 'Test urgent reminder untuk dokumen yang akan expired dalam 7 hari'
                },
                'expired_update': {
                    'days_ahead': 0,
                    'message_type': 'expired',
                    'description': 'Test update status dokumen yang sudah expired'
                }
            }
            
            return test_scenarios
            
        except Exception as e:
            logger.error(f"Error creating test scenarios: {str(e)}")
            return {}
    
    def validate_notification_format(self, message):
        """Validasi format notifikasi"""
        try:
            # Cek apakah pesan mengandung elemen yang diperlukan
            required_elements = [
                '📋',  # Icon dokumen
                '📅',  # Icon tanggal
                '⏰',  # Icon waktu
                '🔔'   # Icon notifikasi
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in message:
                    missing_elements.append(element)
            
            if missing_elements:
                return {
                    'valid': False,
                    'missing_elements': missing_elements,
                    'message': f'Missing required elements: {missing_elements}'
                }
            else:
                return {
                    'valid': True,
                    'message': 'Notification format is valid'
                }
                
        except Exception as e:
            logger.error(f"Error validating notification format: {str(e)}")
            return {
                'valid': False,
                'message': f'Error validating format: {str(e)}'
            }

# Global instance
remind_exp_docs_scheduler = RemindExpDocsScheduler()
