#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Controller untuk Agent AI
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.validators import validate_telegram_request
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

# Create blueprint
telegram_bp = Blueprint('telegram', __name__)

@telegram_bp.route('/chat', methods=['POST'])
def telegram_chat():
    """Handle Telegram chat messages"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Validate request
        validation_result = validate_telegram_request(data)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'message': 'Invalid request data',
                'errors': validation_result['errors'],
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Extract data
        user_id = data.get('user_id')
        message = data.get('message')
        session_id = data.get('session_id', f'telegram_{user_id}')
        source = data.get('source', 'telegram')
        rag_context = data.get('rag_context', None)
        
        logger.info(f"📨 Processing Telegram message from user {user_id}: {message[:50]}...")
        
        # Process RAG context if available
        processed_context = None
        if rag_context and rag_context.get('context_available'):
            try:
                from services.rag_context_service import rag_context_service
                processed_context = rag_context_service.process_context(rag_context)
                logger.info(f"✅ RAG context processed: {processed_context.get('total_chunks', 0)} chunks")
            except Exception as e:
                logger.warning(f"⚠️ Failed to process RAG context: {e}")
                processed_context = None
        
        # Generate response using LLM service with RAG context
        response = llm_service.generate_response(
            message=message,
            user_id=user_id,
            session_id=session_id,
            source=source,
            context=processed_context  # Include processed RAG context
        )
        
        if response.get('success'):
            logger.info(f"✅ Telegram response generated successfully for user {user_id}")
            return jsonify({
                'success': True,
                'data': {
                    'response': response.get('response'),
                    'model_used': response.get('model_used'),
                    'processing_time': response.get('processing_time'),
                    'tokens_used': response.get('tokens_used'),
                    'rag_context_used': processed_context.get('context_available', False) if processed_context else False,
                    'rag_chunks_used': processed_context.get('total_chunks', 0) if processed_context else 0,
                    'rag_avg_similarity': processed_context.get('avg_similarity', 0.0) if processed_context else 0.0
                },
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            logger.error(f"❌ Failed to generate Telegram response: {response.get('error')}")
            return jsonify({
                'success': False,
                'message': 'Failed to generate response',
                'error': response.get('error'),
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Telegram chat error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@telegram_bp.route('/test', methods=['POST'])
def test_telegram():
    """Test Telegram endpoint"""
    try:
        data = request.get_json() or {}
        
        test_message = data.get('message', 'Hello, this is a test message')
        user_id = data.get('user_id', 12345)
        
        logger.info(f"🧪 Testing Telegram endpoint with message: {test_message}")
        
        # Generate test response
        response = llm_service.generate_response(
            message=test_message,
            user_id=user_id,
            session_id='test_telegram',
            source='test',
            context=None
        )
        
        return jsonify({
            'success': True,
            'message': 'Telegram endpoint test completed',
            'test_data': {
                'input_message': test_message,
                'user_id': user_id,
                'response': response.get('response'),
                'model_used': response.get('model_used'),
                'processing_time': response.get('processing_time')
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Telegram test error: {e}")
        return jsonify({
            'success': False,
            'message': 'Test failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
