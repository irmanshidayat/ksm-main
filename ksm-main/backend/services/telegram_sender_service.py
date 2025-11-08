#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Sender Service - Service untuk kirim notifikasi ke Telegram
Digunakan untuk Daily Task Notification System
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from config.config import Config

logger = logging.getLogger(__name__)

class TelegramSenderService:
    """Service untuk kirim pesan ke Telegram"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.default_chat_id = Config.TELEGRAM_DEFAULT_CHAT_ID
        self.admin_chat_id = Config.ADMIN_ALERT_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.max_retries = 3
        self.retry_delay = 30  # seconds
    
    def send_message(self, chat_id: str, message: str, parse_mode: str = "Markdown") -> Tuple[bool, str]:
        """
        Kirim pesan ke Telegram
        
        Args:
            chat_id: ID chat Telegram
            message: Pesan yang akan dikirim
            parse_mode: Mode parsing (Markdown, HTML)
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not self.bot_token:
            error_msg = "Bot token tidak tersedia"
            self.logger.error(error_msg)
            return False, error_msg
        
        if not chat_id:
            error_msg = "Chat ID tidak tersedia"
            self.logger.error(error_msg)
            return False, error_msg
        
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Sending message to chat {chat_id} (attempt {attempt + 1})")
                
                response = requests.post(url, json=data, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get('ok'):
                    self.logger.info(f"Message sent successfully to chat {chat_id}")
                    return True, "Message sent successfully"
                else:
                    error_msg = f"Telegram API error: {result.get('description', 'Unknown error')}"
                    self.logger.error(error_msg)
                    
                    if attempt < self.max_retries - 1:
                        self.logger.info(f"Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                    else:
                        return False, error_msg
                        
            except requests.exceptions.RequestException as e:
                error_msg = f"Request error: {str(e)}"
                self.logger.error(error_msg)
                
                if attempt < self.max_retries - 1:
                    self.logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    return False, error_msg
                    
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.logger.error(error_msg)
                return False, error_msg
        
        return False, "Max retries exceeded"
    
    def send_daily_task_report(self, report_data: Dict, chat_id: str = None) -> Tuple[bool, str]:
        """
        Kirim daily task report ke Telegram
        
        Args:
            report_data: Data report dari Agent AI
            chat_id: ID chat target (default: default_chat_id)
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not chat_id:
                chat_id = self.default_chat_id
            
            if not chat_id:
                error_msg = "Chat ID tidak tersedia untuk daily report"
                self.logger.error(error_msg)
                return False, error_msg
            
            # Format message dari Agent AI response
            message = self._format_daily_report_message(report_data)
            
            if not message:
                error_msg = "Gagal format message report"
                self.logger.error(error_msg)
                return False, error_msg
            
            # Kirim message
            success, result_msg = self.send_message(chat_id, message)
            
            if success:
                self.logger.info(f"Daily task report sent successfully to {chat_id}")
            else:
                self.logger.error(f"Failed to send daily task report: {result_msg}")
            
            return success, result_msg
            
        except Exception as e:
            error_msg = f"Error sending daily task report: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def send_error_notification(self, error_message: str, chat_id: str = None) -> Tuple[bool, str]:
        """
        Kirim error notification ke admin
        
        Args:
            error_message: Pesan error
            chat_id: ID chat admin (default: admin_chat_id)
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not chat_id:
                chat_id = self.admin_chat_id
            
            if not chat_id:
                error_msg = "Admin chat ID tidak tersedia untuk error notification"
                self.logger.error(error_msg)
                return False, error_msg
            
            # Format error message
            message = self._format_error_message(error_message)
            
            # Kirim error notification
            success, result_msg = self.send_message(chat_id, message)
            
            if success:
                self.logger.info(f"Error notification sent successfully to admin {chat_id}")
            else:
                self.logger.error(f"Failed to send error notification: {result_msg}")
            
            return success, result_msg
            
        except Exception as e:
            error_msg = f"Error sending error notification: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _format_daily_report_message(self, report_data: Dict) -> str:
        """
        Format daily report message dari Agent AI response
        
        Args:
            report_data: Data report dari Agent AI
        
        Returns:
            str: Formatted message
        """
        try:
            # Extract data dari Agent AI response
            title = report_data.get('title', '📋 DAILY TASK REPORT')
            summary = report_data.get('summary', {})
            sections = report_data.get('sections', {})
            recommendations = report_data.get('recommendations', [])
            
            # Build message
            message = f"{title}\n"
            message += f"⏰ **Jam 17:00 - Task Status**\n\n"
            
            # Summary section
            message += "📊 **SUMMARY:**\n"
            message += f"• Total Task: {summary.get('total', 0)}\n"
            message += f"• Selesai: {summary.get('done', 0)} ({summary.get('progressPercent', 0)}%)\n"
            message += f"• Belum Selesai: {summary.get('pending', 0)} ({100 - summary.get('progressPercent', 0)}%)\n\n"
            
            # Pending tasks section
            pending_tasks = sections.get('pendingTasks', [])
            if pending_tasks:
                message += "📝 **TASK BELUM SELESAI:**\n\n"
                for i, task in enumerate(pending_tasks, 1):
                    message += f"**{i}. {task.get('title', 'Unknown Task')}**\n"
                    message += f"   👤 Assignee: {task.get('assignee', 'Unknown')}\n"
                    message += f"   ⏱️ Estimasi: {task.get('estimatedTime', 'N/A')}\n"
                    message += f"   📊 Status: {task.get('status', 'Unknown')}\n"
                    message += f"   📅 Dibuat: {task.get('createdAt', 'N/A')}\n"
                    if task.get('category'):
                        message += f"   🏷️ Category: {task.get('category')}\n"
                    if task.get('priority'):
                        message += f"   ⚡ Priority: {task.get('priority')}\n"
                    message += "\n"
            
            # Completed tasks section
            done_tasks = sections.get('doneToday', [])
            if done_tasks:
                message += "✅ **TASK SELESAI HARI INI:**\n\n"
                for i, task in enumerate(done_tasks, 1):
                    message += f"**{i}. {task.get('title', 'Unknown Task')}**\n"
                    message += f"   👤 Assignee: {task.get('assignee', 'Unknown')}\n"
                    message += f"   📅 Selesai: {task.get('completedAt', 'N/A')}\n"
                    if task.get('actualTime'):
                        message += f"   ⏱️ Actual: {task.get('actualTime')}\n"
                    if task.get('completionNote'):
                        message += f"   📝 Note: {task.get('completionNote')}\n"
                    message += "\n"
            
            # Recommendations section
            if recommendations:
                message += "⚠️ **REKOMENDASI:**\n"
                for rec in recommendations:
                    message += f"• {rec}\n"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formatting daily report message: {e}")
            return None
    
    def _format_error_message(self, error_message: str) -> str:
        """
        Format error message untuk admin
        
        Args:
            error_message: Pesan error
        
        Returns:
            str: Formatted error message
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"🚨 **ERROR NOTIFICATION**\n"
            message += f"⏰ **Time:** {timestamp}\n"
            message += f"🔧 **Service:** Daily Task Notification\n\n"
            message += f"❌ **Error:** {error_message}\n\n"
            message += f"🔍 **Action Required:** Please check the logs and fix the issue."
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formatting error message: {e}")
            return f"Error: {error_message}"
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test koneksi ke Telegram API
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.bot_token:
                return False, "Bot token tidak tersedia"
            
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ok'):
                bot_info = result.get('result', {})
                bot_name = bot_info.get('first_name', 'Unknown')
                bot_username = bot_info.get('username', 'Unknown')
                
                return True, f"Bot connected: {bot_name} (@{bot_username})"
            else:
                return False, f"Telegram API error: {result.get('description', 'Unknown error')}"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def get_bot_info(self) -> Dict:
        """
        Get bot information
        
        Returns:
            Dict: Bot information
        """
        try:
            if not self.bot_token:
                return {'error': 'Bot token tidak tersedia'}
            
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ok'):
                return result.get('result', {})
            else:
                return {'error': result.get('description', 'Unknown error')}
                
        except Exception as e:
            return {'error': str(e)}

# Singleton instance
telegram_sender_service = TelegramSenderService()
