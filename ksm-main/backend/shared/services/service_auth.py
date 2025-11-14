#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service Authentication untuk KSM-Main
API key management untuk service-to-service communication
"""

import os
import time
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AuthStatus(Enum):
    """Authentication status"""
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    MISSING = "missing"

@dataclass
class ServiceAuthResult:
    """Service authentication result"""
    status: AuthStatus
    service_name: str = None
    permissions: List[str] = None
    error: str = None

@dataclass
class APIKey:
    """API Key configuration"""
    key_id: str
    key_value: str
    service_name: str
    permissions: List[str]
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None

class ServiceAuth:
    """Service authentication untuk KSM-Main"""
    
    def __init__(self):
        self.api_keys: Dict[str, APIKey] = {}
        self.secret_key = os.getenv('SERVICE_AUTH_SECRET', 'KSM-main-service-secret-key')
        
        # Initialize default API keys
        self._initialize_default_api_keys()
        
        logger.info("🔐 Service Authentication initialized for KSM-Main")
    
    def validate_api_key(self, api_key: str) -> ServiceAuthResult:
        """Validate API key"""
        try:
            if not api_key:
                return ServiceAuthResult(
                    status=AuthStatus.MISSING,
                    error="API key is required"
                )
            
            # Find matching API key
            for key in self.api_keys.values():
                if (key.key_value == api_key and 
                    key.is_active and 
                    (key.expires_at is None or key.expires_at > datetime.now())):
                    
                    # Update last used
                    key.last_used = datetime.now()
                    
                    return ServiceAuthResult(
                        status=AuthStatus.VALID,
                        service_name=key.service_name,
                        permissions=key.permissions
                    )
            
            return ServiceAuthResult(
                status=AuthStatus.INVALID,
                error="Invalid API key"
            )
            
        except Exception as e:
            logger.error(f"❌ API key validation failed: {e}")
            return ServiceAuthResult(
                status=AuthStatus.INVALID,
                error="Authentication error"
            )
    
    def add_api_key(self, api_key: APIKey) -> bool:
        """Add API key"""
        try:
            if api_key.key_id in self.api_keys:
                logger.warning(f"⚠️ API key already exists: {api_key.key_id}")
                return False
            
            api_key.created_at = datetime.now()
            self.api_keys[api_key.key_id] = api_key
            logger.info(f"✅ API key added: {api_key.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add API key: {e}")
            return False
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key"""
        try:
            if key_id in self.api_keys:
                self.api_keys[key_id].is_active = False
                logger.info(f"✅ API key revoked: {key_id}")
                return True
            else:
                logger.warning(f"⚠️ API key not found: {key_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to revoke API key: {e}")
            return False
    
    def generate_api_key(self, service_name: str, permissions: List[str] = None) -> str:
        """Generate new API key"""
        try:
            timestamp = str(int(time.time()))
            key_data = f"{service_name}:{timestamp}:{self.secret_key}"
            api_key = hashlib.sha256(key_data.encode()).hexdigest()
            
            # Create API key object
            key_id = f"key_{service_name}_{timestamp}"
            api_key_obj = APIKey(
                key_id=key_id,
                key_value=api_key,
                service_name=service_name,
                permissions=permissions or ['read', 'write'],
                expires_at=None,  # No expiration by default
                is_active=True
            )
            
            # Add to registry
            self.add_api_key(api_key_obj)
            
            return api_key
            
        except Exception as e:
            logger.error(f"❌ Failed to generate API key: {e}")
            return None
    
    def get_api_keys(self) -> Dict[str, APIKey]:
        """Get all API keys"""
        return self.api_keys
    
    def get_api_key_for_service(self, service_name: str) -> Optional[str]:
        """Get API key for specific service"""
        for key in self.api_keys.values():
            if key.service_name == service_name and key.is_active:
                return key.key_value
        return None
    
    def _initialize_default_api_keys(self):
        """Initialize default API keys"""
        try:
            # Default API key for KSM-Main (self)
            KSM_main_key = APIKey(
                key_id="KSM_main_self",
                key_value=os.getenv('KSM_MAIN_SELF_API_KEY', 'KSM-main-self-key-12345'),
                service_name="KSM_main",
                permissions=['read', 'write', 'admin'],
                expires_at=None,
                is_active=True
            )
            self.api_keys[KSM_main_key.key_id] = KSM_main_key
            
            # Default API key for Agent AI communication
            agent_ai_key = APIKey(
                key_id="agent_ai_communication",
                key_value=os.getenv('KSM_MAIN_API_KEY', 'KSM-main-default-key-12345'),
                service_name="agent_ai",
                permissions=['read', 'write'],
                expires_at=None,
                is_active=True
            )
            self.api_keys[agent_ai_key.key_id] = agent_ai_key
            
            # Default API key for testing
            test_key = APIKey(
                key_id="test_default",
                key_value=os.getenv('TEST_API_KEY', 'test-default-key-12345'),
                service_name="test",
                permissions=['read'],
                expires_at=None,
                is_active=True
            )
            self.api_keys[test_key.key_id] = test_key
            
            logger.info("✅ Default API keys initialized for KSM-Main")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize default API keys: {e}")

# Global service auth instance
service_auth = ServiceAuth()

# Convenience functions
def validate_service_auth(api_key: str) -> ServiceAuthResult:
    """Validate service authentication"""
    return service_auth.validate_api_key(api_key)

def get_api_key_for_agent_ai() -> str:
    """Get API key for Agent AI communication"""
    return service_auth.get_api_key_for_service('agent_ai') or 'KSM-main-default-key-12345'

def generate_service_api_key(service_name: str, permissions: List[str] = None) -> str:
    """Generate API key for service"""
    return service_auth.generate_api_key(service_name, permissions)

def get_all_api_keys() -> Dict[str, APIKey]:
    """Get all API keys"""
    return service_auth.get_api_keys()
