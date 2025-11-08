#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Controller - API endpoints untuk email functionality
"""

import logging
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.email_service import EmailService
from config.database import db
from models.request_pembelian_models import Vendor, VendorPenawaran, VendorPenawaranItem
from models.email_attachment_model import EmailAttachment

logger = logging.getLogger(__name__)

# Create blueprint
email_bp = Blueprint('email', __name__)

# Initialize email service
email_service = EmailService()

@email_bp.route('/send-vendor-email', methods=['POST', 'OPTIONS'])
@jwt_required()
def send_vendor_email():
    """Send email to vendor with custom message"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['vendor_email', 'vendor_name', 'items']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        vendor_email = data['vendor_email']
        vendor_name = data['vendor_name']
        items = data['items']
        custom_message = data.get('custom_message', '')
        subject = data.get('subject', f'Permintaan Penawaran - {vendor_name}')
        cc_emails = data.get('cc_emails', [])
        bcc_emails = data.get('bcc_emails', [])
        
        # Debug: Log received data
        logger.info(f"📧 Email data received:")
        logger.info(f"  - To: {vendor_email}")
        logger.info(f"  - Subject: {subject}")
        logger.info(f"  - CC: {cc_emails}")
        logger.info(f"  - BCC: {bcc_emails}")
        logger.info(f"  - Items count: {len(items)}")
        
        # Validate items
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({
                'success': False,
                'message': 'Items must be a non-empty list'
            }), 400
        
        # Validate CC and BCC emails
        if not isinstance(cc_emails, list):
            return jsonify({
                'success': False,
                'message': 'CC emails must be a list'
            }), 400
        
        if not isinstance(bcc_emails, list):
            return jsonify({
                'success': False,
                'message': 'BCC emails must be a list'
            }), 400
        
        # Validate email format for CC and BCC
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        
        for email in cc_emails:
            if not re.match(email_pattern, email):
                return jsonify({
                    'success': False,
                    'message': f'Invalid CC email format: {email}'
                }), 400
        
        for email in bcc_emails:
            if not re.match(email_pattern, email):
                return jsonify({
                    'success': False,
                    'message': f'Invalid BCC email format: {email}'
                }), 400
        
        # Send email
        result = email_service.send_vendor_email(
            vendor_email=vendor_email,
            vendor_name=vendor_name,
            items=items,
            custom_message=custom_message,
            subject=subject,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails,
            user_id=get_jwt_identity(),  # Pass current user ID
            use_gmail_api=True  # Try Gmail API first
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Email berhasil dikirim',
                'data': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message'],
                'data': result
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error in send_vendor_email: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@email_bp.route('/get-vendor-data/<int:vendor_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_vendor_data(vendor_id):
    """Get vendor data for email composition"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        # Get vendor data
        vendor = db.session.query(Vendor).filter(Vendor.id == vendor_id).first()
        
        if not vendor:
            return jsonify({
                'success': False,
                'message': 'Vendor tidak ditemukan'
            }), 404
        
        # Get vendor items through VendorPenawaran relationship
        items = db.session.query(VendorPenawaranItem).join(
            VendorPenawaran, VendorPenawaranItem.vendor_penawaran_id == VendorPenawaran.id
        ).filter(VendorPenawaran.vendor_id == vendor_id).all()
        
        # Format items data
        items_data = []
        for item in items:
            items_data.append({
                'id': item.id,
                'vendor_penawaran_id': item.vendor_penawaran_id,
                'request_item_id': item.request_item_id,
                'vendor_unit_price': float(item.vendor_unit_price) if item.vendor_unit_price else None,
                'vendor_total_price': float(item.vendor_total_price) if item.vendor_total_price else None,
                'vendor_quantity': item.vendor_quantity,
                'vendor_specifications': item.vendor_specifications,
                'vendor_notes': item.vendor_notes,
                'vendor_merk': item.vendor_merk,
                'kategori': item.kategori,
                'is_selected': item.is_selected,
                'selected_quantity': item.selected_quantity,
                'selected_by_user_id': item.selected_by_user_id,
                'selected_at': item.selected_at.isoformat() if item.selected_at else None,
                'selection_notes': item.selection_notes,
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'updated_at': item.updated_at.isoformat() if item.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'vendor': {
                    'id': vendor.id,
                    'company_name': vendor.company_name,
                    'contact_person': vendor.contact_person,
                    'email': vendor.email,
                    'phone': vendor.phone,
                    'address': vendor.address,
                    'business_license': vendor.business_license,
                    'tax_id': vendor.tax_id,
                    'bank_account': vendor.bank_account,
                    'vendor_category': vendor.vendor_category,
                    'custom_category': vendor.custom_category,
                    'vendor_type': vendor.vendor_type,
                    'business_model': vendor.business_model,
                    'status': vendor.status
                },
                'items': items_data
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_vendor_data: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@email_bp.route('/get-email-templates', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_email_templates():
    """Get available email templates"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        templates = email_service.get_email_templates()
        
        return jsonify({
            'success': True,
            'data': templates
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_email_templates: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@email_bp.route('/check-email-config', methods=['GET', 'OPTIONS'])
@jwt_required()
def check_email_config():
    """Check email configuration status"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        # Check SMTP configuration
        smtp_config = {
            'server': email_service.smtp_server,
            'port': email_service.smtp_port,
            'username': email_service.smtp_username,
            'password_configured': bool(email_service.smtp_password and email_service.smtp_password != 'your-app-password'),
            'from_email': email_service.from_email,
            'from_name': email_service.from_name
        }
        
        # Check if SMTP is properly configured
        smtp_configured = (
            smtp_config['username'] and 
            smtp_config['username'] != 'your-email@gmail.com' and
            smtp_config['password_configured']
        )
        
        # Check Gmail API configuration
        gmail_config = {
            'client_id': bool(email_service.gmail_oauth_service.client_id),
            'client_secret': bool(email_service.gmail_oauth_service.client_secret),
            'redirect_uri': bool(email_service.gmail_oauth_service.redirect_uri),
            'scopes': email_service.gmail_oauth_service.scopes
        }
        
        gmail_configured = (
            gmail_config['client_id'] and 
            gmail_config['client_secret'] and 
            gmail_config['redirect_uri']
        )
        
        return jsonify({
            'success': True,
            'data': {
                'smtp': {
                    'configured': smtp_configured,
                    'config': smtp_config
                },
                'gmail_api': {
                    'configured': gmail_configured,
                    'config': gmail_config
                },
                'overall_status': 'configured' if (smtp_configured or gmail_configured) else 'not_configured',
                'recommendations': {
                    'smtp': 'Configure SMTP credentials in .env file' if not smtp_configured else None,
                    'gmail_api': 'Connect Gmail account via OAuth' if not gmail_configured else None
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in check_email_config: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@email_bp.route('/preview-email', methods=['POST', 'OPTIONS'])
@jwt_required()
def preview_email():
    """Preview email content before sending"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['vendor_name', 'items']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        vendor_name = data['vendor_name']
        items = data['items']
        custom_message = data.get('custom_message', '')
        subject = data.get('subject', f'Permintaan Penawaran - {vendor_name}')
        
        # Generate preview content
        html_content = email_service._generate_email_template(
            vendor_name, items, custom_message, subject
        )
        text_content = email_service._generate_text_template(
            vendor_name, items, custom_message, subject
        )
        
        return jsonify({
            'success': True,
            'data': {
                'html_content': html_content,
                'text_content': text_content
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in preview_email: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@email_bp.route('/upload-attachment', methods=['POST', 'OPTIONS'])
@jwt_required()
def upload_attachment():
    """Upload file attachment for email"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        # Debug logging
        logger.info(f"🔍 Upload attachment request received")
        logger.info(f"🔍 Request method: {request.method}")
        logger.info(f"🔍 Request content type: {request.content_type}")
        logger.info(f"🔍 Request files: {list(request.files.keys())}")
        logger.info(f"🔍 Request form: {dict(request.form)}")
        logger.info(f"🔍 Request headers: {dict(request.headers)}")
        
        # Check if file is present
        if 'file' not in request.files:
            logger.error("❌ No 'file' key in request.files")
            return jsonify({
                'success': False,
                'message': 'Tidak ada file yang diupload'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Tidak ada file yang dipilih'
            }), 400
        
        # Get additional data
        request_pembelian_id = request.form.get('request_pembelian_id', type=int)
        email_subject = request.form.get('email_subject', '')
        email_recipient = request.form.get('email_recipient', '')
        
        # Validate file
        if not EmailAttachment.is_allowed_file_type(file.filename):
            allowed_exts = ', '.join(EmailAttachment.get_allowed_extensions())
            return jsonify({
                'success': False,
                'message': f'Tipe file tidak diizinkan. File yang diizinkan: {allowed_exts}'
            }), 400
        
        # Get file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if not EmailAttachment.is_file_size_valid(file_size):
            max_size = EmailAttachment.get_max_file_size_mb()
            return jsonify({
                'success': False,
                'message': f'Ukuran file terlalu besar. Maksimal {max_size}MB'
            }), 400
        
        # Generate secure filename
        original_filename = secure_filename(file.filename)
        file_extension = os.path.splitext(original_filename)[1].lower()
        stored_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Create upload directory
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'email-attachments')
        year_month = datetime.now().strftime('%Y/%m')
        full_upload_dir = os.path.join(upload_dir, year_month)
        
        os.makedirs(full_upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(full_upload_dir, stored_filename)
        file.save(file_path)
        
        # Get MIME type
        import mimetypes
        mime_type, _ = mimetypes.guess_type(original_filename)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Save to database
        attachment = EmailAttachment(
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            file_extension=file_extension,
            request_pembelian_id=request_pembelian_id,
            uploaded_by_user_id=get_jwt_identity(),
            email_subject=email_subject,
            email_recipient=email_recipient
        )
        
        db.session.add(attachment)
        db.session.commit()
        
        logger.info(f"📎 File uploaded successfully: {original_filename} ({file_size} bytes)")
        
        return jsonify({
            'success': True,
            'message': 'File berhasil diupload',
            'data': attachment.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in upload_attachment: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@email_bp.route('/delete-attachment/<int:attachment_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def delete_attachment(attachment_id):
    """Delete file attachment"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        # Get attachment
        attachment = db.session.query(EmailAttachment).filter(
            EmailAttachment.id == attachment_id,
            EmailAttachment.uploaded_by_user_id == get_jwt_identity()
        ).first()
        
        if not attachment:
            return jsonify({
                'success': False,
                'message': 'File attachment tidak ditemukan'
            }), 404
        
        # Delete physical file
        try:
            if os.path.exists(attachment.file_path):
                os.remove(attachment.file_path)
                logger.info(f"🗑️ Physical file deleted: {attachment.file_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not delete physical file: {str(e)}")
        
        # Mark as deleted in database
        attachment.status = 'deleted'
        attachment.deleted_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"🗑️ Attachment deleted from database: {attachment.original_filename}")
        
        return jsonify({
            'success': True,
            'message': 'File attachment berhasil dihapus'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in delete_attachment: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@email_bp.route('/get-attachments', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_attachments():
    """Get user's file attachments"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        # Get query parameters
        request_pembelian_id = request.args.get('request_pembelian_id', type=int)
        status = request.args.get('status', 'active')
        
        # Build query
        query = db.session.query(EmailAttachment).filter(
            EmailAttachment.uploaded_by_user_id == get_jwt_identity(),
            EmailAttachment.status == status
        )
        
        if request_pembelian_id:
            query = query.filter(EmailAttachment.request_pembelian_id == request_pembelian_id)
        
        attachments = query.order_by(EmailAttachment.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [attachment.to_dict() for attachment in attachments]
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_attachments: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@email_bp.route('/download-attachment/<int:attachment_id>', methods=['GET'])
@jwt_required()
def download_attachment(attachment_id):
    """Download attachment file"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get attachment
        attachment = db.session.query(EmailAttachment).filter(
            EmailAttachment.id == attachment_id,
            EmailAttachment.status == 'active'
        ).first()
        
        if not attachment:
            return jsonify({
                'success': False,
                'message': 'Attachment tidak ditemukan'
            }), 404
        
        # Check if user has permission (uploaded by user or admin)
        # For now, allow if uploaded by current user or if attachment is linked to request pembelian
        # You can add more permission checks here
        has_permission = (
            attachment.uploaded_by_user_id == current_user_id or
            attachment.request_pembelian_id is not None
        )
        
        if not has_permission:
            return jsonify({
                'success': False,
                'message': 'Anda tidak memiliki akses untuk mengunduh file ini'
            }), 403
        
        # Check if file exists
        if not os.path.exists(attachment.file_path):
            logger.error(f"❌ File not found: {attachment.file_path}")
            return jsonify({
                'success': False,
                'message': 'File tidak ditemukan di server'
            }), 404
        
        # Send file
        return send_file(
            attachment.file_path,
            as_attachment=True,
            download_name=attachment.original_filename,
            mimetype=attachment.mime_type
        )
        
    except Exception as e:
        logger.error(f"❌ Error downloading attachment {attachment_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@email_bp.route('/send-vendor-email-with-attachments', methods=['POST', 'OPTIONS'])
@jwt_required()
def send_vendor_email_with_attachments():
    """Send email to vendor with attachments"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['vendor_email', 'vendor_name', 'items']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        vendor_email = data['vendor_email']
        vendor_name = data['vendor_name']
        items = data['items']
        custom_message = data.get('custom_message', '')
        subject = data.get('subject', f'Permintaan Penawaran - {vendor_name}')
        cc_emails = data.get('cc_emails', [])
        bcc_emails = data.get('bcc_emails', [])
        attachment_ids = data.get('attachment_ids', [])
        
        # Validate items
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({
                'success': False,
                'message': 'Items must be a non-empty list'
            }), 400
        
        # Get attachments
        attachments = []
        if attachment_ids:
            attachments = db.session.query(EmailAttachment).filter(
                EmailAttachment.id.in_(attachment_ids),
                EmailAttachment.uploaded_by_user_id == get_jwt_identity(),
                EmailAttachment.status == 'active'
            ).all()
            
            # Verify all files exist
            for attachment in attachments:
                if not os.path.exists(attachment.file_path):
                    return jsonify({
                        'success': False,
                        'message': f'File attachment tidak ditemukan: {attachment.original_filename}'
                    }), 400
        
        # Send email with attachments
        result = email_service.send_vendor_email_with_attachments(
            vendor_email=vendor_email,
            vendor_name=vendor_name,
            items=items,
            custom_message=custom_message,
            subject=subject,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails,
            attachments=attachments,
            user_id=get_jwt_identity(),
            use_gmail_api=True
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Email dengan attachment berhasil dikirim',
                'data': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message'],
                'data': result
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error in send_vendor_email_with_attachments: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500
