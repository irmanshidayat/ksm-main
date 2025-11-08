#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification Controller - Controller untuk daily task report di Agent AI
Digunakan untuk Daily Task Notification System
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from services.daily_task_report_service import daily_task_report_service

logger = logging.getLogger(__name__)

notification_bp = Blueprint('notification', __name__, url_prefix='/api')

@notification_bp.route('/report/daily-task', methods=['POST'])
def generate_daily_task_report():
    """
    Endpoint untuk generate daily task report
    Menerima data dari ksm-main backend dan mengembalikan formatted JSON
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Validate data
        is_valid, error_message = daily_task_report_service.validate_report_data(data)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'message': f'Invalid data: {error_message}'
            }), 400
        
        # Generate report JSON
        report_json = daily_task_report_service.generate_report_json(data)
        
        # Get statistics
        stats = daily_task_report_service.get_report_statistics(data)
        
        logger.info(f"Daily task report generated successfully for {data.get('date', 'unknown date')}")
        
        return jsonify({
            'success': True,
            'message': 'Daily task report generated successfully',
            'data': report_json,
            'statistics': stats,
            'generated_at': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating daily task report: {e}")
        return jsonify({
            'success': False,
            'message': f'Error generating report: {str(e)}'
        }), 500

@notification_bp.route('/report/test', methods=['POST'])
def test_report_generation():
    """
    Test endpoint untuk report generation
    """
    try:
        # Test data
        test_data = {
            'date': '2025-01-21',
            'summary': {
                'total': 5,
                'done': 2,
                'progress_percent': 40,
                'pending': 3
            },
            'sections': {
                'pendingTasks': [
                    {
                        'title': 'Test Task 1',
                        'assignee': 'admin',
                        'estimatedTime': '30m',
                        'status': 'To Do',
                        'createdAt': '21/01/2025',
                        'category': 'Regular',
                        'priority': 'Medium'
                    }
                ],
                'doneToday': [
                    {
                        'title': 'Completed Task 1',
                        'assignee': 'admin',
                        'completedAt': '21/01/2025',
                        'actualTime': '25m',
                        'completionNote': 'Task completed successfully'
                    }
                ]
            },
            'recommendations': [
                'Prioritaskan task dengan estimasi terpendek',
                'Pertimbangkan memindahkan task ke hari berikutnya'
            ],
            'filters': {
                'department_id': None,
                'category': None,
                'priority': None
            }
        }
        
        # Generate test report
        report_json = daily_task_report_service.generate_report_json(test_data)
        
        return jsonify({
            'success': True,
            'message': 'Test report generated successfully',
            'data': report_json,
            'test_data': test_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error in test report generation: {e}")
        return jsonify({
            'success': False,
            'message': f'Error in test: {str(e)}'
        }), 500

@notification_bp.route('/report/validate', methods=['POST'])
def validate_report_data():
    """
    Validate report data format
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Validate data
        is_valid, error_message = daily_task_report_service.validate_report_data(data)
        
        if is_valid:
            return jsonify({
                'success': True,
                'message': 'Data is valid',
                'data': data
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': error_message,
                'data': data
            }), 400
            
    except Exception as e:
        logger.error(f"Error validating report data: {e}")
        return jsonify({
            'success': False,
            'message': f'Error validating data: {str(e)}'
        }), 500

@notification_bp.route('/report/statistics', methods=['POST'])
def get_report_statistics():
    """
    Get statistics dari report data
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Get statistics
        stats = daily_task_report_service.get_report_statistics(data)
        
        return jsonify({
            'success': True,
            'message': 'Statistics generated successfully',
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting report statistics: {e}")
        return jsonify({
            'success': False,
            'message': f'Error getting statistics: {str(e)}'
        }), 500

@notification_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check untuk notification service
    """
    try:
        return jsonify({
            'success': True,
            'message': 'Notification service is healthy',
            'service': 'daily_task_report',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            'success': False,
            'message': f'Health check failed: {str(e)}'
        }), 500
