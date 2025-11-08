#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification Routes - Best Practices Implementation
API routes untuk notification system dengan batching dan analytics
"""

from flask import Blueprint, request, jsonify
from middlewares.api_auth import jwt_required_custom, admin_required

# Try to import flask_socketio, but don't fail if it's not available
try:
    from flask_socketio import emit, join_room, leave_room
    SOCKETIO_AVAILABLE = True
except ImportError:
    print("⚠️ Flask-SocketIO not available, WebSocket features will be disabled")
    SOCKETIO_AVAILABLE = False
    # Create dummy functions for compatibility
    def emit(*args, **kwargs):
        pass
    def join_room(*args, **kwargs):
        pass
    def leave_room(*args, **kwargs):
        pass
from services.notification_service import NotificationService, NotificationBatchingService, NotificationAnalyticsService
from utils.response_standardizer import APIResponse
import logging
from datetime import datetime, timedelta

# Create blueprint
notification_bp = Blueprint('notification', __name__, url_prefix='/api/notifications')

# Initialize services
notification_service = NotificationService()
batching_service = NotificationBatchingService()
analytics_service = NotificationAnalyticsService()

@notification_bp.route('', methods=['GET'])
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

@notification_bp.route('/<int:notification_id>/read', methods=['POST'])
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

@notification_bp.route('/mark-all-read', methods=['POST'])
@jwt_required_custom
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        from flask_jwt_extended import get_jwt_identity
        from models.notification_models import Notification, db
        
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

@notification_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required_custom
def delete_notification(notification_id):
    """Delete notification"""
    try:
        from flask_jwt_extended import get_jwt_identity
        from models.notification_models import Notification, db
        
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

@notification_bp.route('/send', methods=['POST'])
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

@notification_bp.route('/batch/process', methods=['POST'])
@admin_required
def process_notification_batches():
    """Process notification batches (admin only)"""
    try:
        batching_service.process_batches()
        
        return APIResponse.success({"message": "Notification batches processed"})
        
    except Exception as e:
        logging.error(f"Error processing notification batches: {e}")
        return APIResponse.server_error("Failed to process notification batches")

@notification_bp.route('/analytics', methods=['GET'])
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

@notification_bp.route('/preferences', methods=['GET'])
@jwt_required_custom
def get_notification_preferences():
    """Get user notification preferences"""
    try:
        from flask_jwt_extended import get_jwt_identity
        from models.notification_models import NotificationPreference
        
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

@notification_bp.route('/preferences', methods=['POST'])
@jwt_required_custom
def update_notification_preferences():
    """Update user notification preferences"""
    try:
        from flask_jwt_extended import get_jwt_identity
        from models.notification_models import NotificationPreference, db
        
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

@notification_bp.route('/test', methods=['POST'])
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

# WebSocket event handlers
def register_socket_events(socketio):
    """Register WebSocket events untuk notification system"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle user connection"""
        logging.info(f"User connected: {request.sid}")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle user disconnection"""
        logging.info(f"User disconnected: {request.sid}")
    
    @socketio.on('join_user_room')
    def handle_join_user_room(data):
        """Join user-specific room untuk notifications"""
        try:
            user_id = data.get('userId')
            if user_id:
                room = f'user_{user_id}'
                join_room(room)
                logging.info(f"User {user_id} joined room: {room}")
                emit('joined_room', {'room': room})
            else:
                emit('error', {'message': 'User ID required'})
        except Exception as e:
            logging.error(f"Error joining user room: {e}")
            emit('error', {'message': 'Failed to join room'})
    
    @socketio.on('leave_user_room')
    def handle_leave_user_room(data):
        """Leave user-specific room"""
        try:
            user_id = data.get('userId')
            if user_id:
                room = f'user_{user_id}'
                leave_room(room)
                logging.info(f"User {user_id} left room: {room}")
                emit('left_room', {'room': room})
        except Exception as e:
            logging.error(f"Error leaving user room: {e}")
    
    @socketio.on('notification_clicked')
    def handle_notification_clicked(data):
        """Handle notification click event"""
        try:
            notification_id = data.get('notification_id')
            user_id = data.get('user_id')
            
            if notification_id and user_id:
                # Track analytics
                analytics_service.track_notification_clicked(notification_id)
                
                logging.info(f"Notification {notification_id} clicked by user {user_id}")
                emit('notification_clicked_ack', {'notification_id': notification_id})
        except Exception as e:
            logging.error(f"Error handling notification click: {e}")
    
    @socketio.on('notification_read')
    def handle_notification_read(data):
        """Handle notification read event"""
        try:
            notification_id = data.get('notification_id')
            user_id = data.get('user_id')
            
            if notification_id and user_id:
                # Mark as read
                notification_service.mark_notification_read(notification_id, user_id)
                
                logging.info(f"Notification {notification_id} read by user {user_id}")
                emit('notification_read_ack', {'notification_id': notification_id})
        except Exception as e:
            logging.error(f"Error handling notification read: {e}")
    
    @socketio.on('request_notification_permission')
    def handle_request_notification_permission():
        """Handle request for notification permission"""
        try:
            # This would typically be handled on the client side
            # But we can log the request for analytics
            logging.info(f"User {request.sid} requested notification permission")
            emit('notification_permission_info', {
                'message': 'Notification permission should be requested on the client side'
            })
        except Exception as e:
            logging.error(f"Error handling notification permission request: {e}")

# Background task untuk processing batches
def process_notification_batches_task():
    """Background task untuk processing notification batches"""
    try:
        batching_service.process_batches()
        logging.info("✅ Processed notification batches")
    except Exception as e:
        logging.error(f"❌ Error processing notification batches: {e}")

# Export untuk digunakan di app.py
__all__ = ['notification_bp', 'register_socket_events', 'process_notification_batches_task']
