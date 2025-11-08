#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Base Controller untuk KSM Main Backend
"""

from flask import Blueprint, request, jsonify, current_app
from services.knowledge_base_service import KnowledgeBaseService
import logging
from datetime import datetime
import os

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
knowledge_base_bp = Blueprint('knowledge_base', __name__)

@knowledge_base_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get semua kategori"""
    try:
        from models.knowledge_base import KnowledgeCategory
        categories = KnowledgeCategory.query.all()
        return jsonify({
            'success': True,
            'data': [category.to_dict() for category in categories]
        }), 200
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@knowledge_base_bp.route('/categories', methods=['POST'])
def create_category():
    """Create kategori baru"""
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        parent_id = data.get('parent_id')
        
        if not name:
            return jsonify({
                'success': False,
                'message': 'Nama kategori wajib diisi'
            }), 400
        
        category = KnowledgeBaseService.create_category(name, description, parent_id)
        return jsonify({
            'success': True,
            'data': category
        }), 201
    except Exception as e:
        logger.error(f"Error creating category: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@knowledge_base_bp.route('/tags', methods=['GET'])
def get_tags():
    """Get semua tags"""
    try:
        from models.knowledge_base import KnowledgeTag
        tags = KnowledgeTag.query.all()
        return jsonify({
            'success': True,
            'data': [tag.to_dict() for tag in tags]
        }), 200
    except Exception as e:
        logger.error(f"Error getting tags: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@knowledge_base_bp.route('/tags', methods=['POST'])
def create_tag():
    """Create tag baru"""
    try:
        data = request.get_json()
        name = data.get('name')
        color = data.get('color', '#007bff')
        
        if not name:
            return jsonify({
                'success': False,
                'message': 'Nama tag wajib diisi'
            }), 400
        
        tag = KnowledgeBaseService.create_tag(name, color)
        return jsonify({
            'success': True,
            'data': tag
        }), 201
    except Exception as e:
        logger.error(f"Error creating tag: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@knowledge_base_bp.route('/files', methods=['GET'])
def get_files():
    """Get file dengan filter dan pagination"""
    try:
        from models.knowledge_base import KnowledgeBaseFile
        from config.database import db
        
        # Debug: Log request parameters
        logger.info(f"📁 GET /files - Query params: {dict(request.args)}")
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Get filters
        filters = {}
        if request.args.get('category_id'):
            filters['category_id'] = int(request.args.get('category_id'))
        if request.args.get('priority_level'):
            filters['priority_level'] = request.args.get('priority_level')
        if request.args.get('is_active') is not None:
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        logger.info(f"🔍 Applied filters: {filters}")
        
        # Build query
        query = KnowledgeBaseFile.query
        
        if filters:
            if filters.get('category_id'):
                query = query.filter(KnowledgeBaseFile.category_id == filters['category_id'])
            if filters.get('priority_level'):
                query = query.filter(KnowledgeBaseFile.priority_level == filters['priority_level'])
            if filters.get('is_active') is not None:
                query = query.filter(KnowledgeBaseFile.is_active == filters['is_active'])
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    db.or_(
                        KnowledgeBaseFile.original_filename.ilike(search_term),
                        KnowledgeBaseFile.description.ilike(search_term)
                    )
                )
        
        # Debug: Count total records before pagination
        total_count = query.count()
        logger.info(f"📊 Total files found: {total_count}")
        
        # Pagination
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Debug: Log pagination results
        logger.info(f"📄 Pagination: page={page}, per_page={per_page}, total={pagination.total}, items={len(pagination.items)}")
        
        result = {
            'files': [file.to_dict() for file in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
        
        logger.info(f"✅ Successfully returned {len(result['files'])} files")
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
    except Exception as e:
        logger.error(f"❌ Error getting files: {str(e)}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error_type': type(e).__name__
        }), 500

@knowledge_base_bp.route('/files', methods=['POST'])
def upload_file():
    """Upload file ke knowledge base"""
    try:
        # Check if file exists
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'File tidak ditemukan'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'File tidak dipilih'
            }), 400
        
        # Get form data
        description = request.form.get('description', '')
        category_id = request.form.get('category_id')
        tags = request.form.get('tags')  # Comma separated tag IDs
        priority_level = request.form.get('priority_level', 'medium')
        created_by = request.form.get('created_by', 1)  # Default to admin
        
        # Parse tags
        tag_ids = None
        if tags:
            try:
                tag_ids = [int(tag_id.strip()) for tag_id in tags.split(',') if tag_id.strip()]
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Format tag tidak valid'
                }), 400
        
        # Parse category_id
        if category_id:
            try:
                category_id = int(category_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'ID kategori tidak valid'
                }), 400
        
        # Parse created_by
        try:
            created_by = int(created_by)
        except ValueError:
            created_by = 1  # Default to admin
        
        # Upload file
        result = KnowledgeBaseService.upload_file(
            file=file,
            description=description,
            category_id=category_id,
            tags=tag_ids,
            priority_level=priority_level,
            created_by=created_by
        )
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'File berhasil diupload'
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return specific error messages
        error_message = str(e)
        if "File tidak valid" in error_message:
            return jsonify({
                'success': False,
                'message': error_message
            }), 400
        elif "Ukuran file terlalu besar" in error_message:
            return jsonify({
                'success': False,
                'message': error_message
            }), 413
        else:
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat upload file. Silakan coba lagi.'
            }), 500

