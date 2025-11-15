#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Domain Routes - Blueprint registration for email domain
"""

from domains.email.controllers.email_controller import email_bp
from domains.email.controllers.email_domain_controller import email_domain_bp

def register_email_routes(app):
    """Register all email domain blueprints"""
    app.register_blueprint(email_bp, url_prefix='/api/email')
    app.register_blueprint(email_domain_bp)

