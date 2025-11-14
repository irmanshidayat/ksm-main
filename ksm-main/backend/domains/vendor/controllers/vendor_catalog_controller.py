#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Catalog Controller - API Endpoints untuk vendor catalog management
Controller untuk mengelola katalog barang vendor dan perbandingan penawaran
"""

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import List, Dict, Any
from datetime import datetime
import logging
import io

from config.database import db
from domains.vendor.services.vendor_catalog_service import VendorCatalogService
from shared.utils.serialization import serialize_models

logger = logging.getLogger(__name__)

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl not installed, Excel export will not work")

# Buat Blueprint untuk Flask
vendor_catalog_bp = Blueprint('vendor_catalog', __name__)

# ===== VENDOR CATALOG MANAGEMENT =====

@vendor_catalog_bp.route("/by-reference/<reference_id>", methods=["GET"])
@jwt_required()
def get_vendor_catalog_by_reference(reference_id):
    """Get semua barang vendor untuk reference ID tertentu"""
    try:
        service = VendorCatalogService(db.session)
        result = service.get_vendor_catalog_by_reference(reference_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"❌ Error getting vendor catalog by reference {reference_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/all", methods=["GET"])
@jwt_required()
def get_all_vendor_catalog_items():
    """Get semua barang vendor dengan pagination dan filter"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get filter parameters
        filters = {
            'vendor_id': request.args.get('vendor_id', type=int),
            'reference_id': request.args.get('reference_id'),
            'status': request.args.get('status'),
            'search': request.args.get('search'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'kategori': request.args.get('kategori'),
            'merek': request.args.get('merek'),
            'vendor_type': request.args.get('vendor_type'),
            'business_model': request.args.get('business_model'),
            'min_harga': request.args.get('min_harga', type=float),
            'max_harga': request.args.get('max_harga', type=float),
            'request_id': request.args.get('request_id', type=int),
            'sort_by': request.args.get('sort_by'),
            'sort_order': request.args.get('sort_order')
        }
        
        # Debug logging
        logger.info(f"🔍 get_all_vendor_catalog_items - Raw request args: {dict(request.args)}")
        logger.info(f"🔍 get_all_vendor_catalog_items - Parsed filters: {filters}")
        logger.info(f"🔍 get_all_vendor_catalog_items - Search term: {filters.get('search')}")
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        service = VendorCatalogService(db.session)
        result = service.get_all_vendor_catalog_items(page, per_page, filters)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"❌ Error getting all vendor catalog items: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/references", methods=["GET"])