@knowledge_base_bp.route('/files/<int:file_id>', methods=['GET'])
def get_file(file_id):
    """Get file berdasarkan ID"""
    try:
        file_data = KnowledgeBaseService.get_file_by_id(file_id)
        return jsonify({
            'success': True,
            'data': file_data
        }), 200
    except Exception as e:
        logger.error(f"Error getting file: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@knowledge_base_bp.route('/files/<int:file_id>', methods=['PUT'])
def update_file(file_id):
    """Update file"""
    try:
        data = request.get_json()
        
        result = KnowledgeBaseService.update_file(
            file_id=file_id,
            description=data.get('description'),
            category_id=data.get('category_id'),
            tags=data.get('tags'),
            priority_level=data.get('priority_level'),
            is_active=data.get('is_active')
        )
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'File berhasil diupdate'
        }), 200
    except Exception as e:
        logger.error(f"Error updating file: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@knowledge_base_bp.route('/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete file"""
    try:
        KnowledgeBaseService.delete_file(file_id)
        return jsonify({
            'success': True,
            'message': 'File berhasil dihapus'
        }), 200
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@knowledge_base_bp.route('/files/<int:file_id>/versions', methods=['GET'])
def get_file_versions(file_id):
    """Get version history file"""
    try:
        versions = KnowledgeBaseService.get_file_versions(file_id)
        return jsonify({
            'success': True,
            'data': versions
        }), 200
    except Exception as e:
        logger.error(f"Error getting file versions: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@knowledge_base_bp.route('/agent/files', methods=['GET'])
def get_files_for_agent():
    """Get file aktif untuk agent AI"""
    try:
        files = KnowledgeBaseService.get_active_files_for_agent()
        return jsonify({
            'success': True,
            'data': files
        }), 200
    except Exception as e:
        logger.error(f"Error getting files for agent: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@knowledge_base_bp.route('/files/<int:file_id>/access', methods=['POST'])
def set_file_access(file_id):
    """Set akses user ke file"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        can_upload = data.get('can_upload', False)
        can_edit = data.get('can_edit', False)
        can_delete = data.get('can_delete', False)
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID wajib diisi'
            }), 400
        
        result = KnowledgeBaseService.set_user_access(
            user_id=user_id,
            file_id=file_id,
            can_upload=can_upload,
            can_edit=can_edit,
            can_delete=can_delete
        )
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Akses berhasil diset'
        }), 200
    except Exception as e:
        logger.error(f"Error setting file access: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@knowledge_base_bp.route('/files/<int:file_id>/download', methods=['GET'])
def download_file(file_id):
    """Download file (return base64 content)"""
    try:
        file_data = KnowledgeBaseService.get_file_by_id(file_id)
        return jsonify({
            'success': True,
            'data': {
                'filename': file_data['original_filename'],
                'base64_content': file_data['base64_content']
            }
        }), 200
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@knowledge_base_bp.route('/debug/database-status', methods=['GET'])
def debug_database_status():
    """Debug endpoint untuk cek status database"""
    try:
        from models.knowledge_base import KnowledgeBaseFile, KnowledgeCategory, KnowledgeTag
        from config.database import db
        from datetime import datetime
        
        # Test database connection
        db_status = "connected"
        db_error = None
        try:
            # Test basic query
            db.session.execute(db.text("SELECT 1"))
        except Exception as e:
            db_status = "error"
            db_error = str(e)
        
        # Count records in each table
        counts = {}
        try:
            counts['knowledge_base_files'] = KnowledgeBaseFile.query.count()
            counts['knowledge_categories'] = KnowledgeCategory.query.count()
            counts['knowledge_tags'] = KnowledgeTag.query.count()
        except Exception as e:
            counts['error'] = str(e)
        
        # Get sample data
        sample_files = []
        try:
            sample_files = [file.to_dict() for file in KnowledgeBaseFile.query.limit(3).all()]
        except Exception as e:
            sample_files = [{'error': str(e)}]
        
        return jsonify({
            'success': True,
            'data': {
                'database_status': db_status,
                'database_error': db_error,
                'table_counts': counts,
                'sample_files': sample_files,
                'timestamp': datetime.now().isoformat(),
                'database_uri': current_app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')
            }
        }), 200
    except Exception as e:
        logger.error(f"Debug database status error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error_type': type(e).__name__
        }), 500

@knowledge_base_bp.route('/debug/raw-files', methods=['GET'])
def debug_raw_files():
    """Debug endpoint untuk melihat data mentah dari database"""
    try:
        from models.knowledge_base import KnowledgeBaseFile
        from config.database import db
        
        # Get raw SQL query results
        raw_files = db.session.execute(
            db.text("SELECT id, filename, original_filename, description, file_size, upload_date, category_id, priority_level, is_active FROM knowledge_base_files LIMIT 10")
        ).fetchall()
        
        # Convert to list of dicts
        files_data = []
        for row in raw_files:
            files_data.append({
                'id': row[0],
                'filename': row[1],
                'original_filename': row[2],
                'description': row[3],
                'file_size': row[4],
                'upload_date': row[5].isoformat() if row[5] else None,
                'category_id': row[6],
                'priority_level': row[7],
                'is_active': bool(row[8])
            })
        
        return jsonify({
            'success': True,
            'data': {
                'raw_files': files_data,
                'total_raw_count': len(files_data),
                'timestamp': datetime.now().isoformat()
            }
        }), 200
    except Exception as e:
        logger.error(f"Debug raw files error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error_type': type(e).__name__
        }), 500

@knowledge_base_bp.route('/debug/create-sample-data', methods=['POST'])
def create_sample_data():
    """Endpoint untuk membuat data sample"""
    try:
        from models.knowledge_base import KnowledgeCategory, KnowledgeTag, KnowledgeBaseFile
        from config.database import db
        import base64
        
        # Check if data already exists
        existing_files = KnowledgeBaseFile.query.count()
        if existing_files > 0:
            return jsonify({
                'success': False,
                'message': f'Database sudah memiliki {existing_files} file. Hapus data existing terlebih dahulu jika ingin membuat sample data baru.',
                'existing_count': existing_files
            }), 400
        
        # Create sample categories
        categories_data = [
            {'name': 'Dokumen Perusahaan', 'description': 'Dokumen resmi perusahaan dan kebijakan'},
            {'name': 'Manual Teknis', 'description': 'Manual dan dokumentasi teknis'},
            {'name': 'Laporan', 'description': 'Laporan keuangan dan operasional'},
            {'name': 'Template', 'description': 'Template dokumen dan form'}
        ]
        
        created_categories = []
        for cat_data in categories_data:
            category = KnowledgeCategory(
                name=cat_data['name'],
                description=cat_data['description']
            )
            db.session.add(category)
            created_categories.append(category)
        
        db.session.commit()
        
        # Create sample tags
        tags_data = [
            {'name': 'penting', 'color': '#dc3545'},
            {'name': 'draft', 'color': '#ffc107'},
            {'name': 'final', 'color': '#28a745'},
            {'name': 'internal', 'color': '#17a2b8'},
            {'name': 'public', 'color': '#6f42c1'},
            {'name': 'confidential', 'color': '#fd7e14'}
        ]
        
        created_tags = []
        for tag_data in tags_data:
            tag = KnowledgeTag(
                name=tag_data['name'],
                color=tag_data['color']
            )
            db.session.add(tag)
            created_tags.append(tag)
        
        db.session.commit()
        
        # Create sample files
        sample_content = base64.b64encode(b"Sample document content for testing purposes").decode('utf-8')
        
        files_data = [
            {
                'filename': 'sample_document_1.pdf',
                'original_filename': 'Kebijakan Perusahaan 2024.pdf',
                'description': 'Dokumen kebijakan perusahaan untuk tahun 2024',
                'file_size': 1024000,
                'category_id': created_categories[0].id,
                'priority_level': 'high',
                'tag_indices': [0, 2]  # penting, final
            },
            {
                'filename': 'sample_document_2.pdf',
                'original_filename': 'Manual Penggunaan Sistem.pdf',
                'description': 'Manual lengkap penggunaan sistem internal',
                'file_size': 2048000,
                'category_id': created_categories[1].id,
                'priority_level': 'medium',
                'tag_indices': [1, 3]  # draft, internal
            },
            {
                'filename': 'sample_document_3.pdf',
                'original_filename': 'Laporan Keuangan Q1 2024.pdf',
                'description': 'Laporan keuangan kuartal pertama tahun 2024',
                'file_size': 1536000,
                'category_id': created_categories[2].id,
                'priority_level': 'high',
                'tag_indices': [0, 5]  # penting, confidential
            },
            {
                'filename': 'sample_document_4.pdf',
                'original_filename': 'Template Surat Resmi.docx',
                'description': 'Template surat resmi perusahaan',
                'file_size': 512000,
                'category_id': created_categories[3].id,
                'priority_level': 'low',
                'tag_indices': [2, 4]  # final, public
            },
            {
                'filename': 'sample_document_5.pdf',
                'original_filename': 'Prosedur Standar Operasi.pdf',
                'description': 'Prosedur standar operasi untuk departemen',
                'file_size': 768000,
                'category_id': created_categories[1].id,
                'priority_level': 'medium',
                'tag_indices': [1, 3]  # draft, internal
            }
        ]
        
        created_files = []
        for file_data in files_data:
            file_obj = KnowledgeBaseFile(
                filename=file_data['filename'],
                original_filename=file_data['original_filename'],
                description=file_data['description'],
                file_size=file_data['file_size'],
                base64_content=sample_content,
                category_id=file_data['category_id'],
                priority_level=file_data['priority_level'],
                is_active=True,
                created_by=1
            )
            
            # Add tags
            for tag_idx in file_data['tag_indices']:
                if tag_idx < len(created_tags):
                    file_obj.tags.append(created_tags[tag_idx])
            
            db.session.add(file_obj)
            created_files.append(file_obj)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Sample data berhasil dibuat',
            'data': {
                'categories_created': len(created_categories),
                'tags_created': len(created_tags),
                'files_created': len(created_files),
                'timestamp': datetime.now().isoformat()
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating sample data: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e),
            'error_type': type(e).__name__
        }), 500

@knowledge_base_bp.route('/debug/create-rag-sample-data', methods=['POST'])
def create_rag_sample_data():
    """Endpoint untuk membuat sample data RAG"""
    try:
        import requests
        import base64
        import json
        
        # Sample PDF content (base64 encoded)
        sample_pdf_content = base64.b64encode(b"""
        %PDF-1.4
        1 0 obj
        <<
        /Type /Catalog
        /Pages 2 0 R
        >>
        endobj
        
        2 0 obj
        <<
        /Type /Pages
        /Kids [3 0 R]
        /Count 1
        >>
        endobj
        
        3 0 obj
        <<
        /Type /Page
        /Parent 2 0 R
        /MediaBox [0 0 612 792]
        /Contents 4 0 R
        >>
        endobj
        
        4 0 obj
        <<
        /Length 44
        >>
        stream
        BT
        /F1 12 Tf
        100 700 Td
        (Sample RAG Document) Tj
        ET
        endstream
        endobj
        
        xref
        0 5
        0000000000 65535 f 
        0000000009 00000 n 
        0000000058 00000 n 
        0000000115 00000 n 
        0000000204 00000 n 
        trailer
        <<
        /Size 5
        /Root 1 0 R
        >>
        startxref
        297
        %%EOF
        """).decode('utf-8')
        
        # Sample documents untuk RAG
        sample_documents = [
            {
                'filename': 'Kebijakan Perusahaan 2024.pdf',
                'title': 'Kebijakan Perusahaan 2024',
                'description': 'Dokumen kebijakan perusahaan untuk tahun 2024',
                'company_id': 'PT. Kian Santang Muliatama'
            },
            {
                'filename': 'Manual Penggunaan Sistem.pdf',
                'title': 'Manual Penggunaan Sistem',
                'description': 'Manual lengkap penggunaan sistem internal',
                'company_id': 'PT. Kian Santang Muliatama'
            },
            {
                'filename': 'Laporan Keuangan Q1 2024.pdf',
                'title': 'Laporan Keuangan Q1 2024',
                'description': 'Laporan keuangan kuartal pertama tahun 2024',
                'company_id': 'PT. Kian Santang Muliatama'
            },
            {
                'filename': 'Prosedur Standar Operasi.pdf',
                'title': 'Prosedur Standar Operasi',
                'description': 'Prosedur standar operasi untuk departemen',
                'company_id': 'PT. Kian Santang Muliatama'
            },
            {
                'filename': 'Template Surat Resmi.pdf',
                'title': 'Template Surat Resmi',
                'description': 'Template surat resmi perusahaan',
                'company_id': 'PT. Kian Santang Muliatama'
            }
        ]
        
        # Agent AI URL - use environment variable
        base_agent_ai_url = os.getenv('AGENT_AI_URL', 'http://localhost:5000')
        agent_ai_url = f'{base_agent_ai_url}/rag/ingest/pdf-base64'
        
        created_documents = []
        failed_documents = []
        
        for doc_data in sample_documents:
            try:
                # Prepare payload untuk Agent AI
                payload = {
                    'company_id': doc_data['company_id'],
                    'client_id': 'KSM_main',
                    'pdf_base64': f"data:application/pdf;base64,{sample_pdf_content}",
                    'metadata': {
                        'title': doc_data['title'],
                        'description': doc_data['description'],
                        'source': 'KSM_main_sample_data',
                        'filename': doc_data['filename'],
                        'company_id': doc_data['company_id']  # Pastikan company_id ada di metadata
                    }
                }
                
                # Log payload untuk debugging
                logger.info(f"📤 Sending RAG request for {doc_data['filename']} to {agent_ai_url}")
                logger.info(f"Payload keys: {list(payload.keys())}")
                logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
                
                # Send request ke Agent AI
                response = requests.post(
                    agent_ai_url,
                    headers={'Content-Type': 'application/json'},
                    json=payload,
                    timeout=30
                )
                
                logger.info(f"📥 Received response: {response.status_code} for {doc_data['filename']}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Response keys: {list(result.keys())}")
                    logger.info(f"Response status: {result.get('status')}")
                    logger.info(f"Response success: {result.get('success')}")
                    logger.debug(f"Response body: {json.dumps(result, indent=2)}")
                    # Agent AI menggunakan 'status': 'success' bukan 'success': True
                    if result.get('status') == 'success' or result.get('success'):
                        created_documents.append({
                            'filename': doc_data['filename'],
                            'title': doc_data['title'],
                            'document_id': result.get('data', {}).get('document_id'),
                            'status': 'success'
                        })
                        logger.info(f"✅ Created RAG document: {doc_data['filename']}")
                    else:
                        failed_documents.append({
                            'filename': doc_data['filename'],
                            'error': result.get('message', 'Unknown error')
                        })
                        logger.error(f"❌ Failed to create RAG document: {doc_data['filename']} - {result.get('message')}")
                else:
                    response_text = response.text
                    logger.error(f"❌ HTTP error response: {response_text}")
                    failed_documents.append({
                        'filename': doc_data['filename'],
                        'error': f'HTTP {response.status_code}: {response_text}'
                    })
                    logger.error(f"❌ HTTP error creating RAG document: {doc_data['filename']} - {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                failed_documents.append({
                    'filename': doc_data['filename'],
                    'error': f'Connection error: {str(e)}'
                })
                logger.error(f"❌ Connection error creating RAG document: {doc_data['filename']} - {e}")
            except Exception as e:
                failed_documents.append({
                    'filename': doc_data['filename'],
                    'error': f'Unexpected error: {str(e)}'
                })
                logger.error(f"❌ Unexpected error creating RAG document: {doc_data['filename']} - {e}")
        
        # Return response
        return jsonify({
            'success': True,
            'message': f'RAG sample data creation completed. {len(created_documents)} successful, {len(failed_documents)} failed.',
            'data': {
                'created_documents': created_documents,
                'failed_documents': failed_documents,
                'total_attempted': len(sample_documents),
                'successful_count': len(created_documents),
                'failed_count': len(failed_documents),
                'timestamp': datetime.now().isoformat()
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating RAG sample data: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error_type': type(e).__name__
        }), 500

@knowledge_base_bp.route('/debug/test-agent-ai-connection', methods=['GET'])
def test_agent_ai_connection():
    """Endpoint untuk test koneksi ke Agent AI"""
    try:
        import requests
        
        # Test basic connection
        agent_ai_health_url = 'http://localhost:5000/api/health'
        agent_ai_rag_url = 'http://localhost:5000/rag/documents?company_id=PT. Kian Santang Muliatama'
        
        results = {
            'health_check': None,
            'rag_documents': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Test health endpoint
        try:
            response = requests.get(agent_ai_health_url, timeout=10)
            if response.status_code == 200:
                response_data = response.json()
                # Agent AI menggunakan 'status': 'success' atau 'success': True
                success = response_data.get('status') == 'success' or response_data.get('success', False)
            else:
                success = False
                response_data = response.text
            
            results['health_check'] = {
                'status_code': response.status_code,
                'success': success,
                'response': response_data
            }
        except Exception as e:
            results['health_check'] = {
                'status_code': None,
                'success': False,
                'error': str(e)
            }
        
        # Test RAG documents endpoint
        try:
            response = requests.get(agent_ai_rag_url, timeout=10)
            if response.status_code == 200:
                response_data = response.json()
                # Agent AI menggunakan 'status': 'success' atau 'success': True
                success = response_data.get('status') == 'success' or response_data.get('success', False)
            else:
                success = False
                response_data = response.text
            
            results['rag_documents'] = {
                'status_code': response.status_code,
                'success': success,
                'response': response_data
            }
        except Exception as e:
            results['rag_documents'] = {
                'status_code': None,
                'success': False,
                'error': str(e)
            }
        
        # Overall status
        overall_success = results['health_check']['success'] and results['rag_documents']['success']
        
        return jsonify({
            'success': overall_success,
            'message': 'Agent AI connection test completed',
            'data': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing Agent AI connection: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error_type': type(e).__name__
        }), 500

@knowledge_base_bp.route('/debug/check-rag-documents', methods=['GET'])
def check_rag_documents():
    """Endpoint untuk debug RAG documents di Agent AI"""
    try:
        import requests
        import json
        
        # Test RAG documents endpoint
        agent_ai_rag_url = 'http://localhost:5000/rag/documents?company_id=PT. Kian Santang Muliatama'
        
        try:
            response = requests.get(agent_ai_rag_url, timeout=10)
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"RAG documents response: {json.dumps(response_data, indent=2)}")
                
                return jsonify({
                    'success': True,
                    'message': 'RAG documents retrieved successfully',
                    'data': {
                        'status_code': response.status_code,
                        'response': response_data,
                        'timestamp': datetime.now().isoformat()
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': f'HTTP {response.status_code}: {response.text}',
                    'data': {
                        'status_code': response.status_code,
                        'response': response.text,
                        'timestamp': datetime.now().isoformat()
                    }
                }), 500
                
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'message': f'Connection error: {str(e)}',
                'data': {
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            }), 500
        
    except Exception as e:
        logger.error(f"Error checking RAG documents: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error_type': type(e).__name__
        }), 500