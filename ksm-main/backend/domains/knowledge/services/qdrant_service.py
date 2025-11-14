#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qdrant Service untuk KSM Main Backend
Service untuk mengelola vector database menggunakan Qdrant.io
"""

import os
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError as e:
    QDRANT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ Qdrant dependencies not available: {e}")

logger = logging.getLogger(__name__)

class QdrantService:
    """Service untuk mengelola Qdrant.io vector database dengan fallback support"""
    
    def __init__(self):
        # Initialize availability status
        self.qdrant_available = QDRANT_AVAILABLE
        
        if not QDRANT_AVAILABLE:
            logger.warning("⚠️ Qdrant dependencies not available, service will be disabled")
            self.client = None
            self.collections = {}
            return
            
        # Konfigurasi Qdrant
        # Gunakan environment variable QDRANT_URL jika ada, jika tidak gunakan default
        # Default untuk Docker: qdrant-dev:6333, untuk local: localhost:6333
        default_url = 'http://qdrant-dev:6333' if os.environ.get('FLASK_ENV') == 'development' else 'http://localhost:6333'
        self.url = os.environ.get('QDRANT_URL', default_url)
        self.api_key = os.environ.get('QDRANT_API_KEY', None)
        self.collection_prefix = os.environ.get('QDRANT_COLLECTION_PREFIX', 'KSM')
        # Vector size for OpenAI embeddings
        self.vector_size = int(os.environ.get('QDRANT_VECTOR_SIZE', '1536'))  # OpenAI embeddings
        self.batch_size = int(os.environ.get('QDRANT_BATCH_SIZE', '100'))
        
        # OpenAI configuration
        self.openai_api_key = os.environ.get('OPENAI_API_KEY', None)
        
        # Initialize Qdrant client
        self.client = None
        self.collections = {}
        
        # Initialize services
        self._init_qdrant()
        
        logger.info("🚀 Qdrant Service initialized successfully")
    
    def is_available(self) -> bool:
        """Check apakah Qdrant tersedia"""
        return self.qdrant_available
    
    def _init_qdrant(self):
        """Initialize Qdrant client"""
        if not QDRANT_AVAILABLE:
            logger.warning("⚠️ Qdrant not available, skipping client initialization")
            self.qdrant_available = False
            return
            
        try:
            # Only use API key if it's provided and URL is not localhost
            if self.api_key and not self.url.startswith('http://localhost'):
                self.client = QdrantClient(
                    url=self.url,
                    api_key=self.api_key
                )
            else:
                self.client = QdrantClient(
                    url=self.url
                )
            
            # Test connection
            collections = self.client.get_collections()
            logger.info(f"✅ Qdrant client initialized successfully. Found {len(collections.collections)} collections")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Qdrant client: {e}")
            logger.warning("Running in fallback mode without Qdrant")
            self.qdrant_available = False
            self.client = None
    
    def _get_collection_name(self, company_id: str, collection: str = 'default') -> str:
        """Generate collection name untuk company dan collection"""
        normalized = collection or 'default'
        return f"{self.collection_prefix}_{company_id}_{normalized}"
    
    def _get_or_create_collection(self, company_id: str, collection: str = 'default'):
        """Get atau create collection untuk company"""
        collection_name = self._get_collection_name(company_id, collection or 'default')
        
        if collection_name not in self.collections:
            try:
                # Coba get existing collection
                collection_info = self.client.get_collection(collection_name)
                logger.info(f"📋 Retrieved existing collection: {collection_name}")
                self.collections[collection_name] = collection_info
            except Exception:
                # Create new collection jika belum ada
                try:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=self.vector_size,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"🆕 Created new collection: {collection_name}")
                    self.collections[collection_name] = collection_name
                    
                    # Create index for company_id to avoid filter errors
                    try:
                        from qdrant_client.models import CreateFieldIndex
                        self.client.create_payload_index(
                            collection_name=collection_name,
                            field_name="metadata.company_id",
                            field_schema="keyword"
                        )
                        logger.info(f"✅ Created index for metadata.company_id in {collection_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to create index for metadata.company_id: {e}")
                        
                except Exception as e:
                    if "already exists" in str(e):
                        # Collection already exists, just retrieve it
                        logger.info(f"📋 Collection {collection_name} already exists, retrieving...")
                        collection_info = self.client.get_collection(collection_name)
                        self.collections[collection_name] = collection_info
                    else:
                        logger.error(f"❌ Failed to create collection {collection_name}: {e}")
                        raise
        
        return collection_name
    
    def add_documents(self, company_id: str = None, documents: List[Dict[str, Any]] = None, 
                     collection: str = 'default', **kwargs) -> List[str]:
        """Add documents ke Qdrant collection dengan fallback.

        Mendukung dua bentuk pemanggilan:
        1) add_documents(company_id, documents=[{text, ...}], collection='rag')
        2) add_documents(collection_name='company_1_rag', documents=["text", ...], metadatas=[...], ids=[...], embeddings=[...])
        """
        if not self.qdrant_available:
            logger.warning("Qdrant tidak tersedia, skip adding documents")
            return []
        
        if not QDRANT_AVAILABLE or not self.client:
            logger.warning("⚠️ Qdrant not available, returning empty document IDs")
            return []
        
        try:
            # Path 2: Advanced signature via kwargs
            if 'collection_name' in kwargs and isinstance(kwargs.get('documents'), list) and kwargs.get('ids') is not None:
                collection_name = kwargs['collection_name']
                ids = kwargs.get('ids') or []
                texts = kwargs.get('documents') or []
                metadatas = kwargs.get('metadatas') or [{} for _ in texts]
                embeddings = kwargs.get('embeddings')  # required
                
                if not ids or not texts or not embeddings:
                    return []
                
                # Ensure collection exists
                self._get_or_create_collection_by_name(collection_name)
                
                # Prepare points
                points = []
                for i, (doc_id, text, metadata, embedding) in enumerate(zip(ids, texts, metadatas, embeddings)):
                    point = PointStruct(
                        id=doc_id,
                        vector=embedding,
                        payload={
                            'text': text,
                            'metadata': metadata,
                            'created_at': datetime.now().isoformat()
                        }
                    )
                    points.append(point)
                
                # Add in batch
                batch_size = self.batch_size
                all_ids = []
                for i in range(0, len(points), batch_size):
                    batch_points = points[i:i + batch_size]
                    self.client.upsert(
                        collection_name=collection_name,
                        points=batch_points
                    )
                    all_ids.extend([p.id for p in batch_points])
                
                logger.info(f"✅ Added {len(all_ids)} documents to collection: {collection_name}")
                return all_ids

            # Path 1: Standard signature
            if not documents or company_id is None:
                logger.warning("⚠️ Missing required parameters for standard path")
                return []
            
            # Get or create collection
            collection_name = self._get_or_create_collection(company_id, collection)
            
            # Prepare data
            points = []
            for i, doc in enumerate(documents):
                # Generate UUID-based ID for Qdrant compatibility
                import uuid
                doc_id = doc.get('id') or str(uuid.uuid4())
                
                # Get embedding from document
                embedding = doc.get('embedding')
                if not embedding:
                    logger.warning(f"⚠️ No embedding found for document {doc_id}")
                    continue
                
                # Clean metadata - remove None values and ensure proper types
                metadata = {
                    'company_id': str(company_id),
                    'collection': str(collection),
                    'created_at': datetime.now().isoformat()
                }
                
                # Add optional fields only if they exist and are not None
                if doc.get('chunk_id') is not None:
                    metadata['chunk_id'] = str(doc.get('chunk_id'))
                if doc.get('document_id') is not None:
                    metadata['document_id'] = str(doc.get('document_id'))
                if doc.get('page_from') is not None:
                    metadata['page_from'] = int(doc.get('page_from'))
                if doc.get('page_to') is not None:
                    metadata['page_to'] = int(doc.get('page_to'))
                if doc.get('chunk_index') is not None:
                    metadata['chunk_index'] = int(doc.get('chunk_index'))
                if doc.get('section_title') is not None:
                    metadata['section_title'] = str(doc.get('section_title'))
                
                point = PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={
                        'text': doc.get('text', ''),
                        'metadata': metadata
                    }
                )
                points.append(point)
            
            if not points:
                logger.warning("⚠️ No valid points to add")
                return []
            
            # Add in batch
            batch_size = self.batch_size
            all_ids = []
            for i in range(0, len(points), batch_size):
                batch_points = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch_points
                )
                all_ids.extend([p.id for p in batch_points])
                logger.info(f"📄 Added batch {i//batch_size + 1}: {len(batch_points)} documents")
            
            logger.info(f"✅ Added {len(all_ids)} documents to collection: {collection_name}")
            return all_ids
            
        except Exception as e:
            logger.error(f"❌ Error adding documents: {e}")
            return []
    
    def upsert_points(self, *, collection_name: Optional[str] = None, company_id: Optional[str] = None,
                      collection: str = 'default', points: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Upsert points ke Qdrant secara modular.
        
        - Jika `collection_name` diberikan, gunakan langsung.
        - Jika tidak, gunakan `company_id` + `collection` untuk membentuk nama koleksi.
        - `points` berupa list dict: {id, vector, payload}
        
        Return: dict standar { success, message, data }
        """
        if not self.qdrant_available or not QDRANT_AVAILABLE or not self.client:
            return { 'success': False, 'message': 'Qdrant tidak tersedia', 'data': {} }
        
        try:
            if not points or not isinstance(points, list):
                return { 'success': False, 'message': 'points is required (list)', 'data': {} }
            
            # Tentukan nama koleksi
            target_collection = collection_name or (self._get_collection_name(str(company_id), collection))
            if not target_collection:
                return { 'success': False, 'message': 'collection_name atau company_id diperlukan', 'data': {} }
            
            # Pastikan koleksi ada
            self._get_or_create_collection_by_name(target_collection)
            self._ensure_collection_indexes(target_collection)
            
            # Normalisasi points ke PointStruct
            qdrant_points: List[PointStruct] = []
            for p in points:
                pid = p.get('id') or str(uuid.uuid4())
                vector = p.get('vector')
                payload = p.get('payload', {})
                if vector is None:
                    # Skip jika tidak ada vektor
                    continue
                qdrant_points.append(
                    PointStruct(
                        id=pid,
                        vector=vector,
                        payload=payload
                    )
                )
            
            if not qdrant_points:
                return { 'success': False, 'message': 'Tidak ada point valid untuk di-upsert', 'data': {} }
            
            # Batch upsert
            operation_ids: List[int] = []
            total = 0
            for i in range(0, len(qdrant_points), self.batch_size):
                batch = qdrant_points[i:i+self.batch_size]
                op = self.client.upsert(collection_name=target_collection, points=batch)
                # op: {'result': {'status': 'acknowledged', 'operation_id': X}, 'status': 'ok', ...}
                try:
                    operation_id = getattr(op, 'operation_id', None)
                    if operation_id is None and isinstance(op, dict):
                        operation_id = op.get('result', {}).get('operation_id')
                    if operation_id is not None:
                        operation_ids.append(int(operation_id))
                except Exception:
                    pass
                total += len(batch)
            
            return {
                'success': True,
                'message': f'Upsert {total} points ke {target_collection} berhasil',
                'data': {
                    'collection_name': target_collection,
                    'points_upserted': total,
                    'operation_ids': operation_ids
                }
            }
        except Exception as e:
            logger.error(f"❌ Error upserting points: {e}")
            return { 'success': False, 'message': str(e), 'data': {} }

    def _build_filter(self, filter_input: Any) -> Optional[Filter]:
        """Bangun Qdrant Filter dari input sederhana.
        Mendukung dua bentuk:
        - dict mapping sederhana: { "metadata.company_id": "abc", "chunk_index": 1 }
        - bentuk Qdrant-like: { "must": [ {"key": "metadata.company_id", "value": "abc"}, ... ] }
        """
        try:
            if not filter_input:
                return None
            conditions = []
            # Bentuk Qdrant-like
            if isinstance(filter_input, dict) and any(k in filter_input for k in ('must', 'should', 'must_not')):
                for cond in filter_input.get('must', []) or []:
                    key = cond.get('key')
                    value = cond.get('value', cond.get('match', {}).get('value') if isinstance(cond.get('match'), dict) else None)
                    if key is not None and value is not None:
                        conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
                # Catatan: untuk kesederhanaan, only 'must' didukung saat ini
                return Filter(must=conditions) if conditions else None
            # Bentuk mapping sederhana
            if isinstance(filter_input, dict):
                for key, value in filter_input.items():
                    conditions.append(FieldCondition(key=str(key), match=MatchValue(value=value)))
                return Filter(must=conditions) if conditions else None
            return None
        except Exception as e:
            logger.warning(f"Gagal membangun filter: {e}")
            return None

    def delete_points(self, *, collection_name: Optional[str] = None, company_id: Optional[str] = None,
                      collection: str = 'default', ids: Optional[List[Any]] = None, 
                      filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Hapus points dari Qdrant dengan ids atau filter.
        Return: dict standar { success, message, data }
        """
        if not self.qdrant_available or not QDRANT_AVAILABLE or not self.client:
            return { 'success': False, 'message': 'Qdrant tidak tersedia', 'data': {} }
        try:
            target_collection = collection_name or (self._get_collection_name(str(company_id), collection))
            if not target_collection:
                return { 'success': False, 'message': 'collection_name atau company_id diperlukan', 'data': {} }
            # Pastikan koleksi ada (akan create jika belum ada)
            self._get_or_create_collection_by_name(target_collection)
            operation_ids: List[int] = []
            total_deleted = 0
            # Hapus berdasarkan ids jika ada
            if ids and isinstance(ids, list) and len(ids) > 0:
                op = self.client.delete(collection_name=target_collection, points_selector=ids)
                try:
                    operation_id = getattr(op, 'operation_id', None)
                    if operation_id is None and isinstance(op, dict):
                        operation_id = op.get('result', {}).get('operation_id')
                    if operation_id is not None:
                        operation_ids.append(int(operation_id))
                except Exception:
                    pass
                total_deleted += len(ids)
            # Hapus berdasarkan filter jika ada
            elif filter:
                qdr_filter = self._build_filter(filter)
                if not qdr_filter:
                    return { 'success': False, 'message': 'Filter tidak valid', 'data': {} }
                # Qdrant delete by filter menggunakan dict-compatible selector
                # SDK modern menerima dict: {"filter": {...}}
                selector = { 'filter': qdr_filter.dict() if hasattr(qdr_filter, 'dict') else qdr_filter }
                op = self.client.delete(collection_name=target_collection, points_selector=selector)
                try:
                    operation_id = getattr(op, 'operation_id', None)
                    if operation_id is None and isinstance(op, dict):
                        operation_id = op.get('result', {}).get('operation_id')
                    if operation_id is not None:
                        operation_ids.append(int(operation_id))
                except Exception:
                    pass
            else:
                return { 'success': False, 'message': 'ids atau filter diperlukan', 'data': {} }
            return {
                'success': True,
                'message': f'Delete points dari {target_collection} diproses',
                'data': {
                    'collection_name': target_collection,
                    'operation_ids': operation_ids,
                    'requested_deletions': total_deleted if total_deleted > 0 else None
                }
            }
        except Exception as e:
            logger.error(f"❌ Error deleting points: {e}")
            return { 'success': False, 'message': str(e), 'data': {} }

    def scroll_points(self, *, collection_name: Optional[str] = None, company_id: Optional[str] = None,
                      collection: str = 'default', filter: Optional[Dict[str, Any]] = None,
                      limit: int = 10, with_payload: bool = True, with_vectors: bool = False,
                      offset: Optional[Any] = None) -> Dict[str, Any]:
        """Scroll points dari Qdrant dengan dukungan filter dan pagination offset.
        Return: dict standar { success, message, data: { points, next_page_offset } }
        """
        if not self.qdrant_available or not QDRANT_AVAILABLE or not self.client:
            return { 'success': False, 'message': 'Qdrant tidak tersedia', 'data': {} }
        try:
            target_collection = collection_name or (self._get_collection_name(str(company_id), collection))
            if not target_collection:
                return { 'success': False, 'message': 'collection_name atau company_id diperlukan', 'data': {} }
            
            qdr_filter = self._build_filter(filter) if filter else None
            
            kwargs: Dict[str, Any] = {
                'collection_name': target_collection,
                'limit': int(limit),
                'with_payload': with_payload,
                'with_vectors': with_vectors
            }
            if qdr_filter:
                kwargs['scroll_filter'] = qdr_filter
            if offset is not None:
                kwargs['offset'] = offset
            
            res_points, next_page = self.client.scroll(**kwargs)
            points_out: List[Dict[str, Any]] = []
            for p in res_points or []:
                points_out.append({
                    'id': getattr(p, 'id', None),
                    'payload': getattr(p, 'payload', None),
                    'vector': getattr(p, 'vector', None),
                    'shard_key': getattr(p, 'shard_key', None)
                })
            return {
                'success': True,
                'message': 'Scroll berhasil',
                'data': {
                    'points': points_out,
                    'next_page_offset': next_page
                }
            }
        except Exception as e:
            logger.error(f"❌ Error scrolling points: {e}")
            return { 'success': False, 'message': str(e), 'data': {} }

    def count_points(self, *, collection_name: Optional[str] = None, company_id: Optional[str] = None,
                     collection: str = 'default', filter: Optional[Dict[str, Any]] = None,
                     exact: bool = True) -> Dict[str, Any]:
        """Hitung jumlah points pada collection dengan optional filter.
        Return: { success, message, data: { count } }
        """
        if not self.qdrant_available or not QDRANT_AVAILABLE or not self.client:
            return { 'success': False, 'message': 'Qdrant tidak tersedia', 'data': {} }
        try:
            target_collection = collection_name or (self._get_collection_name(str(company_id), collection))
            if not target_collection:
                return { 'success': False, 'message': 'collection_name atau company_id diperlukan', 'data': {} }
            qdr_filter = self._build_filter(filter) if filter else None
            kwargs: Dict[str, Any] = {
                'collection_name': target_collection,
                'exact': bool(exact)
            }
            if qdr_filter:
                kwargs['count_filter'] = qdr_filter
            res = self.client.count(**kwargs)
            # res may be CountResponse or dict
            count_val = None
            try:
                count_val = getattr(res, 'count', None)
                if count_val is None and isinstance(res, dict):
                    count_val = res.get('result', {}).get('count') or res.get('count')
            except Exception:
                pass
            if count_val is None:
                # fallback to 0 if not present
                count_val = 0
            return {
                'success': True,
                'message': 'Count berhasil',
                'data': {
                    'count': int(count_val)
                }
            }
        except Exception as e:
            logger.error(f"❌ Error counting points: {e}")
            return { 'success': False, 'message': str(e), 'data': {} }

    def retrieve_points(self, *, collection_name: Optional[str] = None, company_id: Optional[str] = None,
                        collection: str = 'default', ids: Optional[List[Any]] = None,
                        with_payload: bool = True, with_vectors: bool = False) -> Dict[str, Any]:
        """Ambil poin berdasarkan IDs dengan opsi payload dan vectors.
        Return: { success, message, data: [ {id, payload, vector, shard_key, order_value} ] }
        """
        if not self.qdrant_available or not QDRANT_AVAILABLE or not self.client:
            return { 'success': False, 'message': 'Qdrant tidak tersedia', 'data': {} }
        try:
            target_collection = collection_name or (self._get_collection_name(str(company_id), collection))
            if not target_collection:
                return { 'success': False, 'message': 'collection_name atau company_id diperlukan', 'data': {} }
            if not ids or not isinstance(ids, list):
                return { 'success': False, 'message': 'ids (list) diperlukan', 'data': {} }
            res = self.client.retrieve(
                collection_name=target_collection,
                ids=ids,
                with_payload=with_payload,
                with_vectors=with_vectors
            )
            out = []
            for p in res or []:
                out.append({
                    'id': getattr(p, 'id', None),
                    'payload': getattr(p, 'payload', None),
                    'vector': getattr(p, 'vector', None),
                    'shard_key': getattr(p, 'shard_key', None),
                    'order_value': getattr(p, 'order_value', None)
                })
            return {
                'success': True,
                'message': 'Retrieve berhasil',
                'data': out
            }
        except Exception as e:
            logger.error(f"❌ Error retrieving points: {e}")
            return { 'success': False, 'message': str(e), 'data': {} }

    def set_payload(self, *, collection_name: Optional[str] = None, company_id: Optional[str] = None,
                    collection: str = 'default', payload: Optional[Dict[str, Any]] = None,
                    ids: Optional[List[Any]] = None, filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Set payload untuk points terpilih (by ids atau filter). Return: standar result."""
        if not self.qdrant_available or not QDRANT_AVAILABLE or not self.client:
            return { 'success': False, 'message': 'Qdrant tidak tersedia', 'data': {} }
        try:
            if not payload or not isinstance(payload, dict):
                return { 'success': False, 'message': 'payload (dict) diperlukan', 'data': {} }
            target_collection = collection_name or (self._get_collection_name(str(company_id), collection))
            if not target_collection:
                return { 'success': False, 'message': 'collection_name atau company_id diperlukan', 'data': {} }
            # pastikan koleksi ada
            self._get_or_create_collection_by_name(target_collection)
            # ids vs filter
            if ids and isinstance(ids, list) and len(ids) > 0:
                op = self.client.set_payload(collection_name=target_collection, payload=payload, points=ids)
            elif filter:
                qdr_filter = self._build_filter(filter)
                if not qdr_filter:
                    return { 'success': False, 'message': 'Filter tidak valid', 'data': {} }
                selector = { 'filter': qdr_filter.dict() if hasattr(qdr_filter, 'dict') else qdr_filter }
                op = self.client.set_payload(collection_name=target_collection, payload=payload, points=selector)
            else:
                return { 'success': False, 'message': 'ids atau filter diperlukan', 'data': {} }
            operation_id = None
            try:
                operation_id = getattr(op, 'operation_id', None)
                if operation_id is None and isinstance(op, dict):
                    operation_id = op.get('result', {}).get('operation_id')
            except Exception:
                pass
            return {
                'success': True,
                'message': 'Set payload diproses',
                'data': {
                    'collection_name': target_collection,
                    'operation_id': operation_id
                }
            }
        except Exception as e:
            logger.error(f"❌ Error setting payload: {e}")
            return { 'success': False, 'message': str(e), 'data': {} }

    def update_vectors(self, *, collection_name: Optional[str] = None, company_id: Optional[str] = None,
                       collection: str = 'default', vectors: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Update vectors saja tanpa menyentuh payload menggunakan REST API Qdrant.
        Input vectors: [{ "id": <id>, "vector": [..] }]
        """
        if not self.qdrant_available or not QDRANT_AVAILABLE or not self.client:
            return { 'success': False, 'message': 'Qdrant tidak tersedia', 'data': {} }
        try:
            if not vectors or not isinstance(vectors, list):
                return { 'success': False, 'message': 'vectors (list) diperlukan', 'data': {} }
            target_collection = collection_name or (self._get_collection_name(str(company_id), collection))
            if not target_collection:
                return { 'success': False, 'message': 'collection_name atau company_id diperlukan', 'data': {} }
            # Gunakan raw HTTP untuk endpoint update vectors agar tidak mengubah payload
            import httpx
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            operation_ids: List[int] = []
            total = 0
            for i in range(0, len(vectors), self.batch_size):
                batch = vectors[i:i+self.batch_size]
                body = { 'points': [{ 'id': v.get('id'), 'vector': v.get('vector') } for v in batch] }
                # Validasi minimal
                body['points'] = [p for p in body['points'] if p.get('id') is not None and p.get('vector') is not None]
                if not body['points']:
                    continue
                url = f"{self.url}/collections/{target_collection}/points/vectors"
                resp = httpx.put(url, json=body, headers=headers, timeout=30.0)
                if resp.status_code >= 200 and resp.status_code < 300:
                    try:
                        j = resp.json()
                        op_id = (j or {}).get('result', {}).get('operation_id')
                        if op_id is not None:
                            operation_ids.append(int(op_id))
                    except Exception:
                        pass
                    total += len(body['points'])
                else:
                    raise Exception(f"HTTP {resp.status_code}: {resp.text}")
            return {
                'success': True,
                'message': f'Update {total} vectors ke {target_collection} berhasil',
                'data': {
                    'collection_name': target_collection,
                    'vectors_updated': total,
                    'operation_ids': operation_ids
                }
            }
        except Exception as e:
            logger.error(f"❌ Error updating vectors: {e}")
            return { 'success': False, 'message': str(e), 'data': {} }
    
    def create_payload_index(self, *, collection_name: Optional[str] = None, company_id: Optional[str] = None,
                              collection: str = 'default', field_name: str = None, field_schema: str = 'keyword') -> Dict[str, Any]:
        """Buat payload index pada collection tertentu.
        - Jika `collection_name` tidak diberikan, akan dibentuk dari `company_id` + `collection`.
        - `field_name` contoh: "metadata.company_id", "payload.some_field" (sesuai skema payload).
        - `field_schema` biasanya 'keyword' atau tipe lain yang didukung Qdrant.
        Return standar: { success, message, data: { collection_name, field_name, field_schema, operation_id } }
        """
        if not self.qdrant_available or not QDRANT_AVAILABLE or not self.client:
            return { 'success': False, 'message': 'Qdrant tidak tersedia', 'data': {} }
        try:
            if not field_name or not isinstance(field_name, str):
                return { 'success': False, 'message': 'field_name (str) diperlukan', 'data': {} }
            target_collection = collection_name or (self._get_collection_name(str(company_id), collection))
            if not target_collection:
                return { 'success': False, 'message': 'collection_name atau company_id diperlukan', 'data': {} }

            # Pastikan koleksi ada
            self._get_or_create_collection_by_name(target_collection)

            op = self.client.create_payload_index(
                collection_name=target_collection,
                field_name=field_name,
                field_schema=field_schema
            )
            operation_id = None
            try:
                operation_id = getattr(op, 'operation_id', None)
                if operation_id is None and isinstance(op, dict):
                    operation_id = op.get('result', {}).get('operation_id')
            except Exception:
                pass
            return {
                'success': True,
                'message': 'Payload index dibuat',
                'data': {
                    'collection_name': target_collection,
                    'field_name': field_name,
                    'field_schema': field_schema,
                    'operation_id': operation_id
                }
            }
        except Exception as e:
            logger.error(f"❌ Error creating payload index: {e}")
            return { 'success': False, 'message': str(e), 'data': {} }

    def delete_payload_index(self, *, collection_name: Optional[str] = None, company_id: Optional[str] = None,
                              collection: str = 'default', field_name: str = None) -> Dict[str, Any]:
        """Hapus payload index pada collection tertentu.
        - Jika `collection_name` tidak diberikan, akan dibentuk dari `company_id` + `collection`.
        - `field_name` contoh: "metadata.company_id".
        Return standar: { success, message, data: { collection_name, field_name, operation_id } }
        """
        if not self.qdrant_available or not QDRANT_AVAILABLE or not self.client:
            return { 'success': False, 'message': 'Qdrant tidak tersedia', 'data': {} }
        try:
            if not field_name or not isinstance(field_name, str):
                return { 'success': False, 'message': 'field_name (str) diperlukan', 'data': {} }
            target_collection = collection_name or (self._get_collection_name(str(company_id), collection))
            if not target_collection:
                return { 'success': False, 'message': 'collection_name atau company_id diperlukan', 'data': {} }

            # Pastikan koleksi ada
            self._get_or_create_collection_by_name(target_collection)

            op = self.client.delete_payload_index(
                collection_name=target_collection,
                field_name=field_name
            )
            operation_id = None
            try:
                operation_id = getattr(op, 'operation_id', None)
                if operation_id is None and isinstance(op, dict):
                    operation_id = op.get('result', {}).get('operation_id')
            except Exception:
                pass
            return {
                'success': True,
                'message': 'Payload index dihapus',
                'data': {
                    'collection_name': target_collection,
                    'field_name': field_name,
                    'operation_id': operation_id
                }
            }
        except Exception as e:
            logger.error(f"❌ Error deleting payload index: {e}")
            return { 'success': False, 'message': str(e), 'data': {} }

    def _get_or_create_collection_by_name(self, collection_name: str):
        """Get atau create collection by direct name"""
        try:
            self.client.get_collection(collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"🆕 Created new collection: {collection_name}")
    
    def _ensure_collection_indexes(self, collection_name: str):
        """Ensure required indexes exist for collection"""
        try:
            # Create index for company_id if it doesn't exist
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="metadata.company_id",
                field_schema="keyword"
            )
            logger.info(f"✅ Ensured index for metadata.company_id in {collection_name}")
        except Exception as e:
            # Index might already exist, which is fine
            logger.debug(f"Index creation result for {collection_name}: {e}")

    def search_documents(self, company_id: str, query: str, top_k: int = 10, 
                        collection: str = 'default', filters: Optional[Dict] = None, 
                        query_embedding: Optional[List[float]] = None) -> List[Dict[str, Any]]:
        """Search documents di Qdrant collection dengan fallback"""
        if not self.qdrant_available:
            logger.warning("Qdrant tidak tersedia, return empty search results")
            return []
        
        if not QDRANT_AVAILABLE or not self.client:
            logger.warning("⚠️ Qdrant not available, returning empty search results")
            return []
            
        try:
            if not query_embedding:
                logger.warning("⚠️ No query embedding provided for search")
                return []
            
            # Get collection
            collection_name = self._get_or_create_collection(company_id, collection or 'default')
            
            # Ensure indexes exist
            self._ensure_collection_indexes(collection_name)
            
            # Prepare filter
            search_filter = None
            if filters or company_id:
                conditions = []
                if company_id:
                    conditions.append(
                        FieldCondition(
                            key="metadata.company_id",
                            match=MatchValue(value=company_id)
                        )
                    )
                if filters:
                    for key, value in filters.items():
                        conditions.append(
                            FieldCondition(
                                key=f"metadata.{key}",
                                match=MatchValue(value=value)
                            )
                        )
                search_filter = Filter(must=conditions)
            
            # Gunakan SDK resmi agar format body selalu sesuai versi Qdrant
            response = self.client.query_points(
                collection_name=collection_name,
                query=query_embedding,
                limit=int(top_k),
                with_payload=True,
                query_filter=search_filter
            )

            # Extract hits dari QueryResponse object
            hits = getattr(response, 'points', []) if hasattr(response, 'points') else []

            # Auto-retry tanpa filter jika hasil kosong (untuk kasus metadata/company_id tidak match)
            if (not hits or len(hits) == 0) and search_filter is not None:
                try:
                    logger.info("ℹ️ No hits with filter; retrying without filter for diagnostics")
                    response_no_filter = self.client.query_points(
                        collection_name=collection_name,
                        query=query_embedding,
                        limit=int(top_k),
                        with_payload=True
                    )
                    hits = getattr(response_no_filter, 'points', []) if hasattr(response_no_filter, 'points') else []
                except Exception:
                    pass

            # Normalisasi hasil ke format lama agar non-redundant untuk pemanggil eksisting
            search_results: List[Dict[str, Any]] = []
            for h in hits or []:
                pld = getattr(h, 'payload', None) or {}
                search_results.append({
                    'id': getattr(h, 'id', None),
                    'text': pld.get('text', ''),
                    'metadata': pld.get('metadata', {}),
                    'distance': getattr(h, 'score', None),
                    'similarity_score': getattr(h, 'score', None)
                })
            
            logger.info(f"🔍 Search completed: {len(search_results)} results for query: '{query[:50]}...'")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Error searching documents: {e}")
            return []

    def search_documents_batch(self, *, company_id: str, embeddings: List[List[float]], top_k: int = 10,
                               collection: str = 'default', filters: Optional[List[Optional[Dict]]] = None
                               ) -> List[List[Dict[str, Any]]]:
        """Batch similarity search menggunakan endpoint POST /collections/:collection_name/points/query/batch.

        - embeddings: daftar vektor query.
        - filters: opsional daftar filter per-query (panjang sama dengan embeddings) atau None untuk tanpa filter.
        - Keluaran: list per-query dari list hasil yang sudah ternormalisasi: [{id, text, metadata, distance, similarity_score}]
        """
        if not self.qdrant_available or not QDRANT_AVAILABLE or not self.client:
            return []
        try:
            if not embeddings or not isinstance(embeddings, list):
                return []

            collection_name = self._get_or_create_collection(company_id, collection or 'default')
            self._ensure_collection_indexes(collection_name)

            # Siapkan body batch
            requests_body: List[Dict[str, Any]] = []
            has_per_query_filters = isinstance(filters, list) and len(filters) == len(embeddings)
            for idx, vec in enumerate(embeddings):
                req: Dict[str, Any] = {
                    'query': { 'vector': vec },
                    'limit': int(top_k),
                    'with_payload': True
                }
                # Tambahkan filter per-query jika diberikan
                if has_per_query_filters and filters[idx]:
                    qdr_filter = self._build_filter(filters[idx])
                    if qdr_filter is not None:
                        try:
                            req['filter'] = qdr_filter.dict() if hasattr(qdr_filter, 'dict') else qdr_filter
                        except Exception:
                            pass
                requests_body.append(req)

            import httpx
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            url = f"{self.url}/collections/{collection_name}/points/query/batch"
            resp = httpx.post(url, json={'requests': requests_body}, headers=headers, timeout=60.0)
            if resp.status_code < 200 or resp.status_code >= 300:
                raise Exception(f"HTTP {resp.status_code}: {resp.text}")

            payload_json = resp.json() or {}
            results_groups = payload_json.get('result') or []  # diharapkan list of list

            normalized: List[List[Dict[str, Any]]] = []
            for group in results_groups or []:
                group_out: List[Dict[str, Any]] = []
                for item in group or []:
                    pld = (item or {}).get('payload') or {}
                    group_out.append({
                        'id': item.get('id'),
                        'text': pld.get('text', ''),
                        'metadata': pld.get('metadata', {}),
                        'distance': item.get('score'),
                        'similarity_score': item.get('score')
                    })
                normalized.append(group_out)

            logger.info(f"🔍 Batch search completed: {sum(len(g) for g in normalized)} total results across {len(normalized)} queries")
            return normalized
        except Exception as e:
            logger.error(f"❌ Error batch searching documents: {e}")
            return []
    
    def delete_documents(self, company_id: str, document_ids: List[str], 
                        collection: str = 'default') -> bool:
        """Delete documents dari Qdrant collection dengan fallback"""
        if not self.qdrant_available:
            logger.warning("Qdrant tidak tersedia, skip deleting documents")
            return True
        
        try:
            if not document_ids:
                return True
            
            # Get collection
            collection_name = self._get_or_create_collection(company_id, collection)
            
            # Delete documents
            self.client.delete(
                collection_name=collection_name,
                points_selector=document_ids
            )
            
            logger.info(f"🗑️ Deleted {len(document_ids)} documents from collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting documents: {e}")
            return False
    
    def delete_document_from_qdrant(self, document_id: str) -> Dict[str, Any]:
        """Delete single document dari Qdrant dengan fallback untuk controller"""
        if not self.qdrant_available:
            logger.warning("Qdrant tidak tersedia, skip deleting document")
            return {
                'success': True,
                'message': 'Qdrant tidak tersedia, document dianggap terhapus',
                'data': {
                    'document_id': document_id,
                    'deleted_at': datetime.now().isoformat()
                }
            }
        
        try:
            if not QDRANT_AVAILABLE or not self.client:
                logger.warning("⚠️ Qdrant not available, returning success")
                return {
                    'success': True,
                    'message': 'Qdrant tidak tersedia, document dianggap terhapus',
                    'data': {
                        'document_id': document_id,
                        'deleted_at': datetime.now().isoformat()
                    }
                }
            
            # Cari document di semua collections yang mungkin
            collections = self.client.get_collections()
            deleted_from_collections = []
            
            for collection in collections.collections:
                collection_name = collection.name
                try:
                    # Coba hapus dari collection ini
                    self.client.delete(
                        collection_name=collection_name,
                        points_selector=[document_id]
                    )
                    deleted_from_collections.append(collection_name)
                    logger.info(f"🗑️ Deleted document {document_id} from collection: {collection_name}")
                except Exception as e:
                    # Document mungkin tidak ada di collection ini, lanjutkan
                    logger.debug(f"Document {document_id} not found in {collection_name}: {e}")
                    continue
            
            if deleted_from_collections:
                return {
                    'success': True,
                    'message': f'Document berhasil dihapus dari {len(deleted_from_collections)} collection(s)',
                    'data': {
                        'document_id': document_id,
                        'deleted_from_collections': deleted_from_collections,
                        'deleted_at': datetime.now().isoformat()
                    }
                }
            else:
                return {
                    'success': False,
                    'message': f'Document {document_id} tidak ditemukan di Qdrant',
                    'data': {
                        'document_id': document_id
                    }
                }
            
        except Exception as e:
            logger.error(f"❌ Error deleting document {document_id}: {e}")
            return {
                'success': False,
                'message': f'Gagal menghapus document: {str(e)}',
                'data': {
                    'document_id': document_id
                }
            }
    
    def get_collection_stats(self, company_id: str, collection: str = 'default') -> Dict[str, Any]:
        """Get statistics untuk collection dengan fallback"""
        if not self.qdrant_available:
            return {
                'company_id': company_id,
                'collection': collection,
                'collection_name': f'fallback_{company_id}_{collection}',
                'document_count': 0,
                'vector_size': self.vector_size,
                'distance_function': 'cosine',
                'status': 'qdrant_unavailable'
            }
        
        try:
            collection_name = self._get_or_create_collection(company_id, collection)
            
            # Gunakan raw API call untuk menghindari masalah validasi Pydantic
            import httpx
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = httpx.get(
                f"{self.url}/collections/{collection_name}",
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                detail_data = response.json()
                result = detail_data.get('result', {})
                
                # Ambil data dengan fallback
                points_count = result.get('points_count', 0)
                
                # Ambil config
                config = result.get('config', {})
                params = config.get('params', {})
                vectors_config = params.get('vectors', {})
                
                vector_size = vectors_config.get('size', self.vector_size)
                distance = vectors_config.get('distance', 'Cosine')
                
                return {
                    'company_id': company_id,
                    'collection': collection,
                    'collection_name': collection_name,
                    'document_count': points_count,
                    'vector_size': vector_size,
                    'distance_function': distance.lower() if distance else 'cosine',
                    'status': 'active'
                }
            else:
                raise Exception(f"HTTP {response.status_code}")
            
        except Exception as e:
            # Log error hanya jika bukan masalah validasi Pydantic yang sudah diketahui
            if "validation errors" not in str(e) and "pydantic" not in str(e).lower():
                logger.error(f"❌ Error getting collection stats: {e}")
            return {}
    
    def list_collections(self, company_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List semua collections dengan fallback dan format standar"""
        if not self.qdrant_available:
            return {
                'success': True,
                'data': {
                    'collections': [],
                    'total': 0
                }
            }
        try:
            collections = self.client.get_collections()
            safe_collections: List[Dict[str, Any]] = []
            for collection in getattr(collections, 'collections', []) or []:
                try:
                    # Ambil nama koleksi secara aman
                    collection_name = getattr(collection, 'name', None)
                    if not collection_name:
                        continue
                    # Status harus diambil dari detail collection, bukan dari CollectionDescription
                    info: Dict[str, Any] = {
                        'name': collection_name,
                        'status': 'unknown'  # Default, akan diupdate dari detail
                    }
                    # Tambahkan points_count dan config jika bisa diambil
                    try:
                        # Gunakan raw API call untuk menghindari masalah validasi Pydantic
                        import httpx
                        import json
                        
                        # Ambil detail collection dengan raw HTTP request
                        headers = {"Authorization": f"Bearer {self.api_key}"}
                        response = httpx.get(
                            f"{self.url}/collections/{collection_name}",
                            headers=headers,
                            timeout=10.0
                        )
                        
                        if response.status_code == 200:
                            detail_data = response.json()
                            result = detail_data.get('result', {})
                            
                            # Ambil points count dengan fallback
                            points_count = result.get('points_count', 0)
                            vectors_count = result.get('vectors_count', points_count)
                            indexed_vectors_count = result.get('indexed_vectors_count', points_count)
                            
                            info['points_count'] = int(points_count or 0)
                            info['vectors_count'] = int(vectors_count or 0)
                            info['indexed_vectors_count'] = int(indexed_vectors_count or 0)
                            
                            # Ambil status
                            status = result.get('status', 'unknown')
                            info['status'] = status
                            
                            # Ambil config dengan fallback
                            config = result.get('config', {})
                            params = config.get('params', {})
                            vectors_config = params.get('vectors', {})
                            
                            vector_size = vectors_config.get('size', 1536)
                            distance = vectors_config.get('distance', 'Cosine')
                            
                            info['config'] = {
                                'vector_size': vector_size,
                                'distance': distance
                            }
                        else:
                            # Fallback ke default values jika gagal
                            raise Exception(f"HTTP {response.status_code}")
                            
                    except Exception as inner_e:
                        # Log warning hanya jika bukan masalah validasi Pydantic yang sudah diketahui
                        if "validation errors" not in str(inner_e) and "pydantic" not in str(inner_e).lower():
                            logger.warning(f"Tidak dapat mendapatkan detail untuk {collection_name}: {inner_e}")
                        
                        info['points_count'] = 0
                        info['vectors_count'] = 0
                        info['indexed_vectors_count'] = 0
                        info['status'] = 'unknown'
                        info['config'] = {
                            'vector_size': 1536,
                            'distance': 'Cosine'
                        }
                except Exception as e:
                    logger.warning(f"Error saat memproses koleksi {getattr(collection, 'name', 'unknown')}: {e}")
                    continue
                # Filter berdasarkan company_id jika diberikan
                if company_id and company_id not in collection_name:
                    continue
                safe_collections.append(info)
            return {
                'success': True,
                'data': {
                    'collections': safe_collections,
                    'total': len(safe_collections)
                }
            }
        except Exception as e:
            logger.error(f"❌ Error listing collections: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def query_points_raw(self, collection_name: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Panggil endpoint Qdrant POST /collections/:collection_name/points/query secara raw.

        - Mengembalikan struktur JSON mengikuti Qdrant (usage, time, status, result...)
        - Tidak melakukan transformasi model di sisi server agar fleksibel (modular, non redundancy)
        """
        if not self.qdrant_available:
            return {
                'success': False,
                'message': 'Qdrant tidak tersedia'
            }
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            url = f"{self.url}/collections/{collection_name}/points/query"
            # Kirim body persis seperti diterima agar fleksibel (prefetch, fusion, recommend, dsb.)
            resp = httpx.post(url, json=body or {}, headers=headers, timeout=30.0)
            data = resp.json() if resp.content else {}
            if 200 <= resp.status_code < 300:
                return {
                    'success': True,
                    'data': data
                }
            return {
                'success': False,
                'message': f"HTTP {resp.status_code}",
                'data': data
            }
        except Exception as e:
            logger.error(f"❌ Error querying points raw '{collection_name}': {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def query_batch_points_raw(self, collection_name: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Panggil endpoint Qdrant POST /collections/:collection_name/points/query/batch secara raw.

        - Body diharapkan mengandung field "requests": [ { ... QueryRequest ... }, ... ]
        - Mengembalikan JSON Qdrant apa adanya dalam field data
        """
        if not self.qdrant_available:
            return {
                'success': False,
                'message': 'Qdrant tidak tersedia'
            }
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            url = f"{self.url}/collections/{collection_name}/points/query/batch"
            resp = httpx.post(url, json=body or {}, headers=headers, timeout=60.0)
            data = resp.json() if resp.content else {}
            if 200 <= resp.status_code < 300:
                return {
                    'success': True,
                    'data': data
                }
            return {
                'success': False,
                'message': f"HTTP {resp.status_code}",
                'data': data
            }
        except Exception as e:
            logger.error(f"❌ Error querying batch points raw '{collection_name}': {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def query_points_groups_raw(self, collection_name: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Panggil endpoint Qdrant POST /collections/:collection_name/points/query/groups secara raw.

        - Body fleksibel (query, group_by, limit, group_size, prefetch, filter, dsb.)
        - Kembalikan JSON Qdrant di field data tanpa transformasi
        """
        if not self.qdrant_available:
            return {
                'success': False,
                'message': 'Qdrant tidak tersedia'
            }
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            url = f"{self.url}/collections/{collection_name}/points/query/groups"
            resp = httpx.post(url, json=body or {}, headers=headers, timeout=60.0)
            data = resp.json() if resp.content else {}
            if 200 <= resp.status_code < 300:
                return {
                    'success': True,
                    'data': data
                }
            return {
                'success': False,
                'message': f"HTTP {resp.status_code}",
                'data': data
            }
        except Exception as e:
            logger.error(f"❌ Error querying points groups raw '{collection_name}': {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def search_matrix_pairs_raw(self, collection_name: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Panggil endpoint Qdrant POST /collections/:collection_name/points/search/matrix/pairs secara raw.

        - Body fleksibel: { sample, limit, filter/query_filter, ... }
        - Kembalikan JSON Qdrant di field data
        """
        if not self.qdrant_available:
            return {
                'success': False,
                'message': 'Qdrant tidak tersedia'
            }
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            url = f"{self.url}/collections/{collection_name}/points/search/matrix/pairs"
            resp = httpx.post(url, json=body or {}, headers=headers, timeout=60.0)
            data = resp.json() if resp.content else {}
            if 200 <= resp.status_code < 300:
                return {
                    'success': True,
                    'data': data
                }
            return {
                'success': False,
                'message': f"HTTP {resp.status_code}",
                'data': data
            }
        except Exception as e:
            logger.error(f"❌ Error search matrix pairs raw '{collection_name}': {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def search_matrix_offsets_raw(self, collection_name: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Panggil endpoint Qdrant POST /collections/:collection_name/points/search/matrix/offsets secara raw.

        - Body fleksibel: { sample, limit, filter/query_filter, ... }
        - Kembalikan JSON Qdrant di field data
        """
        if not self.qdrant_available:
            return {
                'success': False,
                'message': 'Qdrant tidak tersedia'
            }
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            url = f"{self.url}/collections/{collection_name}/points/search/matrix/offsets"
            resp = httpx.post(url, json=body or {}, headers=headers, timeout=60.0)
            data = resp.json() if resp.content else {}
            if 200 <= resp.status_code < 300:
                return {
                    'success': True,
                    'data': data
                }
            return {
                'success': False,
                'message': f"HTTP {resp.status_code}",
                'data': data
            }
        except Exception as e:
            logger.error(f"❌ Error search matrix offsets raw '{collection_name}': {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get detail sebuah collection dalam format standar untuk controller."""
        if not self.qdrant_available:
            return {
                'success': False,
                'message': 'Qdrant tidak tersedia'
            }
        try:
            # Gunakan raw API call untuk menghindari masalah validasi Pydantic
            import httpx
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = httpx.get(
                f"{self.url}/collections/{collection_name}",
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                detail_data = response.json()
                result = detail_data.get('result', {})
                
                # Ambil data dengan fallback
                points_count = result.get('points_count', 0)
                vectors_count = result.get('vectors_count', points_count)
                indexed_vectors_count = result.get('indexed_vectors_count', points_count)
                
                # Ambil config
                config = result.get('config', {})
                params = config.get('params', {})
                vectors_config = params.get('vectors', {})
                
                vector_size = vectors_config.get('size', 1536)
                distance = vectors_config.get('distance', 'Cosine')
                
                return {
                    'success': True,
                    'data': {
                        'collection_name': collection_name,
                        'vectors_count': vectors_count,
                        'indexed_vectors_count': indexed_vectors_count,
                        'points_count': points_count,
                        'config': {
                            'vector_size': vector_size,
                            'distance': distance
                        }
                    }
                }
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            # Log error hanya jika bukan masalah validasi Pydantic yang sudah diketahui
            if "validation errors" not in str(e) and "pydantic" not in str(e).lower():
                logger.error(f"❌ Error getting collection info '{collection_name}': {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def get_collection_details_raw(self, collection_name: str) -> Dict[str, Any]:
        """Ambil detail collection langsung dari Qdrant (raw JSON seperti REST Qdrant).
        Return: { success, data } dengan data berisi response Qdrant (usage, status, result, dll.)
        """
        if not self.qdrant_available:
            return {
                'success': False,
                'message': 'Qdrant tidak tersedia'
            }
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            response = httpx.get(
                f"{self.url}/collections/{collection_name}",
                headers=headers,
                timeout=10.0
            )
            # Kembalikan persis struktur dari Qdrant (JSON)
            data = response.json() if response.content else {}
            if 200 <= response.status_code < 300:
                return {
                    'success': True,
                    'data': data
                }
            return {
                'success': False,
                'message': f"HTTP {response.status_code}",
                'data': data
            }
        except Exception as e:
            logger.error(f"❌ Error getting raw collection details '{collection_name}': {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def create_collection(self, collection_name: str, vector_size: int = None, distance: str = 'Cosine') -> Dict[str, Any]:
        """Buat collection secara eksplisit (by name) mengikuti Qdrant REST semantics.
        - distance: 'Cosine' | 'Dot' | 'Euclid'
        Return: { success, message, data: { collection_name, vector_size, distance } }
        """
        if not self.qdrant_available or not QDRANT_AVAILABLE or not self.client:
            return { 'success': False, 'message': 'Qdrant tidak tersedia', 'data': {} }
        try:
            if not collection_name:
                return { 'success': False, 'message': 'collection_name diperlukan', 'data': {} }
            size = int(vector_size or self.vector_size)
            dist = str(distance or 'Cosine').strip().lower()
            if dist == 'cosine':
                dist_enum = Distance.COSINE
            elif dist == 'dot' or dist == 'dotproduct' or dist == 'dot_product':
                dist_enum = Distance.DOT
            elif dist == 'euclid' or dist == 'l2':
                dist_enum = Distance.EUCLID
            else:
                dist_enum = Distance.COSINE

            op = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=size, distance=dist_enum)
            )

            # Optional: buat index penting untuk RAG
            try:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="metadata.company_id",
                    field_schema="keyword"
                )
            except Exception:
                pass

            # Normalisasi response
            result_true = True
            try:
                if isinstance(op, dict):
                    # beberapa versi mengembalikan dict
                    pass
            except Exception:
                pass
            return {
                'success': True,
                'message': 'Collection created successfully',
                'data': {
                    'collection_name': collection_name,
                    'vector_size': size,
                    'distance': 'Cosine' if dist_enum == Distance.COSINE else ('Dot' if dist_enum == Distance.DOT else 'Euclid'),
                    'result': result_true
                }
            }
        except Exception as e:
            # Jika already exists, anggap sukses idempotent
            if 'already exists' in str(e).lower():
                return {
                    'success': True,
                    'message': 'Collection already exists',
                    'data': {
                        'collection_name': collection_name,
                        'vector_size': int(vector_size or self.vector_size),
                        'distance': distance or 'Cosine',
                        'result': True
                    }
                }
            logger.error(f"❌ Error creating collection '{collection_name}': {e}")
            return { 'success': False, 'message': str(e), 'data': {} }

    def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Hapus collection secara eksplisit mengikuti REST Qdrant.
        Return: { success, message, data: { collection_name, result } }
        """
        if not self.qdrant_available or not QDRANT_AVAILABLE or not self.client:
            return { 'success': False, 'message': 'Qdrant tidak tersedia', 'data': {} }
        try:
            if not collection_name:
                return { 'success': False, 'message': 'collection_name diperlukan', 'data': {} }
            op = self.client.delete_collection(collection_name=collection_name)
            result_true = True
            try:
                if isinstance(op, dict):
                    pass
            except Exception:
                pass
            # bersihkan cache koleksi lokal jika ada
            try:
                if collection_name in self.collections:
                    del self.collections[collection_name]
            except Exception:
                pass
            return {
                'success': True,
                'message': 'Collection deleted successfully',
                'data': {
                    'collection_name': collection_name,
                    'result': result_true
                }
            }
        except Exception as e:
            # Jika not found, anggap idempotent sukses
            if 'not found' in str(e).lower() or 'does not exist' in str(e).lower():
                return {
                    'success': True,
                    'message': 'Collection not found, treated as deleted',
                    'data': {
                        'collection_name': collection_name,
                        'result': True
                    }
                }
            logger.error(f"❌ Error deleting collection '{collection_name}': {e}")
            return { 'success': False, 'message': str(e), 'data': {} }

    def get_documents(self, company_id: str, limit: int = 10, offset: int = 0, status: str = '') -> Dict[str, Any]:
        """Ambil daftar dokumen RAG dari database untuk tampilan di UI.
        Diselaraskan dengan kebutuhan controller qdrant_knowledge_base_controller.
        """
        try:
            # Import lokal untuk menghindari dependency saat Qdrant tidak tersedia
            from domains.knowledge.models.rag_models import RagDocument
            from config.database import db
            query = RagDocument.query.filter_by(company_id=company_id)
            if status:
                query = query.filter_by(status=status)
            total = query.count()
            documents = query.offset(offset).limit(limit).all()
            documents_data: List[Dict[str, Any]] = []
            for doc in documents:
                doc_data = doc.to_dict()
                # Enrich dengan info agregat yang berguna
                try:
                    pages_count = len(doc.pages) if getattr(doc, 'pages', None) else 0
                except Exception:
                    pages_count = 0
                try:
                    chunks = getattr(doc, 'chunks', None)
                    chunks_count = len(chunks) if chunks else 0
                    embeddings_count = sum(len(getattr(ch, 'embeddings', []) or []) for ch in (chunks or []))
                except Exception:
                    chunks_count = 0
                    embeddings_count = 0
                doc_data['pages_count'] = pages_count
                doc_data['chunks_count'] = chunks_count
                doc_data['embeddings_count'] = embeddings_count
                documents_data.append(doc_data)
            return {
                'success': True,
                'data': {
                    'documents': documents_data,
                    'total': total,
                    'limit': limit,
                    'offset': offset,
                    'company_id': company_id
                }
            }
        except Exception as e:
            logger.error(f"❌ Failed to get documents: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    # --- Compatibility helpers for other services ---
    def get_collection(self, name_or_company: str, collection: str = None):
        """Get collection by direct name or by company_id + collection dengan fallback."""
        if not self.qdrant_available:
            return None
        
        try:
            if not QDRANT_AVAILABLE or not self.client:
                return None
            
            if collection is None:
                # name_or_company dianggap full collection name
                try:
                    return self.client.get_collection(name_or_company)
                except Exception:
                    return None
            
            # Bangun nama dengan pola standar
            name = self._get_collection_name(str(name_or_company), collection)
            try:
                return self.client.get_collection(name)
            except Exception:
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting collection '{name_or_company}': {e}")
            return None

    def get_collection_count(self, name_or_company: str, collection: str = None) -> int:
        """Get jumlah dokumen dalam collection (by name atau company+collection) dengan fallback."""
        if not self.qdrant_available:
            return 0
        
        try:
            if collection is None:
                collection_info = self.client.get_collection(name_or_company)
                return collection_info.points_count
            else:
                collection_name = self._get_collection_name(str(name_or_company), collection)
                collection_info = self.client.get_collection(collection_name)
                return collection_info.points_count
        except Exception as e:
            logger.error(f"❌ Error getting collection count '{name_or_company}': {e}")
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """Health check untuk Qdrant service dengan fallback"""
        if not self.qdrant_available:
            return {
                'status': 'unavailable',
                'message': 'Qdrant service tidak tersedia',
                'fallback_mode': True,
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Test basic operations
            collections = self.client.get_collections()
            
            return {
                'status': 'healthy',
                'message': 'Qdrant service is working properly',
                'url': self.url,
                'collections_count': len(collections.collections),
                'vector_size': self.vector_size,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Qdrant health check failed: {e}")
            return {
                'status': 'unhealthy',
                'message': f'Qdrant service error: {str(e)}',
                'url': self.url,
                'vector_size': self.vector_size
            }


# Global instances - lazy initialization
_qdrant_service = None

def get_qdrant_service() -> QdrantService:
    """Get global Qdrant service instance with lazy initialization"""
    global _qdrant_service
    if _qdrant_service is None:
        try:
            _qdrant_service = QdrantService()
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant service: {e}")
            # Create a fallback service instance
            _qdrant_service = QdrantService()
    return _qdrant_service

# For backward compatibility - use getter functions instead of global instances
def get_qdrant_service_instance():
    """Get qdrant service instance for backward compatibility"""
    return get_qdrant_service()

# These will be initialized when first accessed
qdrant_service = None
qdrant_fallback = None

def get_qdrant_fallback_service() -> QdrantService:
    """Get global Qdrant fallback service instance (same as main service with fallback support)"""
    return qdrant_fallback
