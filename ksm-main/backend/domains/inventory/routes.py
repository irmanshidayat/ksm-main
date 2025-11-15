#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inventory Domain Routes - Blueprint registration for inventory domain
"""

from domains.inventory.controllers.stok_barang_controller import stok_barang_bp
from domains.inventory.controllers.request_pembelian_controller import request_pembelian_bp

def register_inventory_routes(app):
    """Register all inventory domain blueprints"""
    app.register_blueprint(stok_barang_bp, url_prefix='/api/stok-barang')
    app.register_blueprint(request_pembelian_bp, url_prefix='/api/request-pembelian')

