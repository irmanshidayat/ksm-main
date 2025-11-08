#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validators untuk Agent AI
"""

import logging
from typing import Dict, Any, List
from config.config import Config

logger = logging.getLogger(__name__)

def validate_telegram_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate Telegram request data"""
    errors = []
    
    # Check required fields
    if not data.get('user_id'):
        errors.append('user_id is required')
    elif not isinstance(data.get('user_id'), int):
        errors.append('user_id must be an integer')
    
    if not data.get('message'):
        errors.append('message is required')
    elif not isinstance(data.get('message'), str):
        errors.append('message must be a string')
    elif len(data.get('message', '')) > Config.MAX_MESSAGE_LENGTH:
        errors.append(f'message too long (max {Config.MAX_MESSAGE_LENGTH} characters)')
    
    # Optional fields validation
    if 'session_id' in data and not isinstance(data.get('session_id'), str):
        errors.append('session_id must be a string')
    
    if 'source' in data and not isinstance(data.get('source'), str):
        errors.append('source must be a string')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_rag_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate RAG request data"""
    errors = []
    
    # Check required fields
    if not data.get('user_id'):
        errors.append('user_id is required')
    elif not isinstance(data.get('user_id'), int):
        errors.append('user_id must be an integer')
    
    if not data.get('message'):
        errors.append('message is required')
    elif not isinstance(data.get('message'), str):
        errors.append('message must be a string')
    elif len(data.get('message', '')) > Config.MAX_MESSAGE_LENGTH:
        errors.append(f'message too long (max {Config.MAX_MESSAGE_LENGTH} characters)')
    
    # Validate context
    context = data.get('context', {})
    if not isinstance(context, dict):
        errors.append('context must be a dictionary')
    else:
        # Validate context structure
        if 'rag_results' in context and not isinstance(context.get('rag_results'), list):
            errors.append('context.rag_results must be a list')
        
        if 'total_chunks' in context and not isinstance(context.get('total_chunks'), int):
            errors.append('context.total_chunks must be an integer')
        
        if 'avg_similarity' in context and not isinstance(context.get('avg_similarity'), (int, float)):
            errors.append('context.avg_similarity must be a number')
    
    # Optional fields validation
    if 'session_id' in data and not isinstance(data.get('session_id'), str):
        errors.append('session_id must be a string')
    
    if 'source' in data and not isinstance(data.get('source'), str):
        errors.append('source must be a string')
    
    if 'metadata' in data and not isinstance(data.get('metadata'), dict):
        errors.append('metadata must be a dictionary')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_context_data(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate RAG context data"""
    errors = []
    
    # Check required fields
    if 'rag_results' not in context:
        errors.append('rag_results is required')
    elif not isinstance(context.get('rag_results'), list):
        errors.append('rag_results must be a list')
    else:
        # Validate each result
        for i, result in enumerate(context.get('rag_results', [])):
            if not isinstance(result, dict):
                errors.append(f'rag_results[{i}] must be a dictionary')
                continue
            
            if 'content' not in result:
                errors.append(f'rag_results[{i}].content is required')
            elif not isinstance(result.get('content'), str):
                errors.append(f'rag_results[{i}].content must be a string')
            
            if 'similarity' not in result:
                errors.append(f'rag_results[{i}].similarity is required')
            elif not isinstance(result.get('similarity'), (int, float)):
                errors.append(f'rag_results[{i}].similarity must be a number')
    
    if 'total_chunks' not in context:
        errors.append('total_chunks is required')
    elif not isinstance(context.get('total_chunks'), int):
        errors.append('total_chunks must be an integer')
    
    if 'avg_similarity' not in context:
        errors.append('avg_similarity is required')
    elif not isinstance(context.get('avg_similarity'), (int, float)):
        errors.append('avg_similarity must be a number')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def sanitize_input(text: str) -> str:
    """Sanitize input text"""
    if not isinstance(text, str):
        return ""
    
    # Remove potentially harmful characters
    sanitized = text.strip()
    
    # Limit length
    if len(sanitized) > Config.MAX_MESSAGE_LENGTH:
        sanitized = sanitized[:Config.MAX_MESSAGE_LENGTH]
    
    return sanitized

def validate_api_key(api_key: str) -> bool:
    """Validate API key format"""
    if not api_key:
        return False
    
    # Basic validation - should be non-empty string
    if not isinstance(api_key, str) or len(api_key) < 10:
        return False
    
    return True
