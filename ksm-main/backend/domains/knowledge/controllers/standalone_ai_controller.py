#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone AI Controller untuk Knowledge Domain
Routes untuk fitur AI standalone dan smart routing
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Import services langsung dari domain
from domains.knowledge.services.smart_routing_service import get_smart_routing_service
from domains.integration.services.agent_ai_sync_service import get_agent_ai_sync_service

# Create blueprint
standalone_ai_bp = Blueprint('standalone_ai', __name__, url_prefix='/api/standalone-ai')

@standalone_ai_bp.route('/ask', methods=['POST'])
def ask_standalone_question():
    """Ask question menggunakan standalone OpenRouter service"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Request data tidak ditemukan'
            }), 400
        
        query = data.get('question', '').strip()
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Pertanyaan tidak boleh kosong'
            }), 400
        
        # Get parameters
        system_prompt = data.get('system_prompt', 'Anda adalah asisten AI yang membantu menjawab pertanyaan umum.')
        use_cache = data.get('use_cache', True)
        
        # Use smart routing service dengan force_service='standalone'
        # Smart routing akan fallback ke agent_ai jika standalone tidak tersedia
        routing_service = get_smart_routing_service()
        response = routing_service.route_ai_request(
            query=query,
            context_type='general',  # Force general/standalone context
            force_service='standalone',  # Try standalone first, will fallback to agent_ai
            use_cache=use_cache
        )
        
        logger.info(f"✅ Standalone AI question answered successfully: {query[:50]}...")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error in standalone AI question: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@standalone_ai_bp.route('/vision', methods=['POST'])
def analyze_standalone_vision():
    """Analyze image menggunakan standalone OpenRouter vision service"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Request data tidak ditemukan'
            }), 400
        
        query = data.get('question', '').strip()
        image_base64 = data.get('image_base64', '').strip()
        
        if not image_base64:
            return jsonify({
                'status': 'error',
                'message': 'Image base64 tidak boleh kosong'
            }), 400
        
        # Get parameters
        use_cache = data.get('use_cache', True)
        
        # Use smart routing service untuk vision request
        routing_service = get_smart_routing_service()
        response = routing_service.route_vision_request(
            query=query,
            image_base64=image_base64,
            context_type='general',  # Force general/standalone context
            force_service='standalone',  # Try standalone first, will fallback to agent_ai
            use_cache=use_cache
        )
        
        logger.info(f"✅ Standalone AI vision analysis completed successfully")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error in standalone AI vision: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@standalone_ai_bp.route('/smart-route', methods=['POST'])
def smart_route_ai_request():
    """Smart route AI request berdasarkan kebutuhan context"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Request data tidak ditemukan'
            }), 400
        
        query = data.get('question', '').strip()
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Pertanyaan tidak boleh kosong'
            }), 400
        
        # Get parameters
        context_type = data.get('context_type')
        force_service = data.get('force_service')
        use_cache = data.get('use_cache', True)
        
        # Use smart routing service
        routing_service = get_smart_routing_service()
        response = routing_service.route_ai_request(
            query=query,
            context_type=context_type,
            force_service=force_service,
            use_cache=use_cache
        )
        
        logger.info(f"✅ Smart routing completed successfully: {query[:50]}...")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error in smart routing: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@standalone_ai_bp.route('/smart-route-vision', methods=['POST'])
def smart_route_vision_request():
    """Smart route vision request berdasarkan kebutuhan context"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Request data tidak ditemukan'
            }), 400
        
        query = data.get('question', '').strip()
        image_base64 = data.get('image_base64', '').strip()
        
        if not image_base64:
            return jsonify({
                'status': 'error',
                'message': 'Image base64 tidak boleh kosong'
            }), 400
        
        # Get parameters
        context_type = data.get('context_type')
        force_service = data.get('force_service')
        use_cache = data.get('use_cache', True)
        
        # Use smart routing service untuk vision
        routing_service = get_smart_routing_service()
        response = routing_service.route_vision_request(
            query=query,
            image_base64=image_base64,
            context_type=context_type,
            force_service=force_service,
            use_cache=use_cache
        )
        
        logger.info(f"✅ Smart vision routing completed successfully")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error in smart vision routing: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@standalone_ai_bp.route('/status', methods=['GET'])
def get_standalone_service_status():
    """Get status dari smart routing service"""
    try:
        routing_service = get_smart_routing_service()
        stats = routing_service.get_routing_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ Error getting service status: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@standalone_ai_bp.route('/routing-stats', methods=['GET'])
def get_routing_stats():
    """Get routing statistics dari smart routing service"""
    try:
        routing_service = get_smart_routing_service()
        stats = routing_service.get_routing_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ Error getting routing stats: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@standalone_ai_bp.route('/test-routing', methods=['POST'])
def test_routing():
    """Test routing dengan berbagai query untuk validasi"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Request data tidak ditemukan'
            }), 400
        
        test_queries = data.get('test_queries', [])
        if not test_queries or not isinstance(test_queries, list):
            return jsonify({
                'status': 'error',
                'message': 'Test queries harus berupa array'
            }), 400
        
        # Use smart routing service
        routing_service = get_smart_routing_service()
        results = routing_service.test_routing(test_queries)
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"❌ Error in test routing: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@standalone_ai_bp.route('/clear-cache', methods=['POST'])
def clear_standalone_cache():
    """Clear cache dari routing service"""
    try:
        routing_service = get_smart_routing_service()
        routing_service.clear_routing_cache()
        
        return jsonify({
            'status': 'success',
            'message': 'Cache berhasil dibersihkan'
        })
        
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@standalone_ai_bp.route('/cache-stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics dari routing service"""
    try:
        routing_service = get_smart_routing_service()
        stats = routing_service.get_routing_cache_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ Error getting cache stats: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@standalone_ai_bp.route('/routing-cache-stats', methods=['GET'])
def get_routing_cache_stats():
    """Get cache statistics dari smart routing service"""
    try:
        routing_service = get_smart_routing_service()
        stats = routing_service.get_routing_cache_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ Error getting routing cache stats: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@standalone_ai_bp.route('/clear-routing-cache', methods=['POST'])
def clear_routing_cache():
    """Clear cache dari smart routing service"""
    try:
        routing_service = get_smart_routing_service()
        routing_service.clear_routing_cache()
        
        return jsonify({
            'status': 'success',
            'message': 'Routing cache berhasil dibersihkan'
        })
        
    except Exception as e:
        logger.error(f"❌ Error clearing routing cache: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

