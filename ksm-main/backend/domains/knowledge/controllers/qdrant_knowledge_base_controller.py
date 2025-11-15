#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qdrant Knowledge Base Controller untuk KSM Main Backend
RESTful API endpoints untuk manajemen dokumen RAG dengan Qdrant integration
"""

from flask import Blueprint, request, jsonify, current_app
# Import qdrant service
from domains.knowledge.services.qdrant_service import get_qdrant_service
from domains.knowledge.models.rag_models import RagDocument, RagDocumentPage, RagDocumentChunk, RagChunkEmbedding
from config.database import db
from datetime import datetime
import logging
import json
import os

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
qdrant_kb_bp = Blueprint('qdrant_kb', __name__)

# ===== DOCUMENT MANAGEMENT ENDPOINTS =====

@qdrant_kb_bp.route('/documents', methods=['POST'])
def upload_document():
    """
    Upload dokumen PDF ke Qdrant Knowledge Base
    
    Request Body:
    {
        "filename": "document.pdf",
        "base64_content": "data:application/pdf;base64,JVBERi0x...",
        "company_id": "PT. Kian Santang Muliatama",
        "title": "Judul Dokumen",
        "description": "Deskripsi dokumen",
        "collection": "default"
    }
    
    Response:
    {
        "success": true,
        "message": "Document uploaded successfully",
        "data": {
            "document_id": 123,
            "filename": "document.pdf",
            "total_pages": 10,
            "chunks_created": 25,
            "vectors_uploaded": 25,
            "collection_name": "KSM",
            "status": "ready"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validasi input
        required_fields = ['filename', 'base64_content', 'company_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        # Get service
        qdrant_service = get_qdrant_service()
        
        # Extract variables
        company_id = data['company_id']
        collection = data.get('collection', 'default')
        
        # Upload document to database and Qdrant
        try:
            from domains.knowledge.models.rag_models import RagDocument
            import base64
            import hashlib
            import os
            from datetime import datetime
            
            # Decode base64 content with validation and padding fix
            base64_content = data['base64_content']
            
            # Remove data URL prefix if present (e.g., "data:application/pdf;base64,")
            if ',' in base64_content:
                base64_content = base64_content.split(',', 1)[1]
            
            # Fix base64 padding if needed
            missing_padding = len(base64_content) % 4
            if missing_padding:
                base64_content += '=' * (4 - missing_padding)
            
            # Validate base64 format
            try:
                file_content = base64.b64decode(base64_content, validate=True)
            except Exception as decode_error:
                logger.error(f"Base64 decode error: {str(decode_error)}")
                raise ValueError(f"Invalid base64 content: {str(decode_error)}")
            
            # Generate file hash for unique identification
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Check if document already exists
            existing_doc = RagDocument.query.filter_by(
                company_id=data['company_id'],
                sha256=file_hash
            ).first()
            
            if existing_doc:
                return jsonify({
                    'success': False,
                    'message': 'Document with same content already exists',
                    'data': {
                        'document_id': existing_doc.id,
                        'title': existing_doc.title,
                        'status': existing_doc.status
                    }
                }), 400
            
            # Prepare storage path first
            storage_dir = f"rag_documents/{data['company_id']}"
            os.makedirs(storage_dir, exist_ok=True)
            storage_path = f"{storage_dir}/{file_hash[:8]}_{data['filename']}"
            
            # Create document record in database
            document = RagDocument(
                title=data.get('title', data['filename']),
                original_name=data['filename'],
                company_id=data['company_id'],
                collection=data.get('collection', 'default'),
                mime=data.get('mime', 'application/pdf'),
                size_bytes=len(file_content),
                sha256=file_hash,
                status='uploaded',
                storage_path=storage_path,
                created_by=1,  # Default user ID
                created_at=datetime.now()
            )
            
            db.session.add(document)
            db.session.commit()
            
            # Save file to storage
            with open(storage_path, 'wb') as f:
                f.write(file_content)
            
            # Process document (extract pages, generate embeddings, update to Qdrant)
            try:
                logger.info(f"🔄 Starting document processing for document {document.id}")
                
                # Update status to processing
                document.status = 'processing'
                db.session.commit()
                
                # Process document using qdrant service directly
                # REMOVED: unified_rag_service - functionality consolidated into qdrant_service
                qdrant_service = get_qdrant_service()
                
                # Full PDF processing with embeddings
                logger.info(f"🔄 Starting full PDF processing for document {document.id}")
                
                try:
                    import PyPDF2
                    import io
                    import uuid
                    from domains.knowledge.services.openai_embedding_service import OpenAIEmbeddingService
                    
                    # Initialize services
                    embedding_service = OpenAIEmbeddingService()
                    
                    # Extract text from PDF
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                    total_pages = len(pdf_reader.pages)
                    
                    # Extract all text
                    all_text = ""
                    for page_num in range(total_pages):
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        all_text += page_text + "\n"
                        
                        # Create page record (metadata only)
                        page_record = RagDocumentPage(
                            document_id=document.id,
                            page_number=page_num + 1,
                            text_len=len(page_text),
                            has_text=len(page_text.strip()) > 0,
                            created_at=datetime.now()
                        )
                        db.session.add(page_record)
                    
                    # Create chunks
                    chunk_size = 1000
                    overlap = 200
                    chunks = []
                    
                    for i in range(0, len(all_text), chunk_size - overlap):
                        chunk = all_text[i:i+chunk_size]
                        if len(chunk.strip()) > 0:
                            chunks.append(chunk)
                            
                            # Create chunk record in database
                            from domains.knowledge.models.rag_models import RagDocumentChunk
                            import hashlib
                            
                            chunk_record = RagDocumentChunk(
                                document_id=document.id,
                                chunk_index=len(chunks) - 1,
                                text=chunk,
                                tokens=len(chunk.split()),
                                text_hash=hashlib.sha256(chunk.encode()).hexdigest(),
                                created_at=datetime.now()
                            )
                            db.session.add(chunk_record)
                    
                    logger.info(f"📄 Created {len(chunks)} chunks from {total_pages} pages")
                    
                    # Generate embeddings
                    embeddings = []
                    for i, chunk in enumerate(chunks):
                        embedding = embedding_service.embed_text(chunk)
                        if embedding:
                            embeddings.append(embedding)
                        else:
                            logger.warning(f"⚠️ Failed to generate embedding for chunk {i+1}")
                    
                    logger.info(f"📄 Generated {len(embeddings)} embeddings")
                    
                    # Store in Qdrant
                    if embeddings:
                        qdrant_docs = []
                        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                            doc = {
                                'id': str(uuid.uuid4()),
                                'text': chunk,
                                'embedding': embedding,
                                'document_id': document.id,
                                'chunk_index': i,
                                'company_id': company_id
                            }
                            qdrant_docs.append(doc)
                        
                        # Store in Qdrant
                        result = qdrant_service.add_documents(
                            company_id=company_id,
                            documents=qdrant_docs,
                            collection=collection
                        )
                        
                        if result:
                            logger.info(f"✅ Successfully stored {len(qdrant_docs)} vectors in Qdrant")
                            
                            # Update document
                            document.status = 'ready'
                            document.total_pages = total_pages
                            document.vector_count = len(qdrant_docs)
                            document.qdrant_collection = f"{company_id}_KSM_{collection}"
                            db.session.commit()
                            
                            logger.info(f"✅ Full processing completed for document {document.id}: {total_pages} pages, {len(qdrant_docs)} vectors")
                        else:
                            logger.error(f"❌ Failed to store vectors in Qdrant for document {document.id}")
                            document.status = 'failed'
                            db.session.commit()
                    else:
                        logger.error(f"❌ No embeddings generated for document {document.id}")
                        document.status = 'failed'
                        db.session.commit()
                    
                except Exception as pdf_error:
                    logger.error(f"❌ PDF processing failed for document {document.id}: {str(pdf_error)}")
                    document.status = 'failed'
                    db.session.commit()
            
            except Exception as process_error:
                logger.error(f"❌ Document processing error for document {document.id}: {str(process_error)}")
                document.status = 'failed'
                db.session.commit()
            
            result = {
                'success': True,
                'message': 'Document uploaded and processed successfully',
                'data': {
                    'document_id': document.id,
                    'title': document.title,
                    'filename': document.original_name,
                    'size_bytes': document.size_bytes,
                    'status': document.status,
                    'total_pages': document.total_pages or 0,
                    'vector_count': document.vector_count or 0,
                    'created_at': document.created_at.isoformat()
                }
            }
            
            logger.info(f"✅ Document uploaded successfully: {document.id} - {document.title}")
            
        except Exception as upload_error:
            logger.error(f"Upload error: {str(upload_error)}")
            result = {
                'success': False,
                'message': f'Upload failed: {str(upload_error)}'
            }
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Upload failed: {str(e)}'
        }), 500

@qdrant_kb_bp.route('/documents', methods=['GET'])
def get_documents():
    """
    Get semua dokumen dengan pagination dan filter
    
    Query Parameters:
    - company_id: ID perusahaan (required)
    - limit: Jumlah dokumen per halaman (default: 10)
    - offset: Offset untuk pagination (default: 0)
    - status: Filter berdasarkan status (uploaded, processing, ready, failed)
    
    Response:
    {
        "success": true,
        "data": {
            "documents": [...],
            "total": 50,
            "limit": 10,
            "offset": 0,
            "has_more": true
        }
    }
    """
    try:
        company_id = request.args.get('company_id')
        if not company_id:
            return jsonify({
                'success': False,
                'message': 'company_id parameter is required'
            }), 400
        
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        status = request.args.get('status', '')
        
        # Get service
        qdrant_service = get_qdrant_service()
        
        # Get documents
        result = qdrant_service.get_documents(company_id, limit, offset, status)
        if isinstance(result, dict) and result.get('success'):
            # Tambahkan flag has_more untuk kenyamanan UI
            try:
                data = result.setdefault('data', {})
                total = int(data.get('total', 0))
                data['has_more'] = (offset + limit) < total
            except Exception:
                pass
            return jsonify(result), 200
        return jsonify(result if isinstance(result, dict) else {'success': False, 'message': 'Unknown error'}), 500
        
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get documents: {str(e)}'
        }), 500

