#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Context Builder Service untuk KSM-Main Backend
Service untuk membangun context yang advanced dengan integrasi Agent AI
"""

import logging
import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import re

# Setup logging
logger = logging.getLogger(__name__)

class AdvancedContextBuilder:
    """Service untuk membangun context yang advanced dengan Agent AI integration"""
    
    def __init__(self):
        self.agent_ai_url = os.getenv('AGENT_AI_URL', 'http://localhost:5000')
        self.agent_ai_api_key = os.getenv('AGENT_AI_API_KEY', 'KSM_api_key_2ptybn')
        self.enabled = os.getenv('ENABLE_ADVANCED_CONTEXT', 'true').lower() == 'true'
        
        # Context configuration
        self.max_context_length = int(os.getenv('MAX_CONTEXT_LENGTH', '4000'))
        self.context_quality_threshold = float(os.getenv('CONTEXT_QUALITY_THRESHOLD', '0.7'))
        
        logger.info(f"✅ Advanced Context Builder initialized (enabled: {self.enabled})")
    
    def build_context(self, 
                     query: str, 
                     user_data: Optional[Dict[str, Any]] = None,
                     session_data: Optional[Dict[str, Any]] = None,
                     knowledge_base: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Build advanced context for processing"""
        try:
            if not self.enabled:
                return self._build_basic_context(query, user_data, session_data)
            
            # Build comprehensive context
            context = {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'user_context': self._build_user_context(user_data),
                'session_context': self._build_session_context(session_data),
                'knowledge_context': self._build_knowledge_context(knowledge_base),
                'system_context': self._build_system_context(),
                'processing_instructions': self._generate_processing_instructions(query)
            }
            
            # Enhance context with Agent AI if available
            enhanced_context = self._enhance_with_agent_ai(context)
            
            return {
                'success': True,
                'context': enhanced_context,
                'context_length': len(json.dumps(enhanced_context)),
                'quality_score': self._calculate_context_quality(enhanced_context),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Advanced context building error: {e}")
            return self._build_basic_context(query, user_data, session_data)
    
    def _build_user_context(self, user_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build user-specific context"""
        if not user_data:
            return {'user_id': 'anonymous', 'preferences': {}}
        
        return {
            'user_id': user_data.get('user_id', 'anonymous'),
            'preferences': user_data.get('preferences', {}),
            'history': user_data.get('history', []),
            'profile': user_data.get('profile', {}),
            'permissions': user_data.get('permissions', [])
        }
    
    def _build_session_context(self, session_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build session-specific context"""
        if not session_data:
            return {'session_id': 'default', 'conversation_history': []}
        
        return {
            'session_id': session_data.get('session_id', 'default'),
            'conversation_history': session_data.get('conversation_history', []),
            'current_topic': session_data.get('current_topic', ''),
            'session_start': session_data.get('session_start', datetime.now().isoformat()),
            'interaction_count': session_data.get('interaction_count', 0)
        }
    
    def _build_knowledge_context(self, knowledge_base: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Build knowledge base context"""
        if not knowledge_base:
            return {'sources': [], 'total_sources': 0}
        
        return {
            'sources': knowledge_base[:5],  # Limit to top 5 sources
            'total_sources': len(knowledge_base),
            'source_types': list(set([source.get('type', 'unknown') for source in knowledge_base])),
            'relevance_scores': [source.get('score', 0.0) for source in knowledge_base[:5]]
        }
    
    def _build_system_context(self) -> Dict[str, Any]:
        """Build system context"""
        return {
            'system': 'KSM-Main Backend',
            'version': '1.0.0',
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'features_enabled': {
                'agent_ai_integration': os.getenv('ENABLE_AGENT_AI_INTEGRATION', 'true').lower() == 'true',
                'telegram_bot': os.getenv('ENABLE_TELEGRAM_BOT', 'true').lower() == 'true',
                'knowledge_base': os.getenv('ENABLE_KNOWLEDGE_BASE', 'true').lower() == 'true',
                'monitoring': os.getenv('ENABLE_MONITORING', 'true').lower() == 'true'
            },
            'current_time': datetime.now().isoformat()
        }
    
    def _generate_processing_instructions(self, query: str) -> List[str]:
        """Generate processing instructions based on query"""
        instructions = [
            "Provide accurate and helpful response",
            "Use available context to enhance response quality",
            "Maintain professional tone"
        ]
        
        # Add specific instructions based on query type
        if any(keyword in query.lower() for keyword in ['help', 'how', 'what', 'why']):
            instructions.append("Provide detailed explanation with examples")
        
        if any(keyword in query.lower() for keyword in ['urgent', 'asap', 'immediately']):
            instructions.append("Prioritize speed and directness")
        
        if any(keyword in query.lower() for keyword in ['technical', 'code', 'programming']):
            instructions.append("Include technical details and code examples if relevant")
        
        return instructions
    
    def _enhance_with_agent_ai(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance context using Agent AI"""
        try:
            # Prepare context for Agent AI processing
            processing_data = {
                'context': json.dumps(context),
                'task': 'context_enhancement',
                'company_id': 'KSM_main',
                'client_id': 'context_builder',
                'company_name': 'KSM Grup',
                'instructions': 'Enhance and optimize the provided context for better processing'
            }
            
            response = requests.post(
                f"{self.agent_ai_url}/api/langchain/process",
                json=processing_data,
                headers={
                    'Content-Type': 'application/json',
                    'X-API-Key': self.agent_ai_api_key
                },
                timeout=15
            )
            
            if response.status_code == 200:
                agent_result = response.json()
                enhanced_data = agent_result.get('data', {})
                
                # Merge enhanced data with original context
                context['agent_ai_enhancement'] = {
                    'enhanced': True,
                    'enhancement_data': enhanced_data,
                    'enhancement_timestamp': datetime.now().isoformat()
                }
                
                logger.debug("✅ Context enhanced with Agent AI")
            else:
                logger.warning(f"⚠️ Agent AI context enhancement failed: {response.status_code}")
                context['agent_ai_enhancement'] = {
                    'enhanced': False,
                    'error': f'HTTP {response.status_code}',
                    'fallback_used': True
                }
                
        except Exception as e:
            logger.error(f"❌ Agent AI context enhancement error: {e}")
            context['agent_ai_enhancement'] = {
                'enhanced': False,
                'error': str(e),
                'fallback_used': True
            }
        
        return context
    
    def _build_basic_context(self, 
                           query: str, 
                           user_data: Optional[Dict[str, Any]] = None,
                           session_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build basic context when advanced features are disabled"""
        return {
            'success': True,
            'context': {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'user_context': self._build_user_context(user_data),
                'session_context': self._build_session_context(session_data),
                'system_context': self._build_system_context(),
                'processing_instructions': self._generate_processing_instructions(query),
                'advanced_features': False
            },
            'context_length': len(query),
            'quality_score': 0.5,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_context_quality(self, context: Dict[str, Any]) -> float:
        """Calculate context quality score"""
        try:
            score = 0.0
            
            # Base score for having context
            score += 0.2
            
            # Score for user context
            if context.get('user_context', {}).get('user_id') != 'anonymous':
                score += 0.2
            
            # Score for session context
            if context.get('session_context', {}).get('conversation_history'):
                score += 0.2
            
            # Score for knowledge context
            if context.get('knowledge_context', {}).get('total_sources', 0) > 0:
                score += 0.2
            
            # Score for Agent AI enhancement
            if context.get('agent_ai_enhancement', {}).get('enhanced'):
                score += 0.2
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Context quality calculation error: {e}")
            return 0.5
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        try:
            # Simple keyword extraction (bisa diimplementasikan lebih advanced)
            words = re.findall(r'\b\w+\b', text.lower())
            
            # Filter common words
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
            
            keywords = [word for word in words if word not in common_words and len(word) > 2]
            
            # Return top 10 keywords
            return keywords[:10]
            
        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            return []
    
    def get_context_stats(self) -> Dict[str, Any]:
        """Get context builder statistics"""
        return {
            'service': 'Advanced Context Builder',
            'enabled': self.enabled,
            'max_context_length': self.max_context_length,
            'context_quality_threshold': self.context_quality_threshold,
            'agent_ai_url': self.agent_ai_url,
            'timestamp': datetime.now().isoformat()
        }

# Global advanced context builder instance
advanced_context_builder = AdvancedContextBuilder()

def get_advanced_context_builder() -> AdvancedContextBuilder:
    """Get advanced context builder instance"""
    return advanced_context_builder
