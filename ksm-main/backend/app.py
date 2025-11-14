#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KSM Main Backend - Entry Point (Refactored)
Menggunakan app_factory untuk struktur yang lebih clean dan modular
"""

import logging
from core.app_factory import create_app

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app using factory
app, socketio = create_app()

if __name__ == '__main__':
    # Initialize vendor templates
    try:
        with app.app_context():
            from domains.vendor.services.vendor_template_service import VendorTemplateService
            from config.database import db
            template_service = VendorTemplateService(db.session)
            template_service.create_default_templates()
            logger.info("[SUCCESS] Vendor templates initialized")
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize vendor templates: {e}")
    
    # Start document processor
    try:
        with app.app_context():
            from domains.knowledge.services.unified_document_processing_service import get_unified_document_processing_service
            processor = get_unified_document_processing_service()
            processor.start_processor()
            logger.info("[SUCCESS] Document processor started")
            
            stats = processor.get_processor_stats()
            logger.info(f"[INFO] Processor stats: {stats}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to start document processor: {e}")
        import traceback
        logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
    
    # Start notification scheduler
    try:
        with app.app_context():
            from shared.utils.notification_scheduler import start_notification_scheduler
            start_notification_scheduler()
            logger.info("[SUCCESS] Notification scheduler started")
    except Exception as e:
        logger.error(f"[ERROR] Failed to start notification scheduler: {e}")
    
    # Start daily task notification scheduler
    try:
        with app.app_context():
            from domains.task.schedulers.daily_task_scheduler import daily_task_scheduler
            if daily_task_scheduler.start_scheduler():
                logger.info("[SUCCESS] Daily task notification scheduler started")
            else:
                logger.warning("[WARNING] Daily task notification scheduler failed to start")
    except Exception as e:
        logger.error(f"[ERROR] Failed to start daily task notification scheduler: {e}")
    
    # Start remind exp docs notification scheduler
    try:
        from domains.task.schedulers.remind_exp_docs_scheduler import remind_exp_docs_scheduler
        remind_exp_docs_scheduler.set_app(app)
        remind_exp_docs_scheduler.start_scheduler()
        logger.info("[SUCCESS] Remind exp docs notification scheduler started")
    except Exception as e:
        logger.error(f"[ERROR] Failed to start remind exp docs notification scheduler: {e}")
    
    # Graceful shutdown handler
    import signal
    import sys
    
    def signal_handler(sig, frame):
        logger.info("[SHUTDOWN] Shutting down gracefully...")
        try:
            from domains.task.schedulers.daily_task_scheduler import daily_task_scheduler
            daily_task_scheduler.stop_scheduler()
            logger.info("[SUCCESS] Daily task scheduler stopped")
        except Exception as e:
            logger.error(f"[ERROR] Error stopping daily task scheduler: {e}")
        
        try:
            from domains.task.schedulers.remind_exp_docs_scheduler import remind_exp_docs_scheduler
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
