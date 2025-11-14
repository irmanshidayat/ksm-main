#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Document Processing Service untuk KSM Main Backend
Konsolidasi dari document_processing_service.py dan async_document_processor.py
Menggabungkan fitur terbaik dari kedua implementasi dengan queue management yang robust
"""

import os
import io
import base64
import hashlib
import logging
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from config.database import db
from domains.knowledge.models.rag_models import RagDocument, RagDocumentPage, RagDocumentChunk, RagChunkEmbedding

# Import services with error handling
try:
    from .unified_embedding_service import get_unified_embedding_service
    UNIFIED_EMBEDDING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Unified embedding service not available: {e}")
    UNIFIED_EMBEDDING_AVAILABLE = False

try:
    from .qdrant_service import QdrantService
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    QdrantService = None

logger = logging.getLogger(__name__)


class JobQueue:
    """Database-based job queue untuk document processing"""
    
    def __init__(self):
        self.table_name = 'document_processing_queue'
        self._create_queue_table()
    
    def _create_queue_table(self):
        """Create job queue table jika belum ada"""
        try:
            from flask import has_app_context
            
            # Check if we're in app context
            if not has_app_context():
                logger.warning("⚠️ Not in app context, skipping queue table creation")
                return
            
            # Check if table exists
            with db.engine.connect() as conn:
                result = conn.execute(db.text("SHOW TABLES LIKE 'document_processing_queue'"))
                if result.fetchone():
                    return
            
            # Create table
            create_sql = """
            CREATE TABLE document_processing_queue (
                id INT AUTO_INCREMENT PRIMARY KEY,
                document_id INT NOT NULL,
                company_id VARCHAR(100) NOT NULL,
                collection VARCHAR(100) DEFAULT '',
                status ENUM('pending', 'processing', 'completed', 'failed', 'retry') DEFAULT 'pending',
                priority INT DEFAULT 0,
                retry_count INT DEFAULT 0,
                max_retries INT DEFAULT 3,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP NULL,
                completed_at TIMESTAMP NULL,
                INDEX idx_status (status),
                INDEX idx_priority (priority),
                INDEX idx_created_at (created_at),
                FOREIGN KEY (document_id) REFERENCES rag_documents(id) ON DELETE CASCADE
            )
            """
            with db.engine.connect() as conn:
                conn.execute(db.text(create_sql))
                conn.commit()
            logger.info("✅ Document processing queue table created")
            
        except Exception as e:
            logger.error(f"❌ Failed to create queue table: {e}")
    
    def add_job(self, document_id: int, company_id: str, collection: str = '', priority: int = 0) -> int:
        """Add job ke queue"""
        try:
            sql = """
            INSERT INTO document_processing_queue 
            (document_id, company_id, collection, priority, status, created_at)
            VALUES (:document_id, :company_id, :collection, :priority, 'pending', NOW())
            """
            with db.engine.connect() as conn:
                result = conn.execute(db.text(sql), {
                    'document_id': document_id,
                    'company_id': company_id,
                    'collection': collection,
                    'priority': priority
                })
                conn.commit()
                job_id = result.lastrowid
                logger.info(f"✅ Added job {job_id} for document {document_id}")
                return job_id
                
        except Exception as e:
            logger.error(f"❌ Failed to add job: {e}")
            return 0
    
    def get_next_job(self) -> Optional[Dict[str, Any]]:
        """Get next pending job dari queue"""
        try:
            sql = """
            SELECT * FROM document_processing_queue 
            WHERE status = 'pending' 
            ORDER BY priority DESC, created_at ASC 
            LIMIT 1
            """
            with db.engine.connect() as conn:
                result = conn.execute(db.text(sql))
                row = result.fetchone()
                if row:
                    return dict(row._mapping)
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get next job: {e}")
            return None
    
    def update_job_status(self, job_id: int, status: str, error_message: str = None):
        """Update job status"""
        try:
            if status == 'processing':
                sql = """
                UPDATE document_processing_queue 
                SET status = :status, started_at = NOW() 
                WHERE id = :job_id
                """
                params = {'status': status, 'job_id': job_id}
            elif status in ['completed', 'failed']:
                sql = """
                UPDATE document_processing_queue 
                SET status = :status, completed_at = NOW(), error_message = :error_message 
                WHERE id = :job_id
                """
                params = {'status': status, 'job_id': job_id, 'error_message': error_message}
            else:
                sql = """
                UPDATE document_processing_queue 
                SET status = :status 
                WHERE id = :job_id
                """
                params = {'status': status, 'job_id': job_id}
            
            with db.engine.connect() as conn:
                conn.execute(db.text(sql), params)
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to update job status: {e}")
    
    def increment_retry(self, job_id: int):
        """Increment retry count untuk job"""
        try:
            sql = """
            UPDATE document_processing_queue 
            SET retry_count = retry_count + 1, status = 'retry' 
            WHERE id = :job_id
            """
            with db.engine.connect() as conn:
                conn.execute(db.text(sql), {'job_id': job_id})
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to increment retry: {e}")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            sql = """
            SELECT 
                status,
                COUNT(*) as count
            FROM document_processing_queue 
            GROUP BY status
            """
            with db.engine.connect() as conn:
                result = conn.execute(db.text(sql))
                stats = {}
                for row in result:
                    stats[row.status] = row.count
                
                return {
                    'total_jobs': sum(stats.values()),
                    'by_status': stats,
                    'pending': stats.get('pending', 0),
                    'processing': stats.get('processing', 0),
                    'completed': stats.get('completed', 0),
                    'failed': stats.get('failed', 0)
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get queue stats: {e}")
            return {}


class UnifiedDocumentProcessingService:
    """Unified service untuk document processing dan ingestion dengan async queue"""
    
    def __init__(self, max_workers: int = 2):
        # Thread pool executor untuk background processing
        self._executor: Optional[ThreadPoolExecutor] = None
        self.max_workers = max_workers
        
        # Job queue
        self.job_queue = JobQueue()
        
        # Services
        if UNIFIED_EMBEDDING_AVAILABLE:
            self.embedding_service = get_unified_embedding_service()
        else:
            self.embedding_service = None
            logger.warning("Unified embedding service not available")
        
        # Qdrant service
        if QDRANT_AVAILABLE and QdrantService:
            try:
                self.qdrant_service = QdrantService()
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Qdrant service: {e}")
                self.qdrant_service = None
        else:
            self.qdrant_service = None
        
        # Processing stats
        self.stats = {
            'total_processed': 0,
            'total_failed': 0,
            'total_retries': 0,
            'start_time': None
        }
        
        logger.info("🚀 Unified Document Processing Service initialized")
    
    def _get_executor(self) -> ThreadPoolExecutor:
        """Get thread pool executor"""
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="doc-process-worker")
        return self._executor
    
    # ===== PDF INGESTION METHODS =====
    
    def compute_sha256(self, file_bytes: bytes) -> str:
        """Compute SHA256 hash untuk file"""
        hasher = hashlib.sha256()
        hasher.update(file_bytes)
        return hasher.hexdigest()
    
    def save_pdf_from_base64(self, storage_dir: str, company_id: str, filename: str, base64_data: str) -> Dict[str, Any]:
        """Save PDF from base64 data"""
        try:
            # Decode base64
            if base64_data.startswith('data:'):
                base64_data = base64_data.split(',')[1]
            
            file_bytes = base64.b64decode(base64_data)
            
            # Create storage directory
            company_dir = os.path.join(storage_dir, company_id)
            os.makedirs(company_dir, exist_ok=True)
            
            # Generate filename
            sha256_hash = self.compute_sha256(file_bytes)
            file_ext = '.pdf'
            if filename.lower().endswith('.txt'):
                file_ext = '.txt'
            elif filename.lower().endswith('.text'):
                file_ext = '.text'
            
            storage_path = os.path.join(company_dir, f"{sha256_hash}{file_ext}")
            
            # Write file
            with open(storage_path, 'wb') as f:
                f.write(file_bytes)
            
            return {
                'success': True,
                'storage_path': storage_path,
                'sha256': sha256_hash,
                'file_size': len(file_bytes)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to save PDF: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_text_pages(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from document file"""
        try:
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return [{
                    'text': content,
                    'has_text': bool(content.strip()),
                    'ocr_used': False,
                    'text_len': len(content),
                    'bbox_available': False
                }]
            elif file_path.endswith('.pdf'):
                # Extract text from PDF using PyPDF2
                try:
                    import PyPDF2
                    
                    pages = []
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        total_pages = len(pdf_reader.pages)
                        
                        logger.info(f"📄 Extracting text from PDF with {total_pages} pages")
                        
                        for page_num in range(total_pages):
                            try:
                                page = pdf_reader.pages[page_num]
                                text = page.extract_text()
                                
                                pages.append({
                                    'text': text,
                                    'has_text': bool(text.strip()),
                                    'ocr_used': False,
                                    'text_len': len(text),
                                    'bbox_available': False
                                })
                                
                                logger.debug(f"   Page {page_num + 1}: {len(text)} chars")
                                
                            except Exception as page_error:
                                logger.warning(f"⚠️ Failed to extract page {page_num + 1}: {page_error}")
                                pages.append({
                                    'text': '',
                                    'has_text': False,
                                    'ocr_used': False,
                                    'text_len': 0,
                                    'bbox_available': False
                                })
                        
                        logger.info(f"✅ Extracted {len(pages)} pages from PDF")
                        return pages
                        
                except ImportError:
                    logger.error("❌ PyPDF2 not available for PDF extraction")
                    return [{
                        'text': '',
                        'has_text': False,
                        'ocr_used': False,
                        'text_len': 0,
                        'bbox_available': False
                    }]
                except Exception as pdf_error:
                    logger.error(f"❌ PDF extraction failed: {pdf_error}")
                    return [{
                        'text': '',
                        'has_text': False,
                        'ocr_used': False,
                        'text_len': 0,
                        'bbox_available': False
                    }]
            else:
                # For other file types, return empty for now
                logger.warning(f"⚠️ Unsupported file type: {file_path}")
                return [{
                    'text': '',
                    'has_text': False,
                    'ocr_used': False,
                    'text_len': 0,
                    'bbox_available': False
                }]
        except Exception as e:
            logger.error(f"❌ Failed to extract text from {file_path}: {e}")
            return []
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Find good break point
            if end < len(text):
                break_point = text.rfind(' ', start, end)
                if break_point == -1:
                    break_point = text.rfind('\n', start, end)
                if break_point == -1:
                    break_point = end
            else:
                break_point = len(text)
            
            chunk = text[start:break_point].strip()
            if chunk:
                chunks.append(chunk)
            
            start = break_point - overlap
            if start >= len(text):
                break
        
        return chunks
    
    # ===== ASYNC PROCESSING METHODS =====
    
    def submit_document(self, document_id: int, company_id: str, collection: str = '', priority: int = 0) -> int:
        """Submit document untuk async processing"""
        try:
            job_id = self.job_queue.add_job(document_id, company_id, collection, priority)
            if job_id:
                # Submit untuk background processing
                executor = self._get_executor()
                executor.submit(self._process_document_job, job_id)
                logger.info(f"📄 Document {document_id} submitted for async processing (job {job_id})")
            return job_id
            
        except Exception as e:
            logger.error(f"❌ Failed to submit document for processing: {e}")
            return 0
    
    def process_document_sync(self, document_id: int, company_id: str, collection: str = '') -> None:
        """Process document ingestion secara sinkron (untuk testing/MVP)"""
        try:
            self._process_document_job_direct(document_id, company_id, collection)
            logger.info(f"📄 Document processed synchronously for document {document_id}")
        except Exception as e:
            logger.error(f"❌ Failed to process document synchronously: {e}")
    
    def _process_document_job(self, job_id: int):
        """Process document ingestion job dari queue"""
        try:
            # Get job details
            job = self.job_queue.get_next_job()
            if not job or job['id'] != job_id:
                logger.warning(f"⚠️ Job {job_id} not found or not pending")
                return
            
            # Update job status
            self.job_queue.update_job_status(job_id, 'processing')
            
            # Process document
            self._process_document_job_direct(
                job['document_id'], 
                job['company_id'], 
                job['collection']
            )
            
            # Mark as completed
            self.job_queue.update_job_status(job_id, 'completed')
            self.stats['total_processed'] += 1
            
            logger.info(f"✅ Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Job {job_id} failed: {e}")
            
            # Update job status
            self.job_queue.update_job_status(job_id, 'failed', str(e))
            self.stats['total_failed'] += 1
            
            # Check if we should retry
            if job and job['retry_count'] < job['max_retries']:
                self.job_queue.increment_retry(job_id)
                self.stats['total_retries'] += 1
                logger.info(f"🔄 Job {job_id} scheduled for retry")
    
    def _process_document_job_direct(self, document_id: int, company_id: str, collection: str = ''):
        """Process document ingestion job directly"""
        try:
            doc = RagDocument.query.get(document_id)
            if not doc:
                logger.error(f"Document {document_id} not found")
                return
            
            # Update status
            doc.status = 'processing'
            db.session.commit()
            
            # Extract text from document
            pages = self.extract_text_pages(doc.storage_path)
            
            # Clean old pages/chunks
            db.session.query(RagDocumentPage).filter_by(document_id=doc.id).delete()
            db.session.query(RagDocumentChunk).filter_by(document_id=doc.id).delete()
            db.session.commit()
            
            # Save pages
            for i, page in enumerate(pages, start=1):
                db.session.add(RagDocumentPage(
                    document_id=doc.id,
                    page_number=i,
                    has_text=page['has_text'],
                    ocr_used=page['ocr_used'],
                    text_len=page['text_len'],
                    bbox_available=page['bbox_available']
                ))
            db.session.commit()
            
            # Create chunks and embeddings
            all_text = '\n'.join([page.get('text', '') for page in pages if page.get('text')])
            if all_text:
                chunks = self.chunk_text(all_text)
                
                for i, chunk_text in enumerate(chunks):
                    chunk = RagDocumentChunk(
                        document_id=doc.id,
                        chunk_index=i,
                        text=chunk_text,
                        page_from=1,  # Simplified
                        page_to=1
                    )
                    db.session.add(chunk)
                    db.session.flush()
                    
                    # Generate embedding
                    if self.embedding_service and self.embedding_service.is_available():
                        embedding = self.embedding_service.embed_text(chunk_text)
                        if embedding:
                            chunk_embedding = RagChunkEmbedding(
                                chunk_id=chunk.id,
                                model_name='unified',
                                qdrant_vector_id=None,
                                qdrant_collection=None,
                                embedding_status='completed'
                            )
                            db.session.add(chunk_embedding)
                
                db.session.commit()
                
                # Store in Qdrant if available
                if self.qdrant_service and self.qdrant_service.is_available():
                    self._store_chunks_in_qdrant(doc, chunks, company_id, collection)
            
            # Update document with final stats
            doc.status = 'ready'
            doc.total_pages = len(pages)
            doc.vector_count = len(chunks) if all_text else 0
            db.session.commit()
            
            logger.info(f"✅ Document {document_id} processed successfully: {len(pages)} pages, {len(chunks) if all_text else 0} vectors")
            
        except Exception as e:
            logger.error(f"❌ Failed to process document {document_id}: {e}")
            # Update status to failed
            try:
                doc = RagDocument.query.get(document_id)
                if doc:
                    doc.status = 'failed'
                    db.session.commit()
            except Exception:
                pass
    
    def _store_chunks_in_qdrant(self, document: RagDocument, chunks: List[str], company_id: str, collection: str):
        """Store document chunks in Qdrant"""
        try:
            if not self.qdrant_service or not self.qdrant_service.is_available():
                return
            
            # Prepare documents for Qdrant
            documents = []
            for i, chunk_text in enumerate(chunks):
                documents.append({
                    'text': chunk_text,
                    'chunk_id': f"{document.id}_chunk_{i}",
                    'document_id': document.id,
                    'chunk_index': i,
                    'section_title': None
                })
            
            # Store in Qdrant
            self.qdrant_service.add_documents(
                company_id=company_id,
                documents=documents,
                collection=collection
            )
            
            logger.info(f"✅ Stored {len(chunks)} chunks in Qdrant for document {document.id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store chunks in Qdrant: {e}")
    
    # ===== QUEUE MANAGEMENT METHODS =====
    
    def get_processing_status(self, document_id: int) -> Dict[str, Any]:
        """Get processing status untuk document"""
        try:
            # Get document status
            doc = RagDocument.query.get(document_id)
            if not doc:
                return {'error': 'Document not found'}
            
            # Get queue status
            sql = """
            SELECT * FROM document_processing_queue 
            WHERE document_id = :document_id 
            ORDER BY created_at DESC 
            LIMIT 1
            """
            with db.engine.connect() as conn:
                result = conn.execute(db.text(sql), {'document_id': document_id})
                job = result.fetchone()
            
            return {
                'document_id': document_id,
                'status': doc.status,
                'queue_status': job.status if job else 'not_queued',
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'updated_at': doc.updated_at.isoformat() if doc.updated_at else None,
                'pages_count': len(doc.pages) if doc.pages else 0,
                'chunks_count': len(doc.chunks) if doc.chunks else 0,
                'embeddings_count': sum(len(chunk.embeddings) for chunk in doc.chunks) if doc.chunks else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get processing status: {e}")
            return {'error': str(e)}
    
    def get_processor_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        try:
            queue_stats = self.job_queue.get_queue_stats()
            
            return {
                'processor_stats': self.stats,
                'queue_stats': queue_stats,
                'services': {
                    'embedding_service_available': self.embedding_service is not None and self.embedding_service.is_available(),
                    'qdrant_service_available': self.qdrant_service is not None and self.qdrant_service.is_available()
                },
                'configuration': {
                    'max_workers': self.max_workers,
                    'executor_active': self._executor is not None
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get processor stats: {e}")
            return {'error': str(e)}
    
    def start_processor(self):
        """Start background processor"""
        try:
            if self._executor is None:
                self._executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="doc-process-worker")
                self.stats['start_time'] = datetime.now()
                logger.info(f"✅ Started document processor with {self.max_workers} workers")
            else:
                logger.warning("⚠️ Processor already running")
        except Exception as e:
            logger.error(f"❌ Failed to start processor: {e}")
    
    def stop_processor(self):
        """Stop background processor"""
        try:
            if self._executor:
                self._executor.shutdown(wait=True)
                self._executor = None
                logger.info("✅ Document processor stopped")
            else:
                logger.warning("⚠️ Processor not running")
        except Exception as e:
            logger.error(f"❌ Failed to stop processor: {e}")


# Global service instance
_unified_document_processing_service = None

def get_unified_document_processing_service() -> UnifiedDocumentProcessingService:
    """Get global unified document processing service instance"""
    global _unified_document_processing_service
    if _unified_document_processing_service is None:
        _unified_document_processing_service = UnifiedDocumentProcessingService()
    return _unified_document_processing_service

# Backward compatibility aliases
def get_async_document_processor() -> UnifiedDocumentProcessingService:
    """Backward compatibility alias"""
    return get_unified_document_processing_service()
