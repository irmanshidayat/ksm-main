#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Request Pembelian Controller - API Endpoints untuk Sistem Request Pembelian Barang
Controller untuk mengelola request pembelian, status management, dan integrasi
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from config.database import db
from domains.inventory.services.request_pembelian_service import RequestPembelianService
from domains.inventory.services.budget_integration_service import BudgetIntegrationService
from shared.utils.serialization import serialize_models

logger = logging.getLogger(__name__)

# Buat Blueprint untuk Flask
request_pembelian_bp = Blueprint('request_pembelian', __name__)

# ===== REQUEST PEMBELIAN CRUD =====

@request_pembelian_bp.route("/requests", methods=["POST"])
@jwt_required()
def create_request():
    """Membuat request pembelian baru"""
    try:
        request_data = request.get_json()
        
        # Get user_id from JWT token if not provided in request
        current_user_id = get_jwt_identity()
        if current_user_id and 'user_id' not in request_data:
            request_data['user_id'] = current_user_id
        elif not current_user_id and 'user_id' not in request_data:
            return jsonify({
                'success': False,
                'message': 'User ID is required. Please provide user_id or ensure you are authenticated.'
            }), 400
        
        # Get department_id from user's primary role if not provided
        if 'department_id' not in request_data and request_data.get('user_id'):
            try:
                from domains.role.models.role_models import UserRole, Role
                user_role = UserRole.query.filter(
                    UserRole.user_id == request_data['user_id'],
                    UserRole.is_active == True,
                    UserRole.is_primary == True
                ).join(Role).first()
                
                if user_role and user_role.role and user_role.role.department_id:
                    request_data['department_id'] = user_role.role.department_id
                    logger.info(f"✅ Auto-filled department_id={user_role.role.department_id} from user's primary role")
                else:
                    # Default to department_id = 1 if no primary role found
                    request_data['department_id'] = 1
                    logger.warning(f"⚠️ No primary role found for user_id={request_data['user_id']}, using default department_id=1")
            except Exception as e:
                logger.warning(f"⚠️ Error getting department_id from user role: {e}. Using default department_id=1")
                request_data['department_id'] = 1
        
        # Validate required fields
        required_fields = ['user_id', 'department_id', 'title']
        for field in required_fields:
            if field not in request_data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        # Validate budget if provided and budget tracking exists
        if 'total_budget' in request_data and request_data['total_budget']:
            budget_service = BudgetIntegrationService(db.session)
            budget_year = datetime.now().year
            
            # Check if budget tracking exists first
            budget_tracking = budget_service.get_budget_tracking(
                department_id=request_data['department_id'],
                budget_year=budget_year,
                budget_category='purchase'
            )
            
            # Only validate if budget tracking exists
            if budget_tracking:
                validation = budget_service.validate_budget(
                    department_id=request_data['department_id'],
                    amount=float(request_data['total_budget']),
                    budget_year=budget_year
                )
                
                if not validation['valid']:
                    return jsonify({
                        'success': False,
                        'message': validation['message'],
                        'budget_info': validation
                    }), 400
            else:
                # Log warning but don't block request if no budget tracking
                logger.warning(f"⚠️ No budget tracking found for department {request_data['department_id']}, year {budget_year}. Request will proceed without budget validation.")
        
        # Create request
        service = RequestPembelianService(db.session)
        result = service.create_request(request_data)
        
        # Reserve budget if provided and budget tracking exists
        if 'total_budget' in request_data and request_data['total_budget']:
            # Check if budget tracking exists before reserving
            budget_tracking = budget_service.get_budget_tracking(
                department_id=request_data['department_id'],
                budget_year=budget_year,
                budget_category='purchase'
            )
            
            if budget_tracking:
                try:
                    budget_service.reserve_budget(
                        department_id=request_data['department_id'],
                        amount=float(request_data['total_budget']),
                        request_id=result.id,
                        budget_year=budget_year
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to reserve budget: {str(e)}. Request created without budget reservation.")
            else:
                logger.info(f"ℹ️ No budget tracking found. Request created without budget reservation.")
        
        return jsonify({
            'success': True,
            'message': 'Request pembelian berhasil dibuat',
            'data': result.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error creating request: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@request_pembelian_bp.route("/", methods=["GET"])
def get_all_requests_root():
    """Mendapatkan semua request pembelian dengan filter - endpoint root untuk kompatibilitas frontend"""
    try:
        # Get query parameters
        filters = {}
        
        if request.args.get('status'):
            status_param = request.args.get('status')
            # Support multiple status separated by comma
            if ',' in status_param:
                filters['status'] = [s.strip() for s in status_param.split(',')]
            else:
                filters['status'] = status_param
        
        if request.args.get('priority'):
            filters['priority'] = request.args.get('priority')
        
        if request.args.get('department_id'):
            filters['department_id'] = int(request.args.get('department_id'))
        
        if request.args.get('user_id'):
            filters['user_id'] = int(request.args.get('user_id'))
        
        if request.args.get('dateFrom'):
            filters['date_from'] = datetime.fromisoformat(request.args.get('dateFrom'))
        elif request.args.get('date_from'):
            filters['date_from'] = datetime.fromisoformat(request.args.get('date_from'))
        
        if request.args.get('dateTo'):
            filters['date_to'] = datetime.fromisoformat(request.args.get('dateTo'))
        elif request.args.get('date_to'):
            filters['date_to'] = datetime.fromisoformat(request.args.get('date_to'))
        
        # Handle search parameter
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        # Handle pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        service = RequestPembelianService(db.session)
        
        # Get total count first (without pagination)
        total_items = len(service.get_all_requests(filters))
        
        # Get paginated results
        results = service.get_all_requests(filters, page=page, per_page=per_page)
        
        # Calculate total pages
        total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1
        
        # Format response sesuai dengan yang diharapkan frontend
        return jsonify({
            'success': True,
            'data': {
                'items': [result.to_dict() for result in results],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_items,
                    'pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ Error getting requests: {str(e)}")
        logger.error(f"❌ Traceback: {error_trace}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error': str(e)
        }), 500

@request_pembelian_bp.route("/requests", methods=["GET"])
def get_all_requests():
    """Mendapatkan semua request pembelian dengan filter"""
    try:
        # Get query parameters
        filters = {}
        
        if request.args.get('status'):
            status_param = request.args.get('status')
            # Support multiple status separated by comma
            if ',' in status_param:
                filters['status'] = [s.strip() for s in status_param.split(',')]
            else:
                filters['status'] = status_param
        
        if request.args.get('priority'):
            filters['priority'] = request.args.get('priority')
        
        if request.args.get('department_id'):
            filters['department_id'] = int(request.args.get('department_id'))
        
        if request.args.get('user_id'):
            filters['user_id'] = int(request.args.get('user_id'))
        
        if request.args.get('date_from'):
            filters['date_from'] = datetime.fromisoformat(request.args.get('date_from'))
        
        if request.args.get('date_to'):
            filters['date_to'] = datetime.fromisoformat(request.args.get('date_to'))
        
        # Handle pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        service = RequestPembelianService(db.session)
        
        # Get total count first (without pagination)
        total_items = len(service.get_all_requests(filters))
        
        # Get paginated results
        results = service.get_all_requests(filters, page=page, per_page=per_page)
        
        # Calculate total pages
        total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1
        
        # Format response sesuai dengan yang diharapkan frontend
        return jsonify({
            'success': True,
            'data': {
                'items': [result.to_dict() for result in results],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_items,
                    'pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ Error getting requests: {str(e)}")
        logger.error(f"❌ Traceback: {error_trace}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error': str(e)
        }), 500

@request_pembelian_bp.route("/requests/<int:request_id>", methods=["GET"])
def get_request_by_id(request_id):
    """Mendapatkan request berdasarkan ID"""
    try:
        service = RequestPembelianService(db.session)
        result = service.get_request_by_id(request_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Request tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting request: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@request_pembelian_bp.route("/requests/reference/<string:reference_id>", methods=["GET"])
def get_request_by_reference(reference_id):
    """Mendapatkan request berdasarkan reference ID"""
    try:
        service = RequestPembelianService(db.session)
        result = service.get_request_by_reference(reference_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Request tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting request by reference: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@request_pembelian_bp.route("/requests/<int:request_id>", methods=["PUT"])
def update_request(request_id):
    """Update request pembelian"""
    try:
        update_data = request.get_json()
        
        service = RequestPembelianService(db.session)
        result = service.update_request(request_id, update_data)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Request tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Request berhasil diupdate',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating request: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@request_pembelian_bp.route("/requests/<int:request_id>", methods=["DELETE"])
def delete_request(request_id):
    """Hapus request pembelian"""
    try:
        service = RequestPembelianService(db.session)
        result = service.delete_request(request_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Request tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Request berhasil dihapus'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error deleting request: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== STATUS MANAGEMENT =====

@request_pembelian_bp.route("/requests/<int:request_id>/submit", methods=["POST"])
def submit_request(request_id):
    """Submit request untuk approval"""
    try:
        service = RequestPembelianService(db.session)
        result = service.submit_request(request_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Request tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Request berhasil disubmit',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error submitting request: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@request_pembelian_bp.route("/requests/<int:request_id>/start-vendor-upload", methods=["POST"])
def start_vendor_upload(request_id):
    """Mulai periode upload vendor"""
    try:
        service = RequestPembelianService(db.session)
        result = service.start_vendor_upload(request_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Request tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Periode upload vendor dimulai',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error starting vendor upload: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@request_pembelian_bp.route("/requests/<int:request_id>/start-analysis", methods=["POST"])
def start_analysis(request_id):
    """Mulai analisis vendor"""
    try:
        service = RequestPembelianService(db.session)
        result = service.start_analysis(request_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Request tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Analisis vendor dimulai',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error starting analysis: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@request_pembelian_bp.route("/requests/<int:request_id>/approve", methods=["POST"])
def approve_request(request_id):
    """Approve request setelah analisis"""
    try:
        data = request.get_json()
        approved_by = data.get('approved_by')
        notes = data.get('notes', '')
        
        if not approved_by:
            return jsonify({
                'success': False,
                'message': 'Field approved_by is required'
            }), 400
        
        service = RequestPembelianService(db.session)
        result = service.approve_request(request_id, approved_by, notes)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Request tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Request berhasil diapprove',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error approving request: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@request_pembelian_bp.route("/requests/<int:request_id>/reject", methods=["POST"])
def reject_request(request_id):
    """Reject request"""
    try:
        data = request.get_json()
        rejected_by = data.get('rejected_by')
        reason = data.get('reason', '')
        
        if not rejected_by:
            return jsonify({
                'success': False,
                'message': 'Field rejected_by is required'
            }), 400
        
        if not reason:
            return jsonify({
                'success': False,
                'message': 'Field reason is required'
            }), 400
        
        service = RequestPembelianService(db.session)
        result = service.reject_request(request_id, rejected_by, reason)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Request tidak ditemukan'
            }), 404
        
        # Release budget if request was rejected and budget tracking exists
        if result.total_budget:
            budget_service = BudgetIntegrationService(db.session)
            budget_year = result.created_at.year
            
            # Check if budget tracking exists before releasing
            budget_tracking = budget_service.get_budget_tracking(
                department_id=result.department_id,
                budget_year=budget_year,
                budget_category='purchase'
            )
            
            if budget_tracking:
                try:
                    budget_service.release_budget(
                        department_id=result.department_id,
                        amount=float(result.total_budget),
                        request_id=request_id,
                        budget_year=budget_year
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to release budget: {str(e)}. Request rejected without budget release.")
            else:
                logger.info(f"ℹ️ No budget tracking found. Request rejected without budget release.")
        
        return jsonify({
            'success': True,
            'message': 'Request berhasil direject',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error rejecting request: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== ITEM MANAGEMENT =====

@request_pembelian_bp.route("/requests/<int:request_id>/items", methods=["POST"])
def add_item(request_id):
    """Tambah item ke request"""
    try:
        item_data = request.get_json()
        
        # Validate required fields
        required_fields = ['barang_id', 'quantity']
        for field in required_fields:
            if field not in item_data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        service = RequestPembelianService(db.session)
        result = service.add_item(request_id, item_data)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Request tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Item berhasil ditambahkan',
            'data': result.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error adding item: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@request_pembelian_bp.route("/requests/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    """Update item dalam request"""
    try:
        update_data = request.get_json()
        
        service = RequestPembelianService(db.session)
        result = service.update_item(item_id, update_data)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Item tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Item berhasil diupdate',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating item: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@request_pembelian_bp.route("/requests/items/<int:item_id>", methods=["DELETE"])
def remove_item(item_id):
    """Hapus item dari request"""
    try:
        service = RequestPembelianService(db.session)
        result = service.remove_item(item_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Item tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Item berhasil dihapus'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error removing item: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== INTEGRATION WITH STOK BARANG =====

@request_pembelian_bp.route("/requests/generate-from-stok", methods=["POST"])
def generate_request_from_stok():
    """Generate request otomatis berdasarkan stok minimum"""
    try:
        data = request.get_json()
        department_id = data.get('department_id')
        user_id = data.get('user_id')
        
        if not department_id or not user_id:
            return jsonify({
                'success': False,
                'message': 'Field department_id and user_id are required'
            }), 400
        
        service = RequestPembelianService(db.session)
        result = service.generate_request_from_stok(department_id, user_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Tidak ada barang dengan stok minimum'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Request otomatis berhasil dibuat',
            'data': result.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error generating request from stok: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== STATISTICS =====

@request_pembelian_bp.route("/requests/statistics", methods=["GET"])
def get_request_statistics():
    """Get statistics untuk request pembelian"""
    try:
        # Get query parameters
        department_id = request.args.get('department_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Convert parameters
        if department_id:
            department_id = int(department_id)
        
        if date_from:
            date_from = datetime.fromisoformat(date_from)
        
        if date_to:
            date_to = datetime.fromisoformat(date_to)
        
        service = RequestPembelianService(db.session)
        stats = service.get_request_statistics(department_id, date_from, date_to)
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting request statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== BUDGET VALIDATION =====

@request_pembelian_bp.route("/requests/validate-budget", methods=["POST"])
def validate_budget():
    """Validasi budget untuk request"""
    try:
        data = request.get_json()
        
        required_fields = ['department_id', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        budget_service = BudgetIntegrationService(db.session)
        budget_year = data.get('budget_year', datetime.now().year)
        
        validation = budget_service.validate_budget(
            department_id=data['department_id'],
            amount=float(data['amount']),
            budget_year=budget_year,
            budget_category=data.get('budget_category', 'purchase')
        )
        
        return jsonify({
            'success': True,
            'data': validation
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error validating budget: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== USER SPECIFIC ENDPOINTS =====

@request_pembelian_bp.route("/requests/user/<int:user_id>", methods=["GET"])
def get_requests_by_user(user_id):
    """Mendapatkan request berdasarkan user"""
    try:
        status = request.args.get('status')
        
        service = RequestPembelianService(db.session)
        results = service.get_requests_by_user(user_id, status)
        
        return jsonify({
            'success': True,
            'data': [result.to_dict() for result in results],
            'total': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting requests by user: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@request_pembelian_bp.route("/dashboard/stats", methods=["GET"])
def get_dashboard_stats():
    """Mendapatkan statistik dashboard request pembelian"""
    try:
        service = RequestPembelianService(db.session)
        stats = service.get_dashboard_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting dashboard stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@request_pembelian_bp.route("/requests/department/<int:department_id>", methods=["GET"])
def get_requests_by_department(department_id):
    """Mendapatkan request berdasarkan departemen"""
    try:
        status = request.args.get('status')
        
        service = RequestPembelianService(db.session)
        results = service.get_requests_by_department(department_id, status)
        
        return jsonify({
            'success': True,
            'data': [result.to_dict() for result in results],
            'total': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting requests by department: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
