from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from domains.auth.models.auth_models import User
from domains.auth.services.jwt_service import JWTService
from config.database import db
from shared.middlewares.role_auth import block_vendor, require_admin
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/users', methods=['GET', 'OPTIONS'])
@jwt_required()
@block_vendor()
def get_users():
    """
    GET /api/users - Ambil semua users
    """
    # Handle OPTIONS request dengan CORS headers yang benar
    if request.method == 'OPTIONS':
        from flask import make_response
        response = make_response('', 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, x-api-key, X-API-Key, Cache-Control, Accept, Origin, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
    
    try:
        users = User.query.filter_by(is_active=True).all()
        users_data = [user.to_dict() for user in users]
        
        return jsonify({
            'success': True,
            'data': users_data,
            'count': len(users_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan saat mengambil data users'
        }), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Login endpoint dengan JWT token - Support untuk user biasa dan vendor
    """
    try:
        # Debug logging untuk melihat request yang masuk
        logger.info(f"🔍 Login request received from {request.remote_addr}")
        logger.info(f"🔍 Request method: {request.method}")
        logger.info(f"🔍 Content-Type: {request.content_type}")
        logger.info(f"🔍 Headers: {dict(request.headers)}")
        logger.info(f"🔍 Raw data: {request.get_data(as_text=True)}")
        
        data = request.get_json(force=True)  # Force JSON parsing
        
        logger.info(f"🔍 Parsed JSON data: {data}")
        
        if not data:
            logger.warning("❌ No data received in request")
            return jsonify({
                'success': False,
                'error': 'Data tidak boleh kosong'
            }), 400
        
        # Support both 'username' and 'email' fields untuk kompatibilitas
        username = data.get('username') or data.get('email')
        password = data.get('password')
        
        logger.info(f"🔍 Extracted username: {username}")
        logger.info(f"🔍 Extracted password length: {len(password) if password else 0}")
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username/Email dan password harus diisi'
            }), 400
        
        # Cari user di database - cek username atau email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            logger.warning(f"❌ Login failed: User {username} not found")
            return jsonify({
                'success': False,
                'error': 'Username atau password salah'
            }), 401
        
        # Verifikasi password
        if not check_password_hash(user.password_hash, password):
            logger.warning(f"❌ Login failed: Invalid password for user {username}")
            return jsonify({
                'success': False,
                'error': 'Username atau password salah'
            }), 401
        
        # Cek apakah user aktif
        if not user.is_active:
            logger.warning(f"❌ Login failed: Inactive user {username}")
            return jsonify({
                'success': False,
                'error': 'Akun tidak aktif'
            }), 401
        
        # Buat JWT tokens
        token_data = JWTService.create_tokens(
            user_id=str(user.id),  # Ensure user_id is string
            username=user.username,
            role=user.role
        )
        
        # Log token usage
        JWTService.log_token_usage(user.id, user.username, 'login')
        
        # Update last login
        user.last_login = db.func.now()
        db.session.commit()
        
        logger.info(f"✅ Login successful for user {username}")
        
        # Prepare response data
        response_data = {
            'success': True,
            'message': 'Login berhasil',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            },
            'access_token': token_data['access_token'],
            'refresh_token': token_data['refresh_token'],
            'expires_in': token_data['expires_in'],
            'token_type': token_data['token_type']
        }
        
        # Jika user adalah vendor, tambahkan informasi vendor
        if user.role == 'vendor' and user.vendor_id:
            try:
                from domains.vendor.models.vendor_models import Vendor
                vendor = Vendor.query.filter_by(id=user.vendor_id).first()
                if vendor:
                    response_data['vendor'] = vendor.to_dict()
                    response_data['tokens'] = {
                        'access_token': token_data['access_token'],
                        'refresh_token': token_data['refresh_token']
                    }
                    response_data['data'] = {
                        'user': response_data['user'],
                        'vendor': vendor.to_dict(),
                        'permissions': [
                            'upload_file',
                            'view_own_files',
                            'view_own_penawaran',
                            'update_profile',
                            'view_requests',
                            'download_templates'
                        ]
                    }
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch vendor info: {str(e)}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error(f"❌ Error details: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Terjadi kesalahan saat login: {str(e)}'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token menggunakan refresh token
    """
    try:
        # Get current user info
        current_user_info = JWTService.get_current_user_info()
        
        if not current_user_info:
            return jsonify({
                'success': False,
                'error': 'Token tidak valid'
            }), 401
        
        # Refresh access token
        token_data = JWTService.refresh_access_token()
        
        # Log token usage
        JWTService.log_token_usage(
            current_user_info['user_id'],
            current_user_info['username'],
            'refresh'
        )
        
        logger.info(f"🔄 Token refreshed for user {current_user_info['username']}")
        
        return jsonify({
            'success': True,
            'message': 'Token berhasil di-refresh',
            'access_token': token_data['access_token'],
            'expires_in': token_data['expires_in'],
            'token_type': token_data['token_type']
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Token refresh error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Gagal refresh token'
        }), 500

@auth_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout endpoint
    """
    try:
        # Get current user info
        current_user_info = JWTService.get_current_user_info()
        
        if current_user_info:
            # Log token usage
            JWTService.log_token_usage(
                current_user_info['user_id'],
                current_user_info['username'],
                'logout'
            )
            
            logger.info(f"🔓 Logout successful for user {current_user_info['username']}")
        
        # Create logout response
        response = JWTService.create_logout_response()
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Logout error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan saat logout'
        }), 500

@auth_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get current user profile
    """
    try:
        # Get current user info dari token
        current_user_info = JWTService.get_current_user_info()
        
        if not current_user_info:
            return jsonify({
                'success': False,
                'error': 'Token tidak valid'
            }), 401
        
        # Get user data dari database
        user = db.session.get(User, current_user_info['user_id'])
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get profile error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan saat mengambil profil'
        }), 500

@auth_bp.route('/auth/validate', methods=['GET'])
@jwt_required()
def validate_token():
    """
    Validate current token
    """
    try:
        # Get current user info
        current_user_info = JWTService.get_current_user_info()
        
        if not current_user_info:
            return jsonify({
                'success': False,
                'error': 'Token tidak valid'
            }), 401
        
        return jsonify({
            'success': True,
            'message': 'Token valid',
            'user': current_user_info
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Token validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Token tidak valid'
        }), 401

@auth_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user info - endpoint untuk frontend compatibility
    """
    try:
        # Get current user info dari token
        current_user_info = JWTService.get_current_user_info()
        
        if not current_user_info:
            return jsonify({
                'success': False,
                'error': 'Token tidak valid'
            }), 401
        
        # Get user data dari database
        user = db.session.get(User, current_user_info['user_id'])
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User tidak ditemukan'
            }), 404
        
        # Return user data sesuai format yang diharapkan frontend
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get current user error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan saat mengambil data user'
        }), 500

@auth_bp.route('/auth/users/validate', methods=['GET'])
@jwt_required()
def validate_user_token():
    """
    Validate current user token - endpoint untuk frontend compatibility
    """
    try:
        # Get current user info
        current_user_info = JWTService.get_current_user_info()
        
        if not current_user_info:
            return jsonify({
                'success': False,
                'error': 'Token tidak valid'
            }), 401
        
        return jsonify({
            'success': True,
            'message': 'Token valid',
            'user': current_user_info
        }), 200
        
    except Exception as e:
        logger.error(f"❌ User token validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Token tidak valid'
        }), 401
