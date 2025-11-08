#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Task Routes untuk KSM Main Backend
RESTful API routes untuk task management
"""

from flask import Blueprint
from controllers.daily_task_controller import DailyTaskController

# Create blueprint
daily_task_bp = Blueprint('daily_task', __name__, url_prefix='/api/attendance')

# Task Management Routes
@daily_task_bp.route('/tasks', methods=['POST'])
def create_task():
    """POST /api/attendance/tasks - Create new task"""
    controller = DailyTaskController()
    return controller.create_task()

@daily_task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """GET /api/attendance/tasks - List tasks dengan filter"""
    controller = DailyTaskController()
    return controller.get_tasks()

@daily_task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """GET /api/attendance/tasks/{task_id} - Get single task"""
    controller = DailyTaskController()
    return controller.get_task(task_id)

@daily_task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """PUT /api/attendance/tasks/{task_id} - Update task (full update)"""
    controller = DailyTaskController()
    return controller.update_task(task_id)

@daily_task_bp.route('/tasks/<int:task_id>', methods=['PATCH'])
def partial_update_task(task_id):
    """PATCH /api/attendance/tasks/{task_id} - Partial update task"""
    controller = DailyTaskController()
    return controller.partial_update_task(task_id)

@daily_task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """DELETE /api/attendance/tasks/{task_id} - Soft delete task"""
    controller = DailyTaskController()
    return controller.delete_task(task_id)

# Task Status Management Routes
@daily_task_bp.route('/tasks/<int:task_id>/status', methods=['PATCH'])
def update_task_status(task_id):
    """PATCH /api/attendance/tasks/{task_id}/status - Update task status"""
    controller = DailyTaskController()
    return controller.update_task_status(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """POST /api/attendance/tasks/{task_id}/start - Start task"""
    controller = DailyTaskController()
    return controller.start_task(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """POST /api/attendance/tasks/{task_id}/complete - Complete task"""
    controller = DailyTaskController()
    return controller.complete_task(task_id)

# Task Assignment Routes
@daily_task_bp.route('/tasks/<int:task_id>/assign', methods=['POST'])
def assign_task(task_id):
    """POST /api/attendance/tasks/{task_id}/assign - Assign task"""
    controller = DailyTaskController()
    return controller.assign_task(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/assign', methods=['DELETE'])
def unassign_task(task_id):
    """DELETE /api/attendance/tasks/{task_id}/assign - Unassign task"""
    controller = DailyTaskController()
    return controller.unassign_task(task_id)

# Task Attachments Routes
@daily_task_bp.route('/tasks/<int:task_id>/attachments', methods=['POST'])
def upload_attachment(task_id):
    """POST /api/attendance/tasks/{task_id}/attachments - Upload attachment"""
    controller = DailyTaskController()
    return controller.upload_attachment(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/attachments', methods=['GET'])
def get_attachments(task_id):
    """GET /api/attendance/tasks/{task_id}/attachments - List attachments"""
    controller = DailyTaskController()
    return controller.get_attachments(task_id)

# Task Comments Routes
@daily_task_bp.route('/tasks/<int:task_id>/comments', methods=['POST'])
def add_comment(task_id):
    """POST /api/attendance/tasks/{task_id}/comments - Add comment"""
    controller = DailyTaskController()
    return controller.add_comment(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/comments', methods=['GET'])
def get_comments(task_id):
    """GET /api/attendance/tasks/{task_id}/comments - List comments"""
    controller = DailyTaskController()
    return controller.get_comments(task_id)

# Analytics & Reports Routes
@daily_task_bp.route('/tasks/statistics', methods=['GET'])
def get_statistics():
    """GET /api/attendance/tasks/statistics - Get task statistics"""
    controller = DailyTaskController()
    return controller.get_statistics()

@daily_task_bp.route('/tasks/summary', methods=['GET'])
def get_summary():
    """GET /api/attendance/tasks/summary - Get daily summary"""
    controller = DailyTaskController()
    return controller.get_summary()

# Validation Routes
@daily_task_bp.route('/tasks/validate-clockout', methods=['GET'])
def validate_clockout():
    """GET /api/attendance/tasks/validate-clockout - Validate tasks before clock-out"""
    controller = DailyTaskController()
    return controller.validate_clockout()
