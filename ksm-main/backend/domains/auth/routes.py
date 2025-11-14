#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auth Domain Routes - Blueprint registration for authentication domain
"""

from flask import Blueprint
from domains.auth.controllers.auth_controller import auth_bp
from domains.auth.controllers.vendor_auth_controller import vendor_auth_bp
from domains.auth.controllers.gmail_auth_controller import gmail_auth_bp
from domains.auth.controllers.user_controller import user_bp

# Register all auth blueprints
def register_auth_routes(app):
    """Register all authentication domain blueprints"""
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(vendor_auth_bp)  # Already has url_prefix='/api/vendor'
    app.register_blueprint(gmail_auth_bp, url_prefix='/api/gmail')
    app.register_blueprint(user_bp)  # User management endpoints