@qdrant_kb_bp.route('/documents/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """
    Get detail dokumen berdasarkan ID
    
    Response:
    {
        "success": true,
        "data": {
            "id": 123,
            "company_id": "PT. Kian Santang Muliatama",
            "original_name": "document.pdf",
            "title": "Judul Dokumen",
            "description": "Deskripsi",
            "status": "ready",
            "total_pages": 10,
            "vector_count": 25,
            "chunks": [...],
            "pages": [...]
        }
    }
    """
    try:
        document = RagDocument.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f'Document with ID {document_id} not found'
            }), 404
        
        # Format response dengan detail lengkap
        doc_data = document.to_dict(include_content=False)
        doc_data['vector_count'] = document.vector_count or 0
        doc_data['chunks_count'] = len(document.chunks) if document.chunks else 0
        doc_data['pages'] = [page.to_dict() for page in document.pages]
        doc_data['chunks'] = [chunk.to_dict(include_text=True) for chunk in document.chunks]
        
        return jsonify({
            'success': True,
            'data': doc_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get document: {str(e)}'
        }), 500

@qdrant_kb_bp.route('/documents/<int:document_id>', methods=['PUT'])
def update_document(document_id):
    """
    Update/re-process dokumen (re-generate embeddings)
    
    Response:
    {
        "success": true,
        "message": "Document updated successfully",
        "data": {
            "old_document_id": 123,
            "new_document_id": 124,
            "filename": "document.pdf",
            "total_pages": 10,
            "chunks_created": 25,
            "vectors_uploaded": 25,
            "status": "ready"
        }
    }
    """
    try:
        # Get service
        qdrant_service = get_qdrant_service()
        
        # Update document
        result = qdrant_service.update_document_in_qdrant(document_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error updating document {document_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to update document: {str(e)}'
        }), 500

@qdrant_kb_bp.route('/documents/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """
    Hapus dokumen dari MySQL dan Qdrant
    
    Response:
    {
        "success": true,
        "message": "Document deleted successfully",
        "data": {
            "document_id": 123,
            "deleted_at": "2024-01-01T12:00:00Z"
        }
    }
    """
    try:
        from domains.knowledge.models.rag_models import RagDocument, RagDocumentPage, RagDocumentChunk, RagChunkEmbedding
        from config.database import db
        
        # Get document from database
        document = RagDocument.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f'Document with ID {document_id} not found'
            }), 404
        
        # Get service
        qdrant_service = get_qdrant_service()
        
        # Delete from Qdrant first
        qdrant_result = qdrant_service.delete_document_from_qdrant(str(document_id))
        logger.info(f"Qdrant delete result: {qdrant_result}")
        
        # Delete related data from database (cascade delete)
        try:
            # Delete embeddings first (foreign key constraint)
            RagChunkEmbedding.query.filter(
                RagChunkEmbedding.chunk_id.in_(
                    db.session.query(RagDocumentChunk.id).filter(
                        RagDocumentChunk.document_id == document_id
                    )
                )
            ).delete(synchronize_session=False)
            
            # Delete chunks
            RagDocumentChunk.query.filter_by(document_id=document_id).delete()
            
            # Delete pages
            RagDocumentPage.query.filter_by(document_id=document_id).delete()
            
            # Delete document
            db.session.delete(document)
            db.session.commit()
            
            logger.info(f"✅ Successfully deleted document {document_id} from database and Qdrant")
            
            return jsonify({
                'success': True,
                'message': 'Document deleted successfully from database and Qdrant',
                'data': {
                    'document_id': document_id,
                    'deleted_at': datetime.now().isoformat(),
                    'qdrant_result': qdrant_result
                }
            }), 200
            
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database delete error for document {document_id}: {str(db_error)}")
            return jsonify({
                'success': False,
                'message': f'Failed to delete document from database: {str(db_error)}',
                'qdrant_result': qdrant_result
            }), 500
        
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to delete document: {str(e)}'
        }), 500

# ===== COLLECTION MANAGEMENT ENDPOINTS =====

@qdrant_kb_bp.route('/collections', methods=['POST'])
def create_collection():
    """
    Buat Qdrant collection baru
    
    Request Body:
    {
        "collection_name": "PT. Kian Santang Muliatama_documents",
        "vector_size": 1536,
        "distance": "Cosine"
    }
    
    Response:
    {
        "success": true,
        "message": "Collection created successfully",
        "data": {
            "collection_name": "PT. Kian Santang Muliatama_documents",
            "vector_size": 1536,
            "distance": "Cosine"
        }
    }
    """
    try:
        data = request.get_json()
        
        collection_name = data.get('collection_name')
        if not collection_name:
            return jsonify({
                'success': False,
                'message': 'collection_name is required'
            }), 400
        
        vector_size = data.get('vector_size', 1536)
        distance = data.get('distance', 'Cosine')
        
        # Get service
        qdrant_service = get_qdrant_service()
        
        # Create collection
        result = qdrant_service.create_collection(collection_name, vector_size, distance)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error creating collection: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to create collection: {str(e)}'
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>', methods=['PUT'])
def create_collection_by_name(collection_name):
    """
    Buat Qdrant collection dengan nama langsung (menyerupai REST Qdrant PUT /collections/:collection_name)

    Request Body opsional:
    {
        "vector_size": 1536,
        "distance": "Cosine"
    }
    """
    try:
        data = request.get_json() or {}
        vector_size = data.get('vector_size')
        distance = data.get('distance', 'Cosine')

        qdrant_service = get_qdrant_service()
        result = qdrant_service.create_collection(collection_name, vector_size, distance)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error creating collection by name '{collection_name}': {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to create collection: {str(e)}'
        }), 500

@qdrant_kb_bp.route('/collections', methods=['GET'])
def list_collections():
    """
    List semua Qdrant collections
    
    Response:
    {
        "success": true,
        "data": {
            "collections": [
                {
                    "collection_name": "KSM",
                    "status": "green",
                    "vectors_count": 150,
                    "config": {
                        "vector_size": 1536,
                        "distance": "Cosine"
                    }
                }
            ],
            "total": 1
        }
    }
    """
    try:
        # Get service
        qdrant_service = get_qdrant_service()
        
        # List collections - normalisasi hasil agar selalu dalam format standar
        result = qdrant_service.list_collections()
        # Jika service mengembalikan list mentah (kompat lama), bungkus ke format standar
        if isinstance(result, list):
            result = {
                'success': True,
                'data': {
                    'collections': result,
                    'total': len(result)
                }
            }
        if isinstance(result, dict) and result.get('success'):
            return jsonify(result), 200
        return jsonify(result if isinstance(result, dict) else {'success': False, 'message': 'Unknown error'}), 500
        
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to list collections: {str(e)}'
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>', methods=['GET'])
def get_collection_info(collection_name):
    """
    Get detail collection dari Qdrant
    
    Response:
    {
        "success": true,
        "data": {
            "collection_name": "KSM",
            "status": "green",
            "vectors_count": 150,
            "indexed_vectors_count": 150,
            "points_count": 150,
            "config": {
                "vector_size": 1536,
                "distance": "Cosine"
            }
        }
    }
    """
    try:
        # Get service
        qdrant_service = get_qdrant_service()
        
        # Get collection info
        result = qdrant_service.get_collection_info(collection_name)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
        
    except Exception as e:
        logger.error(f"Error getting collection info: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get collection info: {str(e)}'
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/details', methods=['GET'])
def get_collection_details_raw(collection_name):
    """
    Get collection details (raw) langsung dari Qdrant REST API.

    Response mengikuti struktur Qdrant (usage, time, status, result...).
    """
    try:
        qdrant_service = get_qdrant_service()
        result = qdrant_service.get_collection_details_raw(collection_name)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error getting raw collection details: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>', methods=['DELETE'])
def delete_collection(collection_name):
    """
    Hapus Qdrant collection
    
    Response:
    {
        "success": true,
        "message": "Collection deleted successfully",
        "data": {
            "collection_name": "KSM",
            "deleted_at": "2024-01-01T12:00:00Z"
        }
    }
    """
    try:
        # Get service
        qdrant_service = get_qdrant_service()
        
        # Delete collection
        result = qdrant_service.delete_collection(collection_name)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error deleting collection: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to delete collection: {str(e)}'
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/index', methods=['PUT'])
def create_collection_payload_index(collection_name):
    """
    Buat payload index untuk sebuah collection di Qdrant.

    Request Body contoh:
    {
        "field_name": "metadata.company_id",
        "field_schema": "keyword",
        "company_id": "PT. Kian Santang Muliatama",  # opsional jika ingin gunakan pola nama otomatis
        "collection": "default"         # opsional jika tidak menggunakan <collection_name> langsung
    }

    Response standar:
    {
        "success": true,
        "message": "Payload index dibuat",
        "data": {"collection_name": "...", "field_name": "...", "field_schema": "keyword", "operation_id": 1}
    }
    """
    try:
        data = request.get_json() or {}
        field_name = data.get('field_name')
        field_schema = data.get('field_schema', 'keyword')
        company_id = data.get('company_id')
        collection = data.get('collection', 'default')

        if not field_name:
            return jsonify({
                'success': False,
                'message': 'field_name diperlukan'
            }), 400

        qdrant_service = get_qdrant_service()
        # Prioritaskan collection_name dari URL (sesuai pola endpoint REST Qdrant)
        result = qdrant_service.create_payload_index(
            collection_name=collection_name,
            company_id=company_id,
            collection=collection,
            field_name=field_name,
            field_schema=field_schema
        )
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error creating payload index on collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/index/<field_name>', methods=['DELETE'])
def delete_collection_payload_index(collection_name, field_name):
    """
    Hapus payload index untuk sebuah collection di Qdrant.

    Response standar:
    {
        "success": true,
        "message": "Payload index dihapus",
        "data": {"collection_name": "...", "field_name": "...", "operation_id": 1}
    }
    """
    try:
        qdrant_service = get_qdrant_service()
        result = qdrant_service.delete_payload_index(
            collection_name=collection_name,
            field_name=field_name
        )
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error deleting payload index {field_name} on collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>', methods=['PUT'])
def update_collection(collection_name):
    """
    Update collection parameters
    
    Request Body:
    {
        "optimizer_config": {
            "indexing_threshold": 10000
        }
    }
    
    Response:
    {
        "success": true,
        "message": "Collection updated successfully",
        "data": {
            "collection_name": "KSM",
            "updated_at": "2024-01-01T12:00:00Z"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Get service
        qdrant_service = get_qdrant_service()
        
        # Update collection (implementasi sederhana untuk sekarang)
        # TODO: Implement proper collection parameter updates
        return jsonify({
            'success': True,
            'message': 'Collection update functionality coming soon',
            'data': {
                'collection_name': collection_name,
                'updated_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating collection: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to update collection: {str(e)}'
        }), 500

# ===== SEARCH ENDPOINTS =====

@qdrant_kb_bp.route('/search', methods=['POST'])
def search_similar():
    """
    Vector similarity search dalam collection
    
    Request Body:
    {
        "query": "cara menggunakan sistem",
        "collection_name": "KSM",
        "limit": 10,
        "score_threshold": 0.7
    }
    
    Response:
    {
        "success": true,
        "data": {
            "query": "cara menggunakan sistem",
            "collection_name": "KSM",
            "results": [
                {
                    "id": "123_456",
                    "score": 0.85,
                    "payload": {
                        "document_id": 123,
                        "chunk_id": 456,
                        "text": "Untuk menggunakan sistem...",
                        "company_id": "PT. Kian Santang Muliatama"
                    }
                }
            ],
            "total_found": 5
        }
    }
    """
    try:
        data = request.get_json()
        
        query = data.get('query')
        collection_name = data.get('collection_name')
        
        if not query or not collection_name:
            return jsonify({
                'success': False,
                'message': 'query and collection_name are required'
            }), 400
        
        limit = data.get('limit', 10)
        score_threshold = data.get('score_threshold', 0.7)
        
        # Get services
        qdrant_service = get_qdrant_service()
        from domains.knowledge.services.openai_embedding_service import OpenAIEmbeddingService
        embedding_service = OpenAIEmbeddingService()
        
        # Generate query embedding
        query_embedding = embedding_service.embed_text(query)
        if not query_embedding:
            return jsonify({
                'success': False,
                'message': 'Failed to generate query embedding'
            }), 500
        
        # Search similar with embedding
        result = qdrant_service.search_documents(
            company_id=data.get('company_id', 'PT. Kian Santang Muliatama'),
            query=query,
            top_k=limit,
            collection='default',
            query_embedding=query_embedding
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Error searching similar: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Search failed: {str(e)}'
        }), 500

# ===== HEALTH CHECK ENDPOINTS =====

@qdrant_kb_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check untuk Qdrant Knowledge Base service
    
    Response:
    {
        "success": true,
        "message": "Service is healthy",
        "data": {
            "qdrant_status": "connected",
            "openai_status": "configured",
            "database_status": "connected",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    }
    """
    try:
        # Get service
        qdrant_service = get_qdrant_service()
        
        # Check Qdrant connection
        qdrant_status = "disconnected"
        try:
            qdrant_service.qdrant_client.get_collections()
            qdrant_status = "connected"
        except:
            pass
        
        # Check OpenAI configuration
        openai_status = "not_configured"
        if qdrant_service.openai_api_key:
            openai_status = "configured"
        
        # Check database connection
        database_status = "disconnected"
        try:
            db.session.execute(db.text("SELECT 1"))
            database_status = "connected"
        except:
            pass
        
        return jsonify({
            'success': True,
            'message': 'Service is healthy',
            'data': {
                'qdrant_status': qdrant_status,
                'openai_status': openai_status,
                'database_status': database_status,
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Health check failed: {str(e)}'
        }), 500

# ===== ADVANCED DOCUMENT PROCESSING ENDPOINTS =====

@qdrant_kb_bp.route('/documents/<int:document_id>/process/local', methods=['POST'])
def process_local_document(document_id):
    """
    Trigger processing dokumen RAG DI KSM-MAIN (lokal), bukan Agent AI
    
    Response:
    {
        "success": true,
        "message": "Document submitted for local processing",
        "data": {
            "document_id": 123,
            "status": "processing",
            "job_id": "job_123"
        }
    }
    """
    try:
        document = RagDocument.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f'Document with ID {document_id} not found'
            }), 404
        
        if document.status != 'uploaded':
            return jsonify({
                'success': False,
                'message': f'Document status is {document.status}, cannot process'
            }), 400
        
        # Update status ke processing
        document.status = 'processing'
        db.session.commit()
        
        # Jalankan full processing dengan embeddings
        try:
            logger.info(f"🔄 Starting full processing for document {document.id}")
            
            # Full PDF processing with embeddings
            try:
                import PyPDF2
                import io
                import uuid
                from domains.knowledge.services.openai_embedding_service import OpenAIEmbeddingService
                from domains.knowledge.services.qdrant_service import get_qdrant_service
                
                # Initialize services
                embedding_service = OpenAIEmbeddingService()
                qdrant_service = get_qdrant_service()
                
                # Read file from storage
                with open(document.storage_path, 'rb') as f:
                    file_content = f.read()
                
                # Extract text from PDF
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                total_pages = len(pdf_reader.pages)
                
                # Extract all text
                all_text = ""
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    all_text += page_text + "\n"
                    
                    # Create page record (metadata only)
                    page_record = RagDocumentPage(
                        document_id=document.id,
                        page_number=page_num + 1,
                        text_len=len(page_text),
                        has_text=len(page_text.strip()) > 0,
                        created_at=datetime.now()
                    )
                    db.session.add(page_record)
                
                # Create chunks
                chunk_size = 1000
                overlap = 200
                chunks = []
                
                for i in range(0, len(all_text), chunk_size - overlap):
                    chunk = all_text[i:i+chunk_size]
                    if len(chunk.strip()) > 0:
                        chunks.append(chunk)
                        
                        # Create chunk record in database
                        from domains.knowledge.models.rag_models import RagDocumentChunk
                        import hashlib
                        
                        chunk_record = RagDocumentChunk(
                            document_id=document.id,
                            chunk_index=len(chunks) - 1,
                            text=chunk,
                            tokens=len(chunk.split()),
                            text_hash=hashlib.sha256(chunk.encode()).hexdigest(),
                            created_at=datetime.now()
                        )
                        db.session.add(chunk_record)
                
                logger.info(f"📄 Created {len(chunks)} chunks from {total_pages} pages")
                
                # Generate embeddings
                embeddings = []
                for i, chunk in enumerate(chunks):
                    embedding = embedding_service.embed_text(chunk)
                    if embedding:
                        embeddings.append(embedding)
                    else:
                        logger.warning(f"⚠️ Failed to generate embedding for chunk {i+1}")
                
                logger.info(f"📄 Generated {len(embeddings)} embeddings")
                
                # Store in Qdrant
                if embeddings:
                    qdrant_docs = []
                    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                        doc = {
                            'id': str(uuid.uuid4()),
                            'text': chunk,
                            'embedding': embedding,
                            'document_id': document.id,
                            'chunk_index': i,
                            'company_id': document.company_id
                        }
                        qdrant_docs.append(doc)
                    
                    # Store in Qdrant
                    result = qdrant_service.add_documents(
                        company_id=document.company_id,
                        documents=qdrant_docs,
                        collection='default'
                    )
                    
                    if result:
                        logger.info(f"✅ Successfully stored {len(qdrant_docs)} vectors in Qdrant")
                        
                        # Update document
                        document.status = 'ready'
                        document.total_pages = total_pages
                        document.vector_count = len(qdrant_docs)
                        document.qdrant_collection = f"{document.company_id}_KSM_default"
                        db.session.commit()
                        
                        job_id = f"full_processing_job_{document.id}"
                        logger.info(f"✅ Full processing completed for document {document.id}: {total_pages} pages, {len(qdrant_docs)} vectors")
                    else:
                        logger.error(f"❌ Failed to store vectors in Qdrant for document {document.id}")
                        document.status = 'failed'
                        db.session.commit()
                        job_id = f"failed_job_{document.id}"
                else:
                    logger.error(f"❌ No embeddings generated for document {document.id}")
                    document.status = 'failed'
                    db.session.commit()
                    job_id = f"failed_job_{document.id}"
                
            except Exception as pdf_error:
                logger.error(f"❌ PDF processing failed for document {document.id}: {str(pdf_error)}")
                document.status = 'failed'
                db.session.commit()
                job_id = f"failed_job_{document.id}"
            
            return jsonify({
                'success': True,
                'message': 'Document submitted for local processing',
                'data': {
                    'document_id': document.id,
                    'status': 'processing',
                    'job_id': job_id
                }
            }), 200
            
        except ImportError:
            # Fallback jika async_document_processor tidak tersedia
            return jsonify({
                'success': False,
                'message': 'Local document processor not available'
            }), 503
        
    except Exception as e:
        logger.error(f"Error processing RAG document {document_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/documents/<int:document_id>/pages', methods=['POST'])
def store_document_pages(document_id):
    """
    Store document pages (dipanggil oleh Agent AI atau local processor)
    
    Request Body:
    {
        "pages": [
            {
                "page_number": 1,
                "has_text": true,
                "ocr_used": false,
                "text_len": 150,
                "bbox_available": false
            }
        ]
    }
    
    Response:
    {
        "success": true,
        "message": "Stored 1 pages successfully",
        "data": {
            "document_id": 123,
            "pages_count": 1
        }
    }
    """
    try:
        data = request.get_json()
        pages_data = data.get('pages', [])
        
        if not pages_data:
            return jsonify({
                'success': False,
                'message': 'Pages data is required'
            }), 400
        
        document = RagDocument.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f'Document with ID {document_id} not found'
            }), 404
        
        # Store pages
        for page_data in pages_data:
            page = RagDocumentPage(
                document_id=document_id,
                page_number=page_data['page_number'],
                has_text=page_data.get('has_text', True),
                ocr_used=page_data.get('ocr_used', False),
                text_len=page_data.get('text_len', 0),
                bbox_available=page_data.get('bbox_available', False)
            )
            db.session.add(page)
        
        db.session.commit()
        
        logger.info(f"✅ Stored {len(pages_data)} pages for document {document_id}")
        
        return jsonify({
            'success': True,
            'message': f'Stored {len(pages_data)} pages successfully',
            'data': {
                'document_id': document_id,
                'pages_count': len(pages_data)
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error storing pages for document {document_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/documents/<int:document_id>/chunks', methods=['POST'])
def store_document_chunks(document_id):
    """
    Store document chunks (dipanggil oleh Agent AI atau local processor)
    
    Request Body:
    {
        "chunks": [
            {
                "chunk_index": 1,
                "text": "chunk content",
                "text_len": 150,
                "page_number": 1,
                "bbox": {"x": 0, "y": 0, "width": 100, "height": 50}
            }
        ]
    }
    
    Response:
    {
        "success": true,
        "message": "Stored 1 chunks successfully",
        "data": {
            "document_id": 123,
            "chunks_count": 1
        }
    }
    """
    try:
        data = request.get_json()
        chunks_data = data.get('chunks', [])
        
        if not chunks_data:
            return jsonify({
                'success': False,
                'message': 'Chunks data is required'
            }), 400
        
        document = RagDocument.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f'Document with ID {document_id} not found'
            }), 404
        
        # Store chunks
        for chunk_data in chunks_data:
            chunk = RagDocumentChunk(
                document_id=document_id,
                chunk_index=chunk_data['chunk_index'],
                text=chunk_data['text'],
                text_len=chunk_data.get('text_len', len(chunk_data['text'])),
                page_number=chunk_data.get('page_number', 1),
                bbox=json.dumps(chunk_data.get('bbox', {})) if chunk_data.get('bbox') else None
            )
            db.session.add(chunk)
        
        db.session.commit()
        
        logger.info(f"✅ Stored {len(chunks_data)} chunks for document {document_id}")
        
        return jsonify({
            'success': True,
            'message': f'Stored {len(chunks_data)} chunks successfully',
            'data': {
                'document_id': document_id,
                'chunks_count': len(chunks_data)
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error storing chunks for document {document_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/documents/<int:document_id>/embeddings', methods=['POST'])
def store_document_embeddings(document_id):
    """
    Store document embeddings (dipanggil oleh Agent AI atau local processor)
    
    Request Body:
    {
        "embeddings": [
            {
                "chunk_id": 1,
                "embedding": [0.1, 0.2, ...],
                "model": "text-embedding-3-small",
                "dimensions": 1536
            }
        ]
    }
    
    Response:
    {
        "success": true,
        "message": "Stored 1 embeddings successfully",
        "data": {
            "document_id": 123,
            "embeddings_count": 1
        }
    }
    """
    try:
        data = request.get_json()
        embeddings_data = data.get('embeddings', [])
        
        if not embeddings_data:
            return jsonify({
                'success': False,
                'message': 'Embeddings data is required'
            }), 400
        
        document = RagDocument.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f'Document with ID {document_id} not found'
            }), 404
        
        # Store embeddings
        for embedding_data in embeddings_data:
            embedding = RagChunkEmbedding(
                chunk_id=embedding_data['chunk_id'],
                embedding=json.dumps(embedding_data['embedding']),
                model=embedding_data.get('model', 'text-embedding-3-small'),
                dimensions=embedding_data.get('dimensions', 1536)
            )
            db.session.add(embedding)
        
        db.session.commit()
        
        logger.info(f"✅ Stored {len(embeddings_data)} embeddings for document {document_id}")
        
        return jsonify({
            'success': True,
            'message': f'Stored {len(embeddings_data)} embeddings successfully',
            'data': {
                'document_id': document_id,
                'embeddings_count': len(embeddings_data)
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error storing embeddings for document {document_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/documents/<int:document_id>/processing-status', methods=['GET'])
def get_processing_status(document_id):
    """
    Get processing status dokumen
    
    Response:
    {
        "success": true,
        "data": {
            "document_id": 123,
            "status": "processing",
            "progress": 75,
            "current_step": "generating_embeddings",
            "total_pages": 10,
            "processed_pages": 7,
            "total_chunks": 25,
            "processed_chunks": 18
        }
    }
    """
    try:
        document = RagDocument.query.get(document_id)
        if not document:
            return jsonify({
                'success': False,
                'message': f'Document with ID {document_id} not found'
            }), 404
        
        # Calculate progress
        total_pages = document.total_pages or 0
        total_chunks = len(document.chunks) if document.chunks else 0
        
        progress = 0
        current_step = "unknown"
        
        if document.status == 'uploaded':
            progress = 0
            current_step = "waiting_for_processing"
        elif document.status == 'processing':
            if total_pages > 0:
                progress = min(50, (total_pages / max(total_pages, 1)) * 50)
                current_step = "extracting_pages"
            if total_chunks > 0:
                progress = min(90, 50 + (total_chunks / max(total_chunks, 1)) * 40)
                current_step = "generating_embeddings"
        elif document.status == 'ready':
            progress = 100
            current_step = "completed"
        elif document.status == 'failed':
            progress = 0
            current_step = "failed"
        
        return jsonify({
            'success': True,
            'data': {
                'document_id': document_id,
                'status': document.status,
                'progress': progress,
                'current_step': current_step,
                'total_pages': total_pages,
                'processed_pages': total_pages if document.status == 'ready' else 0,
                'total_chunks': total_chunks,
                'processed_chunks': total_chunks if document.status == 'ready' else 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting processing status for document {document_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== RAG QUERY ENDPOINTS =====

@qdrant_kb_bp.route('/query', methods=['POST'])
def rag_query():
    """
    Complete RAG query pipeline: Search + Context + Generate
    
    Request Body:
    {
        "query": "cara menggunakan sistem",
        "company_id": "PT. Kian Santang Muliatama",
        "top_k": 5,
        "collection": "default"
    }
    
    Response:
    {
        "success": true,
        "response": "Untuk menggunakan sistem...",
        "search_results": [...],
        "context_used": 3,
        "processing_time": 1.234,
        "model_used": "text-embedding-3-small"
    }
    """
    try:
        data = request.get_json()
        
        query = data.get('query')
        company_id = data.get('company_id', 'PT. Kian Santang Muliatama')
        top_k = data.get('top_k', 5)
        collection = data.get('collection', 'default')
        
        if not query:
            return jsonify({
                'success': False,
                'message': 'query is required'
            }), 400
        
        # Use qdrant service for RAG query
        try:
            qdrant_service = get_qdrant_service()
            from domains.knowledge.services.openai_embedding_service import OpenAIEmbeddingService
            embedding_service = OpenAIEmbeddingService()
            
            if qdrant_service:
                # Generate query embedding
                query_embedding = embedding_service.embed_text(query)
                if not query_embedding:
                    return jsonify({
                        'success': False,
                        'message': 'Failed to generate query embedding'
                    }), 500
                
                # Use qdrant service for search with embedding
                search_result = qdrant_service.search_documents(
                    company_id=company_id,
                    query=query,
                    top_k=top_k,
                    collection=collection,
                    query_embedding=query_embedding
                )
                
                if search_result.get('success'):
                    return jsonify({
                        'success': True,
                        'response': 'Search completed, response generation handled by Agent AI',
                        'search_results': search_result.get('data', {}).get('results', []),
                        'context_used': len(search_result.get('data', {}).get('results', [])),
                        'processing_time': 0.1,
                        'model_used': 'qdrant'
                    }), 200
                else:
                    return jsonify(search_result), 500
            else:
                return jsonify({
                    'success': False,
                    'message': 'Qdrant service not available'
                }), 503
                    
        except Exception as e:
            logger.error(f"Error in qdrant service: {e}")
            return jsonify({
                'success': False,
                'message': 'RAG service not available'
            }), 503
        
    except Exception as e:
        logger.error(f"Error in RAG query: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'RAG query failed: {str(e)}'
        }), 500

@qdrant_kb_bp.route('/query/batch', methods=['POST'])
def rag_query_batch():
    """
    RAG batch query: menerima banyak pertanyaan sekaligus dan mengembalikan hasil per-query.

    Request Body:
    {
        "queries": ["cara menggunakan sistem", "bagaimana reset password"],
        "company_id": "PT. Kian Santang Muliatama",
        "top_k": 5,
        "collection": "default",
        "filters": [ {"metadata.department": "support"}, null ]  // opsional per-query
    }

    Response:
    {
        "success": true,
        "data": {
            "results": [ [ {..}, {..} ], [ {..} ] ],
            "counts": [2, 1],
            "queries": ["cara menggunakan sistem", "bagaimana reset password"],
            "processing_time_ms": 123.45
        }
    }
    """
    try:
        data = request.get_json() or {}
        queries = data.get('queries') or []
        company_id = data.get('company_id', 'PT. Kian Santang Muliatama')
        top_k = int(data.get('top_k', 5))
        collection = data.get('collection', 'default')
        filters = data.get('filters')  # opsional: list sama panjang dengan queries

        if not isinstance(queries, list) or len(queries) == 0:
            return jsonify({
                'success': False,
                'message': 'queries (list) diperlukan'
            }), 400

        # Layanan
        qdrant_service = get_qdrant_service()
        try:
            from domains.knowledge.services.openai_embedding_service import OpenAIEmbeddingService
            embedding_service = OpenAIEmbeddingService()
        except Exception as e:
            logger.error(f"Embedding service unavailable: {e}")
            return jsonify({
                'success': False,
                'message': 'Embedding service unavailable'
            }), 503

        # Generate embeddings per query
        import time
        start_time = time.time()
        embeddings = []
        for q in queries:
            emb = embedding_service.embed_text(str(q) if q is not None else '')
            if not emb:
                embeddings.append([])  # tetap jaga indeks; hasil akan kosong
            else:
                embeddings.append(emb)

        # Panggil batch search; untuk query tanpa embedding valid, filter-kan vektor kosong agar hasilnya []
        valid_indices = [i for i, v in enumerate(embeddings) if isinstance(v, list) and len(v) > 0]
        batch_results: list[list[dict]] = [[] for _ in queries]
        if len(valid_indices) > 0:
            # Susun embeddings dan filters valid berurutan
            valid_embeddings = [embeddings[i] for i in valid_indices]
            valid_filters = None
            if isinstance(filters, list) and len(filters) == len(queries):
                valid_filters = [filters[i] for i in valid_indices]

            grouped = qdrant_service.search_documents_batch(
                company_id=company_id,
                embeddings=valid_embeddings,
                top_k=top_k,
                collection=collection,
                filters=valid_filters
            ) or []

            # Re-map ke posisi semula
            for pos, gi in enumerate(valid_indices):
                if pos < len(grouped):
                    batch_results[gi] = grouped[pos] or []

        elapsed_ms = round((time.time() - start_time) * 1000.0, 2)
        counts = [len(r or []) for r in batch_results]

        return jsonify({
            'success': True,
            'data': {
                'results': batch_results,
                'counts': counts,
                'queries': queries,
                'processing_time_ms': elapsed_ms
            }
        }), 200

    except Exception as e:
        logger.error(f"Error in RAG batch query: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'RAG batch query failed: {str(e)}'
        }), 500

# ===== POINTS UPSERT ENDPOINT =====

@qdrant_kb_bp.route('/collections/<collection_name>/points', methods=['PUT'])
def upsert_points(collection_name):
    """
    Upsert points ke Qdrant collection.
    
    Request Body contoh minimal:
    {
        "points": [
            {"id": 1, "payload": {"color": "red"}, "vector": [0.9, 0.1, 0.1]},
            {"id": 2, "payload": {"color": "green"}, "vector": [0.1, 0.9, 0.1]}
        ]
    }
    
    Response standar:
    {
        "success": true,
        "message": "Upsert 3 points ke KSM_company_default berhasil",
        "data": {"collection_name": "...", "points_upserted": 3, "operation_ids": [1]}
    }
    """
    try:
        data = request.get_json() or {}
        points = data.get('points', [])
        company_id = data.get('company_id')  # optional jika ingin bangun nama koleksi otomatis
        collection = data.get('collection', 'default')
        
        if not points or not isinstance(points, list):
            return jsonify({
                'success': False,
                'message': 'points (list) diperlukan'
            }), 400
        
        qdrant_service = get_qdrant_service()
        # Gunakan nama koleksi yang diberikan pada URL terlebih dahulu
        result = qdrant_service.upsert_points(
            collection_name=collection_name,
            company_id=company_id,
            collection=collection,
            points=points
        )
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error upserting points to collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/points/query', methods=['POST'])
def query_points(collection_name):
    """
    Proxy modular untuk Qdrant POST /collections/:collection_name/points/query.

    Body request diteruskan apa adanya ke Qdrant agar mendukung seluruh variasi query:
    - query by id/string/vector
    - recommend (RecommendQuery)
    - fusion/hybrid (prefetch + FusionQuery)
    - two-stage/colbert multi-vector
    - sample/random, formula/score boost, geo boost, dsb.

    Response akan mengikuti struktur Qdrant (usage, time, status, result...).
    """
    try:
        body = request.get_json() or {}
        qdrant_service = get_qdrant_service()
        result = qdrant_service.query_points_raw(collection_name, body)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error querying points in collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/points/query/batch', methods=['POST'])
def query_points_batch(collection_name):
    """
    Proxy batch untuk Qdrant POST /collections/:collection_name/points/query/batch.

    Body harus berisi "requests": [ { ... }, ... ] sesuai spesifikasi Qdrant SDK/REST.
    """
    try:
        body = request.get_json() or {}
        qdrant_service = get_qdrant_service()
        result = qdrant_service.query_batch_points_raw(collection_name, body)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error batch querying points in collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/points/query/groups', methods=['POST'])
def query_points_groups(collection_name):
    """
    Proxy groups untuk Qdrant POST /collections/:collection_name/points/query/groups.

    Body fleksibel: { "query": [...], "group_by": "document_id", "limit": 10, "group_size": 5, ... }
    """
    try:
        body = request.get_json() or {}
        qdrant_service = get_qdrant_service()
        result = qdrant_service.query_points_groups_raw(collection_name, body)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error grouping query points in collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/points/search/matrix/pairs', methods=['POST'])
def search_matrix_pairs(collection_name):
    """
    Proxy untuk Qdrant POST /collections/:collection_name/points/search/matrix/pairs.

    Body contoh: { "sample": 100, "limit": 5, "filter": { ... } }
    """
    try:
        body = request.get_json() or {}
        qdrant_service = get_qdrant_service()
        result = qdrant_service.search_matrix_pairs_raw(collection_name, body)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error distance matrix pairs in collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/points/search/matrix/offsets', methods=['POST'])
def search_matrix_offsets(collection_name):
    """
    Proxy untuk Qdrant POST /collections/:collection_name/points/search/matrix/offsets.

    Body contoh: { "sample": 100, "limit": 5, "filter": { ... } }
    """
    try:
        body = request.get_json() or {}
        qdrant_service = get_qdrant_service()
        result = qdrant_service.search_matrix_offsets_raw(collection_name, body)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error distance matrix offsets in collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/points', methods=['POST'])
def retrieve_points(collection_name):
    """
    Retrieve points berdasarkan IDs dengan opsi payload/vectors.
    
    Contoh request body:
    {
        "ids": [0, 3, 100],
        "with_payload": true,
        "with_vectors": false
    }
    """
    try:
        data = request.get_json() or {}
        ids = data.get('ids')
        with_payload = data.get('with_payload', True)
        with_vectors = data.get('with_vectors', False)
        company_id = data.get('company_id')
        collection = data.get('collection', 'default')
        
        if not ids or not isinstance(ids, list):
            return jsonify({
                'success': False,
                'message': 'ids (list) diperlukan'
            }), 400
        
        qdrant_service = get_qdrant_service()
        result = qdrant_service.retrieve_points(
            collection_name=collection_name,
            company_id=company_id,
            collection=collection,
            ids=ids,
            with_payload=with_payload,
            with_vectors=with_vectors
        )
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error retrieving points from collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/points/delete', methods=['POST'])
def delete_points(collection_name):
    """
    Delete points dari Qdrant collection dengan ids atau filter.
    
    Contoh request body (by ids):
    {
        "ids": [0, 3, 100]
    }
    
    Contoh request body (by filter):
    {
        "filter": {
            "must": [
                {"key": "payload.color", "value": "red"}
            ]
        }
    }
    """
    try:
        data = request.get_json() or {}
        ids = data.get('ids')
        filter_payload = data.get('filter')
        company_id = data.get('company_id')
        collection = data.get('collection', 'default')
        
        if not ids and not filter_payload:
            return jsonify({
                'success': False,
                'message': 'ids atau filter diperlukan'
            }), 400
        
        qdrant_service = get_qdrant_service()
        result = qdrant_service.delete_points(
            collection_name=collection_name,
            company_id=company_id,
            collection=collection,
            ids=ids,
            filter=filter_payload
        )
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error deleting points from collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/points/scroll', methods=['POST'])
def scroll_points(collection_name):
    """
    Scroll points pada Qdrant collection dengan filter dan pagination.
    
    Contoh request body:
    {
        "filter": {
            "must": [
                {"key": "payload.color", "value": "red"}
            ]
        },
        "limit": 2,
        "with_payload": true,
        "with_vectors": false,
        "offset": null
    }
    """
    try:
        data = request.get_json() or {}
        filter_payload = data.get('filter')
        limit = data.get('limit', 10)
        with_payload = data.get('with_payload', True)
        with_vectors = data.get('with_vectors', False)
        offset = data.get('offset')
        company_id = data.get('company_id')
        collection = data.get('collection', 'default')
        
        qdrant_service = get_qdrant_service()
        result = qdrant_service.scroll_points(
            collection_name=collection_name,
            company_id=company_id,
            collection=collection,
            filter=filter_payload,
            limit=limit,
            with_payload=with_payload,
            with_vectors=with_vectors,
            offset=offset
        )
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error scrolling points in collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/points/count', methods=['POST'])
def count_points(collection_name):
    """
    Hitung jumlah points pada Qdrant collection dengan filter opsional.
    
    Contoh request body:
    {
        "filter": {
            "must": [
                {"key": "payload.color", "value": "red"}
            ]
        },
        "exact": true
    }
    """
    try:
        data = request.get_json() or {}
        filter_payload = data.get('filter')
        exact = data.get('exact', True)
        company_id = data.get('company_id')
        collection = data.get('collection', 'default')
        
        qdrant_service = get_qdrant_service()
        result = qdrant_service.count_points(
            collection_name=collection_name,
            company_id=company_id,
            collection=collection,
            filter=filter_payload,
            exact=exact
        )
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error counting points in collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/points/<point_id>', methods=['GET'])
def get_point(collection_name, point_id):
    """
    Retrieve single point by ID.
    
    Query params optional:
    - with_payload: bool (default true)
    - with_vectors: bool (default false)
    
    Response standar mengikuti retrieve multi, namun untuk satu point.
    """
    try:
        with_payload = request.args.get('with_payload', 'true').lower() != 'false'
        with_vectors = request.args.get('with_vectors', 'false').lower() == 'true'
        company_id = request.args.get('company_id')
        collection = request.args.get('collection', 'default')
        
        qdrant_service = get_qdrant_service()
        result = qdrant_service.retrieve_points(
            collection_name=collection_name,
            company_id=company_id,
            collection=collection,
            ids=[point_id],
            with_payload=with_payload,
            with_vectors=with_vectors
        )
        if result.get('success'):
            items = result.get('data', []) or []
            point = items[0] if items else None
            return jsonify({
                'success': True,
                'message': 'Retrieve berhasil',
                'data': point
            }), 200
        return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error retrieving point {point_id} from collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/points/payload', methods=['POST'])
def set_points_payload(collection_name):
    """
    Set payload untuk points terpilih (by ids atau filter).
    
    Contoh request body (by ids):
    {
        "payload": {"property1": "string", "property2": "string"},
        "ids": [0, 3, 10]
    }
    
    Contoh request body (by filter):
    {
        "payload": {"tag": "important"},
        "filter": {"must": [{"key": "metadata.company_id", "value": "acme"}]}
    }
    """
    try:
        data = request.get_json() or {}
        payload = data.get('payload')
        ids = data.get('ids')
        filter_payload = data.get('filter')
        company_id = data.get('company_id')
        collection = data.get('collection', 'default')
        
        if not payload or not isinstance(payload, dict):
            return jsonify({
                'success': False,
                'message': 'payload (dict) diperlukan'
            }), 400
        
        if not ids and not filter_payload:
            return jsonify({
                'success': False,
                'message': 'ids atau filter diperlukan'
            }), 400
        
        qdrant_service = get_qdrant_service()
        result = qdrant_service.set_payload(
            collection_name=collection_name,
            company_id=company_id,
            collection=collection,
            payload=payload,
            ids=ids,
            filter=filter_payload
        )
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error setting payload in collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/collections/<collection_name>/points/vectors', methods=['PUT'])
def update_vectors(collection_name):
    """
    Update vectors secara batch tanpa mengubah payload.
    
    Contoh request body:
    {
        "vectors": [
            {"id": 1, "vector": [0.1, 0.2, ...]},
            {"id": 2, "vector": [0.2, 0.3, ...]}
        ]
    }
    """
    try:
        data = request.get_json() or {}
        vectors = data.get('vectors')
        company_id = data.get('company_id')
        collection = data.get('collection', 'default')
        
        if not vectors or not isinstance(vectors, list):
            return jsonify({
                'success': False,
                'message': 'vectors (list) diperlukan'
            }), 400
        
        qdrant_service = get_qdrant_service()
        result = qdrant_service.update_vectors(
            collection_name=collection_name,
            company_id=company_id,
            collection=collection,
            vectors=vectors
        )
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error updating vectors in collection {collection_name}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@qdrant_kb_bp.route('/config', methods=['GET'])
def get_config():
    """
    Get RAG configuration
    
    Response:
    {
        "success": true,
        "data": {
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "similarity_threshold": 0.3,
            "max_context_length": 30000,
            "top_k_results": 10,
            "embedding_model": "text-embedding-3-small",
            "vector_size": 1536
        }
    }
    """
    try:
        # Get configuration from environment or defaults
        config = {
            'chunk_size': int(os.getenv('RAG_CHUNK_SIZE', '1000')),
            'chunk_overlap': int(os.getenv('RAG_CHUNK_OVERLAP', '200')),
            'similarity_threshold': float(os.getenv('RAG_SIMILARITY_THRESHOLD', '0.3')),
            'max_context_length': int(os.getenv('RAG_MAX_CONTEXT_LENGTH', '30000')),
            'top_k_results': int(os.getenv('RAG_TOP_K_RESULTS', '10')),
            'embedding_model': os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small'),
            'vector_size': int(os.getenv('QDRANT_VECTOR_SIZE', '1536'))
        }
        
        return jsonify({
            'success': True,
            'data': config
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting RAG config: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get config: {str(e)}'
        }), 500

# ===== STATISTICS ENDPOINTS =====

@qdrant_kb_bp.route('/stats', methods=['GET'])
def get_statistics():
    """
    Get statistics untuk dashboard
    
    Query Parameters:
    - company_id: ID perusahaan (optional)
    
    Response:
    {
        "success": true,
        "data": {
            "total_documents": 25,
            "total_collections": 3,
            "total_vectors": 500,
            "total_storage_mb": 150.5,
            "documents_by_status": {
                "ready": 20,
                "processing": 3,
                "failed": 2
            }
        }
    }
    """
    try:
        company_id = request.args.get('company_id')
        
        # Get document statistics
        query = RagDocument.query
        if company_id:
            query = query.filter_by(company_id=company_id)
        
        total_documents = query.count()
        
        # Documents by status
        status_counts = {}
        for status in ['uploaded', 'processing', 'ready', 'failed']:
            count = query.filter_by(status=status).count()
            status_counts[status] = count
        
        # Get collections count
        qdrant_service = get_qdrant_service()
        collections_result = qdrant_service.list_collections()
        total_collections = 0
        total_vectors = 0
        
        if isinstance(collections_result, dict) and collections_result.get('success'):
            # Pastikan data dan collections ada
            if 'data' in collections_result and isinstance(collections_result['data'], dict):
                collections = collections_result['data'].get('collections', [])
                if isinstance(collections, list):
                    total_collections = len(collections)
                    for collection in collections:
                        if isinstance(collection, dict):
                            total_vectors += collection.get('points_count', 0)
        else:
            # Fallback jika format tidak sesuai ekspektasi
            if isinstance(collections_result, list):
                total_collections = len(collections_result)
                for collection in collections_result:
                    if isinstance(collection, dict):
                        total_vectors += collection.get('points_count', 0)
        
        # Calculate storage (approximate)
        total_storage_mb = 0
        for doc in query.all():
            if doc.size_bytes:
                total_storage_mb += doc.size_bytes / (1024 * 1024)
        
        return jsonify({
            'success': True,
            'data': {
                'total_documents': total_documents,
                'total_collections': total_collections,
                'total_vectors': total_vectors,
                'total_storage_mb': round(total_storage_mb, 2),
                'documents_by_status': status_counts
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get statistics: {str(e)}'
        }), 500
