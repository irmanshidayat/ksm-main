#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Authentication Controller - API Endpoints untuk Sistem Vendor Authentication
Controller untuk mengelola vendor login, profile, dan authentication
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from config.database import db
from services.vendor_auth_service import VendorAuthService
from services.vendor_request_service import VendorRequestService
from services.vendor_template_service import VendorTemplateService
from services.vendor_notification_service import VendorNotificationService
from services.vendor_management_service import VendorManagementService
from utils.security_validator import security_validator
from utils.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# Buat Blueprint untuk Flask
vendor_auth_bp = Blueprint('vendor_auth', __name__, url_prefix='/api/vendor')

# ===== VENDOR AUTHENTICATION =====
# Note: Login endpoint dihapus - vendor menggunakan endpoint /api/login yang sama dengan user biasa

@vendor_auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_vendor_profile():
    """Mendapatkan profil vendor"""
    try:
        user_id = int(get_jwt_identity())
        
        service = VendorAuthService(db.session)
        vendor = service.get_vendor_by_user_id(user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Get vendor categories
        categories = service.get_vendor_categories(vendor.id)
        
        return jsonify({
            'success': True,
            'data': {
                'vendor': vendor.to_dict(),
                'categories': categories
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil profil'
        }), 500

@vendor_auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_vendor_profile():
    """Update profil vendor"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data tidak boleh kosong'
            }), 400
        
        service = VendorAuthService(db.session)
        vendor = service.get_vendor_by_user_id(user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Update profile
        updated_vendor = service.update_vendor_profile(vendor.id, data)
        
        if not updated_vendor:
            return jsonify({
                'success': False,
                'message': 'Gagal mengupdate profil'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Profil berhasil diupdate',
            'data': updated_vendor.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating vendor profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengupdate profil'
        }), 500

@vendor_auth_bp.route("/history", methods=["GET"])
@jwt_required()
def get_vendor_history():
    """Mendapatkan riwayat penawaran vendor"""
    try:
        user_id = int(get_jwt_identity())
        limit = request.args.get('limit', 50, type=int)
        
        service = VendorAuthService(db.session)
        vendor = service.get_vendor_by_user_id(user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Get penawaran history
        history = service.get_vendor_penawaran_history(vendor.id, limit)
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor history: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil riwayat'
        }), 500

# NOTE: Route /dashboard sudah dipindahkan ke vendor_dashboard_controller.py
# untuk menghindari konflik route dengan vendor_dashboard_bp
# Endpoint /api/vendor/dashboard sekarang ditangani oleh vendor_dashboard_bp

@vendor_auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def vendor_logout():
    """Logout vendor"""
    try:
        user_id = int(get_jwt_identity())
        
        # Log logout activity
        logger.info(f"✅ Vendor logout: User ID {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Logout berhasil'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in vendor logout: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat logout'
        }), 500

@vendor_auth_bp.route("/validate", methods=["GET"])
@jwt_required()
def validate_vendor_token():
    """Validasi token vendor"""
    try:
        user_id = int(get_jwt_identity())
        
        service = VendorAuthService(db.session)
        vendor = service.get_vendor_by_user_id(user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Token tidak valid'
            }), 401
        
        return jsonify({
            'success': True,
            'message': 'Token valid',
            'data': {
                'user_id': user_id,
                'vendor_id': vendor.id,
                'company_name': vendor.company_name,
                'permissions': service._get_vendor_permissions()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error validating vendor token: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Token tidak valid'
        }), 401

# Route /requests dipindahkan ke vendor_dashboard_controller.py untuk menghindari duplikasi

# Route /requests/<int:request_id> dipindahkan ke vendor_dashboard_controller.py untuk menghindari duplikasi

@vendor_auth_bp.route("/requests/<int:request_id>/penawaran", methods=["GET"])
@jwt_required()
def get_vendor_penawaran_for_request(request_id):
    """Mendapatkan penawaran vendor untuk request tertentu"""
    try:
        user_id = int(get_jwt_identity())
        
        service = VendorAuthService(db.session)
        vendor = service.get_vendor_by_user_id(user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Get penawaran
        request_service = VendorRequestService(db.session)
        penawaran = request_service.get_vendor_penawaran_for_request(vendor.id, request_id)
        
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
        logger.error(f"❌ Error getting vendor penawaran: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil penawaran'
        }), 500


@vendor_auth_bp.route("/templates/category/<string:category>", methods=["GET"])
@jwt_required()
def get_vendor_templates_by_category(category):
    """Mendapatkan template berdasarkan kategori"""
    try:
        user_id = int(get_jwt_identity())
        
        service = VendorAuthService(db.session)
        vendor = service.get_vendor_by_user_id(user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Get templates by category
        template_service = VendorTemplateService(db.session)
        templates = template_service.get_templates_by_category(category)
        
        return jsonify({
            'success': True,
            'data': templates
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor templates by category: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil template'
        }), 500

# Route /requests/<int:request_id>/upload dipindahkan ke vendor_dashboard_controller.py untuk menghindari duplikasi

@vendor_auth_bp.route("/penawaran/<int:penawaran_id>/files", methods=["GET"])
@jwt_required()
def get_vendor_penawaran_files(penawaran_id):
    """Mendapatkan file-file penawaran vendor"""
    try:
        user_id = int(get_jwt_identity())
        
        service = VendorAuthService(db.session)
        vendor = service.get_vendor_by_user_id(user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Get files
        upload_service = VendorManagementService(db.session)
        files = upload_service.get_penawaran_files(penawaran_id, vendor.id)
        
        return jsonify({
            'success': True,
            'data': files
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor penawaran files: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil file penawaran'
        }), 500

@vendor_auth_bp.route("/penawaran/<int:penawaran_id>", methods=["DELETE"])
@jwt_required()
def delete_vendor_penawaran(penawaran_id):
    """Hapus penawaran vendor"""
    try:
        user_id = int(get_jwt_identity())
        
        service = VendorAuthService(db.session)
        vendor = service.get_vendor_by_user_id(user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Delete penawaran
        upload_service = VendorManagementService(db.session)
        success = upload_service.delete_penawaran(penawaran_id, vendor.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Penawaran berhasil dihapus'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Penawaran tidak ditemukan atau tidak dapat dihapus'
            }), 404
        
    except Exception as e:
        logger.error(f"❌ Error deleting vendor penawaran: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat menghapus penawaran'
        }), 500

@vendor_auth_bp.route("/upload/limits", methods=["GET"])
@jwt_required()
def get_upload_limits():
    """Mendapatkan informasi batasan upload"""
    try:
        user_id = int(get_jwt_identity())
        
        service = VendorAuthService(db.session)
        vendor = service.get_vendor_by_user_id(user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Get upload limits
        upload_service = VendorManagementService(db.session)
        limits = upload_service.get_upload_limits()
        
        return jsonify({
            'success': True,
            'data': limits
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting upload limits: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil informasi upload'
        }), 500

# Notifications endpoints moved to vendor_controller.py to avoid duplication

# All notification endpoints moved to vendor_controller.py to avoid duplication
