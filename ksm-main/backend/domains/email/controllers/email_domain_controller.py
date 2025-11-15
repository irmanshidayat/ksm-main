#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Domain Controller - API endpoints untuk email domain functionality
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from domains.email.services.email_domain_service import EmailDomainService
from domains.email.models.email_models import UserEmailDomain
from config.database import db

logger = logging.getLogger(__name__)

# Create blueprint
email_domain_bp = Blueprint('email_domain', __name__)

# Initialize email domain service
email_domain_service = EmailDomainService()

@email_domain_bp.route('/api/email-domain/config', methods=['GET', 'POST', 'PUT', 'DELETE'])
@email_domain_bp.route('/api/email-domain/config/<int:domain_id>', methods=['DELETE'])
@jwt_required()
def manage_domain_config(domain_id=None):
    """Manage konfigurasi email domain"""
    try:
        user_id = get_jwt_identity()
        
        if request.method == 'GET':
            # Ambil semua konfigurasi domain user
            result = email_domain_service.get_user_domains(user_id)
            return jsonify(result), 200 if result['success'] else 400
        
        elif request.method == 'POST':
            # Buat konfigurasi domain baru
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Data konfigurasi tidak ditemukan'
                }), 400
            
            result = email_domain_service.create_domain_config(user_id, data)
            return jsonify(result), 201 if result['success'] else 400
        
        elif request.method == 'PUT':
            # Update konfigurasi domain
            data = request.get_json()
            domain_id = data.get('id')
            
            if not domain_id:
                return jsonify({
                    'success': False,
                    'message': 'Domain ID tidak ditemukan'
                }), 400
            
            # Ambil domain yang akan diupdate
            domain = UserEmailDomain.query.filter_by(
                id=domain_id,
                user_id=user_id,
                is_active=True
            ).first()
            
            if not domain:
                return jsonify({
                    'success': False,
                    'message': 'Domain tidak ditemukan atau tidak aktif'
                }), 404
            
            # Update fields
            if 'domain_name' in data:
                domain.domain_name = data['domain_name']
            if 'smtp_server' in data:
                domain.smtp_server = data['smtp_server']
            if 'smtp_port' in data:
                domain.smtp_port = int(data['smtp_port'])
            if 'username' in data:
                domain.username = data['username']
            if 'from_name' in data:
                domain.from_name = data['from_name']
            # Update password hanya jika ada dan tidak kosong
            if 'password' in data and data['password'] and data['password'].strip():
                domain.set_password(data['password'])
            if 'is_default' in data:
                if data['is_default']:
                    # Set semua domain user menjadi non-default
                    UserEmailDomain.query.filter_by(user_id=user_id).update({'is_default': False})
                domain.is_default = data['is_default']
            
            db.session.commit()
            
            logger.info(f"✅ Domain config updated for user {user_id}: {domain.domain_name}")
            
            return jsonify({
                'success': True,
                'message': 'Konfigurasi domain berhasil diupdate',
                'data': domain.to_dict()
            }), 200
        
        elif request.method == 'DELETE':
            # Hapus konfigurasi domain
            # Support both URL parameter and body parameter
            if domain_id:
                # ID dari URL parameter
                target_domain_id = domain_id
            else:
                # ID dari body JSON
                data = request.get_json()
                target_domain_id = data.get('id') if data else None
            
            if not target_domain_id:
                return jsonify({
                    'success': False,
                    'message': 'Domain ID tidak ditemukan'
                }), 400
            
            result = email_domain_service.delete_domain_config(user_id, target_domain_id)
            return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"❌ Error in manage_domain_config: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@email_domain_bp.route('/api/email-domain/test', methods=['POST'])
