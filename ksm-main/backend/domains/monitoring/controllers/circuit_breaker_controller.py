#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Circuit Breaker Controller untuk Monitoring Domain
Monitoring dan management endpoints untuk circuit breakers
"""

from flask import Blueprint, jsonify, request
from shared.services.circuit_breaker import circuit_breaker_manager, get_agent_ai_circuit_breaker
from services.agent_ai_client import get_circuit_breaker_stats, reset_circuit_breaker
import logging

logger = logging.getLogger(__name__)

# Create blueprint
circuit_breaker_bp = Blueprint('circuit_breaker', __name__, url_prefix='/api/v1/circuit-breaker')

@circuit_breaker_bp.route('/stats', methods=['GET'])
def get_circuit_breaker_stats():
    """Get circuit breaker statistics"""
    try:
        stats = circuit_breaker_manager.get_all_stats()
        
        # Convert stats to serializable format
        serializable_stats = {}
        for name, stat in stats.items():
            serializable_stats[name] = {
                'state': stat.state.value,
                'failure_count': stat.failure_count,
                'success_count': stat.success_count,
                'last_failure_time': stat.last_failure_time.isoformat() if stat.last_failure_time else None,
                'last_success_time': stat.last_success_time.isoformat() if stat.last_success_time else None,
                'total_requests': stat.total_requests,
                'total_failures': stat.total_failures,
                'total_successes': stat.total_successes,
                'last_state_change': stat.last_state_change.isoformat()
            }
        
        return jsonify({
            'circuit_breakers': serializable_stats,
            'total_circuit_breakers': len(serializable_stats)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get circuit breaker stats: {e}")
        return jsonify({
            'error': 'Failed to get circuit breaker statistics',
            'message': str(e)
        }), 500

@circuit_breaker_bp.route('/agent-ai/stats', methods=['GET'])
def get_agent_ai_circuit_breaker_stats():
    """Get Agent AI circuit breaker statistics"""
    try:
        stats = get_circuit_breaker_stats()
        
        return jsonify({
            'circuit_breaker': 'agent_ai',
            'state': stats.state.value,
            'failure_count': stats.failure_count,
            'success_count': stats.success_count,
            'last_failure_time': stats.last_failure_time.isoformat() if stats.last_failure_time else None,
            'last_success_time': stats.last_success_time.isoformat() if stats.last_success_time else None,
            'total_requests': stats.total_requests,
            'total_failures': stats.total_failures,
            'total_successes': stats.total_successes,
            'last_state_change': stats.last_state_change.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get Agent AI circuit breaker stats: {e}")
        return jsonify({
            'error': 'Failed to get Agent AI circuit breaker statistics',
            'message': str(e)
        }), 500

@circuit_breaker_bp.route('/agent-ai/reset', methods=['POST'])
def reset_agent_ai_circuit_breaker():
    """Reset Agent AI circuit breaker"""
    try:
        reset_circuit_breaker()
        
        return jsonify({
            'message': 'Agent AI circuit breaker reset successfully',
            'circuit_breaker': 'agent_ai'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to reset Agent AI circuit breaker: {e}")
        return jsonify({
            'error': 'Failed to reset Agent AI circuit breaker',
            'message': str(e)
        }), 500

@circuit_breaker_bp.route('/reset-all', methods=['POST'])
def reset_all_circuit_breakers():
    """Reset all circuit breakers"""
    try:
        circuit_breaker_manager.reset_all()
        
        return jsonify({
            'message': 'All circuit breakers reset successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to reset all circuit breakers: {e}")
        return jsonify({
            'error': 'Failed to reset all circuit breakers',
            'message': str(e)
        }), 500

@circuit_breaker_bp.route('/<circuit_name>/stats', methods=['GET'])
def get_specific_circuit_breaker_stats(circuit_name):
    """Get specific circuit breaker statistics"""
    try:
        cb = circuit_breaker_manager.get_circuit_breaker(circuit_name)
        stats = cb.get_stats()
        
        return jsonify({
            'circuit_breaker': circuit_name,
            'state': stats.state.value,
            'failure_count': stats.failure_count,
            'success_count': stats.success_count,
            'last_failure_time': stats.last_failure_time.isoformat() if stats.last_failure_time else None,
            'last_success_time': stats.last_success_time.isoformat() if stats.last_success_time else None,
            'total_requests': stats.total_requests,
            'total_failures': stats.total_failures,
            'total_successes': stats.total_successes,
            'last_state_change': stats.last_state_change.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get circuit breaker stats for {circuit_name}: {e}")
        return jsonify({
            'error': f'Failed to get circuit breaker statistics for {circuit_name}',
            'message': str(e)
        }), 500

@circuit_breaker_bp.route('/<circuit_name>/reset', methods=['POST'])
def reset_specific_circuit_breaker(circuit_name):
    """Reset specific circuit breaker"""
    try:
        cb = circuit_breaker_manager.get_circuit_breaker(circuit_name)
        cb.reset()
        
        return jsonify({
            'message': f'Circuit breaker {circuit_name} reset successfully',
            'circuit_breaker': circuit_name
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker {circuit_name}: {e}")
        return jsonify({
            'error': f'Failed to reset circuit breaker {circuit_name}',
            'message': str(e)
        }), 500

