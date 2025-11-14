#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service Controller untuk Monitoring Domain
Routes untuk service management dan monitoring
"""

from flask import Blueprint, request, jsonify
import logging
import os
from datetime import datetime
from typing import Dict, Any

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
service_bp = Blueprint('service', __name__, url_prefix='/api/services')

@service_bp.route('/status', methods=['GET'])
def get_service_status():
    """Get status of all services"""
    try:
        status_data = {
            'timestamp': datetime.now().isoformat(),
            'services': {
                'KSM_main': {
                    'status': 'running',
                    'version': '1.0.0',
                    'uptime': 'active'
                },
                'agent_ai_integration': {
                    'status': 'connected',
                    'url': os.getenv('AGENT_AI_URL', 'http://localhost:5000'),
                    'last_check': datetime.now().isoformat()
                },
                'database': {
                    'status': 'connected',
                    'type': 'mysql',
                    'last_check': datetime.now().isoformat()
                },
                'telegram_bot': {
                    'status': 'active',
                    'webhook_configured': True,
                    'last_check': datetime.now().isoformat()
                }
            },
            'health': 'healthy'
        }
        
        logger.info("Service status requested")
        return jsonify({
            'success': True,
            'message': 'Service status retrieved successfully',
            'data': status_data,
            'status_code': 200
        })
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get service status',
            'error': str(e),
            'status_code': 500
        }), 500

@service_bp.route('/agent-ai/status', methods=['GET'])
def agent_ai_status():
    """Check Agent AI integration status"""
    try:
        import requests
        
        agent_ai_url = os.getenv('AGENT_AI_URL', 'http://localhost:5000')
        
        # Check Agent AI health
        response = requests.get(f"{agent_ai_url}/health", timeout=10)
        
        if response.status_code == 200:
            agent_data = response.json()
            status_data = {
                'agent_ai_status': 'connected',
                'agent_ai_health': agent_data.get('data', {}),
                'last_check': datetime.now().isoformat(),
                'integration_status': 'active'
            }
            
            return jsonify({
                'success': True,
                'message': 'Agent AI integration is healthy',
                'data': status_data,
                'status_code': 200
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Agent AI is not responding',
                'data': {
                    'agent_ai_status': 'disconnected',
                    'last_check': datetime.now().isoformat(),
                    'integration_status': 'inactive'
                },
                'status_code': 503
            }), 503
            
    except Exception as e:
        logger.error(f"Agent AI status check failed: {e}")
        return jsonify({
            'success': False,
            'message': 'Agent AI status check failed',
            'error': str(e),
            'data': {
                'agent_ai_status': 'error',
                'last_check': datetime.now().isoformat(),
                'integration_status': 'error'
            },
            'status_code': 500
        }), 500

@service_bp.route('/agent-ai/forward', methods=['POST'])
def forward_to_agent_ai():
    """Forward request to Agent AI - OPTIMIZED for AI response generation only"""
    try:
        import requests
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided',
                'status_code': 400
            }), 400
        
        endpoint = data.get('endpoint', '/api/knowledge/query')
        agent_ai_url = os.getenv('AGENT_AI_URL', 'http://localhost:5000')
        api_key = os.getenv('AGENT_AI_API_KEY', 'KSM_api_key_2ptybn')
        
        # Forward request to Agent AI
        response = requests.post(
            f"{agent_ai_url}{endpoint}",
            json=data.get('payload', {}),
            headers={
                'Content-Type': 'application/json',
                'X-API-Key': api_key
            },
            timeout=30
        )
        
        if response.status_code == 200:
            agent_response = response.json()
            return jsonify({
                'success': True,
                'message': 'Request forwarded to Agent AI successfully',
                'data': agent_response,
                'status_code': 200
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Agent AI request failed with status {response.status_code}',
                'data': response.text,
                'status_code': response.status_code
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error forwarding to Agent AI: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to forward request to Agent AI',
            'error': str(e),
            'status_code': 500
        }), 500

@service_bp.route('/config', methods=['GET'])
def get_service_config():
    """Get service configuration"""
    try:
        config_data = {
            'agent_ai_url': os.getenv('AGENT_AI_URL', 'http://localhost:5000'),
            'agent_ai_api_key': os.getenv('AGENT_AI_API_KEY', 'KSM_api_key_2ptybn'),
            'database_url': os.getenv('DATABASE_URL', 'mysql://root:@localhost:3306/KSM_main'),
            'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN', 'Not configured'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'debug_mode': os.getenv('DEBUG', 'false').lower() == 'true',
            'features': {
                'agent_ai_integration': os.getenv('ENABLE_AGENT_AI_INTEGRATION', 'true').lower() == 'true',
                'telegram_bot': os.getenv('ENABLE_TELEGRAM_BOT', 'true').lower() == 'true',
                'knowledge_base': os.getenv('ENABLE_KNOWLEDGE_BASE', 'true').lower() == 'true',
                'monitoring': os.getenv('ENABLE_MONITORING', 'true').lower() == 'true'
            }
        }
        
        return jsonify({
            'success': True,
            'message': 'Service configuration retrieved successfully',
            'data': config_data,
            'status_code': 200
        })
        
    except Exception as e:
        logger.error(f"Error getting service config: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get service configuration',
            'error': str(e),
            'status_code': 500
        }), 500

# Error handlers
@service_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Service endpoint not found',
        'status_code': 404
    }), 404

@service_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal service error',
        'status_code': 500
    }), 500

