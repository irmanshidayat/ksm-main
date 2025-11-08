#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KSM Main Backend - Versi Optimasi Sederhana untuk Mengurangi Penggunaan Memori
"""

import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
import requests
import os
import logging
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import threading
from collections import defaultdict
import gc

# Import SQLAlchemy dan Knowledge Base
from config.database import init_database, db
from config.models_init import init_models

from controllers.knowledge_base_controller import knowledge_base_bp
from controllers.knowledge_ai_controller import knowledge_ai_bp
from controllers.qdrant_knowledge_base_controller import qdrant_kb_bp
from controllers.auth_controller import auth_bp
from controllers.unified_notion_controller import unified_notion_bp, database_discovery_bp
# Enhanced Notion endpoints now consolidated in unified_notion_controller
from controllers.telegram_controller import telegram_bp
from controllers.stok_barang_controller import stok_barang_bp
# REMOVED: unified_rag_controller - functionality consolidated into qdrant_knowledge_base_controller

# monitoring_controller dihapus - digantikan oleh unified_monitoring_controller
from controllers.unified_monitoring_controller import unified_monitoring_bp
# rag_documents_controller dihapus - digantikan oleh unified_rag_controller
# Import unified health controller (replaces all scattered health check endpoints)
from controllers.unified_health_controller import unified_health_bp
from routes.standalone_ai_routes import standalone_ai_bp
# REMOVED: vector_routes - functionality consolidated into qdrant_knowledge_base_controller
from routes.service_routes import service_routes_bp
# health_routes dihapus - digantikan oleh unified_health_controller
from routes.debug_routes import debug_bp
from routes.notification_routes import notification_bp
from routes.notifications_routes import notifications_bp
from routes.role_management_routes import role_management_bp
from routes.permission_routes import permission_bp
from routes.approval_routes import approval_bp
from routes.gmail_routes import gmail_bp
from routes.mobil_routes import mobil_bp
from controllers.request_pembelian_controller import request_pembelian_bp
from controllers.vendor_selection_controller import vendor_selection_bp
from controllers.analysis_controller import analysis_bp
from controllers.vendor_crud_controller import vendor_crud_bp
from controllers.vendor_upload_controller import vendor_upload_bp
from controllers.vendor_dashboard_controller import vendor_dashboard_bp
from controllers.vendor_penawaran_controller import vendor_penawaran_bp
from controllers.vendor_catalog_controller import vendor_catalog_bp
from controllers.vendor_auth_controller import vendor_auth_bp
from controllers.vendor_order_controller import vendor_order_bp
from controllers.vendor_debug_controller import vendor_debug_bp
from controllers.vendor_bulk_import_controller import vendor_bulk_import_bp
from controllers.vendor_catalog_bulk_import_controller import vendor_catalog_bulk_import_bp
from controllers.vendor_approval_controller import vendor_approval_bp
from controllers.email_controller import email_bp
from controllers.email_domain_controller import email_domain_bp
from controllers.user_controller import user_bp
from controllers.attendance_controller import attendance_bp
from routes.daily_task_routes import daily_task_bp
from routes.remind_exp_docs_routes import remind_exp_docs_bp
from utils.notification_scheduler import start_notification_scheduler, stop_notification_scheduler
from config.jwt_config import JWTConfig
from middlewares.api_auth import jwt_required_custom
from middlewares.error_handler import ErrorHandler

# Import new services
from services.unified_monitoring_service import get_monitoring_service
# REMOVED: hybrid_search_service - redundant with Agent AI
# from services.hybrid_search_service import get_hybrid_search_service
from services.intelligent_cache_service import get_intelligent_cache_service
from services.advanced_context_builder import get_advanced_context_builder

# Setup logging dengan level yang lebih rendah untuk menghemat memori
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Disable strict slashes to prevent redirects that break CORS preflight
app.url_map.strict_slashes = False

# Additional CORS configuration to handle redirects
app.config['CORS_SUPPORTS_CREDENTIALS'] = True
app.config['CORS_AUTOMATIC_OPTIONS'] = True

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}

# Additional configuration for multipart/form-data handling
app.config['WTF_CSRF_ENABLED'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Import Config terlebih dahulu untuk CORS configuration
from config.config import Config

# Initialize SocketIO dengan CORS support menggunakan Config
socketio = SocketIO(app, cors_allowed_origins=Config.CORS_ORIGINS)

# Initialize database first
init_database(app)

# Initialize models after database is ready
models = init_models()

# Initialize Role Management Services within app context
try:
    with app.app_context():
        from services.permission_service import permission_service
        from services.workflow_service import workflow_service
        from services.audit_service import audit_service
        
        logger.info("[INIT] Initializing role management services...")
        permission_service.initialize_default_permissions()
        workflow_service.initialize_default_workflows()
        audit_service.initialize_audit_tables()
        logger.info("[SUCCESS] Role management services initialized successfully")
except Exception as e:
    logger.error(f"[ERROR] Error initializing role management services: {e}")
    # Continue without role management services if they fail

# Initialize JWT
jwt = JWTManager(app)
JWTConfig.init_app(app)

# Initialize Error Handler
# error_handler = ErrorHandler(app)  # Temporarily disabled for debugging

# Initialize Services
monitoring_service = get_monitoring_service()
# REMOVED: hybrid_search_service - redundant with Agent AI
# hybrid_search_service = get_hybrid_search_service()
intelligent_cache_service = get_intelligent_cache_service()
advanced_context_builder = get_advanced_context_builder()

# Initialize Notification Service dengan SocketIO
from services.notification_service import NotificationService
notification_service = NotificationService(socketio)

# Register WebSocket Events
from routes.notification_routes import register_socket_events
register_socket_events(socketio)

# Konfigurasi CORS yang benar - menggunakan konfigurasi dari config.py

CORS(app, 
     origins=Config.CORS_ORIGINS,  # Menggunakan konfigurasi dari Config yang auto-detect environment
     supports_credentials=True, 
     methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-API-Key", "Cache-Control", "Accept", "Origin", "X-Requested-With"],
     expose_headers=["Content-Type", "Authorization"],
     max_age=3600,
     automatic_options=True,
     send_wildcard=False,
     # Additional configuration for multipart/form-data
     vary_header=True)

# Log CORS configuration saat startup
logger.info(f"🌐 CORS Configuration loaded - Allowed origins: {Config.CORS_ORIGINS}")

# Configuration
AGENT_AI_URL = os.getenv('AGENT_AI_URL', 'http://localhost:5001')
API_KEY = os.getenv('AGENT_AI_API_KEY', 'KSM_api_key_2ptybn')

# Optimized Rate Limiter dengan memory management
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
            # Clean expired requests
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < window
            ]
            
            current_count = len(self.requests[client_ip])
            
            if current_count >= max_requests:
                return False
            
            self.requests[client_ip].append(current_time)
            
            # Cleanup old IPs periodically
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
    
    def get_cached_data(self, key: str, cache_duration: int = 60):
        """Get cached data dengan size limit"""
        current_time = datetime.now().timestamp()
        
        with self.cache_lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if current_time - timestamp < cache_duration:
                    return data
                else:
                    del self.cache[key]
            return None
    
    def set_cached_data(self, key: str, data):
        """Set cached data dengan size limit"""
        with self.cache_lock:
            # Cleanup jika cache terlalu besar
            if len(self.cache) >= self.max_cache_size:
                # Remove oldest entries
                oldest_keys = sorted(self.cache.keys(), 
                                   key=lambda k: self.cache[k][1])[:self.max_cache_size//2]
                for old_key in oldest_keys:
                    del self.cache[old_key]
            
            self.cache[key] = (data, datetime.now().timestamp())

# Global instances dengan memory management
rate_limiter = OptimizedRateLimiter(max_cache_size=500)

# Global CORS handler untuk semua requests - ENABLED untuk memastikan CORS bekerja
@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    origin = request.headers.get('Origin')
    # Debug logging untuk CORS - gunakan INFO level untuk visibility
    logger.info(f"🔍 CORS after_request - Origin: {origin}, Allowed origins: {Config.CORS_ORIGINS}")
    logger.info(f"🔍 CORS check - origin in list: {origin in Config.CORS_ORIGINS if origin else False}")
    
    # Gunakan Config.CORS_ORIGINS yang sudah auto-detect environment
    if origin and origin in Config.CORS_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        logger.debug(f"✅ CORS allowed for origin: {origin}")
    elif Config.CORS_ORIGINS:
        # Fallback ke origin pertama jika origin tidak ada di list
        response.headers['Access-Control-Allow-Origin'] = Config.CORS_ORIGINS[0]
        logger.debug(f"⚠️ CORS origin {origin} not in allowed list, using fallback: {Config.CORS_ORIGINS[0]}")
    else:
        # Fallback terakhir
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3002'
        logger.debug(f"⚠️ CORS_ORIGINS empty, using hardcoded fallback")
    
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key, Cache-Control, Accept, Origin, X-Requested-With'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

@app.before_request
def handle_preflight():
    """Handle preflight OPTIONS request untuk CORS"""
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        origin = request.headers.get('Origin')
        # Debug logging untuk CORS preflight - gunakan INFO level untuk visibility
        logger.info(f"🔍 CORS preflight - Origin: {origin}, Allowed origins: {Config.CORS_ORIGINS}")
        logger.info(f"🔍 CORS preflight check - origin in list: {origin in Config.CORS_ORIGINS if origin else False}")
        
        # Gunakan Config.CORS_ORIGINS yang sudah auto-detect environment
        if origin and origin in Config.CORS_ORIGINS:
            response.headers['Access-Control-Allow-Origin'] = origin
            logger.debug(f"✅ CORS preflight allowed for origin: {origin}")
        elif Config.CORS_ORIGINS:
            # Fallback ke origin pertama jika origin tidak ada di list
            response.headers['Access-Control-Allow-Origin'] = Config.CORS_ORIGINS[0]
            logger.debug(f"⚠️ CORS preflight origin {origin} not in allowed list, using fallback: {Config.CORS_ORIGINS[0]}")
        else:
            # Fallback terakhir
            response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3002'
            logger.debug(f"⚠️ CORS_ORIGINS empty in preflight, using hardcoded fallback")
        
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key, Cache-Control, Accept, Origin, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response

@app.before_request
def debug_request():
    """Debug request untuk file upload"""
    if request.method == 'POST' and 'multipart/form-data' in request.content_type:
        logger.info(f"🔍 Multipart request detected: {request.endpoint}")
        logger.info(f"🔍 Content-Type: {request.content_type}")
        logger.info(f"🔍 Files: {list(request.files.keys())}")
        logger.info(f"🔍 Form: {list(request.form.keys())}")

# Unified database initialization
def init_unified_database():
    """Single database initialization untuk menghemat memori"""
    with app.app_context():
        try:
            # Test database connection first
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
                # Try to create mobil tables manually if they don't exist
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
            
            # Jika database tidak tersedia, log warning tapi jangan crash
            if "Can't connect to MySQL server" in str(e) or "Access denied" in str(e):
                logger.warning("Database tidak tersedia, aplikasi akan berjalan tanpa database")
            else:
                logger.error(f"Database error: {e}")
        finally:
            # Force garbage collection
            gc.collect()

# Authentication middleware yang dioptimasi
def require_auth(f):
    """Decorator untuk authentication dengan memory optimization"""
    def decorated_function(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        
        # Skip authentication for OPTIONS requests
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
        
        try:
            # Verify JWT token
            verify_jwt_in_request()
            
            # Get current user
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return jsonify({'error': 'Invalid token'}), 401
            
            # Check rate limiting
            client_ip = request.remote_addr
            if not rate_limiter.is_allowed(client_ip, max_requests=200, window=60):
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.warning(f"Authentication error: {e}")
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function

# Simple memory monitoring endpoint tanpa psutil
@app.route('/api/memory-status', methods=['GET'])
def memory_status():
    """Endpoint untuk monitoring penggunaan memori sederhana"""
    try:
        # Simple memory estimation tanpa psutil
        import sys
        import gc
        
        # Get garbage collection stats
        gc.collect()
        gc_stats = gc.get_stats()
        
        # Estimate memory usage
        memory_estimate = len(gc.get_objects()) * 64  # Rough estimate
        
        return jsonify({
            'success': True,
            'memory_usage_mb': round(memory_estimate / 1024 / 1024, 2),
            'memory_percent': round((memory_estimate / (8 * 1024 * 1024 * 1024)) * 100, 2),  # Assuming 8GB RAM
            'cpu_percent': 0,  # Not available without psutil
            'gc_objects': len(gc.get_objects()),
            'gc_stats': gc_stats,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Memory monitoring error: {str(e)}'
        }), 500

# Health check endpoint dihapus - sekarang menggunakan unified_health_controller

# Metrics endpoint alias untuk kompatibilitas frontend (didefinisikan sebelum blueprint untuk memastikan terdaftar)
@app.route('/api/metrics', methods=['GET'])
def get_metrics_alias():
    """Alias endpoint untuk /api/metrics yang redirect ke monitoring service"""
    try:
        # Get window parameter
        window_minutes = request.args.get('window', 60, type=int)
        
        metrics = monitoring_service.get_metrics()
        
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"❌ Failed to get metrics: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Register blueprints
app.register_blueprint(knowledge_base_bp, url_prefix='/api/knowledge-base')
# CONSOLIDATED: qdrant_knowledge_base_controller now includes all RAG functionality
app.register_blueprint(qdrant_kb_bp, url_prefix='/api/qdrant-knowledge-base')
# REMOVED: unified_rag_bp - functionality consolidated into qdrant_kb_bp
# REMOVED: vector_bp - functionality consolidated into qdrant_kb_bp
app.register_blueprint(knowledge_ai_bp)
app.register_blueprint(auth_bp, url_prefix='/api')  # Register auth_bp with /api prefix to fix /refresh endpoint
app.register_blueprint(unified_notion_bp)
app.register_blueprint(database_discovery_bp)  # Database Discovery routes untuk kompatibilitas frontend
# Enhanced Notion endpoints now consolidated in unified_notion_controller
app.register_blueprint(telegram_bp)
app.register_blueprint(stok_barang_bp, url_prefix='/api/stok-barang')
# Enhanced RAG controller replaced by qdrant_kb_bp above
# monitoring_bp dihapus - digantikan oleh unified_monitoring_bp
app.register_blueprint(unified_monitoring_bp, url_prefix='/api/monitoring')
app.register_blueprint(standalone_ai_bp)
app.register_blueprint(service_routes_bp)  # Service Routes
# Unified Health Controller replaces all scattered health check endpoints
app.register_blueprint(unified_health_bp, url_prefix='/api')
# health_bp dihapus - digantikan oleh unified_health_bp
app.register_blueprint(debug_bp)  # Debug Routes
app.register_blueprint(notification_bp)  # Notification Routes
app.register_blueprint(notifications_bp)  # Daily Task Notifications Routes
app.register_blueprint(role_management_bp)  # Role Management Routes
app.register_blueprint(permission_bp, url_prefix='/api/permission-management')  # Permission Management Routes
# Register approval blueprint dengan error handling yang lebih baik
try:
    # Verify blueprint is importable
    logger.info(f"📦 Attempting to register approval_bp...")
    logger.info(f"   Blueprint name: {approval_bp.name}")
    logger.info(f"   Blueprint URL prefix: {approval_bp.url_prefix}")
    
    # Count routes before registration
    routes_before = len(list(app.url_map.iter_rules()))
    
    # Register blueprint
    app.register_blueprint(approval_bp)
    
    # Count routes after registration
    routes_after = len(list(app.url_map.iter_rules()))
    routes_added = routes_after - routes_before
    
    logger.info(f"✅ Successfully registered approval_bp blueprint")
    logger.info(f"   Routes before: {routes_before}, Routes after: {routes_after}, Added: {routes_added}")
    
    # Get all approval routes
    approval_routes = []
    for rule in app.url_map.iter_rules():
        if 'approval' in str(rule).lower() or 'approval' in rule.endpoint.lower():
            approval_routes.append({
                'endpoint': rule.endpoint,
                'rule': str(rule),
                'methods': list(rule.methods)
            })
    
    logger.info(f"📋 Found {len(approval_routes)} approval-related routes:")
    for route in approval_routes[:15]:  # Log first 15 routes
        logger.info(f"   - {route['rule']} [{', '.join(route['methods'])}]")
    
    if len(approval_routes) == 0:
        logger.error(f"❌ WARNING: No approval routes found after registration!")
        logger.error(f"   This means the blueprint was registered but no routes were added.")
        logger.error(f"   Check if routes are properly decorated with @approval_bp.route()")
        
except Exception as e:
    logger.error(f"❌ CRITICAL: Failed to register approval_bp: {e}")
    import traceback
    logger.error(traceback.format_exc())
    # Continue execution even if approval_bp fails
    # Register fallback routes directly in app if blueprint fails
    logger.warning("⚠️ Registering fallback approval routes directly in app...")
    
    @app.route('/api/approval/requests', methods=['GET'])
    @jwt_required_custom
    def fallback_get_approval_requests():
        """Fallback endpoint for approval requests"""
        try:
            from flask_jwt_extended import get_jwt_identity
            models = init_models()
            ApprovalRequest = models['approval']['ApprovalRequest']
            
            user_id = get_jwt_identity()
            if not user_id:
                return APIResponse.unauthorized("User not authenticated")
            
            limit = min(request.args.get('limit', 50, type=int), 100)
            offset = request.args.get('offset', 0, type=int)
            
            query = ApprovalRequest.query.order_by(ApprovalRequest.created_at.desc())
            total_count = query.count()
            requests = query.offset(offset).limit(limit).all()
            requests_data = [req.to_dict() for req in requests]
            
            return APIResponse.success(
                data=requests_data,
                message="Approval requests retrieved successfully",
                total=total_count
            )
        except Exception as e:
            logging.error(f"Error getting approval requests: {e}")
            return APIResponse.error("Failed to get approval requests")
    
    @app.route('/api/approval/stats', methods=['GET'])
    @jwt_required_custom
    def fallback_get_approval_stats():
        """Fallback endpoint for approval stats"""
        try:
            from flask_jwt_extended import get_jwt_identity
            models = init_models()
            ApprovalRequest = models['approval']['ApprovalRequest']
            
            user_id = get_jwt_identity()
            if not user_id:
                return APIResponse.unauthorized("User not authenticated")
            
            stats = {
                'pending_approvals': ApprovalRequest.query.filter_by(status='pending').count(),
                'my_requests': ApprovalRequest.query.filter_by(requester_id=user_id).count(),
                'approved_requests': ApprovalRequest.query.filter_by(requester_id=user_id, status='approved').count(),
                'rejected_requests': ApprovalRequest.query.filter_by(requester_id=user_id, status='rejected').count()
            }
            
            return APIResponse.success(
                data=stats,
                message="Approval statistics retrieved successfully"
            )
        except Exception as e:
            logging.error(f"Error getting approval stats: {e}")
            return APIResponse.error("Failed to get approval statistics")
    
    logger.info("✅ Fallback approval routes registered directly in app")

# Always register fallback approval routes as backup (even if blueprint succeeds)
# This ensures endpoints are always available
from utils.response_standardizer import APIResponse

@app.route('/api/approval/requests', methods=['GET'])
@app.route('/api/approval/requests-backup', methods=['GET'])  # Backup route
@jwt_required_custom
def backup_get_approval_requests():
    """Backup endpoint for approval requests - always available"""
    try:
        from flask_jwt_extended import get_jwt_identity
        models = init_models()
        ApprovalRequest = models['approval']['ApprovalRequest']
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        query = ApprovalRequest.query.order_by(ApprovalRequest.created_at.desc())
        total_count = query.count()
        requests = query.offset(offset).limit(limit).all()
        requests_data = [req.to_dict() for req in requests]
        
        return APIResponse.success(
            data=requests_data,
            message="Approval requests retrieved successfully",
            total=total_count
        )
    except Exception as e:
        logging.error(f"Error getting approval requests: {e}")
        return APIResponse.error("Failed to get approval requests")

@app.route('/api/approval/stats', methods=['GET'])
@app.route('/api/approval/stats-backup', methods=['GET'])  # Backup route
@jwt_required_custom
def backup_get_approval_stats():
    """Backup endpoint for approval stats - always available"""
    try:
        from flask_jwt_extended import get_jwt_identity
        models = init_models()
        ApprovalRequest = models['approval']['ApprovalRequest']
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        
        stats = {
            'pending_approvals': ApprovalRequest.query.filter_by(status='pending').count(),
            'my_requests': ApprovalRequest.query.filter_by(requester_id=user_id).count(),
            'approved_requests': ApprovalRequest.query.filter_by(requester_id=user_id, status='approved').count(),
            'rejected_requests': ApprovalRequest.query.filter_by(requester_id=user_id, status='rejected').count()
        }
        
        return APIResponse.success(
            data=stats,
            message="Approval statistics retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting approval stats: {e}")
        return APIResponse.error("Failed to get approval statistics")

logger.info("✅ Backup approval routes registered directly in app (always available)")

app.register_blueprint(gmail_bp)  # Gmail API Routes
app.register_blueprint(mobil_bp)  # Mobil Management Routes
app.register_blueprint(request_pembelian_bp, url_prefix='/api/request-pembelian')  # Request Pembelian Routes
app.register_blueprint(vendor_selection_bp, url_prefix='/api/vendor-selection')  # Vendor Selection Routes
app.register_blueprint(analysis_bp, url_prefix='/api/analysis')  # Analysis Routes
app.register_blueprint(vendor_crud_bp, url_prefix='/api/vendor')  # Vendor CRUD Routes
app.register_blueprint(vendor_upload_bp, url_prefix='/api/vendor')  # Vendor Upload Routes
# Vendor Dashboard Routes - harus terdaftar sebelum vendor_auth_bp untuk menghindari konflik
app.register_blueprint(vendor_dashboard_bp, url_prefix='/api/vendor')  # Vendor Dashboard Routes
logger.info(f"✅ Registered vendor_dashboard_bp with url_prefix='/api/vendor'")
# Log semua routes vendor setelah registrasi vendor_dashboard_bp
all_vendor_routes = [rule for rule in app.url_map.iter_rules() if '/api/vendor' in rule.rule]
vendor_dashboard_routes = [rule for rule in all_vendor_routes if 'vendor_dashboard' in rule.endpoint]
logger.info(f"   Total vendor routes after vendor_dashboard_bp: {len(all_vendor_routes)}")
if vendor_dashboard_routes:
    logger.info(f"   Found {len(vendor_dashboard_routes)} vendor_dashboard routes:")
    for rule in vendor_dashboard_routes[:5]:  # Log first 5 routes
        logger.info(f"   - {rule.rule} [{', '.join(rule.methods)}] endpoint: {rule.endpoint}")
    # Cek khusus route /dashboard
    dashboard_routes = [r for r in vendor_dashboard_routes if '/dashboard' in r.rule]
    if dashboard_routes:
        logger.info(f"   ✅ Found /dashboard route: {dashboard_routes[0].rule}")
    else:
        logger.error(f"   ❌ /dashboard route NOT FOUND in vendor_dashboard routes!")
else:
    logger.warning(f"   ⚠️ No vendor_dashboard routes found after registration!")

app.register_blueprint(vendor_penawaran_bp, url_prefix='/api/vendor')  # Vendor Penawaran Routes
app.register_blueprint(vendor_catalog_bp, url_prefix='/api/vendor-catalog')  # Vendor Catalog Routes
app.register_blueprint(vendor_auth_bp)  # Vendor Authentication Routes (sudah punya url_prefix='/api/vendor' di definisi)
app.register_blueprint(vendor_order_bp)  # Vendor Order Routes
app.register_blueprint(vendor_debug_bp, url_prefix='/api/vendor')  # Vendor Debug Routes
app.register_blueprint(vendor_bulk_import_bp)  # Vendor Bulk Import Routes
app.register_blueprint(vendor_catalog_bulk_import_bp)  # Vendor Catalog Bulk Import Routes
app.register_blueprint(vendor_approval_bp, url_prefix='/api/vendor-approval')  # Vendor Approval Routes
app.register_blueprint(email_bp, url_prefix='/api/email')  # Email Routes
app.register_blueprint(email_domain_bp, url_prefix='')  # Email Domain Routes
app.register_blueprint(user_bp)  # Users Routes
app.register_blueprint(attendance_bp)  # Attendance Routes
app.register_blueprint(daily_task_bp)  # Daily Task Routes
app.register_blueprint(remind_exp_docs_bp)  # Remind Exp Docs Routes

# Agent AI Integration Endpoints
@app.route('/api/agent-ai/status', methods=['GET'])
def agent_ai_status():
    """Check Agent AI integration status"""
    try:
        status = monitoring_service.get_agent_ai_status()
        return jsonify({
            'success': True,
            'message': 'Agent AI status retrieved successfully',
            'data': status,
            'status_code': 200
        })
    except Exception as e:
        logger.error(f"Agent AI status check failed: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get Agent AI status',
            'error': str(e),
            'status_code': 500
        }), 500

# ===== Compatibility aliases for attendance tasks stats without /api prefix =====
@app.route('/attendance/tasks/statistics', methods=['GET'])
def compat_attendance_tasks_statistics():
    try:
        from controllers.daily_task_controller import DailyTaskController
        controller = DailyTaskController()
        return controller.get_statistics()
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to route statistics',
            'error': str(e)
        }), 500

@app.route('/attendance/tasks/department-stats', methods=['GET'])
def compat_attendance_tasks_department_stats():
    try:
        return jsonify({
            'success': True,
            'data': []
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to route department stats',
            'error': str(e)
        }), 500

@app.route('/attendance/tasks/user-stats', methods=['GET'])
def compat_attendance_tasks_user_stats():
    try:
        return jsonify({
            'success': True,
            'data': []
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to route user stats',
            'error': str(e)
        }), 500

@app.route('/api/agent/status', methods=['GET'])
def agent_status_endpoint():
    """Agent status endpoint untuk frontend compatibility"""
    try:
        # Try to get Agent AI status through monitoring service
        try:
            agent_ai_status = monitoring_service.get_agent_ai_status()
            
            # Format response untuk compatibility dengan frontend
            if agent_ai_status.get('status') == 'connected':
                status_data = {
                    'service': 'Agent AI',
                    'status': 'healthy',
                    'version': '1.0.0',
                    'timestamp': datetime.now().isoformat(),
                    'agents': {
                        'total': 1,
                        'active': 1,
                        'inactive': 0
                    },
                    'database': 'connected',
                    'ai_services': 'operational',
                    'integration': {
                        'KSM_main': 'connected',
                        'response_time': agent_ai_status.get('response_time', 0)
                    }
                }
                
                # Try to get agent information from Agent AI
                try:
                    agent_data = agent_ai_status.get('data', {})
                    if agent_data:
                        status_data.update({
                            'model': agent_data.get('model', 'unknown'),
                            'provider': agent_data.get('provider', 'unknown'),
                            'uptime': agent_data.get('uptime', 0)
                        })
                except Exception as e:
                    logger.warning(f"Could not extract agent data: {e}")
                
                return jsonify({
                    'success': True,
                    'message': 'Agent status retrieved successfully',
                    'data': status_data,
                    'status_code': 200
                })
            else:
                # Agent AI is not connected, return mock data
                return jsonify({
                    'success': True,
                    'message': 'Agent AI status (mock)',
                    'data': {
                        'service': 'Agent AI',
                        'status': 'healthy',
                        'version': '1.0.0',
                        'timestamp': datetime.now().isoformat(),
                        'agents': {
                            'total': 1,
                            'active': 1,
                            'inactive': 0
                        },
                        'database': 'connected',
                        'ai_services': 'operational',
                        'integration': {
                            'KSM_main': 'connected',
                            'response_time': 0.1
                        },
                        'model': 'gpt-4o-mini',
                        'provider': 'openai',
                        'uptime': 3600
                    },
                    'status_code': 200
                })
                
        except Exception as monitoring_error:
            logger.warning(f"Monitoring service error: {monitoring_error}")
            # Return mock data if monitoring service fails
            return jsonify({
                'success': True,
                'message': 'Agent AI status (mock - monitoring service unavailable)',
                'data': {
                    'service': 'Agent AI',
                    'status': 'healthy',
                    'version': '1.0.0',
                    'timestamp': datetime.now().isoformat(),
                    'agents': {
                        'total': 1,
                        'active': 1,
                        'inactive': 0
                    },
                    'database': 'connected',
                    'ai_services': 'operational',
                    'integration': {
                        'KSM_main': 'connected',
                        'response_time': 0.1
                    },
                    'model': 'gpt-4o-mini',
                    'provider': 'openai',
                    'uptime': 3600
                },
                'status_code': 200
            })
            
    except Exception as e:
        logger.error(f"Agent status endpoint failed: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get agent status',
            'error': str(e),
            'data': {
                'service': 'Agent AI',
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            },
            'status_code': 500
        }), 500

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint"""
    try:
        return jsonify({
            'success': True,
            'message': 'Backend is running',
            'timestamp': datetime.now().isoformat(),
            'status': 'OK'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-agent', methods=['GET'])
def test_agent_endpoint():
    """Test Agent AI connection"""
    try:
        agent_ai_status = monitoring_service.get_agent_ai_status()
        return jsonify({
            'success': True,
            'message': 'Agent AI test result',
            'agent_ai_status': agent_ai_status,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Agent AI test failed',
            'error': str(e)
        }), 500

@app.route('/api/cors-test', methods=['GET', 'POST', 'OPTIONS'])
def cors_test_endpoint():
    """CORS test endpoint untuk debugging"""
    if request.method == 'OPTIONS':
        logger.info("CORS preflight request received")
        return '', 200
    
    try:
        return jsonify({
            'success': True,
            'message': 'CORS test successful',
            'method': request.method,
            'origin': request.headers.get('Origin'),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users-test', methods=['GET', 'OPTIONS'])
def users_test_endpoint():
    """Test endpoint untuk users tanpa authentication"""
    if request.method == 'OPTIONS':
        logger.info("Users test OPTIONS request received")
        return '', 200
    
    try:
        return jsonify({
            'success': True,
            'message': 'Users test endpoint accessible',
            'method': request.method,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users-new/<int:user_id>', methods=['DELETE', 'OPTIONS'])
def users_new_delete(user_id: int):
    """Compatibility DELETE endpoint for users-new to perform soft delete"""
    try:
        if request.method == 'OPTIONS':
            logger.info(f"[USERS-NEW][OPTIONS] /api/users-new/{user_id}")
            return '', 200

        logger.info(f"[USERS-NEW][DELETE] Start user_id={user_id}")

        # Import models
        from models.knowledge_base import User
        from config.database import db

        user = User.query.get(user_id)
        if not user:
            logger.warning(f"[USERS-NEW][DELETE] User {user_id} tidak ditemukan")
            return jsonify({'success': False, 'error': 'User tidak ditemukan'}), 404

        # Soft delete
        user.is_active = False
        db.session.commit()
        logger.info(f"[USERS-NEW][DELETE] Success user_id={user_id}")
        return ('', 204)
    except Exception as e:
        logger.error(f"[USERS-NEW][DELETE] Error: {e}")
        try:
            from config.database import db
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'success': False, 'error': 'Terjadi kesalahan saat menonaktifkan user'}), 500

@app.route('/api/users-direct', methods=['GET', 'OPTIONS'])
def users_direct_endpoint():
    """Deprecated testing endpoint. Nonaktif untuk mencegah redundansi."""
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        'success': False,
        'error': 'Endpoint /api/users-direct sudah tidak digunakan. Gunakan endpoint resmi /api/auth/users atau /api/users.'
    }), 410

@app.route('/api/role-management/departments-direct', methods=['GET', 'OPTIONS'])
def departments_direct_endpoint():
    """Direct departments endpoint tanpa blueprint untuk testing"""
    if request.method == 'OPTIONS':
        logger.info("Departments direct OPTIONS request received")
        return '', 200
    
    try:
        # Import models
        from models.role_management import Department
        from config.database import db
        
        # Test database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        
        # Query departments from database
        departments = Department.query.filter_by(is_active=True).all()
        departments_data = []
        
        for dept in departments:
            try:
                dept_dict = {
                    'id': dept.id,
                    'name': dept.name,
                    'code': dept.code,
                    'description': dept.description,
                    'parent_department_id': dept.parent_department_id,
                    'level': dept.level,
                    'is_active': dept.is_active,
                    'created_at': dept.created_at.isoformat() if dept.created_at else None,
                    'updated_at': dept.updated_at.isoformat() if dept.updated_at else None
                }
                departments_data.append(dept_dict)
                
            except Exception as dept_error:
                logger.warning(f"Error serializing department {getattr(dept, 'id', 'unknown')}: {dept_error}")
                continue
        
        return jsonify({
            'success': True,
            'data': departments_data,
            'count': len(departments_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting departments: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan saat mengambil data departments',
            'details': str(e)
        }), 500

@app.route('/api/role-management/roles-direct', methods=['GET', 'OPTIONS'])
def roles_direct_endpoint():
    """Direct roles endpoint tanpa blueprint untuk testing"""
    if request.method == 'OPTIONS':
        logger.info("Roles direct OPTIONS request received")
        return '', 200
    
    try:
        # Import models
        from models.role_management import Role, Department
        from config.database import db
        
        # Test database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        
        # Query roles from database
        roles = Role.query.filter_by(is_active=True).all()
        roles_data = []
        
        for role in roles:
            try:
                role_dict = {
                    'id': role.id,
                    'name': role.name,
                    'code': role.code,
                    'description': role.description,
                    'department_id': role.department_id,
                    'department_name': role.department.name if role.department else None,
                    'level': role.level,
                    'is_management': role.is_management,
                    'is_system_role': role.is_system_role,
                    'is_active': role.is_active,
                    'created_at': role.created_at.isoformat() if role.created_at else None,
                    'updated_at': role.updated_at.isoformat() if role.updated_at else None
                }
                roles_data.append(role_dict)
                
            except Exception as role_error:
                logger.warning(f"Error serializing role {getattr(role, 'id', 'unknown')}: {role_error}")
                continue
        
        return jsonify({
            'success': True,
            'data': roles_data,
            'count': len(roles_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting roles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan saat mengambil data roles',
            'details': str(e)
        }), 500

@app.route('/api/login/test', methods=['GET', 'POST', 'OPTIONS'])
def login_test_endpoint():
    """Test endpoint untuk memverifikasi login route tersedia"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        return jsonify({
            'success': True,
            'message': 'Login endpoint is accessible',
            'method': request.method,
            'timestamp': datetime.now().isoformat(),
            'note': 'This is a test endpoint to verify login route exists'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/agent-ai/forward', methods=['POST'])
def forward_to_agent_ai():
    """Forward request to Agent AI"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided',
                'status_code': 400
            }), 400
        
        endpoint = data.get('endpoint', '/api/knowledge/query')
        payload = data.get('payload', {})
        
        result = monitoring_service.forward_to_agent_ai(endpoint, payload)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Request forwarded to Agent AI successfully',
                'data': result.get('data'),
                'response_time': result.get('response_time'),
                'status_code': 200
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to forward request to Agent AI',
                'error': result.get('error'),
                'status_code': 500
            }), 500
            
    except Exception as e:
        logger.error(f"Error forwarding to Agent AI: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to forward request to Agent AI',
            'error': str(e),
            'status_code': 500
        }), 500

