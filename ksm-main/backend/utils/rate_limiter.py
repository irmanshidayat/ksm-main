#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rate Limiter - API rate limiting and abuse prevention
"""

import time
import logging
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for API endpoints"""
    
    def __init__(self):
        self.requests = defaultdict(lambda: defaultdict(deque))
        self.locks = defaultdict(threading.Lock)
        
        # Rate limit configurations
        self.limits = {
            'upload': {
                'requests_per_minute': 10,
                'requests_per_hour': 100,
                'requests_per_day': 500,
            },
            'download': {
                'requests_per_minute': 30,
                'requests_per_hour': 300,
                'requests_per_day': 1000,
            },
            'api': {
                'requests_per_minute': 60,
                'requests_per_hour': 1000,
                'requests_per_day': 5000,
            }
        }
    
    def is_allowed(self, user_id: str, endpoint: str, user_role: str = 'vendor') -> Tuple[bool, Dict]:
        """
        Check if request is allowed based on rate limits
        
        Returns:
            (is_allowed, rate_limit_info)
        """
        now = time.time()
        key = f"{user_id}:{endpoint}"
        
        with self.locks[key]:
            # Get rate limits for endpoint
            limits = self.limits.get(endpoint, self.limits['api'])
            
            # Adjust limits based on user role
            if user_role == 'admin':
                for limit_type in limits:
                    limits[limit_type] = int(limits[limit_type] * 2)
            elif user_role == 'super_admin':
                for limit_type in limits:
                    limits[limit_type] = int(limits[limit_type] * 5)
            
            # Clean old requests
            self._clean_old_requests(key, now)
            
            # Check rate limits
            rate_info = {
                'user_id': user_id,
                'endpoint': endpoint,
                'user_role': user_role,
                'timestamp': now,
                'limits': limits,
                'current_usage': {}
            }
            
            # Check minute limit
            minute_ago = now - 60
            minute_requests = [req_time for req_time in self.requests[key]['minute'] if req_time > minute_ago]
            rate_info['current_usage']['minute'] = len(minute_requests)
            
            if len(minute_requests) >= limits['requests_per_minute']:
                rate_info['retry_after'] = 60 - (now - minute_requests[0])
                return False, rate_info
            
            # Check hour limit
            hour_ago = now - 3600
            hour_requests = [req_time for req_time in self.requests[key]['hour'] if req_time > hour_ago]
            rate_info['current_usage']['hour'] = len(hour_requests)
            
            if len(hour_requests) >= limits['requests_per_hour']:
                rate_info['retry_after'] = 3600 - (now - hour_requests[0])
                return False, rate_info
            
            # Check day limit
            day_ago = now - 86400
            day_requests = [req_time for req_time in self.requests[key]['day'] if req_time > day_ago]
            rate_info['current_usage']['day'] = len(day_requests)
            
            if len(day_requests) >= limits['requests_per_day']:
                rate_info['retry_after'] = 86400 - (now - day_requests[0])
                return False, rate_info
            
            # Add current request
            self.requests[key]['minute'].append(now)
            self.requests[key]['hour'].append(now)
            self.requests[key]['day'].append(now)
            
            return True, rate_info
    
    def _clean_old_requests(self, key: str, now: float):
        """Clean old requests from memory"""
        # Keep only requests from the last day
        day_ago = now - 86400
        
        for period in ['minute', 'hour', 'day']:
            requests = self.requests[key][period]
            while requests and requests[0] < day_ago:
                requests.popleft()
    
    def get_usage_stats(self, user_id: str, endpoint: str) -> Dict:
        """Get current usage statistics for user"""
        key = f"{user_id}:{endpoint}"
        now = time.time()
        
        with self.locks[key]:
            self._clean_old_requests(key, now)
            
            minute_ago = now - 60
            hour_ago = now - 3600
            day_ago = now - 86400
            
            return {
                'minute': len([req for req in self.requests[key]['minute'] if req > minute_ago]),
                'hour': len([req for req in self.requests[key]['hour'] if req > hour_ago]),
                'day': len([req for req in self.requests[key]['day'] if req > day_ago]),
                'limits': self.limits.get(endpoint, self.limits['api'])
            }

