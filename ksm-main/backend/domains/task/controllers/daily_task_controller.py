#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Task Controller untuk KSM Main Backend
RESTful API endpoints untuk task management
"""

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from domains.task.services.daily_task_service import DailyTaskService
from shared.utils.validators import validate_request_data
import json


class DailyTaskController:
    """Controller untuk daily task management"""
    
    def __init__(self):
        self.task_service = DailyTaskService()
    
    @jwt_required()
    def create_task(self):
        """POST /api/attendance/tasks - Create new task"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            # Validasi required fields
            required_fields = ['title']
            if not validate_request_data(data, required_fields):
                return jsonify({
                    'success': False,
                    'message': 'Data tidak lengkap',
                    'errors': ['Title harus diisi']
                }), 400
            
            # Validasi task_date format
            if 'task_date' in data:
                try:
                    datetime.strptime(data['task_date'], '%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': 'Format tanggal tidak valid. Gunakan YYYY-MM-DD'
                    }), 400
            
            # Create task
            task = self.task_service.create_task(
                user_id=current_user_id,
                task_data=data,
                assigned_by=data.get('assigned_by')
            )
            
            return jsonify({
                'success': True,
                'message': 'Task berhasil dibuat',
                'data': task
            }), 201
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def get_tasks(self):
        """GET /api/attendance/tasks - List tasks dengan filter"""
        try:
            current_user_id = get_jwt_identity()
            
            # Get query parameters
            filters = {
                'status': request.args.get('status'),
                'category': request.args.get('category'),
                'priority': request.args.get('priority'),
                'date': request.args.get('date'),
                'date_from': request.args.get('date_from'),
                'date_to': request.args.get('date_to'),
                'view': request.args.get('view', 'all'),
                'order_by': request.args.get('order_by', 'created_at'),
                'order_dir': request.args.get('order_dir', 'desc')
            }
            
            # Pagination parameters
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 100))
            
            # Remove None values
            filters = {k: v for k, v in filters.items() if v is not None}
            
            tasks = self.task_service.get_user_tasks(current_user_id, filters)
            
            # Calculate pagination
            total = len(tasks)
            pages = (total + per_page - 1) // per_page if per_page > 0 else 1
            
            # Apply pagination
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_tasks = tasks[start_idx:end_idx]
            
            return jsonify({
                'success': True,
                'data': {
                    'items': paginated_tasks,
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': pages
                }
            }), 200
            
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return empty data instead of error for missing table
                return jsonify({
                    'success': True,
                    'data': {
                        'items': [],
                        'page': 1,
                        'per_page': 100,
                        'total': 0,
                        'pages': 0
                    },
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator.'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def get_task(self, task_id):
        """GET /api/attendance/tasks/{task_id} - Get single task"""
        try:
            current_user_id = get_jwt_identity()
            
            task = self.task_service.get_task_by_id(task_id, current_user_id)
            
            return jsonify({
                'success': True,
                'data': task
            }), 200
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 404
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def update_task(self, task_id):
        """PUT /api/attendance/tasks/{task_id} - Update task (full update)"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Data tidak boleh kosong'
                }), 400
            
            task = self.task_service.update_task(task_id, current_user_id, data)
            
            return jsonify({
                'success': True,
                'message': 'Task berhasil diupdate',
                'data': task
            }), 200
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def partial_update_task(self, task_id):
        """PATCH /api/attendance/tasks/{task_id} - Partial update task"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Data tidak boleh kosong'
                }), 400
            
            task = self.task_service.update_task(task_id, current_user_id, data)
            
            return jsonify({
                'success': True,
                'message': 'Task berhasil diupdate',
                'data': task
            }), 200
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def delete_task(self, task_id):
        """DELETE /api/attendance/tasks/{task_id} - Soft delete task"""
        try:
            current_user_id = get_jwt_identity()
            
            success = self.task_service.soft_delete_task(task_id, current_user_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Task berhasil dihapus'
                }), 204
            else:
                return jsonify({
                    'success': False,
                    'message': 'Gagal menghapus task'
                }), 400
                
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def update_task_status(self, task_id):
        """PATCH /api/attendance/tasks/{task_id}/status - Update task status"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            if not data or 'status' not in data:
                return jsonify({
                    'success': False,
                    'message': 'Status harus diisi'
                }), 400
            
            status = data['status']
            valid_statuses = ['todo', 'in_progress', 'done', 'cancelled']
            
            if status not in valid_statuses:
                return jsonify({
                    'success': False,
                    'message': f'Status tidak valid. Gunakan: {", ".join(valid_statuses)}'
                }), 400
            
            additional_data = data.get('additional_data', {})
            task = self.task_service.update_task_status(task_id, current_user_id, status, additional_data)
            
            return jsonify({
                'success': True,
                'message': f'Status task berhasil diupdate ke {status}',
                'data': task
            }), 200
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def start_task(self, task_id):
        """POST /api/attendance/tasks/{task_id}/start - Start task"""
        try:
            current_user_id = get_jwt_identity()
            
            task = self.task_service.update_task_status(task_id, current_user_id, 'in_progress')
            
            return jsonify({
                'success': True,
                'message': 'Task berhasil dimulai',
                'data': task
            }), 200
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def complete_task(self, task_id):
        """POST /api/attendance/tasks/{task_id}/complete - Complete task"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json() or {}
            
            additional_data = {
                'actual_minutes': data.get('actual_minutes'),
                'completion_note': data.get('completion_note')
            }
            
            task = self.task_service.update_task_status(task_id, current_user_id, 'done', additional_data)
            
            return jsonify({
                'success': True,
                'message': 'Task berhasil diselesaikan',
                'data': task
            }), 200
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def assign_task(self, task_id):
        """POST /api/attendance/tasks/{task_id}/assign - Assign task"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            if not data or 'assigned_to' not in data:
                return jsonify({
                    'success': False,
                    'message': 'assigned_to harus diisi'
                }), 400
            
            assigned_to = data['assigned_to']
            requires_approval = data.get('requires_approval', False)
            
            task = self.task_service.assign_task(task_id, current_user_id, assigned_to, requires_approval)
            
            return jsonify({
                'success': True,
                'message': 'Task berhasil di-assign',
                'data': task
            }), 200
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def unassign_task(self, task_id):
        """DELETE /api/attendance/tasks/{task_id}/assign - Unassign task"""
        try:
            current_user_id = get_jwt_identity()
            
            # Set task back to self-created
            task_data = {
                'assigned_by': None,
                'assigned_to': current_user_id,
                'is_self_created': True,
                'requires_approval': False,
                'is_approved': True
            }
            
            task = self.task_service.update_task(task_id, current_user_id, task_data)
            
            return jsonify({
                'success': True,
                'message': 'Task berhasil di-unassign',
                'data': task
            }), 200
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def upload_attachment(self, task_id):
        """POST /api/attendance/tasks/{task_id}/attachments - Upload attachment"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            required_fields = ['filename', 'file_type', 'file_size', 'base64_content']
            if not validate_request_data(data, required_fields):
                return jsonify({
                    'success': False,
                    'message': 'Data attachment tidak lengkap'
                }), 400
            
            attachment = self.task_service.upload_attachment(task_id, current_user_id, data)
            
            return jsonify({
                'success': True,
                'message': 'Attachment berhasil diupload',
                'data': attachment
            }), 201
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def get_attachments(self, task_id):
        """GET /api/attendance/tasks/{task_id}/attachments - List attachments"""
        try:
            current_user_id = get_jwt_identity()
            
            # Get task first to check permission
            task = self.task_service.get_task_by_id(task_id, current_user_id)
            
            # Get attachments from task data
            attachments = task.get('attachments', [])
            
            return jsonify({
                'success': True,
                'data': attachments,
                'count': len(attachments)
            }), 200
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 404
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def add_comment(self, task_id):
        """POST /api/attendance/tasks/{task_id}/comments - Add comment"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            if not data or 'comment_text' not in data:
                return jsonify({
                    'success': False,
                    'message': 'comment_text harus diisi'
                }), 400
            
            comment = self.task_service.add_comment(task_id, current_user_id, data['comment_text'])
            
            return jsonify({
                'success': True,
                'message': 'Komentar berhasil ditambahkan',
                'data': comment
            }), 201
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def get_comments(self, task_id):
        """GET /api/attendance/tasks/{task_id}/comments - List comments"""
        try:
            current_user_id = get_jwt_identity()
            
            # Get task first to check permission
            task = self.task_service.get_task_by_id(task_id, current_user_id)
            
            # Get comments from task data
            comments = task.get('comments', [])
            
            return jsonify({
                'success': True,
                'data': comments,
                'count': len(comments)
            }), 200
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 404
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def get_statistics(self):
        """GET /api/attendance/tasks/statistics - Get task statistics"""
        try:
            current_user_id = get_jwt_identity()
            
            # Get query parameters
            user_id = request.args.get('user_id')
            department_id = request.args.get('department_id')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Parse dates
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            stats = self.task_service.get_task_statistics(
                user_id=user_id or current_user_id,
                department_id=department_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return jsonify({
                'success': True,
                'data': stats
            }), 200
            
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def get_summary(self):
        """GET /api/attendance/tasks/summary - Get daily summary"""
        try:
            current_user_id = get_jwt_identity()
            
            # Get query parameters
            user_id = request.args.get('user_id', current_user_id)
            task_date = request.args.get('date', date.today().isoformat())
            
            # Get tasks for the date
            filters = {
                'date': task_date,
                'user_id': user_id
            }
            
            tasks = self.task_service.get_user_tasks(user_id, filters)
            
            # Count by status
            summary = {
                'todo': len([t for t in tasks if t['status'] == 'todo']),
                'in_progress': len([t for t in tasks if t['status'] == 'in_progress']),
                'done': len([t for t in tasks if t['status'] == 'done']),
                'cancelled': len([t for t in tasks if t['status'] == 'cancelled']),
                'total': len(tasks)
            }
            
            return jsonify({
                'success': True,
                'data': summary
            }), 200
            
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500
    
    @jwt_required()
    def validate_clockout(self):
        """GET /api/attendance/tasks/validate-clockout - Validate tasks before clock-out"""
        try:
            current_user_id = get_jwt_identity()
            task_date = request.args.get('date', date.today().isoformat())
            
            validation_result = self.task_service.validate_clockout_tasks(current_user_id, task_date)
            
            return jsonify({
                'success': True,
                'data': validation_result
            }), 200
            
        except Exception as e:
            # Check if it's a table not found error
            error_msg = str(e)
            if "doesn't exist in engine" in error_msg or "Table" in error_msg:
                # Return error message for missing table
                return jsonify({
                    'success': False,
                    'message': 'Tabel daily_tasks belum tersedia. Silakan hubungi administrator untuk membuat tabel database.',
                    'error': 'Database table not found'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan server',
                    'error': str(e)
                }), 500


# Instansiasi dipindahkan ke routes untuk menghindari penggunaan context saat import
