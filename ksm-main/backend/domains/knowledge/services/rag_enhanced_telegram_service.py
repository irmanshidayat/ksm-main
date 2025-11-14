#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Enhanced Telegram Service - Mengintegrasikan RAG Qdrant dengan Agent AI untuk Telegram
"""

import os
import json
import time
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import threading

# Import existing services (tanpa unified_rag_service; gunakan qdrant_service langsung)
from domains.integration.services.agent_ai_sync_service import agent_ai_sync
from .telegram_integration_service import telegram_integration
from .qdrant_service import get_qdrant_service
from .openai_embedding_service import OpenAIEmbeddingService

logger = logging.getLogger(__name__)


class RAGEnhancedTelegramService:
    """Service untuk mengintegrasikan RAG Qdrant dengan Agent AI untuk Telegram chatbot"""
    
    def __init__(self):
        # Initialize services
        self.qdrant_service = get_qdrant_service()
        self.embedding_service = OpenAIEmbeddingService()
        self.agent_ai_sync = agent_ai_sync
        self.telegram_integration = telegram_integration
        
        # Configuration
        self._init_configuration()
        
        # Cache untuk RAG results
        self._rag_cache = {}
        self._cache_lock = threading.Lock()
        
        logger.info("🚀 RAG Enhanced Telegram Service initialized")
    
    def _init_configuration(self):
        """Initialize configuration untuk Telegram RAG"""
        # Telegram-specific RAG settings
        self.telegram_top_k = int(os.getenv('TELEGRAM_RAG_TOP_K', '5'))
        self.telegram_similarity_threshold = float(os.getenv('TELEGRAM_RAG_SIMILARITY_THRESHOLD', '0.3'))
        self.telegram_max_context = int(os.getenv('TELEGRAM_RAG_MAX_CONTEXT', '8000'))
        
        # Cache settings
        self.rag_cache_ttl = int(os.getenv('TELEGRAM_RAG_CACHE_TTL', '1800'))  # 30 menit
        self.response_cache_ttl = int(os.getenv('TELEGRAM_RESPONSE_CACHE_TTL', '300'))  # 5 menit
        
        # Fallback settings
        self.enable_rag_fallback = os.getenv('TELEGRAM_ENABLE_RAG_FALLBACK', 'true').lower() == 'true'
        self.enable_agent_ai_fallback = os.getenv('TELEGRAM_ENABLE_AGENT_AI_FALLBACK', 'true').lower() == 'true'
        
        logger.info(f"📋 Telegram RAG Config: top_k={self.telegram_top_k}, threshold={self.telegram_similarity_threshold}")
    
    def _generate_cache_key(self, company_id: str, message: str) -> str:
        """Generate cache key untuk RAG results"""
        message_hash = hashlib.md5(message.encode()).hexdigest()
        return f"rag_telegram:{company_id}:{message_hash}"
    
    def _get_cached_rag_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached RAG result"""
        with self._cache_lock:
            if cache_key in self._rag_cache:
                cached_data = self._rag_cache[cache_key]
                if time.time() - cached_data['timestamp'] < self.rag_cache_ttl:
                    return cached_data['data']
                else:
                    # Remove expired cache
                    del self._rag_cache[cache_key]
        return None
    
    def _cache_rag_result(self, cache_key: str, data: Dict[str, Any]):
        """Cache RAG result"""
        with self._cache_lock:
            self._rag_cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
    
    def _search_similar(self, company_id: str, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Cari chunk serupa menggunakan Qdrant secara langsung dan normalisasi hasil."""
        try:
            # Generate embedding
            query_embedding = self.embedding_service.embed_text(query)
            if not query_embedding:
                return []
            # Search via qdrant_service
            results = self.qdrant_service.search_documents(
                company_id=company_id,
                query=query,
                top_k=top_k,
                collection='default',
                query_embedding=query_embedding
            ) or []
            # Normalisasi ke struktur yang dipakai Telegram RAG enhanced
            normalized: List[Dict[str, Any]] = []
            for r in results:
                text = r.get('text') if isinstance(r, dict) else getattr(r, 'text', '')
                metadata = r.get('metadata') if isinstance(r, dict) else getattr(r, 'metadata', {})
                similarity = r.get('similarity_score') if isinstance(r, dict) else getattr(r, 'score', 0.0)
                chunk_id = metadata.get('chunk_id') if isinstance(metadata, dict) else None
                source_document = metadata.get('document_id') if isinstance(metadata, dict) else None
                normalized.append({
                    'content': text or '',
                    'similarity': float(similarity) if similarity is not None else 0.0,
                    'source_document': str(source_document) if source_document is not None else '',
                    'chunk_id': str(chunk_id) if chunk_id is not None else '',
                    'metadata': metadata or {}
                })
            return normalized
        except Exception as e:
            logger.error(f"❌ Error during similarity search: {e}")
            return []

    def _build_rag_context(self, company_id: str, query: str) -> Dict[str, Any]:
        """Build RAG context untuk dikirim ke Agent AI"""
        try:
            start_time = time.time()
            
            # Check cache first
            cache_key = self._generate_cache_key(company_id, query)
            cached_result = self._get_cached_rag_result(cache_key)
            if cached_result:
                logger.info(f"📦 Using cached RAG result for query: {query[:50]}...")
                return cached_result
            
            # Perform RAG search via qdrant_service
            rag_result = self._search_similar(company_id=company_id, query=query, top_k=self.telegram_top_k)
            
            search_time = time.time() - start_time
            
            if not rag_result:
                return {
                    'rag_results': [],
                    'total_chunks': 0,
                    'avg_similarity': 0.0,
                    'search_time_ms': round(search_time * 1000, 2),
                    'cached': False,
                    'context_available': False
                }
            
            # Filter berdasarkan similarity threshold dengan logging detail
            filtered_results = []
            total_similarity = 0.0
            
            logger.info(f"🔍 Processing {len(rag_result)} RAG results with threshold: {self.telegram_similarity_threshold}")
            
            for i, result in enumerate(rag_result):
                similarity = result.get('similarity', 0.0)
                logger.info(f"📊 Result {i+1}: similarity={similarity:.3f}, threshold={self.telegram_similarity_threshold:.3f}")
                
                if similarity >= self.telegram_similarity_threshold:
                    filtered_results.append({
                        'content': result.get('content', ''),
                        'similarity': similarity,
                        'source_document': result.get('source_document', ''),
                        'chunk_id': result.get('chunk_id', ''),
                        'metadata': result.get('metadata', {})
                    })
                    total_similarity += similarity
                    logger.info(f"✅ Result {i+1} passed filter")
                else:
                    logger.info(f"❌ Result {i+1} filtered out (similarity too low)")
            
            # Jika semua tersaring, gunakan fallback adaptif: ambil top-N teratas apa adanya
            if not filtered_results and rag_result:
                logger.info("⚠️ No results passed threshold, using adaptive fallback with top results")
                # Ambil sampai 3 teratas sebagai context minimal
                for r in rag_result[:3]:
                    filtered_results.append({
                        'content': r.get('content', ''),
                        'similarity': float(r.get('similarity', 0.0) or 0.0),
                        'source_document': r.get('source_document', ''),
                        'chunk_id': r.get('chunk_id', ''),
                        'metadata': r.get('metadata', {})
                    })
                    total_similarity += float(r.get('similarity', 0.0) or 0.0)

            # Calculate average similarity (setelah fallback jika diterapkan)
            avg_similarity = total_similarity / len(filtered_results) if filtered_results else 0.0
            
            # Build context
            context_data = {
                'rag_results': filtered_results,
                'total_chunks': len(filtered_results),
                'avg_similarity': round(avg_similarity, 3),
                'search_time_ms': round(search_time * 1000, 2),
                'cached': False,
                'context_available': len(filtered_results) > 0,
                'similarity_threshold': self.telegram_similarity_threshold
            }
            
            # Cache the result
            self._cache_rag_result(cache_key, context_data)
            
            logger.info(f"🔍 RAG search completed: {len(filtered_results)} chunks, avg_similarity={avg_similarity:.3f}")
            
            return context_data
            
        except Exception as e:
            logger.error(f"❌ Error building RAG context: {e}")
            return {
                'rag_results': [],
                'total_chunks': 0,
                'avg_similarity': 0.0,
                'search_time_ms': 0,
                'cached': False,
                'context_available': False,
                'error': str(e)
            }
    
    def _format_message_for_agent_ai(self, user_id: int, message: str, session_id: str, 
                                   context: Dict[str, Any], company_id: str) -> Dict[str, Any]:
        """Format message untuk dikirim ke Agent AI dengan RAG context"""
        return {
            'user_id': user_id,
            'message': message,
            'session_id': session_id,
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
    
    def _handle_agent_ai_response(self, response: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle response dari Agent AI dan tambahkan metadata"""
        if response.get('success'):
            # Add RAG metadata to response
            response['rag_metadata'] = {
                'context_used': context.get('context_available', False),
                'chunks_used': context.get('total_chunks', 0),
                'avg_similarity': context.get('avg_similarity', 0.0),
                'search_time_ms': context.get('search_time_ms', 0)
            }
        
        return response
    
    def _fallback_to_rag_only(self, company_id: str, query: str) -> Dict[str, Any]:
        """Fallback ke RAG-only response jika Agent AI tidak tersedia"""
        try:
            logger.info("🔄 Using RAG-only fallback")
            
            # Use existing RAG fallback
            chunks = self._search_similar(company_id=company_id, query=query, top_k=self.telegram_top_k)
            if chunks:
                # Bangun jawaban sederhana dari top chunks (RAG-only fallback)
                joined = "\n\n".join((c.get('content') or '')[:500] for c in chunks[:3])
                return {
                    'success': True,
                    'data': {
                        'response': joined or 'Maaf, tidak ada informasi yang relevan ditemukan.',
                        'source': 'rag_fallback',
                        'context_used': True
                    },
                    'rag_metadata': {
                        'context_used': True,
                        'chunks_used': len(chunks),
                        'fallback_type': 'rag_only'
                    }
                }
            return {
                'success': False,
                'data': {
                    'response': 'Maaf, tidak ada informasi yang relevan ditemukan.',
                    'source': 'error_fallback'
                },
                'rag_metadata': {
                    'context_used': False,
                    'fallback_type': 'error'
                }
            }
                
        except Exception as e:
            logger.error(f"❌ RAG fallback error: {e}")
            return {
                'success': False,
                'data': {
                    'response': 'Maaf, sistem sedang mengalami gangguan.',
                    'source': 'system_error'
                },
                'rag_metadata': {
                    'context_used': False,
                    'fallback_type': 'system_error',
                    'error': str(e)
                }
            }
    
    def process_telegram_message(self, user_id: int, message: str, session_id: str = None, 
                               company_id: str = None) -> Dict[str, Any]:
        """
        Main method untuk memproses pesan Telegram dengan RAG + Agent AI
        
        Flow:
        1. Build RAG context
        2. Send ke Agent AI dengan context
        3. Handle response atau fallback
        """
        try:
            # Use default company_id if not provided
            if company_id is None:
                from config.config import Config
                company_id = Config.DEFAULT_COMPANY_ID
            
            start_time = time.time()
            logger.info(f"📨 Processing Telegram message from user {user_id}: {message[:50]}...")
            
            # Step 1: Build RAG context
            context = self._build_rag_context(company_id, message)
            
            # Step 2: Check Agent AI availability
            if not self.agent_ai_sync:
                logger.warning("⚠️ Agent AI sync service not available, using RAG fallback")
                return self._fallback_to_rag_only(company_id, message)
            
            health_status = self.agent_ai_sync.check_agent_ai_health()
            if not health_status.get('success'):
                logger.warning(f"⚠️ Agent AI not available: {health_status.get('status')}, using RAG fallback")
                return self._fallback_to_rag_only(company_id, message)
            
            # Step 3: Format message untuk Agent AI
            formatted_message = self._format_message_for_agent_ai(
                user_id, message, session_id or f'telegram_{user_id}', context, company_id
            )
            
            # Step 4: Send ke Agent AI
            logger.info(f"🤖 Sending message to Agent AI with {context.get('total_chunks', 0)} context chunks")
            
            # Use existing telegram integration but with enhanced data
            agent_response = self.telegram_integration.send_message_to_agent(
                user_id=user_id,
                message=message,
                session_id=session_id,
                company_id=company_id
            )
            
            # Step 5: Handle response
            if agent_response.get('success'):
                enhanced_response = self._handle_agent_ai_response(agent_response, context)
                processing_time = time.time() - start_time
                enhanced_response['processing_time'] = round(processing_time, 2)
                
                logger.info(f"✅ Telegram message processed successfully in {processing_time:.2f}s")
                return enhanced_response
            else:
                # Fallback jika Agent AI response gagal
                logger.warning(f"⚠️ Agent AI response failed: {agent_response.get('message')}")
                if self.enable_rag_fallback:
                    return self._fallback_to_rag_only(company_id, message)
                else:
                    return {
                        'success': False,
                        'data': {
                            'response': 'Maaf, sistem AI sedang tidak tersedia.',
                            'source': 'agent_ai_unavailable'
                        },
                        'rag_metadata': {
                            'context_used': context.get('context_available', False),
                            'fallback_type': 'agent_ai_failed'
                        }
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error processing Telegram message: {e}")
            return {
                'success': False,
                'data': {
                    'response': 'Maaf, terjadi kesalahan saat memproses pesan Anda.',
                    'source': 'processing_error'
                },
                'rag_metadata': {
                    'context_used': False,
                    'fallback_type': 'exception',
                    'error': str(e)
                }
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status service"""
        return {
            'service': 'rag_enhanced_telegram',
            'status': 'active',
            'configuration': {
                'telegram_top_k': self.telegram_top_k,
                'telegram_similarity_threshold': self.telegram_similarity_threshold,
                'telegram_max_context': self.telegram_max_context,
                'rag_cache_ttl': self.rag_cache_ttl,
                'response_cache_ttl': self.response_cache_ttl
            },
            'cache_stats': {
                'cached_items': len(self._rag_cache),
                'cache_ttl': self.rag_cache_ttl
            },
            'dependencies': {
                'rag_service': 'available' if self.rag_service else 'unavailable',
                'agent_ai_sync': 'available' if self.agent_ai_sync else 'unavailable',
                'telegram_integration': 'available' if self.telegram_integration else 'unavailable'
            },
            'timestamp': datetime.now().isoformat()
        }


# Global instance
rag_enhanced_telegram = RAGEnhancedTelegramService()
