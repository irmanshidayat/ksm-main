#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Embedding Service untuk KSM Main Backend
Konsolidasi dari embedding_service.py dan local_embedding_service.py
Menggabungkan fitur terbaik dari kedua implementasi dengan fallback yang robust
"""

import os
import re
import math
import hashlib
import logging
import threading
import time
import struct
from typing import List, Dict, Any, Optional
from datetime import datetime

# Sentence transformers removed - using OpenAI embeddings only
SENTENCE_TRANSFORMERS_AVAILABLE = False

# Try to import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class UnifiedEmbeddingService:
    """Unified Embedding Service yang menggabungkan fitur terbaik dari semua implementasi"""
    
    def __init__(self):
        # Configuration
        self._init_configuration()
        
        # Model management
        self.model = None
        self.model_loaded = False
        self.loading_lock = threading.Lock()
        
        # Service management
        self.openai_service = None
        self.sentence_transformer_service = None
        
        # Cache management
        self.embedding_cache = {}
        self.cache_max_size = int(os.getenv('EMBEDDING_CACHE_MAX_SIZE', '1000'))
        self.cache_ttl = int(os.getenv('EMBEDDING_CACHE_TTL', '3600'))
        
        # Performance tracking
        self.stats = {
            'total_embeddings': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'model_load_time': 0,
            'avg_embedding_time': 0,
            'fallback_usage': 0,
            'openai_usage': 0,
            'sentence_transformer_usage': 0
        }
        
        # Initialize services
        self._init_services()
        
        logger.info(f"[INIT] Unified Embedding Service initialized")
        logger.info(f"[CONFIG] Configuration: provider={self.provider}, model={self.model_name}, dim={self.embedding_dim}")
    
    def _init_configuration(self):
        """Initialize service configuration"""
        # Provider configuration
        self.provider = os.getenv('EMBEDDING_PROVIDER', 'openai')
        
        # Model configuration based on provider
        if self.provider == 'openai':
            self.model_name = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
            self.embedding_dim = int(os.getenv('EMBEDDING_DIMENSIONS', '1536'))
        else:
            self.model_name = os.getenv('EMBEDDING_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')
            self.embedding_dim = int(os.getenv('EMBEDDING_DIMENSION', '384'))
        
        self.fallback_model = os.getenv('EMBEDDING_FALLBACK_MODEL', 'all-MiniLM-L6-v2')
        
        # Qdrant service for advanced features
        self.qdrant_service = None
        self._init_qdrant_service()
    
    def _init_services(self):
        """Initialize embedding services based on provider"""
        if self.provider == 'openai':
            self._init_openai_service()
        elif self.provider == 'sentence-transformers':
            logger.warning("⚠️ sentence-transformers provider not available, falling back to OpenAI")
            self._init_openai_service()
        elif self.provider == 'hybrid':
            logger.warning("⚠️ hybrid provider not available, using OpenAI only")
            self._init_openai_service()
        else:
            logger.warning(f"⚠️ Unknown provider: {self.provider}, falling back to OpenAI")
            self._init_openai_service()
    
    def _init_openai_service(self):
        """Initialize OpenAI embedding service"""
        try:
            from .openai_embedding_service import get_openai_embedding_service
            self.openai_service = get_openai_embedding_service()
            if self.openai_service.is_available():
                logger.info("[SUCCESS] OpenAI embedding service initialized")
            else:
                logger.warning("⚠️ OpenAI service not available (missing API key or library)")
                self.openai_service = None
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize OpenAI service: {e}")
            self.openai_service = None
    
    def _init_sentence_transformer_service(self):
        """Initialize Sentence Transformer service - DEPRECATED"""
        logger.warning("⚠️ Sentence Transformer service is deprecated, using OpenAI embeddings only")
    
    def _init_qdrant_service(self):
        """Initialize Qdrant service if available"""
        try:
            from .qdrant_service import get_qdrant_fallback_service
            self.qdrant_service = get_qdrant_fallback_service()
            logger.info("[SUCCESS] Qdrant service initialized for embeddings")
        except Exception as e:
            logger.warning(f"⚠️ Qdrant service not available: {e}")
            self.qdrant_service = None
    
    def _load_model(self):
        """Load model - DEPRECATED, using OpenAI embeddings only"""
        logger.warning("⚠️ _load_model is deprecated, using OpenAI embeddings only")
        return False
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key untuk text"""
        return hashlib.sha256(f"{self.model_name}::{text}".encode('utf-8')).hexdigest()
    
    def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """Get embedding dari cache"""
        cache_key = self._get_cache_key(text)
        
        if cache_key in self.embedding_cache:
            cached_data = self.embedding_cache[cache_key]
            # Check TTL
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                self.stats['cache_hits'] += 1
                return cached_data['embedding']
            else:
                # Remove expired cache
                del self.embedding_cache[cache_key]
        
        self.stats['cache_misses'] += 1
        return None
    
    def _save_to_cache(self, text: str, embedding: List[float]):
        """Save embedding ke cache"""
        cache_key = self._get_cache_key(text)
        
        # Cleanup cache jika terlalu besar
        if len(self.embedding_cache) >= self.cache_max_size:
            # Remove oldest entries
            oldest_keys = sorted(
                self.embedding_cache.keys(),
                key=lambda k: self.embedding_cache[k]['timestamp']
            )[:100]  # Remove 100 oldest entries
            
            for key in oldest_keys:
                del self.embedding_cache[key]
        
        self.embedding_cache[cache_key] = {
            'embedding': embedding,
            'timestamp': time.time()
        }
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenisasi sederhana: huruf kecil, ambil kata alfanumerik."""
        text = (text or '').lower()
        return re.findall(r"[\w]+", text, flags=re.UNICODE)
    
    def _hash_to_index(self, token: str) -> int:
        """Peta token -> index [0, dim) secara deterministik."""
        h = hashlib.sha256(token.encode('utf-8')).hexdigest()
        return int(h, 16) % self.embedding_dim
    
    def _hash_to_sign(self, token: str) -> int:
        """Tentukan tanda +1/-1 untuk mengurangi collision bias."""
        h = hashlib.md5(token.encode('utf-8')).digest()
        # Ambil bit terakhir untuk tanda
        return 1 if (h[0] & 1) == 0 else -1
    
    def _build_local_embedding(self, text: str) -> List[float]:
        """Bangun embedding hashed BOW berukuran self.embedding_dim, L2-normalized."""
        vec = [0.0] * self.embedding_dim
        try:
            tokens = self._tokenize(text)
            if not tokens:
                return vec

            # Hitung TF sederhana dan sebar menggunakan hashing trick
            for tok in tokens:
                idx = self._hash_to_index(tok)
                sgn = self._hash_to_sign(tok)
                vec[idx] += 1.0 * sgn

            # L2 normalize agar cosine similarity bermakna
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            vec = [v / norm for v in vec]
            return vec
        except Exception as e:
            logger.warning(f"⚠️ Local embedding failed, using fallback: {e}")
            return self._generate_fallback_embedding(text)
    
    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate fallback embedding menggunakan hash-based approach"""
        # Normalize text
        normalized_text = text.lower().strip()
        
        # Generate hash
        text_hash = hashlib.sha256(normalized_text.encode('utf-8')).digest()
        
        # Convert hash to embedding vector
        embedding = []
        for i in range(0, len(text_hash), 4):
            # Take 4 bytes and convert to float
            chunk = text_hash[i:i+4]
            if len(chunk) == 4:
                # Convert bytes to float (0-1 range)
                value = struct.unpack('>I', chunk)[0] / (2**32 - 1)
                embedding.append(value)
            else:
                # Pad with zeros if needed
                embedding.append(0.0)
        
        # Ensure we have the right dimension
        while len(embedding) < self.embedding_dim:
            embedding.append(0.0)
        
        # Truncate if too long
        embedding = embedding[:self.embedding_dim]
        
        # Normalize to unit vector
        norm = math.sqrt(sum(x*x for x in embedding))
        if norm > 0:
            embedding = [x/norm for x in embedding]
        
        logger.debug(f"Generated fallback embedding for text: {text[:50]}...")
        return embedding
    
    def embed_text(self, text: str) -> List[float]:
        """Buat embedding untuk single text menggunakan provider yang dikonfigurasi"""
        if not text or not text.strip():
            return [0.0] * self.embedding_dim
        
        # Check cache first
        cached_embedding = self._get_from_cache(text)
        if cached_embedding:
            return cached_embedding
        
        # Try OpenAI first if configured
        if self.provider in ['openai', 'hybrid'] and self.openai_service and self.openai_service.is_available():
            try:
                embedding = self.openai_service.embed_text(text)
                if embedding and len(embedding) > 0:
                    self.stats['openai_usage'] += 1
                    self._save_to_cache(text, embedding)
                    return embedding
            except Exception as e:
                logger.warning(f"⚠️ OpenAI embedding failed: {e}")
                if self.provider == 'openai':
                    # If OpenAI is primary provider and fails, use fallback
                    self.stats['fallback_usage'] += 1
                    return self._generate_fallback_embedding(text)
        
        # Sentence Transformers removed - using OpenAI only
        
        # Fallback to hash-based embedding
        logger.warning("⚠️ All embedding services failed, using fallback")
        self.stats['fallback_usage'] += 1
        return self._generate_fallback_embedding(text)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Buat embedding untuk multiple texts secara batch menggunakan provider yang dikonfigurasi"""
        if not texts:
            return []
        
        # Filter empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            return [[0.0] * self.embedding_dim] * len(texts)
        
        # Check cache untuk semua texts
        cached_embeddings = {}
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(valid_texts):
            cached_embedding = self._get_from_cache(text)
            if cached_embedding:
                cached_embeddings[i] = cached_embedding
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Generate embeddings untuk uncached texts
        if uncached_texts:
            # Try OpenAI first if configured
            if self.provider in ['openai', 'hybrid'] and self.openai_service and self.openai_service.is_available():
                try:
                    new_embeddings = self.openai_service.embed_texts(uncached_texts)
                    if new_embeddings and len(new_embeddings) == len(uncached_texts):
                        # Save to cache dan update results
                        for i, (text, embedding) in enumerate(zip(uncached_texts, new_embeddings)):
                            cached_embeddings[uncached_indices[i]] = embedding
                            self._save_to_cache(text, embedding)
                        
                        self.stats['openai_usage'] += len(uncached_texts)
                        return [cached_embeddings.get(i, [0.0] * self.embedding_dim) for i in range(len(texts))]
                except Exception as e:
                    logger.warning(f"⚠️ OpenAI batch embedding failed: {e}")
                    if self.provider == 'openai':
                        # If OpenAI is primary provider and fails, use fallback
                        for i, text in zip(uncached_indices, uncached_texts):
                            cached_embeddings[i] = self._generate_fallback_embedding(text)
                        self.stats['fallback_usage'] += len(uncached_texts)
                        return [cached_embeddings.get(i, [0.0] * self.embedding_dim) for i in range(len(texts))]
            
            # Sentence Transformers removed - using OpenAI only
            # No valid provider, use fallback
            for i, text in zip(uncached_indices, uncached_texts):
                cached_embeddings[i] = self._generate_fallback_embedding(text)
            self.stats['fallback_usage'] += len(uncached_texts)
        
        # Return embeddings in original order
        return [cached_embeddings.get(i, [0.0] * self.embedding_dim) for i in range(len(texts))]
    
    def add_documents_to_qdrant(self, company_id: str, documents: List[Dict[str, Any]], 
                               collection: str = 'default') -> List[str]:
        """Add documents to Qdrant with embeddings"""
        try:
            if not self.qdrant_service:
                logger.warning("Qdrant service not available")
                return []
            
            # Extract texts - support both 'content' and 'text' keys
            texts = []
            for doc in documents:
                text = doc.get('content', doc.get('text', ''))
                texts.append(text)
            
            # Generate embeddings
            embeddings = self.embed_texts(texts)
            
            # Prepare documents for Qdrant - use the format expected by qdrant service
            qdrant_docs = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                text = doc.get('content', doc.get('text', ''))
                doc_id = doc.get('id', doc.get('metadata', {}).get('id', f'doc_{i}'))
                
                qdrant_docs.append({
                    'id': doc_id,
                    'text': text,
                    'embedding': embedding,  # Include embedding in document
                    'metadata': {
                        **doc.get('metadata', {}),
                        'company_id': company_id,
                        'collection': collection
                    }
                })
            
            # Add to Qdrant using the correct method signature
            result = self.qdrant_service.add_documents(
                company_id=company_id,
                documents=qdrant_docs,
                collection=collection
            )
            
            logger.info(f"✅ Added {len(result)} documents to Qdrant")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents to Qdrant: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        cache_hit_rate = 0
        if self.stats['cache_hits'] + self.stats['cache_misses'] > 0:
            cache_hit_rate = self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses'])
        
        return {
            'model_name': self.model_name,
            'model_loaded': self.model_loaded,
            'embedding_dimension': self.embedding_dim,
            'provider': self.provider,
            'cache_size': len(self.embedding_cache),
            'cache_max_size': self.cache_max_size,
            'cache_hit_rate': round(cache_hit_rate, 3),
            'total_embeddings': self.stats['total_embeddings'],
            'model_load_time': round(self.stats['model_load_time'], 2),
            'avg_embedding_time': round(self.stats['avg_embedding_time'], 3),
            'fallback_usage': self.stats['fallback_usage'],
            'openai_usage': self.stats['openai_usage'],
            'sentence_transformer_usage': 0,  # Deprecated
            'openai_available': self.openai_service is not None and self.openai_service.is_available(),
            'sentence_transformers_available': False,  # Deprecated
            'qdrant_available': self.qdrant_service is not None
        }
    
    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache.clear()
        logger.info("🧹 Embedding cache cleared")
    
    def is_available(self) -> bool:
        """Check apakah service tersedia"""
        return self.openai_service is not None and self.openai_service.is_available()


# Global service instance
_unified_embedding_service = None

def get_unified_embedding_service() -> UnifiedEmbeddingService:
    """Get global unified embedding service instance"""
    global _unified_embedding_service
    if _unified_embedding_service is None:
        _unified_embedding_service = UnifiedEmbeddingService()
    return _unified_embedding_service

# Backward compatibility aliases
def get_embedding_service() -> UnifiedEmbeddingService:
    """Backward compatibility alias"""
    return get_unified_embedding_service()

def get_local_embedding_service() -> UnifiedEmbeddingService:
    """Backward compatibility alias"""
    return get_unified_embedding_service()
