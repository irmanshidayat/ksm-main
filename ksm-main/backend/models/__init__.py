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
    file_tags,
    # RAG models
    RagDocument,
    RagDocumentPage,
    RagDocumentChunk,
    RagChunkEmbedding,
    RagDocumentPermission
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
    WorkflowInstance,
    # Menu models
    Menu,
    MenuPermission,
    PermissionAuditLog,
    RoleLevelTemplate
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
from domains.email.models import (
    UserEmailDomain,
    EmailAttachment
)

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

# Integration models sudah dipindah ke domains/integration/models
# Import dari domain untuk backward compatibility
from domains.integration.models import (
    NotionDatabase,
    PropertyMapping
)

# Mobil models sudah dipindah ke domains/mobil/models
# Import dari domain untuk backward compatibility
from domains.mobil.models import (
    Mobil,
    MobilRequest,
    WaitingList,
    MobilBackup,
    MobilUsageLog,
    MobilStatus,
    RequestStatus,
    RecurringPattern,
    WaitingListStatus
)

# Vendor Order models sudah dipindah ke domains/vendor/models
# Import dari domain untuk backward compatibility
from domains.vendor.models import (
    VendorOrder,
    VendorOrderStatusHistory
)

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
    # RAG models
    'RagDocument',
    'RagDocumentPage',
    'RagDocumentChunk',
    'RagChunkEmbedding',
    'RagDocumentPermission',
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
    # Menu models
    'Menu',
    'MenuPermission',
    'PermissionAuditLog',
    'RoleLevelTemplate',
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
    'EmailAttachment',
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
    # Mobil models
    'Mobil',
    'MobilRequest',
    'WaitingList',
    'MobilBackup',
    'MobilUsageLog',
    'MobilStatus',
    'RequestStatus',
    'RecurringPattern',
    'WaitingListStatus',
    'VendorOrder',
    'VendorOrderStatusHistory'
]
