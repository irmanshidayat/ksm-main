#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Auth Controller - API endpoints untuk Gmail OAuth authentication
"""

import logging
import os
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.gmail_oauth_service import GmailOAuthService
from config.database import db
from models.knowledge_base import User

logger = logging.getLogger(__name__)

# Create blueprint
gmail_auth_bp = Blueprint('gmail_auth', __name__)

# Initialize Gmail OAuth service
gmail_oauth_service = GmailOAuthService()

@gmail_auth_bp.route('/connect', methods=['GET', 'OPTIONS'])
@jwt_required()
def connect_gmail():
    """Generate Gmail OAuth authorization URL"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        # Get current user
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User tidak ditemukan'
            }), 404
        
        # Check if Gmail already connected
        if user.gmail_connected:
            return jsonify({
                'success': True,
                'message': 'Gmail sudah terhubung',
                'connected': True,
                'user_email': user.email
            }), 200
        
        # Generate authorization URL
        result = gmail_oauth_service.get_authorization_url()
        
        if result['success']:
            return jsonify({
                'success': True,
                'authorization_url': result['authorization_url'],
                'state': result['state']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error in connect_gmail: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@gmail_auth_bp.route('/callback', methods=['POST', 'OPTIONS'])
@jwt_required()
def gmail_oauth_callback():
    """Handle Gmail OAuth callback"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        data = request.get_json()
        
        # Validate required fields
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'message': 'Authorization code is required'
            }), 400
        
        authorization_code = data['code']
        state = data.get('state', '')
        
        # Get current user
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User tidak ditemukan'
            }), 404
        
        # Handle OAuth callback
        result = gmail_oauth_service.handle_oauth_callback(authorization_code, state)
        
        if result['success']:
            # Save credentials to database
            credentials_saved = gmail_oauth_service.save_user_gmail_credentials(
                current_user_id, 
                result['credentials']
            )
            
            if credentials_saved:
                return jsonify({
                    'success': True,
                    'message': 'Gmail berhasil terhubung',
                    'user_info': result['user_info']
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Gagal menyimpan credentials Gmail'
                }), 500
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error in gmail_oauth_callback: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@gmail_auth_bp.route('/status', methods=['GET', 'OPTIONS'])
@jwt_required()
def gmail_status():
    """Get Gmail connection status"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        # Get current user
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'connected': user.gmail_connected,
            'user_email': user.email,
            'gmail_connected_at': user.gmail_token_expires_at.isoformat() if user.gmail_token_expires_at else None
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in gmail_status: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@gmail_auth_bp.route('/disconnect', methods=['POST', 'OPTIONS'])
@jwt_required()
def disconnect_gmail():
    """Disconnect Gmail from user account"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        # Get current user
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User tidak ditemukan'
            }), 404
        
        # Disconnect Gmail
        success = gmail_oauth_service.disconnect_gmail(current_user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Gmail berhasil diputuskan'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Gagal memutuskan Gmail'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error in disconnect_gmail: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@gmail_auth_bp.route('/test-config', methods=['GET', 'OPTIONS'])
def test_gmail_config():
    """Test Gmail OAuth configuration without authentication"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        # Get current configuration
        config = {
            'client_id': gmail_oauth_service.client_id,
            'redirect_uri': gmail_oauth_service.redirect_uri,
            'scopes': gmail_oauth_service.scopes,
            'env_redirect_uri': os.getenv('GMAIL_REDIRECT_URI'),
            'env_client_id': os.getenv('GMAIL_CLIENT_ID')
        }
        
        return jsonify({
            'success': True,
            'config': config,
            'message': 'Gmail OAuth configuration test (no auth required)'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in test_gmail_config: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@gmail_auth_bp.route('/test-auth-url', methods=['GET', 'OPTIONS'])
def test_auth_url():
    """Test Gmail OAuth authorization URL generation without authentication"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        # Generate authorization URL
        result = gmail_oauth_service.get_authorization_url()
        
        return jsonify({
            'success': True,
            'result': result,
            'message': 'Gmail OAuth authorization URL test (no auth required)'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in test_auth_url: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@gmail_auth_bp.route('/debug-config', methods=['GET', 'OPTIONS'])
@jwt_required()
def debug_gmail_config():
    """Debug Gmail OAuth configuration"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        # Get current configuration
        config = {
            'client_id': gmail_oauth_service.client_id,
            'redirect_uri': gmail_oauth_service.redirect_uri,
            'scopes': gmail_oauth_service.scopes,
            'env_redirect_uri': os.getenv('GMAIL_REDIRECT_URI'),
            'env_client_id': os.getenv('GMAIL_CLIENT_ID')
        }
        
        return jsonify({
            'success': True,
            'config': config,
            'message': 'Gmail OAuth configuration debug info'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in debug_gmail_config: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@gmail_auth_bp.route('/test-send', methods=['POST', 'OPTIONS'])
@jwt_required()
def test_gmail_send():
    """Test Gmail sending functionality"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200
        
        data = request.get_json()
        
        # Validate required fields
        if not data or 'to_email' not in data:
            return jsonify({
                'success': False,
                'message': 'to_email is required'
            }), 400
        
        to_email = data['to_email']
        subject = data.get('subject', 'Test Email dari KSM System')
        message = data.get('message', 'Ini adalah email test dari KSM Procurement System.')
        
        # Get current user
        current_user_id = get_jwt_identity()
        
        # Create test email content
        html_content = f"""
        <html>
        <body>
            <h2>Test Email dari KSM System</h2>
            <p>{message}</p>
            <p><strong>Dikirim dari:</strong> KSM Procurement System</p>
            <p><strong>Tanggal:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Test Email dari KSM System
        
        {message}
        
        Dikirim dari: KSM Procurement System
        Tanggal: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """
        
        # Send test email
        result = gmail_oauth_service.send_email_via_gmail_api(
            current_user_id,
            to_email,
            subject,
            html_content,
            text_content
        )
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"❌ Error in test_gmail_send: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500
