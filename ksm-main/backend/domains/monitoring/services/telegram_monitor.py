#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Monitoring System
Monitor dan logging untuk notifikasi Telegram
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from datetime import datetime, timedelta
from config.database import db
from domains.knowledge.models import TelegramSettings
import logging
import json

# Setup logging
logger = logging.getLogger('telegram_monitor')
logger.setLevel(logging.INFO)

# File handler
log_file = os.path.join(os.path.dirname(__file__), '../../../logs/telegram_notifications.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

class TelegramMonitor:
    """Monitor untuk notifikasi Telegram"""
    
    def __init__(self):
        self.stats = {
            'total_sent': 0,
            'total_failed': 0,
            'last_sent': None,
            'last_error': None
        }
    
    def log_notification_sent(self, message_type, success=True, error_message=None):
        """Log notifikasi yang dikirim"""
        if success:
            self.stats['total_sent'] += 1
            self.stats['last_sent'] = datetime.now()
            logger.info(f"✅ Notification sent: {message_type}")
        else:
            self.stats['total_failed'] += 1
            self.stats['last_error'] = {
                'timestamp': datetime.now(),
                'type': message_type,
                'error': error_message
            }
            logger.error(f"❌ Notification failed: {message_type} - {error_message}")
    
    def get_stats(self):
        """Ambil statistik monitoring"""
        return {
            **self.stats,
            'success_rate': (self.stats['total_sent'] / (self.stats['total_sent'] + self.stats['total_failed']) * 100) if (self.stats['total_sent'] + self.stats['total_failed']) > 0 else 0
        }
    
    def check_telegram_health(self):
        """Check kesehatan Telegram integration"""
        try:
            from app import app
            with app.app_context():
                settings = TelegramSettings.query.filter_by(
                    company_id='PT. Kian Santang Muliatama'
                ).first()
                
                if not settings:
                    logger.warning("⚠️  Telegram settings not found")
                    return {
                        'healthy': False,
                        'message': 'Telegram settings not configured'
                    }
                
                if not settings.is_active:
                    logger.warning("⚠️  Telegram bot is not active")
                    return {
                        'healthy': False,
                        'message': 'Telegram bot is not active'
                    }
                
                if not settings.bot_token or not settings.admin_chat_id:
                    logger.warning("⚠️  Telegram bot token or chat ID missing")
                    return {
                        'healthy': False,
                        'message': 'Bot token or chat ID not configured'
                    }
                
                logger.info("✅ Telegram integration is healthy")
                return {
                    'healthy': True,
                    'message': 'All systems operational',
                    'bot_token_present': bool(settings.bot_token),
                    'chat_id_present': bool(settings.admin_chat_id),
                    'is_active': settings.is_active
                }
                
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return {
                'healthy': False,
                'message': f'Health check error: {str(e)}'
            }
    
    def generate_monitoring_report(self):
        """Generate laporan monitoring"""
        stats = self.get_stats()
        health = self.check_telegram_health()
        
        report = f"""
╔══════════════════════════════════════════════════════════╗
║        TELEGRAM MONITORING REPORT                        ║
╚══════════════════════════════════════════════════════════╝

📅 Report Generated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

📊 STATISTICS:
   • Total Sent: {stats['total_sent']}
   • Total Failed: {stats['total_failed']}
   • Success Rate: {stats['success_rate']:.2f}%
   • Last Sent: {stats['last_sent'].strftime('%d/%m/%Y %H:%M:%S') if stats['last_sent'] else 'Never'}

🏥 HEALTH STATUS:
   • Status: {'✅ Healthy' if health['healthy'] else '❌ Unhealthy'}
   • Message: {health['message']}
   • Bot Token: {'✅ Configured' if health.get('bot_token_present') else '❌ Missing'}
   • Chat ID: {'✅ Configured' if health.get('chat_id_present') else '❌ Missing'}
   • Active: {'✅ Yes' if health.get('is_active') else '❌ No'}

{'⚠️  LAST ERROR:' if stats['last_error'] else ''}
{f"   • Time: {stats['last_error']['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}" if stats['last_error'] else ''}
{f"   • Type: {stats['last_error']['type']}" if stats['last_error'] else ''}
{f"   • Error: {stats['last_error']['error']}" if stats['last_error'] else ''}

╚══════════════════════════════════════════════════════════╝
"""
        
        logger.info(report)
        return report

# Global monitor instance
telegram_monitor = TelegramMonitor()

if __name__ == '__main__':
    # Test monitoring
    print("🔍 Running Telegram Monitor Health Check...")
    monitor = TelegramMonitor()
    report = monitor.generate_monitoring_report()
    print(report)