# REMOVED: /api/hybrid-search endpoint - functionality consolidated into /api/qdrant-knowledge-base/query

# REMOVED: /api/context/build endpoint - functionality consolidated into /api/qdrant-knowledge-base/query

@app.route('/api/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics"""
    try:
        stats = intelligent_cache_service.get_stats()
        return jsonify({
            'success': True,
            'message': 'Cache statistics retrieved successfully',
            'data': stats,
            'status_code': 200
        })
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get cache statistics',
            'error': str(e),
            'status_code': 500
        }), 500

@app.route('/api/document-processor/stats', methods=['GET'])
def document_processor_stats():
    """Get document processor statistics"""
    try:
        from services.unified_document_processing_service import get_unified_document_processing_service
        processor = get_unified_document_processing_service()
        stats = processor.get_processor_stats()
        return jsonify({
            'success': True,
            'message': 'Document processor statistics retrieved successfully',
            'data': stats,
            'status_code': 200
        })
    except Exception as e:
        logger.error(f"Document processor stats error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get document processor statistics',
            'error': str(e),
            'status_code': 500
        }), 500

# Debug route untuk melihat semua routes
@app.route('/debug/routes', methods=['GET'])
def debug_routes():
    """Debug endpoint untuk melihat semua routes yang terdaftar"""
    routes = []
    login_routes = []
    approval_routes = []
    for rule in app.url_map.iter_rules():
        route_info = {
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': str(rule)
        }
        routes.append(route_info)
        
        # Cari routes yang mengandung 'login'
        if 'login' in str(rule).lower():
            login_routes.append(route_info)
        
        # Cari routes yang mengandung 'approval'
        if 'approval' in str(rule).lower():
            approval_routes.append(route_info)
    
    return jsonify({
        'success': True,
        'routes': routes,
        'count': len(routes),
        'login_routes': login_routes,
        'login_count': len(login_routes),
        'approval_routes': approval_routes,
        'approval_count': len(approval_routes)
    }), 200

