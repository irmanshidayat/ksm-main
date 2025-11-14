#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialize Default Permissions Script
Script untuk menginisialisasi default permissions dalam application context
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from domains.role.services.permission_service import permission_service
from domains.role.services.workflow_service import workflow_service
from shared.services.audit_trail_service import audit_service
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_services():
    """Initialize all services with default data"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🚀 Starting service initialization...")
            
            # Initialize default permissions
            logger.info("📋 Initializing default permissions...")
            permission_service.initialize_default_permissions()
            
            # Initialize default workflows
            logger.info("🔄 Initializing default workflows...")
            workflow_service.initialize_default_workflows()
            
            # Initialize audit service
            logger.info("📊 Initializing audit service...")
            audit_service.initialize_audit_tables()
            
            logger.info("✅ All services initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error initializing services: {e}")
            raise

if __name__ == "__main__":
    initialize_services()
