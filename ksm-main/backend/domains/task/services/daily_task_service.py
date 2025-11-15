#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Task Service untuk KSM Main Backend
Service untuk mengelola task harian karyawan dengan integrasi absensi
"""

from datetime import datetime, date, timedelta
from config.database import db
from domains.task.models.task_models import DailyTask, TaskAttachment, TaskComment, TaskSettings
from domains.attendance.models.attendance_models import AttendanceRecord
from domains.auth.models.auth_models import User
from domains.role.models.role_models import Department, Role, UserRole
from domains.notification.models.notification_models import Notification
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import joinedload
from shared.utils.logger import get_logger
import json
import base64
import os

logger = get_logger(__name__)


class DailyTaskService:
    """Service untuk mengelola daily task"""
    
    def __init__(self):
        # Lazy loading: tidak memanggil query database di __init__
        # Settings akan di-load saat pertama kali diakses melalui property
        self._task_settings = None
    
    @property
    def task_settings(self):
        """Lazy-load task settings saat pertama kali diakses"""
        if self._task_settings is None:
            self._task_settings = self._get_task_settings()
        return self._task_settings
    
    def _get_task_settings(self):
        """Get task settings, create default if not exists"""
        settings = TaskSettings.query.first()
        if not settings:
            settings = TaskSettings()
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def create_task(self, user_id, task_data, assigned_by=None):
        """
        Create new task
        
        Args:
            user_id (int): ID user yang membuat task
            task_data (dict): Data task
            assigned_by (int): ID user yang assign task (optional)
        
        Returns:
            dict: Task yang dibuat
        """
        try:
            # Validasi data
            if not task_data.get('title'):
                raise ValueError("Title task harus diisi")
            
            # Tentukan assigned_to
            assigned_to = task_data.get('assigned_to', user_id)
            is_self_created = assigned_to == user_id and not assigned_by
            
            # Buat task baru
            task = DailyTask(
                user_id=user_id,
                task_date=datetime.strptime(task_data.get('task_date', date.today().isoformat()), '%Y-%m-%d').date(),
                title=task_data['title'],
                description=task_data.get('description'),
                category=task_data.get('category', self.task_settings.default_task_category),
                priority=task_data.get('priority', self.task_settings.default_task_priority),
                status='todo',
                assigned_by=assigned_by,
                assigned_to=assigned_to,
                is_self_created=is_self_created,
                estimated_minutes=task_data.get('estimated_minutes'),
                requires_approval=task_data.get('requires_approval', False),
                is_approved=self.task_settings.auto_approve_self_tasks if is_self_created else False,
                tags=json.dumps(task_data.get('tags', [])) if task_data.get('tags') else None
            )
            
            db.session.add(task)
            db.session.commit()
            
            # Send notification jika task di-assign
            if assigned_by and assigned_to != assigned_by:
                self._send_task_assigned_notification(task)
            
            return task.to_dict()
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_user_tasks(self, user_id, filters=None):
        """
        Get tasks untuk user dengan filter
        
        Args:
            user_id (int): ID user
            filters (dict): Filter options
        
        Returns:
            list: List tasks
        """
        try:
            # Convert user_id to int if it's a string (from JWT)
            if isinstance(user_id, str):
                user_id = int(user_id)
            
            query = DailyTask.query.filter(
                and_(
                    DailyTask.deleted_at.is_(None),
                    or_(
                        DailyTask.user_id == user_id,
                        DailyTask.assigned_to == user_id
                    )
                )
            ).options(
                joinedload(DailyTask.attachments),
                joinedload(DailyTask.comments)
            )
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    query = query.filter(DailyTask.status == filters['status'])
                
                if filters.get('category'):
                    query = query.filter(DailyTask.category == filters['category'])
                
                if filters.get('priority'):
                    query = query.filter(DailyTask.priority == filters['priority'])
                
                if filters.get('date'):
                    task_date = datetime.strptime(filters['date'], '%Y-%m-%d').date()
                    query = query.filter(DailyTask.task_date == task_date)
                
                if filters.get('date_from'):
                    date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d').date()
                    query = query.filter(DailyTask.task_date >= date_from)
                
                if filters.get('date_to'):
                    date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d').date()
                    query = query.filter(DailyTask.task_date <= date_to)
                
                if filters.get('view') == 'me':
                    query = query.filter(DailyTask.user_id == user_id)
                elif filters.get('view') == 'assigned':
                    query = query.filter(DailyTask.assigned_to == user_id)
                elif filters.get('view') == 'team':
                    # Get team tasks (manager view)
                    user_department = self._get_user_department(user_id)
                    if user_department:
                        team_users = self._get_department_users(user_department.id)
                        user_ids = [u.id for u in team_users]
                        query = query.filter(DailyTask.user_id.in_(user_ids))
            
            # Order by
            order_by = filters.get('order_by', 'created_at')
            order_dir = filters.get('order_dir', 'desc')
            
            if order_dir == 'desc':
                query = query.order_by(desc(getattr(DailyTask, order_by)))
            else:
                query = query.order_by(asc(getattr(DailyTask, order_by)))
            
            tasks = query.all()
            return [task.to_dict() for task in tasks]
            
        except Exception as e:
            raise e
    
    def get_task_by_id(self, task_id, user_id):
        """
        Get single task by ID dengan permission check
        
        Args:
            task_id (int): ID task
            user_id (int): ID user yang request
        
        Returns:
            dict: Task data
        """
        try:
            # Convert user_id to int if it's a string (from JWT)
            if isinstance(user_id, str):
                user_id = int(user_id)
            
            task = DailyTask.query.filter(
                and_(
                    DailyTask.id == task_id,
                    DailyTask.deleted_at.is_(None),
                    or_(
                        DailyTask.user_id == user_id,
                        DailyTask.assigned_to == user_id,
                        DailyTask.assigned_by == user_id
                    )
                )
            ).options(
                joinedload(DailyTask.attachments),
                joinedload(DailyTask.comments)
            ).first()
            
            if not task:
                raise ValueError("Task tidak ditemukan atau tidak memiliki akses")
            
            return task.to_dict()
            
        except Exception as e:
            raise e
    
    def update_task(self, task_id, user_id, update_data):
        """
        Update task
        
        Args:
            task_id (int): ID task
            user_id (int): ID user yang update
            update_data (dict): Data yang diupdate
        
        Returns:
            dict: Updated task
        """
        try:
            # Convert user_id to int if it's a string (from JWT)
            if isinstance(user_id, str):
                user_id = int(user_id)
            
            task = DailyTask.query.filter(
                and_(
                    DailyTask.id == task_id,
                    DailyTask.deleted_at.is_(None)
                )
            ).first()
            
            if not task:
                raise ValueError("Task tidak ditemukan")
            
            # Permission check
            if not self._can_edit_task(task, user_id):
                raise ValueError("Tidak memiliki permission untuk edit task ini")
            
            # Update fields
            if 'title' in update_data:
                task.title = update_data['title']
            if 'description' in update_data:
                task.description = update_data['description']
            if 'category' in update_data:
                task.category = update_data['category']
            if 'priority' in update_data:
                task.priority = update_data['priority']
            if 'estimated_minutes' in update_data:
                task.estimated_minutes = update_data['estimated_minutes']
            if 'tags' in update_data:
                task.tags = json.dumps(update_data['tags']) if update_data['tags'] else None
            if 'status' in update_data:
                # Update status dengan handling khusus
                new_status = update_data['status']
                task.status = new_status
                
                # Set timestamp sesuai status
                if new_status == 'in_progress' and not task.started_at:
                    task.started_at = datetime.utcnow()
                elif new_status in ['completed', 'done']:
                    task.completed_at = datetime.utcnow()
                elif new_status in ['pending', 'cancelled']:
                    # Reset timestamps jika kembali ke pending atau cancelled
                    if new_status == 'pending':
                        task.started_at = None
                        task.completed_at = None
            
            task.updated_at = datetime.utcnow()
            db.session.commit()
            
            return task.to_dict()
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update_task_status(self, task_id, user_id, status, additional_data=None):
        """
        Update task status
        
        Args:
            task_id (int): ID task
            user_id (int): ID user
            status (str): Status baru
            additional_data (dict): Data tambahan (actual_minutes, completion_note)
        
        Returns:
            dict: Updated task
        """
        try:
            # Convert user_id to int if it's a string (from JWT)
            if isinstance(user_id, str):
                user_id = int(user_id)
            
            task = DailyTask.query.filter(
                and_(
                    DailyTask.id == task_id,
                    DailyTask.deleted_at.is_(None)
                )
            ).first()
            
            if not task:
                raise ValueError("Task tidak ditemukan")
            
            # Permission check
            if not self._can_edit_task(task, user_id):
                raise ValueError("Tidak memiliki permission untuk update task ini")
            
            # Update status
            task.status = status
            
            if status == 'in_progress' and not task.started_at:
                task.started_at = datetime.utcnow()
            elif status == 'done':
                task.completed_at = datetime.utcnow()
                if additional_data and additional_data.get('actual_minutes'):
                    task.actual_minutes = additional_data['actual_minutes']
                if additional_data and additional_data.get('completion_note'):
                    task.completion_note = additional_data['completion_note']
            
            task.updated_at = datetime.utcnow()
            db.session.commit()
            
            return task.to_dict()
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def assign_task(self, task_id, assigned_by, assigned_to, requires_approval=False):
        """
        Assign task ke user lain
        
        Args:
            task_id (int): ID task
            assigned_by (int): ID user yang assign
            assigned_to (int): ID user yang di-assign
            requires_approval (bool): Apakah perlu approval
        
        Returns:
            dict: Updated task
        """
        try:
            task = DailyTask.query.filter(
                and_(
                    DailyTask.id == task_id,
                    DailyTask.deleted_at.is_(None)
                )
            ).first()
            
            if not task:
                raise ValueError("Task tidak ditemukan")
            
            # Permission check - hanya manager/admin yang bisa assign
            if not self._can_assign_task(assigned_by, assigned_to):
                raise ValueError("Tidak memiliki permission untuk assign task")
            
            # Update assignment
            task.assigned_by = assigned_by
            task.assigned_to = assigned_to
            task.is_self_created = False
            task.requires_approval = requires_approval
            task.is_approved = not requires_approval
            task.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Send notification
            self._send_task_assigned_notification(task)
            
            return task.to_dict()
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def upload_attachment(self, task_id, user_id, file_data):
        """
        Upload attachment ke task
        
        Args:
            task_id (int): ID task
            user_id (int): ID user yang upload
            file_data (dict): File data (filename, file_type, file_size, base64_content)
        
        Returns:
            dict: Attachment data
        """
        try:
            # Validasi file size
            max_size = self.task_settings.max_attachment_size_mb * 1024 * 1024
            if file_data['file_size'] > max_size:
                raise ValueError(f"File size terlalu besar. Maksimal {self.task_settings.max_attachment_size_mb}MB")
            
            # Validasi file type
            allowed_types = self.task_settings.get_allowed_file_types()
            file_extension = file_data['file_type'].lower()
            if file_extension not in allowed_types:
                raise ValueError(f"File type tidak diizinkan. Yang diizinkan: {', '.join(allowed_types)}")
            
            # Check task permission
            task = DailyTask.query.filter(
                and_(
                    DailyTask.id == task_id,
                    DailyTask.deleted_at.is_(None)
                )
            ).first()
            
            if not task:
                raise ValueError("Task tidak ditemukan")
            
            if not self._can_edit_task(task, user_id):
                raise ValueError("Tidak memiliki permission untuk upload attachment")
            
            # Create attachment
            attachment = TaskAttachment(
                task_id=task_id,
                filename=file_data['filename'],
                original_filename=file_data['original_filename'],
                file_type=file_data['file_type'],
                file_size=file_data['file_size'],
                base64_content=file_data['base64_content'],
                uploaded_by=user_id
            )
            
            db.session.add(attachment)
            db.session.commit()
            
            return attachment.to_dict()
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def add_comment(self, task_id, user_id, comment_text):
        """
        Add comment ke task
        
        Args:
            task_id (int): ID task
            user_id (int): ID user
            comment_text (str): Text komentar
        
        Returns:
            dict: Comment data
        """
        try:
            # Check task permission
            task = DailyTask.query.filter(
                and_(
                    DailyTask.id == task_id,
                    DailyTask.deleted_at.is_(None)
                )
            ).first()
            
            if not task:
                raise ValueError("Task tidak ditemukan")
            
            if not self._can_view_task(task, user_id):
                raise ValueError("Tidak memiliki permission untuk add comment")
            
            # Create comment
            comment = TaskComment(
                task_id=task_id,
                user_id=user_id,
                comment_text=comment_text
            )
            
            db.session.add(comment)
            db.session.commit()
            
            return comment.to_dict()
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def validate_clockout_tasks(self, user_id, task_date=None):
        """
        Validasi task sebelum clock-out
        
        Args:
            user_id (int): ID user
            task_date (date): Tanggal task (default: hari ini)
        
        Returns:
            dict: Validation result
        """
        try:
            logger.info(f"Task validation - User ID: {user_id}, Date: {task_date}")
            logger.info(f"Task settings - require_task_before_clockout: {self.task_settings.require_task_before_clockout}")
            logger.info(f"Task settings - minimum_tasks_required: {self.task_settings.minimum_tasks_required}")
            
            if not self.task_settings.require_task_before_clockout:
                logger.info("Task validation not required")
                return {'valid': True, 'message': 'Task validation tidak diperlukan'}
            
            if not task_date:
                task_date = date.today()
            
            # Get tasks untuk hari ini
            tasks = DailyTask.query.filter(
                and_(
                    DailyTask.user_id == user_id,
                    DailyTask.task_date == task_date,
                    DailyTask.deleted_at.is_(None)
                )
            ).all()
            
            logger.info(f"Found {len(tasks)} tasks for user {user_id} on {task_date}")
            
            # Check minimum tasks required
            if len(tasks) < self.task_settings.minimum_tasks_required:
                logger.warning(f"Not enough tasks: {len(tasks)} < {self.task_settings.minimum_tasks_required}")
                return {
                    'valid': False,
                    'message': f'Minimal harus ada {self.task_settings.minimum_tasks_required} task untuk hari ini',
                    'incomplete_tasks': []
                }
            
            # Check completed tasks
            completed_tasks = [t for t in tasks if t.status == 'done']
            incomplete_tasks = [t for t in tasks if t.status in ['todo', 'in_progress']]
            
            logger.info(f"Completed tasks: {len(completed_tasks)}, Incomplete tasks: {len(incomplete_tasks)}")
            
            if len(completed_tasks) < self.task_settings.minimum_tasks_required:
                logger.warning(f"Not enough completed tasks: {len(completed_tasks)} < {self.task_settings.minimum_tasks_required}")
                return {
                    'valid': False,
                    'message': f'Minimal {self.task_settings.minimum_tasks_required} task harus selesai sebelum clock-out',
                    'incomplete_tasks': [t.to_dict() for t in incomplete_tasks]
                }
            
            logger.info("Task validation successful")
            return {
                'valid': True,
                'message': 'Task validation berhasil',
                'completed_tasks': len(completed_tasks),
                'total_tasks': len(tasks)
            }
            
        except Exception as e:
            logger.error(f"Error validating clockout tasks: {e}")
            return {
                'valid': False,
                'message': f'Error validating tasks: {str(e)}'
            }
    
    def get_task_statistics(self, user_id=None, department_id=None, start_date=None, end_date=None):
        """
        Get task statistics untuk dashboard
        
        Args:
            user_id (int): ID user (optional)
            department_id (int): ID department (optional)
            start_date (date): Start date (optional)
            end_date (date): End date (optional)
        
        Returns:
            dict: Statistics data
        """
        try:
            query = DailyTask.query.filter(DailyTask.deleted_at.is_(None))
            
            # Apply filters
            if user_id:
                query = query.filter(DailyTask.user_id == user_id)
            
            if department_id:
                # Get users in department
                dept_users = self._get_department_users(department_id)
                user_ids = [u.id for u in dept_users]
                query = query.filter(DailyTask.user_id.in_(user_ids))
            
            if start_date:
                query = query.filter(DailyTask.task_date >= start_date)
            
            if end_date:
                query = query.filter(DailyTask.task_date <= end_date)
            
            # Get basic stats
            total_tasks = query.count()
            completed_tasks = query.filter(DailyTask.status == 'done').count()
            in_progress_tasks = query.filter(DailyTask.status == 'in_progress').count()
            todo_tasks = query.filter(DailyTask.status == 'todo').count()
            
            # Calculate completion rate
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Get average completion time
            completed_with_time = query.filter(
                and_(
                    DailyTask.status == 'done',
                    DailyTask.actual_minutes.isnot(None)
                )
            ).all()
            
            avg_completion_time = 0
            if completed_with_time:
                total_time = sum(t.actual_minutes for t in completed_with_time)
                avg_completion_time = total_time / len(completed_with_time)
            
            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'todo_tasks': todo_tasks,
                'completion_rate': round(completion_rate, 2),
                'avg_completion_time_minutes': round(avg_completion_time, 2),
                'avg_completion_time_hours': round(avg_completion_time / 60, 2)
            }
            
        except Exception as e:
            raise e
    
    def soft_delete_task(self, task_id, user_id):
        """
        Soft delete task
        
        Args:
            task_id (int): ID task
            user_id (int): ID user yang delete
        
        Returns:
            bool: Success status
        """
        try:
            task = DailyTask.query.filter(
                and_(
                    DailyTask.id == task_id,
                    DailyTask.deleted_at.is_(None)
                )
            ).first()
            
            if not task:
                raise ValueError("Task tidak ditemukan")
            
            # Permission check
            if not self._can_edit_task(task, user_id):
                raise ValueError("Tidak memiliki permission untuk delete task")
            
            task.soft_delete()
            return True
            
        except Exception as e:
            raise e
    
    def _can_edit_task(self, task, user_id):
        """Check if user can edit task"""
        # Owner atau assigned user bisa edit
        if task.user_id == user_id or task.assigned_to == user_id:
            return True
        
        # Manager bisa edit task tim
        if self._is_manager_of_user(user_id, task.user_id):
            return True
        
        return False
    
    def _can_view_task(self, task, user_id):
        """Check if user can view task"""
        # Owner, assigned user, atau assigner bisa view
        if task.user_id == user_id or task.assigned_to == user_id or task.assigned_by == user_id:
            return True
        
        # Manager bisa view task tim
        if self._is_manager_of_user(user_id, task.user_id):
            return True
        
        return False
    
    def _can_assign_task(self, assigned_by, assigned_to):
        """Check if user can assign task"""
        # Admin bisa assign ke semua user
        if self._is_admin(assigned_by):
            return True
        
        # Manager hanya bisa assign ke tim sendiri
        if self._is_manager_of_user(assigned_by, assigned_to):
            return True
        
        return False
    
    def _is_admin(self, user_id):
        """Check if user is admin"""
        user_roles = UserRole.query.filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.is_active == True
            )
        ).join(Role).filter(Role.code.in_(['admin', 'super_admin'])).first()
        
        return user_roles is not None
    
    def _is_manager_of_user(self, manager_id, user_id):
        """Check if manager_id is manager of user_id"""
        # Get manager department
        manager_dept = self._get_user_department(manager_id)
        if not manager_dept:
            return False
        
        # Get user department
        user_dept = self._get_user_department(user_id)
        if not user_dept:
            return False
        
        # Check if same department and manager has management role
        if manager_dept.id == user_dept.id:
            manager_roles = UserRole.query.filter(
                and_(
                    UserRole.user_id == manager_id,
                    UserRole.is_active == True
                )
            ).join(Role).filter(Role.is_management == True).first()
            
            return manager_roles is not None
        
        return False
    
    def _get_user_department(self, user_id):
        """Get user department"""
        user_role = UserRole.query.filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.is_active == True,
                UserRole.is_primary == True
            )
        ).join(Role).join(Department).first()
        
        return user_role.role.department if user_role else None
    
    def _get_department_users(self, department_id):
        """Get all users in department"""
        users = User.query.join(UserRole).join(Role).filter(
            and_(
                Role.department_id == department_id,
                UserRole.is_active == True
            )
        ).all()
        
        return users
    
    def _send_task_assigned_notification(self, task):
        """Send notification when task is assigned"""
        try:
            if not self.task_settings.notification_enabled:
                return
            
            # Create in-app notification
            notification = Notification(
                user_id=task.assigned_to,
                type='task_assigned',
                title='Task Baru Ditetapkan',
                message=f'Anda mendapat task baru: {task.title}',
                data={
                    'task_id': task.id,
                    'assigned_by': task.assigned_by,
                    'task_title': task.title
                },
                priority='normal',
                action_required=True
            )
            
            db.session.add(notification)
            db.session.commit()
            
            # TODO: Send email notification if enabled
            
        except Exception as e:
            # Don't raise error for notification failure
            pass
