#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat Models untuk Agent AI
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class MessageSource(Enum):
    """Message source types"""
    TELEGRAM = "telegram"
    RAG = "rag"
    WEB = "web"
    API = "api"
    TEST = "test"

class MessageStatus(Enum):
    """Message status types"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ChatMessage:
    """Chat message model"""
    user_id: int
    message: str
    session_id: str
    source: MessageSource
    timestamp: datetime
    message_id: Optional[str] = None
    status: MessageStatus = MessageStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['source'] = self.source.value
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create from dictionary"""
        return cls(
            user_id=data['user_id'],
            message=data['message'],
            session_id=data['session_id'],
            source=MessageSource(data.get('source', 'telegram')),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            message_id=data.get('message_id'),
            status=MessageStatus(data.get('status', 'pending'))
        )

@dataclass
class ChatResponse:
    """Chat response model"""
    message_id: str
    response: str
    model_used: str
    processing_time: float
    tokens_used: int
    timestamp: datetime
    context_used: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatResponse':
        """Create from dictionary"""
        return cls(
            message_id=data['message_id'],
            response=data['response'],
            model_used=data['model_used'],
            processing_time=data['processing_time'],
            tokens_used=data['tokens_used'],
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            context_used=data.get('context_used', False),
            error=data.get('error')
        )

@dataclass
class RAGContext:
    """RAG context model"""
    rag_results: List[Dict[str, Any]]
    total_chunks: int
    avg_similarity: float
    search_time_ms: float
    context_available: bool
    similarity_threshold: float
    cached: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RAGContext':
        """Create from dictionary"""
        return cls(
            rag_results=data['rag_results'],
            total_chunks=data['total_chunks'],
            avg_similarity=data['avg_similarity'],
            search_time_ms=data['search_time_ms'],
            context_available=data['context_available'],
            similarity_threshold=data['similarity_threshold'],
            cached=data.get('cached', False)
        )

@dataclass
class ChatSession:
    """Chat session model"""
    session_id: str
    user_id: int
    source: MessageSource
    created_at: datetime
    last_activity: datetime
    message_count: int = 0
    total_tokens: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['source'] = self.source.value
        data['created_at'] = self.created_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatSession':
        """Create from dictionary"""
        return cls(
            session_id=data['session_id'],
            user_id=data['user_id'],
            source=MessageSource(data.get('source', 'telegram')),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            last_activity=datetime.fromisoformat(data.get('last_activity', datetime.now().isoformat())),
            message_count=data.get('message_count', 0),
            total_tokens=data.get('total_tokens', 0)
        )

@dataclass
class ServiceStatus:
    """Service status model"""
    service_name: str
    status: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceStatus':
        """Create from dictionary"""
        return cls(
            service_name=data['service_name'],
            status=data['status'],
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            details=data.get('details'),
            error=data.get('error')
        )
