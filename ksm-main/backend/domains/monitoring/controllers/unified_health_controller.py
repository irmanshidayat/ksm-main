#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Health Controller untuk KSM Main Backend
Menggantikan semua health check endpoints yang tersebar
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime

from domains.monitoring.services.unified_health_service import get_unified_health_service

# Initialize blueprint
unified_health_bp = Blueprint('unified_health', __name__)

# Initialize service
health_service = get_unified_health_service()

# Setup logging
logger = logging.getLogger(__name__)


@unified_health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Unified health check endpoint
    Menggantikan semua health check endpoints yang tersebar
    """
    try:
        # Get query parameters
        detailed = request.args.get('detailed', 'false').lower() == 'true'
        service = request.args.get('service', None)
        
        # If specific service requested
        if service:
            result = health_service.get_service_health(service)
            return jsonify(result), 200 if result.get('success') else 500
        
        # Get comprehensive or simple health check
        if detailed:
            result = health_service.get_comprehensive_health(include_details=True)
        else:
            result = health_service.get_simple_health()
        
        return jsonify(result), 200 if result.get('success') else 500
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'Health check failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_health_bp.route('/health/comprehensive', methods=['GET'])
def comprehensive_health_check():
    """
    Comprehensive health check endpoint
    Detailed health status for all services
    """
    try:
        result = health_service.get_comprehensive_health(include_details=True)
        return jsonify(result), 200 if result.get('success') else 500
        
    except Exception as e:
        logger.error(f"❌ Comprehensive health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'Comprehensive health check failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_health_bp.route('/health/simple', methods=['GET'])
def simple_health_check():
    """
    Simple health check endpoint
    Basic health status for quick checks
    """
    try:
        result = health_service.get_simple_health()
        return jsonify(result), 200 if result.get('success') else 500
        
    except Exception as e:
        logger.error(f"❌ Simple health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'Simple health check failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_health_bp.route('/health/service/<service_name>', methods=['GET'])
def service_health_check(service_name):
    """
    Health check for specific service
    """
    try:
        result = health_service.get_service_health(service_name)
        return jsonify(result), 200 if result.get('success') else 500
        
    except Exception as e:
        logger.error(f"❌ Service health check failed for {service_name}: {e}")
        return jsonify({
            'success': False,
            'service': service_name,
            'status': 'error',
            'message': f'Service health check failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@unified_health_bp.route('/health/status', methods=['GET'])
def health_status():
    """
    Health status endpoint for monitoring systems
    """
    try:
        result = health_service.get_comprehensive_health(include_details=False)
        
        # Return simplified status for monitoring
        return jsonify({
            'status': result.get('overall_status', 'unknown'),
            'health_percentage': result.get('health_percentage', 0),
            'healthy_services': result.get('healthy_services', 0),
            'total_services': result.get('total_services', 0),
            'timestamp': result.get('timestamp')
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Health status check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Health status check failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500
