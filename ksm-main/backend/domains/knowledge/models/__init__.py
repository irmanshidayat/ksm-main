"""
Knowledge Models Package
"""

from .knowledge_models import (
    KnowledgeCategory,
    KnowledgeTag,
    KnowledgeBaseFile,
    FileVersion,
    UserFileAccess,
    file_tags,
    EmailLog,
    TelegramSettings,
    BotStatusHistory
)

from .rag_models import (
    RagDocument,
    RagDocumentPage,
    RagDocumentChunk,
    RagChunkEmbedding,
    RagDocumentPermission
)

# User model sudah dipindah ke domains/auth/models/
# Import untuk backward compatibility
from domains.auth.models.auth_models import User

__all__ = [
    'KnowledgeCategory',
    'KnowledgeTag',
    'KnowledgeBaseFile',
    'FileVersion',
    'UserFileAccess',
    'file_tags',
    'User',  # Imported from auth domain
    'EmailLog',
    'TelegramSettings',
    'BotStatusHistory',
    # RAG models
    'RagDocument',
    'RagDocumentPage',
    'RagDocumentChunk',
    'RagChunkEmbedding',
    'RagDocumentPermission'
]

