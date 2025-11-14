#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone AI Controller untuk Knowledge Domain
Routes untuk fitur AI standalone dan smart routing
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Any
import sys
import os

logger = logging.getLogger(__name__)

def safe_import_service(service_name, function_name):
    """Safe import service dengan fallback untuk relative import"""
    # Mapping service name ke domain path
    service_mapping = {
        "smart_routing_service": "domains.knowledge.services.smart_routing_service",
        "enhanced_ai_service": "services.enhanced_ai_service"  # Keep for backward compatibility
    }
    
    # Try domain import first
    if service_name in service_mapping:
        try:
            module = __import__(service_mapping[service_name], fromlist=[function_name])
            return getattr(module, function_name)
        except ImportError:
            pass
    
    # Try absolute import from services (for backward compatibility)
    try:
        module = __import__(f"services.{service_name}", fromlist=[function_name])
        return getattr(module, function_name)
    except ImportError:
        # Fallback untuk relative import
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        try:
            module = __import__(f"services.{service_name}", fromlist=[function_name])
            return getattr(module, function_name)
        except ImportError:
            # Last resort: direct import
            sys.path.append(current_dir)
            module = __import__(service_name, fromlist=[function_name])
            return getattr(module, function_name)

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
        model = data.get('model')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 2048))
        use_cache = data.get('use_cache', True)
        
        # Import service
        get_standalone_openrouter_service = safe_import_service("enhanced_ai_service", "get_standalone_openrouter_service")
        service = get_standalone_openrouter_service()
        
        # Generate response
        response = service.generate_standalone_response(
            query=query,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
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
        system_prompt = data.get('system_prompt', 'Anda adalah asisten AI dengan kemampuan vision untuk menganalisis gambar.')
        temperature = float(data.get('temperature', 0.3))
        max_tokens = int(data.get('max_tokens', 2048))
        use_cache = data.get('use_cache', True)
        
        # Import service
        get_standalone_openrouter_service = safe_import_service("enhanced_ai_service", "get_standalone_openrouter_service")
        service = get_standalone_openrouter_service()
        
        # Generate vision response
        response = service.generate_standalone_vision_response(
            query=query,
            image_base64=image_base64,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
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
        
        # Import service
        get_smart_routing_service = safe_import_service("smart_routing_service", "get_smart_routing_service")
        service = get_smart_routing_service()
        
        # Route request
        response = service.route_ai_request(
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
        
        # Import service
        get_smart_routing_service = safe_import_service("smart_routing_service", "get_smart_routing_service")
        service = get_smart_routing_service()
        
        # Route vision request
        response = service.route_vision_request(
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
    """Get status dari standalone OpenRouter service"""
    try:
        get_standalone_openrouter_service = safe_import_service("enhanced_ai_service", "get_standalone_openrouter_service")
        service = get_standalone_openrouter_service()
        
        status = service.get_service_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"❌ Error getting standalone service status: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@standalone_ai_bp.route('/routing-stats', methods=['GET'])
def get_routing_stats():
    """Get routing statistics dari smart routing service"""
    try:
        get_smart_routing_service = safe_import_service("smart_routing_service", "get_smart_routing_service")
        service = get_smart_routing_service()
        
        stats = service.get_routing_stats()
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
        
        # Import service
        get_smart_routing_service = safe_import_service("smart_routing_service", "get_smart_routing_service")
        service = get_smart_routing_service()
        
        # Test routing
        results = service.test_routing(test_queries)
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"❌ Error in test routing: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@standalone_ai_bp.route('/clear-cache', methods=['POST'])
def clear_standalone_cache():
    """Clear cache dari standalone OpenRouter service"""
    try:
        get_standalone_openrouter_service = safe_import_service("enhanced_ai_service", "get_standalone_openrouter_service")
        service = get_standalone_openrouter_service()
        
        service.clear_cache()
        
        return jsonify({
            'status': 'success',
            'message': 'Cache berhasil dibersihkan'
        })
        
    except Exception as e:
        logger.error(f"❌ Error clearing standalone cache: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@standalone_ai_bp.route('/cache-stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics dari standalone OpenRouter service"""
    try:
        get_standalone_openrouter_service = safe_import_service("enhanced_ai_service", "get_standalone_openrouter_service")
        service = get_standalone_openrouter_service()
        
        stats = service.get_cache_stats()
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
        get_smart_routing_service = safe_import_service("smart_routing_service", "get_smart_routing_service")
        service = get_smart_routing_service()
        
        stats = service.get_routing_cache_stats()
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
        get_smart_routing_service = safe_import_service("smart_routing_service", "get_smart_routing_service")
        service = get_smart_routing_service()
        
        service.clear_routing_cache()
        
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