class UploadRateLimiter:
    """Specialized rate limiter for file uploads"""
    
    def __init__(self):
        self.upload_sessions = defaultdict(dict)
        self.locks = defaultdict(threading.Lock)
        
        # Upload-specific limits
        self.upload_limits = {
            'vendor': {
                'max_concurrent_uploads': 3,
                'max_uploads_per_hour': 20,
                'max_total_size_per_hour': 100 * 1024 * 1024,  # 100MB
                'max_total_size_per_day': 500 * 1024 * 1024,   # 500MB
            },
            'admin': {
                'max_concurrent_uploads': 10,
                'max_uploads_per_hour': 100,
                'max_total_size_per_hour': 1000 * 1024 * 1024,  # 1GB
                'max_total_size_per_day': 5000 * 1024 * 1024,   # 5GB
            },
            'super_admin': {
                'max_concurrent_uploads': 20,
                'max_uploads_per_hour': 500,
                'max_total_size_per_hour': 5000 * 1024 * 1024,  # 5GB
                'max_total_size_per_day': 25000 * 1024 * 1024,  # 25GB
            }
        }
    
    def can_start_upload(self, user_id: str, user_role: str = 'vendor', file_size: int = 0) -> Tuple[bool, str, Dict]:
        """
        Check if user can start a new upload
        
        Returns:
            (can_upload, error_message, usage_info)
        """
        now = time.time()
        limits = self.upload_limits.get(user_role, self.upload_limits['vendor'])
        
        with self.locks[user_id]:
            session = self.upload_sessions[user_id]
            
            # Clean old data
            self._clean_old_uploads(user_id, now)
            
            # Check concurrent uploads
            active_uploads = len([upload for upload in session.get('uploads', {}).values() 
                                if upload.get('status') == 'active'])
            
            if active_uploads >= limits['max_concurrent_uploads']:
                return False, f"Terlalu banyak upload aktif. Maksimal {limits['max_concurrent_uploads']}", {}
            
            # Check hourly upload count
            hour_ago = now - 3600
            hourly_uploads = len([upload for upload in session.get('uploads', {}).values()
                                if upload.get('timestamp', 0) > hour_ago])
            
            if hourly_uploads >= limits['max_uploads_per_hour']:
                return False, f"Terlalu banyak upload per jam. Maksimal {limits['max_uploads_per_hour']}", {}
            
            # Check hourly size limit
            hourly_size = sum([upload.get('size', 0) for upload in session.get('uploads', {}).values()
                             if upload.get('timestamp', 0) > hour_ago])
            
            if hourly_size + file_size > limits['max_total_size_per_hour']:
                return False, f"Ukuran total upload per jam melebihi batas", {}
            
            # Check daily size limit
            day_ago = now - 86400
            daily_size = sum([upload.get('size', 0) for upload in session.get('uploads', {}).values()
                            if upload.get('timestamp', 0) > day_ago])
            
            if daily_size + file_size > limits['max_total_size_per_day']:
                return False, f"Ukuran total upload per hari melebihi batas", {}
            
            usage_info = {
                'active_uploads': active_uploads,
                'hourly_uploads': hourly_uploads,
                'hourly_size': hourly_size,
                'daily_size': daily_size,
                'limits': limits
            }
            
            return True, "", usage_info
    
    def start_upload(self, user_id: str, upload_id: str, file_size: int):
        """Mark upload as started"""
        now = time.time()
        
        with self.locks[user_id]:
            if 'uploads' not in self.upload_sessions[user_id]:
                self.upload_sessions[user_id]['uploads'] = {}
            
            self.upload_sessions[user_id]['uploads'][upload_id] = {
                'timestamp': now,
                'size': file_size,
                'status': 'active'
            }
    
    def finish_upload(self, user_id: str, upload_id: str):
        """Mark upload as finished"""
        with self.locks[user_id]:
            if upload_id in self.upload_sessions[user_id].get('uploads', {}):
                self.upload_sessions[user_id]['uploads'][upload_id]['status'] = 'completed'
    
    def cancel_upload(self, user_id: str, upload_id: str):
        """Mark upload as cancelled"""
        with self.locks[user_id]:
            if upload_id in self.upload_sessions[user_id].get('uploads', {}):
                del self.upload_sessions[user_id]['uploads'][upload_id]
    
    def _clean_old_uploads(self, user_id: str, now: float):
        """Clean old upload records"""
        day_ago = now - 86400
        
        if 'uploads' in self.upload_sessions[user_id]:
            uploads = self.upload_sessions[user_id]['uploads']
            expired_uploads = [upload_id for upload_id, upload in uploads.items()
                             if upload.get('timestamp', 0) < day_ago]
            
            for upload_id in expired_uploads:
                del uploads[upload_id]

# Decorator function untuk upload rate limiting
def upload_rate_limiter(f):
    """Decorator untuk rate limiting pada upload endpoints"""
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify
        from flask_jwt_extended import get_jwt_identity
        
        # Get user info
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User tidak terautentikasi'
            }), 401
        
        # Get user role (default to vendor)
        user_role = getattr(request, 'user_role', 'vendor')
        
        # Check if upload is allowed
        can_upload, error_msg, usage_info = upload_rate_limiter_instance.can_start_upload(
            user_id=str(user_id),
            user_role=user_role,
            file_size=0  # Will be updated when file size is known
        )
        
        if not can_upload:
            return jsonify({
                'success': False,
                'message': error_msg,
                'rate_limit_info': usage_info
            }), 429
        
        # Call original function
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

# Export singleton instances
rate_limiter = RateLimiter()
upload_rate_limiter_instance = UploadRateLimiter()
