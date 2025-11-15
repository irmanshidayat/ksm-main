#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge AI Controller untuk KSM Main Backend
Controller untuk menangani endpoint API knowledge AI
"""

from flask import Blueprint, request, jsonify
import logging
import time
import traceback
from datetime import datetime
from sqlalchemy import text
# unified_ai_service removed - using Agent AI directly
from domains.integration.services.agent_ai_sync_service import agent_ai_sync

# Initialize blueprint
knowledge_ai_bp = Blueprint('knowledge_ai', __name__)

# Initialize service - using Agent AI
knowledge_ai_service = None  # Removed

# Setup logging
logger = logging.getLogger(__name__)

@knowledge_ai_bp.route('/api/knowledge-ai/ask', methods=['POST'])
def ask_question():
    """
    Endpoint untuk bertanya kepada knowledge base AI
    """
    start_time = time.time()
    
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data request wajib diisi',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # Validate required fields
        query = data.get('query')
        if not query or not query.strip():
            return jsonify({
                'success': False,
                'message': 'Pertanyaan wajib diisi',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # Get optional parameters
        category_id = data.get('category_id')
        priority_level = data.get('priority_level')
        
        # Validate priority level
        if priority_level and priority_level not in ['high', 'medium', 'low']:
            return jsonify({
                'success': False,
                'message': 'Priority level harus high, medium, atau low',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # Generate AI response using Agent AI
        try:
            agent_result = agent_ai_sync.send_message_to_agent(
                user_id=0,  # System user
                message=query.strip(),
                session_id='knowledge_ai_ask'
            )
            
            if agent_result.get('success'):
                response = {
                    'success': True,
                    'data': {
                        'response': agent_result['data'].get('response', 'Maaf, tidak ada respons dari AI.'),
                        'model_used': agent_result['data'].get('model_used', 'agent_ai'),
                        'tokens_used': agent_result['data'].get('tokens_used', 0)
                    }
                }
            else:
                response = {
                    'success': False,
                    'message': agent_result.get('message', 'Gagal memproses pertanyaan')
                }
        except Exception as e:
            response = {
                'success': False,
                'message': f'Error: {str(e)}'
            }
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        
        # Add metadata to response
        response['metadata'] = {
            'query': query,
            'category_id': category_id,
            'priority_level': priority_level,
            'response_time_ms': round(response_time, 2),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Return response
        if response['success']:
            return jsonify(response), 200
        else:
            return jsonify(response), 404
            
    except Exception as e:
        logger.error(f"Error in ask_question: {e}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan internal server',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# REMOVED: /api/knowledge-ai/search endpoint - functionality consolidated into /api/qdrant-knowledge-base/search

@knowledge_ai_bp.route('/api/knowledge-ai/stats', methods=['GET'])
def get_knowledge_stats():
    """
    Endpoint untuk mendapatkan statistik knowledge base
    """
    try:
        # Debug: Log request
        logger.info("🔍 Knowledge AI Stats Request received")
        
        # Cek database connection terlebih dahulu
        try:
            from config.database import db
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("✅ Database connection OK")
        except Exception as db_error:
            logger.error(f"❌ Database connection failed: {db_error}")
            return jsonify({
                'success': False,
                'message': 'Database tidak tersedia',
                'error': f'Database connection error: {str(db_error)}',
                'debug_info': {
                    'error_type': 'database_connection',
                    'timestamp': datetime.utcnow().isoformat()
                }
            }), 503
        
        # REMOVED: Direct knowledge_ai_service - now handled by Agent AI
        # Cek service availability
        try:
            # stats = knowledge_ai_service.get_knowledge_stats()
            stats = {
                'total_files': 0,
                'total_categories': 0,
                'total_size_mb': 0,
                'message': 'Stats moved to Agent AI'
            }
            logger.info("✅ Knowledge AI Service OK (moved to Agent AI)")
        except Exception as service_error:
            logger.error(f"❌ Knowledge AI Service failed: {service_error}")
            return jsonify({
                'success': False,
                'message': 'Knowledge AI Service tidak tersedia',
                'error': f'Service error: {str(service_error)}',
                'debug_info': {
                    'error_type': 'service_error',
                    'timestamp': datetime.utcnow().isoformat()
                }
            }), 503
        
        if 'error' in stats:
            logger.error(f"❌ Stats returned error: {stats['error']}")
            return jsonify({
                'success': False,
                'message': 'Gagal mendapatkan statistik',
                'error': stats['error'],
                'debug_info': {
                    'error_type': 'stats_error',
                    'timestamp': datetime.utcnow().isoformat()
                }
            }), 500
        
        logger.info(f"✅ Stats retrieved successfully: {stats.get('total_files', 0)} files")
        return jsonify({
            'success': True,
            'data': stats,
            'message': 'Statistik knowledge base berhasil diambil',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_knowledge_stats: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan internal server',
            'error': str(e),
            'debug_info': {
                'error_type': 'unexpected_error',
                'traceback': traceback.format_exc(),
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 500

# Health check endpoint dihapus - sekarang menggunakan unified_health_controller

@knowledge_ai_bp.route('/api/knowledge-ai/suggestions', methods=['POST'])
def get_search_suggestions():
    """
    Endpoint untuk mendapatkan saran pencarian
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data request wajib diisi',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # Get query
        query = data.get('query', '')
        
        # REMOVED: Direct knowledge_ai_service - now handled by Agent AI
        # Generate suggestions
        suggestions = []  # Moved to Agent AI
        
        return jsonify({
            'success': True,
            'data': {
                'query': query,
                'suggestions': suggestions
            },
            'message': f'Ditemukan {len(suggestions)} saran pencarian',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_search_suggestions: {e}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan internal server',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@knowledge_ai_bp.route('/api/knowledge-ai/chat', methods=['POST'])
def chat_with_knowledge():
    """
    Endpoint untuk chat dengan knowledge base AI (conversational)
    """
    start_time = time.time()
    
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data request wajib diisi',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # Validate required fields
        message = data.get('message')
        if not message or not message.strip():
            return jsonify({
                'success': False,
                'message': 'Pesan wajib diisi',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # Get conversation history
        conversation_history = data.get('conversation_history', [])
        
        # Get user context
        user_context = data.get('context', {})
        
        # REMOVED: Direct knowledge_ai_service - now handled by Agent AI
        # Generate AI response
        response = {
            'success': False,
            'message': 'AI response generation moved to Agent AI'
        }
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        
        # Add metadata to response
        response['metadata'] = {
            'message': message,
            'conversation_history_length': len(conversation_history),
            'response_time_ms': round(response_time, 2),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Return response
        if response['success']:
            return jsonify(response), 200
        else:
            return jsonify(response), 404
            
    except Exception as e:
        logger.error(f"Error in chat_with_knowledge: {e}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan internal server',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
