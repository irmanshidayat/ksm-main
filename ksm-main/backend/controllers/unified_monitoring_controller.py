#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Monitoring Controller untuk KSM Main Backend
Menggantikan monitoring_controller.py dengan fungsionalitas yang lebih lengkap
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime

from services.unified_monitoring_service import get_unified_monitoring_service

# Initialize blueprint
unified_monitoring_bp = Blueprint('unified_monitoring', __name__)

# Initialize service
monitoring_service = get_unified_monitoring_service()

# Setup logging
logger = logging.getLogger(__name__)


@unified_monitoring_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get system metrics"""
    try:
        # Get window parameter
        window_minutes = request.args.get('window', 60, type=int)
        
        metrics = monitoring_service.get_metrics()
        
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"❌ Failed to get metrics: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_monitoring_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get system alerts"""
    try:
        # Get parameters
        limit = request.args.get('limit', 50, type=int)
        unresolved_only = request.args.get('unresolved_only', 'true').lower() == 'true'
        
        alerts = monitoring_service.get_alerts(
            limit=limit,
            unresolved_only=unresolved_only
        )
        
        return jsonify({
            'alerts': alerts,
            'total_count': len(alerts),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Failed to get alerts: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_monitoring_bp.route('/alerts/<alert_timestamp>/resolve', methods=['POST'])
def resolve_alert(alert_timestamp: str):
    """Resolve alert"""
    try:
        success = monitoring_service.resolve_alert(alert_timestamp)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Alert resolved successfully',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Alert not found',
                'timestamp': datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Failed to resolve alert: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_monitoring_bp.route('/embedding/metrics', methods=['GET'])
def get_embedding_metrics():
    """Get embedding service metrics"""
    try:
        result = monitoring_service.get_embedding_metrics()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"❌ Failed to get embedding metrics: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_monitoring_bp.route('/embedding/health', methods=['GET'])
def get_embedding_health():
    """Get embedding service health"""
    try:
        result = monitoring_service.get_embedding_health()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"❌ Failed to get embedding health: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_monitoring_bp.route('/embedding/clear-cache', methods=['POST'])
def clear_embedding_cache():
    """Clear embedding cache"""
    try:
        result = monitoring_service.clear_embedding_cache()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"❌ Failed to clear embedding cache: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_monitoring_bp.route('/export', methods=['GET'])
def export_metrics():
    """Export metrics data"""
    try:
        format_type = request.args.get('format', 'json')
        
        result = monitoring_service.export_metrics(format=format_type)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"❌ Failed to export metrics: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_monitoring_bp.route('/cleanup', methods=['POST'])
def cleanup_old_metrics():
    """Cleanup old metrics data"""
    try:
        days = request.json.get('days', 7) if request.json else 7
        
        result = monitoring_service.cleanup_old_metrics(days=days)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"❌ Failed to cleanup metrics: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_monitoring_bp.route('/rag/metrics', methods=['GET'])
def get_rag_metrics():
    """Get RAG system metrics"""
    try:
        days = request.args.get('days', 7, type=int)
        
        result = monitoring_service.get_rag_metrics(days=days)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"❌ Failed to get RAG metrics: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_monitoring_bp.route('/rag/health', methods=['GET'])
def get_rag_health():
    """Get RAG system health status"""
    try:
        result = monitoring_service.get_rag_health_status()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"❌ Failed to get RAG health: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_monitoring_bp.route('/system/status', methods=['GET'])
def get_system_status():
    """Get overall system status"""
    try:
        result = monitoring_service.get_system_status()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"❌ Failed to get system status: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


# Error handlers
@unified_monitoring_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'timestamp': datetime.now().isoformat()
    }), 404


@unified_monitoring_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'timestamp': datetime.now().isoformat()
    }), 500
