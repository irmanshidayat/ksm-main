#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Validator untuk KSM Main Backend
Validasi konfigurasi environment dan memberikan feedback yang jelas
"""

import os
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result dari configuration validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

class ConfigValidator:
    """Configuration validator untuk KSM Main Backend"""
    
    def __init__(self):
        self.required_vars = {
            'SECRET_KEY': 'Flask secret key untuk security',
            'DB_PASSWORD': 'MySQL database password',
            'OPENROUTER_API_KEY': 'OpenRouter API key untuk AI models',
        }
        
        self.optional_vars = {
            'JWT_SECRET_KEY': 'JWT secret key untuk authentication',
            'AGENT_AI_API_KEY': 'Agent AI integration API key',
            'REDIS_PASSWORD': 'Redis password (if using Redis)',
        }
        
        self.qdrant_vars = {
            'QDRANT_URL': 'Qdrant.io URL',
            'QDRANT_API_KEY': 'Qdrant.io API key',
        }
        
        self.database_vars = {
            'DB_HOST': 'MySQL database host',
            'DB_PORT': 'MySQL database port',
            'DB_NAME': 'MySQL database name',
            'DB_USER': 'MySQL database user',
        }
    
    def validate_all(self) -> ValidationResult:
        """Validasi semua konfigurasi"""
        errors = []
        warnings = []
        suggestions = []
        
        # Validasi required variables
        required_result = self._validate_required()
        errors.extend(required_result.errors)
        warnings.extend(required_result.warnings)
        suggestions.extend(required_result.suggestions)
        
        # Validasi database configuration
        database_result = self._validate_database()
        errors.extend(database_result.errors)
        warnings.extend(database_result.warnings)
        suggestions.extend(database_result.suggestions)
        
        # Validasi Qdrant configuration
        qdrant_result = self._validate_qdrant()
        errors.extend(qdrant_result.errors)
        warnings.extend(qdrant_result.warnings)
        suggestions.extend(qdrant_result.suggestions)
        
        # Validasi RAG configuration
        rag_result = self._validate_rag()
        errors.extend(rag_result.errors)
        warnings.extend(rag_result.warnings)
        suggestions.extend(rag_result.suggestions)
        
        # Validasi feature flags
        feature_result = self._validate_feature_flags()
        warnings.extend(feature_result.warnings)
        suggestions.extend(feature_result.suggestions)
        
        # Validasi performance settings
        performance_result = self._validate_performance()
        warnings.extend(performance_result.warnings)
        suggestions.extend(performance_result.suggestions)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_required(self) -> ValidationResult:
        """Validasi required environment variables"""
        errors = []
        warnings = []
        suggestions = []
        
        for var, description in self.required_vars.items():
            value = os.environ.get(var)
            if not value:
                errors.append(f"❌ {var}: {description} - REQUIRED")
            elif value in ['your-secret-key-here', 'your-mysql-password', 'your-openrouter-api-key-here']:
                errors.append(f"❌ {var}: Please update from placeholder value")
            else:
                logger.info(f"✅ {var}: Configured")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_database(self) -> ValidationResult:
        """Validasi database configuration"""
        errors = []
        warnings = []
        suggestions = []
        
        # Check database connection parameters
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '3306')
        db_name = os.environ.get('DB_NAME', 'KSM_main')
        db_user = os.environ.get('DB_USER', 'root')
        db_password = os.environ.get('DB_PASSWORD')
        
        # Password kosong diperbolehkan untuk development (root tanpa password)
        if not db_password:
            warnings.append("⚠️ DB_PASSWORD: Using empty password (development mode)")
        
        # Check port
        try:
            port = int(db_port)
            if port != 3306:
                warnings.append(f"⚠️ DB_PORT: Using non-standard MySQL port {port}")
        except ValueError:
            errors.append("❌ DB_PORT: Must be a valid port number")
        
        # Check database name
        if db_name != 'KSM_main':
            warnings.append(f"⚠️ DB_NAME: Using non-standard database name '{db_name}'")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_qdrant(self) -> ValidationResult:
        """Validasi Qdrant configuration"""
        errors = []
        warnings = []
        suggestions = []
        
        qdrant_enabled = os.environ.get('ENABLE_QDRANT', 'true').lower() == 'true'
        
        if qdrant_enabled:
            # Check Qdrant URL
            qdrant_url = os.environ.get('QDRANT_URL')
            if not qdrant_url:
                errors.append("❌ QDRANT_URL: Qdrant.io URL is required")
            elif not qdrant_url.startswith('https://'):
                warnings.append("⚠️ QDRANT_URL: Should use HTTPS for security")
            
            # Check Qdrant API Key
            qdrant_api_key = os.environ.get('QDRANT_API_KEY')
            if not qdrant_api_key:
                errors.append("❌ QDRANT_API_KEY: Qdrant.io API key is required")
            elif len(qdrant_api_key) < 20:
                warnings.append("⚠️ QDRANT_API_KEY: API key seems too short")
            
            # Check vector size
            try:
                vector_size = int(os.environ.get('QDRANT_VECTOR_SIZE', '384'))
                if vector_size not in [384, 768, 1024, 1536]:
                    warnings.append(f"⚠️ QDRANT_VECTOR_SIZE: {vector_size} is not a standard embedding dimension")
            except ValueError:
                errors.append("❌ QDRANT_VECTOR_SIZE: Must be a valid number")
            
            # Check similarity threshold
            try:
                threshold = float(os.environ.get('QDRANT_SIMILARITY_THRESHOLD', '0.7'))
                if threshold < 0 or threshold > 1:
                    warnings.append(f"⚠️ QDRANT_SIMILARITY_THRESHOLD: {threshold} should be between 0 and 1")
            except ValueError:
                errors.append("❌ QDRANT_SIMILARITY_THRESHOLD: Must be a valid number")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_rag(self) -> ValidationResult:
        """Validasi RAG configuration"""
        errors = []
        warnings = []
        suggestions = []
        
        rag_enabled = os.environ.get('RAG_ENABLED', 'true').lower() == 'true'
        
        if rag_enabled:
            # Check chunk size
            try:
                chunk_size = int(os.environ.get('RAG_CHUNK_SIZE', '800'))
                if chunk_size < 100:
                    warnings.append(f"⚠️ RAG_CHUNK_SIZE: {chunk_size} may be too small for effective retrieval")
                elif chunk_size > 2000:
                    warnings.append(f"⚠️ RAG_CHUNK_SIZE: {chunk_size} may be too large for precise retrieval")
            except ValueError:
                errors.append("❌ RAG_CHUNK_SIZE: Must be a valid number")
            
            # Check chunk overlap
            try:
                overlap = int(os.environ.get('RAG_CHUNK_OVERLAP', '150'))
                chunk_size = int(os.environ.get('RAG_CHUNK_SIZE', '800'))
                if overlap >= chunk_size:
                    errors.append("❌ RAG_CHUNK_OVERLAP: Must be less than RAG_CHUNK_SIZE")
            except ValueError:
                errors.append("❌ RAG_CHUNK_OVERLAP: Must be a valid number")
            
            # Check max chunks
            try:
                max_chunks = int(os.environ.get('RAG_MAX_CHUNKS', '20'))
                if max_chunks > 50:
                    warnings.append(f"⚠️ RAG_MAX_CHUNKS: {max_chunks} may be too high for performance")
            except ValueError:
                errors.append("❌ RAG_MAX_CHUNKS: Must be a valid number")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_feature_flags(self) -> ValidationResult:
        """Validasi feature flags"""
        errors = []
        warnings = []
        suggestions = []
        
        feature_flags = [
            'ENABLE_KNOWLEDGE_BASE',
            'ENABLE_VECTOR_SEARCH',
            'ENABLE_DOCUMENT_UPLOAD',
            'ENABLE_RAG_QUERY',
            'ENABLE_QDRANT',
            'ENABLE_EMBEDDINGS_CACHE',
            'ENABLE_DOCUMENT_ANALYSIS',
            'ENABLE_SEMANTIC_SEARCH',
            'ENABLE_AGENT_AI_INTEGRATION',
            'ENABLE_WEBHOOK_NOTIFICATIONS',
            'ENABLE_BATCH_PROCESSING'
        ]
        
        enabled_features = []
        disabled_features = []
        
        for flag in feature_flags:
            value = os.environ.get(flag, 'true').lower()
            if value == 'true':
                enabled_features.append(flag)
            else:
                disabled_features.append(flag)
        
        logger.info(f"✅ Enabled features: {len(enabled_features)}")
        logger.info(f"⚠️ Disabled features: {len(disabled_features)}")
        
        if len(disabled_features) > 5:
            warnings.append(f"⚠️ Many features are disabled ({len(disabled_features)}). Consider enabling more features for full functionality.")
        
        return ValidationResult(
            is_valid=True,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_performance(self) -> ValidationResult:
        """Validasi performance settings"""
        errors = []
        warnings = []
        suggestions = []
        
        # Check database pool settings
        try:
            pool_size = int(os.environ.get('DB_POOL_SIZE', '10'))
            if pool_size < 5:
                warnings.append(f"⚠️ DB_POOL_SIZE: {pool_size} may be too small for production")
            elif pool_size > 50:
                warnings.append(f"⚠️ DB_POOL_SIZE: {pool_size} may be too large for resource usage")
        except ValueError:
            errors.append("❌ DB_POOL_SIZE: Must be a valid number")
        
        # Check cache settings
        cache_enabled = os.environ.get('ENABLE_EMBEDDINGS_CACHE', 'true').lower() == 'true'
        if not cache_enabled:
            warnings.append("⚠️ ENABLE_EMBEDDINGS_CACHE: Disabled, may impact performance")
            suggestions.append("💡 Consider enabling embeddings cache for better performance")
        
        # Check rate limiting
        rate_limit_enabled = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
        if not rate_limit_enabled:
            warnings.append("⚠️ RATE_LIMIT_ENABLED: Disabled, may cause abuse")
            suggestions.append("💡 Consider enabling rate limiting for security")
        
        # Check file size limits
        try:
            max_file_size = int(os.environ.get('MAX_FILE_SIZE', '10485760'))
            if max_file_size > 52428800:  # 50MB
                warnings.append(f"⚠️ MAX_FILE_SIZE: {max_file_size} bytes may be too large for web uploads")
        except ValueError:
            errors.append("❌ MAX_FILE_SIZE: Must be a valid number")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def generate_config_report(self) -> str:
        """Generate configuration report"""
        result = self.validate_all()
        
        report = []
        report.append("🔧 KSM MAIN BACKEND CONFIGURATION REPORT")
        report.append("=" * 50)
        
        if result.is_valid:
            report.append("✅ Configuration Status: VALID")
        else:
            report.append("❌ Configuration Status: INVALID")
        
        report.append("")
        
        if result.errors:
            report.append("🚨 ERRORS (Must Fix):")
            for error in result.errors:
                report.append(f"  {error}")
            report.append("")
        
        if result.warnings:
            report.append("⚠️ WARNINGS (Should Fix):")
            for warning in result.warnings:
                report.append(f"  {warning}")
            report.append("")
        
        if result.suggestions:
            report.append("💡 SUGGESTIONS (Consider):")
            for suggestion in result.suggestions:
                report.append(f"  {suggestion}")
            report.append("")
        
        # Summary
        report.append("📊 SUMMARY:")
        report.append(f"  Errors: {len(result.errors)}")
        report.append(f"  Warnings: {len(result.warnings)}")
        report.append(f"  Suggestions: {len(result.suggestions)}")
        
        return "\n".join(report)

def main():
    """Main function untuk testing"""
    validator = ConfigValidator()
    report = validator.generate_config_report()
    print(report)
    
    result = validator.validate_all()
    return result.is_valid

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
