#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent AI - Main Flask Application
LLM Service untuk KSM Main dengan RAG Integration
"""

import os
import sys
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import traceback

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import configuration
from config.config import Config

# Import controllers
from controllers.telegram_controller import telegram_bp
from controllers.rag_controller import rag_bp
from controllers.health_controller import health_bp
from controllers.notification_controller import notification_bp

# Import services
from services.llm_service import llm_service
from services.rag_context_service import rag_context_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent_ai.log')
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """Create Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Enable CORS
    CORS(app, origins=['http://localhost:3000', 'http://localhost:8080'])
    
    # Register blueprints
    app.register_blueprint(telegram_bp, url_prefix='/api/telegram')
    app.register_blueprint(rag_bp, url_prefix='/api/rag')
    app.register_blueprint(health_bp, url_prefix='')
    app.register_blueprint(notification_bp)  # Daily Task Notification Routes
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Endpoint not found',
            'error': '404'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': '500'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred',
            'error': str(e)
        }), 500
    
    # Root endpoint
    @app.route('/')
    def root():
        return jsonify({
            'service': 'Agent AI',
            'version': '1.0.0',
            'description': 'LLM Service untuk KSM Main dengan RAG Integration',
            'status': 'active',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'health': '/health',
                'status': '/status',
                'telegram_chat': '/api/telegram/chat',
                'rag_chat': '/api/rag/chat',
                'daily_task_report': '/api/report/daily-task',
                'rag_status': '/api/rag/status'
            }
        })
    
    # Initialize services
    def initialize_services():
        """Initialize services on startup"""
        try:
            logger.info("Initializing Agent AI services...")
            
            # Initialize RAG context service first (no external dependencies)
            rag_context_service.initialize()
            logger.info("RAG Context Service initialized")
            
            # Try to initialize LLM service (may fail if OpenAI API key is invalid)
            try:
                llm_service.initialize()
                logger.info("LLM Service initialized")
            except Exception as llm_error:
                logger.warning(f"LLM Service initialization failed: {llm_error}")
                logger.warning("Agent AI will run without LLM service (fallback mode)")
            
            logger.info("Agent AI services initialization completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            logger.error(traceback.format_exc())
    
    # Initialize services immediately
    initialize_services()
    
    return app

def main():
    """Main function"""
    try:
        app = create_app()
        
        # Get configuration
        host = os.getenv('AGENT_AI_HOST', '0.0.0.0')
        port = int(os.getenv('AGENT_AI_PORT', '5000'))
        debug = os.getenv('AGENT_AI_DEBUG', 'false').lower() == 'true'
        
        logger.info(f"Starting Agent AI on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        
        # Run application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start Agent AI: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
