#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mobil Domain Routes - Blueprint registration for mobil domain
"""

from domains.mobil.controllers.mobil_controller import mobil_bp

def register_mobil_routes(app):
    """Register all mobil domain blueprints"""
    app.register_blueprint(mobil_bp)

