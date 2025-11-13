import os
from dotenv import load_dotenv
import logging

# Load .env file dengan fallback strategy:
# 1. Coba load dari backend/.env (untuk backward compatibility)
# 2. Jika tidak ada, fallback ke root ksm-main/.env (untuk unified env)
backend_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
root_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')

logger_config = logging.getLogger(__name__)

# Priority: backend/.env > root/.env
env_loaded = False
env_path_used = None

if os.path.exists(backend_env_path):
    load_dotenv(dotenv_path=backend_env_path, override=True)
    env_loaded = True
    env_path_used = backend_env_path
    logger_config.info(f"📁 Loading .env from backend folder: {backend_env_path}")
elif os.path.exists(root_env_path):
    load_dotenv(dotenv_path=root_env_path, override=True)
    env_loaded = True
    env_path_used = root_env_path
    logger_config.info(f"📁 Loading .env from root folder: {root_env_path}")
else:
    logger_config.warning(f"⚠️  No .env file found! Tried:")
    logger_config.warning(f"   - {backend_env_path}")
    logger_config.warning(f"   - {root_env_path}")
    logger_config.warning(f"   Using system environment variables only")

if env_loaded:
    logger_config.info(f"✅ .env file loaded successfully from: {env_path_used}")
    logger_config.info(f"📁 CORS_ORIGINS from .env: {os.environ.get('CORS_ORIGINS', 'NOT SET')}")

def detect_environment():
    """
    Detect if running in Docker or Local environment
    Returns: 'docker' or 'local'
    """
    # 1. Check explicit environment variable (highest priority)
    run_mode = os.environ.get('RUN_MODE', '').lower()
    if run_mode in ['docker', 'container']:
        return 'docker'
    if run_mode in ['local', 'development']:
        return 'local'
    
    # 2. Check if DB_HOST is explicitly set to docker service name
    db_host = os.environ.get('DB_HOST', '')
    if db_host and ('mysql-prod' in db_host or 'mysql' in db_host.lower() and db_host != 'localhost' and '127.0.0.1' not in db_host):
        return 'docker'
    
    # 3. Check Docker indicators (only if not Windows or if explicitly in container)
    if os.path.exists('/.dockerenv'):
        return 'docker'
    
    # 4. Check /proc/1/cgroup (Linux only, not Windows)
    if os.path.exists('/proc/1/cgroup'):
        try:
            with open('/proc/1/cgroup', 'r') as f:
                content = f.read()
                if 'docker' in content or 'containerd' in content:
                    return 'docker'
        except (IOError, OSError):
            pass
    
    # 5. Check hostname (if contains service names)
    hostname = os.environ.get('HOSTNAME', '')
    if hostname and any(service in hostname.lower() for service in ['mysql-prod', 'redis-prod', 'backend-prod', 'agent-ai-prod', 'ksm-']):
        return 'docker'
    
    # 6. Check if running on Windows (likely local development)
    import platform
    if platform.system() == 'Windows':
        # On Windows, default to local unless explicitly set to docker
        # Check if we can connect to localhost MySQL (XAMPP)
        return 'local'
    
    # 7. Default to local (safer for development)
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
            'DB_PASSWORD': os.environ.get('DB_PASSWORD', 'admin123'),  # Default password untuk Docker
            'REDIS_URL': 'redis://redis-prod:6379/0',
            'AGENT_AI_URL': 'http://agent-ai-prod:5000',
            'AGENT_AI_BASE_URL': 'http://agent-ai-prod:5000',
            'CORS_ORIGINS': 'http://localhost:3002,http://localhost:3005,http://localhost:8001,http://localhost:5001,https://report.ptkiansatang.com',
            'GMAIL_REDIRECT_URI': 'https://report.ptkiansatang.com/request-pembelian/auth/gmail/callback',
            'FLASK_ENV': 'production',
            'FLASK_DEBUG': False,
            'LOG_LEVEL': 'INFO'
        }
    else:  # local
        return {
            'DB_HOST': 'localhost',
            'DB_PORT': 3306,
            'DB_PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'REDIS_URL': 'redis://localhost:6379/0',
            'AGENT_AI_URL': 'http://localhost:5000',
            'AGENT_AI_BASE_URL': 'http://localhost:5000',
            'CORS_ORIGINS': 'http://localhost:3000,http://localhost:3004,http://localhost:8000,http://localhost:5000',
            'GMAIL_REDIRECT_URI': 'http://localhost:3000/request-pembelian/auth/gmail/callback',
            'FLASK_ENV': 'development',
            'FLASK_DEBUG': True,
            'LOG_LEVEL': 'DEBUG'
        }

