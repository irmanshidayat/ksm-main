#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Order Controller - API Endpoints untuk Sistem Vendor Orders
Controller untuk mengelola pesanan vendor dengan status tracking lengkap
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config.database import db
from domains.vendor.services.vendor_order_service import VendorOrderService
from shared.middlewares.role_auth import require_role
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create blueprint
vendor_order_bp = Blueprint('vendor_order', __name__, url_prefix='/api/vendor-orders')


# ===== VENDOR ENDPOINTS =====

@vendor_order_bp.route("/my-orders", methods=["GET"])
@jwt_required()
@require_role(['vendor'])
def get_my_orders():
    """Get list pesanan vendor dengan pagination dan filter"""
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID tidak ditemukan'
            }), 401
        
        # Get vendor_id from user_id using Vendor model
        from domains.vendor.models.vendor_models import Vendor
        vendor = db.session.query(Vendor).filter(Vendor.user_id == user_id).first()
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan untuk user ini'
            }), 404
        
        vendor_id = vendor.id
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status_filter = request.args.get('status', 'all')
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_dir = request.args.get('sort_dir', 'desc')
        
        # Validate pagination
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # Get orders
        service = VendorOrderService(db.session)
        result = service.get_vendor_orders(
            vendor_id=vendor_id,
            page=page,
            per_page=per_page,
            status_filter=status_filter if status_filter != 'all' else None,
            search=search if search else None,
            sort_by=sort_by,
            sort_dir=sort_dir
        )
        
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
        logger.error(f"❌ Error getting vendor orders: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat memuat pesanan'
        }), 500


@vendor_order_bp.route("/<int:order_id>/history", methods=["GET"])
@jwt_required()
@require_role(['vendor', 'admin', 'manager'])
def get_order_status_history(order_id):
    """Get status history untuk pesanan"""
    try:
        # Get user info
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID tidak ditemukan'
            }), 401
        
        # Get status history
        service = VendorOrderService(db.session)
        result = service.get_order_status_history(order_id)
        
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
        logger.error(f"❌ Error getting order status history: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat memuat histori status'
        }), 500


@vendor_order_bp.route("/<int:order_id>", methods=["GET"])
@jwt_required()
@require_role(['vendor', 'admin', 'manager'])
def get_order_detail(order_id):
    """Get detail pesanan"""
    try:
        # Get user info
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID tidak ditemukan'
            }), 401
        
        # Check if user is vendor (can only see their own orders)
        vendor_id = None
        # Note: In real implementation, you'd check user role and get vendor_id from user profile
        # For now, we'll assume vendor_id is same as user_id for vendors
        
        # Get order detail
        service = VendorOrderService(db.session)
        result = service.get_order_detail(order_id, vendor_id)
        
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
        logger.error(f"❌ Error getting order detail: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat memuat detail pesanan'
        }), 500


@vendor_order_bp.route("/<int:order_id>/confirm", methods=["PUT"])
@jwt_required()
@require_role(['vendor'])
def confirm_order(order_id):
    """Vendor konfirmasi pesanan"""
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID tidak ditemukan'
            }), 401
        
        # Get vendor_id from user_id using Vendor model
        from domains.vendor.models.vendor_models import Vendor
        vendor = db.session.query(Vendor).filter(Vendor.user_id == user_id).first()
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan untuk user ini'
            }), 404
        
        vendor_id = vendor.id
        
        # Get request data
        data = request.get_json()
        if not data:
            data = {}
        
        vendor_notes = data.get('vendor_notes', '')
        
        # Confirm order
        service = VendorOrderService(db.session)
        result = service.confirm_order(
            order_id=order_id,
            vendor_id=vendor_id,
            vendor_notes=vendor_notes
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': result['order']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error confirming order: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengkonfirmasi pesanan'
        }), 500


@vendor_order_bp.route("/<int:order_id>/status", methods=["PUT"])
@jwt_required()
@require_role(['vendor', 'admin', 'manager'])
def update_order_status(order_id):
    """Update status pesanan (vendor atau admin)"""
    try:
        # Get user info
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID tidak ditemukan'
            }), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data tidak ditemukan'
            }), 400
        
        new_status = data.get('status')
        tracking_number = data.get('tracking_number')
        estimated_delivery_date = data.get('estimated_delivery_date')
        notes = data.get('notes', '')
        
        if not new_status:
            return jsonify({
                'success': False,
                'message': 'Status tidak boleh kosong'
            }), 400
        
        # Check if user is vendor (can only update their own orders)
        vendor_id = None
        # Note: In real implementation, you'd check user role and get vendor_id from user profile
        # For now, we'll assume vendor_id is same as user_id for vendors
        
        # Update order status
        service = VendorOrderService(db.session)
        result = service.update_order_status(
            order_id=order_id,
            new_status=new_status,
            updated_by_user_id=user_id,
            vendor_id=vendor_id,
            tracking_number=tracking_number,
            estimated_delivery_date=estimated_delivery_date,
            notes=notes
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': result['order']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error updating order status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengupdate status pesanan'
        }), 500


