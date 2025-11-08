#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent AI Configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def detect_environment():
    """
    Detect if running in Docker or Local environment
    Returns: 'docker' or 'local'
    """
    # 1. Check explicit environment variable
    run_mode = os.environ.get('RUN_MODE', '').lower()
    if run_mode in ['docker', 'container']:
        return 'docker'
    if run_mode in ['local', 'development']:
        return 'local'
    
    # 2. Check Docker indicators
    if os.path.exists('/.dockerenv'):
        return 'docker'
    
    # 3. Check /proc/1/cgroup (Linux only)
    if os.path.exists('/proc/1/cgroup'):
        try:
            with open('/proc/1/cgroup', 'r') as f:
                content = f.read()
                if 'docker' in content or 'containerd' in content:
                    return 'docker'
        except (IOError, OSError):
            pass
    
    # 4. Check hostname (if contains service names)
    hostname = os.environ.get('HOSTNAME', '')
    if any(service in hostname.lower() for service in ['mysql-prod', 'redis-prod', 'backend-prod', 'agent-ai-prod']):
        return 'docker'
    
    # 5. Check if DB_HOST contains service name (docker-compose service name)
    db_host = os.environ.get('DB_HOST', '')
    if db_host and 'mysql-prod' in db_host:
        return 'docker'
    
    # 6. Default to local
    return 'local'

# Detect environment once at module load
_ENV_MODE = detect_environment()

def get_env_config():
    """
    Get environment-specific configuration
    Returns dict with overrides for Docker or Local
    """
    if _ENV_MODE == 'docker':
        return {
            'DB_HOST': 'mysql-prod',
            'DB_PORT': 3306,
            'DB_PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
            'REDIS_URL': 'redis://redis-prod:6379/0',
            'CORS_ORIGINS': 'http://localhost:3002,http://localhost:8001,http://localhost:5001',
            'AGENT_AI_DEBUG': False,
            'LOG_LEVEL': 'INFO'
        }
    else:  # local
        return {
            'DB_HOST': 'localhost',
            'DB_PORT': 3306,
            'DB_PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'REDIS_URL': 'redis://localhost:6379/0',
            'CORS_ORIGINS': 'http://localhost:3000,http://localhost:8000,http://localhost:5000',
            'AGENT_AI_DEBUG': True,
            'LOG_LEVEL': 'DEBUG'
        }

# Get environment-specific config
_ENV_CONFIG = get_env_config()

