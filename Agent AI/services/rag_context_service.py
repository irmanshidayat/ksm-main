#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Context Service untuk Agent AI
Memproses RAG context dari KSM Main
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from config.config import Config

logger = logging.getLogger(__name__)

class RAGContextService:
    """Service untuk memproses RAG context dari KSM Main"""
    
    def __init__(self):
        self.max_context_length = Config.RAG_MAX_CONTEXT_LENGTH
        self.min_similarity = Config.RAG_MIN_SIMILARITY
        self.max_chunks = Config.RAG_MAX_CHUNKS
        self.initialized = False
        
    def initialize(self):
        """Initialize RAG context service"""
        try:
            self.initialized = True
            logger.info("RAG Context Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG Context Service: {e}")
            self.initialized = False
            raise
    
    def _validate_context(self, context: Dict[str, Any]) -> bool:
        """Validate RAG context format"""
        try:
            # Check required fields
            required_fields = ['rag_results', 'total_chunks', 'avg_similarity']
            for field in required_fields:
                if field not in context:
                    logger.warning(f"⚠️ Missing required field in context: {field}")
                    return False
            
            # Validate rag_results
            rag_results = context.get('rag_results', [])
            if not isinstance(rag_results, list):
                logger.warning("⚠️ rag_results must be a list")
                return False
            
            # Validate each result
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
            
        except Exception as e:
            logger.error(f"❌ Error validating context: {e}")
            return False
    
    def _filter_results(self, rag_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter RAG results berdasarkan similarity threshold"""
        try:
            filtered_results = []
            
            for result in rag_results:
                similarity = result.get('similarity', 0.0)
                
                # Filter berdasarkan minimum similarity
                if similarity >= self.min_similarity:
                    filtered_results.append(result)
            
            # Fallback: jika tidak ada hasil yang lolos threshold, ambil top 3 terbaik
            if not filtered_results and rag_results:
                logger.info(f"⚠️ No results passed threshold {self.min_similarity}, using adaptive fallback with top results")
                # Sort semua hasil by similarity (descending)
                sorted_results = sorted(rag_results, key=lambda x: x.get('similarity', 0.0), reverse=True)
                # Ambil top 3 terbaik
                filtered_results = sorted_results[:3]
                logger.info(f"✅ Using {len(filtered_results)} top results as fallback")
            
            # Sort by similarity (descending)
            filtered_results.sort(key=lambda x: x.get('similarity', 0.0), reverse=True)
            
            # Limit jumlah chunks
            if len(filtered_results) > self.max_chunks:
                filtered_results = filtered_results[:self.max_chunks]
            
            logger.info(f"Filtered {len(filtered_results)} results from {len(rag_results)} total")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error filtering results: {e}")
            return []
    
    def _build_context_content(self, filtered_results: List[Dict[str, Any]]) -> str:
        """Build context content dari filtered results"""
        try:
            if not filtered_results:
                return ""
            
            context_parts = []
            
            for i, result in enumerate(filtered_results, 1):
                content = result.get('content', '').strip()
                similarity = result.get('similarity', 0.0)
                source = result.get('source_document', 'Dokumen')
                chunk_id = result.get('chunk_id', '')
                
                if content:
                    # Format context entry
                    context_entry = f"[{i}] {source}"
                    if chunk_id:
                        context_entry += f" (Chunk: {chunk_id})"
                    context_entry += f" [Relevansi: {similarity:.2f}]\n{content}"
                    
                    context_parts.append(context_entry)
            
            # Join all parts
            full_context = "\n\n".join(context_parts)
            
            # Truncate if too long
            if len(full_context) > self.max_context_length:
                full_context = full_context[:self.max_context_length] + "..."
                logger.warning(f"⚠️ Context truncated to {self.max_context_length} characters")
            
            return full_context
            
        except Exception as e:
            logger.error(f"❌ Error building context content: {e}")
            return ""
    
    def process_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process RAG context dari KSM Main"""
        try:
            start_time = time.time()
            
            # Validate context
            if not self._validate_context(context):
                logger.warning("⚠️ Invalid context format, returning empty context")
                return {
                    'context_available': False,
                    'total_chunks': 0,
                    'avg_similarity': 0.0,
                    'context_content': '',
                    'processing_time': 0,
                    'error': 'Invalid context format'
                }
            
            # Get rag_results
            rag_results = context.get('rag_results', [])
            
            if not rag_results:
                logger.info("📝 No RAG results provided")
                return {
                    'context_available': False,
                    'total_chunks': 0,
                    'avg_similarity': 0.0,
                    'context_content': '',
                    'processing_time': time.time() - start_time,
                    'message': 'No RAG results provided'
                }
            
            # Filter results
            filtered_results = self._filter_results(rag_results)
            
            if not filtered_results:
                logger.info("📝 No results passed similarity threshold")
                return {
                    'context_available': False,
                    'total_chunks': 0,
                    'avg_similarity': 0.0,
                    'context_content': '',
                    'processing_time': time.time() - start_time,
                    'message': 'No results passed similarity threshold'
                }
            
            # Build context content
            context_content = self._build_context_content(filtered_results)
            
            # Calculate average similarity
            total_similarity = sum(result.get('similarity', 0.0) for result in filtered_results)
            avg_similarity = total_similarity / len(filtered_results)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Context processed: {len(filtered_results)} chunks, avg_similarity: {avg_similarity:.3f}")
            
            return {
                'context_available': True,
                'total_chunks': len(filtered_results),
                'avg_similarity': round(avg_similarity, 3),
                'context_content': context_content,
                'filtered_results': filtered_results,
                'processing_time': round(processing_time, 3),
                'original_chunks': len(rag_results),
                'similarity_threshold': self.min_similarity
            }
            
        except Exception as e:
            logger.error(f"Error processing context: {e}")
            return {
                'context_available': False,
                'total_chunks': 0,
                'avg_similarity': 0.0,
                'context_content': '',
                'processing_time': time.time() - start_time if 'start_time' in locals() else 0,
                'error': str(e)
            }
    
    def check_health(self) -> Dict[str, Any]:
        """Check RAG context service health"""
        try:
            if not self.initialized:
                return {
                    'success': False,
                    'status': 'not_initialized',
                    'error': 'RAG Context Service not initialized'
                }
            
            # Test with sample context
            test_context = {
                'rag_results': [
                    {
                        'content': 'Test content',
                        'similarity': 0.8,
                        'source_document': 'test.pdf',
                        'chunk_id': 'test_1'
                    }
                ],
                'total_chunks': 1,
                'avg_similarity': 0.8
            }
            
            result = self.process_context(test_context)
            
            return {
                'success': True,
                'status': 'healthy',
                'test_result': result.get('context_available', False)
            }
            
        except Exception as e:
            logger.error(f"RAG Context health check failed: {e}")
            return {
                'success': False,
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get RAG context service status"""
        return {
            'service': 'RAG Context Service',
            'initialized': self.initialized,
            'max_context_length': self.max_context_length,
            'min_similarity': self.min_similarity,
            'max_chunks': self.max_chunks,
            'timestamp': datetime.now().isoformat()
        }

# Global instance
rag_context_service = RAGContextService()
