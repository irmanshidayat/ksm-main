#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Domain Routes - Blueprint registration for vendor domain
"""

from flask import Blueprint
from domains.vendor.controllers.vendor_crud_controller import vendor_crud_bp
from domains.vendor.controllers.vendor_upload_controller import vendor_upload_bp
from domains.vendor.controllers.vendor_dashboard_controller import vendor_dashboard_bp
from domains.vendor.controllers.vendor_penawaran_controller import vendor_penawaran_bp
from domains.vendor.controllers.vendor_catalog_controller import vendor_catalog_bp
from domains.vendor.controllers.vendor_order_controller import vendor_order_bp
from domains.vendor.controllers.vendor_debug_controller import vendor_debug_bp
from domains.vendor.controllers.vendor_bulk_import_controller import vendor_bulk_import_bp
from domains.vendor.controllers.vendor_catalog_bulk_import_controller import vendor_catalog_bulk_import_bp
from domains.vendor.controllers.vendor_approval_controller import vendor_approval_bp
from domains.vendor.controllers.vendor_selection_controller import vendor_selection_bp
from domains.vendor.controllers.analysis_controller import analysis_bp

def register_vendor_routes(app):
    """Register all vendor domain blueprints"""
    app.register_blueprint(vendor_crud_bp, url_prefix='/api/vendor')
    app.register_blueprint(vendor_upload_bp, url_prefix='/api/vendor')
    app.register_blueprint(vendor_dashboard_bp, url_prefix='/api/vendor')
    app.register_blueprint(vendor_penawaran_bp, url_prefix='/api/vendor')
    app.register_blueprint(vendor_catalog_bp, url_prefix='/api/vendor-catalog')
    app.register_blueprint(vendor_order_bp)
    app.register_blueprint(vendor_debug_bp, url_prefix='/api/vendor')
    app.register_blueprint(vendor_bulk_import_bp)
    app.register_blueprint(vendor_catalog_bulk_import_bp)
    app.register_blueprint(vendor_approval_bp, url_prefix='/api/vendor-approval')
    app.register_blueprint(vendor_selection_bp, url_prefix='/api/vendor-selection')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')

