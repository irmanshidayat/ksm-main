#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Approval Domain Routes - Blueprint registration for approval domain
"""

from domains.approval.controllers.approval_controller import approval_bp

def register_approval_routes(app):
    """Register all approval domain blueprints"""
    app.register_blueprint(approval_bp)

