#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Models Initialization untuk KSM Main Backend
File ini dipanggil setelah database diinisialisasi
"""

def init_models():
    """Initialize semua models setelah database siap"""
    # Import inventory models dari domain
    from domains.inventory.models.inventory_models import (
        KategoriBarang, Barang, StokBarang, Supplier, 
        BarangMasuk, BarangKeluar
    )
    
    from domains.inventory.models.request_pembelian_models import (
        RequestPembelian, RequestPembelianItem
    )
    
    # Import knowledge models dari domain
    from domains.knowledge.models.knowledge_models import (
        KnowledgeCategory, KnowledgeTag, KnowledgeBaseFile, 
        FileVersion, UserFileAccess, TelegramSettings,
        BotStatusHistory, file_tags, EmailLog
    )
    
    # Import auth models dari domain
    from domains.auth.models.auth_models import User
    
    # Import email domain models
    from domains.email.models.email_models import UserEmailDomain
    
    from models.notion_database import NotionDatabase
    from models.property_mapping import PropertyMapping
    from models.rag_models import (
        RagDocument, RagDocumentPage, RagDocumentChunk,
        RagChunkEmbedding, RagDocumentPermission
    )
    
    # Import role management models dari domain
    from domains.role.models.role_models import (
        Department, Role, Permission, RolePermission, UserRole, 
        CrossDepartmentAccess, AccessRequest
    )
    
    # Import menu models
    from models.menu_models import (
        Menu, MenuPermission, PermissionAuditLog
    )
    
    # Import approval models
    from domains.approval.models.approval_models import (
        ApprovalWorkflow, ApprovalRequest, ApprovalAction, ApprovalStep,
        EscalationLog, ApprovalTemplate
    )
    
    # Import notification models dari domain
    from domains.notification.models.notification_models import (
        Notification, NotificationBatch, NotificationPreference, 
        NotificationBatchItem, NotificationAnalytics, NotificationMetrics, UserActivity
    )
    
    # Import shared models (audit, encryption, budget)
    from shared.models.audit_models import (
        UserActivityLog, SystemEventLog, SecurityEventLog, DataChangeLog, 
        AccessLog, SecurityAlert, ComplianceReport, AuditConfiguration
    )
    
    from shared.models.encryption_models import (
        EncryptionKey, KeyRotationLog, KeyBackup, KeyRecoveryLog, 
        EncryptedData, DataEncryptionPolicy
    )
    
    from shared.models.budget_models import (
        BudgetTracking, BudgetTransaction, AnalysisConfig, RequestTimelineConfig
    )
    
    # Import mobil models dari domain
    from domains.mobil.models.mobil_models import (
        Mobil, MobilRequest, WaitingList, MobilBackup, MobilUsageLog
    )
    
    # Import vendor models dari domain
    from domains.vendor.models.vendor_models import (
        Vendor, VendorCategory, VendorPenawaran, 
        VendorPenawaranFile, VendorPenawaranItem, VendorAnalysis,
        UploadConfig, FileUploadLog, VendorTemplate, VendorNotification
    )
    
    # Import task models dari domain
    from domains.task.models.task_models import (
        RemindExpDocs, DocumentStatus, DailyTask,
        TaskAttachment, TaskComment, TaskSettings
    )
    
    # Import attendance models dari domain
    from domains.attendance.models.attendance_models import (
        AttendanceRecord, AttendanceLeave, OvertimeRequest, AttendanceSettings
    )
    
    # Import email attachment models
    from models.email_attachment_model import EmailAttachment
    
    return {
        'inventory': {
            'KategoriBarang': KategoriBarang,
            'Barang': Barang,
            'StokBarang': StokBarang,
            'Supplier': Supplier,
            'BarangMasuk': BarangMasuk,
            'BarangKeluar': BarangKeluar,
            'RequestPembelian': RequestPembelian,
            'RequestPembelianItem': RequestPembelianItem
        },
        'vendor': {
            'Vendor': Vendor,
            'VendorCategory': VendorCategory,
            'VendorPenawaran': VendorPenawaran,
            'VendorPenawaranFile': VendorPenawaranFile,
            'VendorPenawaranItem': VendorPenawaranItem,
            'VendorAnalysis': VendorAnalysis,
            'UploadConfig': UploadConfig,
            'FileUploadLog': FileUploadLog,
            'VendorTemplate': VendorTemplate,
            'VendorNotification': VendorNotification
        },
        'knowledge_base': {
            'KnowledgeCategory': KnowledgeCategory,
            'KnowledgeTag': KnowledgeTag,
            'KnowledgeBaseFile': KnowledgeBaseFile,
            'FileVersion': FileVersion,
            'UserFileAccess': UserFileAccess,
            'User': User,
            'TelegramSettings': TelegramSettings,
            'BotStatusHistory': BotStatusHistory,
            'file_tags': file_tags
        },
        'notion': {
            'NotionDatabase': NotionDatabase
        },
        'property_mapping': {
            'PropertyMapping': PropertyMapping
        },
        'rag': {
            'RagDocument': RagDocument,
            'RagDocumentPage': RagDocumentPage,
            'RagDocumentChunk': RagDocumentChunk,
            'RagChunkEmbedding': RagChunkEmbedding,
            'RagDocumentPermission': RagDocumentPermission
        },
        'role_management': {
            'Department': Department,
            'Role': Role,
            'Permission': Permission,
            'RolePermission': RolePermission,
            'UserRole': UserRole,
            'CrossDepartmentAccess': CrossDepartmentAccess,
            'AccessRequest': AccessRequest
        },
        'approval': {
            'ApprovalWorkflow': ApprovalWorkflow,
            'ApprovalRequest': ApprovalRequest,
            'ApprovalAction': ApprovalAction,
            'ApprovalStep': ApprovalStep,
            'EscalationLog': EscalationLog,
            'ApprovalTemplate': ApprovalTemplate
        },
        'notification': {
            'Notification': Notification,
            'NotificationBatch': NotificationBatch,
            'NotificationPreference': NotificationPreference,
            'NotificationBatchItem': NotificationBatchItem,
            'NotificationAnalytics': NotificationAnalytics,
            'NotificationMetrics': NotificationMetrics,
            'UserActivity': UserActivity
        },
        'audit': {
            'UserActivityLog': UserActivityLog,
            'SystemEventLog': SystemEventLog,
            'SecurityEventLog': SecurityEventLog,
            'DataChangeLog': DataChangeLog,
            'AccessLog': AccessLog,
            'SecurityAlert': SecurityAlert,
            'ComplianceReport': ComplianceReport,
            'AuditConfiguration': AuditConfiguration
        },
        'encryption': {
            'EncryptionKey': EncryptionKey,
            'KeyRotationLog': KeyRotationLog,
            'KeyBackup': KeyBackup,
            'KeyRecoveryLog': KeyRecoveryLog,
            'EncryptedData': EncryptedData,
            'DataEncryptionPolicy': DataEncryptionPolicy
        },
        'mobil': {
            'Mobil': Mobil,
            'MobilRequest': MobilRequest,
            'WaitingList': WaitingList,
            'MobilBackup': MobilBackup,
            'MobilUsageLog': MobilUsageLog
        },
        'task': {
            'RemindExpDocs': RemindExpDocs,
            'DocumentStatus': DocumentStatus,
            'DailyTask': DailyTask,
            'TaskAttachment': TaskAttachment,
            'TaskComment': TaskComment,
            'TaskSettings': TaskSettings
        },
        'attendance': {
            'AttendanceRecord': AttendanceRecord,
            'AttendanceLeave': AttendanceLeave,
            'OvertimeRequest': OvertimeRequest,
            'AttendanceSettings': AttendanceSettings
        },
        'budget': {
            'BudgetTracking': BudgetTracking,
            'BudgetTransaction': BudgetTransaction,
            'AnalysisConfig': AnalysisConfig,
            'RequestTimelineConfig': RequestTimelineConfig
        },
        'email_attachments': {
            'EmailAttachment': EmailAttachment
        }
    }
