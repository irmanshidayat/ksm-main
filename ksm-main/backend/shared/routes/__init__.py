#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared Routes - Routes yang digunakan cross-domain atau untuk development
"""

from .debug_routes import debug_bp
from .compatibility_routes import compatibility_bp

__all__ = ['debug_bp', 'compatibility_bp']

