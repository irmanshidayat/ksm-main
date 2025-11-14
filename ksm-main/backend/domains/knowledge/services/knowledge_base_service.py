#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Base Service untuk KSM Main Backend
"""

import os
import io
import base64
import PyPDF2
from datetime import datetime
from werkzeug.utils import secure_filename
from config.database import db
from domains.knowledge.models import (
    KnowledgeCategory, KnowledgeTag, KnowledgeBaseFile, 
    FileVersion, UserFileAccess
)
from flask import current_app

class KnowledgeBaseService:
    """Service untuk mengelola knowledge base"""
    
    ALLOWED_EXTENSIONS = {'pdf'}
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    
    @staticmethod
    def allowed_file(filename):
        """Check apakah file diizinkan"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in KnowledgeBaseService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file_size(file_size):
        """Validasi ukuran file"""
        return file_size <= KnowledgeBaseService.MAX_FILE_SIZE
    
    @staticmethod
    def convert_to_base64(file_path):
        """Konversi file ke base64"""
        try:
            with open(file_path, 'rb') as file:
                file_content = file.read()
                return base64.b64encode(file_content).decode('utf-8')
        except Exception as e:
            raise Exception(f"Error converting file to base64: {str(e)}")
    
    @staticmethod
    def extract_pdf_text(base64_content):
        """Extract text dari PDF untuk search dengan multiple methods untuk memastikan ekstraksi maksimal"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Decode base64
            pdf_content = base64.b64decode(base64_content)
            logger.info(f"Decoded PDF size: {len(pdf_content)} bytes")
            
            extracted_text = ""
            
            # Method 1: Try pdfplumber (most reliable for complex PDFs)
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                    text = ""
                    total_pages = len(pdf.pages)
                    logger.info(f"pdfplumber: Processing {total_pages} pages")
                    
                    for page_num, page in enumerate(pdf.pages, 1):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text += f"\n--- HALAMAN {page_num} ---\n"
                                text += page_text + "\n"
                                logger.info(f"pdfplumber: Page {page_num} extracted {len(page_text)} characters")
                            else:
                                logger.warning(f"pdfplumber: Page {page_num} extracted empty text")
                        except Exception as e:
                            logger.error(f"pdfplumber: Error extracting page {page_num}: {e}")
                    
                    if text.strip():
                        extracted_text = text.strip()
                        logger.info(f"pdfplumber: Successfully extracted {len(extracted_text)} total characters from {total_pages} pages")
                        return extracted_text
                    else:
                        logger.warning("pdfplumber: Extracted empty text from all pages")
                        
            except ImportError:
                logger.warning("pdfplumber not installed, trying next method")
            except Exception as e:
                logger.warning(f"pdfplumber failed: {e}")
            
            # Method 2: Try PyMuPDF (fitz) - excellent for text extraction
            try:
                import fitz  # PyMuPDF
                pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
                text = ""
                total_pages = pdf_document.page_count
                logger.info(f"PyMuPDF: Processing {total_pages} pages")
                
                for page_num in range(total_pages):
                    try:
                        page = pdf_document.load_page(page_num)
                        page_text = page.get_text()
                        if page_text:
                            text += f"\n--- HALAMAN {page_num + 1} ---\n"
                            text += page_text + "\n"
                            logger.info(f"PyMuPDF: Page {page_num + 1} extracted {len(page_text)} characters")
                        else:
                            logger.warning(f"PyMuPDF: Page {page_num + 1} extracted empty text")
                    except Exception as e:
                        logger.error(f"PyMuPDF: Error extracting page {page_num + 1}: {e}")
                
                pdf_document.close()
                
                if text.strip():
                    extracted_text = text.strip()
                    logger.info(f"PyMuPDF: Successfully extracted {len(extracted_text)} total characters from {total_pages} pages")
                    return extracted_text
                else:
                    logger.warning("PyMuPDF: Extracted empty text from all pages")
                    
            except ImportError:
                logger.warning("PyMuPDF not installed, trying next method")
            except Exception as e:
                logger.warning(f"PyMuPDF failed: {e}")
            
            # Method 3: Try PyPDF2 (fallback)
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                text = ""
                total_pages = len(pdf_reader.pages)
                logger.info(f"PyPDF2: Processing {total_pages} pages")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- HALAMAN {page_num} ---\n"
                            text += page_text + "\n"
                            logger.info(f"PyPDF2: Page {page_num} extracted {len(page_text)} characters")
                        else:
                            logger.warning(f"PyPDF2: Page {page_num} extracted empty text")
                    except Exception as e:
                        logger.error(f"PyPDF2: Error extracting page {page_num}: {e}")
                
                extracted_text = text.strip()
                logger.info(f"PyPDF2: Successfully extracted {len(extracted_text)} total characters from {total_pages} pages")
                
                if extracted_text:
                    return extracted_text
                else:
                    logger.warning("PyPDF2: Extracted empty text from all pages")
                    
            except Exception as e:
                logger.error(f"PyPDF2 failed: {e}")
            
            # If all methods failed
            logger.error("All PDF extraction methods failed")
            return "Error: Tidak dapat mengekstrak teks dari PDF. File mungkin rusak atau terenkripsi."
            
        except Exception as e:
            logger.error(f"Error extracting text from base64: {e}")
            return f"Error extracting text: {str(e)}"
    
    @staticmethod
    def create_category(name, description=None, parent_id=None):
        """Membuat kategori baru"""
        try:
            category = KnowledgeCategory(
                name=name,
                description=description,
                parent_id=parent_id
            )
            db.session.add(category)
            db.session.commit()
            return category.to_dict()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error creating category: {str(e)}")
    
    @staticmethod
    def get_categories():
        """Mengambil semua kategori"""
        try:
            categories = KnowledgeCategory.query.all()
            return [category.to_dict() for category in categories]
        except Exception as e:
            raise Exception(f"Error getting categories: {str(e)}")
    
    @staticmethod
    def create_tag(name, color='#007bff'):
        """Membuat tag baru"""
        try:
            tag = KnowledgeTag(name=name, color=color)
            db.session.add(tag)
            db.session.commit()
            return tag.to_dict()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error creating tag: {str(e)}")
    
    @staticmethod
    def get_tags():
        """Mengambil semua tags"""
        try:
            tags = KnowledgeTag.query.all()
            return [tag.to_dict() for tag in tags]
        except Exception as e:
            raise Exception(f"Error getting tags: {str(e)}")
    
    @staticmethod
    def upload_file(file, description=None, category_id=None, tags=None, 
                   priority_level='medium', created_by=None):
        """Upload file ke knowledge base"""
        temp_path = None
        try:
            # Validasi file
            if not file:
                raise Exception("File tidak ditemukan")
            
            if not file.filename:
                raise Exception("Nama file tidak valid")
            
            if not KnowledgeBaseService.allowed_file(file.filename):
                raise Exception("File tidak valid atau format tidak didukung")
            
            # Baca file content untuk validasi ukuran
            file_content = file.read()
            file.seek(0)  # Reset file pointer
            
            if not KnowledgeBaseService.validate_file_size(len(file_content)):
                raise Exception("Ukuran file terlalu besar (maksimal 20MB)")
            
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            filename = f"{timestamp}_{original_filename}"
            
            # Create temp directory if not exists
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save file temporarily
            temp_path = os.path.join(temp_dir, filename)
            file.save(temp_path)
            
            # Convert to base64
            base64_content = KnowledgeBaseService.convert_to_base64(temp_path)
            
            # Calculate file size from base64
            file_size = len(base64.b64decode(base64_content))
            
            # Create file record
            knowledge_file = KnowledgeBaseFile(
                filename=filename,
                original_filename=original_filename,
                description=description,
                file_size=file_size,
                base64_content=base64_content,
                category_id=category_id,
                priority_level=priority_level,
                created_by=created_by
            )
            
            # Add tags if provided
            if tags:
                for tag_id in tags:
                    tag = KnowledgeTag.query.get(tag_id)
                    if tag:
                        knowledge_file.tags.append(tag)
            
            db.session.add(knowledge_file)
            db.session.commit()
            
            # Create initial version
            version = FileVersion(
                file_id=knowledge_file.id,
                version_number=1,
                filename=filename,
                base64_content=base64_content,
                file_size=file_size,
                change_description="Initial upload",
                created_by=created_by
            )
            db.session.add(version)
            db.session.commit()
            
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            
            return knowledge_file.to_dict()
            
        except Exception as e:
            db.session.rollback()
            # Clean up temp file if exists
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            raise Exception(f"Error uploading file: {str(e)}")
    
    @staticmethod
    def get_files(filters=None, page=1, per_page=10):
        """Mengambil file dengan filter dan pagination"""
        try:
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
            
            # Pagination
            pagination = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            return {
                'files': [file.to_dict() for file in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page
            }
            
        except Exception as e:
            raise Exception(f"Error getting files: {str(e)}")
    
    @staticmethod
    def get_file_by_id(file_id):
        """Mengambil file berdasarkan ID"""
        try:
            file = KnowledgeBaseFile.query.get(file_id)
            if not file:
                raise Exception("File tidak ditemukan")
            return file.to_dict()
        except Exception as e:
            raise Exception(f"Error getting file: {str(e)}")
    
    @staticmethod
    def update_file(file_id, description=None, category_id=None, tags=None, 
                   priority_level=None, is_active=None):
        """Update file"""
        try:
            file = KnowledgeBaseFile.query.get(file_id)
            if not file:
                raise Exception("File tidak ditemukan")
            
            if description is not None:
                file.description = description
            if category_id is not None:
                file.category_id = category_id
            if priority_level is not None:
                file.priority_level = priority_level
            if is_active is not None:
                file.is_active = is_active
            
            # Update tags
            if tags is not None:
                file.tags.clear()
                for tag_id in tags:
                    tag = KnowledgeTag.query.get(tag_id)
                    if tag:
                        file.tags.append(tag)
            
            db.session.commit()
            return file.to_dict()
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error updating file: {str(e)}")
    
    @staticmethod
    def delete_file(file_id):
        """Delete file"""
        try:
            file = KnowledgeBaseFile.query.get(file_id)
            if not file:
                raise Exception("File tidak ditemukan")
            
            db.session.delete(file)
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error deleting file: {str(e)}")
    
    @staticmethod
    def get_file_versions(file_id):
        """Mengambil version history file"""
        try:
            versions = FileVersion.query.filter_by(file_id=file_id).order_by(FileVersion.version_number.desc()).all()
            return [version.to_dict() for version in versions]
        except Exception as e:
            raise Exception(f"Error getting file versions: {str(e)}")
    
    @staticmethod
    def get_active_files_for_agent():
        """Mengambil file aktif untuk agent AI"""
        try:
            files = KnowledgeBaseFile.query.filter_by(is_active=True).all()
            return [{
                'id': file.id,
                'filename': file.original_filename,
                'description': file.description,
                'base64_content': file.base64_content,
                'category': file.category.name if file.category else None,
                'priority_level': file.priority_level,
                'tags': [tag.name for tag in file.tags]
            } for file in files]
        except Exception as e:
            raise Exception(f"Error getting active files for agent: {str(e)}")
    
    @staticmethod
    def set_user_access(user_id, file_id, can_upload=False, can_edit=False, can_delete=False):
        """Set akses user ke file"""
        try:
            access = UserFileAccess.query.filter_by(user_id=user_id, file_id=file_id).first()
            
            if access:
                access.can_upload = can_upload
                access.can_edit = can_edit
                access.can_delete = can_delete
            else:
                access = UserFileAccess(
                    user_id=user_id,
                    file_id=file_id,
                    can_upload=can_upload,
                    can_edit=can_edit,
                    can_delete=can_delete
                )
                db.session.add(access)
            
            db.session.commit()
            return access.to_dict()
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error setting user access: {str(e)}")
    
    @staticmethod
    def check_user_access(user_id, file_id, action):
        """Check apakah user punya akses untuk action tertentu"""
        try:
            access = UserFileAccess.query.filter_by(user_id=user_id, file_id=file_id).first()
            
            if not access:
                return False
            
            if action == 'upload':
                return access.can_upload
            elif action == 'edit':
                return access.can_edit
            elif action == 'delete':
                return access.can_delete
            
            return False
            
        except Exception as e:
            return False
