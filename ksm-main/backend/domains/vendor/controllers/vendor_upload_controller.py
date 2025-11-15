#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Upload Controller - API Endpoints untuk file upload operations
Controller untuk mengelola file upload, chunk upload, dan file management
"""

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import List, Dict, Any
from datetime import datetime
import logging
import os

from config.database import db
from domains.vendor.services.vendor_management_service import VendorManagementService
from shared.utils.security_validator import security_validator
from shared.utils.rate_limiter import upload_rate_limiter
from config.upload_config import upload_config
from domains.vendor.models.vendor_models import VendorPenawaran

logger = logging.getLogger(__name__)

# Buat Blueprint untuk Flask
vendor_upload_bp = Blueprint('vendor_upload', __name__)

# ===== FILE UPLOAD =====

@vendor_upload_bp.route("/<int:vendor_id>/upload", methods=["POST"])
@jwt_required()
@upload_rate_limiter
def upload_file(vendor_id):
    """Upload file untuk vendor"""
    try:
        # Check if vendor exists
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_id(vendor_id)
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
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
        
        # Get additional data
        request_id = request.form.get('request_id')
        description = request.form.get('description', '')
        
        # Validate file
        if not security_validator.validate_file_upload(file):
            return jsonify({
                'success': False,
                'message': 'File tidak valid atau tidak diizinkan'
            }), 400
        
        # Upload file
        upload_service = VendorManagementService(db.session)
        result = upload_service.upload_file(
            vendor_id=vendor_id,
            file=file,
            request_id=request_id,
            description=description
        )
        
        return jsonify({
            'success': True,
            'message': 'File berhasil diupload',
            'data': result.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error uploading file for vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_upload_bp.route("/<int:vendor_id>/upload-chunk", methods=["POST"])
@jwt_required()
@upload_rate_limiter
def upload_chunk(vendor_id):
    """Upload file chunk untuk large file upload"""
    try:
        # Check if vendor exists
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_id(vendor_id)
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Get chunk data
        chunk_data = request.get_json()
        if not chunk_data:
            return jsonify({
                'success': False,
                'message': 'Chunk data tidak ditemukan'
            }), 400
        
        required_fields = ['chunk_number', 'total_chunks', 'chunk_data', 'file_name']
        for field in required_fields:
            if field not in chunk_data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        # Upload chunk
        upload_service = VendorManagementService(db.session)
        result = upload_service.upload_chunk(
            vendor_id=vendor_id,
            chunk_number=chunk_data['chunk_number'],
            total_chunks=chunk_data['total_chunks'],
            chunk_data=chunk_data['chunk_data'],
            file_name=chunk_data['file_name'],
            request_id=chunk_data.get('request_id')
        )
        
        return jsonify({
            'success': True,
            'message': 'Chunk berhasil diupload',
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error uploading chunk for vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_upload_bp.route("/<int:vendor_id>/finalize-upload", methods=["POST"])
@jwt_required()
def finalize_upload(vendor_id):
    """Finalize chunked upload"""
    try:
        # Check if vendor exists
        vendor_service = VendorManagementService(db.session)
        vendor = vendor_service.get_vendor_by_id(vendor_id)
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Get finalize data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Finalize data tidak ditemukan'
            }), 400
        
        required_fields = ['file_name', 'total_chunks']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        # Finalize upload
        upload_service = VendorManagementService(db.session)
        result = upload_service.finalize_upload(
            vendor_id=vendor_id,
            file_name=data['file_name'],
            total_chunks=data['total_chunks'],
            request_id=data.get('request_id'),
            description=data.get('description', '')
        )
        
        return jsonify({
            'success': True,
            'message': 'Upload berhasil difinalisasi',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error finalizing upload for vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== FILE MANAGEMENT =====

@vendor_upload_bp.route("/<int:vendor_id>/files/<int:request_id>", methods=["GET"])
@jwt_required()
def get_vendor_files(vendor_id, request_id):
    """Get files for vendor and request"""
    try:
        upload_service = VendorManagementService(db.session)
        files = upload_service.get_penawaran_files(vendor_id, request_id)
        
        return jsonify({
            'success': True,
            'data': [file.to_dict() for file in files]
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting files for vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_upload_bp.route("/<int:vendor_id>/files/<int:file_id>", methods=["GET", "DELETE"])
@jwt_required()
def get_or_delete_vendor_file(vendor_id, file_id):
    """Get or delete vendor file"""
    try:
        upload_service = VendorManagementService(db.session)
        
        if request.method == "GET":
            # Get file info
            file_info = upload_service.get_file_by_id(file_id)
            
            if not file_info:
                return jsonify({
                    'success': False,
                    'message': 'File tidak ditemukan'
                }), 404
            
            # Check if vendor owns this file
            penawaran = upload_service.db.query(VendorPenawaran).filter(
                VendorPenawaran.id == file_info.vendor_penawaran_id,
                VendorPenawaran.vendor_id == vendor_id
            ).first()
            
            if not penawaran:
                return jsonify({
                    'success': False,
                    'message': 'File tidak ditemukan atau tidak memiliki akses'
                }), 404
            
            return jsonify({
                'success': True,
                'data': file_info.to_dict()
            }), 200
            
        else:  # DELETE
            result = upload_service.delete_penawaran_file(file_id, vendor_id)
            
            if not result:
                return jsonify({
                    'success': False,
                    'message': 'File tidak ditemukan'
                }), 404
            
            return jsonify({
                'success': True,
                'message': 'File berhasil dihapus'
            }), 200
        
    except Exception as e:
        logger.error(f"❌ Error with file {file_id} for vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_upload_bp.route("/files/<int:file_id>/download", methods=["GET"])
@jwt_required()
def download_file(file_id):
    """Download vendor file"""
    try:
        upload_service = VendorManagementService(db.session)
        file_info = upload_service.get_file_info(file_id)
        
        if not file_info:
            return jsonify({
                'success': False,
                'message': 'File tidak ditemukan'
            }), 404
        
        # Check if file exists
        file_path = file_info['file_path']
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': 'File tidak ditemukan di storage'
            }), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_info['original_filename']
        )
        
    except Exception as e:
        logger.error(f"❌ Error downloading file {file_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== UPLOAD CONFIGURATION =====

@vendor_upload_bp.route("/upload-limits", methods=["GET"])
@jwt_required()
def get_upload_limits():
    """Get upload limits configuration"""
    try:
        limits = upload_config.get_upload_limits()
        
        return jsonify({
            'success': True,
            'data': limits
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting upload limits: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_upload_bp.route("/upload-stats", methods=["GET"])
@jwt_required()
def get_upload_stats():
    """Get upload statistics"""
    try:
        upload_service = VendorManagementService(db.session)
        stats = upload_service.get_upload_statistics()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting upload stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_upload_bp.route("/upload-config", methods=["GET"])
@jwt_required()
def get_upload_config():
    """Get upload configuration"""
    try:
        config = upload_config.get_config()
        
        return jsonify({
            'success': True,
            'data': config
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting upload config: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_upload_bp.route("/upload-config", methods=["PUT"])
@jwt_required()
def update_upload_config():
    """Update upload configuration"""
    try:
        config_data = request.get_json()
        if not config_data:
            return jsonify({
                'success': False,
                'message': 'Config data tidak ditemukan'
            }), 400
        
        # Update configuration
        upload_config.update_config(config_data)
        
        return jsonify({
            'success': True,
            'message': 'Upload configuration berhasil diupdate'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating upload config: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
