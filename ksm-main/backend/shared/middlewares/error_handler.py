#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error Handler Middleware untuk KSM-Main Backend
Middleware untuk handling error dengan integrasi Agent AI
"""

import logging
import os
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify

# Setup logging
logger = logging.getLogger(__name__)

class ErrorHandler:
    """Error handler middleware dengan integrasi Agent AI"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.agent_ai_url = os.getenv('AGENT_AI_URL', 'http://localhost:5000')
        self.agent_ai_api_key = os.getenv('AGENT_AI_API_KEY', 'KSM_api_key_2ptybn')
        self.enabled = os.getenv('ENABLE_ERROR_HANDLING', 'true').lower() == 'true'
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize error handler with Flask app"""
        if not self.enabled:
            return
        
        # Register error handlers
        app.register_error_handler(400, self.handle_bad_request)
        app.register_error_handler(401, self.handle_unauthorized)
        app.register_error_handler(403, self.handle_forbidden)
        app.register_error_handler(404, self.handle_not_found)
        app.register_error_handler(405, self.handle_method_not_allowed)
        app.register_error_handler(500, self.handle_internal_error)
        app.register_error_handler(Exception, self.handle_general_error)
        
        logger.info("✅ Error Handler middleware initialized")
    
    def handle_bad_request(self, error):
        """Handle 400 Bad Request errors"""
        return self._create_error_response(
            error_code=400,
            message="Bad Request",
            details=str(error),
            error_type="BadRequest"
        )
    
    def handle_unauthorized(self, error):
        """Handle 401 Unauthorized errors"""
        return self._create_error_response(
            error_code=401,
            message="Unauthorized",
            details="Authentication required",
            error_type="Unauthorized"
        )
    
    def handle_forbidden(self, error):
        """Handle 403 Forbidden errors"""
        return self._create_error_response(
            error_code=403,
            message="Forbidden",
            details="Access denied",
            error_type="Forbidden"
        )
    
    def handle_not_found(self, error):
        """Handle 404 Not Found errors"""
        return self._create_error_response(
            error_code=404,
            message="Not Found",
            details="The requested resource was not found",
            error_type="NotFound"
        )
    
    def handle_method_not_allowed(self, error):
        """Handle 405 Method Not Allowed errors"""
        return self._create_error_response(
            error_code=405,
            message="Method Not Allowed",
            details="The requested method is not allowed for this resource",
            error_type="MethodNotAllowed"
        )
    
    def handle_internal_error(self, error):
        """Handle 500 Internal Server Error"""
        return self._create_error_response(
            error_code=500,
            message="Internal Server Error",
            details="An internal server error occurred",
            error_type="InternalError"
        )
    
    def handle_general_error(self, error):
        """Handle general exceptions"""
        return self._create_error_response(
            error_code=500,
            message="Internal Server Error",
            details=str(error),
            error_type="GeneralError"
        )
    
    def _create_error_response(self, 
                              error_code: int, 
                              message: str, 
                              details: str, 
                              error_type: str) -> tuple:
        """Create standardized error response"""
        error_data = {
            'success': False,
            'error': {
                'code': error_code,
                'type': error_type,
                'message': message,
                'details': details,
                'timestamp': datetime.now().isoformat(),
                'request_id': self._get_request_id(),
                'path': request.path if request else None,
                'method': request.method if request else None
            },
            'status_code': error_code
        }
        
        # Log error
        logger.error(f"Error {error_code}: {message} - {details}")
        
        # Try to enhance error with Agent AI if available
        if self.enabled and error_code >= 500:
            enhanced_error = self._enhance_error_with_agent_ai(error_data)
            if enhanced_error:
                error_data['error']['suggestions'] = enhanced_error.get('suggestions', [])
                error_data['error']['enhanced'] = True
        
        return jsonify(error_data), error_code
    
    def _get_request_id(self) -> str:
        """Generate or get request ID"""
        if request and hasattr(request, 'request_id'):
            return request.request_id
        return f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _enhance_error_with_agent_ai(self, error_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhance error with Agent AI suggestions"""
        try:
            payload = {
                'error_data': error_data,
                'task': 'error_analysis',
                'company_id': 'KSM_main',
                'client_id': 'error_handler',
                'company_name': 'KSM Grup',
                'instructions': 'Analyze the error and provide helpful suggestions for resolution'
            }
            
            response = requests.post(
                f"{self.agent_ai_url}/api/langchain/process",
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'X-API-Key': self.agent_ai_api_key
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('data', {})
            else:
                logger.warning(f"Agent AI error enhancement failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Agent AI error enhancement error: {e}")
            return None
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log error with context"""
        try:
            error_info = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'timestamp': datetime.now().isoformat(),
                'context': context or {},
                'request_path': request.path if request else None,
                'request_method': request.method if request else None,
                'user_agent': request.headers.get('User-Agent') if request else None
            }
            
            logger.error(f"Error logged: {error_info}")
            
            # Send to Agent AI for analysis if enabled
            if self.enabled:
                self._send_error_to_agent_ai(error_info)
                
        except Exception as e:
            logger.error(f"Error logging failed: {e}")
    
    def _send_error_to_agent_ai(self, error_info: Dict[str, Any]):
        """Send error information to Agent AI for analysis"""
        try:
            payload = {
                'error_info': error_info,
                'task': 'error_logging',
                'company_id': 'KSM_main',
                'client_id': 'error_handler',
                'company_name': 'KSM Grup',
                'instructions': 'Log and analyze this error for monitoring purposes'
            }
            
            requests.post(
                f"{self.agent_ai_url}/api/langchain/process",
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'X-API-Key': self.agent_ai_api_key
                },
                timeout=5
            )
            
        except Exception as e:
            logger.error(f"Failed to send error to Agent AI: {e}")

# Global error handler instance
error_handler = ErrorHandler()

def get_error_handler() -> ErrorHandler:
    """Get error handler instance"""
    return error_handler
