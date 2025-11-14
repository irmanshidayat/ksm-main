#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification Controller - Controller untuk testing daily task notification
Digunakan untuk Daily Task Notification System
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date
from typing import Dict, Optional
import logging
from shared.middlewares.api_auth import jwt_required_custom
from shared.middlewares.role_auth import require_admin
from domains.task.schedulers.daily_task_scheduler import daily_task_scheduler
from services.task_query_service import task_query_service
from services.report_bridge_service import report_bridge_service
from domains.notification.services.telegram_sender_service import telegram_sender_service

logger = logging.getLogger(__name__)

notification_bp = Blueprint('notification', __name__, url_prefix='/api/notification')

@notification_bp.route('/test/daily-task-report', methods=['GET', 'POST'])
@jwt_required_custom
@require_admin()
def test_daily_task_report():
    """
    Test endpoint untuk daily task report
    GET: Test dengan parameter query
    POST: Test dengan data JSON
    """
    try:
        # Get parameters
        if request.method == 'GET':
            target_date_str = request.args.get('date')
            department_id = request.args.get('department_id', type=int)
            category = request.args.get('category')
            priority = request.args.get('priority')
            dry_run = request.args.get('dry_run', 'false').lower() == 'true'
        else:
            data = request.get_json() or {}
            target_date_str = data.get('date')
            department_id = data.get('department_id')
            category = data.get('category')
            priority = data.get('priority')
            dry_run = data.get('dry_run', False)
        
        # Parse target date
        target_date = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
        else:
            target_date = date.today()
        
        # Dry run - hanya test query tanpa kirim
        if dry_run:
            try:
                # Test query data
                summary = task_query_service.get_task_summary(target_date, department_id, category, priority)
                unfinished_tasks = task_query_service.get_unfinished_tasks(target_date, department_id, category, priority)
                completed_tasks = task_query_service.get_completed_tasks_today(target_date, department_id, category, priority)
                recommendations = task_query_service.get_recommendations(target_date)
                
                return jsonify({
                    'success': True,
                    'message': 'Dry run successful',
                    'data': {
                        'target_date': target_date.isoformat(),
                        'summary': summary,
                        'unfinished_tasks_count': len(unfinished_tasks),
                        'completed_tasks_count': len(completed_tasks),
                        'recommendations_count': len(recommendations),
                        'filters': {
                            'department_id': department_id,
                            'category': category,
                            'priority': priority
                        }
                    }
                }), 200
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Dry run failed: {str(e)}'
                }), 500
        
        # Real test - kirim report
        try:
            success, message = daily_task_scheduler.send_manual_report(
                target_date, department_id, category, priority
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': message,
                    'data': {
                        'target_date': target_date.isoformat(),
                        'sent_at': datetime.now().isoformat(),
                        'filters': {
                            'department_id': department_id,
                            'category': category,
                            'priority': priority
                        }
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': message
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Test failed: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in test_daily_task_report: {e}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@notification_bp.route('/status', methods=['GET'])
@jwt_required_custom
@require_admin()
def get_notification_status():
    """Get status notification system"""
    try:
        # Get scheduler status
        scheduler_status = daily_task_scheduler.get_scheduler_status()
        
        # Test connections
        connection_tests = daily_task_scheduler.test_connections()
        
        return jsonify({
            'success': True,
            'data': {
                'scheduler': scheduler_status,
                'connections': connection_tests,
                'timestamp': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting notification status: {e}")
        return jsonify({
            'success': False,
            'message': f'Error getting status: {str(e)}'
        }), 500

@notification_bp.route('/test/connections', methods=['GET'])
@jwt_required_custom
@require_admin()
def test_connections():
    """Test semua koneksi yang diperlukan"""
    try:
        connection_tests = daily_task_scheduler.test_connections()
        
        return jsonify({
            'success': True,
            'data': connection_tests
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing connections: {e}")
        return jsonify({
            'success': False,
            'message': f'Error testing connections: {str(e)}'
        }), 500

@notification_bp.route('/test/telegram', methods=['POST'])
@jwt_required_custom
@require_admin()
def test_telegram():
    """Test koneksi Telegram"""
    try:
        data = request.get_json() or {}
        test_message = data.get('message', 'Test message from KSM Main Backend')
        chat_id = data.get('chat_id')
        
        success, message = telegram_sender_service.send_message(chat_id, test_message)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Telegram test successful',
                'data': {
                    'sent_at': datetime.now().isoformat(),
                    'chat_id': chat_id
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Telegram test failed: {message}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error testing Telegram: {e}")
        return jsonify({
            'success': False,
            'message': f'Error testing Telegram: {str(e)}'
        }), 500

@notification_bp.route('/test/agent-ai', methods=['POST'])
@jwt_required_custom
@require_admin()
def test_agent_ai():
    """Test koneksi Agent AI"""
    try:
        data = request.get_json() or {}
        target_date_str = data.get('date')
        
        # Parse target date
        target_date = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
        else:
            target_date = date.today()
        
        # Test generate report
        success, report_data, message = report_bridge_service.generate_report(target_date)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Agent AI test successful',
                'data': {
                    'target_date': target_date.isoformat(),
                    'report_data': report_data,
                    'tested_at': datetime.now().isoformat()
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Agent AI test failed: {message}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error testing Agent AI: {e}")
        return jsonify({
            'success': False,
            'message': f'Error testing Agent AI: {str(e)}'
        }), 500

@notification_bp.route('/scheduler/start', methods=['POST'])
@jwt_required_custom
@require_admin()
def start_scheduler():
    """Start scheduler manual"""
    try:
        success = daily_task_scheduler.start_scheduler()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Scheduler started successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to start scheduler'
            }), 500
            
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        return jsonify({
            'success': False,
            'message': f'Error starting scheduler: {str(e)}'
        }), 500

@notification_bp.route('/scheduler/stop', methods=['POST'])
@jwt_required_custom
@require_admin()
def stop_scheduler():
    """Stop scheduler manual"""
    try:
        success = daily_task_scheduler.stop_scheduler()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Scheduler stopped successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to stop scheduler'
            }), 500
            
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        return jsonify({
            'success': False,
            'message': f'Error stopping scheduler: {str(e)}'
        }), 500

@notification_bp.route('/scheduler/status', methods=['GET'])
@jwt_required_custom
@require_admin()
def get_scheduler_status():
    """Get scheduler status"""
    try:
        status = daily_task_scheduler.get_scheduler_status()
        
        return jsonify({
            'success': True,
            'data': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return jsonify({
            'success': False,
            'message': f'Error getting scheduler status: {str(e)}'
        }), 500

@notification_bp.route('/test/public', methods=['GET'])
def test_public():
    """Public test endpoint untuk testing sistem tanpa authentication"""
    try:
        # Test scheduler status
        scheduler_status = daily_task_scheduler.get_scheduler_status()
        
        # Test connections
        connection_tests = daily_task_scheduler.test_connections()
        
        return jsonify({
            'success': True,
            'message': 'Daily Task Notification System is working',
            'data': {
                'scheduler': scheduler_status,
                'connections': connection_tests,
                'timestamp': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in public test: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@notification_bp.route('/test/manual-report', methods=['POST'])
def test_manual_report():
    """Test manual report generation tanpa authentication"""
    try:
        data = request.get_json() or {}
        target_date_str = data.get('date', date.today().isoformat())
        dry_run = data.get('dry_run', True)
        
        # Convert string to date object
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = date.today()
        
        logger.info(f"Testing manual report generation for {target_date} (dry_run: {dry_run})")
        
        # Generate report
        success, report_data, message = report_bridge_service.generate_report(
            target_date=target_date
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Manual report generated successfully for {target_date}',
                'data': {
                    'report': report_data,
                    'target_date': target_date,
                    'dry_run': dry_run,
                    'generated_at': datetime.now().isoformat()
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to generate report: {message}',
                'data': {
                    'target_date': target_date,
                    'dry_run': dry_run,
                    'error': message
                }
            }), 500
            
    except Exception as e:
        logger.error(f"Error in manual report test: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@notification_bp.route('/test/trigger-scheduler', methods=['POST'])
def test_trigger_scheduler():
    """Test trigger scheduler manual tanpa authentication"""
    try:
        logger.info("Testing manual scheduler trigger")
        
        # Trigger scheduler manual
        success, message = daily_task_scheduler.send_manual_report()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Scheduler triggered successfully',
                'data': {
                    'triggered_at': datetime.now().isoformat(),
                    'message': message
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to trigger scheduler: {message}',
                'data': {
                    'triggered_at': datetime.now().isoformat(),
                    'error': message
                }
            }), 500
            
    except Exception as e:
        logger.error(f"Error in scheduler trigger test: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@notification_bp.route('/test/update-scheduler-time', methods=['POST'])
def test_update_scheduler_time():
    """Update scheduler time untuk testing"""
    try:
        data = request.get_json() or {}
        new_time = data.get('time', '09:38')
        
        logger.info(f"Updating scheduler time to {new_time}")
        
        # Update scheduler time
        success, message = daily_task_scheduler.update_report_time(new_time)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Scheduler time updated to {new_time}',
                'data': {
                    'new_time': new_time,
                    'updated_at': datetime.now().isoformat(),
                    'message': message
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to update scheduler time: {message}',
                'data': {
                    'new_time': new_time,
                    'error': message
                }
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating scheduler time: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@notification_bp.route('/test/simulate-scheduler', methods=['POST'])
def test_simulate_scheduler():
    """Simulate scheduler trigger untuk testing tanpa menunggu waktu real"""
    try:
        data = request.get_json() or {}
        target_date = data.get('date', date.today().isoformat())
        
        logger.info(f"Simulating scheduler trigger for {target_date}")
        
        # Simulate scheduler trigger
        success, message = daily_task_scheduler.send_manual_report(
            target_date=datetime.strptime(target_date, '%Y-%m-%d').date()
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Scheduler simulation successful for {target_date}',
                'data': {
                    'target_date': target_date,
                    'simulated_at': datetime.now().isoformat(),
                    'message': message
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Scheduler simulation failed: {message}',
                'data': {
                    'target_date': target_date,
                    'error': message
                }
            }), 500
            
    except Exception as e:
        logger.error(f"Error in scheduler simulation: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@notification_bp.route('/test/force-trigger-now', methods=['POST'])
def test_force_trigger_now():
    """Force trigger scheduler sekarang juga untuk testing"""
    try:
        logger.info("Force triggering scheduler now for testing")
        
        # Force trigger scheduler
        success, message = daily_task_scheduler.send_manual_report()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Scheduler force triggered successfully',
                'data': {
                    'triggered_at': datetime.now().isoformat(),
                    'message': message
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to force trigger scheduler: {message}',
                'data': {
                    'triggered_at': datetime.now().isoformat(),
                    'error': message
                }
            }), 500
            
    except Exception as e:
        logger.error(f"Error in force trigger: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