# Get environment-specific config
_ENV_CONFIG = get_env_config()

class Config:
    """Base configuration class for KSM Main"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Log Level - Auto-adjusted based on environment
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or _ENV_CONFIG['LOG_LEVEL']
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    
    # MySQL Database Configuration - Auto-adjusted based on environment
    DB_HOST = os.environ.get('DB_HOST') or _ENV_CONFIG['DB_HOST']
    DB_PORT = int(os.environ.get('DB_PORT') or str(_ENV_CONFIG['DB_PORT']))
    DB_NAME = os.environ.get('DB_NAME', 'KSM_main')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or _ENV_CONFIG['DB_PASSWORD']
    
    # Database URL - Auto-adjusted based on environment
    DATABASE_URL = os.environ.get('DATABASE_URL') or f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # =============================================================================
    # QDRANT CONFIGURATION
    # =============================================================================
    
    # Qdrant Settings
    QDRANT_URL = os.environ.get('QDRANT_URL')
    QDRANT_API_KEY = os.environ.get('QDRANT_API_KEY')
    
    # Qdrant Performance Settings
    QDRANT_BATCH_SIZE = int(os.environ.get('QDRANT_BATCH_SIZE', '100'))
    QDRANT_VECTOR_SIZE = int(os.environ.get('QDRANT_VECTOR_SIZE', '384'))
    QDRANT_COLLECTION_PREFIX = os.environ.get('QDRANT_COLLECTION_PREFIX', 'KSM')
    
    # Qdrant Collection Settings
    QDRANT_DEFAULT_COLLECTION = os.environ.get('QDRANT_DEFAULT_COLLECTION', 'KSM_main_documents')
    QDRANT_METADATA_FILTERS = os.environ.get('QDRANT_METADATA_FILTERS', 'true').lower() == 'true'
    QDRANT_SIMILARITY_THRESHOLD = float(os.environ.get('QDRANT_SIMILARITY_THRESHOLD', '0.7'))
    QDRANT_DISTANCE_FUNCTION = os.environ.get('QDRANT_DISTANCE_FUNCTION', 'cosine')
    
    # =============================================================================
    # VECTOR SEARCH CONFIGURATION
    # =============================================================================
    
    # Vector Search Settings
    VECTOR_SEARCH_ENABLED = os.environ.get('VECTOR_SEARCH_ENABLED', 'true').lower() == 'true'
    VECTOR_SEARCH_ENGINE = os.environ.get('VECTOR_SEARCH_ENGINE', 'qdrant')
    VECTOR_SEARCH_TOP_K = int(os.environ.get('VECTOR_SEARCH_TOP_K', '10'))
    VECTOR_SEARCH_SIMILARITY_THRESHOLD = float(os.environ.get('VECTOR_SEARCH_SIMILARITY_THRESHOLD', '0.5'))
    
    # Embeddings Settings
    EMBEDDINGS_MODEL = os.environ.get('EMBEDDINGS_MODEL', 'google/gemini-2.5-pro')
    EMBEDDINGS_DIMENSION = int(os.environ.get('EMBEDDINGS_DIMENSION', '768'))
    EMBEDDINGS_BATCH_SIZE = int(os.environ.get('EMBEDDINGS_BATCH_SIZE', '100'))
    EMBEDDINGS_CACHE_TTL = int(os.environ.get('EMBEDDINGS_CACHE_TTL', '3600'))
    
    # =============================================================================
    # RAG CONFIGURATION
    # =============================================================================
    
    # RAG Settings
    RAG_ENABLED = os.environ.get('RAG_ENABLED', 'true').lower() == 'true'
    RAG_CHUNK_SIZE = int(os.environ.get('RAG_CHUNK_SIZE', '800'))
    RAG_CHUNK_OVERLAP = int(os.environ.get('RAG_CHUNK_OVERLAP', '150'))
    RAG_MAX_CHUNKS = int(os.environ.get('RAG_MAX_CHUNKS', '20'))
    RAG_SIMILARITY_THRESHOLD = float(os.environ.get('RAG_SIMILARITY_THRESHOLD', '0.6'))
    
    # Document Processing
    DOCUMENT_PROCESSING_ENABLED = os.environ.get('DOCUMENT_PROCESSING_ENABLED', 'true').lower() == 'true'
    SUPPORTED_FORMATS = os.environ.get('SUPPORTED_FORMATS', 'pdf,txt,docx,md').split(',')
    MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', '10485760'))  # 10MB
    PROCESSING_TIMEOUT = int(os.environ.get('PROCESSING_TIMEOUT', '300'))
    
    # =============================================================================
    # AI MODEL CONFIGURATION
    # =============================================================================
    
    # AI Provider
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'openrouter')
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
    OPENROUTER_BASE_URL = os.environ.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
    
    # Default Models
    DEFAULT_TEXT_MODEL = os.environ.get('DEFAULT_TEXT_MODEL', 'google/gemini-2.5-flash-preview-09-2025')
    DEFAULT_EMBEDDINGS_MODEL = os.environ.get('DEFAULT_EMBEDDINGS_MODEL', 'google/gemini-2.5-flash-preview-09-2025')
    DEFAULT_FALLBACK_MODEL = os.environ.get('DEFAULT_FALLBACK_MODEL', 'google/gemini-2.5-flash-preview-09-2025')
    
    # Model Parameters
    AI_TEMPERATURE = float(os.environ.get('AI_TEMPERATURE', '0.7'))
    AI_MAX_TOKENS = int(os.environ.get('AI_MAX_TOKENS', '2000'))
    AI_TOP_P = float(os.environ.get('AI_TOP_P', '0.9'))
    
    # =============================================================================
    # TELEGRAM RAG CONFIGURATION
    # =============================================================================
    
    # Telegram-specific RAG settings
    TELEGRAM_RAG_TOP_K = int(os.environ.get('TELEGRAM_RAG_TOP_K', '5'))
    TELEGRAM_RAG_SIMILARITY_THRESHOLD = float(os.environ.get('TELEGRAM_RAG_SIMILARITY_THRESHOLD', '0.65'))
    TELEGRAM_RAG_MAX_CONTEXT = int(os.environ.get('TELEGRAM_RAG_MAX_CONTEXT', '8000'))
    
    # Telegram RAG Cache settings
    TELEGRAM_RAG_CACHE_TTL = int(os.environ.get('TELEGRAM_RAG_CACHE_TTL', '1800'))  # 30 menit
    TELEGRAM_RESPONSE_CACHE_TTL = int(os.environ.get('TELEGRAM_RESPONSE_CACHE_TTL', '300'))  # 5 menit
    
    # Telegram RAG Fallback settings
    TELEGRAM_ENABLE_RAG_FALLBACK = os.environ.get('TELEGRAM_ENABLE_RAG_FALLBACK', 'true').lower() == 'true'
    TELEGRAM_ENABLE_AGENT_AI_FALLBACK = os.environ.get('TELEGRAM_ENABLE_AGENT_AI_FALLBACK', 'true').lower() == 'true'
    
    # =============================================================================
    # API CONFIGURATION
    # =============================================================================
    
    # API Settings
    API_VERSION = os.environ.get('API_VERSION', 'v1')
    API_PREFIX = os.environ.get('API_PREFIX', '/api')
    # CORS Origins - Auto-adjusted based on environment
    CORS_ORIGINS_STR = os.environ.get('CORS_ORIGINS') or _ENV_CONFIG['CORS_ORIGINS']
    # Split dan strip whitespace untuk menghindari masalah parsing
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(',') if origin.strip()]
    # Log untuk debugging
    logger_config.info(f"🌐 CORS_ORIGINS_STR: {CORS_ORIGINS_STR}")
    logger_config.info(f"🌐 CORS_ORIGINS loaded from {'ENV' if os.environ.get('CORS_ORIGINS') else 'CONFIG'}: {CORS_ORIGINS}")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '3600'))
    
    # Request Settings
    MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '3'))
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', '30'))
    
    # =============================================================================
    # NOTION API CONFIGURATION
    # =============================================================================
    
    # Notion API Settings
    NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
    NOTION_DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')
    NOTION_INTEGRATION_ENABLED = os.environ.get('NOTION_INTEGRATION_ENABLED', 'true').lower() == 'true'
    NOTION_SYNC_INTERVAL = int(os.environ.get('NOTION_SYNC_INTERVAL', '300'))
    NOTION_MAX_RETRIES = int(os.environ.get('NOTION_MAX_RETRIES', '3'))
    NOTION_TIMEOUT = int(os.environ.get('NOTION_TIMEOUT', '30'))
    
    # Notion Database IDs
    NOTION_TASKS_DATABASE_ID = os.environ.get('NOTION_TASKS_DATABASE_ID', NOTION_DATABASE_ID)
    NOTION_EMPLOYEES_DATABASE_ID = os.environ.get('NOTION_EMPLOYEES_DATABASE_ID')
    NOTION_PROJECTS_DATABASE_ID = os.environ.get('NOTION_PROJECTS_DATABASE_ID')
    
    # =============================================================================
    # AGENT AI INTEGRATION
    # =============================================================================
    
    # Agent AI Backend Integration - Auto-adjusted based on environment
    AGENT_AI_URL = os.environ.get('AGENT_AI_URL') or _ENV_CONFIG['AGENT_AI_URL']
    AGENT_AI_API_KEY = os.environ.get('AGENT_AI_API_KEY', 'KSM_api_key_2ptybn')
    AGENT_AI_TIMEOUT = int(os.environ.get('AGENT_AI_TIMEOUT', '30'))
    
    # Integration Settings
    ENABLE_AGENT_AI_INTEGRATION = os.environ.get('ENABLE_AGENT_AI_INTEGRATION', 'true').lower() == 'true'
    AGENT_AI_FALLBACK_ENABLED = os.environ.get('AGENT_AI_FALLBACK_ENABLED', 'true').lower() == 'true'
    AGENT_AI_RETRY_COUNT = int(os.environ.get('AGENT_AI_RETRY_COUNT', '3'))
    
    # =============================================================================
    # CACHING CONFIGURATION
    # =============================================================================
    
    # Redis Cache - Auto-adjusted based on environment
    REDIS_ENABLED = os.environ.get('REDIS_ENABLED', 'false').lower() == 'true'
    REDIS_URL = os.environ.get('REDIS_URL') or _ENV_CONFIG['REDIS_URL']
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
    REDIS_TTL = int(os.environ.get('REDIS_TTL', '3600'))
    
    # Memory Cache
    MEMORY_CACHE_ENABLED = os.environ.get('MEMORY_CACHE_ENABLED', 'true').lower() == 'true'
    MEMORY_CACHE_SIZE = int(os.environ.get('MEMORY_CACHE_SIZE', '1000'))
    MEMORY_CACHE_TTL = int(os.environ.get('MEMORY_CACHE_TTL', '300'))
    
    # =============================================================================
    # SECURITY CONFIGURATION
    # =============================================================================
    
    # JWT Settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', '86400'))
    
    # API Authentication
    API_KEY_HEADER = os.environ.get('API_KEY_HEADER', 'X-API-Key')
    REQUIRE_API_KEY = os.environ.get('REQUIRE_API_KEY', 'true').lower() == 'true'
    API_KEY_WHITELIST = os.environ.get('API_KEY_WHITELIST', 'KSM_api_key_2ptybn,admin_key_123').split(',')
    
    # =============================================================================
    # DAILY TASK NOTIFICATION CONFIGURATION
    # =============================================================================
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_DEFAULT_CHAT_ID = os.environ.get('TELEGRAM_DEFAULT_CHAT_ID')
    ADMIN_ALERT_CHAT_ID = os.environ.get('ADMIN_ALERT_CHAT_ID')
    
    # Scheduler Configuration
    TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Jakarta')
    SCHEDULER_ENABLED = os.environ.get('SCHEDULER_ENABLED', 'true').lower() == 'true'
    DAILY_REPORT_TIME = os.environ.get('DAILY_REPORT_TIME', '17:00')  # Format: HH:MM
    
    # Report Configuration
    REPORT_ENABLED = os.environ.get('REPORT_ENABLED', 'true').lower() == 'true'
    REPORT_FREQUENCY = os.environ.get('REPORT_FREQUENCY', 'daily')  # daily, weekly, custom
    REPORT_WEEKDAYS_ONLY = os.environ.get('REPORT_WEEKDAYS_ONLY', 'true').lower() == 'true'
    
    # Agent AI Integration for Reports - Auto-adjusted based on environment
    AGENT_AI_BASE_URL = os.environ.get('AGENT_AI_BASE_URL') or _ENV_CONFIG['AGENT_AI_BASE_URL']
    AGENT_AI_REPORT_ENDPOINT = os.environ.get('AGENT_AI_REPORT_ENDPOINT', '/api/report/daily-task')
    
    # Error Handling
    ERROR_NOTIFICATION_ENABLED = os.environ.get('ERROR_NOTIFICATION_ENABLED', 'true').lower() == 'true'
    ERROR_NOTIFICATION_METHOD = os.environ.get('ERROR_NOTIFICATION_METHOD', 'telegram')  # telegram, email, both
    
    # =============================================================================
    # COMPANY CONFIGURATION
    # =============================================================================
    
    # Default Company ID
    DEFAULT_COMPANY_ID = os.environ.get('DEFAULT_COMPANY_ID', 'PT. Kian Santang Muliatama')
    
    # =============================================================================
    # FEATURE FLAGS
    # =============================================================================
    
    # Core Features
    ENABLE_KNOWLEDGE_BASE = os.environ.get('ENABLE_KNOWLEDGE_BASE', 'true').lower() == 'true'
    ENABLE_VECTOR_SEARCH = os.environ.get('ENABLE_VECTOR_SEARCH', 'true').lower() == 'true'
    ENABLE_DOCUMENT_UPLOAD = os.environ.get('ENABLE_DOCUMENT_UPLOAD', 'true').lower() == 'true'
    ENABLE_RAG_QUERY = os.environ.get('ENABLE_RAG_QUERY', 'true').lower() == 'true'
    
    # RAG Configuration (for compatibility)
    RAG_ENABLED = os.environ.get('RAG_ENABLED', 'true').lower() == 'true'
    
    # Advanced Features
    ENABLE_QDRANT = os.environ.get('ENABLE_QDRANT', 'true').lower() == 'true'
    ENABLE_EMBEDDINGS_CACHE = os.environ.get('ENABLE_EMBEDDINGS_CACHE', 'true').lower() == 'true'
    ENABLE_DOCUMENT_ANALYSIS = os.environ.get('ENABLE_DOCUMENT_ANALYSIS', 'true').lower() == 'true'
    ENABLE_SEMANTIC_SEARCH = os.environ.get('ENABLE_SEMANTIC_SEARCH', 'true').lower() == 'true'
    
    # Integration Features
    ENABLE_WEBHOOK_NOTIFICATIONS = os.environ.get('ENABLE_WEBHOOK_NOTIFICATIONS', 'true').lower() == 'true'
    ENABLE_BATCH_PROCESSING = os.environ.get('ENABLE_BATCH_PROCESSING', 'true').lower() == 'true'
    
    # =============================================================================
    # PERFORMANCE CONFIGURATION
    # =============================================================================
    
    # Database Pooling
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '10'))
    DB_POOL_OVERFLOW = int(os.environ.get('DB_POOL_OVERFLOW', '20'))
    DB_POOL_TIMEOUT = int(os.environ.get('DB_POOL_TIMEOUT', '30'))
    DB_POOL_RECYCLE = int(os.environ.get('DB_POOL_RECYCLE', '3600'))
    
    # Connection Settings
    DB_CONNECT_TIMEOUT = int(os.environ.get('DB_CONNECT_TIMEOUT', '10'))
    DB_READ_TIMEOUT = int(os.environ.get('DB_READ_TIMEOUT', '30'))
    DB_WRITE_TIMEOUT = int(os.environ.get('DB_WRITE_TIMEOUT', '30'))
    
    # =============================================================================
    # MONITORING & HEALTH CHECKS
    # =============================================================================
    
    # Health Check Settings
    HEALTH_CHECK_ENABLED = os.environ.get('HEALTH_CHECK_ENABLED', 'true').lower() == 'true'
    HEALTH_CHECK_INTERVAL = int(os.environ.get('HEALTH_CHECK_INTERVAL', '60'))
    HEALTH_CHECK_TIMEOUT = int(os.environ.get('HEALTH_CHECK_TIMEOUT', '10'))
    
    # Metrics
    METRICS_ENABLED = os.environ.get('METRICS_ENABLED', 'true').lower() == 'true'
    METRICS_PORT = int(os.environ.get('METRICS_PORT', '9091'))
    METRICS_PATH = os.environ.get('METRICS_PATH', '/metrics')
    
    # =============================================================================
    # FILE STORAGE CONFIGURATION
    # =============================================================================
    
    # File Storage
    FILE_STORAGE_PATH = os.environ.get('FILE_STORAGE_PATH', './uploads')
    MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', '10485760'))  # 10MB
    ALLOWED_EXTENSIONS = os.environ.get('ALLOWED_EXTENSIONS', 'pdf,txt,docx,md').split(',')
    
    # =============================================================================
    # GMAIL API CONFIGURATION
    # =============================================================================
    
    # Gmail OAuth 2.0 Configuration - Auto-adjusted based on environment
    GMAIL_CLIENT_ID = os.environ.get('GMAIL_CLIENT_ID')
    GMAIL_CLIENT_SECRET = os.environ.get('GMAIL_CLIENT_SECRET')
    GMAIL_REDIRECT_URI = os.environ.get('GMAIL_REDIRECT_URI') or _ENV_CONFIG['GMAIL_REDIRECT_URI']
    GMAIL_SCOPES = os.environ.get('GMAIL_SCOPES', 'https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/userinfo.profile')
    
    # Gmail API Configuration
    GMAIL_ENABLED = os.environ.get('GMAIL_ENABLED', 'true').lower() == 'true'
    GMAIL_TIMEOUT = int(os.environ.get('GMAIL_TIMEOUT', '30'))
    GMAIL_RETRY_ATTEMPTS = int(os.environ.get('GMAIL_RETRY_ATTEMPTS', '3'))
    
    # OAuth Library Configuration - Relax scope validation
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}?charset=utf8mb4"
    
    # Development specific settings
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}?charset=utf8mb4"
    
    # Production specific settings
    LOG_LEVEL = 'INFO'
    
    # Security settings
    REQUIRE_API_KEY = True
    RATE_LIMIT_ENABLED = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    
    # Testing specific settings
    LOG_LEVEL = 'WARNING'
    
    # Disable external services for testing
    ENABLE_AGENT_AI_INTEGRATION = False
    REDIS_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
