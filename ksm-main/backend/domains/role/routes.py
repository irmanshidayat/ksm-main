#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Role Domain Routes - Blueprint registration for role domain
"""

# Import from domain routes
from domains.role.role_management_routes import role_management_bp
from domains.role.permission_routes import permission_bp

def register_role_routes(app):
    """Register all role domain blueprints"""
    app.register_blueprint(role_management_bp)
    app.register_blueprint(permission_bp, url_prefix='/api/permission-management')

