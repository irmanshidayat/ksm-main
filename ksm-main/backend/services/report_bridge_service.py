#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report Bridge Service - Service untuk bridge data ke Agent AI
Digunakan untuk Daily Task Notification System
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from config.config import Config
from services.task_query_service import task_query_service

logger = logging.getLogger(__name__)

class ReportBridgeService:
    """Service untuk bridge data ke Agent AI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agent_ai_base_url = Config.AGENT_AI_BASE_URL
        self.agent_ai_endpoint = Config.AGENT_AI_REPORT_ENDPOINT
        self.agent_ai_api_key = Config.AGENT_AI_API_KEY
        self.timeout = Config.AGENT_AI_TIMEOUT
        self.max_retries = Config.AGENT_AI_RETRY_COUNT
        self.retry_delays = [10, 20, 30]  # Exponential backoff
    
    def generate_report(self, target_date: date = None, 
                       department_id: int = None,
                       category: str = None,
                       priority: str = None) -> Tuple[bool, Dict, str]:
        """
        Generate report dengan mengirim data ke Agent AI
        
        Args:
            target_date: Tanggal target (default: hari ini)
            department_id: Filter berdasarkan department
            category: Filter berdasarkan category
            priority: Filter berdasarkan priority
        
        Returns:
            Tuple[bool, Dict, str]: (success, report_data, message)
        """
        try:
            if target_date is None:
                # Use timezone-aware date for consistency
                import pytz
                jakarta_tz = pytz.timezone('Asia/Jakarta')
                target_date = datetime.now(jakarta_tz).date()
            
            # Get data dari task query service
            self.logger.info(f"Generating report for {target_date}")
            
            # Get task data
            unfinished_tasks = task_query_service.get_unfinished_tasks(
                target_date, department_id, category, priority
            )
            
            completed_tasks = task_query_service.get_completed_tasks_today(
                target_date, department_id, category, priority
            )
            
            task_summary = task_query_service.get_task_summary(
                target_date, department_id, category, priority
            )
            
            recommendations = task_query_service.get_recommendations(target_date)
            
            # Prepare data untuk Agent AI
            report_data = {
                'date': target_date.isoformat(),
                'summary': {
                    'total': task_summary.get('total', 0),
                    'done': task_summary.get('done', 0),
                    'progress_percent': task_summary.get('progress_percent', 0),
                    'pending': task_summary.get('pending', 0)
                },
                'sections': {
                    'pendingTasks': self._format_pending_tasks(unfinished_tasks),
                    'doneToday': self._format_completed_tasks(completed_tasks)
                },
                'recommendations': recommendations,
                'filters': {
                    'department_id': department_id,
                    'category': category,
                    'priority': priority
                }
            }
            
            # Send ke Agent AI
            success, agent_response, message = self._send_to_agent_ai(report_data)
            
            if success:
                self.logger.info(f"Report generated successfully for {target_date}")
                return True, agent_response, "Report generated successfully"
            else:
                self.logger.error(f"Failed to generate report: {message}")
                return False, {}, message
                
        except Exception as e:
            error_msg = f"Error generating report: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
    
    def _send_to_agent_ai(self, report_data: Dict) -> Tuple[bool, Dict, str]:
        """
        Send data ke Agent AI untuk format report
        
        Args:
            report_data: Data report
        
        Returns:
            Tuple[bool, Dict, str]: (success, response, message)
        """
        try:
            url = f"{self.agent_ai_base_url}{self.agent_ai_endpoint}"
            
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.agent_ai_api_key
            }
            
            for attempt in range(self.max_retries):
                try:
                    self.logger.info(f"Sending data to Agent AI (attempt {attempt + 1})")
                    
                    response = requests.post(
                        url, 
                        json=report_data, 
                        headers=headers, 
                        timeout=self.timeout
                    )
                    
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    if result.get('success'):
                        self.logger.info("Agent AI response received successfully")
                        return True, result.get('data', {}), "Agent AI response received"
                    else:
                        error_msg = f"Agent AI error: {result.get('message', 'Unknown error')}"
                        self.logger.error(error_msg)
                        
                        if attempt < self.max_retries - 1:
                            delay = self.retry_delays[attempt]
                            self.logger.info(f"Retrying in {delay} seconds...")
                            time.sleep(delay)
                        else:
                            return False, {}, error_msg
                            
                except requests.exceptions.RequestException as e:
                    error_msg = f"Request error: {str(e)}"
                    self.logger.error(error_msg)
                    
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delays[attempt]
                        self.logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        return False, {}, error_msg
                        
                except Exception as e:
                    error_msg = f"Unexpected error: {str(e)}"
                    self.logger.error(error_msg)
                    return False, {}, error_msg
            
            return False, {}, "Max retries exceeded"
            
        except Exception as e:
            error_msg = f"Error sending to Agent AI: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
    
    def _format_pending_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """
        Format pending tasks untuk Agent AI
        
        Args:
            tasks: List pending tasks
        
        Returns:
            List[Dict]: Formatted pending tasks
        """
        try:
            formatted_tasks = []
            
            for task in tasks:
                formatted_task = {
                    'title': task.get('title', 'Unknown Task'),
                    'assignee': task.get('assigned_to_name', 'Unknown'),
                    'estimatedTime': self._format_estimated_time(task.get('estimated_minutes')),
                    'status': task.get('status_display', 'Unknown'),
                    'createdAt': self._format_date(task.get('created_at')),
                    'category': task.get('category_display', 'Unknown'),
                    'priority': task.get('priority_display', 'Unknown')
                }
                formatted_tasks.append(formatted_task)
            
            return formatted_tasks
            
        except Exception as e:
            self.logger.error(f"Error formatting pending tasks: {e}")
            return []
    
    def _format_completed_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """
        Format completed tasks untuk Agent AI
        
        Args:
            tasks: List completed tasks
        
        Returns:
            List[Dict]: Formatted completed tasks
        """
        try:
            formatted_tasks = []
            
            for task in tasks:
                formatted_task = {
                    'title': task.get('title', 'Unknown Task'),
                    'assignee': task.get('assigned_to_name', 'Unknown'),
                    'completedAt': self._format_date(task.get('completed_at')),
                    'actualTime': self._format_estimated_time(task.get('actual_minutes')),
                    'completionNote': task.get('completion_note', '')
                }
                formatted_tasks.append(formatted_task)
            
            return formatted_tasks
            
        except Exception as e:
            self.logger.error(f"Error formatting completed tasks: {e}")
            return []
    
    def _format_estimated_time(self, minutes: int) -> str:
        """
        Format estimated time dari menit ke string
        
        Args:
            minutes: Waktu dalam menit
        
        Returns:
            str: Formatted time string
        """
        try:
            if not minutes or minutes <= 0:
                return "N/A"
            
            if minutes < 60:
                return f"{minutes}m"
            else:
                hours = minutes // 60
                remaining_minutes = minutes % 60
                if remaining_minutes == 0:
                    return f"{hours}h"
                else:
                    return f"{hours}h {remaining_minutes}m"
                    
        except Exception as e:
            self.logger.error(f"Error formatting estimated time: {e}")
            return "N/A"
    
    def _format_date(self, date_str: str) -> str:
        """
        Format date string untuk display
        
        Args:
            date_str: Date string
        
        Returns:
            str: Formatted date string
        """
        try:
            if not date_str:
                return "N/A"
            
            # Parse ISO format date
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime("%d/%m/%Y %H:%M")
            else:
                # Simple date format
                return date_str
                
        except Exception as e:
            self.logger.error(f"Error formatting date: {e}")
            return "N/A"
    
    def test_agent_ai_connection(self) -> Tuple[bool, str]:
        """
        Test koneksi ke Agent AI
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            url = f"{self.agent_ai_base_url}/health"
            
            headers = {
                'X-API-Key': self.agent_ai_api_key
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('status') == 'healthy' or result.get('success'):
                return True, "Agent AI connection successful"
            else:
                return False, f"Agent AI health check failed: {result.get('message', 'Unknown error')}"
                
        except Exception as e:
            return False, f"Agent AI connection test failed: {str(e)}"
    
    def get_agent_ai_status(self) -> Dict:
        """
        Get Agent AI status
        
        Returns:
            Dict: Agent AI status
        """
        try:
            url = f"{self.agent_ai_base_url}/status"
            
            headers = {
                'X-API-Key': self.agent_ai_api_key
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            return {'error': str(e), 'success': False}

# Singleton instance
report_bridge_service = ReportBridgeService()
