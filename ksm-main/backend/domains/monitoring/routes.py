#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitoring Domain Routes - Blueprint registration for monitoring domain
"""

from domains.monitoring.controllers.unified_monitoring_controller import unified_monitoring_bp
from domains.monitoring.controllers.unified_health_controller import unified_health_bp

def register_monitoring_routes(app):
    """Register all monitoring domain blueprints"""
    app.register_blueprint(unified_monitoring_bp, url_prefix='/api/monitoring')
    app.register_blueprint(unified_health_bp, url_prefix='/api')

