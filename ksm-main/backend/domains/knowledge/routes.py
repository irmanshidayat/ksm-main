#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Domain Routes - Blueprint registration for knowledge domain
"""

from domains.knowledge.controllers.knowledge_base_controller import knowledge_base_bp
from domains.knowledge.controllers.knowledge_ai_controller import knowledge_ai_bp
from domains.knowledge.controllers.qdrant_knowledge_base_controller import qdrant_kb_bp
from domains.knowledge.controllers.standalone_ai_controller import standalone_ai_bp

def register_knowledge_routes(app):
    """Register all knowledge domain blueprints"""
    app.register_blueprint(knowledge_base_bp, url_prefix='/api/knowledge-base')
    app.register_blueprint(qdrant_kb_bp, url_prefix='/api/qdrant-knowledge-base')
    app.register_blueprint(knowledge_ai_bp)
    app.register_blueprint(standalone_ai_bp)

