#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger utility untuk KSM Main Backend
"""

import logging
import sys
import os
from datetime import datetime

# Global flag untuk memastikan root logger hanya di-setup sekali
_root_logger_configured = False

def get_logger(name):
    """Mendapatkan logger instance dengan konfigurasi yang konsisten"""
    global _root_logger_configured
    
    logger = logging.getLogger(name)
    
    # Setup root logger hanya sekali untuk menghindari duplicate logging
    if not _root_logger_configured:
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Hapus semua handler yang sudah ada untuk menghindari duplicate
        root_logger.handlers.clear()
        
        # Setup formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # Setup file handler dengan path yang benar
        log_file = os.path.join(os.getcwd(), 'ksm_backend.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Add handlers ke root logger
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # Set flag agar tidak di-setup lagi
        _root_logger_configured = True
    
    # Set level untuk logger spesifik
    logger.setLevel(logging.INFO)
    
    # Pastikan logger tidak propagate ke root jika sudah ada handler sendiri
    # Tapi untuk konsistensi, kita biarkan propagate ke root logger yang sudah dikonfigurasi
    logger.propagate = True
    
    return logger
