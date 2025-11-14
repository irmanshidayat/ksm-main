#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification CRUD Controller - Controller untuk CRUD operations notification
API routes untuk notification system dengan batching dan analytics
"""

from flask import Blueprint, request
from shared.middlewares.api_auth import jwt_required_custom, admin_required
from domains.notification.services.notification_service import NotificationService, NotificationBatchingService, NotificationAnalyticsService
from shared.utils.response_standardizer import APIResponse
import logging
from datetime import datetime, timedelta

# Create blueprint
notification_crud_bp = Blueprint('notification_crud', __name__, url_prefix='/api/notifications')

# Initialize services
notification_service = NotificationService()
batching_service = NotificationBatchingService()
analytics_service = NotificationAnalyticsService()

@notification_crud_bp.route('', methods=['GET'])
@jwt_required_custom
def get_notifications():
    """Get user notifications dengan pagination dan filtering"""
    try:
        from flask_jwt_extended import get_jwt_identity
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        
        # Parse query parameters
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        notification_type = request.args.get('type')
        priority = request.args.get('priority')
        
        # Get notifications
        notifications = notification_service.get_user_notifications(
            user_id=user_id,
            limit=limit,
            unread_only=unread_only
        )
        
        # Filter by type if specified
        if notification_type:
            notifications = [n for n in notifications if n.get('type') == notification_type]
        
        # Filter by priority if specified
        if priority:
            notifications = [n for n in notifications if n.get('priority') == priority]
        
        # Get unread count
        unread_count = notification_service.get_unread_count(user_id)
        
        return APIResponse.success({
            'notifications': notifications,
            'unread_count': unread_count,
            'total_count': len(notifications),
            'has_more': len(notifications) == limit
        })
        
    except Exception as e:
        logging.error(f"Error getting notifications: {e}")
        return APIResponse.server_error("Failed to retrieve notifications")

@notification_crud_bp.route('/<int:notification_id>/read', methods=['POST'])
@jwt_required_custom
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        from flask_jwt_extended import get_jwt_identity
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        
        success = notification_service.mark_notification_read(notification_id, user_id)
        
        if success:
            return APIResponse.success({"message": "Notification marked as read"})
        else:
            return APIResponse.not_found("Notification not found")
        
    except Exception as e:
        logging.error(f"Error marking notification as read: {e}")
        return APIResponse.server_error("Failed to mark notification as read")

@notification_crud_bp.route('/mark-all-read', methods=['POST'])
@jwt_required_custom
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        from flask_jwt_extended import get_jwt_identity
        from models import Notification, db
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        
        # Mark all notifications as read
        updated_count = Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({'is_read': True, 'read_at': datetime.utcnow()})
        
        db.session.commit()
        
        return APIResponse.success({
            "message": f"Marked {updated_count} notifications as read"
        })
        
    except Exception as e:
        logging.error(f"Error marking all notifications as read: {e}")
        return APIResponse.server_error("Failed to mark all notifications as read")

@notification_crud_bp.route('/read-all', methods=['POST'])
@jwt_required_custom
def mark_all_read_alias():
    """Alias untuk mark-all-read (untuk kompatibilitas frontend)"""
    return mark_all_notifications_read()

@notification_crud_bp.route('/stats', methods=['GET'])
@jwt_required_custom
def get_notification_stats():
    """Get notification statistics"""
    try:
        from flask_jwt_extended import get_jwt_identity
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        
        # Get stats
        unread_count = notification_service.get_unread_count(user_id)
        
        return APIResponse.success({
            'unread_count': unread_count
        })
        
    except Exception as e:
        logging.error(f"Error getting notification stats: {e}")
        return APIResponse.server_error("Failed to retrieve notification stats")

@notification_crud_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required_custom
def delete_notification(notification_id):
    """Delete notification"""
    try:
        from flask_jwt_extended import get_jwt_identity
        from models import Notification, db
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        
        # Find notification
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if not notification:
            return APIResponse.not_found("Notification not found")
        
        # Delete notification
        db.session.delete(notification)
        db.session.commit()
        
        return APIResponse.success({"message": "Notification deleted successfully"})
        
    except Exception as e:
        logging.error(f"Error deleting notification: {e}")
        return APIResponse.server_error("Failed to delete notification")

@notification_crud_bp.route('/send', methods=['POST'])
@admin_required
def send_notification():
    """Send notification (admin only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'type', 'title', 'message']
        for field in required_fields:
            if field not in data:
                return APIResponse.bad_request(f"Missing required field: {field}")
        
        # Send notification
        result = notification_service.send_notification(
            user_id=data['user_id'],
            notification_type=data['type'],
            title=data['title'],
            message=data['message'],
            data=data.get('data'),
            priority=data.get('priority', 'normal'),
            action_required=data.get('action_required', False)
        )
        
        return APIResponse.success(result)
        
    except Exception as e:
        logging.error(f"Error sending notification: {e}")
        return APIResponse.server_error("Failed to send notification")

