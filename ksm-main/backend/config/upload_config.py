#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload Configuration - Optimized settings for upload system
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class UserRole(Enum):
    VENDOR = "vendor"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

@dataclass
class UploadLimits:
    """Upload limits configuration"""
    max_file_size: int  # in bytes
    max_files_per_upload: int
    max_total_size_per_upload: int  # in bytes
    max_concurrent_uploads: int
    max_uploads_per_hour: int
    max_uploads_per_day: int
    max_total_size_per_hour: int  # in bytes
    max_total_size_per_day: int  # in bytes

@dataclass
class FileTypeConfig:
    """File type configuration"""
    extension: str
    mime_types: List[str]
    max_size: int  # in bytes
    compression_enabled: bool
    compression_quality: float  # 0.0 to 1.0
    virus_scan_required: bool
    preview_supported: bool

@dataclass
class TimelineConfig:
    """Timeline configuration"""
    default_deadline_hours: int
    min_deadline_hours: int
    max_deadline_hours: int
    reminder_hours: List[int]  # Hours before deadline to send reminders
    grace_period_hours: int  # Grace period after deadline
    auto_close_hours: int  # Auto close after this many hours past deadline

class UploadConfiguration:
    """Main upload configuration manager"""
    
    def __init__(self):
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from environment or defaults"""
        
        # Upload limits by user role
        self.upload_limits = {
            UserRole.VENDOR: UploadLimits(
                max_file_size=int(os.getenv('VENDOR_MAX_FILE_SIZE', 10 * 1024 * 1024)),  # 10MB
                max_files_per_upload=int(os.getenv('VENDOR_MAX_FILES', 5)),
                max_total_size_per_upload=int(os.getenv('VENDOR_MAX_TOTAL_SIZE', 50 * 1024 * 1024)),  # 50MB
                max_concurrent_uploads=int(os.getenv('VENDOR_MAX_CONCURRENT', 3)),
                max_uploads_per_hour=int(os.getenv('VENDOR_MAX_HOURLY', 20)),
                max_uploads_per_day=int(os.getenv('VENDOR_MAX_DAILY', 100)),
                max_total_size_per_hour=int(os.getenv('VENDOR_MAX_HOURLY_SIZE', 100 * 1024 * 1024)),  # 100MB
                max_total_size_per_day=int(os.getenv('VENDOR_MAX_DAILY_SIZE', 500 * 1024 * 1024)),  # 500MB
            ),
            UserRole.ADMIN: UploadLimits(
                max_file_size=int(os.getenv('ADMIN_MAX_FILE_SIZE', 50 * 1024 * 1024)),  # 50MB
                max_files_per_upload=int(os.getenv('ADMIN_MAX_FILES', 10)),
                max_total_size_per_upload=int(os.getenv('ADMIN_MAX_TOTAL_SIZE', 200 * 1024 * 1024)),  # 200MB
                max_concurrent_uploads=int(os.getenv('ADMIN_MAX_CONCURRENT', 10)),
                max_uploads_per_hour=int(os.getenv('ADMIN_MAX_HOURLY', 100)),
                max_uploads_per_day=int(os.getenv('ADMIN_MAX_DAILY', 500)),
                max_total_size_per_hour=int(os.getenv('ADMIN_MAX_HOURLY_SIZE', 1000 * 1024 * 1024)),  # 1GB
                max_total_size_per_day=int(os.getenv('ADMIN_MAX_DAILY_SIZE', 5000 * 1024 * 1024)),  # 5GB
            ),
            UserRole.SUPER_ADMIN: UploadLimits(
                max_file_size=int(os.getenv('SUPER_ADMIN_MAX_FILE_SIZE', 100 * 1024 * 1024)),  # 100MB
                max_files_per_upload=int(os.getenv('SUPER_ADMIN_MAX_FILES', 20)),
                max_total_size_per_upload=int(os.getenv('SUPER_ADMIN_MAX_TOTAL_SIZE', 500 * 1024 * 1024)),  # 500MB
                max_concurrent_uploads=int(os.getenv('SUPER_ADMIN_MAX_CONCURRENT', 20)),
                max_uploads_per_hour=int(os.getenv('SUPER_ADMIN_MAX_HOURLY', 500)),
                max_uploads_per_day=int(os.getenv('SUPER_ADMIN_MAX_DAILY', 2000)),
                max_total_size_per_hour=int(os.getenv('SUPER_ADMIN_MAX_HOURLY_SIZE', 5000 * 1024 * 1024)),  # 5GB
                max_total_size_per_day=int(os.getenv('SUPER_ADMIN_MAX_DAILY_SIZE', 25000 * 1024 * 1024)),  # 25GB
            )
        }
        
        # File type configurations
        self.file_types = {
            'pdf': FileTypeConfig(
                extension='pdf',
                mime_types=['application/pdf'],
                max_size=int(os.getenv('PDF_MAX_SIZE', 50 * 1024 * 1024)),  # 50MB
                compression_enabled=False,
                compression_quality=0.8,
                virus_scan_required=True,
                preview_supported=True
            ),
            'documents': FileTypeConfig(
                extension='doc,docx',
                mime_types=[
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                ],
                max_size=int(os.getenv('DOC_MAX_SIZE', 25 * 1024 * 1024)),  # 25MB
                compression_enabled=False,
                compression_quality=0.8,
                virus_scan_required=True,
                preview_supported=False
            ),
            'spreadsheets': FileTypeConfig(
                extension='xls,xlsx',
                mime_types=[
                    'application/vnd.ms-excel',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ],
                max_size=int(os.getenv('XLS_MAX_SIZE', 25 * 1024 * 1024)),  # 25MB
                compression_enabled=False,
                compression_quality=0.8,
                virus_scan_required=True,
                preview_supported=False
            ),
            'images': FileTypeConfig(
                extension='jpg,jpeg,png,gif,bmp,webp',
                mime_types=[
                    'image/jpeg',
                    'image/png',
                    'image/gif',
                    'image/bmp',
                    'image/webp'
                ],
                max_size=int(os.getenv('IMAGE_MAX_SIZE', 10 * 1024 * 1024)),  # 10MB
                compression_enabled=True,
                compression_quality=float(os.getenv('IMAGE_COMPRESSION_QUALITY', 0.8)),
                virus_scan_required=True,
                preview_supported=True
            ),
            'archives': FileTypeConfig(
                extension='zip,rar,7z',
                mime_types=[
                    'application/zip',
                    'application/x-rar-compressed',
                    'application/x-7z-compressed'
                ],
                max_size=int(os.getenv('ARCHIVE_MAX_SIZE', 100 * 1024 * 1024)),  # 100MB
                compression_enabled=False,
                compression_quality=0.8,
                virus_scan_required=True,
                preview_supported=False
            )
        }
        
        # Timeline configuration
        self.timeline = TimelineConfig(
            default_deadline_hours=int(os.getenv('DEFAULT_DEADLINE_HOURS', 72)),  # 3 days
            min_deadline_hours=int(os.getenv('MIN_DEADLINE_HOURS', 24)),  # 1 day
            max_deadline_hours=int(os.getenv('MAX_DEADLINE_HOURS', 720)),  # 30 days
            reminder_hours=[int(x) for x in os.getenv('REMINDER_HOURS', '24,12,2').split(',')],  # 24h, 12h, 2h before
            grace_period_hours=int(os.getenv('GRACE_PERIOD_HOURS', 2)),  # 2 hours grace
            auto_close_hours=int(os.getenv('AUTO_CLOSE_HOURS', 24))  # Auto close after 24h past deadline
        )
        
        # Performance configuration
        self.performance = {
            'chunk_size': int(os.getenv('UPLOAD_CHUNK_SIZE', 1024 * 1024)),  # 1MB chunks
            'max_concurrent_uploads': int(os.getenv('MAX_CONCURRENT_UPLOADS', 5)),
            'connection_timeout': int(os.getenv('CONNECTION_TIMEOUT', 300)),  # 5 minutes
            'retry_attempts': int(os.getenv('RETRY_ATTEMPTS', 3)),
            'retry_delay': int(os.getenv('RETRY_DELAY', 1000)),  # 1 second
            'cleanup_interval': int(os.getenv('CLEANUP_INTERVAL', 3600)),  # 1 hour
        }
        
        # Security configuration
        self.security = {
            'virus_scan_enabled': os.getenv('VIRUS_SCAN_ENABLED', 'true').lower() == 'true',
            'file_encryption_enabled': os.getenv('FILE_ENCRYPTION_ENABLED', 'true').lower() == 'true',
            'audit_logging_enabled': os.getenv('AUDIT_LOGGING_ENABLED', 'true').lower() == 'true',
            'rate_limiting_enabled': os.getenv('RATE_LIMITING_ENABLED', 'true').lower() == 'true',
            'ip_whitelist_enabled': os.getenv('IP_WHITELIST_ENABLED', 'false').lower() == 'true',
            'allowed_ips': os.getenv('ALLOWED_IPS', '').split(',') if os.getenv('ALLOWED_IPS') else [],
        }
    
    def get_upload_limits(self, user_role: str) -> UploadLimits:
        """Get upload limits for user role"""
        role = UserRole(user_role) if user_role in [e.value for e in UserRole] else UserRole.VENDOR
        return self.upload_limits[role]
    
    def get_file_type_config(self, file_extension: str) -> FileTypeConfig:
        """Get file type configuration"""
        for config in self.file_types.values():
            if file_extension.lower() in config.extension.split(','):
                return config
        
        # Default configuration for unknown file types
        return FileTypeConfig(
            extension=file_extension,
            mime_types=[],
            max_size=1024 * 1024,  # 1MB default
            compression_enabled=False,
            compression_quality=0.8,
            virus_scan_required=True,
            preview_supported=False
        )
    
    def get_timeline_config(self) -> TimelineConfig:
        """Get timeline configuration"""
        return self.timeline
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return self.performance
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.security
    
    def is_file_type_allowed(self, file_extension: str) -> bool:
        """Check if file type is allowed"""
        for config in self.file_types.values():
            if file_extension.lower() in config.extension.split(','):
                return True
        return False
    
    def get_allowed_extensions(self) -> List[str]:
        """Get all allowed file extensions"""
        extensions = []
        for config in self.file_types.values():
            extensions.extend(config.extension.split(','))
        return extensions
    
    def get_allowed_mime_types(self) -> List[str]:
        """Get all allowed MIME types"""
        mime_types = []
        for config in self.file_types.values():
            mime_types.extend(config.mime_types)
        return mime_types
    
    def validate_file_size(self, file_size: int, file_extension: str, user_role: str) -> bool:
        """Validate file size against limits"""
        # Check user role limit
        user_limits = self.get_upload_limits(user_role)
        if file_size > user_limits.max_file_size:
            return False
        
        # Check file type specific limit
        file_config = self.get_file_type_config(file_extension)
        if file_size > file_config.max_size:
            return False
        
        return True
    
    def get_compression_settings(self, file_extension: str) -> Dict[str, Any]:
        """Get compression settings for file type"""
        file_config = self.get_file_type_config(file_extension)
        return {
            'enabled': file_config.compression_enabled,
            'quality': file_config.compression_quality
        }
    
    def should_scan_for_viruses(self, file_extension: str) -> bool:
        """Check if file should be scanned for viruses"""
        file_config = self.get_file_type_config(file_extension)
        return file_config.virus_scan_required and self.security['virus_scan_enabled']
    
    def supports_preview(self, file_extension: str) -> bool:
        """Check if file type supports preview"""
        file_config = self.get_file_type_config(file_extension)
        return file_config.preview_supported
    
    def get_reminder_schedule(self) -> List[int]:
        """Get reminder schedule in hours before deadline"""
        return self.timeline.reminder_hours
    
    def calculate_deadline(self, base_time: str = None) -> str:
        """Calculate deadline based on configuration"""
        from datetime import datetime, timedelta
        
        if base_time:
            base = datetime.fromisoformat(base_time.replace('Z', '+00:00'))
        else:
            base = datetime.now()
        
        deadline = base + timedelta(hours=self.timeline.default_deadline_hours)
        return deadline.isoformat()
    
    def is_within_grace_period(self, deadline: str) -> bool:
        """Check if current time is within grace period after deadline"""
        from datetime import datetime, timedelta
        
        deadline_time = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        grace_end = deadline_time + timedelta(hours=self.timeline.grace_period_hours)
        
        return datetime.now() < grace_end
    
    def should_auto_close(self, deadline: str) -> bool:
        """Check if request should be auto-closed"""
        from datetime import datetime, timedelta
        
        deadline_time = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        auto_close_time = deadline_time + timedelta(hours=self.timeline.auto_close_hours)
        
        return datetime.now() > auto_close_time

# Export singleton instance
upload_config = UploadConfiguration()
