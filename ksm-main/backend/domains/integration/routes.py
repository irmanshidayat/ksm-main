#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Domain Routes - Blueprint registration for integration domain
"""

from domains.integration.controllers.unified_notion_controller import unified_notion_bp, database_discovery_bp

def register_integration_routes(app):
    """Register all integration domain blueprints"""
    app.register_blueprint(unified_notion_bp)
    app.register_blueprint(database_discovery_bp)