@notification_crud_bp.route('/batch/process', methods=['POST'])
@admin_required
def process_notification_batches():
    """Process notification batches (admin only)"""
    try:
        batching_service.process_batches()
        
        return APIResponse.success({"message": "Notification batches processed"})
        
    except Exception as e:
        logging.error(f"Error processing notification batches: {e}")
        return APIResponse.server_error("Failed to process notification batches")

@notification_crud_bp.route('/analytics', methods=['GET'])
@admin_required
def get_notification_analytics():
    """Get notification analytics (admin only)"""
    try:
        # Parse query parameters
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')
        department_id = request.args.get('department_id', type=int)
        
        # Parse dates
        date_from = datetime.fromisoformat(date_from_str) if date_from_str else datetime.utcnow() - timedelta(days=30)
        date_to = datetime.fromisoformat(date_to_str) if date_to_str else datetime.utcnow()
        
        # Get analytics
        metrics = analytics_service.get_notification_metrics(
            date_from=date_from,
            date_to=date_to,
            department_id=department_id
        )
        
        return APIResponse.success(metrics)
        
    except Exception as e:
        logging.error(f"Error getting notification analytics: {e}")
        return APIResponse.server_error("Failed to retrieve notification analytics")

@notification_crud_bp.route('/preferences', methods=['GET'])
@jwt_required_custom
def get_notification_preferences():
    """Get user notification preferences"""
    try:
        from flask_jwt_extended import get_jwt_identity
        from models import NotificationPreference
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        
        # Get preferences
        preferences = NotificationPreference.query.filter_by(user_id=user_id).all()
        
        return APIResponse.success({
            'preferences': [p.to_dict() for p in preferences]
        })
        
    except Exception as e:
        logging.error(f"Error getting notification preferences: {e}")
        return APIResponse.server_error("Failed to retrieve notification preferences")

@notification_crud_bp.route('/preferences', methods=['POST'])
@jwt_required_custom
def update_notification_preferences():
    """Update user notification preferences"""
    try:
        from flask_jwt_extended import get_jwt_identity
        from models import NotificationPreference, db
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        
        data = request.get_json()
        
        # Update or create preference
        preference = NotificationPreference.query.filter_by(
            user_id=user_id,
            notification_type=data.get('notification_type', 'default')
        ).first()
        
        if preference:
            # Update existing preference
            for key, value in data.items():
                if hasattr(preference, key):
                    setattr(preference, key, value)
        else:
            # Create new preference
            preference = NotificationPreference(
                user_id=user_id,
                **data
            )
            db.session.add(preference)
        
        db.session.commit()
        
        return APIResponse.success({
            'message': 'Notification preferences updated',
            'preference': preference.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error updating notification preferences: {e}")
        return APIResponse.server_error("Failed to update notification preferences")

@notification_crud_bp.route('/test', methods=['POST'])
@admin_required
def test_notification():
    """Test notification system (admin only)"""
    try:
        from flask_jwt_extended import get_jwt_identity
        
        admin_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Send test notification
        result = notification_service.send_notification(
            user_id=admin_user_id,
            notification_type='test',
            title='Test Notification',
            message='This is a test notification to verify the system is working correctly.',
            data={'test': True, 'timestamp': datetime.utcnow().isoformat()},
            priority='normal',
            action_required=False
        )
        
        return APIResponse.success({
            'message': 'Test notification sent successfully',
            'result': result
        })
        
    except Exception as e:
        logging.error(f"Error sending test notification: {e}")
        return APIResponse.server_error("Failed to send test notification")

