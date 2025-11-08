#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Dashboard Controller - API Endpoints untuk vendor dashboard dan profile
Controller untuk mengelola vendor profile, dashboard, dan statistics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import List, Dict, Any
from datetime import datetime
import logging

from config.database import db
from services.vendor_management_service import VendorManagementService
from services.vendor_request_service import VendorRequestService
from services.vendor_notification_service import VendorNotificationService
from utils.serialization import serialize_models

logger = logging.getLogger(__name__)

# Buat Blueprint untuk Flask
vendor_dashboard_bp = Blueprint('vendor_dashboard', __name__)

# ===== VENDOR PROFILE =====

@vendor_dashboard_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_vendor_profile():
    """Get vendor profile"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get vendor by user ID
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'data': vendor.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_dashboard_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_vendor_profile():
    """Update vendor profile"""
    try:
        current_user_id = get_jwt_identity()
        profile_data = request.get_json()
        
        if not profile_data:
            return jsonify({
                'success': False,
                'message': 'Profile data tidak ditemukan'
            }), 400
        
        # Get vendor by user ID
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        # Update profile
        result = vendor_service.update_vendor(vendor.id, profile_data)
        
        return jsonify({
            'success': True,
            'message': 'Profile berhasil diupdate',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating vendor profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== VENDOR DASHBOARD =====

@vendor_dashboard_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def get_vendor_dashboard():
    """Get vendor dashboard data"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get vendor by user ID
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        # Get dashboard data
        request_service = VendorRequestService(db.session)
        dashboard_data = request_service.get_vendor_dashboard_data(vendor.id)
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_dashboard_bp.route("/statistics", methods=["GET"])
@jwt_required()
def get_vendor_statistics():
    """Get vendor statistics"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get vendor by user ID
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        # Get statistics
        request_service = VendorRequestService(db.session)
        stats = request_service.get_vendor_statistics(vendor.id)
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== VENDOR REQUESTS =====

@vendor_dashboard_bp.route("/requests", methods=["GET"])
@jwt_required()
def get_vendor_requests():
    """Get vendor requests"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get vendor by user ID
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        status = request.args.get('status')
        category_filter = request.args.get('category_filter')  # 'all' or 'my_categories'
        
        # Get requests
        request_service = VendorRequestService(db.session)
        result = request_service.get_vendor_requests_paginated(
            vendor_id=vendor.id,
            page=page,
            per_page=per_page,
            status=status,
            category_filter=category_filter
        )
        
        return jsonify({
            'success': True,
            'data': result['requests'],
            'pagination': result['pagination']
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor requests: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_dashboard_bp.route("/requests/<int:request_id>", methods=["GET"])
@jwt_required()
def get_vendor_request(request_id):
    """Get specific vendor request detail"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get vendor by user ID
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        # Get request detail
        request_service = VendorRequestService(db.session)
        request_detail = request_service.get_vendor_request(vendor.id, request_id)
        
        if not request_detail:
            return jsonify({
                'success': False,
                'message': 'Request tidak ditemukan atau tidak dapat diakses'
            }), 404
        
        return jsonify({
            'success': True,
            'data': request_detail
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor request detail: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_dashboard_bp.route("/requests/<int:request_id>/upload", methods=["POST"])
@jwt_required()
def upload_to_request(request_id):
    """Upload file to specific request"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get vendor by user ID
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        # Get uploaded file
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Tidak ada file yang diupload'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Nama file tidak boleh kosong'
            }), 400
        
        # Upload file to request
        request_service = VendorRequestService(db.session)
        result = request_service.upload_file_to_request(
            vendor_id=vendor.id,
            request_id=request_id,
            file=file,
            description=request.form.get('description', '')
        )
        
        return jsonify({
            'success': True,
            'message': 'File berhasil diupload ke request',
            'data': result.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error uploading file to request {request_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== VENDOR NOTIFICATIONS =====

@vendor_dashboard_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_vendor_notifications():
    """Get vendor notifications"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get vendor by user ID
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        # Get notifications
        notification_service = VendorNotificationService(db.session)
        result = notification_service.get_vendor_notifications_paginated(
            vendor_id=vendor.id,
            page=page,
            per_page=per_page,
            unread_only=unread_only
        )
        
        return jsonify({
            'success': True,
            'data': result['notifications'],
            'pagination': result['pagination']
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor notifications: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_dashboard_bp.route("/notifications/<int:notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get vendor by user ID
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        # Mark notification as read
        notification_service = VendorNotificationService(db.session)
        result = notification_service.mark_notification_read(vendor.id, notification_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Notification tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Notification berhasil ditandai sebagai dibaca'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error marking notification {notification_id} as read: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_dashboard_bp.route("/notifications/read-all", methods=["PUT"])
@jwt_required()
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get vendor by user ID
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        # Mark all notifications as read
        notification_service = VendorNotificationService(db.session)
        count = notification_service.mark_all_notifications_read(vendor.id)
        
        return jsonify({
            'success': True,
            'message': f'{count} notifications berhasil ditandai sebagai dibaca'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error marking all notifications as read: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_dashboard_bp.route("/notifications/statistics", methods=["GET"])
@jwt_required()
def get_notification_statistics():
    """Get notification statistics"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get vendor by user ID
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        # Get notification statistics
        notification_service = VendorNotificationService(db.session)
        stats = notification_service.get_notification_statistics(vendor.id)
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting notification statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== VENDOR HISTORY =====

@vendor_dashboard_bp.route("/history", methods=["GET"])
@jwt_required()
def get_vendor_history():
    """Get vendor activity history"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get vendor by user ID
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_user_id(current_user_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan'
            }), 404
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        limit = request.args.get('limit', type=int)  # Support 'limit' parameter from frontend
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Use limit if provided, otherwise use per_page
        if limit:
            per_page = limit
        
        # Get history
        request_service = VendorRequestService(db.session)
        result = request_service.get_vendor_history_paginated(
            vendor_id=vendor.id,
            page=page,
            per_page=per_page,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate success rate
        success_rate = request_service.calculate_vendor_success_rate(vendor.id)
        
        logger.info(f"🔍 Vendor {vendor.id} history result: {len(result['history'])} items, success_rate: {success_rate}%")
        
        return jsonify({
            'success': True,
            'data': result['history'],
            'pagination': result['pagination'],
            'statistics': {
                'total_count': result['pagination']['total'],
                'success_rate': success_rate
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor history: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
