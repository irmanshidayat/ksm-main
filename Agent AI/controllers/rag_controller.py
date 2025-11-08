#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Controller untuk Agent AI
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.validators import validate_rag_request
from services.llm_service import llm_service
from services.rag_context_service import rag_context_service

logger = logging.getLogger(__name__)

# Create blueprint
rag_bp = Blueprint('rag', __name__)

@rag_bp.route('/chat', methods=['POST'])
def rag_chat():
    """Handle RAG-enhanced chat messages"""
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
        validation_result = validate_rag_request(data)
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
        context = data.get('context', {})
        session_id = data.get('session_id', f'rag_{user_id}')
        source = data.get('source', 'rag')
        metadata = data.get('metadata', {})
        
        logger.info(f"📨 Processing RAG-enhanced message from user {user_id}: {message[:50]}...")
        logger.info(f"🔍 RAG context: {context.get('total_chunks', 0)} chunks, avg_similarity: {context.get('avg_similarity', 0.0)}")
        
        # Process RAG context
        processed_context = rag_context_service.process_context(context)
        
        # Generate response using LLM service with RAG context
        response = llm_service.generate_response(
            message=message,
            user_id=user_id,
            session_id=session_id,
            source=source,
            context=processed_context,
            metadata=metadata
        )
        
        if response.get('success'):
            logger.info(f"✅ RAG-enhanced response generated successfully for user {user_id}")
            return jsonify({
                'success': True,
                'data': {
                    'response': response.get('response'),
                    'model_used': response.get('model_used'),
                    'processing_time': response.get('processing_time'),
                    'tokens_used': response.get('tokens_used'),
                    'rag_metadata': {
                        'context_used': processed_context.get('context_available', False),
                        'chunks_processed': processed_context.get('total_chunks', 0),
                        'avg_similarity': processed_context.get('avg_similarity', 0.0),
                        'context_processing_time': processed_context.get('processing_time', 0)
                    }
                },
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            logger.error(f"❌ Failed to generate RAG-enhanced response: {response.get('error')}")
            return jsonify({
                'success': False,
                'message': 'Failed to generate response',
                'error': response.get('error'),
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"❌ RAG chat error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@rag_bp.route('/status', methods=['GET'])
def rag_status():
    """Get RAG service status"""
    try:
        # Get RAG context service status
        rag_status = rag_context_service.get_status()
        
        # Get LLM service status
        llm_status = llm_service.get_status()
        
        return jsonify({
            'success': True,
            'data': {
                'rag_context_service': rag_status,
                'llm_service': llm_status,
                'endpoints': {
                    'rag_chat': '/api/rag/chat',
                    'rag_status': '/api/rag/status',
                    'rag_test': '/api/rag/test'
                }
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ RAG status error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get RAG status',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@rag_bp.route('/test', methods=['POST'])
def test_rag():
    """Test RAG endpoint"""
    try:
        data = request.get_json() or {}
        
        test_message = data.get('message', 'Hello, this is a test RAG message')
        user_id = data.get('user_id', 12345)
        
        # Create test context
        test_context = {
            'rag_results': [
                {
                    'content': 'This is a test content from RAG system',
                    'similarity': 0.85,
                    'source_document': 'test_document.pdf',
                    'chunk_id': 'test_chunk_1',
                    'metadata': {'test': True}
                }
            ],
            'total_chunks': 1,
            'avg_similarity': 0.85,
            'search_time_ms': 150.5,
            'context_available': True,
            'similarity_threshold': 0.65
        }
        
        logger.info(f"🧪 Testing RAG endpoint with message: {test_message}")
        
        # Process test context
        processed_context = rag_context_service.process_context(test_context)
        
        # Generate test response
        response = llm_service.generate_response(
            message=test_message,
            user_id=user_id,
            session_id='test_rag',
            source='test_rag',
            context=processed_context,
            metadata={'test_mode': True}
        )
        
        return jsonify({
            'success': True,
            'message': 'RAG endpoint test completed',
            'test_data': {
                'input_message': test_message,
                'user_id': user_id,
                'context_chunks': test_context.get('total_chunks', 0),
                'avg_similarity': test_context.get('avg_similarity', 0.0),
                'response': response.get('response'),
                'model_used': response.get('model_used'),
                'processing_time': response.get('processing_time'),
                'rag_metadata': {
                    'context_used': processed_context.get('context_available', False),
                    'chunks_processed': processed_context.get('total_chunks', 0)
                }
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ RAG test error: {e}")
        return jsonify({
            'success': False,
            'message': 'RAG test failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
