#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Services Module - Backward Compatibility
File-file services yang sudah dipindah ke shared/services/ masih bisa diakses dari sini
untuk backward compatibility
"""

# Import dari shared/services untuk backward compatibility
from shared.services.audit_trail_service import (
    AuditTrailService,
    audit_service,
    audit_trail_service
)
from shared.services.encryption_service import (
    EncryptionService,
    KeyManagementService,
    DataEncryptionService
)
from shared.services.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitBreakerConfig,
    CircuitBreakerStats,
    CircuitState,
    CircuitBreakerOpenException,
    circuit_breaker_manager,
    get_agent_ai_circuit_breaker,
    get_circuit_breaker,
    call_with_circuit_breaker,
    circuit_breaker
)
from shared.services.intelligent_cache_service import (
    IntelligentCacheService,
    intelligent_cache_service,
    get_intelligent_cache_service
)
from shared.services.database_naming_service import DatabaseNamingConvention
from shared.services.service_auth import (
    ServiceAuth,
    AuthStatus,
    ServiceAuthResult,
    APIKey,
    service_auth,
    validate_service_auth,
    get_api_key_for_agent_ai,
    generate_service_api_key,
    get_all_api_keys
)

__all__ = [
    # Audit Trail
    'AuditTrailService',
    'audit_service',
    'audit_trail_service',
    # Encryption
    'EncryptionService',
    'KeyManagementService',
    'DataEncryptionService',
    # Circuit Breaker
    'CircuitBreaker',
    'CircuitBreakerManager',
    'CircuitBreakerConfig',
    'CircuitBreakerStats',
    'CircuitState',
    'CircuitBreakerOpenException',
    'circuit_breaker_manager',
    'get_agent_ai_circuit_breaker',
    'get_circuit_breaker',
    'call_with_circuit_breaker',
    'circuit_breaker',
    # Intelligent Cache
    'IntelligentCacheService',
    'intelligent_cache_service',
    'get_intelligent_cache_service',
    # Database Naming
    'DatabaseNamingConvention',
    # Service Auth
    'ServiceAuth',
    'AuthStatus',
    'ServiceAuthResult',
    'APIKey',
    'service_auth',
    'validate_service_auth',
    'get_api_key_for_agent_ai',
    'generate_service_api_key',
    'get_all_api_keys'
]

