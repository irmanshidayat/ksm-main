from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt, decode_token
from models import User
from config.database import db
import logging

logger = logging.getLogger(__name__)

def jwt_required_custom(fn):
    """
    Custom JWT decorator yang menangani error dengan lebih baik
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            # Get Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                logger.warning("❌ No Authorization header found")
                return jsonify({
                    'success': False,
                    'error': 'Authorization header tidak ditemukan'
                }), 401
            
            # Check if header starts with 'Bearer '
            if not auth_header.startswith('Bearer '):
                logger.warning("❌ Invalid Authorization header format")
                return jsonify({
                    'success': False,
                    'error': 'Format Authorization header tidak valid'
                }), 401
            
            # Extract token
            token = auth_header.split(' ')[1]
            if not token:
                logger.warning("❌ Empty token after Bearer")
                return jsonify({
                    'success': False,
                    'error': 'Token kosong'
                }), 401
            
            # Verify JWT token
            try:
                verify_jwt_in_request()
            except Exception as jwt_error:
                logger.error(f"❌ JWT verification failed: {str(jwt_error)}")
                return jsonify({
                    'success': False,
                    'error': 'Token tidak valid atau expired'
                }), 401
            
            # Get current user
            current_user_id = get_jwt_identity()
            if not current_user_id:
                logger.warning("❌ No user identity found in token")
                return jsonify({
                    'success': False,
                    'error': 'Token tidak valid'
                }), 401
            
            # Get user from database
            try:
                user_id = int(current_user_id)
                user = db.session.get(User, user_id)
            except (ValueError, TypeError):
                logger.warning(f"❌ Invalid user ID format: {current_user_id}")
                return jsonify({
                    'success': False,
                    'error': 'User ID tidak valid'
                }), 401
            
            if not user:
                logger.warning(f"❌ User {current_user_id} not found in database")
                return jsonify({
                    'success': False,
                    'error': 'User tidak ditemukan'
                }), 401
            
            if not user.is_active:
                logger.warning(f"❌ User {current_user_id} is not active")
                return jsonify({
                    'success': False,
                    'error': 'User tidak aktif'
                }), 401
            
            # Add user to request context
            request.current_user = user
            request.current_user_id = user_id
            
            return fn(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"❌ JWT verification error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Token tidak valid atau expired'
            }), 401
    
    return wrapper

def admin_required(fn):
    """
    Decorator untuk endpoint yang memerlukan role admin
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            # Verify JWT token
            verify_jwt_in_request()
            
            # Get current user
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return jsonify({
                    'success': False,
                    'error': 'Token tidak valid'
                }), 401
            
            # Get user from database
            try:
                user_id = int(current_user_id)
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'User ID tidak valid'
                }), 401
            user = db.session.get(User, user_id)
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User tidak ditemukan'
                }), 401
            
            if not user.is_active:
                return jsonify({
                    'success': False,
                    'error': 'User tidak aktif'
                }), 401
            
            # Check if user is admin
            if user.role != 'admin':
                return jsonify({
                    'success': False,
                    'error': 'Akses ditolak - Admin required'
                }), 403
            
            # Add user to request context
            request.current_user = user
            request.current_user_id = user_id
            
            return fn(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"❌ Admin verification error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Token tidak valid atau expired'
            }), 401
    
    return wrapper

def optional_jwt(fn):
    """
    Decorator untuk endpoint yang bisa diakses tanpa JWT (optional)
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            # Get Authorization header
            auth_header = request.headers.get('Authorization')
            
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                if token:
                    try:
                        verify_jwt_in_request()
                        current_user_id = get_jwt_identity()
                        if current_user_id:
                            user = db.session.get(User, current_user_id)
                            if user and user.is_active:
                                request.current_user = user
                                request.current_user_id = current_user_id
                    except:
                        # Token invalid, tapi tidak error karena optional
                        pass
            
            return fn(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"❌ Optional JWT error: {str(e)}")
            return fn(*args, **kwargs)
    
    return wrapper

# Alias untuk backward compatibility
require_auth = jwt_required_custom
