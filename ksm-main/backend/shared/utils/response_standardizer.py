#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Response Standardizer - Utility untuk standardisasi response API
"""

from flask import jsonify
from datetime import datetime
import logging

class APIResponse:
    """Class untuk standardisasi response API"""
    
    @staticmethod
    def success(data=None, message="Success", status_code=200, total=None):
        """Response sukses"""
        response = {
            "success": True,
            "message": message,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        }
        
        if data is not None:
            response["data"] = data
        
        if total is not None:
            response["total"] = total
            
        return jsonify(response), status_code
    
    @staticmethod
    def error(message="Error", status_code=400, error_code=None, details=None):
        """Response error"""
        response = {
            "success": False,
            "message": message,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        }
        
        if error_code:
            response["error_code"] = error_code
            
        if details:
            response["details"] = details
            
        return jsonify(response), status_code
    
    @staticmethod
    def not_found(message="Resource not found"):
        """Response 404"""
        return APIResponse.error(message, 404)
    
    @staticmethod
    def unauthorized(message="Unauthorized"):
        """Response 401"""
        return APIResponse.error(message, 401)
    
    @staticmethod
    def forbidden(message="Forbidden"):
        """Response 403"""
        return APIResponse.error(message, 403)
    
    @staticmethod
    def server_error(message="Internal server error"):
        """Response 500"""
        return APIResponse.error(message, 500)
