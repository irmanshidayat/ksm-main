#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notifications Routes - Routes untuk daily task notification
Digunakan untuk Daily Task Notification System
"""

from flask import Blueprint
from controllers.notification_controller import notification_bp

# Register notification blueprint
notifications_bp = Blueprint('notifications', __name__)

# Register notification controller routes
notifications_bp.register_blueprint(notification_bp)
