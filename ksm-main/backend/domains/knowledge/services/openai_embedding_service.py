#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI Embedding Service untuk KSM Main Backend
Service khusus untuk menggunakan OpenAI Embeddings API
"""

import os
import time
import logging
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Try to import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class OpenAIEmbeddingService:
    """Service untuk generate embeddings menggunakan OpenAI API"""
    
    def __init__(self):
        # Configuration
        self._init_configuration()
        
        # Cache management
        self.embedding_cache = {}
        self.cache_max_size = int(os.getenv('EMBEDDING_CACHE_MAX_SIZE', '1000'))
        self.cache_ttl = int(os.getenv('EMBEDDING_CACHE_TTL', '3600'))
        
        # Rate limiting
        self.rate_limit_lock = threading.Lock()
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        # Performance tracking
        self.stats = {
            'total_embeddings': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_embedding_time': 0,
            'api_errors': 0,
            'rate_limit_hits': 0
        }
        
        # Initialize OpenAI client
        self._init_openai_client()
        
        logger.info(f"[INIT] OpenAI Embedding Service initialized")
        logger.info(f"[CONFIG] Configuration: model={self.model_name}, dim={self.embedding_dim}")
    
    def _init_configuration(self):
        """Initialize service configuration"""
        # OpenAI configuration
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model_name = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        self.embedding_dim = int(os.getenv('EMBEDDING_DIMENSIONS', '1536'))
        
        # Batch processing
        self.batch_size = int(os.getenv('EMBEDDING_BATCH_SIZE', '100'))
        self.max_retries = int(os.getenv('EMBEDDING_MAX_RETRIES', '3'))
        self.timeout = int(os.getenv('EMBEDDING_TIMEOUT', '30'))
        
        # Validate configuration
        if not self.api_key:
            logger.warning("⚠️ OPENAI_API_KEY not found in environment variables")
    
    def _init_openai_client(self):
        """Initialize OpenAI client"""
        if not OPENAI_AVAILABLE:
            logger.error("❌ OpenAI library not available")
            self.client = None
            return
        
        if not self.api_key:
            logger.error("❌ OpenAI API key not configured")
            self.client = None
            return
        
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("[SUCCESS] OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            self.client = None
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        import hashlib
        return hashlib.md5(f"{text}_{self.model_name}".encode()).hexdigest()
    
    def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache if available and not expired"""
        cache_key = self._get_cache_key(text)
        
        if cache_key in self.embedding_cache:
            cached_data = self.embedding_cache[cache_key]
            cache_time = cached_data['timestamp']
            
            # Check if cache is still valid
            if datetime.now() - cache_time < timedelta(seconds=self.cache_ttl):
                self.stats['cache_hits'] += 1
                logger.debug(f"📋 Cache hit for text: {text[:50]}...")
                return cached_data['embedding']
            else:
                # Remove expired cache entry
                del self.embedding_cache[cache_key]
        
        self.stats['cache_misses'] += 1
        return None
    
    def _save_to_cache(self, text: str, embedding: List[float]):
        """Save embedding to cache"""
        cache_key = self._get_cache_key(text)
        
        # Clean cache if it's too large
        if len(self.embedding_cache) >= self.cache_max_size:
            # Remove oldest entries
            oldest_keys = sorted(
                self.embedding_cache.keys(),
                key=lambda k: self.embedding_cache[k]['timestamp']
            )[:len(self.embedding_cache) // 2]
            
            for key in oldest_keys:
                del self.embedding_cache[key]
        
        self.embedding_cache[cache_key] = {
            'embedding': embedding,
            'timestamp': datetime.now()
        }
    
    def _rate_limit(self):
        """Implement rate limiting"""
        with self.rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                time.sleep(sleep_time)
                self.stats['rate_limit_hits'] += 1
            
            self.last_request_time = time.time()
    
    def _call_openai_api(self, texts: List[str]) -> List[List[float]]:
        """Call OpenAI API to generate embeddings"""
        if not self.client:
            raise Exception("OpenAI client not initialized")
        
        # Rate limiting
        self._rate_limit()
        
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts,
                encoding_format="float"
            )
            
            embeddings = [data.embedding for data in response.data]
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {e}")
            self.stats['api_errors'] += 1
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        if not text or not text.strip():
            return [0.0] * self.embedding_dim
        
        # Check cache first
        cached_embedding = self._get_from_cache(text)
        if cached_embedding:
            return cached_embedding
        
        # Generate embedding
        try:
            start_time = time.time()
            
            embeddings = self._call_openai_api([text])
            embedding = embeddings[0]
            
            # Save to cache
            self._save_to_cache(text, embedding)
            
            # Update stats
            embedding_time = time.time() - start_time
            self.stats['total_embeddings'] += 1
            self.stats['avg_embedding_time'] = (
                (self.stats['avg_embedding_time'] * (self.stats['total_embeddings'] - 1) + embedding_time) 
                / self.stats['total_embeddings']
            )
            
            logger.debug(f"✅ Generated embedding for text: {text[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dim
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch"""
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            return [[0.0] * self.embedding_dim] * len(texts)
        
        # Check cache for each text
        cached_embeddings = {}
        texts_to_process = []
        result_indices = []
        
        for i, text in enumerate(valid_texts):
            cached_embedding = self._get_from_cache(text)
            if cached_embedding:
                cached_embeddings[i] = cached_embedding
            else:
                texts_to_process.append(text)
                result_indices.append(i)
        
        # Process texts that aren't cached
        if texts_to_process:
            try:
                start_time = time.time()
                
                # Process in batches
                batch_embeddings = []
                for i in range(0, len(texts_to_process), self.batch_size):
                    batch = texts_to_process[i:i + self.batch_size]
                    batch_result = self._call_openai_api(batch)
                    batch_embeddings.extend(batch_result)
                
                # Save to cache
                for i, embedding in enumerate(batch_embeddings):
                    text = texts_to_process[i]
                    self._save_to_cache(text, embedding)
                
                # Update stats
                embedding_time = time.time() - start_time
                self.stats['total_embeddings'] += len(texts_to_process)
                self.stats['avg_embedding_time'] = (
                    (self.stats['avg_embedding_time'] * (self.stats['total_embeddings'] - len(texts_to_process)) + embedding_time) 
                    / self.stats['total_embeddings']
                )
                
                # Combine cached and new embeddings
                for i, embedding in enumerate(batch_embeddings):
                    cached_embeddings[result_indices[i]] = embedding
                
            except Exception as e:
                logger.error(f"❌ Failed to generate batch embeddings: {e}")
                # Return zero vectors for failed texts
                for i in result_indices:
                    cached_embeddings[i] = [0.0] * self.embedding_dim
        
        # Return embeddings in original order
        result = []
        for i in range(len(valid_texts)):
            result.append(cached_embeddings[i])
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            'cache_size': len(self.embedding_cache),
            'cache_max_size': self.cache_max_size,
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
            'client_available': self.client is not None
        }
    
    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache.clear()
        logger.info("🧹 Embedding cache cleared")
    
    def is_available(self) -> bool:
        """Check if service is available"""
        return (
            OPENAI_AVAILABLE and 
            self.client is not None and 
            self.api_key is not None
        )


# Global instance
_openai_embedding_service = None


def get_openai_embedding_service() -> OpenAIEmbeddingService:
    """Get global OpenAI embedding service instance"""
    global _openai_embedding_service
    if _openai_embedding_service is None:
        _openai_embedding_service = OpenAIEmbeddingService()
    return _openai_embedding_service
