#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Controller - Menangani pengaturan telegram bot dengan integrasi Agent AI
"""

from flask import Blueprint, request, jsonify
from models.knowledge_base import TelegramSettings, db
from datetime import datetime
import logging
import traceback
import requests
import os
from services.telegram_integration_service import telegram_integration, telegram_webhook
# telegram_rag_service removed - using Agent AI directly
from models.knowledge_base import TelegramSettings
from services.agent_ai_sync_service import agent_ai_sync
from middlewares.api_auth import jwt_required_custom
from middlewares.role_auth import block_vendor
from config.config import Config

logger = logging.getLogger(__name__)

class TelegramController:
    """Controller class untuk mengelola Telegram notifications"""
    
    def __init__(self):
        self.telegram_integration = telegram_integration
    
    def send_message_to_admin(self, message):
        """Kirim pesan ke admin melalui Telegram"""
        try:
            # Ambil pengaturan telegram dari database
            company_id = Config.DEFAULT_COMPANY_ID
            settings = TelegramSettings.query.filter_by(company_id=company_id).first()
            
            if not settings or not settings.is_active or not settings.bot_token:
                logger.warning("Telegram bot tidak aktif atau token tidak tersedia")
                return {
                    'success': False,
                    'message': 'Telegram bot tidak aktif atau token tidak tersedia. Silakan konfigurasi di halaman Telegram Bot Management.'
                }
            
            # Ambil admin chat ID dari settings
            admin_chat_id = settings.admin_chat_id if hasattr(settings, 'admin_chat_id') else None
            
            if not admin_chat_id:
                logger.warning("Admin chat ID tidak tersedia")
                return {
                    'success': False,
                    'message': 'Admin chat ID tidak tersedia. Silakan kirim pesan ke bot terlebih dahulu.'
                }
            
            # Kirim pesan ke Telegram menggunakan bot token
            bot_token = settings.bot_token
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                'chat_id': admin_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"Telegram notification sent successfully to chat_id: {admin_chat_id}")
                    return {
                        'success': True,
                        'message': 'Notification sent successfully',
                        'data': result
                    }
                else:
                    logger.error(f"Telegram API error: {result}")
                    return {
                        'success': False,
                        'message': f'Telegram API error: {result.get("description", "Unknown error")}'
                    }
            else:
                logger.error(f"Failed to send telegram notification: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'message': f'Failed to send notification: {response.status_code}'
                }
            
        except Exception as e:
            logger.error(f"Error sending telegram notification: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }

telegram_bp = Blueprint('telegram', __name__, url_prefix='/api/telegram')

@telegram_bp.route('/test', methods=['GET'])
def test_telegram():
    """Test endpoint untuk memastikan blueprint berfungsi"""
    logger.info("Testing telegram blueprint endpoint")
    return jsonify({
        'success': True,
        'message': 'Telegram blueprint berfungsi dengan baik',
        'timestamp': datetime.now().isoformat()
    }), 200

@telegram_bp.route('/status', methods=['GET', 'OPTIONS'])
def telegram_status():
    """Endpoint untuk status telegram bot"""
    
    logger.info(f"Telegram status endpoint called - Method: {request.method}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        logger.debug("Handling OPTIONS preflight for telegram status")
        return '', 200
    
    try:
        company_id = Config.DEFAULT_COMPANY_ID  # Default company ID from config
        logger.debug(f"Checking telegram status for company: {company_id}")
        
        # Cek apakah tabel telegram_settings ada
        try:
            logger.debug("Attempting to query TelegramSettings table")
            settings = TelegramSettings.query.filter_by(company_id=company_id).first()
            logger.debug(f"TelegramSettings query result: {settings}")
        except Exception as db_error:
            logger.error(f"Database error in telegram status: {str(db_error)}")
            logger.error(traceback.format_exc())
            # Jika tabel belum ada, return inactive status
            return jsonify({
                'success': True,
                'data': {
                    'status': 'inactive',
                    'bot_info': {'first_name': 'KSM Bot', 'username': 'KSM_bot'}
                },
                'message': 'Bot telegram tidak aktif - database belum siap',
                'debug_info': {
                    'error': str(db_error),
                    'error_type': type(db_error).__name__
                },
                'timestamp': datetime.now().isoformat()
            }), 200
        
        # Default bot info fallback
        default_bot_info = {'first_name': 'KSM Bot', 'username': 'KSM_bot'}
        
        if settings and settings.is_active and settings.bot_token:
            logger.info("Telegram bot is active")
            # Pastikan polling aktif jika tidak ada webhook HTTPS
            try:
                if not telegram_integration.webhook_url:
                    telegram_integration.bot_token = settings.bot_token
                    telegram_integration.ensure_polling_active()
            except Exception as _e:
                logger.debug(f"ensure_polling_active skipped: {_e}")
            
            # Ambil informasi bot real dari Telegram API
            bot_info = default_bot_info.copy()
            try:
                response = requests.get(f"https://api.telegram.org/bot{settings.bot_token}/getMe", timeout=5)
                if response.status_code == 200:
                    telegram_data = response.json()
                    if telegram_data.get('ok'):
                        result = telegram_data.get('result', {})
                        bot_info = {
                            'first_name': result.get('first_name', 'KSM Bot'),
                            'username': result.get('username', 'KSM_bot')
                        }
                        logger.debug(f"Got real bot info: {bot_info}")
                    else:
                        logger.warning(f"Telegram API returned error: {telegram_data}")
                else:
                    logger.warning(f"Failed to get bot info: {response.status_code}")
            except Exception as e:
                logger.warning(f"Error getting bot info: {e}")
            
            return jsonify({
                'success': True,
                'data': {
                    'status': 'active',
                    'bot_info': bot_info
                },
                'message': 'Bot telegram aktif',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            logger.info("Telegram bot is inactive")
            return jsonify({
                'success': True,
                'data': {
                    'status': 'inactive',
                    'bot_info': default_bot_info
                },
                'message': 'Bot telegram tidak aktif',
                'debug_info': {
                    'has_settings': settings is not None,
                    'is_active': settings.is_active if settings else False,
                    'has_token': bool(settings.bot_token) if settings else False
                },
                'timestamp': datetime.now().isoformat()
            }), 200
    
    except Exception as e:
        logger.error(f"Error in telegram status: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'data': {
                'status': 'error',
                'bot_info': {'first_name': 'KSM Bot', 'username': 'KSM_bot'}
            },
            'message': f'Terjadi kesalahan: {str(e)}',
            'debug_info': {
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
        }), 500

@telegram_bp.route('/start', methods=['POST', 'OPTIONS'])
@jwt_required_custom
def telegram_start():
    """Endpoint untuk memulai telegram bot"""
    
    logger.info(f"Telegram start endpoint called - Method: {request.method}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        logger.debug("Handling OPTIONS preflight for telegram start")
        return '', 200
    
    try:
        company_id = Config.DEFAULT_COMPANY_ID  # Default company ID from config
        logger.debug(f"Starting telegram bot for company: {company_id}")
        
        data = request.get_json()
        logger.debug(f"Request data: {data}")
        
        if not data:
            logger.warning("No data provided in request")
            return jsonify({
                'success': False,
                'message': 'Data tidak boleh kosong'
            }), 400
        
        bot_token = data.get('bot_token', '')
        if not bot_token or not bot_token.strip():
            logger.warning("Bot token tidak boleh kosong")
            return jsonify({
                'success': False,
                'message': 'Bot token tidak boleh kosong'
            }), 400
        
        # Validasi format bot token (format: 123456789:ABCdefGhIjKlmNoPqRsTuVwXyZ)
        bot_token = bot_token.strip()
        if ':' not in bot_token or len(bot_token.split(':')) != 2:
            logger.warning("Format bot token tidak valid - harus mengandung :")
            return jsonify({
                'success': False,
                'message': 'Format bot token tidak valid. Bot token harus dalam format: 123456789:ABCdefGhIjKlmNoPqRsTuVwXyZ'
            }), 400
        
        bot_id, bot_secret = bot_token.split(':')
        if not bot_id.isdigit() or len(bot_id) < 8 or len(bot_secret) < 35:
            logger.warning("Format bot token tidak valid - ID atau secret tidak sesuai")
            return jsonify({
                'success': False,
                'message': 'Format bot token tidak valid. Bot ID harus angka minimal 8 digit dan secret minimal 35 karakter.'
            }), 400
        
        try:
            # Gunakan service integrasi untuk setup bot
            logger.debug("Setting up bot using integration service...")
            
            if telegram_integration.set_bot_token(bot_token):
                logger.info("Bot setup successful via integration service")
                
                # Update atau buat settings di database
                settings = TelegramSettings.query.filter_by(company_id=company_id).first()
                
                if not settings:
                    logger.debug("Creating new telegram settings")
                    settings = TelegramSettings(
                        bot_token=bot_token,
                        is_active=True,
                        company_id=company_id
                    )
                    db.session.add(settings)
                else:
                    logger.debug("Updating existing telegram settings")
                    settings.bot_token = bot_token
                    settings.is_active = True
                    settings.updated_at = datetime.now()
                
                db.session.commit()
                logger.info("Telegram bot started successfully")
                
                # Sinkronisasi dengan Agent AI
                logger.info("Syncing with Agent AI...")
                webhook_url = f"http://localhost:5000/api/telegram/webhook"
                sync_result = agent_ai_sync.sync_telegram_webhook(webhook_url)
                
                # Get bot status dari service
                bot_status = telegram_integration.get_bot_status()
                
                return jsonify({
                    'success': True,
                    'message': 'Bot telegram berhasil dimulai dan terhubung dengan Agent AI',
                    'data': {
                        'bot_token': settings.bot_token,
                        'is_active': settings.is_active,
                        'company_id': settings.company_id,
                        'integration_status': bot_status,
                        'agent_ai_sync': sync_result,
                        'webhook_url': webhook_url,
                        'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
                    }
                }), 200
            else:
                logger.error("Bot setup failed via integration service")
                return jsonify({
                    'success': False,
                    'message': 'Gagal setup bot atau webhook. Periksa log untuk detail error.',
                    'debug_info': {
                        'bot_token_length': len(bot_token) if bot_token else 0,
                        'integration_status': telegram_integration.get_bot_status()
                    }
                }), 500
            
        except requests.exceptions.Timeout:
            logger.error("Telegram API connection timeout")
            return jsonify({
                'success': False,
                'message': 'Timeout: Tidak dapat terhubung ke Telegram API'
            }), 408
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram API connection error: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error koneksi: {str(e)}'
            }), 500
        
        except Exception as db_error:
            logger.error(f"Database error in telegram start: {str(db_error)}")
            logger.error(traceback.format_exc())
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Database belum siap, tidak dapat menyimpan pengaturan',
                'debug_info': {
                    'error': str(db_error),
                    'error_type': type(db_error).__name__
                }
            }), 500
    
    except Exception as e:
        logger.error(f"Error in telegram start: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}',
            'debug_info': {
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
        }), 500

@telegram_bp.route('/stop', methods=['POST', 'OPTIONS'])
@jwt_required_custom
def telegram_stop():
    """Endpoint untuk menghentikan telegram bot"""
    
    logger.info(f"Telegram stop endpoint called - Method: {request.method}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        logger.debug("Handling OPTIONS preflight for telegram stop")
        return '', 200
    
    try:
        company_id = Config.DEFAULT_COMPANY_ID  # Default company ID from config
        logger.debug(f"Stopping telegram bot for company: {company_id}")
        
        try:
            settings = TelegramSettings.query.filter_by(company_id=company_id).first()
            
            if not settings:
                logger.warning("No telegram settings found")
                return jsonify({
                    'success': False,
                    'message': 'Pengaturan telegram tidak ditemukan'
                }), 404
            
            # Hapus webhook via service integrasi
            logger.debug("Removing webhook via integration service...")
            if telegram_integration.remove_webhook():
                logger.info("Webhook removed successfully")
            else:
                logger.warning("Failed to remove webhook")
            
            # Update settings
            settings.is_active = False
            settings.updated_at = datetime.now()
            
            db.session.commit()
            logger.info("Telegram bot stopped successfully")
            
            return jsonify({
                'success': True,
                'message': 'Bot telegram berhasil dihentikan dan webhook dihapus',
                'data': {
                    'bot_token': settings.bot_token,
                    'is_active': settings.is_active,
                    'company_id': settings.company_id,
                    'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
                }
            }), 200
            
        except Exception as db_error:
            logger.error(f"Database error in telegram stop: {str(db_error)}")
            logger.error(traceback.format_exc())
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Database belum siap, tidak dapat menghentikan bot',
                'debug_info': {
                    'error': str(db_error),
                    'error_type': type(db_error).__name__
                }
            }), 500
    
    except Exception as e:
        logger.error(f"Error in telegram stop: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}',
            'debug_info': {
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
        }), 500

@telegram_bp.route('/ping', methods=['GET'])
def telegram_ping():
    """Simple ping endpoint untuk test koneksi"""
    return jsonify({
        'success': True,
        'message': 'pong',
        'timestamp': datetime.now().isoformat()
    }), 200

@telegram_bp.route('/webhook', methods=['POST'])
def telegram_webhook_endpoint():
    """Webhook endpoint untuk menerima pesan dari Telegram"""
    try:
        logger.info("Webhook endpoint called")
        
        # Get webhook data
        webhook_data = request.get_json()
        if not webhook_data:
            logger.warning("No webhook data received")
            return jsonify({'success': False, 'message': 'No data received'}), 400
        
        logger.debug(f"Webhook data: {webhook_data}")
        
        # Extract minimal fields
        message = None
        chat_id = None
        user_id = None
        if 'message' in webhook_data and 'text' in webhook_data['message']:
            message = webhook_data['message']['text']
            chat_id = webhook_data['message']['chat']['id']
            user_id = webhook_data['message']['from']['id']
        elif 'callback_query' in webhook_data:
            message = webhook_data['callback_query'].get('data', '')
            chat_id = webhook_data['callback_query']['message']['chat']['id']
            user_id = webhook_data['callback_query']['from']['id']

        if not message:
            return jsonify({'success': True, 'message': 'Ignored non-text update'}), 200

        # TODO enterprise: resolve company_id dari mapping telegram_user_links
        company_id = Config.DEFAULT_COMPANY_ID

        # Pastikan bot token runtime tersedia (ambil dari DB jika perlu)
        try:
            if not telegram_integration.bot_token:
                settings = TelegramSettings.query.filter_by(company_id=company_id).first()
                if settings and settings.bot_token:
                    telegram_integration.bot_token = settings.bot_token
                    # Jika tidak ada webhook HTTPS, aktifkan polling
                    telegram_integration.ensure_polling_active()
        except Exception:
            pass

        # Use RAG Enhanced Telegram Service untuk integrasi RAG + Agent AI
        try:
            from services.rag_enhanced_telegram_service import rag_enhanced_telegram
            
            agent_result = rag_enhanced_telegram.process_telegram_message(
                user_id=user_id,
                message=message,
                session_id=f'telegram_{user_id}',
                company_id=company_id
            )
            
            logger.info(f"🤖 RAG Enhanced Telegram processed message for user {user_id}")
            
        except ImportError as e:
            logger.warning(f"⚠️ RAG Enhanced Telegram Service not available: {e}, using fallback")
            # Fallback ke method lama dengan company_id
            agent_result = telegram_integration.send_message_to_agent(
                user_id=user_id,
                message=message,
                session_id=f'telegram_{user_id}',
                company_id=company_id
            )

        # Kirim balik via Telegram API jika ada token terkonfigurasi
        if agent_result.get('success') and 'data' in agent_result:
            response_text = agent_result['data'].get('response', 'Maaf, tidak ada respons dari AI.')
            sent = telegram_integration._send_telegram_response(chat_id, response_text)
            return jsonify({'success': True, 'message': 'OK', 'sent': bool(sent)}), 200

        return jsonify({'success': False, 'message': agent_result.get('message', 'process_failed')}), 500
            
    except Exception as e:
        logger.error(f"Error in webhook endpoint: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@telegram_bp.route('/debug', methods=['GET'])
def telegram_debug():
    """Endpoint untuk debug info"""
    return jsonify({
        'success': True,
        'message': 'Debug info endpoint',
        'timestamp': datetime.now().isoformat()
    }), 200

@telegram_bp.route('/settings/public', methods=['GET', 'OPTIONS'])
def telegram_settings_public():
    """Public endpoint untuk telegram settings tanpa authentication"""
    
    logger.info(f"Public telegram settings endpoint called - Method: {request.method}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        logger.debug("Handling OPTIONS preflight for public telegram settings")
        return '', 200
    
    try:
        company_id = Config.DEFAULT_COMPANY_ID  # Default company ID from config
        logger.debug(f"Processing public telegram settings for company: {company_id}")
        
        # Get telegram settings
        logger.debug("Getting telegram settings")
        try:
            settings = TelegramSettings.query.filter_by(company_id=company_id).first()
            logger.debug(f"Retrieved settings: {settings}")
            
            if not settings:
                logger.debug("No settings found, creating default settings")
                # Create default settings if not exists
                settings = TelegramSettings(
                    bot_token='',
                    is_active=False,
                    company_id=company_id
                )
                db.session.add(settings)
                db.session.commit()
                logger.debug("Default settings created successfully")
            
            return jsonify({
                'success': True,
                'data': {
                    'bot_token': settings.bot_token or '',
                    'is_active': settings.is_active,
                    'company_id': settings.company_id,
                    'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
                }
            }), 200
        except Exception as db_error:
            logger.error(f"Database error in public telegram settings GET: {str(db_error)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'success': True,
                'data': {
                    'bot_token': '',
                    'is_active': False,
                    'company_id': company_id,
                    'updated_at': None
                },
                'message': 'Database belum siap, menggunakan pengaturan default',
                'debug_info': {
                    'error': str(db_error),
                    'error_type': type(db_error).__name__
                }
            }), 200
            
    except Exception as e:
        logger.error(f"Error in public telegram settings: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan saat mengambil pengaturan',
            'timestamp': datetime.now().isoformat()
        }), 500

@telegram_bp.route('/settings', methods=['GET', 'POST', 'PUT', 'OPTIONS'])
@jwt_required_custom
@block_vendor()
def telegram_settings():
    """Endpoint untuk mengelola pengaturan telegram bot"""
    
    logger.info(f"Telegram settings endpoint called - Method: {request.method}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        logger.debug("Handling OPTIONS preflight for telegram settings")
        return '', 200
    
    try:
        company_id = Config.DEFAULT_COMPANY_ID  # Default company ID from config
        logger.debug(f"Processing telegram settings for company: {company_id}")
        
        if request.method == 'GET':
            # Get telegram settings
            logger.debug("Getting telegram settings")
            try:
                settings = TelegramSettings.query.filter_by(company_id=company_id).first()
                logger.debug(f"Retrieved settings: {settings}")
                
                if not settings:
                    logger.debug("No settings found, creating default settings")
                    # Create default settings if not exists
                    settings = TelegramSettings(
                        bot_token='',
                        is_active=False,
                        company_id=company_id
                    )
                    db.session.add(settings)
                    db.session.commit()
                    logger.debug("Default settings created successfully")
                
                return jsonify({
                    'success': True,
                    'data': {
                        'bot_token': settings.bot_token or '',
                        'is_active': settings.is_active,
                        'company_id': settings.company_id,
                        'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
                    }
                }), 200
            except Exception as db_error:
                logger.error(f"Database error in telegram settings GET: {str(db_error)}")
                logger.error(traceback.format_exc())
                return jsonify({
                    'success': True,
                    'data': {
                        'bot_token': '',
                        'is_active': False,
                        'company_id': company_id,
                        'updated_at': None
                    },
                    'message': 'Database belum siap, menggunakan pengaturan default',
                    'debug_info': {
                        'error': str(db_error),
                        'error_type': type(db_error).__name__
                    }
                }), 200
        
        elif request.method in ['POST', 'PUT']:
            # Update telegram settings
            logger.debug("Updating telegram settings")
            data = request.get_json()
            logger.debug(f"Request data: {data}")
            logger.debug(f"Request method: {request.method}")
            logger.debug(f"Request headers: {dict(request.headers)}")
            
            if not data:
                logger.warning("No data provided in request")
                return jsonify({
                    'success': False,
                    'message': 'Data tidak boleh kosong'
                }), 400
            
            bot_token = data.get('bot_token', '')
            is_active = data.get('is_active', False)
            logger.debug(f"Bot token: {bot_token[:10]}..., Is active: {is_active}")
            logger.debug(f"Bot token length: {len(bot_token) if bot_token else 0}")
            logger.debug(f"Bot token is digit: {bot_token.isdigit() if bot_token else False}")
            
            # Validasi bot token - wajib diisi dan format harus benar
            if not bot_token or not bot_token.strip():
                logger.warning("Bot token tidak boleh kosong")
                return jsonify({
                    'success': False,
                    'message': 'Bot token tidak boleh kosong'
                }), 400
            
            bot_token = bot_token.strip()
            if ':' not in bot_token or len(bot_token.split(':')) != 2:
                logger.warning("Format bot token tidak valid - harus mengandung :")
                return jsonify({
                    'success': False,
                    'message': 'Format bot token tidak valid. Bot token harus dalam format: 123456789:ABCdefGhIjKlmNoPqRsTuVwXyZ'
                }), 400
            
            bot_id, bot_secret = bot_token.split(':')
            if not bot_id.isdigit() or len(bot_id) < 8 or len(bot_secret) < 35:
                logger.warning("Format bot token tidak valid - ID atau secret tidak sesuai")
                return jsonify({
                    'success': False,
                    'message': 'Format bot token tidak valid. Bot ID harus angka minimal 8 digit dan secret minimal 35 karakter.'
                }), 400
            
            try:
                settings = TelegramSettings.query.filter_by(company_id=company_id).first()
                logger.debug(f"Existing settings: {settings}")
                
                if not settings:
                    logger.debug("Creating new telegram settings")
                    # Create new settings
                    settings = TelegramSettings(
                        bot_token=bot_token,
                        is_active=is_active,
                        company_id=company_id
                    )
                    db.session.add(settings)
                else:
                    logger.debug("Updating existing telegram settings")
                    # Update existing settings
                    settings.bot_token = bot_token
                    settings.is_active = is_active
                    settings.updated_at = datetime.now()
                
                db.session.commit()
                logger.info("Telegram settings saved successfully")
            except Exception as db_error:
                logger.error(f"Database error in telegram settings POST/PUT: {str(db_error)}")
                logger.error(traceback.format_exc())
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': 'Database belum siap, tidak dapat menyimpan pengaturan',
                    'debug_info': {
                        'error': str(db_error),
                        'error_type': type(db_error).__name__
                    }
                }), 500
            
            return jsonify({
                'success': True,
                'message': 'Pengaturan telegram berhasil disimpan',
                'data': {
                    'bot_token': settings.bot_token,
                    'is_active': settings.is_active,
                    'company_id': settings.company_id,
                    'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
                }
            }), 200
    
    except Exception as e:
        logger.error(f"Error in telegram settings: {str(e)}")
        logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}',
            'debug_info': {
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
        }), 500

@telegram_bp.route('/settings/test', methods=['POST', 'OPTIONS'])
@jwt_required_custom
def test_telegram_settings():
    """Test koneksi telegram bot"""
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        logger.debug(f"Test settings request data: {data}")
        logger.debug(f"Test settings request method: {request.method}")
        logger.debug(f"Test settings request headers: {dict(request.headers)}")
        
        if not data:
            logger.warning("No data provided in test settings request")
            return jsonify({
                'success': False,
                'message': 'Data tidak boleh kosong'
            }), 400
            
        bot_token = data.get('bot_token', '')
        logger.debug(f"Test settings bot token: {bot_token[:10]}...")
        logger.debug(f"Test settings bot token length: {len(bot_token) if bot_token else 0}")
        logger.debug(f"Test settings bot token is digit: {bot_token.isdigit() if bot_token else False}")
        
        if not bot_token or not bot_token.strip():
            logger.warning("Bot token tidak boleh kosong in test settings")
            return jsonify({
                'success': False,
                'message': 'Bot token tidak boleh kosong'
            }), 400
        
        # Validasi format bot token
        bot_token = bot_token.strip()
        if ':' not in bot_token or len(bot_token.split(':')) != 2:
            logger.warning("Format bot token tidak valid - harus mengandung : in test settings")
            return jsonify({
                'success': False,
                'message': 'Format bot token tidak valid. Bot token harus dalam format: 123456789:ABCdefGhIjKlmNoPqRsTuVwXyZ'
            }), 400
        
        bot_id, bot_secret = bot_token.split(':')
        if not bot_id.isdigit() or len(bot_id) < 8 or len(bot_secret) < 35:
            logger.warning("Format bot token tidak valid - ID atau secret tidak sesuai in test settings")
            return jsonify({
                'success': False,
                'message': 'Format bot token tidak valid. Bot ID harus angka minimal 8 digit dan secret minimal 35 karakter.'
            }), 400
        
        # Test koneksi ke Telegram API
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            return jsonify({
                'success': True,
                'message': 'Koneksi berhasil',
                'data': {
                    'bot_name': bot_info.get('result', {}).get('first_name', ''),
                    'bot_username': bot_info.get('result', {}).get('username', ''),
                    'bot_id': bot_info.get('result', {}).get('id', '')
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Token tidak valid atau tidak dapat terhubung ke Telegram API'
            }), 400
    
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'message': 'Timeout: Tidak dapat terhubung ke Telegram API'
        }), 408
    
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'message': f'Error koneksi: {str(e)}'
        }), 500
    
    except Exception as e:
        logger.error(f"Error testing telegram settings: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@telegram_bp.route('/integration/status', methods=['GET'])
@jwt_required_custom
def telegram_integration_status():
    """Get status integrasi dengan Agent AI"""
    try:
        # Get bot status
        bot_status = telegram_integration.get_bot_status()
        
        # Test koneksi ke Agent AI
        agent_status = telegram_integration.test_agent_ai_connection()
        
        return jsonify({
            'success': True,
            'data': {
                'bot_status': bot_status,
                'agent_ai_status': agent_status,
                'timestamp': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting integration status: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@telegram_bp.route('/integration/test', methods=['POST'])
@jwt_required_custom
def test_telegram_integration():
    """Test integrasi dengan Agent AI"""
    try:
        data = request.get_json()
        test_message = data.get('message', 'Test message') if data else 'Test message'
        test_user_id = data.get('user_id', 12345) if data else 12345
        
        # Test kirim pesan ke Agent AI
        result = telegram_integration.send_message_to_agent(
            user_id=test_user_id,
            message=test_message,
            session_id=f'test_{test_user_id}'
        )
        
        return jsonify({
            'success': True,
            'data': {
                'test_result': result,
                'timestamp': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing integration: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@telegram_bp.route('/test-connection', methods=['GET'])
@jwt_required_custom
def test_telegram_connection():
    """Test koneksi ke Telegram API dan Agent AI"""
    try:
        # Test koneksi ke Agent AI
        agent_status = telegram_integration.test_agent_ai_connection()
        
        # Test koneksi ke Telegram API (jika ada token)
        telegram_status = {
            'bot_token_set': bool(telegram_integration.bot_token),
            'webhook_set': bool(telegram_integration.webhook_url)
        }
        
        agent_ai_url = os.getenv('AGENT_AI_URL', 'http://localhost:5000')
        return jsonify({
            'success': True,
            'data': {
                'agent_ai_status': agent_status,
                'telegram_status': telegram_status,
                'backend_url': agent_ai_url,
                'agent_ai_url': agent_ai_url,
                'timestamp': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@telegram_bp.route('/sync/agent-ai', methods=['GET', 'POST'])
@jwt_required_custom
def sync_with_agent_ai():
    """Sinkronisasi dengan Agent AI"""
    try:
        if request.method == 'GET':
            # Get sync status
            sync_status = agent_ai_sync.get_sync_status()
            return jsonify({
                'success': True,
                'data': sync_status
            }), 200
        
        elif request.method == 'POST':
            # Force sync
            sync_result = agent_ai_sync.force_sync()
            return jsonify({
                'success': True,
                'data': sync_result
            }), 200
            
    except Exception as e:
        logger.error(f"Error syncing with Agent AI: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@telegram_bp.route('/sync/webhook', methods=['POST'])
@jwt_required_custom
def sync_webhook_with_agent_ai():
    """Sinkronisasi webhook dengan Agent AI"""
    try:
        data = request.get_json()
        webhook_url = data.get('webhook_url') if data else None
        
        if not webhook_url:
            agent_ai_url = os.getenv('AGENT_AI_URL', 'http://localhost:5000')
            webhook_url = f"{agent_ai_url}/api/telegram/webhook"
        
        # Sync webhook dengan Agent AI
        sync_result = agent_ai_sync.sync_telegram_webhook(webhook_url)
        
        return jsonify({
            'success': True,
            'data': sync_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error syncing webhook: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@telegram_bp.route('/rag/test', methods=['POST'])
@jwt_required_custom
def test_rag_integration():
    """Test RAG integration dengan Telegram"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data request wajib diisi'
            }), 400
        
        message = data.get('message', 'Test message')
        company_id = data.get('company_id', Config.DEFAULT_COMPANY_ID)
        user_id = data.get('user_id', 12345)
        
        # Test RAG Enhanced Telegram Service
        try:
            from services.rag_enhanced_telegram_service import rag_enhanced_telegram
            
            result = rag_enhanced_telegram.process_telegram_message(
                user_id=user_id,
                message=message,
                session_id=f'test_{user_id}',
                company_id=company_id
            )
            
            return jsonify({
                'success': True,
                'message': 'RAG integration test completed',
                'data': result
            }), 200
            
        except ImportError as e:
            return jsonify({
                'success': False,
                'message': f'RAG Enhanced Telegram Service not available: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error testing RAG integration: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@telegram_bp.route('/rag/status', methods=['GET'])
@jwt_required_custom
def get_rag_status():
    """Get status RAG integration"""
    try:
        try:
            from services.rag_enhanced_telegram_service import rag_enhanced_telegram
            
            status = rag_enhanced_telegram.get_service_status()
            
            return jsonify({
                'success': True,
                'message': 'RAG status retrieved',
                'data': status
            }), 200
            
        except ImportError as e:
            return jsonify({
                'success': False,
                'message': f'RAG Enhanced Telegram Service not available: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error getting RAG status: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
