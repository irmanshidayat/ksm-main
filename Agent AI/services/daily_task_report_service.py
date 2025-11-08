#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Task Report Service - Service untuk format data ke JSON report
Digunakan untuk Daily Task Notification System di Agent AI
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class DailyTaskReportService:
    """Service untuk format data ke JSON report"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_report_json(self, report_data: Dict) -> Dict:
        """
        Generate report JSON dari data yang diterima
        
        Args:
            report_data: Data report dari ksm-main backend
        
        Returns:
            Dict: Formatted JSON report
        """
        try:
            self.logger.info(f"Generating report JSON for {report_data.get('date', 'unknown date')}")
            
            # Extract data
            target_date = report_data.get('date', date.today().isoformat())
            summary = report_data.get('summary', {})
            sections = report_data.get('sections', {})
            recommendations = report_data.get('recommendations', [])
            filters = report_data.get('filters', {})
            
            # Format date untuk title
            try:
                date_obj = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime("%d/%m/%Y")
            except:
                formatted_date = target_date
            
            # Generate title
            title = f"📋 DAILY TASK REPORT - {formatted_date}"
            
            # Format summary
            formatted_summary = {
                'total': summary.get('total', 0),
                'done': summary.get('done', 0),
                'progressPercent': summary.get('progress_percent', 0),
                'pending': summary.get('pending', 0)
            }
            
            # Format sections
            formatted_sections = {
                'pendingTasks': self._format_pending_tasks(sections.get('pendingTasks', [])),
                'doneToday': self._format_completed_tasks(sections.get('doneToday', []))
            }
            
            # Format recommendations
            formatted_recommendations = self._format_recommendations(recommendations)
            
            # Build final report
            report_json = {
                'title': title,
                'summary': formatted_summary,
                'sections': formatted_sections,
                'recommendations': formatted_recommendations,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'target_date': target_date,
                    'filters': filters
                }
            }
            
            self.logger.info(f"Report JSON generated successfully for {target_date}")
            
            return report_json
            
        except Exception as e:
            self.logger.error(f"Error generating report JSON: {e}")
            return self._generate_error_report(str(e))
    
    def _format_pending_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """
        Format pending tasks untuk report
        
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
                    'assignee': task.get('assignee', 'Unknown'),
                    'estimatedTime': task.get('estimatedTime', 'N/A'),
                    'status': task.get('status', 'Unknown'),
                    'createdAt': task.get('createdAt', 'N/A'),
                    'category': task.get('category', 'Unknown'),
                    'priority': task.get('priority', 'Unknown')
                }
                formatted_tasks.append(formatted_task)
            
            return formatted_tasks
            
        except Exception as e:
            self.logger.error(f"Error formatting pending tasks: {e}")
            return []
    
    def _format_completed_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """
        Format completed tasks untuk report
        
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
                    'assignee': task.get('assignee', 'Unknown'),
                    'completedAt': task.get('completedAt', 'N/A'),
                    'actualTime': task.get('actualTime', 'N/A'),
                    'completionNote': task.get('completionNote', '')
                }
                formatted_tasks.append(formatted_task)
            
            return formatted_tasks
            
        except Exception as e:
            self.logger.error(f"Error formatting completed tasks: {e}")
            return []
    
    def _format_recommendations(self, recommendations: List[str]) -> List[str]:
        """
        Format recommendations untuk report
        
        Args:
            recommendations: List recommendations
        
        Returns:
            List[str]: Formatted recommendations
        """
        try:
            if not recommendations:
                return [
                    "Lanjutkan progress task sesuai dengan prioritas yang sudah ditentukan",
                    "Pastikan semua task penting sudah tercatat dan terassign dengan benar"
                ]
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error formatting recommendations: {e}")
            return ["Terjadi kesalahan dalam generate rekomendasi"]
    
    def _generate_error_report(self, error_message: str) -> Dict:
        """
        Generate error report jika terjadi kesalahan
        
        Args:
            error_message: Pesan error
        
        Returns:
            Dict: Error report
        """
        try:
            return {
                'title': '📋 DAILY TASK REPORT - ERROR',
                'summary': {
                    'total': 0,
                    'done': 0,
                    'progressPercent': 0,
                    'pending': 0
                },
                'sections': {
                    'pendingTasks': [],
                    'doneToday': []
                },
                'recommendations': [
                    f"Terjadi kesalahan dalam generate report: {error_message}",
                    "Silakan coba lagi atau hubungi administrator"
                ],
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'error': True,
                    'error_message': error_message
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating error report: {e}")
            return {
                'title': '📋 DAILY TASK REPORT - CRITICAL ERROR',
                'summary': {
                    'total': 0,
                    'done': 0,
                    'progressPercent': 0,
                    'pending': 0
                },
                'sections': {
                    'pendingTasks': [],
                    'doneToday': []
                },
                'recommendations': [
                    "Terjadi kesalahan kritis dalam generate report",
                    "Silakan hubungi administrator segera"
                ],
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'error': True,
                    'critical_error': True,
                    'error_message': str(e)
                }
            }
    
    def validate_report_data(self, report_data: Dict) -> tuple:
        """
        Validate report data yang diterima
        
        Args:
            report_data: Data report
        
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Check required fields
            required_fields = ['date', 'summary', 'sections']
            for field in required_fields:
                if field not in report_data:
                    return False, f"Missing required field: {field}"
            
            # Check summary fields
            summary = report_data.get('summary', {})
            required_summary_fields = ['total', 'done', 'progress_percent', 'pending']
            for field in required_summary_fields:
                if field not in summary:
                    return False, f"Missing required summary field: {field}"
            
            # Check sections
            sections = report_data.get('sections', {})
            if 'pendingTasks' not in sections or 'doneToday' not in sections:
                return False, "Missing required sections"
            
            return True, "Data is valid"
            
        except Exception as e:
            return False, f"Error validating data: {str(e)}"
    
    def get_report_statistics(self, report_data: Dict) -> Dict:
        """
        Get statistics dari report data
        
        Args:
            report_data: Data report
        
        Returns:
            Dict: Statistics
        """
        try:
            summary = report_data.get('summary', {})
            sections = report_data.get('sections', {})
            
            stats = {
                'total_tasks': summary.get('total', 0),
                'completed_tasks': summary.get('done', 0),
                'pending_tasks': summary.get('pending', 0),
                'progress_percentage': summary.get('progress_percent', 0),
                'pending_tasks_count': len(sections.get('pendingTasks', [])),
                'completed_tasks_count': len(sections.get('doneToday', [])),
                'recommendations_count': len(report_data.get('recommendations', [])),
                'filters_applied': bool(report_data.get('filters', {}))
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting report statistics: {e}")
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'pending_tasks': 0,
                'progress_percentage': 0,
                'error': str(e)
            }

# Singleton instance
daily_task_report_service = DailyTaskReportService()
