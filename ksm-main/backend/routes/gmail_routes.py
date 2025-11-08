#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Routes - Routes untuk Gmail API endpoints
"""

from flask import Blueprint
from controllers.gmail_auth_controller import gmail_auth_bp

# Create main Gmail blueprint
gmail_bp = Blueprint('gmail', __name__, url_prefix='/api/gmail')

# Register sub-blueprints
gmail_bp.register_blueprint(gmail_auth_bp, url_prefix='/auth')

# Export blueprint
__all__ = ['gmail_bp']
