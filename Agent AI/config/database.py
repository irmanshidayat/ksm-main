#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent AI Database Configuration
Shared database dengan KSM Main
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager untuk Agent AI (Shared dengan KSM Main)"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection"""
        try:
            # Get database URL from environment
            database_url = os.getenv('DATABASE_URL')
            
            if not database_url:
                logger.error("❌ DATABASE_URL not found in environment variables")
                return
            
            # Create engine with connection pooling
            self.engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("✅ Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            self.engine = None
            self.SessionLocal = None
    
    def get_session(self):
        """Get database session"""
        if not self.SessionLocal:
            raise Exception("Database not initialized")
        
        return self.SessionLocal()
    
    def test_connection(self):
        """Test database connection"""
        try:
            if not self.engine:
                return {
                    'success': False,
                    'error': 'Database engine not initialized'
                }
            
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
            
            return {
                'success': True,
                'message': 'Database connection successful'
            }
            
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_connection_info(self):
        """Get database connection information"""
        if not self.engine:
            return {
                'connected': False,
                'error': 'Database not initialized'
            }
        
        try:
            url = self.engine.url
            return {
                'connected': True,
                'driver': url.drivername,
                'host': url.host,
                'port': url.port,
                'database': url.database,
                'username': url.username,
                'pool_size': self.engine.pool.size(),
                'checked_out': self.engine.pool.checkedout(),
                'overflow': self.engine.pool.overflow(),
                'checked_in': self.engine.pool.checkedin()
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("🔌 Database connection closed")

# Global database manager instance
db_manager = DatabaseManager()

def get_db_session():
    """Get database session (dependency injection)"""
    return db_manager.get_session()

def test_database_connection():
    """Test database connection"""
    return db_manager.test_connection()

def get_database_info():
    """Get database information"""
    return db_manager.get_connection_info()
