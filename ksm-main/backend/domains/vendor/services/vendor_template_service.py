#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Template Service - Business Logic untuk Sistem Vendor Template Management
Service untuk mengelola template download untuk vendor
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class VendorTemplateService:
    """Service untuk mengelola vendor templates"""
    
    def __init__(self, db: Session):
        self.db = db
        self.template_base_path = os.path.join(os.getcwd(), 'templates', 'vendor')
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """Mendapatkan semua template yang tersedia"""
        try:
            # Get templates from database
            from models import VendorTemplate
            templates = self.db.query(VendorTemplate).filter(
                VendorTemplate.is_active == True
            ).order_by(VendorTemplate.category, VendorTemplate.name).all()
            
            template_list = []
            for template in templates:
                template_data = template.to_dict()
                
                # Check if file exists
                file_path = os.path.join(self.template_base_path, template.file_path)
                template_data['file_exists'] = os.path.exists(file_path)
                template_data['file_size'] = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                
                template_list.append(template_data)
            
            logger.info(f"✅ Retrieved {len(template_list)} templates")
            return template_list
            
        except Exception as e:
            logger.error(f"❌ Error getting templates: {str(e)}")
            return []
    
    def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Mendapatkan template berdasarkan kategori"""
        try:
            from models import VendorTemplate
            templates = self.db.query(VendorTemplate).filter(
                VendorTemplate.category == category,
                VendorTemplate.is_active == True
            ).order_by(VendorTemplate.name).all()
            
            template_list = []
            for template in templates:
                template_data = template.to_dict()
                
                # Check if file exists
                file_path = os.path.join(self.template_base_path, template.file_path)
                template_data['file_exists'] = os.path.exists(file_path)
                template_data['file_size'] = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                
                template_list.append(template_data)
            
            logger.info(f"✅ Retrieved {len(template_list)} templates for category: {category}")
            return template_list
            
        except Exception as e:
            logger.error(f"❌ Error getting templates by category: {str(e)}")
            return []
    
    def get_template_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Mendapatkan template berdasarkan ID"""
        try:
            from models import VendorTemplate
            template = self.db.query(VendorTemplate).filter(
                VendorTemplate.id == template_id,
                VendorTemplate.is_active == True
            ).first()
            
            if not template:
                return None
            
            template_data = template.to_dict()
            
            # Check if file exists
            file_path = os.path.join(self.template_base_path, template.file_path)
            template_data['file_exists'] = os.path.exists(file_path)
            template_data['file_size'] = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            template_data['full_file_path'] = file_path
            
            return template_data
            
        except Exception as e:
            logger.error(f"❌ Error getting template by ID: {str(e)}")
            return None
    
    def download_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Download template dan update download count"""
        try:
            from models import VendorTemplate
            template = self.db.query(VendorTemplate).filter(
                VendorTemplate.id == template_id,
                VendorTemplate.is_active == True
            ).first()
            
            if not template:
                return None
            
            # Check if file exists
            file_path = os.path.join(self.template_base_path, template.file_path)
            if not os.path.exists(file_path):
                logger.error(f"❌ Template file not found: {file_path}")
                return None
            
            # Update download count
            template.download_count += 1
            self.db.commit()
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(template.file_path)
            
            logger.info(f"✅ Template downloaded: {template.name} (ID: {template_id})")
            
            return {
                'template': template.to_dict(),
                'file_path': file_path,
                'file_name': file_name,
                'file_size': file_size,
                'mime_type': self._get_mime_type(template.file_type)
            }
            
        except Exception as e:
            logger.error(f"❌ Error downloading template: {str(e)}")
            return None
    
    def get_template_categories(self) -> List[Dict[str, Any]]:
        """Mendapatkan daftar kategori template"""
        try:
            from models import VendorTemplate
            categories = self.db.query(VendorTemplate.category).filter(
                VendorTemplate.is_active == True
            ).distinct().all()
            
            category_list = []
            for category in categories:
                category_name = category[0]
                count = self.db.query(VendorTemplate).filter(
                    VendorTemplate.category == category_name,
                    VendorTemplate.is_active == True
                ).count()
                
                category_list.append({
                    'name': category_name,
                    'display_name': self._get_category_display_name(category_name),
                    'count': count,
                    'description': self._get_category_description(category_name)
                })
            
            logger.info(f"✅ Retrieved {len(category_list)} template categories")
            return category_list
            
        except Exception as e:
            logger.error(f"❌ Error getting template categories: {str(e)}")
            return []
    
    def _get_mime_type(self, file_type: str) -> str:
        """Mendapatkan MIME type berdasarkan file type"""
        mime_types = {
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'pdf': 'application/pdf',
            'word': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return mime_types.get(file_type, 'application/octet-stream')
    
    def _get_category_display_name(self, category: str) -> str:
        """Mendapatkan display name untuk kategori"""
        display_names = {
            'proposal': 'Template Proposal',
            'company_profile': 'Company Profile',
            'technical_spec': 'Spesifikasi Teknis',
            'cover_letter': 'Surat Penawaran',
            'checklist': 'Checklist Persyaratan'
        }
        return display_names.get(category, category.title())
    
    def _get_category_description(self, category: str) -> str:
        """Mendapatkan deskripsi untuk kategori"""
        descriptions = {
            'proposal': 'Template untuk membuat proposal penawaran dengan breakdown harga dan spesifikasi',
            'company_profile': 'Template untuk company profile dan informasi perusahaan',
            'technical_spec': 'Template untuk spesifikasi teknis produk atau layanan',
            'cover_letter': 'Template untuk surat penawaran formal',
            'checklist': 'Checklist persyaratan dan dokumen yang diperlukan'
        }
        return descriptions.get(category, 'Template dokumen')
    
    def get_template_file_path(self, template) -> Optional[str]:
        """Mendapatkan path file template"""
        try:
            if isinstance(template, dict):
                file_path = template.get('file_path')
            else:
                file_path = template.file_path
            
            if not file_path:
                return None
            
            full_path = os.path.join(self.template_base_path, file_path)
            
            if os.path.exists(full_path):
                return full_path
            else:
                logger.error(f"❌ Template file not found: {full_path}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting template file path: {str(e)}")
            return None
    
    def create_default_templates(self) -> bool:
        """Membuat template default jika belum ada"""
        try:
            from models import VendorTemplate
            
            # Check if templates already exist
            existing_count = self.db.query(VendorTemplate).count()
            if existing_count > 0:
                logger.info("✅ Templates already exist, skipping creation")
                return True
            
            # Create default templates
            default_templates = [
                {
                    'name': 'Template Proposal Excel',
                    'description': 'Template untuk breakdown harga dan spesifikasi teknis',
                    'file_path': 'proposal_template.xlsx',
                    'file_type': 'excel',
                    'category': 'proposal'
                },
                {
                    'name': 'Company Profile Template',
                    'description': 'Template untuk company profile',
                    'file_path': 'company_profile.pdf',
                    'file_type': 'pdf',
                    'category': 'company_profile'
                },
                {
                    'name': 'Technical Specification Template',
                    'description': 'Template untuk spesifikasi teknis',
                    'file_path': 'technical_spec.docx',
                    'file_type': 'word',
                    'category': 'technical_spec'
                },
                {
                    'name': 'Cover Letter Template',
                    'description': 'Template untuk surat penawaran',
                    'file_path': 'cover_letter.docx',
                    'file_type': 'word',
                    'category': 'cover_letter'
                },
                {
                    'name': 'Requirements Checklist',
                    'description': 'Checklist persyaratan penawaran',
                    'file_path': 'requirements_checklist.pdf',
                    'file_type': 'pdf',
                    'category': 'checklist'
                }
            ]
            
            for template_data in default_templates:
                template = VendorTemplate(**template_data)
                self.db.add(template)
            
            self.db.commit()
            logger.info(f"✅ Created {len(default_templates)} default templates")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating default templates: {str(e)}")
            return False