@jwt_required()
def get_reference_ids_with_penawaran():
    """Get daftar reference ID yang memiliki penawaran vendor"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get filter parameters
        filters = {
            'search': request.args.get('search'),
            'status': request.args.get('status')
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        service = VendorCatalogService(db.session)
        result = service.get_reference_ids_with_penawaran(page, per_page, filters)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"❌ Error getting reference IDs with penawaran: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/items", methods=["POST"])
@jwt_required()
def create_vendor_catalog_item():
    """Create item katalog vendor baru"""
    try:
        item_data = request.get_json()
        if not item_data:
            return jsonify({
                'success': False,
                'message': 'Item data tidak ditemukan'
            }), 400
        
        service = VendorCatalogService(db.session)
        result = service.create_vendor_catalog_item(item_data)
        
        return jsonify(result), 201 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"❌ Error creating vendor catalog item: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/items/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_vendor_catalog_item(item_id):
    """Update item katalog vendor"""
    try:
        update_data = request.get_json()
        if not update_data:
            return jsonify({
                'success': False,
                'message': 'Update data tidak ditemukan'
            }), 400
        
        service = VendorCatalogService(db.session)
        result = service.update_vendor_catalog_item(item_id, update_data)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"❌ Error updating vendor catalog item {item_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/items/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_vendor_catalog_item(item_id):
    """Delete item katalog vendor"""
    try:
        service = VendorCatalogService(db.session)
        result = service.delete_vendor_catalog_item(item_id)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"❌ Error deleting vendor catalog item {item_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/export", methods=["GET"])
@jwt_required()
def export_vendor_catalog():
    """Export data katalog vendor ke CSV atau Excel"""
    try:
        format_type = request.args.get('format', 'csv').lower()
        
        # Get filter parameters
        filters = {
            'vendor_id': request.args.get('vendor_id', type=int),
            'reference_id': request.args.get('reference_id'),
            'status': request.args.get('status'),
            'search': request.args.get('search'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'kategori': request.args.get('kategori'),
            'merek': request.args.get('merek'),
            'min_harga': request.args.get('min_harga', type=float),
            'max_harga': request.args.get('max_harga', type=float),
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        service = VendorCatalogService(db.session)
        
        # Get all data (no pagination for export)
        result = service.get_all_vendor_catalog_items(page=1, per_page=10000, filters=filters)
        
        if not result['success']:
            return jsonify(result), 400
        
        items = result['data']
        
        if format_type in ['excel', 'xlsx']:
            if not OPENPYXL_AVAILABLE:
                return jsonify({
                    'success': False,
                    'message': 'openpyxl tidak terinstall, tidak dapat export Excel'
                }), 500
            
            # Create Excel workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Daftar Barang Vendor"
            
            # Define headers
            headers = [
                'No', 'Reference ID', 'Request Title', 'Vendor', 'Email Vendor',
                'Nama Barang', 'Kategori', 'Merek', 'Quantity', 'Satuan',
                'Harga Satuan', 'Harga Total', 'Spesifikasi Vendor', 
                'Status Penawaran', 'Tanggal Submit', 'Catatan'
            ]
            
            # Style for headers
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")
            
            # Write headers
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
            # Write data
            for row, item in enumerate(items, 2):
                row_data = [
                    row - 1,  # No
                    item.get('request', {}).get('reference_id', ''),
                    item.get('request', {}).get('title', ''),
                    item.get('vendor', {}).get('company_name', ''),
                    item.get('vendor', {}).get('email', ''),
                    item.get('nama_barang', ''),
                    item.get('kategori', ''),
                    item.get('vendor_merk', ''),
                    item.get('vendor_quantity', 0),
                    item.get('satuan', 'pcs'),
                    item.get('vendor_unit_price', 0),
                    item.get('vendor_total_price', 0),
                    item.get('vendor_specifications', ''),
                    item.get('penawaran', {}).get('status', ''),
                    item.get('penawaran', {}).get('created_at', ''),
                    item.get('vendor_notes', '')
                ]
                
                for col, value in enumerate(row_data, 1):
                    ws.cell(row=row, column=col, value=value)
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Save to BytesIO
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"daftar_barang_vendor_{timestamp}.xlsx"
            
            return send_file(
                output,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            # CSV export (existing logic)
            result = service.export_vendor_catalog(filters)
            
            if result['success']:
                # Create file-like object
                csv_io = io.BytesIO()
                csv_io.write(result['data'].encode('utf-8'))
                csv_io.seek(0)
                
                return send_file(
                    csv_io,
                    as_attachment=True,
                    download_name=result['filename'],
                    mimetype='text/csv'
                )
            else:
                return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Error exporting vendor catalog: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/vendors", methods=["GET"])
@jwt_required()
def get_vendors_list():
    """Get daftar vendor untuk dropdown"""
    try:
        service = VendorCatalogService(db.session)
        vendors = service.get_vendors_list()
        
        return jsonify({
            'success': True,
            'data': vendors
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendors list: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/vendors/public", methods=["GET"])
def get_vendors_list_public():
    """Get daftar vendor untuk dropdown (public endpoint for testing)"""
    try:
        service = VendorCatalogService(db.session)
        vendors = service.get_vendors_list()
        
        return jsonify({
            'success': True,
            'data': vendors
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendors list: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@vendor_catalog_bp.route("/request-items", methods=["GET"])
@jwt_required()
def get_request_items_list():
    """Get daftar request items untuk dropdown"""
    try:
        request_id = request.args.get('request_id', type=int)
        
        service = VendorCatalogService(db.session)
        items = service.get_request_items_list(request_id)
        
        return jsonify({
            'success': True,
            'data': items
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting request items list: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/categories", methods=["GET"])
@jwt_required()
def get_categories_list():
    """Get daftar kategori untuk dropdown"""
    try:
        service = VendorCatalogService(db.session)
        categories = service.get_categories_list()
        
        return jsonify({
            'success': True,
            'data': categories
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting categories list: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/categories/public", methods=["GET"])
def get_categories_list_public():
    """Get daftar kategori untuk dropdown (public endpoint for testing)"""
    try:
        service = VendorCatalogService(db.session)
        categories = service.get_categories_list()
        
        return jsonify({
            'success': True,
            'data': categories
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting categories list: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/requests", methods=["GET"])
@jwt_required()
def get_requests_list():
    """Get daftar requests untuk dropdown"""
    try:
        service = VendorCatalogService(db.session)
        requests = service.get_requests_list()
        
        return jsonify({
            'success': True,
            'data': requests
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting requests list: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/requests/public", methods=["GET"])
def get_requests_list_public():
    """Get daftar requests untuk dropdown (public endpoint for testing)"""
    try:
        service = VendorCatalogService(db.session)
        requests = service.get_requests_list()
        
        return jsonify({
            'success': True,
            'data': requests
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting requests list: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/mereks", methods=["GET"])
@jwt_required()
def get_mereks_list():
    """Get daftar merek untuk dropdown"""
    try:
        service = VendorCatalogService(db.session)
        mereks = service.get_mereks_list()
        
        return jsonify({
            'success': True,
            'data': mereks
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting mereks list: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/mereks/public", methods=["GET"])
def get_mereks_list_public():
    """Get daftar merek untuk dropdown (public endpoint for testing)"""
    try:
        service = VendorCatalogService(db.session)
        mereks = service.get_mereks_list()
        
        return jsonify({
            'success': True,
            'data': mereks
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting mereks list: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/penawarans", methods=["GET"])
@jwt_required()
def get_penawarans_list():
    """Get daftar penawaran untuk dropdown"""
    try:
        service = VendorCatalogService(db.session)
        penawarans = service.get_penawarans_list()
        
        return jsonify({
            'success': True,
            'data': penawarans
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting penawarans list: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_catalog_bp.route("/debug/penawarans", methods=["GET"])
@jwt_required()
def debug_penawarans_list():
    """Debug endpoint untuk penawaran list"""
    try:
        service = VendorCatalogService(db.session)
        debug_info = service.debug_penawarans_list()
        
        return jsonify({
            'success': True,
            'debug_info': debug_info
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error debugging penawarans list: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500