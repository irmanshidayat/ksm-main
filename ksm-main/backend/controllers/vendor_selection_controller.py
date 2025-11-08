#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Selection Controller - API Endpoints untuk vendor selection management
Controller untuk mengelola seleksi dan approval item penawaran vendor
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import List, Dict, Any
import logging

from config.database import db
from services.vendor_selection_service import VendorSelectionService
from middlewares.role_auth import require_role

logger = logging.getLogger(__name__)

# Buat Blueprint untuk Flask
vendor_selection_bp = Blueprint('vendor_selection', __name__)

# ===== REFERENCE IDS MANAGEMENT =====

@vendor_selection_bp.route("/reference-ids", methods=["GET"])
@jwt_required()
@require_role(['admin', 'manager'])
def get_reference_ids():
    """Get list reference_id dengan pagination & filter status"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        search = request.args.get('search')
        
        # Build filters
        filters = {}
        if status:
            filters['status'] = status
        if search:
            filters['search'] = search
        
        # Get data from service
        service = VendorSelectionService(db.session)
        result = service.get_reference_ids_with_penawarans(page, per_page, filters)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['data'],
                'pagination': result['pagination']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error getting reference IDs: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil data reference IDs'
        }), 500

@vendor_selection_bp.route("/reference/<string:reference_id>/items", methods=["GET"])
@jwt_required()
@require_role(['admin', 'manager'])
def get_penawaran_items_by_reference(reference_id):
    """Get detail items per reference_id (group by vendor)"""
    try:
        service = VendorSelectionService(db.session)
        result = service.get_penawaran_items_by_reference(reference_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Error getting penawaran items for reference {reference_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil data items'
        }), 500

# ===== ITEM SELECTION MANAGEMENT =====

@vendor_selection_bp.route("/select-items", methods=["POST"])
@jwt_required()
@require_role(['admin', 'manager'])
def select_items():
    """Batch select/unselect items dengan support quantity split"""
    try:
        data = request.get_json()
        logger.info(f"📥 Received select-items request: {data}")
        
        if not data:
            logger.warning("⚠️ No data received in select-items request")
            return jsonify({
                'success': False,
                'message': 'Data tidak ditemukan'
            }), 400
        
        # Support both old format (item_ids) and new format (item_selections)
        item_selections = data.get('item_selections', [])
        item_ids = data.get('item_ids', [])  # Backward compatibility
        notes = data.get('notes', '')
        
        # Convert old format to new format if needed
        if item_ids and not item_selections:
            action = data.get('action', 'select')
            item_selections = [
                {
                    'item_id': item_id,
                    'selected_quantity': 0,  # Will be set to vendor_quantity in service
                    'action': action
                }
                for item_id in item_ids
            ]
        
        if not item_selections:
            return jsonify({
                'success': False,
                'message': 'Item selections tidak boleh kosong'
            }), 400
        
        # Validate item_selections format
        for selection in item_selections:
            if 'item_id' not in selection:
                return jsonify({
                    'success': False,
                    'message': 'Setiap selection harus memiliki item_id'
                }), 400
            
            if 'action' not in selection:
                selection['action'] = 'select'  # Default action
            
            if selection['action'] not in ['select', 'unselect']:
                return jsonify({
                    'success': False,
                    'message': 'Action harus berupa select atau unselect'
                }), 400
        
        # Get current user ID
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({
                'success': False,
                'message': 'User ID tidak ditemukan'
            }), 401
        
        # Process selection
        service = VendorSelectionService(db.session)
        logger.info(f"🔄 Processing {len(item_selections)} item selections for user {current_user_id}")
        result = service.select_vendor_items(item_selections, current_user_id, notes)
        
        if result['success']:
            logger.info(f"✅ Successfully updated {result['updated_count']} items")
            return jsonify({
                'success': True,
                'message': result['message'],
                'updated_count': result['updated_count']
            }), 200
        else:
            logger.warning(f"⚠️ Failed to select items: {result['message']}")
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error selecting items: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat memproses seleksi items'
        }), 500

@vendor_selection_bp.route("/approve-selections", methods=["POST"])
@jwt_required()
@require_role(['admin', 'manager'])
def approve_selections():
    """Approve final selection untuk reference_id"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data tidak ditemukan'
            }), 400
        
        # Validate required fields
        reference_id = data.get('reference_id')
        notes = data.get('notes', '')
        
        if not reference_id:
            return jsonify({
                'success': False,
                'message': 'Reference ID tidak boleh kosong'
            }), 400
        
        # Get current user ID
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({
                'success': False,
                'message': 'User ID tidak ditemukan'
            }), 401
        
        # Process approval
        service = VendorSelectionService(db.session)
        result = service.approve_selected_items(reference_id, current_user_id, notes)
        
        if result['success']:
            # Include order creation details in response
            response_data = {
                'success': True,
                'message': result['message'],
                'approved_items_count': result['approved_items_count'],
                'approved_vendors_count': result['approved_vendors_count']
            }
            
            # Add order creation details if available
            if 'order_creation_result' in result:
                order_result = result['order_creation_result']
                response_data['order_creation'] = {
                    'success': order_result['success'],
                    'message': order_result['message'],
                    'orders_created': order_result.get('orders_created', 0),
                    'vendors_notified': order_result.get('vendors_notified', 0)
                }
                
                # If order creation failed, include error details
                if not order_result['success']:
                    response_data['order_creation']['error'] = order_result['message']
                    logger.error(f"❌ Order creation failed for reference {reference_id}: {order_result['message']}")
            
            return jsonify(response_data), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error approving selections: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat memproses approval'
        }), 500

# ===== STATISTICS =====

@vendor_selection_bp.route("/statistics", methods=["GET"])
@jwt_required()
@require_role(['admin', 'manager'])
def get_selection_statistics():
    """Get statistics untuk dashboard"""
    try:
        service = VendorSelectionService(db.session)
        result = service.get_selection_statistics()
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error getting selection statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil statistik'
        }), 500

# ===== BULK OPERATIONS =====

@vendor_selection_bp.route("/bulk-select", methods=["POST"])
@jwt_required()
@require_role(['admin', 'manager'])
def bulk_select_items():
    """Bulk select items dari multiple references"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data tidak ditemukan'
            }), 400
        
        # Validate required fields
        selections = data.get('selections', [])  # Array of {reference_id, item_ids, action}
        notes = data.get('notes', '')
        
        if not selections:
            return jsonify({
                'success': False,
                'message': 'Selections tidak boleh kosong'
            }), 400
        
        # Get current user ID
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({
                'success': False,
                'message': 'User ID tidak ditemukan'
            }), 401
        
        # Process each selection
        service = VendorSelectionService(db.session)
        results = []
        total_updated = 0
        
        for selection in selections:
            reference_id = selection.get('reference_id')
            item_ids = selection.get('item_ids', [])
            action = selection.get('action', 'select')
            
            if not reference_id or not item_ids:
                continue
            
            result = service.select_vendor_items(item_ids, current_user_id, notes, action)
            if result['success']:
                total_updated += result['updated_count']
                results.append({
                    'reference_id': reference_id,
                    'success': True,
                    'updated_count': result['updated_count']
                })
            else:
                results.append({
                    'reference_id': reference_id,
                    'success': False,
                    'message': result['message']
                })
        
        return jsonify({
            'success': True,
            'message': f'Berhasil memproses {len(selections)} selections, total {total_updated} items diupdate',
            'results': results,
            'total_updated': total_updated
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in bulk select: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat memproses bulk selection'
        }), 500
