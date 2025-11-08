#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Approval Controller - API Endpoints untuk vendor approval management
Controller untuk mengelola approval workflow vendor internal dan mitra
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import List, Dict, Any
import logging

from config.database import db
from services.vendor_approval_service import VendorApprovalService

logger = logging.getLogger(__name__)

# Buat Blueprint untuk Flask
vendor_approval_bp = Blueprint('vendor_approval', __name__)

# ===== VENDOR APPROVAL MANAGEMENT =====

@vendor_approval_bp.route("/requirements/<int:vendor_id>", methods=["GET"])
@jwt_required()
def get_vendor_approval_requirements(vendor_id):
    """Get approval requirements untuk vendor tertentu"""
    try:
        service = VendorApprovalService(db.session)
        result = service.validate_vendor_approval_requirements(vendor_id)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor approval requirements: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_approval_bp.route("/workflow/<int:vendor_id>", methods=["POST"])
@jwt_required()
def create_approval_workflow(vendor_id):
    """Membuat approval workflow untuk vendor"""
    try:
        current_user_id = get_jwt_identity()
        service = VendorApprovalService(db.session)
        result = service.create_approval_workflow(vendor_id, current_user_id)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"❌ Error creating approval workflow: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_approval_bp.route("/approve/<int:vendor_id>", methods=["POST"])
@jwt_required()
def approve_vendor(vendor_id):
    """Approve vendor pada level tertentu"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        approval_level = data.get('approval_level')
        notes = data.get('notes')
        
        if not approval_level:
            return jsonify({
                'success': False,
                'message': 'Approval level diperlukan'
            }), 400
        
        service = VendorApprovalService(db.session)
        result = service.approve_vendor(vendor_id, current_user_id, approval_level, notes)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"❌ Error approving vendor: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_approval_bp.route("/pending", methods=["GET"])
@jwt_required()
def get_pending_approvals():
    """Get daftar vendor yang pending approval"""
    try:
        approval_level = request.args.get('approval_level')
        service = VendorApprovalService(db.session)
        result = service.get_pending_approvals(approval_level)
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting pending approvals: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_approval_bp.route("/requirements-info", methods=["GET"])
@jwt_required()
def get_approval_requirements_info():
    """Get informasi requirements untuk semua vendor type dan business model"""
    try:
        service = VendorApprovalService(db.session)
        
        # Get requirements for all combinations
        combinations = [
            ('internal', 'supplier'),
            ('partner', 'supplier'),
            ('partner', 'reseller'),
            ('partner', 'both')
        ]
        
        requirements_info = {}
        for vendor_type, business_model in combinations:
            requirements_info[f"{vendor_type}_{business_model}"] = service.get_approval_requirements(vendor_type, business_model)
        
        return jsonify({
            'success': True,
            'data': requirements_info
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting approval requirements info: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