@vendor_order_bp.route("/statistics", methods=["GET"])
@jwt_required()
@require_role(['vendor'])
def get_order_statistics():
    """Get statistik pesanan vendor"""
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID tidak ditemukan'
            }), 401
        
        # Get vendor_id from user_id using Vendor model
        from domains.vendor.models.vendor_models import Vendor
        vendor = db.session.query(Vendor).filter(Vendor.user_id == user_id).first()
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor profile tidak ditemukan untuk user ini'
            }), 404
        
        vendor_id = vendor.id
        
        # Get statistics
        service = VendorOrderService(db.session)
        result = service.get_order_statistics(vendor_id)
        
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
        logger.error(f"❌ Error getting order statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat memuat statistik pesanan'
        }), 500


# ===== ADMIN ENDPOINTS =====

@vendor_order_bp.route("/admin/all-orders", methods=["GET"])
@jwt_required()
@require_role(['admin', 'manager'])
def get_all_orders_admin():
    """Get semua pesanan untuk admin monitoring"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status_filter = request.args.get('status', 'all')
        vendor_filter = request.args.get('vendor_id')
        search = request.args.get('search', '')
        
        # Validate pagination
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # Convert vendor_filter to int if provided
        vendor_id_filter = None
        if vendor_filter:
            try:
                vendor_id_filter = int(vendor_filter)
            except ValueError:
                pass
        
        # Get all orders
        service = VendorOrderService(db.session)
        result = service.get_all_orders_for_admin(
            page=page,
            per_page=per_page,
            status_filter=status_filter if status_filter != 'all' else None,
            vendor_filter=vendor_id_filter,
            search=search if search else None
        )
        
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
        logger.error(f"❌ Error getting all orders for admin: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat memuat pesanan'
        }), 500


@vendor_order_bp.route("/admin/order/<int:order_id>", methods=["PUT"])
@jwt_required()
@require_role(['admin', 'manager'])
def admin_update_order_status(order_id):
    """Admin update status pesanan"""
    try:
        # Get user info
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID tidak ditemukan'
            }), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data tidak ditemukan'
            }), 400
        
        new_status = data.get('status')
        tracking_number = data.get('tracking_number')
        estimated_delivery_date = data.get('estimated_delivery_date')
        admin_notes = data.get('admin_notes', '')
        
        if not new_status:
            return jsonify({
                'success': False,
                'message': 'Status tidak boleh kosong'
            }), 400
        
        # Update order status (admin can update any order)
        service = VendorOrderService(db.session)
        result = service.update_order_status(
            order_id=order_id,
            new_status=new_status,
            updated_by_user_id=user_id,
            vendor_id=None,  # Admin can update any order
            tracking_number=tracking_number,
            estimated_delivery_date=estimated_delivery_date,
            notes=admin_notes
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': result['order']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error updating order status (admin): {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengupdate status pesanan'
        }), 500


# ===== UTILITY ENDPOINTS =====

@vendor_order_bp.route("/status-options", methods=["GET"])
@jwt_required()
def get_status_options():
    """Get daftar status options yang tersedia"""
    try:
        status_options = [
            {
                'value': 'pending_confirmation',
                'label': 'Menunggu Konfirmasi',
                'color': '#f6ad55',
                'description': 'Pesanan menunggu konfirmasi dari vendor'
            },
            {
                'value': 'confirmed',
                'label': 'Dikonfirmasi',
                'color': '#4299e1',
                'description': 'Vendor telah mengkonfirmasi pesanan'
            },
            {
                'value': 'processing',
                'label': 'Diproses',
                'color': '#9f7aea',
                'description': 'Pesanan sedang diproses'
            },
            {
                'value': 'shipped',
                'label': 'Dikirim',
                'color': '#38b2ac',
                'description': 'Pesanan telah dikirim'
            },
            {
                'value': 'delivered',
                'label': 'Diterima',
                'color': '#48bb78',
                'description': 'Pesanan telah diterima'
            },
            {
                'value': 'completed',
                'label': 'Selesai',
                'color': '#68d391',
                'description': 'Pesanan telah selesai'
            },
            {
                'value': 'cancelled',
                'label': 'Dibatalkan',
                'color': '#f56565',
                'description': 'Pesanan dibatalkan'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': status_options
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting status options: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat memuat status options'
        }), 500


@vendor_order_bp.route("/stream", methods=["GET"])
def stream_orders():
    """SSE endpoint untuk realtime updates pesanan vendor"""
    try:
        from flask import Response
        from flask_jwt_extended import decode_token
        import json
        import time
        
        # Get token from query parameter (for SSE compatibility)
        token = request.args.get('token')
        if not token:
            return jsonify({
                'success': False,
                'message': 'Token tidak ditemukan'
            }), 401
        
        # Decode token manually
        try:
            decoded_token = decode_token(token)
            vendor_id = decoded_token.get('sub')
            user_role = decoded_token.get('role')
            
            if not vendor_id:
                return jsonify({
                    'success': False,
                    'message': 'Vendor ID tidak ditemukan dalam token'
                }), 401
            
            if user_role != 'vendor':
                return jsonify({
                    'success': False,
                    'message': 'Akses ditolak - hanya vendor yang dapat mengakses'
                }), 403
                
        except Exception as token_error:
            logger.error(f"Token decode error: {str(token_error)}")
            return jsonify({
                'success': False,
                'message': 'Token tidak valid atau expired'
            }), 401
        
        def generate_events():
            """Generator untuk SSE events"""
            try:
                # Send initial connection event
                yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                
                # Keep connection alive and send periodic updates
                last_check = datetime.utcnow()
                while True:
                    try:
                        # Check for new orders or status changes every 30 seconds
                        current_time = datetime.utcnow()
                        if (current_time - last_check).seconds >= 30:
                            service = VendorOrderService(db.session)
                            
                            # Get recent orders (last 5 minutes)
                            recent_orders = service.get_recent_orders_for_vendor(vendor_id, minutes=5)
                            
                            if recent_orders['success'] and recent_orders['data']:
                                for order in recent_orders['data']:
                                    event_data = {
                                        'type': 'order_update',
                                        'order': order,
                                        'timestamp': current_time.isoformat()
                                    }
                                    yield f"data: {json.dumps(event_data)}\n\n"
                            
                            last_check = current_time
                        
                        # Send keep-alive every 10 seconds
                        time.sleep(10)
                        yield f"data: {json.dumps({'type': 'ping', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                        
                    except Exception as e:
                        logger.error(f"Error in SSE stream: {str(e)}")
                        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                        break
                        
            except Exception as e:
                logger.error(f"SSE connection error: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'message': 'Connection lost'})}\n\n"
        
        return Response(
            generate_events(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating SSE stream: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat membuat koneksi realtime'
        }), 500


@vendor_order_bp.route("/export", methods=["GET"])
@jwt_required()
@require_role(['vendor'])
def export_orders():
    """Export pesanan vendor ke CSV/Excel"""
    try:
        from flask import send_file
        import io
        import csv
        import pandas as pd
        
        vendor_id = get_jwt_identity()
        if not vendor_id:
            return jsonify({
                'success': False,
                'message': 'Vendor ID tidak ditemukan'
            }), 401
        
        # Get query parameters
        format_type = request.args.get('format', 'csv').lower()
        status_filter = request.args.get('status', 'all')
        search = request.args.get('search', '')
        
        # Validate format
        if format_type not in ['csv', 'xlsx', 'excel']:
            return jsonify({
                'success': False,
                'message': 'Format tidak didukung. Gunakan csv atau xlsx'
            }), 400
        
        # Get orders data
        service = VendorOrderService(db.session)
        result = service.get_vendor_orders_for_export(
            vendor_id=vendor_id,
            status_filter=status_filter if status_filter != 'all' else None,
            search=search if search else None
        )
        
        if not result['success']:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
        
        orders = result['data']
        
        # Prepare data for export
        export_data = []
        for order in orders:
            export_data.append({
                'Order Number': order.get('order_number', ''),
                'Reference ID': order.get('reference_id', ''),
                'Item Name': order.get('item_name', ''),
                'Quantity': order.get('ordered_quantity', 0),
                'Unit Price': order.get('unit_price', 0),
                'Total Price': order.get('total_price', 0),
                'Status': order.get('status', ''),
                'Created At': order.get('created_at', ''),
                'Updated At': order.get('updated_at', '')
            })
        
        if format_type == 'csv':
            # Create CSV
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=export_data[0].keys() if export_data else [])
            writer.writeheader()
            writer.writerows(export_data)
            
            # Create file response
            output.seek(0)
            csv_data = io.BytesIO()
            csv_data.write(output.getvalue().encode('utf-8'))
            csv_data.seek(0)
            
            return send_file(
                csv_data,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'vendor_orders_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        
        else:  # xlsx
            # Create Excel
            df = pd.DataFrame(export_data)
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Vendor Orders', index=False)
            
            output.seek(0)
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'vendor_orders_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
            
    except Exception as e:
        logger.error(f"❌ Error exporting orders: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat export data'
        }), 500


@vendor_order_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Vendor Order API is healthy',
        'timestamp': str(datetime.utcnow())
    }), 200
