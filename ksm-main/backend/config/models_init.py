#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Models Initialization untuk KSM Main Backend
File ini dipanggil setelah database diinisialisasi
"""

def init_models():
    """Initialize semua models setelah database siap"""
    # Import models setelah database siap
    from models.stok_barang import (
        KategoriBarang, Barang, StokBarang, Supplier, 
        BarangMasuk, BarangKeluar
    )
    
    from models.knowledge_base import (
        KnowledgeCategory, KnowledgeTag, KnowledgeBaseFile, 
        FileVersion, UserFileAccess, User, TelegramSettings,
        BotStatusHistory, file_tags, EmailLog
    )
    
    # Import email domain models
    from models.email_domain_models import UserEmailDomain
    
    from models.notion_database import NotionDatabase
    from models.property_mapping import PropertyMapping
    from models.rag_models import (
        RagDocument, RagDocumentPage, RagDocumentChunk,
        RagChunkEmbedding, RagDocumentPermission
    )
    
    # Import role management models
    from models.role_management import (
        Department, Role, Permission, RolePermission, UserRole, 
        CrossDepartmentAccess, AccessRequest
    )
    
    # Import menu models
    from models.menu_models import (
        Menu, MenuPermission, PermissionAuditLog
    )
    
    # Import approval models
    from models.approval_models import (
        ApprovalWorkflow, ApprovalRequest, ApprovalAction, ApprovalStep,
        EscalationLog, ApprovalTemplate
    )
    
    # Import notification models
    from models.notification_models import (
        Notification, NotificationBatch, NotificationPreference, 
        NotificationBatchItem, NotificationAnalytics, NotificationMetrics, UserActivity
    )
    
    # Import audit models
    from models.audit_models import (
        UserActivityLog, SystemEventLog, SecurityEventLog, DataChangeLog, 
        AccessLog, SecurityAlert, ComplianceReport, AuditConfiguration
    )
    
    # Import encryption models
    from models.encryption_models import (
        EncryptionKey, KeyRotationLog, KeyBackup, KeyRecoveryLog, 
        EncryptedData, DataEncryptionPolicy
    )
    
    # Import mobil models
    from models.mobil_models import (
        Mobil, MobilRequest, WaitingList, MobilBackup, MobilUsageLog
    )
    
    # Import request pembelian models
    from models.request_pembelian_models import (
        RequestPembelian, RequestPembelianItem, VendorPenawaran, 
        VendorPenawaranFile, VendorPenawaranItem, VendorAnalysis, Vendor, VendorCategory
    )
    
    # Import email attachment models
    from models.email_attachment_model import EmailAttachment
    
    # Import budget models
    from models.budget_models import (
        BudgetTracking, BudgetTransaction, AnalysisConfig, 
        RequestTimelineConfig
    )
    
    return {
        'stok_barang': {
            'KategoriBarang': KategoriBarang,
            'Barang': Barang,
            'StokBarang': StokBarang,
            'Supplier': Supplier,
            'BarangMasuk': BarangMasuk,
            'BarangKeluar': BarangKeluar
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
        'request_pembelian': {
            'RequestPembelian': RequestPembelian,
            'RequestPembelianItem': RequestPembelianItem,
            'VendorPenawaran': VendorPenawaran,
            'VendorPenawaranFile': VendorPenawaranFile,
            'VendorPenawaranItem': VendorPenawaranItem,
            'VendorAnalysis': VendorAnalysis,
            'Vendor': Vendor,
            'VendorCategory': VendorCategory
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
