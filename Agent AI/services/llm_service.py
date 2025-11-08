#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Service untuk Agent AI
Menggunakan OpenAI API untuk response generation
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import openai
from config.config import Config

logger = logging.getLogger(__name__)

class LLMService:
    """LLM Service menggunakan OpenAI API"""
    
    def __init__(self):
        self.client = None
        self.model = Config.DEFAULT_MODEL
        self.temperature = Config.AI_TEMPERATURE
        self.max_tokens = Config.AI_MAX_TOKENS
        self.top_p = Config.AI_TOP_P
        self.initialized = False
        
    def initialize(self):
        """Initialize OpenAI client"""
        try:
            api_key = Config.OPENAI_API_KEY
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in configuration")
            
            # Initialize OpenAI client
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=Config.OPENAI_BASE_URL
            )
            
            # Test connection with simple request
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5,
                    temperature=0.1
                )
                logger.info("OpenAI API connection test successful")
            except Exception as test_error:
                logger.warning(f"OpenAI API test failed: {test_error}")
                # Continue anyway for now
            
            self.initialized = True
            logger.info("LLM Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM Service: {e}")
            self.initialized = False
            raise
    
    def _test_connection(self):
        """Test OpenAI API connection"""
        try:
            # Simple test request
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                temperature=0.1
            )
            
            logger.info("OpenAI API connection test successful")
            
        except Exception as e:
            logger.error(f"OpenAI API connection test failed: {e}")
            raise
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build system prompt berdasarkan context"""
        base_prompt = """Anda adalah asisten AI yang membantu menjawab pertanyaan berdasarkan informasi yang tersedia. 
        Berikan jawaban yang akurat, informatif, dan mudah dipahami dalam bahasa Indonesia.
        
        Instruksi:
        1. Gunakan informasi dari context yang diberikan jika tersedia
        2. Jika tidak ada informasi yang relevan, katakan dengan jujur
        3. Berikan jawaban yang terstruktur dan mudah dibaca
        4. Gunakan bahasa Indonesia yang baik dan benar
        5. Jika perlu, berikan contoh atau penjelasan tambahan"""
        
        if context and context.get('context_available'):
            context_info = f"""
        
        Context Information:
        - Jumlah dokumen yang relevan: {context.get('total_chunks', 0)}
        - Tingkat relevansi rata-rata: {context.get('avg_similarity', 0.0):.2f}
        - Informasi dari knowledge base tersedia
        
        Gunakan informasi dari context ini untuk memberikan jawaban yang akurat."""
            base_prompt += context_info
        
        return base_prompt
    
    def _build_messages(self, message: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Build messages untuk OpenAI API"""
        messages = [
            {"role": "system", "content": self._build_system_prompt(context)}
        ]
        
        # Add context information if available
        if context and context.get('context_available') and context.get('rag_results'):
            context_content = "Informasi yang relevan dari knowledge base:\n\n"
            
            for i, result in enumerate(context.get('rag_results', [])[:5], 1):  # Limit to top 5
                content = result.get('content', '')
                similarity = result.get('similarity', 0.0)
                source = result.get('source_document', 'Dokumen')
                
                context_content += f"{i}. **{source}** (Relevansi: {similarity:.2f})\n{content}\n\n"
            
            messages.append({
                "role": "system", 
                "content": context_content
            })
        
        # Add user message
        messages.append({
            "role": "user", 
            "content": message
        })
        
        return messages
    
    def generate_response(self, message: str, user_id: int, session_id: str, 
                         source: str, context: Optional[Dict[str, Any]] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate response menggunakan OpenAI API"""
        try:
            if not self.initialized:
                return {
                    'success': False,
                    'error': 'LLM Service not initialized'
                }
            
            start_time = time.time()
            
            # Build messages
            messages = self._build_messages(message, context)
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p
            )
            
            processing_time = time.time() - start_time
            
            # Extract response
            ai_response = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            logger.info(f"Response generated in {processing_time:.2f}s, tokens: {tokens_used}")
            
            return {
                'success': True,
                'response': ai_response,
                'model_used': self.model,
                'processing_time': round(processing_time, 2),
                'tokens_used': tokens_used,
                'context_used': context.get('context_available', False) if context else False,
                'metadata': {
                    'user_id': user_id,
                    'session_id': session_id,
                    'source': source,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'success': False,
                'error': str(e),
                'model_used': self.model,
                'processing_time': time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def check_health(self) -> Dict[str, Any]:
        """Check LLM service health"""
        try:
            if not self.initialized:
                return {
                    'success': False,
                    'status': 'not_initialized',
                    'error': 'LLM Service not initialized'
                }
            
            # Test with simple request
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                temperature=0.1
            )
            response_time = time.time() - start_time
            
            return {
                'success': True,
                'status': 'healthy',
                'model': self.model,
                'response_time': round(response_time, 3),
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return {
                'success': False,
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get LLM service status"""
        return {
            'service': 'LLM Service',
            'initialized': self.initialized,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'top_p': self.top_p,
            'api_base_url': Config.OPENAI_BASE_URL,
            'timestamp': datetime.now().isoformat()
        }

# Global instance
llm_service = LLMService()
