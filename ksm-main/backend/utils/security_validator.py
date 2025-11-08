#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security Validator - Advanced file validation and security checks
"""

import os
import hashlib
import logging
from typing import Dict, List, Tuple, Optional
from werkzeug.utils import secure_filename
import mimetypes
import re

# Try to import magic, fallback to mimetypes if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("Warning: python-magic not available, using mimetypes fallback")

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Advanced security validator for file uploads"""
    
    # Allowed file types with MIME types
    ALLOWED_TYPES = {
        'documents': {
            'pdf': ['application/pdf'],
            'doc': ['application/msword'],
            'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'xls': ['application/vnd.ms-excel'],
            'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
            'txt': ['text/plain'],
        },
        'images': {
            'jpg': ['image/jpeg'],
            'jpeg': ['image/jpeg'],
            'png': ['image/png'],
            'gif': ['image/gif'],
            'bmp': ['image/bmp'],
            'webp': ['image/webp'],
        },
        'archives': {
            'zip': ['application/zip'],
            'rar': ['application/x-rar-compressed'],
            '7z': ['application/x-7z-compressed'],
        }
    }
    
    # File size limits by user role (in bytes)
    SIZE_LIMITS = {
        'vendor': 10 * 1024 * 1024,  # 10MB
        'admin': 50 * 1024 * 1024,   # 50MB
        'super_admin': 100 * 1024 * 1024,  # 100MB
    }
    
    # Maximum files per upload
    MAX_FILES = {
        'vendor': 5,
        'admin': 10,
        'super_admin': 20,
    }
    
    # Dangerous file patterns
    DANGEROUS_PATTERNS = [
        r'\.exe$', r'\.bat$', r'\.cmd$', r'\.scr$', r'\.pif$',
        r'\.com$', r'\.vbs$', r'\.js$', r'\.jar$', r'\.app$',
        r'\.deb$', r'\.rpm$', r'\.dmg$', r'\.iso$', r'\.img$'
    ]
    
    # Suspicious content patterns
    SUSPICIOUS_PATTERNS = [
        b'<script', b'javascript:', b'vbscript:', b'onload=',
        b'onerror=', b'eval(', b'exec(', b'system(',
        b'cmd.exe', b'powershell', b'bash', b'sh'
    ]

    def __init__(self):
        if MAGIC_AVAILABLE:
            self.mime_detector = magic.Magic(mime=True)
        else:
            self.mime_detector = None
    
    def validate_file(self, file, user_role: str = 'vendor', file_data: Dict = None) -> Tuple[bool, str, Dict]:
        """
        Comprehensive file validation
        
        Returns:
            (is_valid, error_message, validation_info)
        """
        try:
            validation_info = {
                'original_name': file.filename,
                'secure_name': secure_filename(file.filename),
                'file_size': 0,
                'mime_type': None,
                'file_hash': None,
                'validation_checks': []
            }
            
            # Reset file pointer
            file.seek(0)
            file_content = file.read()
            file.seek(0)
            
            validation_info['file_size'] = len(file_content)
            validation_info['file_hash'] = hashlib.sha256(file_content).hexdigest()
            
            # Check 1: File name validation
            if not self._validate_filename(file.filename):
                return False, "Nama file tidak valid atau mengandung karakter berbahaya", validation_info
            
            validation_info['validation_checks'].append('filename_valid')
            
            # Check 2: File size validation
            if not self._validate_file_size(len(file_content), user_role):
                return False, f"Ukuran file melebihi batas yang diizinkan untuk role {user_role}", validation_info
            
            validation_info['validation_checks'].append('size_valid')
            
            # Check 3: File extension validation
            if not self._validate_extension(file.filename):
                return False, "Ekstensi file tidak diizinkan", validation_info
            
            validation_info['validation_checks'].append('extension_valid')
            
            # Check 4: MIME type validation
            mime_type = self._get_mime_type(file_content, file.filename)
            validation_info['mime_type'] = mime_type
            
            if not self._validate_mime_type(mime_type, file.filename):
                return False, f"Tipe file tidak valid. Ditemukan: {mime_type}", validation_info
            
            validation_info['validation_checks'].append('mime_type_valid')
            
            # Check 5: Content validation
            if not self._validate_content(file_content, mime_type):
                return False, "Konten file mengandung data yang mencurigakan", validation_info
            
            validation_info['validation_checks'].append('content_valid')
            
            # Check 6: Virus scanning (if available)
            if not self._scan_for_viruses(file_content):
                return False, "File terdeteksi sebagai malware atau virus", validation_info
            
            validation_info['validation_checks'].append('virus_scan_passed')
            
            logger.info(f"✅ File validation passed: {file.filename} ({mime_type}, {len(file_content)} bytes)")
            return True, "File valid", validation_info
            
        except Exception as e:
            logger.error(f"❌ File validation error: {str(e)}")
            return False, f"Error validasi file: {str(e)}", validation_info
    
    def _validate_filename(self, filename: str) -> bool:
        """Validate filename for security"""
        if not filename or len(filename) > 255:
            return False
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, filename.lower()):
                return False
        
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for null bytes
        if '\x00' in filename:
            return False
        
        return True
    
    def _validate_file_size(self, size: int, user_role: str) -> bool:
        """Validate file size based on user role"""
        max_size = self.SIZE_LIMITS.get(user_role, self.SIZE_LIMITS['vendor'])
        return size <= max_size
    
    def _validate_extension(self, filename: str) -> bool:
        """Validate file extension"""
        if not filename:
            return False
        
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # Check if extension is in allowed types
        for category in self.ALLOWED_TYPES.values():
            if ext in category:
                return True
        
        return False
    
    def _get_mime_type(self, content: bytes, filename: str) -> str:
        """Get MIME type using multiple methods"""
        if MAGIC_AVAILABLE and self.mime_detector:
            try:
                # Method 1: python-magic
                mime_type = self.mime_detector.from_buffer(content)
                if mime_type and mime_type != 'application/octet-stream':
                    return mime_type
            except:
                pass
        
        try:
            # Method 2: mimetypes module
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type:
                return mime_type
        except:
            pass
        
        return 'application/octet-stream'
    
    def _validate_mime_type(self, mime_type: str, filename: str) -> bool:
        """Validate MIME type against allowed types"""
        if not mime_type:
            return False
        
        # Get expected MIME types for this file extension
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        expected_mimes = []
        
        for category in self.ALLOWED_TYPES.values():
            if ext in category:
                expected_mimes.extend(category[ext])
        
        # Check if MIME type matches expected types
        return mime_type in expected_mimes
    
    def _validate_content(self, content: bytes, mime_type: str) -> bool:
        """Validate file content for suspicious patterns"""
        # Check for suspicious patterns in content
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern in content.lower():
                logger.warning(f"Suspicious pattern detected: {pattern}")
                return False
        
        # Additional content validation based on MIME type
        if mime_type.startswith('text/'):
            return self._validate_text_content(content)
        elif mime_type.startswith('image/'):
            return self._validate_image_content(content)
        elif mime_type == 'application/pdf':
            return self._validate_pdf_content(content)
        
        return True
    
    def _validate_text_content(self, content: bytes) -> bool:
        """Validate text file content"""
        try:
            # Check if content is valid text
            content.decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False
    
    def _validate_image_content(self, content: bytes) -> bool:
        """Validate image file content"""
        # Check for valid image headers
        image_headers = [
            b'\xff\xd8\xff',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'GIF87a',  # GIF
            b'GIF89a',  # GIF
            b'BM',  # BMP
        ]
        
        for header in image_headers:
            if content.startswith(header):
                return True
        
        return False
    
    def _validate_pdf_content(self, content: bytes) -> bool:
        """Validate PDF file content"""
        # Check for PDF header
        if content.startswith(b'%PDF-'):
            return True
        return False
    
    def _scan_for_viruses(self, content: bytes) -> bool:
        """Basic virus scanning (placeholder for real antivirus integration)"""
        # This is a placeholder for real antivirus integration
        # In production, integrate with ClamAV or similar
        
        # Check for common malware signatures (basic)
        malware_signatures = [
            b'MZ',  # PE executable
            b'\x7fELF',  # ELF executable
        ]
        
        for signature in malware_signatures:
            if content.startswith(signature):
                logger.warning(f"Potential malware signature detected: {signature}")
                return False
        
        return True
    
    def get_upload_limits(self, user_role: str) -> Dict:
        """Get upload limits for user role"""
        return {
            'max_file_size': self.SIZE_LIMITS.get(user_role, self.SIZE_LIMITS['vendor']),
            'max_files': self.MAX_FILES.get(user_role, self.MAX_FILES['vendor']),
            'allowed_extensions': list(self.ALLOWED_TYPES.keys()),
            'allowed_mime_types': self._get_all_mime_types()
        }
    
    def _get_all_mime_types(self) -> List[str]:
        """Get all allowed MIME types"""
        mime_types = []
        for category in self.ALLOWED_TYPES.values():
            for ext_mimes in category.values():
                mime_types.extend(ext_mimes)
        return mime_types

# Export singleton instance
security_validator = SecurityValidator()
