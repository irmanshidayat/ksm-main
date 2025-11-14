#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Models Package untuk KSM Main Backend
"""

# Knowledge models sudah dipindah ke domains/knowledge/models
# Import dari domain untuk backward compatibility
from domains.knowledge.models import (
    KnowledgeCategory,
    KnowledgeTag,
    KnowledgeBaseFile,
    FileVersion,
    UserFileAccess,
    TelegramSettings,
    BotStatusHistory,
    EmailLog,
    file_tags
)

# Auth models sudah dipindah ke domains/auth/models
# User model dipindah dari knowledge ke auth domain
from domains.auth.models import User

# Role models sudah dipindah ke domains/role/models
# Import dari domain untuk backward compatibility
from domains.role.models import (
    Department,
    Role,
    Permission,
    RolePermission,
    UserRole,
    CrossDepartmentAccess,
    AccessRequest,
    PermissionTemplate,
    WorkflowTemplate,
    AuditLog,
    WorkflowInstance
)

# Inventory models sudah dipindah ke domains/inventory/models
from domains.inventory.models import (
    KategoriBarang,
    Barang,
    StokBarang,
    Supplier,
    BarangMasuk,
    BarangKeluar,
    RequestPembelian,
    RequestPembelianItem
)

# Vendor models sudah dipindah ke domains/vendor/models
from domains.vendor.models import (
    Vendor,
    VendorCategory,
    VendorPenawaran,
    VendorPenawaranFile,
    VendorPenawaranItem,
    VendorAnalysis,
    UploadConfig,
    FileUploadLog,
    VendorTemplate,
    VendorNotification
)

# Shared models sudah dipindah ke shared/models
from shared.models import (
    BudgetTracking,
    BudgetTransaction,
    AnalysisConfig,
    RequestTimelineConfig,
    UserActivityLog,
    SystemEventLog,
    SecurityEventLog,
    DataChangeLog,
    AccessLog,
    SecurityAlert,
    ComplianceReport,
    AuditConfiguration,
    EncryptionKey,
    KeyRotationLog,
    KeyBackup,
    KeyRecoveryLog,
    EncryptedData,
    DataEncryptionPolicy
)

# Notification models sudah dipindah ke domains/notification/models
from domains.notification.models import (
    Notification,
    NotificationBatch,
    NotificationPreference,
    NotificationBatchItem,
    NotificationAnalytics,
    NotificationMetrics,
    UserActivity
)

# Email models sudah dipindah ke domains/email/models
from domains.email.models import UserEmailDomain

# Task models sudah dipindah ke domains/task/models
from domains.task.models import (
    RemindExpDocs,
    DocumentStatus,
    DailyTask,
    TaskAttachment,
    TaskComment,
    TaskSettings
)

# Attendance models sudah dipindah ke domains/attendance/models
from domains.attendance.models import (
    AttendanceRecord,
    AttendanceLeave,
    OvertimeRequest,
    AttendanceSettings
)

from .notion_database import NotionDatabase

from .property_mapping import PropertyMapping

from .mobil_models import (
    MobilRequest,
    WaitingList,
    Mobil,
    MobilUsageLog
)

from .vendor_order_models import VendorOrder

__all__ = [
    # Knowledge models
    'KnowledgeCategory',
    'KnowledgeTag', 
    'KnowledgeBaseFile',
    'FileVersion',
    'UserFileAccess',
    'User',
    'TelegramSettings',
    'BotStatusHistory',
    'EmailLog',
    'file_tags',
    # Role models
    'Department',
    'Role',
    'Permission',
    'RolePermission',
    'UserRole',
    'CrossDepartmentAccess',
    'AccessRequest',
    'PermissionTemplate',
    'WorkflowTemplate',
    'AuditLog',
    'WorkflowInstance',
    # Inventory models
    'KategoriBarang',
    'Barang',
    'StokBarang',
    'Supplier',
    'BarangMasuk',
    'BarangKeluar',
    'RequestPembelian',
    'RequestPembelianItem',
    # Vendor models
    'Vendor',
    'VendorCategory',
    'VendorPenawaran',
    'VendorPenawaranFile',
    'VendorPenawaranItem',
    'VendorAnalysis',
    'UploadConfig',
    'FileUploadLog',
    'VendorTemplate',
    'VendorNotification',
    # Shared models
    'BudgetTracking',
    'BudgetTransaction',
    'AnalysisConfig',
    'RequestTimelineConfig',
    'UserActivityLog',
    'SystemEventLog',
    'SecurityEventLog',
    'DataChangeLog',
    'AccessLog',
    'SecurityAlert',
    'ComplianceReport',
    'AuditConfiguration',
    'EncryptionKey',
    'KeyRotationLog',
    'KeyBackup',
    'KeyRecoveryLog',
    'EncryptedData',
    'DataEncryptionPolicy',
    # Notification models
    'Notification',
    'NotificationBatch',
    'NotificationPreference',
    'NotificationBatchItem',
    'NotificationAnalytics',
    'NotificationMetrics',
    'UserActivity',
    # Email models
    'UserEmailDomain',
    # Task models
    'RemindExpDocs',
    'DocumentStatus',
    'DailyTask',
    'TaskAttachment',
    'TaskComment',
    'TaskSettings',
    # Attendance models
    'AttendanceRecord',
    'AttendanceLeave',
    'OvertimeRequest',
    'AttendanceSettings',
    # Other models
    'NotionDatabase',
    'PropertyMapping',
    'MobilRequest',
    'WaitingList',
    'Mobil',
    'MobilUsageLog',
    'VendorOrder'
]
