#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Bulk Import Controller - API Endpoints untuk bulk import vendor
Controller untuk mengelola bulk import vendor dari file Excel/CSV
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from typing import List, Dict, Any
from datetime import datetime
import logging
import pandas as pd
import io
from functools import wraps

from config.database import db
from services.vendor_management_service import VendorManagementService
from utils.serialization import serialize_models
from utils.security_validator import security_validator
from utils.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# Buat Blueprint untuk Flask
vendor_bulk_import_bp = Blueprint('vendor_bulk_import', __name__)

# Custom decorator untuk mengizinkan OPTIONS request
def jwt_required_allow_options(f):
    """Decorator yang mengizinkan OPTIONS request untuk CORS preflight"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS':
            return '', 200
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication failed'}), 401
    return decorated_function

# ===== BULK IMPORT VALIDATION =====

@vendor_bulk_import_bp.route("/api/vendor/bulk-validate", methods=["POST"])
@jwt_required_allow_options
def validate_bulk_import():
    """Validate file untuk bulk import vendor"""
    try:
        # Check if file is provided
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'File tidak ditemukan'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'File tidak dipilih'
            }), 400
        
        # Read file based on extension
        file_extension = file.filename.split('.')[-1].lower()
        
        try:
            if file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(file)
            elif file_extension == 'csv':
                df = pd.read_csv(file)
            else:
                return jsonify({
                    'success': False,
                    'message': 'Format file tidak didukung. Gunakan Excel (.xlsx, .xls) atau CSV (.csv)'
                }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Gagal membaca file: {str(e)}'
            }), 400
        
        # Validate required columns
        required_columns = ['Nama Barang', 'Vendor ID', 'Quantity', 'Harga Satuan', 'Harga Total', 'Kategori', 'Merek', 'Spesifikasi', 'Status']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'success': False,
                'message': f'Kolom yang diperlukan tidak ditemukan: {", ".join(missing_columns)}'
            }), 400
        
        # Validate data
        errors = []
        warnings = []
        preview_data = []
        
        for index, row in df.iterrows():
            row_errors = []
            
            # Validate required fields
            if pd.isna(row['Nama Barang']) or str(row['Nama Barang']).strip() == '':
                row_errors.append('Nama Barang tidak boleh kosong')
            
            if pd.isna(row['Vendor ID']) or str(row['Vendor ID']).strip() == '':
                row_errors.append('Vendor ID tidak boleh kosong')
            
            if pd.isna(row['Quantity']) or not str(row['Quantity']).isdigit():
                row_errors.append('Quantity harus berupa angka')
            
            if pd.isna(row['Harga Satuan']) or not str(row['Harga Satuan']).replace('.', '').isdigit():
                row_errors.append('Harga Satuan harus berupa angka')
            
            if pd.isna(row['Harga Total']) or not str(row['Harga Total']).replace('.', '').isdigit():
                row_errors.append('Harga Total harus berupa angka')
            
            # Check if vendor exists
            try:
                vendor_id = int(row['Vendor ID'])
                # TODO: Check if vendor exists in database
            except ValueError:
                row_errors.append('Vendor ID harus berupa angka')
            
            if row_errors:
                errors.extend([f'Baris {index + 2}: {error}' for error in row_errors])
            else:
                # Add to preview data
                preview_data.append({
                    'nama_barang': str(row['Nama Barang']).strip(),
                    'vendor_id': int(row['Vendor ID']),
                    'quantity': int(row['Quantity']),
                    'harga_satuan': float(str(row['Harga Satuan']).replace(',', '')),
                    'harga_total': float(str(row['Harga Total']).replace(',', '')),
                    'kategori': str(row['Kategori']).strip() if not pd.isna(row['Kategori']) else '',
                    'merek': str(row['Merek']).strip() if not pd.isna(row['Merek']) else '',
                    'spesifikasi': str(row['Spesifikasi']).strip() if not pd.isna(row['Spesifikasi']) else '',
                    'status': str(row['Status']).strip() if not pd.isna(row['Status']) else 'submitted'
                })
        
        return jsonify({
            'success': True,
            'data': {
                'isValid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'preview': preview_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error validating bulk import: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan saat memvalidasi file: {str(e)}'
        }), 500

# ===== BULK IMPORT EXECUTION =====

@vendor_bulk_import_bp.route("/api/vendor/bulk-import", methods=["POST"])
@jwt_required_allow_options
def execute_bulk_import():
    """Execute bulk import vendor"""
    try:
        # Check if file is provided
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'File tidak ditemukan'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'File tidak dipilih'
            }), 400
        
        # Read file
        file_extension = file.filename.split('.')[-1].lower()
        
        try:
            if file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(file)
            elif file_extension == 'csv':
                df = pd.read_csv(file)
            else:
                return jsonify({
                    'success': False,
                    'message': 'Format file tidak didukung'
                }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Gagal membaca file: {str(e)}'
            }), 400
        
        # Process data
        successful_imports = 0
        failed_imports = 0
        errors = []
        imported_items = []
        
        for index, row in df.iterrows():
            try:
                # Validate row data
                if pd.isna(row['Nama Barang']) or str(row['Nama Barang']).strip() == '':
                    errors.append({
                        'row': index + 2,
                        'field': 'Nama Barang',
                        'message': 'Nama Barang tidak boleh kosong'
                    })
                    failed_imports += 1
                    continue
                
                # Create vendor catalog item
                # TODO: Implement actual database insertion
                # For now, just simulate success
                item_data = {
                    'id': successful_imports + 1,
                    'nama_barang': str(row['Nama Barang']).strip(),
                    'vendor_id': int(row['Vendor ID']),
                    'quantity': int(row['Quantity']),
                    'harga_satuan': float(str(row['Harga Satuan']).replace(',', '')),
                    'harga_total': float(str(row['Harga Total']).replace(',', '')),
                    'kategori': str(row['Kategori']).strip() if not pd.isna(row['Kategori']) else '',
                    'merek': str(row['Merek']).strip() if not pd.isna(row['Merek']) else '',
                    'spesifikasi': str(row['Spesifikasi']).strip() if not pd.isna(row['Spesifikasi']) else '',
                    'status': str(row['Status']).strip() if not pd.isna(row['Status']) else 'submitted'
                }
                
                imported_items.append(item_data)
                successful_imports += 1
                
            except Exception as e:
                errors.append({
                    'row': index + 2,
                    'field': 'General',
                    'message': f'Error processing row: {str(e)}'
                })
                failed_imports += 1
        
        return jsonify({
            'success': True,
            'data': {
                'total_rows': len(df),
                'successful_imports': successful_imports,
                'failed_imports': failed_imports,
                'errors': errors,
                'imported_vendors': imported_items
            }
        })
        
    except Exception as e:
        logger.error(f"Error executing bulk import: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan saat mengimport data: {str(e)}'
        }), 500

# ===== HEALTH CHECK =====

@vendor_bulk_import_bp.route("/api/vendor/bulk-import/health", methods=["GET"])
def health_check():
    """Health check untuk bulk import service"""
    return jsonify({
        'status': 'healthy',
        'service': 'vendor_bulk_import',
        'timestamp': datetime.utcnow().isoformat()
    })
