#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health Controller untuk Agent AI
"""

import logging
from flask import Blueprint, jsonify
from datetime import datetime
from config.database import test_database_connection, get_database_info
from services.llm_service import llm_service
from services.rag_context_service import rag_context_service

logger = logging.getLogger(__name__)

# Create blueprint
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_status = test_database_connection()
        
        # Check LLM service
        llm_status = llm_service.check_health()
        
        # Check RAG context service
        rag_status = rag_context_service.check_health()
        
        # Overall health status
        overall_healthy = (
            db_status.get('success', False) and
            llm_status.get('success', False) and
            rag_status.get('success', False)
        )
        
        return jsonify({
            'service': 'Agent AI',
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'database': db_status,
                'llm_service': llm_status,
                'rag_context_service': rag_status
            },
            'version': '1.0.0'
        }), 200 if overall_healthy else 503
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'service': 'Agent AI',
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_bp.route('/status', methods=['GET'])
def get_status():
    """Get detailed status"""
    try:
        # Get database info
        db_info = get_database_info()
        
        # Get service statuses
        llm_status = llm_service.get_status()
        rag_status = rag_context_service.get_status()
        
        return jsonify({
            'service': 'Agent AI',
            'status': 'active',
            'timestamp': datetime.now().isoformat(),
            'database': db_info,
            'services': {
                'llm_service': llm_status,
                'rag_context_service': rag_status
            },
            'endpoints': {
                'health': '/health',
                'status': '/status',
                'telegram_chat': '/api/telegram/chat',
                'rag_chat': '/api/rag/chat',
                'rag_status': '/api/rag/status'
            },
            'version': '1.0.0'
        }), 200
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({
            'service': 'Agent AI',
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint"""
    return jsonify({
        'message': 'pong',
        'timestamp': datetime.now().isoformat()
    }), 200
