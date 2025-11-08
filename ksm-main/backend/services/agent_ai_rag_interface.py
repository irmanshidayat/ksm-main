#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent AI RAG Interface - Interface untuk komunikasi dengan Agent AI dengan RAG context
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AgentAIRAGInterface:
    """Interface untuk komunikasi dengan Agent AI dengan RAG context"""
    
    def __init__(self):
        # Configuration
        self.agent_ai_url = os.getenv('AGENT_AI_URL', 'http://localhost:5000')
        self.api_key = os.getenv('AGENT_AI_API_KEY', 'KSM_api_key_2ptybn')
        self.timeout = int(os.getenv('AGENT_AI_TIMEOUT', '30'))
        
        # Endpoints
        self.rag_chat_endpoint = f"{self.agent_ai_url}/api/rag/chat"
        self.telegram_chat_endpoint = f"{self.agent_ai_url}/api/telegram/chat"
        self.health_endpoint = f"{self.agent_ai_url}/health"
        self.status_endpoint = f"{self.agent_ai_url}/status"
        
        logger.info(f"🤖 Agent AI RAG Interface initialized: {self.agent_ai_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers untuk request ke Agent AI"""
        return {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
            'User-Agent': 'KSM-Main-RAG-Interface/1.0'
        }
    
    def _validate_rag_context(self, context: Dict[str, Any]) -> bool:
        """Validate RAG context format"""
        required_fields = ['rag_results', 'total_chunks', 'avg_similarity']
        
        for field in required_fields:
            if field not in context:
                logger.warning(f"⚠️ Missing required field in RAG context: {field}")
                return False
        
        # Validate rag_results structure
        rag_results = context.get('rag_results', [])
        if not isinstance(rag_results, list):
            logger.warning("⚠️ rag_results must be a list")
            return False
        
        for result in rag_results:
            if not isinstance(result, dict):
                logger.warning("⚠️ Each rag_result must be a dictionary")
                return False
            
            required_result_fields = ['content', 'similarity']
            for field in required_result_fields:
                if field not in result:
                    logger.warning(f"⚠️ Missing required field in rag_result: {field}")
                    return False
        
        return True
    
    def _format_rag_context_for_agent_ai(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Format RAG context untuk dikirim ke Agent AI"""
        try:
            # Validate context first
            if not self._validate_rag_context(context):
                logger.warning("⚠️ Invalid RAG context, using empty context")
                return {
                    'rag_results': [],
                    'total_chunks': 0,
                    'avg_similarity': 0.0,
                    'context_available': False,
                    'error': 'Invalid context format'
                }
            
            # Format context untuk Agent AI
            formatted_context = {
                'rag_results': [],
                'total_chunks': context.get('total_chunks', 0),
                'avg_similarity': context.get('avg_similarity', 0.0),
                'search_time_ms': context.get('search_time_ms', 0),
                'context_available': context.get('context_available', False),
                'similarity_threshold': context.get('similarity_threshold', 0.65),
                'cached': context.get('cached', False)
            }
            
            # Format rag_results
            for result in context.get('rag_results', []):
                formatted_result = {
                    'content': result.get('content', ''),
                    'similarity': result.get('similarity', 0.0),
                    'source_document': result.get('source_document', ''),
                    'chunk_id': result.get('chunk_id', ''),
                    'metadata': result.get('metadata', {})
                }
                formatted_context['rag_results'].append(formatted_result)
            
            return formatted_context
            
        except Exception as e:
            logger.error(f"❌ Error formatting RAG context: {e}")
            return {
                'rag_results': [],
                'total_chunks': 0,
                'avg_similarity': 0.0,
                'context_available': False,
                'error': str(e)
            }
    
    def send_rag_enhanced_message(self, user_id: int, message: str, context: Dict[str, Any], 
                                 session_id: str = None, company_id: str = None,
                                 metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send message ke Agent AI dengan RAG context
        
        Args:
            user_id: ID user
            message: Pesan dari user
            context: RAG context dari ksm-main
            session_id: Session ID
            company_id: Company ID
            metadata: Additional metadata
        
        Returns:
            Dict dengan response dari Agent AI
        """
        try:
            # Use default company_id if not provided
            if company_id is None:
                from config.config import Config
                company_id = Config.DEFAULT_COMPANY_ID
            
            start_time = time.time()
            
            # Format RAG context
            formatted_context = self._format_rag_context_for_agent_ai(context)
            
            # Prepare request data
            request_data = {
                'user_id': user_id,
                'message': message,
                'session_id': session_id or f'telegram_{user_id}',
                'source': 'KSM_main_telegram_rag',
                'context': formatted_context,
                'metadata': {
                    'company_id': company_id,
                    'timestamp': datetime.now().isoformat(),
                    'rag_enabled': True,
                    'telegram_bot': True,
                    'context_chunks': formatted_context.get('total_chunks', 0),
                    'avg_similarity': formatted_context.get('avg_similarity', 0.0),
                    'interface_version': '1.0'
                }
            }
            
            # Add additional metadata if provided
            if metadata:
                request_data['metadata'].update(metadata)
            
            logger.info(f"📤 Sending RAG-enhanced message to Agent AI: {message[:50]}... with {formatted_context.get('total_chunks', 0)} chunks")
            
            # Send request ke Agent AI
            response = requests.post(
                self.rag_chat_endpoint,
                json=request_data,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Add interface metadata
                result['interface_metadata'] = {
                    'response_time': round(response_time, 3),
                    'context_chunks_sent': formatted_context.get('total_chunks', 0),
                    'avg_similarity': formatted_context.get('avg_similarity', 0.0),
                    'interface_version': '1.0'
                }
                
                logger.info(f"✅ RAG-enhanced message sent successfully in {response_time:.3f}s")
                
                return {
                    'success': True,
                    'status': 'rag_enhanced_success',
                    'data': result,
                    'response_time': round(response_time, 3),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"❌ Agent AI RAG endpoint error: {response.status_code} - {response.text}")
                
                return {
                    'success': False,
                    'status': 'rag_enhanced_error',
                    'error_code': response.status_code,
                    'error_message': response.text,
                    'response_time': round(response_time, 3),
                    'timestamp': datetime.now().isoformat()
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Agent AI RAG request timeout after {self.timeout}s")
            return {
                'success': False,
                'status': 'timeout',
                'error': f'Request timeout after {self.timeout}s',
                'timestamp': datetime.now().isoformat()
            }
            
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Agent AI connection error: {self.agent_ai_url}")
            return {
                'success': False,
                'status': 'connection_error',
                'error': f'Cannot connect to Agent AI at {self.agent_ai_url}',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Unexpected error in RAG interface: {e}")
            return {
                'success': False,
                'status': 'unexpected_error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def send_simple_message(self, user_id: int, message: str, session_id: str = None) -> Dict[str, Any]:
        """Send simple message ke Agent AI tanpa RAG context (fallback)"""
        try:
            start_time = time.time()
            
            request_data = {
                'user_id': user_id,
                'message': message,
                'session_id': session_id or f'telegram_{user_id}',
                'source': 'KSM_main_telegram_simple',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"📤 Sending simple message to Agent AI: {message[:50]}...")
            
            response = requests.post(
                self.telegram_chat_endpoint,
                json=request_data,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                logger.info(f"✅ Simple message sent successfully in {response_time:.3f}s")
                
                return {
                    'success': True,
                    'status': 'simple_success',
                    'data': result,
                    'response_time': round(response_time, 3),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"❌ Agent AI simple endpoint error: {response.status_code} - {response.text}")
                
                return {
                    'success': False,
                    'status': 'simple_error',
                    'error_code': response.status_code,
                    'error_message': response.text,
                    'response_time': round(response_time, 3),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error in simple message interface: {e}")
            return {
                'success': False,
                'status': 'simple_exception',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_agent_ai_health(self) -> Dict[str, Any]:
        """Check kesehatan Agent AI"""
        try:
            start_time = time.time()
            
            response = requests.get(
                self.health_endpoint,
                headers=self._get_headers(),
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'status': 'healthy',
                    'data': data,
                    'response_time': round(response_time, 3),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'status': 'unhealthy',
                    'error_code': response.status_code,
                    'response_time': round(response_time, 3),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_agent_ai_status(self) -> Dict[str, Any]:
        """Get status Agent AI"""
        try:
            response = requests.get(
                self.status_endpoint,
                headers=self._get_headers(),
                timeout=10
            )
            
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
    
    def test_rag_endpoint(self) -> Dict[str, Any]:
        """Test RAG endpoint di Agent AI"""
        try:
            # Test data
            test_context = {
                'rag_results': [
                    {
                        'content': 'Test content from KSM Main RAG system',
                        'similarity': 0.85,
                        'source_document': 'test_document.pdf',
                        'chunk_id': 'test_chunk_1',
                        'metadata': {'test': True}
                    }
                ],
                'total_chunks': 1,
                'avg_similarity': 0.85,
                'search_time_ms': 150.5,
                'context_available': True,
                'similarity_threshold': 0.65
            }
            
            result = self.send_rag_enhanced_message(
                user_id=12345,
                message='Test RAG message from KSM Main',
                context=test_context,
                session_id='test_rag_interface',
                company_id='PT. Kian Santang Muliatama',
                metadata={'test_mode': True}
            )
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'status': 'test_error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_interface_info(self) -> Dict[str, Any]:
        """Get interface information"""
        return {
            'interface_name': 'Agent AI RAG Interface',
            'version': '1.0',
            'agent_ai_url': self.agent_ai_url,
            'endpoints': {
                'rag_chat': self.rag_chat_endpoint,
                'telegram_chat': self.telegram_chat_endpoint,
                'health': self.health_endpoint,
                'status': self.status_endpoint
            },
            'timeout': self.timeout,
            'api_key_configured': bool(self.api_key),
            'timestamp': datetime.now().isoformat()
        }


# Global instance
agent_ai_rag_interface = AgentAIRAGInterface()
