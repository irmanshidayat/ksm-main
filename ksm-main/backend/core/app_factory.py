#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
App Factory - Factory untuk membuat Flask application instance
"""

import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
import os
import logging
from datetime import datetime
from werkzeug.security import generate_password_hash
import threading
from collections import defaultdict
import gc

# Import SQLAlchemy dan Knowledge Base
from config.database import init_database, db
from config.models_init import init_models
from config.config import Config
from config.jwt_config import JWTConfig

# Import domain routes
from domains.auth.routes import register_auth_routes
from domains.vendor.routes import register_vendor_routes
from domains.knowledge.routes import register_knowledge_routes
from domains.notification.routes import register_notification_routes
from domains.inventory.routes import register_inventory_routes
from domains.email.routes import register_email_routes
from domains.attendance.routes import register_attendance_routes
from domains.task.routes import register_task_routes
from domains.role.routes import register_role_routes
from domains.monitoring.routes import register_monitoring_routes
from domains.integration.routes import register_integration_routes
from domains.mobil.routes import register_mobil_routes

# Setup logging early untuk error handling
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import other routes (legacy routes that haven't been migrated yet)
try:
    from shared.routes.debug_routes import debug_bp
except ImportError as e:
    logger.warning(f"Failed to import debug_routes: {e}. Creating empty blueprint.")
    debug_bp = Blueprint('debug', __name__)

try:
    from shared.routes.compatibility_routes import compatibility_bp
except ImportError as e:
    logger.warning(f"Failed to import compatibility_routes: {e}. Creating empty blueprint.")
    compatibility_bp = Blueprint('compatibility', __name__)
# notification_bp removed - now handled by domains.notification.routes
# service_routes_bp removed - now handled by domains.monitoring.routes (registered above)
# circuit_breaker_bp removed - now handled by domains.monitoring.routes (registered above)
# standalone_ai_bp removed - now handled by domains.knowledge.routes (registered above)
from domains.approval.routes import register_approval_routes
# mobil_bp removed - now handled by domains.mobil.routes (registered below)
# user_bp now registered via domains.auth.routes

# Import services
from domains.monitoring.services.unified_monitoring_service import get_monitoring_service
from shared.services.intelligent_cache_service import get_intelligent_cache_service
from domains.knowledge.services.advanced_context_builder import get_advanced_context_builder

# Import middlewares
from shared.middlewares.api_auth import jwt_required_custom
from shared.middlewares.error_handler import ErrorHandler

# Import utils
from shared.utils.notification_scheduler import start_notification_scheduler, stop_notification_scheduler


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Disable strict slashes to prevent redirects that break CORS preflight
    app.url_map.strict_slashes = False
    
    # Additional CORS configuration
    app.config['CORS_SUPPORTS_CREDENTIALS'] = True
    app.config['CORS_AUTOMATIC_OPTIONS'] = True
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # Initialize SocketIO dengan CORS support
    socketio = SocketIO(app, cors_allowed_origins=Config.CORS_ORIGINS)
    
    # Initialize database
    init_database(app)
    
    # Initialize models
    models = init_models()
    
    # Initialize Role Management Services
    try:
        with app.app_context():
            from domains.role.services.permission_service import permission_service
            from domains.role.services.workflow_service import workflow_service
            from shared.services.audit_trail_service import audit_service
            
            logger.info("[INIT] Initializing role management services...")
            permission_service.initialize_default_permissions()
            workflow_service.initialize_default_workflows()
            audit_service.initialize_audit_tables()
            logger.info("[SUCCESS] Role management services initialized successfully")
    except Exception as e:
        logger.error(f"[ERROR] Error initializing role management services: {e}")
    
    # Initialize JWT
    jwt = JWTManager(app)
    JWTConfig.init_app(app)
    
    # Initialize Services
    monitoring_service = get_monitoring_service()
    try:
        intelligent_cache_service = get_intelligent_cache_service()
        advanced_context_builder = get_advanced_context_builder()
    except Exception as e:
        logger.warning(f"Some services failed to initialize: {e}")
        intelligent_cache_service = None
        advanced_context_builder = None
    
    # Initialize Notification Service dengan SocketIO
    from domains.notification.services.notification_service import NotificationService
    notification_service = NotificationService(socketio)
    
    # Register WebSocket Events
    from domains.notification.routes import register_socket_events
    register_socket_events(socketio)
    
    # Configure CORS
    CORS(app, 
         origins=Config.CORS_ORIGINS,
         supports_credentials=True, 
         methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-API-Key", "Cache-Control", "Accept", "Origin", "X-Requested-With"],
         expose_headers=["Content-Type", "Authorization"],
         max_age=3600,
         automatic_options=True,
         send_wildcard=False,
         vary_header=True)
    
    logger.info(f"[CORS] Configuration loaded - Allowed origins: {Config.CORS_ORIGINS}")
    
    # Register domain routes
    register_auth_routes(app)
    register_vendor_routes(app)
    register_knowledge_routes(app)
    register_notification_routes(app)
    register_inventory_routes(app)
    register_email_routes(app)
    register_attendance_routes(app)
    register_task_routes(app)
    register_role_routes(app)
    register_monitoring_routes(app)
    register_integration_routes(app)
    
    # Register approval routes
    register_approval_routes(app)
    
    # Register mobil routes
    register_mobil_routes(app)
    
    # Register legacy routes (to be migrated later)
    app.register_blueprint(debug_bp)
    # notification_bp removed - now handled by domains.notification.routes (registered above)
    app.register_blueprint(compatibility_bp)
    # service_routes_bp removed - now handled by domains.monitoring.routes (registered above)
    # circuit_breaker_bp removed - now handled by domains.monitoring.routes (registered above)
    # standalone_ai_bp removed - now handled by domains.knowledge.routes (registered above)
    # gmail_bp removed - now handled by domains.auth.routes (registered above)
    # mobil_bp removed - now handled by domains.mobil.routes (registered above)
    # user_bp now registered via register_auth_routes above
    
    # Setup rate limiter
    rate_limiter = setup_rate_limiter()
    
    # Initialize database with default data
    init_unified_database(app, models)
    
    # Note: Notification scheduler will be started in app.py main block
    # to avoid starting it multiple times during testing
    
    return app, socketio


def setup_rate_limiter():
    """Setup rate limiter"""
    class OptimizedRateLimiter:
        def __init__(self, max_cache_size=1000):
            self.requests = defaultdict(list)
            self.lock = threading.Lock()
            self.cache = {}
            self.cache_lock = threading.Lock()
            self.max_cache_size = max_cache_size
            self._cleanup_counter = 0
        
        def is_allowed(self, client_ip: str, max_requests: int = 100, window: int = 60) -> bool:
            """Rate limiting dengan cleanup otomatis"""
            current_time = datetime.now().timestamp()
            
            with self.lock:
                self.requests[client_ip] = [
                    req_time for req_time in self.requests[client_ip]
                    if current_time - req_time < window
                ]
                
                current_count = len(self.requests[client_ip])
                
                if current_count >= max_requests:
                    return False
                
                self.requests[client_ip].append(current_time)
                
                self._cleanup_counter += 1
                if self._cleanup_counter >= 100:
                    self._cleanup_old_ips(current_time, window)
                    self._cleanup_counter = 0
                
                return True
        
        def _cleanup_old_ips(self, current_time, window):
            """Cleanup IPs yang tidak aktif"""
            expired_ips = []
            for ip, requests in self.requests.items():
                if not requests or (current_time - max(requests)) > window * 2:
                    expired_ips.append(ip)
            
            for ip in expired_ips:
                del self.requests[ip]
    
    return OptimizedRateLimiter(max_cache_size=500)


def init_unified_database(app, models):
    """Initialize database with default data"""
    with app.app_context():
        try:
            # Test database connection
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text('SELECT 1'))
                logger.info("Database connection successful")
            except Exception as conn_error:
                logger.warning(f"Database connection failed: {conn_error}")
                return
            
            # Create all tables
            try:
                db.create_all()
            except Exception as create_error:
                logger.warning(f"Some tables may not exist yet: {create_error}")
                try:
                    from scripts.create_all_mobil_tables import create_all_mobil_tables
                    create_all_mobil_tables()
                except Exception as mobil_error:
                    logger.warning(f"Could not create mobil tables: {mobil_error}")
            
            # Insert default admin user if not exists
            if not models['knowledge_base']['User'].query.filter_by(username='admin').first():
                admin_password = generate_password_hash('admin123')
                admin_user = models['knowledge_base']['User'](
                    username='admin',
                    password_hash=admin_password,
                    email='admin@KSM.com',
                    role='admin'
                )
                db.session.add(admin_user)
                db.session.commit()
            
            # Insert default telegram settings if not exists
            if not models['knowledge_base']['TelegramSettings'].query.filter_by(company_id='PT. Kian Santang Muliatama').first():
                telegram_settings = models['knowledge_base']['TelegramSettings'](
                    bot_token='',
                    is_active=False,
                    company_id='PT. Kian Santang Muliatama'
                )
                db.session.add(telegram_settings)
                db.session.commit()
            
            # Insert default categories if not exists
            if not models['knowledge_base']['KnowledgeCategory'].query.first():
                default_categories = [
                    {'name': 'HR', 'description': 'Human Resources'},
                    {'name': 'Finance', 'description': 'Keuangan dan Akuntansi'},
                    {'name': 'Marketing', 'description': 'Pemasaran dan Penjualan'},
                    {'name': 'Technical', 'description': 'Teknis dan IT'},
                    {'name': 'Legal', 'description': 'Hukum dan Legal'},
                    {'name': 'Operations', 'description': 'Operasional'}
                ]
                
                for cat_data in default_categories:
                    category = models['knowledge_base']['KnowledgeCategory'](**cat_data)
                    db.session.add(category)
                
                db.session.commit()
            
            # Insert default tags if not exists
            if not models['knowledge_base']['KnowledgeTag'].query.first():
                default_tags = [
                    {'name': 'Panduan', 'color': '#28a745'},
                    {'name': 'SOP', 'color': '#007bff'},
                    {'name': 'Kebijakan', 'color': '#dc3545'},
                    {'name': 'Template', 'color': '#ffc107'},
                    {'name': 'Laporan', 'color': '#6f42c1'},
                    {'name': 'Manual', 'color': '#17a2b8'}
                ]
                
                for tag_data in default_tags:
                    tag = models['knowledge_base']['KnowledgeTag'](**tag_data)
                    db.session.add(tag)
                
                db.session.commit()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            db.session.rollback()
            
            if "Can't connect to MySQL server" in str(e) or "Access denied" in str(e):
                logger.warning("Database tidak tersedia, aplikasi akan berjalan tanpa database")
            else:
                logger.error(f"Database error: {e}")
        finally:
            gc.collect()

