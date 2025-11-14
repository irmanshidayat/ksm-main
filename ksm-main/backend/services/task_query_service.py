#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Query Service - Service untuk query DailyTask dengan filter
Digunakan untuk Daily Task Notification System
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import and_, or_
from models import DailyTask
from models import User
from config.database import db
import logging

logger = logging.getLogger(__name__)

class TaskQueryService:
    """Service untuk query DailyTask dengan berbagai filter"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_unfinished_tasks(self, target_date: date = None, 
                           department_id: int = None, 
                           category: str = None, 
                           priority: str = None) -> List[Dict]:
        """
        Query task yang belum selesai (status: todo, in_progress)
        
        Args:
            target_date: Tanggal target (default: hari ini)
            department_id: Filter berdasarkan department
            category: Filter berdasarkan category (regular, urgent, project)
            priority: Filter berdasarkan priority (low, medium, high, critical)
        
        Returns:
            List[Dict]: List task yang belum selesai
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            # Base query untuk task yang belum selesai
            query = DailyTask.query.filter(
                and_(
                    DailyTask.task_date == target_date,
                    DailyTask.status.in_(['todo', 'in_progress']),
                    DailyTask.deleted_at.is_(None)  # Hanya task yang tidak soft deleted
                )
            )
            
            # Filter berdasarkan department
            if department_id:
                query = query.join(User).filter(User.department_id == department_id)
            
            # Filter berdasarkan category
            if category:
                query = query.filter(DailyTask.category == category)
            
            # Filter berdasarkan priority
            if priority:
                query = query.filter(DailyTask.priority == priority)
            
            # Hanya admin dan manager yang bisa terima report
            query = query.join(User, DailyTask.user_id == User.id).filter(
                or_(
                    User.role == 'admin',
                    User.role == 'manager'
                )
            )
            
            tasks = query.all()
            
            self.logger.info(f"Found {len(tasks)} unfinished tasks for {target_date}")
            
            return [task.to_dict() for task in tasks]
            
        except Exception as e:
            self.logger.error(f"Error getting unfinished tasks: {e}")
            return []
    
    def get_completed_tasks_today(self, target_date: date = None,
                                 department_id: int = None,
                                 category: str = None,
                                 priority: str = None) -> List[Dict]:
        """
        Query task yang selesai hari ini
        
        Args:
            target_date: Tanggal target (default: hari ini)
            department_id: Filter berdasarkan department
            category: Filter berdasarkan category
            priority: Filter berdasarkan priority
        
        Returns:
            List[Dict]: List task yang selesai hari ini
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            # Base query untuk task yang selesai hari ini
            query = DailyTask.query.filter(
                and_(
                    DailyTask.task_date == target_date,
                    DailyTask.status == 'done',
                    DailyTask.completed_at.isnot(None),
                    DailyTask.deleted_at.is_(None)
                )
            )
            
            # Filter berdasarkan department
            if department_id:
                query = query.join(User).filter(User.department_id == department_id)
            
            # Filter berdasarkan category
            if category:
                query = query.filter(DailyTask.category == category)
            
            # Filter berdasarkan priority
            if priority:
                query = query.filter(DailyTask.priority == priority)
            
            # Hanya admin dan manager yang bisa terima report
            query = query.join(User, DailyTask.user_id == User.id).filter(
                or_(
                    User.role == 'admin',
                    User.role == 'manager'
                )
            )
            
            tasks = query.all()
            
            self.logger.info(f"Found {len(tasks)} completed tasks for {target_date}")
            
            return [task.to_dict() for task in tasks]
            
        except Exception as e:
            self.logger.error(f"Error getting completed tasks: {e}")
            return []
    
    def get_task_summary(self, target_date: date = None,
                        department_id: int = None,
                        category: str = None,
                        priority: str = None) -> Dict:
        """
        Get ringkasan task untuk hari tertentu
        
        Args:
            target_date: Tanggal target (default: hari ini)
            department_id: Filter berdasarkan department
            category: Filter berdasarkan category
            priority: Filter berdasarkan priority
        
        Returns:
            Dict: Summary task dengan total, done, progress, dll
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            # Base query untuk semua task hari ini
            base_query = DailyTask.query.filter(
                and_(
                    DailyTask.task_date == target_date,
                    DailyTask.deleted_at.is_(None)
                )
            )
            
            # Filter berdasarkan department
            if department_id:
                base_query = base_query.join(User).filter(User.department_id == department_id)
            
            # Filter berdasarkan category
            if category:
                base_query = base_query.filter(DailyTask.category == category)
            
            # Filter berdasarkan priority
            if priority:
                base_query = base_query.filter(DailyTask.priority == priority)
            
            # Hanya admin dan manager yang bisa terima report
            base_query = base_query.join(User, DailyTask.user_id == User.id).filter(
                or_(
                    User.role == 'admin',
                    User.role == 'manager'
                )
            )
            
            # Get semua task
            all_tasks = base_query.all()
            
            # Hitung summary
            total = len(all_tasks)
            done = len([task for task in all_tasks if task.status == 'done'])
            todo = len([task for task in all_tasks if task.status == 'todo'])
            in_progress = len([task for task in all_tasks if task.status == 'in_progress'])
            cancelled = len([task for task in all_tasks if task.status == 'cancelled'])
            
            # Hitung progress percentage
            progress_percent = round((done / total * 100), 1) if total > 0 else 0
            
            # Hitung pending (todo + in_progress)
            pending = todo + in_progress
            
            summary = {
                'date': target_date.isoformat(),
                'total': total,
                'done': done,
                'todo': todo,
                'in_progress': in_progress,
                'cancelled': cancelled,
                'pending': pending,
                'progress_percent': progress_percent,
                'department_id': department_id,
                'category': category,
                'priority': priority
            }
            
            self.logger.info(f"Task summary for {target_date}: {summary}")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting task summary: {e}")
            return {
                'date': target_date.isoformat() if target_date else date.today().isoformat(),
                'total': 0,
                'done': 0,
                'todo': 0,
                'in_progress': 0,
                'cancelled': 0,
                'pending': 0,
                'progress_percent': 0,
                'error': str(e)
            }
    
    def get_tasks_by_priority(self, target_date: date = None) -> Dict[str, List[Dict]]:
        """
        Get task berdasarkan priority untuk rekomendasi
        
        Args:
            target_date: Tanggal target (default: hari ini)
        
        Returns:
            Dict: Task grouped by priority
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            # Get unfinished tasks
            unfinished_tasks = self.get_unfinished_tasks(target_date)
            
            # Group by priority
            priority_groups = {
                'critical': [],
                'high': [],
                'medium': [],
                'low': []
            }
            
            for task in unfinished_tasks:
                priority = task.get('priority', 'medium')
                if priority in priority_groups:
                    priority_groups[priority].append(task)
            
            return priority_groups
            
        except Exception as e:
            self.logger.error(f"Error getting tasks by priority: {e}")
            return {
                'critical': [],
                'high': [],
                'medium': [],
                'low': []
            }
    
    def get_tasks_by_category(self, target_date: date = None) -> Dict[str, List[Dict]]:
        """
        Get task berdasarkan category
        
        Args:
            target_date: Tanggal target (default: hari ini)
        
        Returns:
            Dict: Task grouped by category
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            # Get unfinished tasks
            unfinished_tasks = self.get_unfinished_tasks(target_date)
            
            # Group by category
            category_groups = {
                'regular': [],
                'urgent': [],
                'project': []
            }
            
            for task in unfinished_tasks:
                category = task.get('category', 'regular')
                if category in category_groups:
                    category_groups[category].append(task)
            
            return category_groups
            
        except Exception as e:
            self.logger.error(f"Error getting tasks by category: {e}")
            return {
                'regular': [],
                'urgent': [],
                'project': []
            }
    
    def get_recommendations(self, target_date: date = None) -> List[str]:
        """
        Generate rekomendasi berdasarkan task data
        
        Args:
            target_date: Tanggal target (default: hari ini)
        
        Returns:
            List[str]: List rekomendasi
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            recommendations = []
            
            # Get task data
            summary = self.get_task_summary(target_date)
            priority_groups = self.get_tasks_by_priority(target_date)
            
            # Rekomendasi berdasarkan progress
            if summary['progress_percent'] < 50:
                recommendations.append("Progress task masih rendah, pertimbangkan untuk memindahkan task ke hari berikutnya")
            
            # Rekomendasi berdasarkan priority
            if len(priority_groups['critical']) > 0:
                recommendations.append("Ada task dengan prioritas critical yang perlu segera diselesaikan")
            
            if len(priority_groups['high']) > 3:
                recommendations.append("Terlalu banyak task dengan prioritas high, pertimbangkan untuk mengurangi beban kerja")
            
            # Rekomendasi berdasarkan estimasi waktu
            unfinished_tasks = self.get_unfinished_tasks(target_date)
            short_tasks = [task for task in unfinished_tasks 
                          if task.get('estimated_minutes', 0) > 0 and task.get('estimated_minutes', 0) <= 30]
            
            if len(short_tasks) > 0:
                recommendations.append("Prioritaskan task dengan estimasi waktu terpendek untuk efisiensi")
            
            # Rekomendasi berdasarkan category
            category_groups = self.get_tasks_by_category(target_date)
            if len(category_groups['urgent']) > 2:
                recommendations.append("Ada banyak task urgent, pastikan prioritas sudah tepat")
            
            # Default recommendation jika tidak ada
            if not recommendations:
                recommendations.append("Lanjutkan progress task sesuai dengan prioritas yang sudah ditentukan")
            
            self.logger.info(f"Generated {len(recommendations)} recommendations for {target_date}")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Terjadi kesalahan dalam generate rekomendasi"]

# Singleton instance
task_query_service = TaskQueryService()
