#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger utility untuk Agent AI
"""

import os
import logging
import logging.handlers
from datetime import datetime
from config.config import Config

def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """Setup logger dengan file dan console handler"""
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create logs directory if not exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)

def log_request(logger: logging.Logger, endpoint: str, method: str, 
                user_id: int = None, processing_time: float = None, 
                success: bool = None, error: str = None):
    """Log request information"""
    
    log_data = {
        'endpoint': endpoint,
        'method': method,
        'timestamp': datetime.now().isoformat()
    }
    
    if user_id:
        log_data['user_id'] = user_id
    
    if processing_time is not None:
        log_data['processing_time'] = round(processing_time, 3)
    
    if success is not None:
        log_data['success'] = success
    
    if error:
        log_data['error'] = error
    
    logger.info(f"Request: {log_data}")

def log_response(logger: logging.Logger, endpoint: str, status_code: int,
                 response_time: float = None, tokens_used: int = None,
                 model_used: str = None):
    """Log response information"""
    
    log_data = {
        'endpoint': endpoint,
        'status_code': status_code,
        'timestamp': datetime.now().isoformat()
    }
    
    if response_time is not None:
        log_data['response_time'] = round(response_time, 3)
    
    if tokens_used is not None:
        log_data['tokens_used'] = tokens_used
    
    if model_used:
        log_data['model_used'] = model_used
    
    logger.info(f"Response: {log_data}")

def log_error(logger: logging.Logger, error: Exception, context: dict = None):
    """Log error dengan context"""
    
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': datetime.now().isoformat()
    }
    
    if context:
        error_data['context'] = context
    
    logger.error(f"Error: {error_data}")

def log_performance(logger: logging.Logger, operation: str, duration: float,
                   details: dict = None):
    """Log performance metrics"""
    
    perf_data = {
        'operation': operation,
        'duration': round(duration, 3),
        'timestamp': datetime.now().isoformat()
    }
    
    if details:
        perf_data.update(details)
    
    logger.info(f"Performance: {perf_data}")
