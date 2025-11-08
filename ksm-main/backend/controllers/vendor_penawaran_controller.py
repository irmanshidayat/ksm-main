#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Penawaran Controller - API Endpoints untuk penawaran management
Controller untuk mengelola penawaran vendor dan template
"""

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import List, Dict, Any
from datetime import datetime
import logging

from config.database import db
from services.vendor_management_service import VendorManagementService
from services.vendor_request_service import VendorRequestService
from services.vendor_template_service import VendorTemplateService
from utils.serialization import serialize_models

logger = logging.getLogger(__name__)

# Buat Blueprint untuk Flask
vendor_penawaran_bp = Blueprint('vendor_penawaran', __name__)

# ===== PENAWARAN MANAGEMENT =====

@vendor_penawaran_bp.route("/penawaran", methods=["POST"])
@jwt_required()
def create_penawaran():
    """Create penawaran untuk request dengan detail items"""
    try:
        # Get vendor from JWT token
        current_user_id = get_jwt_identity()
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        vendor_id = vendor.id
        
        penawaran_data = request.get_json()
        if not penawaran_data:
            return jsonify({
                'success': False,
                'message': 'Penawaran data tidak ditemukan'
            }), 400
        
        # Validate required fields
        required_fields = ['request_id', 'total_quoted_price', 'delivery_time_days']
        for field in required_fields:
            if field not in penawaran_data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        # Validate items data
        items_data = penawaran_data.get('items', [])
        if not items_data or len(items_data) == 0:
            return jsonify({
                'success': False,
                'message': 'Items data tidak boleh kosong'
            }), 400
        
        # Validate each item
        for i, item in enumerate(items_data):
            item_required_fields = ['request_item_id', 'quantity', 'harga_satuan']
            for field in item_required_fields:
                if field not in item or not item[field]:
                    return jsonify({
                        'success': False,
                        'message': f'Item {i+1}: Field {field} is required'
                    }), 400
            
            # Calculate total price for item
            quantity = int(item['quantity'])
            harga_satuan = float(item['harga_satuan'])
            item['harga_total'] = quantity * harga_satuan
        
        # Create penawaran with items
        request_service = VendorRequestService(db.session)
        result = request_service.create_penawaran_with_items(
            vendor_id=vendor_id,
            request_id=penawaran_data['request_id'],
            penawaran_data={
                'total_quoted_price': penawaran_data['total_quoted_price'],
                'delivery_time_days': penawaran_data['delivery_time_days'],
                'payment_terms': penawaran_data.get('payment_terms', ''),
                'quality_rating': penawaran_data.get('quality_rating', 3),
                'notes': penawaran_data.get('notes', '')
            },
            items_data=items_data
        )
        
        return jsonify({
            'success': True,
            'message': 'Penawaran berhasil dibuat',
            'data': result
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error creating penawaran for vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_penawaran_bp.route("/penawaran/<int:penawaran_id>", methods=["PUT"])
@jwt_required()
def update_penawaran(penawaran_id):
    """Update penawaran"""
    try:
        # Get vendor from JWT token
        current_user_id = get_jwt_identity()
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        vendor_id = vendor.id
        
        penawaran_data = request.get_json()
        if not penawaran_data:
            return jsonify({
                'success': False,
                'message': 'Penawaran data tidak ditemukan'
            }), 400
        
        # Update penawaran
        request_service = VendorRequestService(db.session)
        result = request_service.update_penawaran(
            vendor_id=vendor_id,
            penawaran_id=penawaran_id,
            update_data=penawaran_data
        )
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Penawaran tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Penawaran berhasil diupdate',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating penawaran {penawaran_id} for vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_penawaran_bp.route("/penawaran/request/<int:request_id>", methods=["GET"])
@jwt_required()
def get_penawaran_by_request(request_id):
    """Get penawaran by request ID"""
    try:
        # Get vendor from JWT token
        current_user_id = get_jwt_identity()
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        vendor_id = vendor.id
        
        # Get penawaran
        request_service = VendorRequestService(db.session)
        penawaran = request_service.get_penawaran_by_request(vendor_id, request_id)
        
        if not penawaran:
            return jsonify({
                'success': False,
                'message': 'Penawaran tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'data': penawaran
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting penawaran for request {request_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_penawaran_bp.route("/penawarans", methods=["GET"])
@jwt_required()
def get_vendor_penawarans():
    """Get all penawarans for vendor"""
    try:
        # Get vendor from JWT token
        current_user_id = get_jwt_identity()
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        vendor_id = vendor.id
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        # Get penawarans
        request_service = VendorRequestService(db.session)
        result = request_service.get_vendor_penawarans_paginated(
            vendor_id=vendor_id,
            page=page,
            per_page=per_page,
            status=status
        )
        
        return jsonify({
            'success': True,
            'data': result['penawarans'],
            'pagination': result['pagination']
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting penawarans for vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== TEMPLATE MANAGEMENT =====

@vendor_penawaran_bp.route("/templates", methods=["GET"])
@jwt_required()
def get_templates():
    """Get available templates"""
    try:
        template_service = VendorTemplateService(db.session)
        templates = template_service.get_all_templates()
        
        return jsonify({
            'success': True,
            'data': templates
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting templates: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_penawaran_bp.route("/templates/<int:template_id>/download", methods=["GET"])
@jwt_required()
def download_template(template_id):
    """Download template file"""
    try:
        template_service = VendorTemplateService(db.session)
        template = template_service.get_template_by_id(template_id)
        
        if not template:
            return jsonify({
                'success': False,
                'message': 'Template tidak ditemukan'
            }), 404
        
        # Get template file path
        file_path = template_service.get_template_file_path(template)
        
        if not file_path:
            return jsonify({
                'success': False,
                'message': 'File template tidak ditemukan'
            }), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=template.get('file_name', template.get('name', 'template'))
        )
        
    except Exception as e:
        logger.error(f"❌ Error downloading template {template_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
