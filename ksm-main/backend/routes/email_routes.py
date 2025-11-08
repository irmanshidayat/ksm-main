#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Routes - Register email-related blueprints
"""

from flask import Flask
from controllers.email_controller import email_bp
from controllers.email_domain_controller import email_domain_bp

def register_email_routes(app: Flask):
    """Register all email-related routes"""
    
    # Register email blueprint
    app.register_blueprint(email_bp, url_prefix='')
    
    # Register email domain blueprint
    app.register_blueprint(email_domain_bp, url_prefix='')
    
    print("✅ Email routes registered successfully")
