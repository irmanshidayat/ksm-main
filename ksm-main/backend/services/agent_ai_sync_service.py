#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent AI Sync Service - Sinkronisasi dengan Agent AI
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import time
import os

logger = logging.getLogger(__name__)

class AgentAISyncService:
    """Service untuk sinkronisasi dengan Agent AI - OPTIMIZED for AI response generation only"""
    
    def __init__(self):
        # Use environment variable with fallback to default
        self.agent_ai_url = os.getenv('AGENT_AI_URL', 'http://localhost:5000')
        self.sync_interval = 30  # seconds
        self.last_sync = None
        self.sync_status = {
            'connected': False,
            'last_check': None,
            'error_count': 0,
            'success_count': 0
        }
    
    def check_agent_ai_health(self) -> Dict[str, Any]:
        """Check kesehatan Agent AI"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.agent_ai_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.sync_status['connected'] = True
                self.sync_status['last_check'] = datetime.now()
                self.sync_status['success_count'] += 1
                self.sync_status['error_count'] = 0
                
                return {
                    'success': True,
                    'status': 'connected',
                    'response_time': round(response_time, 3),
                    'data': response.json() if response.text else {},
                    'timestamp': datetime.now().isoformat()
                }
            else:
                self.sync_status['connected'] = False
                self.sync_status['error_count'] += 1
                
                return {
                    'success': False,
                    'status': 'error',
                    'error_code': response.status_code,
                    'response_time': round(response_time, 3),
                    'timestamp': datetime.now().isoformat()
                }
                
        except requests.exceptions.Timeout:
            self.sync_status['connected'] = False
            self.sync_status['error_count'] += 1
            
            return {
                'success': False,
                'status': 'timeout',
                'error': 'Connection timeout',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.sync_status['connected'] = False
            self.sync_status['error_count'] += 1
            
            return {
                'success': False,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_openrouter_sync_status(self) -> Dict[str, Any]:
        """Check status sinkronisasi OpenRouter dengan Agent AI"""
        try:
            # Check local OpenRouter service
            local_status = "unavailable"
            try:
                from .unified_ai_service import get_unified_ai_service
                local_service = get_unified_ai_service()
                local_status = "available" if local_service else "unavailable"
            except ImportError:
                local_status = "not_imported"
            
            # Check Agent AI OpenRouter status
            agent_status = "unknown"
            try:
                response = requests.get(f"{self.agent_ai_url}/api/monitoring/ai-status", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        agent_status = data.get('data', {}).get('openrouter_status', 'unknown')
            except:
                agent_status = "unreachable"
            
            return {
                'success': True,
                'local_openrouter_status': local_status,
                'agent_ai_openrouter_status': agent_status,
                'synchronized': local_status == agent_status,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_telegram_integration(self) -> Dict[str, Any]:
        """Test integrasi telegram dengan Agent AI"""
        try:
            # Test endpoint chat di Agent AI
            test_data = {
                'user_id': 12345,
                'message': 'Test message from KSM Main',
                'session_id': 'test_KSM_main',
                'source': 'KSM_main_test'
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.agent_ai_url}/api/telegram/chat",
                json=test_data,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'status': 'integration_ok',
                    'response_time': round(response_time, 3),
                    'data': result,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'status': 'integration_error',
                    'error_code': response.status_code,
                    'response_text': response.text,
                    'response_time': round(response_time, 3),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'status': 'integration_error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_agent_ai_info(self) -> Dict[str, Any]:
        """Get informasi Agent AI"""
        try:
            response = requests.get(f"{self.agent_ai_url}/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error_code': response.status_code,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def sync_telegram_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Sinkronisasi webhook dengan Agent AI"""
        try:
            # Kirim informasi webhook ke Agent AI untuk sinkronisasi
            sync_data = {
                'webhook_url': webhook_url,
                'backend_url': self.agent_ai_url,  # Use configured Agent AI URL
                'sync_timestamp': datetime.now().isoformat(),
                'action': 'webhook_sync'
            }
            
            response = requests.post(
                f"{self.agent_ai_url}/api/telegram/sync",
                json=sync_data,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'status': 'webhook_synced',
                    'data': response.json() if response.text else {},
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'status': 'webhook_sync_failed',
                    'error_code': response.status_code,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'status': 'webhook_sync_error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get status sinkronisasi"""
        return {
            'sync_status': self.sync_status,
            'agent_ai_url': self.agent_ai_url,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'timestamp': datetime.now().isoformat()
        }
    
    def force_sync(self) -> Dict[str, Any]:
        """Force sync dengan Agent AI"""
        try:
            # Check health
            health_status = self.check_agent_ai_health()
            
            # Test integration
            integration_status = self.test_telegram_integration()
            
            # Get info
            info_status = self.get_agent_ai_info()
            
            self.last_sync = datetime.now()
            
            return {
                'success': True,
                'data': {
                    'health': health_status,
                    'integration': integration_status,
                    'info': info_status,
                    'sync_timestamp': self.last_sync.isoformat()
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def send_rag_enhanced_message(self, user_id: int, message: str, context: Dict[str, Any], 
                                 session_id: str = None, company_id: str = None) -> Dict[str, Any]:
        """Send message ke Agent AI dengan RAG context"""
        try:
            # Use default company_id if not provided
            if company_id is None:
                from config.config import Config
                company_id = Config.DEFAULT_COMPANY_ID
            
            # Prepare data untuk Agent AI RAG endpoint
            rag_data = {
                'user_id': user_id,
                'message': message,
                'session_id': session_id or f'telegram_{user_id}',
                'source': 'KSM_main_telegram_rag',
                'context': context,
                'metadata': {
                    'company_id': company_id,
                    'timestamp': datetime.now().isoformat(),
                    'rag_enabled': True,
                    'telegram_bot': True,
                    'context_chunks': context.get('total_chunks', 0),
                    'avg_similarity': context.get('avg_similarity', 0.0)
                }
            }
            
            # Send ke Agent AI RAG endpoint
            start_time = time.time()
            response = requests.post(
                f"{self.agent_ai_url}/api/rag/chat",
                json=rag_data,
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'status': 'rag_enhanced_success',
                    'response_time': round(response_time, 3),
                    'data': result,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'status': 'rag_enhanced_error',
                    'error_code': response.status_code,
                    'response_text': response.text,
                    'response_time': round(response_time, 3),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'status': 'rag_enhanced_exception',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_rag_integration(self) -> Dict[str, Any]:
        """Test integrasi RAG dengan Agent AI"""
        try:
            # Test data dengan RAG context
            test_context = {
                'rag_results': [
                    {
                        'content': 'Test content from RAG system',
                        'similarity': 0.85,
                        'source_document': 'test_document.pdf',
                        'chunk_id': 'test_chunk_1'
                    }
                ],
                'total_chunks': 1,
                'avg_similarity': 0.85,
                'search_time_ms': 150.5,
                'context_available': True
            }
            
            test_data = {
                'user_id': 12345,
                'message': 'Test RAG message from KSM Main',
                'session_id': 'test_KSM_main_rag',
                'source': 'KSM_main_test_rag',
                'context': test_context,
                'metadata': {
                    'company_id': 'PT. Kian Santang Muliatama',
                    'timestamp': datetime.now().isoformat(),
                    'rag_enabled': True,
                    'test_mode': True
                }
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.agent_ai_url}/api/rag/chat",
                json=test_data,
                timeout=15
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'status': 'rag_integration_ok',
                    'response_time': round(response_time, 3),
                    'data': result,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'status': 'rag_integration_error',
                    'error_code': response.status_code,
                    'response_text': response.text,
                    'response_time': round(response_time, 3),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'status': 'rag_integration_exception',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_rag_endpoint_status(self) -> Dict[str, Any]:
        """Check status RAG endpoint di Agent AI"""
        try:
            # Check if RAG endpoint exists
            response = requests.get(f"{self.agent_ai_url}/api/rag/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'rag_endpoint_available': True,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'rag_endpoint_available': False,
                    'error_code': response.status_code,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'rag_endpoint_available': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global instance
agent_ai_sync = AgentAISyncService()