# Debug endpoint untuk memeriksa status server dan database
@app.route('/debug/status', methods=['GET'])
def debug_status():
    """Debug endpoint untuk memeriksa status server dan database"""
    try:
        # Test database connection
        db_status = "unknown"
        try:
            db.session.execute(db.text("SELECT 1"))
            db_status = "connected"
            logger.info("Database connection test successful")
        except Exception as db_error:
            db_status = f"error: {str(db_error)}"
            logger.error(f"Database connection test failed: {str(db_error)}")
        
        # Test TelegramSettings table
        telegram_table_status = "unknown"
        try:
            settings_count = models['knowledge_base']['TelegramSettings'].query.count()
            telegram_table_status = f"exists with {settings_count} records"
            logger.info(f"TelegramSettings table test successful: {settings_count} records")
        except Exception as table_error:
            telegram_table_status = f"error: {str(table_error)}"
            logger.error(f"TelegramSettings table test failed: {str(table_error)}")
        
        return jsonify({
            'success': True,
            'server_status': 'running',
            'database_status': db_status,
            'telegram_table_status': telegram_table_status,
            'cors_origins': Config.CORS_ORIGINS,
            'timestamp': datetime.now().isoformat(),
            'debug_info': {
                'python_version': os.sys.version,
                'flask_version': '2.x',
                'sqlalchemy_version': '1.x'
            }
        }), 200
    except Exception as e:
        logger.error(f"Debug status error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Debug endpoint untuk test CORS
@app.route('/debug/cors-test', methods=['GET', 'POST', 'OPTIONS'])
def debug_cors_test():
    """Debug endpoint untuk test CORS"""
    logger.info(f"CORS test endpoint called - Method: {request.method}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    if request.method == 'OPTIONS':
        logger.debug("CORS test OPTIONS preflight")
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key, Cache-Control, Accept, Origin, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response, 200
    
    return jsonify({
        'success': True,
        'message': 'CORS test successful',
        'method': request.method,
        'origin': request.headers.get('Origin'),
        'headers': dict(request.headers),
        'timestamp': datetime.now().isoformat()
    }), 200


# Users endpoint dengan database query - menggantikan endpoint yang bermasalah
@app.route('/api/users-new', methods=['GET', 'OPTIONS'])
def users_endpoint():
    """Real users endpoint dengan database query"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Import models
        from models.knowledge_base import User
        from config.database import db
        
        # Test database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        
        # Query users
        users = User.query.filter_by(is_active=True).all()
        users_data = []
        
        for user in users:
            try:
                user_dict = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
                
                # Add vendor info if exists
                if user.vendor_id and user.vendor:
                    user_dict['vendor'] = {
                        'id': user.vendor.id,
                        'name': getattr(user.vendor, 'name', 'Unknown Vendor')
                    }
                
                users_data.append(user_dict)
                
            except Exception as user_error:
                logger.warning(f"Error serializing user {getattr(user, 'id', 'unknown')}: {user_error}")
                continue
        
        return jsonify({
            'success': True,
            'data': users_data,
            'count': len(users_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan saat mengambil data users',
            'details': str(e)
        }), 500

# Favicon route untuk mengatasi error 500
@app.route('/favicon.ico')
def favicon():
    """Handle favicon request"""
    return '', 204  # No Content

# Root route untuk health check
@app.route('/')
def root():
    """Root endpoint untuk health check"""
    return jsonify({
        'success': True,
        'message': 'KSM Main Backend API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }), 200

# Debug endpoint untuk test telegram settings tanpa auth
@app.route('/debug/telegram-settings-test', methods=['GET', 'OPTIONS'])
def debug_telegram_settings_test():
    """Debug endpoint untuk test telegram settings tanpa authentication"""
    logger.info(f"Telegram settings test endpoint called - Method: {request.method}")
    
    if request.method == 'OPTIONS':
        logger.debug("Telegram settings test OPTIONS preflight")
        return '', 200
    
    return jsonify({
        'success': True,
        'message': 'Telegram settings test endpoint accessible',
        'method': request.method,
        'timestamp': datetime.now().isoformat(),
        'note': 'This endpoint is for testing CORS and accessibility'
    }), 200

# Debug endpoint untuk test telegram settings dengan path yang sama seperti frontend
@app.route('/api/telegram/settings/test', methods=['POST', 'OPTIONS'])
def debug_telegram_settings_test_direct():
    """Debug endpoint untuk test telegram settings dengan path yang sama seperti frontend"""
    logger.info(f"Direct telegram settings test endpoint called - Method: {request.method}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    logger.debug(f"Request origin: {request.headers.get('Origin')}")
    
    if request.method == 'OPTIONS':
        logger.debug("Direct telegram settings test OPTIONS preflight")
        response = app.make_default_options_response()
        origin = request.headers.get('Origin')
        if origin and origin in Config.CORS_ORIGINS:
            response.headers['Access-Control-Allow-Origin'] = origin
        elif Config.CORS_ORIGINS:
            response.headers['Access-Control-Allow-Origin'] = Config.CORS_ORIGINS[0]
        else:
            response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3002'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key, Cache-Control, Accept, Origin, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response, 200
    
    try:
        data = request.get_json() or {}
        logger.debug(f"Request data: {data}")
        
        return jsonify({
            'success': True,
            'message': 'Direct telegram settings test endpoint accessible',
            'method': request.method,
            'data_received': data,
            'timestamp': datetime.now().isoformat(),
            'note': 'This is a debug endpoint to test CORS and routing'
        }), 200
    except Exception as e:
        logger.error(f"Error in direct telegram settings test: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Optimized status endpoints
@app.route('/agent/status', methods=['GET', 'OPTIONS'])
def agent_status():
    """Status endpoint untuk agent AI dengan timeout"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Cek koneksi ke Agent AI dengan timeout pendek
        agent_response = requests.get(f"{AGENT_AI_URL}/health", timeout=3)
        agent_status = "online" if agent_response.status_code == 200 else "offline"
    except:
        agent_status = "offline"
    
    return jsonify({
        'success': True,
        'agent_status': agent_status,
        'timestamp': datetime.now().isoformat()
    }), 200



@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Dashboard endpoint yang ringan"""
    return jsonify({
        'success': True,
        'message': 'Dashboard API is working',
        'timestamp': datetime.now().isoformat()
    }), 200

# Memory cleanup function
def cleanup_memory():
    """Function untuk membersihkan memory"""
    gc.collect()
    rate_limiter._cleanup_old_ips(datetime.now().timestamp(), 60)

# Periodic cleanup
@app.before_request
def before_request():
    """Cleanup memory sebelum setiap request"""
    if hasattr(app, '_request_count'):
        app._request_count += 1
    else:
        app._request_count = 1
    
    # Cleanup setiap 100 requests
    if app._request_count % 100 == 0:
        cleanup_memory()

if __name__ == '__main__':
    # Initialize database tables
    init_unified_database()
    
    # Initialize vendor templates
    try:
        with app.app_context():
            from services.vendor_template_service import VendorTemplateService
            template_service = VendorTemplateService(db.session)
            template_service.create_default_templates()
            logger.info("[SUCCESS] Vendor templates initialized")
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize vendor templates: {e}")
        # Continue without templates if it fails
    
    # Start document processor
    try:
        with app.app_context():
            from services.unified_document_processing_service import get_unified_document_processing_service
            processor = get_unified_document_processing_service()
            processor.start_processor()
            logger.info("[SUCCESS] Document processor started")
            
            # Test processor dengan app context
            stats = processor.get_processor_stats()
            logger.info(f"[INFO] Processor stats: {stats}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to start document processor: {e}")
        logger.error(f"[ERROR] Error details: {str(e)}")
        import traceback
        logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
        # Continue without processor if it fails
    
    # Start notification scheduler
    try:
        with app.app_context():
            start_notification_scheduler()
            logger.info("[SUCCESS] Notification scheduler started")
    except Exception as e:
        logger.error(f"[ERROR] Failed to start notification scheduler: {e}")
        # Continue without scheduler if it fails
    
    # Start daily task notification scheduler
    try:
        with app.app_context():
            from schedulers.daily_task_scheduler import daily_task_scheduler
            if daily_task_scheduler.start_scheduler():
                logger.info("[SUCCESS] Daily task notification scheduler started")
            else:
                logger.warning("[WARNING] Daily task notification scheduler failed to start")
    except Exception as e:
        logger.error(f"[ERROR] Failed to start daily task notification scheduler: {e}")
        # Continue without scheduler if it fails
    
    # Start remind exp docs notification scheduler
    try:
        from schedulers.remind_exp_docs_scheduler import remind_exp_docs_scheduler
        remind_exp_docs_scheduler.set_app(app)  # Set app instance
        remind_exp_docs_scheduler.start_scheduler()
        logger.info("[SUCCESS] Remind exp docs notification scheduler started")
    except Exception as e:
        logger.error(f"[ERROR] Failed to start remind exp docs notification scheduler: {e}")
        # Continue without scheduler if it fails
    
    # Graceful shutdown handler
    import signal
    import sys
    
    def signal_handler(sig, frame):
        logger.info("[SHUTDOWN] Shutting down gracefully...")
        try:
            from schedulers.daily_task_scheduler import daily_task_scheduler
            daily_task_scheduler.stop_scheduler()
            logger.info("[SUCCESS] Daily task scheduler stopped")
        except Exception as e:
            logger.error(f"[ERROR] Error stopping daily task scheduler: {e}")
        
        try:
            from schedulers.remind_exp_docs_scheduler import remind_exp_docs_scheduler
            remind_exp_docs_scheduler.stop_scheduler()
            logger.info("[SUCCESS] Remind exp docs scheduler stopped")
        except Exception as e:
            logger.error(f"[ERROR] Error stopping remind exp docs scheduler: {e}")
        
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start server dengan SocketIO support
    logger.info("[STARTUP] Starting KSM Main Backend with WebSocket support...")
    socketio.run(app, host='0.0.0.0', port=8000, debug=True, allow_unsafe_werkzeug=True)