class Config:
    """Base configuration class for Agent AI"""
    
    # =============================================================================
    # FLASK CONFIGURATION
    # =============================================================================
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'agent-ai-secret-key'
    # Debug mode - Auto-adjusted based on environment
    DEBUG_ENV = os.environ.get('AGENT_AI_DEBUG', '').lower()
    DEBUG = _ENV_CONFIG['AGENT_AI_DEBUG'] if DEBUG_ENV == '' else (DEBUG_ENV == 'true')
    HOST = os.environ.get('AGENT_AI_HOST', '0.0.0.0')
    PORT = int(os.environ.get('AGENT_AI_PORT', '5000'))
    
    # =============================================================================
    # DATABASE CONFIGURATION (Shared dengan KSM Main)
    # =============================================================================
    
    # MySQL Database Configuration (Shared dengan KSM Main) - Auto-adjusted based on environment
    DB_HOST = os.environ.get('DB_HOST') or _ENV_CONFIG['DB_HOST']
    DB_PORT = int(os.environ.get('DB_PORT') or str(_ENV_CONFIG['DB_PORT']))
    DB_NAME = os.environ.get('DB_NAME', 'KSM_main')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or _ENV_CONFIG['DB_PASSWORD']
    
    # Database URL (Shared dengan KSM Main) - Auto-adjusted based on environment
    DATABASE_URL = os.environ.get('DATABASE_URL') or f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # =============================================================================
    # OPENAI CONFIGURATION
    # =============================================================================
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    # Default Models
    DEFAULT_MODEL = os.environ.get('DEFAULT_MODEL', 'gpt-4o-mini')
    DEFAULT_EMBEDDING_MODEL = os.environ.get('DEFAULT_EMBEDDING_MODEL', 'text-embedding-3-small')
    
    # Model Parameters
    AI_TEMPERATURE = float(os.environ.get('AI_TEMPERATURE', '0.7'))
    AI_MAX_TOKENS = int(os.environ.get('AI_MAX_TOKENS', '2000'))
    AI_TOP_P = float(os.environ.get('AI_TOP_P', '0.9'))
    
    # =============================================================================
    # RAG CONFIGURATION
    # =============================================================================
    
    # RAG Context Processing
    RAG_MAX_CONTEXT_LENGTH = int(os.environ.get('RAG_MAX_CONTEXT_LENGTH', '8000'))
    RAG_MIN_SIMILARITY = float(os.environ.get('RAG_MIN_SIMILARITY', '0.3'))
    RAG_MAX_CHUNKS = int(os.environ.get('RAG_MAX_CHUNKS', '10'))
    
    # RAG Response Generation
    RAG_RESPONSE_TEMPERATURE = float(os.environ.get('RAG_RESPONSE_TEMPERATURE', '0.7'))
    RAG_RESPONSE_MAX_TOKENS = int(os.environ.get('RAG_RESPONSE_MAX_TOKENS', '1500'))
    
    # =============================================================================
    # COMPANY CONFIGURATION
    # =============================================================================
    
    # Default Company ID
    DEFAULT_COMPANY_ID = os.environ.get('DEFAULT_COMPANY_ID', 'PT. Kian Santang Muliatama')
    
    # =============================================================================
    # TELEGRAM CONFIGURATION
    # =============================================================================
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_WEBHOOK_URL = os.environ.get('TELEGRAM_WEBHOOK_URL')
    
    # Telegram Response Settings
    TELEGRAM_MAX_RESPONSE_LENGTH = int(os.environ.get('TELEGRAM_MAX_RESPONSE_LENGTH', '4000'))
    TELEGRAM_RESPONSE_TIMEOUT = int(os.environ.get('TELEGRAM_RESPONSE_TIMEOUT', '30'))
    
    # =============================================================================
    # API CONFIGURATION
    # =============================================================================
    
    # API Settings
    API_KEY = os.environ.get('AGENT_AI_API_KEY', 'KSM_api_key_2ptybn')
    API_TIMEOUT = int(os.environ.get('API_TIMEOUT', '30'))
    
    # CORS Settings - Auto-adjusted based on environment
    CORS_ORIGINS_STR = os.environ.get('CORS_ORIGINS') or _ENV_CONFIG['CORS_ORIGINS']
    CORS_ORIGINS = CORS_ORIGINS_STR.split(',')
    
    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    
    # Log Level - Auto-adjusted based on environment
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or _ENV_CONFIG['LOG_LEVEL']
    LOG_FILE = os.environ.get('LOG_FILE', 'agent_ai.log')
    
    # =============================================================================
    # CACHE CONFIGURATION
    # =============================================================================
    
    # Cache Settings
    CACHE_ENABLED = os.environ.get('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_TTL = int(os.environ.get('CACHE_TTL', '3600'))  # 1 hour
    CACHE_MAX_SIZE = int(os.environ.get('CACHE_MAX_SIZE', '1000'))
    
    # =============================================================================
    # MONITORING CONFIGURATION
    # =============================================================================
    
    # Monitoring Settings
    MONITORING_ENABLED = os.environ.get('MONITORING_ENABLED', 'true').lower() == 'true'
    METRICS_ENABLED = os.environ.get('METRICS_ENABLED', 'true').lower() == 'true'
    
    # =============================================================================
    # SECURITY CONFIGURATION
    # =============================================================================
    
    # Security Settings
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '3600'))  # 1 hour
    
    # Input Validation
    MAX_MESSAGE_LENGTH = int(os.environ.get('MAX_MESSAGE_LENGTH', '4000'))
    MAX_CONTEXT_LENGTH = int(os.environ.get('MAX_CONTEXT_LENGTH', '10000'))
    
    @classmethod
    def validate_config(cls):
        """Validate configuration"""
        errors = []
        
        # Check required configurations
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        
        if not cls.API_KEY:
            errors.append("AGENT_AI_API_KEY is required")
        
        # Check database connection
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL is required")
        
        return errors
    
    @classmethod
    def get_config_summary(cls):
        """Get configuration summary"""
        return {
            'flask': {
                'debug': cls.DEBUG,
                'host': cls.HOST,
                'port': cls.PORT
            },
            'database': {
                'host': cls.DB_HOST,
                'port': cls.DB_PORT,
                'name': cls.DB_NAME
            },
            'openai': {
                'model': cls.DEFAULT_MODEL,
                'temperature': cls.AI_TEMPERATURE,
                'max_tokens': cls.AI_MAX_TOKENS
            },
            'rag': {
                'max_context_length': cls.RAG_MAX_CONTEXT_LENGTH,
                'min_similarity': cls.RAG_MIN_SIMILARITY,
                'max_chunks': cls.RAG_MAX_CHUNKS
            },
            'telegram': {
                'max_response_length': cls.TELEGRAM_MAX_RESPONSE_LENGTH,
                'response_timeout': cls.TELEGRAM_RESPONSE_TIMEOUT
            },
            'api': {
                'timeout': cls.API_TIMEOUT,
                'rate_limit_enabled': cls.RATE_LIMIT_ENABLED
            }
        }
