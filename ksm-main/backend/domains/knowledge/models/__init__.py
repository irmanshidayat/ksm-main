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
    'BotStatusHistory'
]

