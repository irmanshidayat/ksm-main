#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification Socket Events - WebSocket event handlers untuk notification system
"""

import logging
from flask import request

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

from domains.notification.services.notification_service import NotificationService, NotificationAnalyticsService

# Initialize services
notification_service = NotificationService()
analytics_service = NotificationAnalyticsService()

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

