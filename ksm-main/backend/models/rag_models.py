#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG (Retrieval-Augmented Generation) Models untuk KSM Main Backend

Catatan:
- Seluruh model menggunakan SQLAlchemy via `config.database.db`
- Tidak ada penghapusan data otomatis (sesuai kebijakan). Soft control dilakukan melalui status/scope.
- Multi-tenant: setiap entitas terkait dokumen mengacu ke `company_id` (String) dan opsional `app_id`/`collection`.
"""

from datetime import datetime
from config.database import db


class RagDocument(db.Model):
    """Dokumen sumber (PDF) untuk modul RAG."""
    __tablename__ = 'rag_documents'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.String(100), index=True, nullable=False)
    app_id = db.Column(db.String(100), index=True)
    collection = db.Column(db.String(100), index=True)

    sha256 = db.Column(db.String(64), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255))  # Judul dokumen
    description = db.Column(db.Text)   # Deskripsi dokumen
    mime = db.Column(db.String(100), default='application/pdf')
    size_bytes = db.Column(db.BigInteger)
    total_pages = db.Column(db.Integer)
    language = db.Column(db.String(20))
    status = db.Column(db.String(20), default='uploaded')  # uploaded|processing|ready|failed
    storage_path = db.Column(db.String(500), nullable=False)
    base64_content = db.Column(db.Text)  # Base64 content untuk storage
    qdrant_collection = db.Column(db.String(100))  # Nama collection di Qdrant
    vector_count = db.Column(db.Integer, default=0)  # Jumlah vectors yang tersimpan

    created_by = db.Column(db.Integer)  # user id referensi ke users.id (legacy)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    pages = db.relationship('RagDocumentPage', backref='document', lazy=True, cascade='all, delete-orphan')
    chunks = db.relationship('RagDocumentChunk', backref='document', lazy=True, cascade='all, delete-orphan')
    permissions = db.relationship('RagDocumentPermission', backref='document', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('company_id', 'sha256', name='uq_rag_doc_company_sha256'),
    )

    def to_dict(self, include_content: bool = False):
        result = {
            'id': self.id,
            'company_id': self.company_id,
            'app_id': self.app_id,
            'collection': self.collection,
            'sha256': self.sha256,
            'original_name': self.original_name,
            'title': self.title,
            'description': self.description,
            'mime': self.mime,
            'size_bytes': self.size_bytes,
            'total_pages': self.total_pages,
            'language': self.language,
            'status': self.status,
            'storage_path': self.storage_path,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_content:
            result['base64_content'] = self.base64_content
        return result


class RagDocumentPage(db.Model):
    """Informasi per halaman dokumen, termasuk status OCR dan ketersediaan bbox."""
    __tablename__ = 'rag_document_pages'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('rag_documents.id'), nullable=False, index=True)
    page_number = db.Column(db.Integer, nullable=False)
    has_text = db.Column(db.Boolean, default=False)
    ocr_used = db.Column(db.Boolean, default=False)
    text_len = db.Column(db.Integer, default=0)
    bbox_available = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('document_id', 'page_number', name='uq_rag_doc_page'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'page_number': self.page_number,
            'has_text': self.has_text,
            'ocr_used': self.ocr_used,
            'text_len': self.text_len,
            'bbox_available': self.bbox_available,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class RagDocumentChunk(db.Model):
    """Potongan teks (chunk) hasil ekstraksi/normalisasi yang akan di-embed dan di-index."""
    __tablename__ = 'rag_document_chunks'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('rag_documents.id'), nullable=False, index=True)
    page_from = db.Column(db.Integer)
    page_to = db.Column(db.Integer)
    chunk_index = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    tokens = db.Column(db.Integer)
    text_hash = db.Column(db.String(64), index=True)
    section_title = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi
    embeddings = db.relationship('RagChunkEmbedding', backref='chunk', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('document_id', 'chunk_index', name='uq_rag_doc_chunk_index'),
    )

    def to_dict(self, include_text: bool = False):
        base = {
            'id': self.id,
            'document_id': self.document_id,
            'page_from': self.page_from,
            'page_to': self.page_to,
            'chunk_index': self.chunk_index,
            'tokens': self.tokens,
            'text_hash': self.text_hash,
            'section_title': self.section_title,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_text:
            base['text'] = self.text
        return base


class RagChunkEmbedding(db.Model):
    """Metadata embedding untuk sebuah chunk. Vektor disimpan di Qdrant vector store."""
    __tablename__ = 'rag_chunk_embeddings'

    id = db.Column(db.Integer, primary_key=True)
    chunk_id = db.Column(db.Integer, db.ForeignKey('rag_document_chunks.id'), nullable=False, index=True)
    model_name = db.Column(db.String(120), nullable=False)
    qdrant_vector_id = db.Column(db.String(100), nullable=True)  # Qdrant vector ID
    qdrant_point_id = db.Column(db.String(100), nullable=True)  # Qdrant point ID (alias untuk qdrant_vector_id)
    qdrant_collection = db.Column(db.String(100), nullable=True)  # Qdrant collection name
    embedding_status = db.Column(db.String(20), default='pending')  # pending|processing|completed|failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('chunk_id', 'model_name', name='uq_rag_chunk_model'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'chunk_id': self.chunk_id,
            'model_name': self.model_name,
            'qdrant_vector_id': self.qdrant_vector_id,
            'qdrant_point_id': self.qdrant_point_id,
            'qdrant_collection': self.qdrant_collection,
            'embedding_status': self.embedding_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class RagDocumentPermission(db.Model):
    """Kontrol akses dokumen (tanpa penghapusan)."""
    __tablename__ = 'rag_document_permissions'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('rag_documents.id'), nullable=False, index=True)
    scope = db.Column(db.String(20), default='company')  # private|team|company
    owner_user_id = db.Column(db.Integer)  # FK ke users.id (legacy table)
    team_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'scope': self.scope,
            'owner_user_id': self.owner_user_id,
            'team_id': self.team_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


