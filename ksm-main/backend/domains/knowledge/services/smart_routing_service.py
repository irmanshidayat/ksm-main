#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Routing Service untuk KSM Main Backend
Service untuk routing request AI berdasarkan kebutuhan context database
"""

import os
import time
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class SmartRoutingService:
    """Service untuk smart routing AI requests berdasarkan kebutuhan context"""
    
    def __init__(self):
        # Import services
        try:
            # unified_ai_service removed - using Agent AI directly
            from domains.integration.services.agent_ai_sync_service import get_agent_ai_sync_service
            
            self.standalone_service = None  # Removed
            self.agent_ai_service = get_agent_ai_sync_service()
            
            logger.info("🚀 Smart Routing Service initialized successfully")
        except ImportError:
            try:
                # Fallback untuk relative import
                import sys
                import os
                current_dir = os.path.dirname(os.path.abspath(__file__))
                if current_dir not in sys.path:
                    sys.path.append(current_dir)
                
                # unified_ai_service removed - using Agent AI directly
                from domains.integration.services.agent_ai_sync_service import get_agent_ai_sync_service
                
                self.standalone_service = None  # Removed
                self.agent_ai_service = get_agent_ai_sync_service()
                
                logger.info("🚀 Smart Routing Service initialized successfully (fallback)")
            except ImportError as e:
                logger.error(f"❌ Failed to import required services: {e}")
                self.standalone_service = None
                self.agent_ai_service = None
        
        # Cache untuk routing responses
        self._routing_cache = {}
        self._routing_cache_ttl = 600  # 10 menit
        
        # Fallback protection
        self._fallback_count = 0
        self._max_fallbacks = 2
    
    def _analyze_query_context(self, query: str, context_type: str = None) -> Dict[str, Any]:
        """Analyze query untuk menentukan apakah butuh context database"""
        query_lower = query.lower()
        
        # Keywords yang menunjukkan butuh context database
        context_keywords = [
            'stok', 'barang', 'inventory', 'produk', 'item',
            'customer', 'pelanggan', 'klien', 'client',
            'order', 'pesanan', 'transaksi', 'penjualan',
            'database', 'data', 'record', 'history',
            'KSM', 'perusahaan', 'company', 'business',
            'laporan', 'report', 'analisis', 'statistik'
        ]
        
        # Keywords yang menunjukkan standalone query
        standalone_keywords = [
            'apa', 'bagaimana', 'jelaskan', 'definisi',
            'contoh', 'tutorial', 'cara', 'tips',
            'umum', 'general', 'pengetahuan', 'ilmu',
            'matematika', 'sains', 'teknologi', 'art'
        ]
        
        # Check context keywords
        context_score = sum(1 for keyword in context_keywords if keyword in query_lower)
        standalone_score = sum(1 for keyword in standalone_keywords if keyword in query_lower)
        
        # Determine routing decision
        needs_context = context_score > standalone_score
        
        # Override based on context_type if provided
        if context_type:
            if context_type in ['database', 'business', 'KSM']:
                needs_context = True
            elif context_type in ['general', 'standalone', 'knowledge']:
                needs_context = False
        
        return {
            'needs_context': needs_context,
            'context_score': context_score,
            'standalone_score': standalone_score,
            'recommended_service': 'agent_ai' if needs_context else 'standalone',
            'reasoning': f"Context score: {context_score}, Standalone score: {standalone_score}"
        }
    
    def route_ai_request(self, query: str, 
                         context_type: str = None,
                         force_service: str = None,
                         use_cache: bool = True) -> Dict[str, Any]:
        """Route AI request ke service yang sesuai"""
        start_time = time.time()
        
        try:
            # Check cache first if enabled
            if use_cache:
                cache_key = self._get_routing_cache_key(query, context_type, force_service)
                cached_response = self._get_cached_routing_response(cache_key)
                if cached_response:
                    logger.info("📋 Using cached routing response")
                    return cached_response
            
            # Force specific service if requested
            if force_service:
                logger.info(f"🔄 Force routing to {force_service} service")
                if force_service == 'standalone':
                    return self._handle_standalone_request(query, start_time, use_cache)
                elif force_service == 'agent_ai':
                    return self._handle_agent_ai_request(query, start_time, use_cache)
                else:
                    logger.warning(f"⚠️ Unknown force service: {force_service}")
            
            # Analyze query for smart routing
            context_analysis = self._analyze_query_context(query, context_type)
            logger.info(f"🧠 Smart routing analysis: {context_analysis}")
            
            # Route based on analysis
            if context_analysis['needs_context']:
                logger.info("🔄 Routing to Agent AI (needs context)")
                return self._handle_agent_ai_request(query, start_time, use_cache)
            else:
                logger.info("🔄 Routing to Standalone OpenRouter (no context needed)")
                return self._handle_standalone_request(query, start_time, use_cache)
                
        except Exception as e:
            logger.error(f"❌ Error in smart routing: {e}")
            return self._generate_routing_error_response(query, start_time, str(e))
    
    def _handle_standalone_request(self, query: str, start_time: float, use_cache: bool) -> Dict[str, Any]:
        """Handle request menggunakan standalone OpenRouter service"""
        try:
            if not self.standalone_service:
                logger.warning("⚠️ Standalone service not available, falling back to Agent AI")
                return self._handle_agent_ai_request(query, start_time, use_cache)
            
            # Use standalone service
            response = self.standalone_service.generate_standalone_response(
                query=query,
                use_cache=use_cache
            )
            
            # Add routing metadata
            response['routing_info'] = {
                'service_used': 'standalone_openrouter',
                'routing_method': 'smart_analysis',
                'routing_time': time.time() - start_time
            }
            
            # Cache response untuk reuse
            if use_cache:
                self._cache_routing_response(query, response, 'standalone')
            
            # Reset fallback count on success
            self._fallback_count = 0
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in standalone request: {e}")
            # Check fallback limit
            if self._fallback_count < self._max_fallbacks:
                self._fallback_count += 1
                logger.warning(f"⚠️ Fallback attempt {self._fallback_count}/{self._max_fallbacks}")
                return self._handle_agent_ai_request(query, start_time, use_cache)
            else:
                logger.error("❌ Maximum fallbacks reached, returning error response")
                return self._generate_routing_error_response(query, start_time, f"Service unavailable after {self._max_fallbacks} fallbacks")
    
    def _handle_agent_ai_request(self, query: str, start_time: float, use_cache: bool) -> Dict[str, Any]:
        """Handle request menggunakan Agent AI service"""
        try:
            if not self.agent_ai_service:
                logger.warning("⚠️ Agent AI service not available, falling back to standalone")
                return self._handle_standalone_request(query, start_time, use_cache)
            
            # Use Agent AI service
            response = self.agent_ai_service.ask_question(
                question=query,
                use_cache=use_cache
            )
            
            # Add routing metadata
            response['routing_info'] = {
                'service_used': 'agent_ai',
                'routing_method': 'smart_analysis',
                'routing_time': time.time() - start_time
            }
            
            # Cache response untuk reuse
            if use_cache:
                self._cache_routing_response(query, response, 'agent_ai')
            
            # Reset fallback count on success
            self._fallback_count = 0
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in Agent AI request: {e}")
            # Check fallback limit
            if self._fallback_count < self._max_fallbacks:
                self._fallback_count += 1
                logger.warning(f"⚠️ Fallback attempt {self._fallback_count}/{self._max_fallbacks}")
                return self._handle_standalone_request(query, start_time, use_cache)
            else:
                logger.error("❌ Maximum fallbacks reached, returning error response")
                return self._generate_routing_error_response(query, start_time, f"Service unavailable after {self._max_fallbacks} fallbacks")
    
    def route_vision_request(self, query: str, image_base64: str,
                           context_type: str = None,
                           force_service: str = None,
                           use_cache: bool = True) -> Dict[str, Any]:
        """Route vision request ke service yang sesuai"""
        start_time = time.time()
        
        try:
            # Force specific service if requested
            if force_service:
                logger.info(f"🔄 Force routing vision request to {force_service} service")
                if force_service == 'standalone':
                    return self._handle_standalone_vision_request(query, image_base64, start_time, use_cache)
                elif force_service == 'agent_ai':
                    return self._handle_agent_ai_vision_request(query, image_base64, start_time, use_cache)
                else:
                    logger.warning(f"⚠️ Unknown force service for vision: {force_service}")
            
            # For vision requests, prefer standalone unless explicitly needs context
            if context_type and context_type in ['database', 'business', 'KSM']:
                logger.info("🔄 Routing vision request to Agent AI (needs business context)")
                return self._handle_agent_ai_vision_request(query, image_base64, start_time, use_cache)
            else:
                logger.info("🔄 Routing vision request to Standalone OpenRouter (general analysis)")
                return self._handle_standalone_vision_request(query, image_base64, start_time, use_cache)
                
        except Exception as e:
            logger.error(f"❌ Error in smart vision routing: {e}")
            return self._generate_routing_error_response(query, start_time, str(e))
    
    def _handle_standalone_vision_request(self, query: str, image_base64: str, 
                                        start_time: float, use_cache: bool) -> Dict[str, Any]:
        """Handle vision request menggunakan standalone OpenRouter service"""
        try:
            if not self.standalone_service:
                logger.warning("⚠️ Standalone vision service not available, falling back to Agent AI")
                return self._handle_agent_ai_vision_request(query, image_base64, start_time, use_cache)
            
            # Use standalone vision service
            response = self.standalone_service.generate_standalone_vision_response(
                query=query,
                image_base64=image_base64,
                use_cache=use_cache
            )
            
            # Add routing metadata
            response['routing_info'] = {
                'service_used': 'standalone_openrouter_vision',
                'routing_method': 'smart_analysis',
                'routing_time': time.time() - start_time
            }
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in standalone vision request: {e}")
            return self._handle_agent_ai_vision_request(query, image_base64, start_time, use_cache)
    
    def _handle_agent_ai_vision_request(self, query: str, image_base64: str,
                                      start_time: float, use_cache: bool) -> Dict[str, Any]:
        """Handle vision request menggunakan Agent AI service"""
        try:
            if not self.agent_ai_service:
                logger.warning("⚠️ Agent AI vision service not available, falling back to standalone")
                return self._handle_standalone_vision_request(query, image_base64, start_time, use_cache)
            
            # Use Agent AI vision service (if available)
            # For now, fallback to standalone
            logger.info("🔄 Agent AI vision service not implemented, using standalone")
            return self._handle_standalone_vision_request(query, image_base64, start_time, use_cache)
            
        except Exception as e:
            logger.error(f"❌ Error in Agent AI vision request: {e}")
            return self._generate_routing_error_response(query, start_time, str(e))
    
    def _get_routing_cache_key(self, query: str, context_type: str = None, force_service: str = None) -> str:
        """Generate cache key untuk routing request"""
        import hashlib
        cache_string = f"{query}:{context_type or 'auto'}:{force_service or 'auto'}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_cached_routing_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached routing response jika masih valid"""
        if cache_key in self._routing_cache:
            cached_data = self._routing_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self._routing_cache_ttl:
                logger.info("📋 Using cached routing response")
                return cached_data['response']
            else:
                # Cache expired, remove it
                del self._routing_cache[cache_key]
        return None
    
    def _cache_routing_response(self, query: str, response: Dict[str, Any], service_type: str):
        """Cache routing response untuk reuse"""
        cache_key = self._get_routing_cache_key(query)
        self._routing_cache[cache_key] = {
            'response': response,
            'timestamp': time.time(),
            'service_type': service_type
        }
        logger.info(f"💾 Cached routing response from {service_type}")
    
    def _generate_routing_error_response(self, query: str, start_time: float, error_msg: str) -> Dict[str, Any]:
        """Generate error response jika routing gagal"""
        response_time = time.time() - start_time
        
        return {
            'status': 'error',
            'message': f'Maaf, terjadi kesalahan dalam routing request AI. Error: {error_msg}',
            'response_time': response_time,
            'routing_info': {
                'service_used': 'error',
                'routing_method': 'error_fallback',
                'routing_time': response_time,
                'error': error_msg
            }
        }
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics untuk monitoring"""
        try:
            standalone_status = self.standalone_service.get_service_status() if self.standalone_service else None
            agent_ai_status = self.agent_ai_service.get_service_status() if self.agent_ai_service else None
            
            # Get cache statistics
            current_time = time.time()
            valid_cache_count = sum(1 for data in self._routing_cache.values() 
                                   if current_time - data['timestamp'] < self._routing_cache_ttl)
            
            cache_stats = {
                'total_cached': len(self._routing_cache),
                'valid_cached': valid_cache_count,
                'expired_cached': len(self._routing_cache) - valid_cache_count,
                'cache_ttl_seconds': self._routing_cache_ttl
            }
            
            return {
                'service_name': 'Smart Routing Service',
                'status': 'available',
                'standalone_service_status': standalone_status,
                'agent_ai_service_status': agent_ai_status,
                'cache_stats': cache_stats,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Error getting routing stats: {e}")
            return {
                'service_name': 'Smart Routing Service',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def clear_routing_cache(self):
        """Clear semua cached routing responses"""
        self._routing_cache.clear()
        logger.info("🗑️ Cleared routing cache")
    
    def get_routing_cache_stats(self) -> Dict[str, Any]:
        """Get routing cache statistics"""
        current_time = time.time()
        valid_cache_count = sum(1 for data in self._routing_cache.values() 
                               if current_time - data['timestamp'] < self._routing_cache_ttl)
        
        # Group by service type
        service_counts = {}
        for data in self._routing_cache.values():
            service_type = data.get('service_type', 'unknown')
            service_counts[service_type] = service_counts.get(service_type, 0) + 1
        
        return {
            'total_cached': len(self._routing_cache),
            'valid_cached': valid_cache_count,
            'expired_cached': len(self._routing_cache) - valid_cache_count,
            'cache_ttl_seconds': self._routing_cache_ttl,
            'service_distribution': service_counts
        }
    
    def test_routing(self, test_queries: List[str]) -> Dict[str, Any]:
        """Test routing dengan berbagai query untuk validasi"""
        results = {}
        
        for query in test_queries:
            try:
                analysis = self._analyze_query_context(query)
                results[query] = {
                    'analysis': analysis,
                    'routing_test': self.route_ai_request(query, force_service=None)
                }
            except Exception as e:
                results[query] = {
                    'error': str(e),
                    'analysis': None,
                    'routing_test': None
                }
        
        return {
            'test_results': results,
            'total_tested': len(test_queries),
            'timestamp': datetime.now().isoformat()
        }

# Global instance
smart_routing_service = SmartRoutingService()

def get_smart_routing_service() -> SmartRoutingService:
    """Get global smart routing service instance"""
    return smart_routing_service
