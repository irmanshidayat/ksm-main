#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Debug Controller - API Endpoints untuk debugging vendor issues
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from config.database import db
from domains.vendor.services.vendor_management_service import VendorManagementService
from models import Vendor, VendorPenawaran
from models import User

logger = logging.getLogger(__name__)

# Buat Blueprint untuk Flask
vendor_debug_bp = Blueprint('vendor_debug', __name__)

@vendor_debug_bp.route("/debug/vendor-info", methods=["GET"])
@jwt_required()
def debug_vendor_info():
    """Debug endpoint untuk melihat info vendor dan penawaran"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get vendor info
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Get all penawarans for this vendor
        penawarans = db.session.query(VendorPenawaran).filter(
            VendorPenawaran.vendor_id == vendor.id
        ).all()
        
        # Get all penawarans in database (for comparison)
        all_penawarans = db.session.query(VendorPenawaran).all()
        
        # Check if there are penawarans with user_id as vendor_id (potential mismatch)
        potential_mismatch = db.session.query(VendorPenawaran).filter(
            VendorPenawaran.vendor_id == current_user_id
        ).all()
        
        return jsonify({
            'success': True,
            'data': {
                'vendor_info': {
                    'id': vendor.id,
                    'company_name': vendor.company_name,
                    'user_id': vendor.user_id,
                    'email': vendor.email
                },
                'current_user_id': current_user_id,
                'penawarans_for_vendor': [
                    {
                        'id': p.id,
                        'reference_id': p.reference_id,
                        'status': p.status,
                        'created_at': p.created_at.isoformat() if p.created_at else None
                    } for p in penawarans
                ],
                'potential_mismatch_penawarans': [
                    {
                        'id': p.id,
                        'reference_id': p.reference_id,
                        'status': p.status,
                        'vendor_id': p.vendor_id,
                        'created_at': p.created_at.isoformat() if p.created_at else None
                    } for p in potential_mismatch
                ],
                'all_penawarans_count': len(all_penawarans),
                'vendor_penawarans_count': len(penawarans),
                'mismatch_penawarans_count': len(potential_mismatch)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in debug vendor info: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_debug_bp.route("/debug/fix-vendor-penawaran", methods=["POST"])
@jwt_required()
def fix_vendor_penawaran():
    """Fix penawaran yang tersimpan dengan vendor_id yang salah"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get vendor info
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Find penawarans with wrong vendor_id (using user_id instead of vendor.id)
        wrong_penawarans = db.session.query(VendorPenawaran).filter(
            VendorPenawaran.vendor_id == current_user_id
        ).all()
        
        fixed_count = 0
        for penawaran in wrong_penawarans:
            penawaran.vendor_id = vendor.id
            fixed_count += 1
        
        if fixed_count > 0:
            db.session.commit()
            logger.info(f"✅ Fixed {fixed_count} penawaran for vendor {vendor.id}")
        
        return jsonify({
            'success': True,
            'message': f'Berhasil memperbaiki {fixed_count} penawaran',
            'fixed_count': fixed_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Error fixing vendor penawaran: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
