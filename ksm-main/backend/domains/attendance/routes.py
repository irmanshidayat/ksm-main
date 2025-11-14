#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Attendance Domain Routes - Blueprint registration for attendance domain
"""

from domains.attendance.controllers.attendance_controller import attendance_bp

def register_attendance_routes(app):
    """Register all attendance domain blueprints"""
    app.register_blueprint(attendance_bp)

