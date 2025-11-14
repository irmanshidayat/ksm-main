#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitoring Domain Routes - Blueprint registration for monitoring domain
"""

from domains.monitoring.controllers.unified_monitoring_controller import unified_monitoring_bp
from domains.monitoring.controllers.unified_health_controller import unified_health_bp
from domains.monitoring.controllers.circuit_breaker_controller import circuit_breaker_bp
from domains.monitoring.controllers.service_controller import service_bp

def register_monitoring_routes(app):
    """Register all monitoring domain blueprints"""
    app.register_blueprint(unified_monitoring_bp, url_prefix='/api/monitoring')
    app.register_blueprint(unified_health_bp, url_prefix='/api')
    app.register_blueprint(circuit_breaker_bp)
    app.register_blueprint(service_bp)

