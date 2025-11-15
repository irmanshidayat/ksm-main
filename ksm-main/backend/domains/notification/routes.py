#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification Domain Routes - Blueprint registration for notification domain
"""

from domains.notification.controllers.notification_controller import notification_bp
from domains.notification.controllers.notification_crud_controller import notification_crud_bp
from domains.notification.controllers.telegram_controller import telegram_bp
from domains.notification.socket_events import register_socket_events

def register_notification_routes(app):
    """Register all notification domain blueprints"""
    app.register_blueprint(notification_bp)
    app.register_blueprint(notification_crud_bp)
    app.register_blueprint(telegram_bp)

# Export socket events untuk digunakan di app_factory
__all__ = ['register_notification_routes', 'register_socket_events']

