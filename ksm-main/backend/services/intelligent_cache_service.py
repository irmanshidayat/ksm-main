#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intelligent Cache Service untuk KSM-Main Backend
Service untuk intelligent caching dengan integrasi Agent AI
"""

import logging
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
import threading
from collections import OrderedDict

# Setup logging
logger = logging.getLogger(__name__)

class IntelligentCacheService:
    """Service untuk intelligent caching dengan Agent AI integration"""
    
    def __init__(self):
        self.enabled = os.getenv('ENABLE_INTELLIGENT_CACHE', 'true').lower() == 'true'
        self.max_size = int(os.getenv('CACHE_MAX_SIZE', '1000'))
        self.default_ttl = int(os.getenv('CACHE_DEFAULT_TTL', '3600'))  # 1 hour
        self.agent_ai_url = os.getenv('AGENT_AI_URL', 'http://localhost:5000')
        self.agent_ai_api_key = os.getenv('AGENT_AI_API_KEY', 'KSM_api_key_2ptybn')
        
        # Cache storage
        self.cache = OrderedDict()
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
        
        # Thread lock for thread safety
        self.lock = threading.Lock()
        
        # Start cleanup thread
        if self.enabled:
            self._start_cleanup_thread()
        
        logger.info(f"✅ Intelligent Cache Service initialized (enabled: {self.enabled})")
    
    def _start_cleanup_thread(self):
        """Start cache cleanup thread"""
        try:
            cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
            cleanup_thread.start()
            logger.info("✅ Cache cleanup thread started")
        except Exception as e:
            logger.error(f"❌ Failed to start cache cleanup thread: {e}")
    
    def _cleanup_expired(self):
        """Cleanup expired cache entries"""
        import time
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                with self.lock:
                    current_time = datetime.now()
                    expired_keys = []
                    
                    for key, value in self.cache.items():
                        if value.get('expires_at') and current_time > value['expires_at']:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        del self.cache[key]
                        self.cache_stats['evictions'] += 1
                    
                    if expired_keys:
                        logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
                        
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    def _generate_key(self, data: Union[str, Dict[str, Any]]) -> str:
        """Generate cache key from data"""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def generate_cache_key(self, prefix: str, *args) -> str:
        """Generate cache key with prefix and arguments"""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return self._generate_key(key_data)
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            with self.lock:
                if key in self.cache:
                    value = self.cache[key]
                    
                    # Check if expired
                    if value.get('expires_at') and datetime.now() > value['expires_at']:
                        del self.cache[key]
                        self.cache_stats['misses'] += 1
                        return None
                    
                    # Move to end (LRU)
                    self.cache.move_to_end(key)
                    self.cache_stats['hits'] += 1
                    
                    logger.debug(f"✅ Cache hit for key: {key}")
                    return value.get('data')
                else:
                    self.cache_stats['misses'] += 1
                    logger.debug(f"❌ Cache miss for key: {key}")
                    return None
                    
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.enabled:
            return False
        
        try:
            with self.lock:
                # Calculate expiration time
                expires_at = None
                if ttl:
                    expires_at = datetime.now() + timedelta(seconds=ttl)
                elif self.default_ttl:
                    expires_at = datetime.now() + timedelta(seconds=self.default_ttl)
                
                # Create cache entry
                cache_entry = {
                    'data': value,
                    'created_at': datetime.now(),
                    'expires_at': expires_at,
                    'access_count': 0
                }
                
                # Check cache size limit
                if len(self.cache) >= self.max_size and key not in self.cache:
                    # Remove oldest entry (LRU)
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    self.cache_stats['evictions'] += 1
                
                # Set cache entry
                self.cache[key] = cache_entry
                self.cache_stats['sets'] += 1
                
                logger.debug(f"✅ Cache set for key: {key}")
                return True
                
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.enabled:
            return False
        
        try:
            with self.lock:
                if key in self.cache:
                    del self.cache[key]
                    self.cache_stats['deletes'] += 1
                    logger.debug(f"✅ Cache delete for key: {key}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache"""
        if not self.enabled:
            return False
        
        try:
            with self.lock:
                self.cache.clear()
                logger.info("🧹 Cache cleared")
                return True
                
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_or_set(self, key: str, func, ttl: Optional[int] = None, *args, **kwargs) -> Any:
        """Get from cache or set using function"""
        # Try to get from cache first
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Execute function and cache result
        try:
            result = func(*args, **kwargs)
            self.set(key, result, ttl)
            return result
        except Exception as e:
            logger.error(f"Cache get_or_set error: {e}")
            raise
    
    def cache_agent_ai_response(self, query: str, response: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache Agent AI response"""
        try:
            cache_key = f"agent_ai:{self._generate_key(query)}"
            return self.set(cache_key, response, ttl or 1800)  # Default 30 minutes
        except Exception as e:
            logger.error(f"Cache Agent AI response error: {e}")
            return False
    
    def get_cached_agent_ai_response(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached Agent AI response"""
        try:
            cache_key = f"agent_ai:{self._generate_key(query)}"
            return self.get(cache_key)
        except Exception as e:
            logger.error(f"Get cached Agent AI response error: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / max(total_requests, 1)) * 100
        
        return {
            'enabled': self.enabled,
            'max_size': self.max_size,
            'current_size': len(self.cache),
            'default_ttl': self.default_ttl,
            'stats': self.cache_stats.copy(),
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        with self.lock:
            cache_info = []
            for key, value in list(self.cache.items())[:10]:  # Show first 10 entries
                cache_info.append({
                    'key': key,
                    'created_at': value['created_at'].isoformat(),
                    'expires_at': value['expires_at'].isoformat() if value['expires_at'] else None,
                    'access_count': value['access_count']
                })
        
        return {
            'cache_entries': cache_info,
            'total_entries': len(self.cache),
            'stats': self.get_stats(),
            'timestamp': datetime.now().isoformat()
        }

# Global intelligent cache service instance
intelligent_cache_service = IntelligentCacheService()

def get_intelligent_cache_service() -> IntelligentCacheService:
    """Get intelligent cache service instance"""
    return intelligent_cache_service
