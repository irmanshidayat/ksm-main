#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor CRUD Controller - API Endpoints untuk CRUD operations vendor
Controller untuk mengelola vendor registration, approval, dan basic operations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from typing import List, Dict, Any
from datetime import datetime
import logging
from functools import wraps

from config.database import db
from models.request_pembelian_models import Vendor
from services.vendor_management_service import VendorManagementService
from services.vendor_auth_service import VendorAuthService
from utils.serialization import serialize_models
from utils.security_validator import security_validator
from utils.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# Buat Blueprint untuk Flask
vendor_crud_bp = Blueprint('vendor_crud', __name__)

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

# ===== VENDOR LIST & MANAGEMENT =====

@vendor_crud_bp.route("/list", methods=["GET"])
@jwt_required_allow_options
def get_vendor_list():
    """Get paginated list of vendors with filters"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        status = request.args.get('status', '')
        vendor_type = request.args.get('vendor_type', '')
        business_model = request.args.get('business_model', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        sort_field = request.args.get('sort_field', 'created_at')
        sort_direction = request.args.get('sort_direction', 'desc')
        
        # Build query
        query = Vendor.query
        
        # Apply filters
        if search:
            query = query.filter(
                (Vendor.company_name.ilike(f'%{search}%')) |
                (Vendor.contact_person.ilike(f'%{search}%')) |
                (Vendor.email.ilike(f'%{search}%'))
            )
        
        if category:
            query = query.filter(Vendor.vendor_category == category)
        
        if status:
            query = query.filter(Vendor.status == status)
        
        if vendor_type:
            query = query.filter(Vendor.vendor_type == vendor_type)
        
        if business_model:
            query = query.filter(Vendor.business_model == business_model)
        
        if date_from:
            query = query.filter(Vendor.created_at >= date_from)
        
        if date_to:
            query = query.filter(Vendor.created_at <= date_to)
        
        # Apply sorting
        if hasattr(Vendor, sort_field):
            if sort_direction == 'desc':
                query = query.order_by(getattr(Vendor, sort_field).desc())
            else:
                query = query.order_by(getattr(Vendor, sort_field).asc())
        
        # Get paginated results
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialize vendors with documents
        vendors_data = []
        for vendor in pagination.items:
            vendor_dict = {
                'id': vendor.id,
                'company_name': vendor.company_name,
                'contact_person': vendor.contact_person,
                'email': vendor.email,
                'phone': vendor.phone,
                'address': vendor.address,
                'vendor_category': vendor.vendor_category,
                'vendor_type': vendor.vendor_type,
                'business_model': vendor.business_model,
                'business_license': vendor.business_license,
                'tax_id': vendor.tax_id,
                'bank_account': vendor.bank_account,
                'status': vendor.status,
                'ktp_director_name': vendor.ktp_director_name,
                'ktp_director_number': vendor.ktp_director_number,
                'created_at': vendor.created_at.isoformat() if vendor.created_at else None,
                'updated_at': vendor.updated_at.isoformat() if vendor.updated_at else None,
                'documents': {
                    'ktp_file': vendor.ktp_director_file_path,
                    'akta_perusahaan_file': vendor.akta_perusahaan_file_path,
                    'nib_file': vendor.nib_file_path,
                    'npwp_file': vendor.npwp_file_path,
                    'company_profile_file': vendor.company_profile_file_path,
                    'surat_keagenan_file': vendor.surat_keagenan_file_path,
                    'tkdn_file': vendor.tkdn_file_path,
                    'surat_pernyataan_manufaktur_file': vendor.surat_pernyataan_manufaktur_file_path
                }
            }
            vendors_data.append(vendor_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'vendors': vendors_data,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'total_pages': pagination.pages
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting vendor list: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Gagal mengambil daftar vendor: {str(e)}'
        }), 500

@vendor_crud_bp.route("/<int:vendor_id>/detail", methods=["GET"])
@jwt_required_allow_options
def get_vendor_detail(vendor_id):
    """Get detailed information of a specific vendor"""
    try:
        vendor = Vendor.query.get_or_404(vendor_id)
        
        vendor_data = {
            'id': vendor.id,
            'company_name': vendor.company_name,
            'contact_person': vendor.contact_person,
            'email': vendor.email,
            'phone': vendor.phone,
            'address': vendor.address,
            'vendor_category': vendor.vendor_category,
            'vendor_type': vendor.vendor_type,
            'business_model': vendor.business_model,
            'business_license': vendor.business_license,
            'tax_id': vendor.tax_id,
            'bank_account': vendor.bank_account,
            'status': vendor.status,
            'ktp_director_name': vendor.ktp_director_name,
            'ktp_director_number': vendor.ktp_director_number,
            'created_at': vendor.created_at.isoformat() if vendor.created_at else None,
            'updated_at': vendor.updated_at.isoformat() if vendor.updated_at else None,
            'documents': {
                'ktp_file': vendor.ktp_director_file_path,
                'akta_perusahaan_file': vendor.akta_perusahaan_file_path,
                'nib_file': vendor.nib_file_path,
                'npwp_file': vendor.npwp_file_path,
                'company_profile_file': vendor.company_profile_file_path,
                'surat_keagenan_file': vendor.surat_keagenan_file_path,
                'tkdn_file': vendor.tkdn_file_path,
                'surat_pernyataan_manufaktur_file': vendor.surat_pernyataan_manufaktur_file_path
            }
        }
        
        return jsonify({
            'success': True,
            'data': vendor_data
        })
        
    except Exception as e:
        logger.error(f"Error getting vendor detail: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Gagal mengambil detail vendor: {str(e)}'
        }), 500

@vendor_crud_bp.route("/bulk-delete", methods=["POST"])
@jwt_required_allow_options
def bulk_delete_vendors():
    """Delete multiple vendors"""
    try:
        data = request.get_json()
        vendor_ids = data.get('vendor_ids', [])
        
        if not vendor_ids:
            return jsonify({
                'success': False,
                'error': 'Tidak ada vendor yang dipilih untuk dihapus'
            }), 400
        
        # Delete vendors
        deleted_count = 0
        for vendor_id in vendor_ids:
            vendor = Vendor.query.get(vendor_id)
            if vendor:
                db.session.delete(vendor)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{deleted_count} vendor berhasil dihapus'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error bulk deleting vendors: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Gagal menghapus vendor: {str(e)}'
        }), 500

@vendor_crud_bp.route("/bulk-status", methods=["POST"])
@jwt_required_allow_options
def bulk_update_status():
    """Update status of multiple vendors"""
    try:
        data = request.get_json()
        vendor_ids = data.get('vendor_ids', [])
        status = data.get('status', '')
        
        if not vendor_ids:
            return jsonify({
                'success': False,
                'error': 'Tidak ada vendor yang dipilih'
            }), 400
        
        if not status:
            return jsonify({
                'success': False,
                'error': 'Status tidak boleh kosong'
            }), 400
        
        # Update vendors
        updated_count = 0
        for vendor_id in vendor_ids:
            vendor = Vendor.query.get(vendor_id)
            if vendor:
                vendor.status = status
                vendor.updated_at = datetime.utcnow()
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Status {updated_count} vendor berhasil diubah'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error bulk updating vendor status: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Gagal mengubah status vendor: {str(e)}'
        }), 500

@vendor_crud_bp.route("/export", methods=["GET"])
@jwt_required_allow_options
def export_vendors():
    """Export vendors to Excel or PDF"""
    try:
        format_type = request.args.get('format', 'excel')
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        status = request.args.get('status', '')
        
        # Build query (similar to list endpoint)
        query = Vendor.query
        
        if search:
            query = query.filter(
                (Vendor.company_name.ilike(f'%{search}%')) |
                (Vendor.contact_person.ilike(f'%{search}%')) |
                (Vendor.email.ilike(f'%{search}%'))
            )
        
        if category:
            query = query.filter(Vendor.vendor_category == category)
        
        if status:
            query = query.filter(Vendor.status == status)
        
        vendors = query.all()
        
        if format_type == 'excel':
            # TODO: Implement Excel export
            return jsonify({
                'success': False,
                'error': 'Export Excel belum diimplementasi'
            }), 501
        elif format_type == 'pdf':
            # TODO: Implement PDF export
            return jsonify({
                'success': False,
                'error': 'Export PDF belum diimplementasi'
            }), 501
        else:
            return jsonify({
                'success': False,
                'error': 'Format export tidak didukung'
            }), 400
            
    except Exception as e:
        logger.error(f"Error exporting vendors: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Gagal mengekspor vendor: {str(e)}'
        }), 500

@vendor_crud_bp.route("/<int:vendor_id>/status", methods=["PUT"])
@jwt_required_allow_options
def update_vendor_status(vendor_id):
    """Update vendor status"""
    try:
        data = request.get_json()
        status = data.get('status', '')
        
        if not status:
            return jsonify({
                'success': False,
                'error': 'Status tidak boleh kosong'
            }), 400
        
        vendor = Vendor.query.get_or_404(vendor_id)
        vendor.status = status
        vendor.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Status vendor berhasil diubah'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating vendor status: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Gagal mengubah status vendor: {str(e)}'
        }), 500

@vendor_crud_bp.route("/<int:vendor_id>/documents/zip", methods=["GET"])
@jwt_required_allow_options
def download_vendor_documents(vendor_id):
    """Download all vendor documents as ZIP"""
    try:
        vendor = Vendor.query.get_or_404(vendor_id)
        
        # TODO: Implement ZIP creation and download
        # This would require creating a ZIP file with all vendor documents
        return jsonify({
            'success': False,
            'error': 'Download dokumen belum diimplementasi'
        }), 501
        
    except Exception as e:
        logger.error(f"Error downloading vendor documents: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Gagal mendownload dokumen vendor: {str(e)}'
        }), 500

@vendor_crud_bp.route("/<int:vendor_id>/document/<document_type>", methods=["GET"])
@jwt_required_allow_options
def download_vendor_document(vendor_id, document_type):
    """Download specific vendor document"""
    try:
        vendor = Vendor.query.get_or_404(vendor_id)
        
        # Map document type to actual field name
        document_field_mapping = {
            'ktp_file': 'ktp_director_file_path',
            'akta_perusahaan_file': 'akta_perusahaan_file_path',
            'nib_file': 'nib_file_path',
            'npwp_file': 'npwp_file_path',
            'company_profile_file': 'company_profile_file_path',
            'surat_keagenan_file': 'surat_keagenan_file_path',
            'tkdn_file': 'tkdn_file_path',
            'surat_pernyataan_manufaktur_file': 'surat_pernyataan_manufaktur_file_path'
        }
        
        field_name = document_field_mapping.get(document_type)
        if not field_name:
            return jsonify({
                'success': False,
                'error': 'Tipe dokumen tidak valid'
            }), 400
        
        document_field = getattr(vendor, field_name, None)
        if not document_field:
            return jsonify({
                'success': False,
                'error': 'Dokumen tidak ditemukan'
            }), 404
        
        # Get file path from document field
        import os
        from flask import send_file
        
        file_path = document_field
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File tidak ditemukan di server'
            }), 404
        
        # Determine file extension and MIME type
        file_extension = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        mime_type = mime_types.get(file_extension, 'application/octet-stream')
        
        # Send file
        return send_file(
            file_path,
            as_attachment=False,  # For preview, don't force download
            mimetype=mime_type,
            download_name=os.path.basename(file_path)
        )
        
    except Exception as e:
        logger.error(f"Error downloading vendor document: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Gagal mendownload dokumen: {str(e)}'
        }), 500

# ===== VENDOR REGISTRATION =====

@vendor_crud_bp.route("/", methods=["POST"])
def register_vendor():
    """Register vendor baru"""
    try:
        vendor_data = request.get_json()
        
        # Validate required fields
        required_fields = ['company_name', 'contact_person', 'email']
        for field in required_fields:
            if field not in vendor_data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        service = VendorManagementService(db.session)
        result = service.register_vendor(vendor_data)
        
        return jsonify({
            'success': True,
            'message': 'Vendor berhasil diregistrasi',
            'data': result.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error registering vendor: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_crud_bp.route("/self-register", methods=["POST"])
def self_register_vendor():
    """Self registration untuk vendor"""
    try:
        vendor_data = request.get_json()
        
        # Validate required fields
        required_fields = ['company_name', 'contact_person', 'email', 'password']
        for field in required_fields:
            if field not in vendor_data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        # Validate password
        if len(vendor_data['password']) < 6:
            return jsonify({
                'success': False,
                'message': 'Password minimal 6 karakter'
            }), 400
        
        # Set default status untuk self-registration
        vendor_data['status'] = 'approved'  # Langsung aktif tanpa verifikasi
        
        service = VendorManagementService(db.session)
        result = service.register_vendor(vendor_data)
        
        # Create user account for vendor login
        auth_service = VendorAuthService(db.session)
        password = vendor_data['password']  # Store password before it's removed
        user_account = auth_service.create_vendor_user_account(result, password)
        
        return jsonify({
            'success': True,
            'message': 'Vendor berhasil diregistrasi dan user account dibuat',
            'data': {
                'vendor': result.to_dict(),
                'user_account': user_account.to_dict() if user_account else None
            }
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error in self-registration: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_crud_bp.route("/test-upload", methods=["POST"])
def test_upload():
    """Test endpoint untuk debug file upload"""
    try:
        logger.info("🔍 Test upload endpoint called")
        logger.info(f"🔍 Request method: {request.method}")
        logger.info(f"🔍 Request content type: {request.content_type}")
        logger.info(f"🔍 Request files keys: {list(request.files.keys())}")
        logger.info(f"🔍 Request form keys: {list(request.form.keys())}")
        logger.info(f"🔍 Request headers: {dict(request.headers)}")
        
        if request.files:
            for key, file in request.files.items():
                logger.info(f"📁 File {key}: {file.filename}, {file.content_type}, {file.content_length}")
        
        return jsonify({
            'success': True,
            'message': 'Test upload successful',
            'files_received': list(request.files.keys()),
            'form_data': dict(request.form)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Test upload error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_crud_bp.route("/<int:vendor_id>/upload-ktp", methods=["POST"])
@jwt_required_allow_options
def upload_ktp_file(vendor_id):
    """Upload KTP file untuk vendor"""
    try:
        logger.info(f"🔍 Starting KTP upload for vendor {vendor_id}")
        
        # Check if vendor exists
        vendor = db.session.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            logger.error(f"❌ Vendor {vendor_id} not found")
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Get form data
        ktp_data = {
            'ktp_director_name': request.form.get('ktp_director_name'),
            'ktp_director_number': request.form.get('ktp_director_number')
        }
        
        logger.info(f"📝 KTP data: {ktp_data}")
        
        # Debug request information
        logger.info(f"🔍 Request files keys: {list(request.files.keys())}")
        logger.info(f"🔍 Request form keys: {list(request.form.keys())}")
        logger.info(f"🔍 Request content type: {request.content_type}")
        logger.info(f"🔍 Request method: {request.method}")
        logger.info(f"🔍 Request headers: {dict(request.headers)}")
        logger.info(f"🔍 Request data length: {len(request.get_data())}")
        
        # Debug raw request data
        try:
            raw_data = request.get_data()
            logger.info(f"🔍 Raw request data (first 200 chars): {raw_data[:200]}")
        except Exception as e:
            logger.error(f"❌ Error getting raw data: {str(e)}")
        
        # Check if request has any files at all
        if not request.files:
            logger.error("❌ No files in request.files at all")
            return jsonify({
                'success': False,
                'message': 'Tidak ada file yang diterima'
            }), 400
        
        # Get file
        if 'ktp_file' not in request.files:
            logger.error("❌ No ktp_file in request.files")
            return jsonify({
                'success': False,
                'message': 'File KTP tidak ditemukan'
            }), 400
        
        file = request.files['ktp_file']
        if file.filename == '':
            logger.error("❌ Empty filename for ktp_file")
            return jsonify({
                'success': False,
                'message': 'File KTP tidak dipilih'
            }), 400
        
        logger.info(f"📁 File info: {file.filename}, {file.content_type}")
        
        service = VendorManagementService(db.session)
        result = service.upload_ktp_file(vendor_id, ktp_data, file)
        
        logger.info(f"✅ KTP upload successful for vendor {vendor_id}")
        return jsonify({
            'success': True,
            'message': 'KTP file berhasil diupload',
            'data': {
                'vendor_id': vendor_id,
                'ktp_director_name': ktp_data['ktp_director_name'],
                'ktp_director_number': ktp_data['ktp_director_number']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error uploading KTP file: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_crud_bp.route("/<int:vendor_id>/upload-attachments", methods=["POST"])
@jwt_required_allow_options
def upload_vendor_attachments(vendor_id):
    """Upload multiple attachment files untuk vendor"""
    try:
        logger.info(f"🔍 Starting attachment upload for vendor {vendor_id}")
        
        # Check if vendor exists
        vendor = db.session.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            logger.error(f"❌ Vendor {vendor_id} not found")
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Get attachment files from form data
        attachment_files = {}
        
        # Define attachment types and their form field names
        attachment_types = {
            'akta_perusahaan': 'akta_perusahaan_file',
            'nib': 'nib_file',
            'npwp': 'npwp_file',
            'company_profile': 'company_profile_file',
            'surat_keagenan': 'surat_keagenan_file',
            'tkdn': 'tkdn_file',
            'surat_pernyataan_manufaktur': 'surat_pernyataan_manufaktur_file'
        }
        
        logger.info(f"📁 Available files in request: {list(request.files.keys())}")
        logger.info(f"📝 Form data: {dict(request.form)}")
        logger.info(f"🔍 Request content type: {request.content_type}")
        logger.info(f"🔍 Request method: {request.method}")
        logger.info(f"🔍 Request headers: {dict(request.headers)}")
        logger.info(f"🔍 Request data length: {len(request.get_data())}")
        
        # Check if request has any files at all
        if not request.files:
            logger.error("❌ No files in request.files at all")
            return jsonify({
                'success': False,
                'message': 'Tidak ada file yang diterima'
            }), 400
        
        # Process each attachment type
        for attachment_type, form_field in attachment_types.items():
            if form_field in request.files:
                file = request.files[form_field]
                if file and file.filename:
                    logger.info(f"📄 Found {attachment_type}: {file.filename}, {file.content_type}")
                    attachment_files[attachment_type] = {
                        'file': file,
                        'form_field': form_field
                    }
                else:
                    logger.info(f"⚠️ {attachment_type} file is empty or no filename")
            else:
                logger.info(f"❌ {attachment_type} not found in request.files")
        
        if not attachment_files:
            logger.error("❌ No attachment files found")
            return jsonify({
                'success': False,
                'message': 'Tidak ada file attachment yang diupload'
            }), 400
        
        logger.info(f"📦 Processing {len(attachment_files)} attachment files")
        
        # Upload files using service
        service = VendorManagementService(db.session)
        result = service.upload_vendor_attachments(vendor_id, attachment_files)
        
        logger.info(f"✅ Attachment upload successful for vendor {vendor_id}")
        return jsonify({
            'success': True,
            'message': f'Berhasil upload {len(attachment_files)} file attachment',
            'data': {
                'vendor_id': vendor_id,
                'uploaded_files': list(attachment_files.keys()),
                'total_files': len(attachment_files)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error uploading attachment files: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== VENDOR LISTING & RETRIEVAL =====

@vendor_crud_bp.route("/", methods=["GET", "OPTIONS"])
@jwt_required_allow_options
def get_vendors():
    """Get all vendors dengan pagination dan filtering"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        search = request.args.get('search')
        
        service = VendorManagementService(db.session)
        result = service.get_vendors_paginated(
            page=page, 
            per_page=per_page, 
            status=status, 
            search=search
        )
        
        return jsonify({
            'success': True,
            'data': result['vendors'],
            'pagination': result['pagination']
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendors: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_crud_bp.route("/<int:vendor_id>", methods=["GET", "OPTIONS"])
@jwt_required_allow_options
def get_vendor(vendor_id):
    """Get vendor by ID"""
    try:
        service = VendorManagementService(db.session)
        vendor = service.get_vendor_by_id(vendor_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'data': vendor.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_crud_bp.route("/email/<string:email>", methods=["GET", "OPTIONS"])
@jwt_required_allow_options
def get_vendor_by_email(email):
    """Get vendor by email"""
    try:
        service = VendorManagementService(db.session)
        vendor = service.get_vendor_by_email(email)
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'data': vendor.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor by email {email}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== VENDOR UPDATE & STATUS MANAGEMENT =====

@vendor_crud_bp.route("/<int:vendor_id>", methods=["PUT", "OPTIONS"])
@jwt_required_allow_options
def update_vendor(vendor_id):
    """Update vendor information"""
    try:
        vendor_data = request.get_json()
        
        service = VendorManagementService(db.session)
        result = service.update_vendor(vendor_id, vendor_data)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Vendor berhasil diupdate',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_crud_bp.route("/<int:vendor_id>/approve", methods=["POST", "OPTIONS"])
@jwt_required_allow_options
def approve_vendor(vendor_id):
    """Approve vendor"""
    try:
        service = VendorManagementService(db.session)
        result = service.approve_vendor(vendor_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Vendor berhasil diapprove',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error approving vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_crud_bp.route("/<int:vendor_id>/reject", methods=["POST", "OPTIONS"])
@jwt_required_allow_options
def reject_vendor(vendor_id):
    """Reject vendor"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Tidak memenuhi kriteria')
        
        service = VendorManagementService(db.session)
        result = service.reject_vendor(vendor_id, reason)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Vendor berhasil direject',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error rejecting vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_crud_bp.route("/<int:vendor_id>/suspend", methods=["POST", "OPTIONS"])
@jwt_required_allow_options
def suspend_vendor(vendor_id):
    """Suspend vendor"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Pelanggaran kebijakan')
        
        service = VendorManagementService(db.session)
        result = service.suspend_vendor(vendor_id, reason)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Vendor berhasil disuspend',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error suspending vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== VENDOR CATEGORIES =====

@vendor_crud_bp.route("/<int:vendor_id>/categories", methods=["POST", "OPTIONS"])
@jwt_required_allow_options
def add_vendor_category(vendor_id):
    """Add category to vendor"""
    try:
        data = request.get_json()
        category_id = data.get('category_id')
        
        if not category_id:
            return jsonify({
                'success': False,
                'message': 'category_id is required'
            }), 400
        
        service = VendorManagementService(db.session)
        result = service.add_vendor_category(vendor_id, category_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Vendor atau kategori tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Kategori berhasil ditambahkan ke vendor',
            'data': result.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error adding category to vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_crud_bp.route("/<int:vendor_id>/categories/<int:category_id>", methods=["DELETE", "OPTIONS"])
@jwt_required_allow_options
def remove_vendor_category(vendor_id, category_id):
    """Remove category from vendor"""
    try:
        service = VendorManagementService(db.session)
        result = service.remove_vendor_category(vendor_id, category_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Vendor atau kategori tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Kategori berhasil dihapus dari vendor'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error removing category from vendor {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@vendor_crud_bp.route("/<int:vendor_id>/categories", methods=["GET", "OPTIONS"])
@jwt_required_allow_options
def get_vendor_categories(vendor_id):
    """Get vendor categories"""
    try:
        service = VendorManagementService(db.session)
        categories = service.get_vendor_categories(vendor_id)
        
        return jsonify({
            'success': True,
            'data': [cat.to_dict() for cat in categories]
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting vendor categories {vendor_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
