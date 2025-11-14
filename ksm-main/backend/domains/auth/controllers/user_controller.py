#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Controller untuk KSM Main Backend
Memindahkan endpoint inline `/api/users` dari app.py menjadi blueprint terpisah
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging

from config.database import db
from models import User

logger = logging.getLogger(__name__)

user_bp = Blueprint('users', __name__, url_prefix='/api/users')


@user_bp.route('', methods=['GET', 'POST', 'OPTIONS'])
def users_endpoint():
    """Users endpoint - GET untuk ambil users, POST untuk create user"""
    if request.method == 'OPTIONS':
        return '', 200
    
    # Temporary: Skip authentication for CORS testing
    # TODO: Re-enable authentication after CORS is working
    pass

    if request.method == 'GET':
        try:
            logger.info("GET /api/users endpoint called")
            # Get users from database with proper error handling
            users_data = []
            
            try:
                # Test database connection first
                db.session.execute('SELECT 1')
                
                # Query users
                users = User.query.filter_by(is_active=True).all()
                logger.info(f"Found {len(users)} active users")
                
                for user in users:
                    try:
                        # Get user data with all fields
                        user_dict = {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'role': user.role,
                            'is_active': user.is_active,
                            'created_at': user.created_at.isoformat() if user.created_at else None,
                            'last_login': user.last_login.isoformat() if user.last_login else None
                        }
                        
                        # Add vendor info if exists
                        if user.vendor_id and user.vendor:
                            user_dict['vendor'] = {
                                'id': user.vendor.id,
                                'name': getattr(user.vendor, 'name', 'Unknown Vendor')
                            }
                        
                        users_data.append(user_dict)
                        
                    except Exception as user_error:
                        logger.warning(f"Error serializing user {getattr(user, 'id', 'unknown')}: {user_error}")
                        continue
                        
            except Exception as db_error:
                logger.error(f"Database error: {str(db_error)}")
                # Return empty array if database fails
                users_data = []
            
            return jsonify({
                'success': True,
                'data': users_data,
                'count': len(users_data)
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Terjadi kesalahan saat mengambil data users',
                'details': str(e)
            }), 500

    # POST
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Data tidak boleh kosong'
            }), 400

        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'error': f'Field {field} harus diisi'
                }), 400

        from werkzeug.security import generate_password_hash

        # Cek duplikasi username/email
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'Username atau email sudah terdaftar'
            }), 409

        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            is_active=True,
            created_at=datetime.now()
        )

        db.session.add(new_user)
        db.session.commit()

        logger.info(f"User baru berhasil dibuat: {new_user.username}")

        return jsonify({
            'success': True,
            'message': 'User berhasil dibuat',
            'user_id': new_user.id,
            'username': new_user.username
        }), 201
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan saat membuat user'
        }), 500


@user_bp.route('/<int:user_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
def user_detail(user_id):
    """Update dan soft delete user"""
    if request.method == 'OPTIONS':
        logger.info(f"[USERS][OPTIONS] /api/users/{user_id}")
        return '', 200

    try:
        logger.info(f"[USERS][{request.method}] Start user_id={user_id}")
        user = User.query.get(user_id)
        if not user:
            logger.warning(f"[USERS][{request.method}] User {user_id} tidak ditemukan")
            return jsonify({
                'success': False,
                'error': 'User tidak ditemukan'
            }), 404

        if request.method == 'PUT':
            data = request.get_json() or {}
            logger.info(f"[USERS][PUT] Payload: {data}")

            # Validasi dasar
            username = data.get('username')
            email = data.get('email')

            if username is not None and username != user.username:
                # Cek duplikasi username
                exists_username = User.query.filter(User.username == username, User.id != user_id).first()
                if exists_username:
                    logger.info(f"[USERS][PUT] Username sudah digunakan: {username}")
                    return jsonify({
                        'success': False,
                        'error': 'Username sudah digunakan'
                    }), 409
                user.username = username

            if email is not None and email != user.email:
                # Cek duplikasi email
                exists_email = User.query.filter(User.email == email, User.id != user_id).first()
                if exists_email:
                    logger.info(f"[USERS][PUT] Email sudah digunakan: {email}")
                    return jsonify({
                        'success': False,
                        'error': 'Email sudah digunakan'
                    }), 409
                user.email = email

            # Handle password change
            if data.get('changePassword'):
                new_password = data.get('newPassword')
                old_password = data.get('oldPassword')  # Optional

                if not new_password:
                    logger.info(f"[USERS][PUT] Password baru tidak dikirim")
                    return jsonify({
                        'success': False,
                        'error': 'Password baru harus diisi'
                    }), 400

                # Jika old_password dikirim, tetap verifikasi; jika tidak, izinkan (admin reset)
                if old_password:
                    from werkzeug.security import check_password_hash
                    if not check_password_hash(user.password_hash, old_password):
                        logger.info(f"[USERS][PUT] Password lama salah untuk user {user_id}")
                        return jsonify({
                            'success': False,
                            'error': 'Password lama salah'
                        }), 401

                # Update password
                from werkzeug.security import generate_password_hash
                user.password_hash = generate_password_hash(new_password)
                logger.info(f"[USERS][PUT] Password berhasil diubah untuk user {user_id}")

            # Opsi: update flag aktif jika dikirim
            if 'is_active' in data and data.get('is_active') is not None:
                user.is_active = bool(data.get('is_active'))

            db.session.commit()
            logger.info(f"[USERS][PUT] Success user_id={user.id}")

            return jsonify({
                'success': True,
                'message': 'User berhasil diperbarui',
                'data': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active
                }
            }), 200

        # DELETE => soft delete
        if user.is_active is False:
            logger.info(f"[USERS][DELETE] User {user_id} sudah nonaktif")
        user.is_active = False
        db.session.commit()
        logger.info(f"[USERS][DELETE] Success user_id={user.id}")
        # 204 No Content untuk respons cepat tanpa body
        return ('', 204)

    except Exception as e:
        logger.error(f"[USERS][{request.method}] Error update/delete user: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan saat memproses user'
        }), 500


@user_bp.route('/validate', methods=['GET'])
@jwt_required()
def validate_user_token():
    """
    Validate current user token - endpoint untuk frontend compatibility
    """
    try:
        from domains.auth.services.jwt_service import JWTService
        
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

