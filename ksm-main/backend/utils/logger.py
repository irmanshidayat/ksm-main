#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger utility untuk KSM Main Backend
"""

import logging
import sys
from datetime import datetime

def get_logger(name):
    """Mendapatkan logger instance"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Setup formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # Setup file handler
        file_handler = logging.FileHandler('ksm_backend.log')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
    
    return logger
