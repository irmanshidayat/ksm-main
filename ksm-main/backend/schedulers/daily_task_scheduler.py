#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Task Scheduler - Scheduler untuk notifikasi task harian
Digunakan untuk Daily Task Notification System
"""

import logging
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.base import JobLookupError
import pytz
from config.config import Config
from services.task_query_service import task_query_service
from services.report_bridge_service import report_bridge_service
from services.telegram_sender_service import telegram_sender_service

logger = logging.getLogger(__name__)

class DailyTaskScheduler:
    """Scheduler untuk daily task notification"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scheduler = None
        self.timezone = pytz.timezone(Config.TIMEZONE)
        self.report_time = Config.DAILY_REPORT_TIME
        self.scheduler_enabled = Config.SCHEDULER_ENABLED
        self.report_enabled = Config.REPORT_ENABLED
        self.weekdays_only = Config.REPORT_WEEKDAYS_ONLY
        self.error_notification_enabled = Config.ERROR_NOTIFICATION_ENABLED
        
        # Cache untuk prevent duplicate notifications
        self.last_report_date = None
        self.cache_ttl = 24 * 60 * 60  # 24 hours in seconds
    
    def start_scheduler(self):
        """Start scheduler jika enabled"""
        try:
            if not self.scheduler_enabled:
                self.logger.info("Scheduler disabled in configuration")
                return False
            
            if not self.report_enabled:
                self.logger.info("Report disabled in configuration")
                return False
            
            # Setup scheduler
            self.scheduler = BackgroundScheduler(
                timezone=self.timezone,
                job_defaults={
                    'coalesce': True,
                    'max_instances': 1,
                    'misfire_grace_time': 300  # 5 minutes
                }
            )
            
            # Add daily report job
            self._add_daily_report_job()
            
            # Start scheduler
            self.scheduler.start()
            
            self.logger.info(f"Daily task scheduler started successfully")
            self.logger.info(f"Report time: {self.report_time} {Config.TIMEZONE}")
            self.logger.info(f"Weekdays only: {self.weekdays_only}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting scheduler: {e}")
            return False
    
    def stop_scheduler(self):
        """Stop scheduler"""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown()
                self.logger.info("Daily task scheduler stopped")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}")
            return False
    
    def _add_daily_report_job(self):
        """Add daily report job ke scheduler"""
        try:
            # Parse report time
            hour, minute = self.report_time.split(':')
            hour = int(hour)
            minute = int(minute)
            
            # Setup cron trigger
            if self.weekdays_only:
                # Senin-Jumat saja
                trigger = CronTrigger(
                    day_of_week='mon-fri',
                    hour=hour,
                    minute=minute,
                    timezone=self.timezone
                )
            else:
                # Setiap hari
                trigger = CronTrigger(
                    hour=hour,
                    minute=minute,
                    timezone=self.timezone
                )
            
            # Add job
            self.scheduler.add_job(
                func=self.send_daily_report,
                trigger=trigger,
                id='daily_task_report',
                name='Daily Task Report',
                replace_existing=True
            )
            
            self.logger.info(f"Daily report job added: {self.report_time} {Config.TIMEZONE}")
            
        except Exception as e:
            self.logger.error(f"Error adding daily report job: {e}")
    
    def send_daily_report(self):
        """Send daily report - main job function"""
        from app import app
        with app.app_context():
            try:
                # Use timezone-aware date
                import pytz
                jakarta_tz = pytz.timezone('Asia/Jakarta')
                current_date = datetime.now(jakarta_tz).date()
                
                # Check cache untuk prevent duplicate
                if self.last_report_date == current_date:
                    self.logger.info(f"Report already sent for {current_date}, skipping")
                    return
                
                self.logger.info(f"Sending daily report for {current_date}")
                
                # Generate report
                success, report_data, message = report_bridge_service.generate_report(
                    current_date, None, None, None
                )
                
                if not success:
                    self.logger.error(f"Failed to generate report: {message}")
                    self._send_error_notification(f"Failed to generate report: {message}")
                    return
                
                # Send to Telegram
                telegram_success, telegram_message = telegram_sender_service.send_daily_task_report(
                    report_data
                )
                
                if telegram_success:
                    self.logger.info(f"Daily report sent successfully: {telegram_message}")
                    # Update cache
                    self.last_report_date = current_date
                else:
                    self.logger.error(f"Failed to send daily report: {telegram_message}")
                    self._send_error_notification(f"Failed to send daily report: {telegram_message}")
                
            except Exception as e:
                error_msg = f"Error in send_daily_report: {str(e)}"
                self.logger.error(error_msg)
                self._send_error_notification(error_msg)
    
    def _send_error_notification(self, error_message: str):
        """Send error notification ke admin"""
        try:
            if not self.error_notification_enabled:
                return
            
            # Send error notification
            success, message = telegram_sender_service.send_error_notification(error_message)
            
            if success:
                self.logger.info(f"Error notification sent: {message}")
            else:
                self.logger.error(f"Failed to send error notification: {message}")
                
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
    
    def send_manual_report(self, target_date: date = None, 
                          department_id: int = None,
                          category: str = None,
                          priority: str = None) -> tuple:
        """
        Send manual report (untuk testing)
        
        Args:
            target_date: Tanggal target
            department_id: Filter department
            category: Filter category
            priority: Filter priority
        
        Returns:
            tuple: (success, message)
        """
        from app import app
        with app.app_context():
            try:
                if target_date is None:
                    # Use timezone-aware date for consistency
                    import pytz
                    jakarta_tz = pytz.timezone('Asia/Jakarta')
                    target_date = datetime.now(jakarta_tz).date()
                
                self.logger.info(f"Sending manual report for {target_date}")
                
                # Generate report
                success, report_data, message = report_bridge_service.generate_report(
                    target_date, department_id, category, priority
                )
                
                if not success:
                    return False, f"Failed to generate report: {message}"
                
                # Send to Telegram
                telegram_success, telegram_message = telegram_sender_service.send_daily_task_report(
                    report_data
                )
                
                if telegram_success:
                    return True, f"Manual report sent successfully: {telegram_message}"
                else:
                    return False, f"Failed to send manual report: {telegram_message}"
                    
            except Exception as e:
                error_msg = f"Error in send_manual_report: {str(e)}"
                self.logger.error(error_msg)
                return False, error_msg
    
    def update_report_time(self, new_time: str) -> tuple:
        """
        Update waktu report scheduler
        
        Args:
            new_time: Waktu baru dalam format HH:MM
        
        Returns:
            tuple: (success, message)
        """
        try:
            self.logger.info(f"Updating report time to {new_time}")
            
            # Parse waktu baru
            try:
                hour, minute = new_time.split(':')
                hour = int(hour)
                minute = int(minute)
            except ValueError:
                return False, f"Invalid time format: {new_time}. Use HH:MM format"
            
            # Update report time
            self.report_time = new_time
            
            # Restart scheduler dengan waktu baru
            if self.scheduler and self.scheduler.running:
                # Remove job lama
                try:
                    self.scheduler.remove_job('daily_task_report')
                except JobLookupError:
                    pass
                
                # Add job baru dengan waktu yang diupdate
                self.scheduler.add_job(
                    func=self.send_daily_report,
                    trigger=CronTrigger(
                        day_of_week='mon-fri',
                        hour=hour,
                        minute=minute,
                        timezone=self.timezone
                    ),
                    id='daily_task_report',
                    name='Daily Task Report',
                    replace_existing=True
                )
                
                self.logger.info(f"Scheduler updated with new time: {new_time}")
                return True, f"Report time updated to {new_time}"
            else:
                return False, "Scheduler is not running"
                
        except Exception as e:
            error_msg = f"Error updating report time: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_scheduler_status(self) -> dict:
        """Get scheduler status"""
        try:
            if not self.scheduler:
                return {
                    'running': False,
                    'enabled': self.scheduler_enabled,
                    'report_enabled': self.report_enabled,
                    'timezone': Config.TIMEZONE,
                    'report_time': self.report_time,
                    'weekdays_only': self.weekdays_only
                }
            
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
            
            return {
                'running': self.scheduler.running,
                'enabled': self.scheduler_enabled,
                'report_enabled': self.report_enabled,
                'timezone': Config.TIMEZONE,
                'report_time': self.report_time,
                'weekdays_only': self.weekdays_only,
                'jobs': jobs,
                'last_report_date': self.last_report_date.isoformat() if self.last_report_date else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting scheduler status: {e}")
            return {
                'running': False,
                'error': str(e)
            }
    
    def test_connections(self) -> dict:
        """Test semua koneksi yang diperlukan"""
        try:
            results = {}
            
            # Test Agent AI connection
            agent_success, agent_message = report_bridge_service.test_agent_ai_connection()
            results['agent_ai'] = {
                'success': agent_success,
                'message': agent_message
            }
            
            # Test Telegram connection
            telegram_success, telegram_message = telegram_sender_service.test_connection()
            results['telegram'] = {
                'success': telegram_success,
                'message': telegram_message
            }
            
            # Test database connection
            try:
                summary = task_query_service.get_task_summary()
                results['database'] = {
                    'success': True,
                    'message': 'Database connection successful'
                }
            except Exception as e:
                results['database'] = {
                    'success': False,
                    'message': f'Database connection failed: {str(e)}'
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing connections: {e}")
            return {'error': str(e)}

# Singleton instance
daily_task_scheduler = DailyTaskScheduler()