@jwt_required()
def test_domain_connection():
    """Test koneksi domain"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data konfigurasi tidak ditemukan'
            }), 400
        
        # Jika ada domain_id, test konfigurasi yang sudah ada
        if 'domain_id' in data:
            domain = UserEmailDomain.query.filter_by(
                id=data['domain_id'],
                user_id=user_id,
                is_active=True
            ).first()
            
            if not domain:
                return jsonify({
                    'success': False,
                    'message': 'Domain tidak ditemukan atau tidak aktif'
                }), 404
            
            result = email_domain_service.test_domain_connection(domain)
            return jsonify(result), 200 if result['success'] else 400
        
        # Jika tidak ada domain_id, test konfigurasi baru
        else:
            # Buat temporary domain object untuk testing
            temp_domain = UserEmailDomain(
                user_id=user_id,
                domain_name=data.get('domain_name', ''),
                smtp_server=data.get('smtp_server', ''),
                smtp_port=int(data.get('smtp_port', 587)),
                username=data.get('username', ''),
                from_name=data.get('from_name', ''),
                is_active=True
            )
            
            # Set password untuk testing
            if 'password' in data:
                temp_domain.set_password(data['password'])
            
            result = email_domain_service.test_domain_connection(temp_domain)
            return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"❌ Error in test_domain_connection: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan saat testing: {str(e)}'
        }), 500

@email_domain_bp.route('/api/email-domain/send', methods=['POST'])
@jwt_required()
def send_via_domain():
    """Kirim email via domain"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Force print untuk debugging (akan muncul di console)
        print(f"📧 [EMAIL DOMAIN SEND] Received request from user {user_id}")
        print(f"📧 [EMAIL DOMAIN SEND] Request data: {data}")
        print(f"📧 [EMAIL DOMAIN SEND] Request data keys: {list(data.keys()) if data else 'None'}")
        
        logger.info(f"📧 Received email send request from user {user_id}")
        logger.info(f"📧 Request data keys: {list(data.keys()) if data else 'None'}")
        
        if not data:
            error_msg = "❌ No data received in request"
            print(error_msg)
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'message': 'Data email tidak ditemukan'
            }), 400
        
        # Validasi required fields
        required_fields = ['domain_id', 'vendor_email', 'vendor_name', 'items']
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
                warning_msg = f"⚠️ Missing required field: {field}"
                print(warning_msg)
                logger.warning(warning_msg)
        
        if missing_fields:
            error_msg = f"❌ Missing required fields: {missing_fields}"
            print(error_msg)
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'message': f'Field berikut wajib diisi: {", ".join(missing_fields)}',
                'missing_fields': missing_fields
            }), 400
        
        # Validasi items
        if not isinstance(data['items'], list) or len(data['items']) == 0:
            error_msg = "❌ Items must be a non-empty list"
            print(error_msg)
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'message': 'Items harus berupa array yang tidak kosong'
            }), 400
        
        success_msg = f"✅ All required fields present. Domain ID: {data['domain_id']}, Items count: {len(data['items'])}"
        print(success_msg)
        logger.info(success_msg)
        
        result = email_domain_service.send_email_via_domain(
            user_id,
            data['domain_id'],
            data
        )
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"❌ Error in send_via_domain: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan saat mengirim email: {str(e)}'
        }), 500

@email_domain_bp.route('/api/email-domain/set-default', methods=['POST'])
@jwt_required()
def set_default_domain():
    """Set domain sebagai default"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'domain_id' not in data:
            return jsonify({
                'success': False,
                'message': 'Domain ID tidak ditemukan'
            }), 400
        
        result = email_domain_service.set_default_domain(user_id, data['domain_id'])
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"❌ Error in set_default_domain: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@email_domain_bp.route('/api/email-domain/validate', methods=['POST'])
@jwt_required()
def validate_domain_config():
    """Validasi konfigurasi domain"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data konfigurasi tidak ditemukan'
            }), 400
        
        # Buat temporary domain object untuk validasi
        temp_domain = UserEmailDomain(
            user_id=0,  # Temporary
            domain_name=data.get('domain_name', ''),
            smtp_server=data.get('smtp_server', ''),
            smtp_port=int(data.get('smtp_port', 587)),
            username=data.get('username', ''),
            from_name=data.get('from_name', ''),
            is_active=True
        )
        
        validation = temp_domain.validate_config()
        
        return jsonify({
            'success': validation['valid'],
            'message': 'Konfigurasi valid' if validation['valid'] else 'Konfigurasi tidak valid',
            'errors': validation['errors']
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in validate_domain_config: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan saat validasi: {str(e)}'
        }), 500

@email_domain_bp.route('/api/email-domain/templates', methods=['GET'])
@jwt_required()
def get_email_templates():
    """Get available email templates"""
    try:
        templates = [
            {
                'id': 'default',
                'name': 'Template Default',
                'description': 'Template standar untuk permintaan penawaran',
                'subject_template': 'Permintaan Penawaran - {vendor_name}',
                'message_template': 'Kepada Yth. {vendor_name},\n\nKami ingin meminta penawaran untuk barang-barang berikut:\n\nMohon kirimkan penawaran harga untuk barang-barang di atas sesuai dengan spesifikasi yang diminta.\n\nTerima kasih atas perhatiannya.'
            },
            {
                'id': 'urgent',
                'name': 'Template Urgent',
                'description': 'Template untuk permintaan mendesak',
                'subject_template': 'URGENT - Permintaan Penawaran - {vendor_name}',
                'message_template': 'Kepada Yth. {vendor_name},\n\nKami membutuhkan penawaran URGENT untuk barang-barang berikut:\n\nMohon kirimkan penawaran harga secepatnya untuk barang-barang di atas.\n\nTerima kasih atas kerjasamanya.'
            },
            {
                'id': 'follow_up',
                'name': 'Template Follow Up',
                'description': 'Template untuk follow up penawaran',
                'subject_template': 'Follow Up - Permintaan Penawaran - {vendor_name}',
                'message_template': 'Kepada Yth. {vendor_name},\n\nKami ingin melakukan follow up untuk permintaan penawaran sebelumnya:\n\nMohon konfirmasi status penawaran untuk barang-barang di atas.\n\nTerima kasih.'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': templates
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_email_templates: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500
