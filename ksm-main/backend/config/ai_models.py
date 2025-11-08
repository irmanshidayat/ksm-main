#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Model Registry untuk OpenRouter Integration (KSM Main)
Mengelola mapping model dan konfigurasi AI models - Synchronized dengan Agent AI
"""

import os
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class AIModelRegistry:
    """Registry untuk mengelola AI models dan konfigurasinya"""
    
    def __init__(self):
        self.models = self._initialize_models()
        self.default_models = self._get_default_models()
        
    def _initialize_models(self) -> Dict[str, Dict[str, Any]]:
        """Inisialisasi model registry dengan semua model yang tersedia"""
        return {
            # Google Gemini Models (via OpenRouter) - Updated to 2.5
            'google/gemini-2.5-flash-preview-09-2025': {
                'name': 'Gemini 2.5 Flash Preview 09-2025',
                'provider': 'google',
                'type': 'multimodal',
                'description': 'Latest Gemini 2.5 Flash Preview model - Fast and efficient',
                'max_tokens': 16384,
                'supports_vision': True,
                'cost_per_1k_tokens': 0.0003,
                'endpoint': '/chat/completions',
                'parameters': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 16384
                }
            },
            'google/gemini-2.5-pro': {
                'name': 'Gemini 2.5 Pro',
                'provider': 'google',
                'type': 'multimodal',
                'description': 'Most capable multimodal model (2.5)',
                'max_tokens': 32768,
                'supports_vision': True,
                'cost_per_1k_tokens': 0.0005,
                'endpoint': '/chat/completions',
                'parameters': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 32768
                }
            },
            # Legacy 1.5 models for backward compatibility
            'google/gemini-2.5-flash-preview-09-2025': {
                'name': 'Gemini 1.5 Flash (Latest)',
                'provider': 'google',
                'type': 'multimodal',
                'description': 'Fast and efficient multimodal model (latest alias)',
                'max_tokens': 16384,
                'supports_vision': True,
                'cost_per_1k_tokens': 0.0003,
                'endpoint': '/chat/completions',
                'parameters': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 16384
                }
            },
            'google/gemini-2.5-flash-preview-09-2025': {
                'name': 'Gemini 1.5 Pro (Latest)',
                'provider': 'google',
                'type': 'multimodal',
                'description': 'Most capable multimodal model (latest alias)',
                'max_tokens': 32768,
                'supports_vision': True,
                'cost_per_1k_tokens': 0.0005,
                'endpoint': '/chat/completions',
                'parameters': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 32768
                }
            },
            'google/gemini-pro': {
                'name': 'Gemini Pro',
                'provider': 'google',
                'type': 'text',
                'description': 'Advanced text generation model',
                'max_tokens': 8192,
                'supports_vision': False,
                'cost_per_1k_tokens': 0.0005,
                'endpoint': '/chat/completions',
                'parameters': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 8192
                }
            },
            'google/gemini-pro-vision': {
                'name': 'Gemini Pro Vision',
                'provider': 'google',
                'type': 'multimodal',
                'description': 'Advanced text and image understanding model',
                'max_tokens': 8192,
                'supports_vision': True,
                'cost_per_1k_tokens': 0.0005,
                'endpoint': '/chat/completions',
                'parameters': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 8192
                }
            },
            'google/gemini-2.5-flash-preview-09-2025': {
                'name': 'Gemini 1.5 Flash',
                'provider': 'google',
                'type': 'multimodal',
                'description': 'Fast and efficient multimodal model',
                'max_tokens': 16384,
                'supports_vision': True,
                'cost_per_1k_tokens': 0.0003,
                'endpoint': '/chat/completions',
                'parameters': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 16384
                }
            },
            'google/gemini-1.5-pro': {
                'name': 'Gemini 1.5 Pro',
                'provider': 'google',
                'type': 'multimodal',
                'description': 'Most capable multimodal model',
                'max_tokens': 32768,
                'supports_vision': True,
                'cost_per_1k_tokens': 0.0005,
                'endpoint': '/chat/completions',
                'parameters': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 32768
                }
            },
            
            # Anthropic Claude Models (via OpenRouter)
            'anthropic/claude-3.5-sonnet': {
                'name': 'Claude 3.5 Sonnet',
                'provider': 'anthropic',
                'type': 'text',
                'description': 'Fast and efficient text model',
                'max_tokens': 16384,
                'supports_vision': False,
                'cost_per_1k_tokens': 0.0003,
                'endpoint': '/chat/completions',
                'parameters': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 16384
                }
            },
            'anthropic/claude-3.5-sonnet-20241022': {
                'name': 'Claude 3.5 Sonnet (Latest)',
                'provider': 'anthropic',
                'type': 'multimodal',
                'description': 'Latest Claude model with vision support',
                'max_tokens': 16384,
                'supports_vision': True,
                'cost_per_1k_tokens': 0.0003,
                'endpoint': '/chat/completions',
                'parameters': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 16384
                }
            },
            
            # OpenAI Models (via OpenRouter)
            'openai/gpt-4': {
                'name': 'GPT-4',
                'provider': 'openai',
                'type': 'text',
                'description': 'Advanced language model',
                'max_tokens': 8192,
                'supports_vision': False,
                'cost_per_1k_tokens': 0.03,
                'endpoint': '/chat/completions',
                'parameters': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 8192
                }
            },
            'openai/gpt-4-vision-preview': {
                'name': 'GPT-4 Vision',
                'provider': 'openai',
                'type': 'multimodal',
                'description': 'GPT-4 with vision capabilities',
                'max_tokens': 4096,
                'supports_vision': True,
                'cost_per_1k_tokens': 0.03,
                'endpoint': '/chat/completions',
                'parameters': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 4096
                }
            }
        }
    
    def _get_default_models(self) -> Dict[str, str]:
        """Ambil default models dari environment variables"""
        return {
            'text': self.normalize_model_id(os.getenv('DEFAULT_TEXT_MODEL', 'google/gemini-2.5-flash-preview-09-2025')),
            'vision': self.normalize_model_id(os.getenv('DEFAULT_VISION_MODEL', 'google/gemini-2.5-flash-preview-09-2025')),
            'pdf': self.normalize_model_id(os.getenv('DEFAULT_PDF_MODEL', 'google/gemini-2.5-flash-preview-09-2025')),
            'multimodal': self.normalize_model_id(os.getenv('DEFAULT_MULTIMODAL_MODEL', 'google/gemini-2.5-flash-preview-09-2025'))
        }
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Dapatkan informasi model berdasarkan ID"""
        return self.models.get(model_id)
    
    def get_default_model(self, model_type: str) -> str:
        """Dapatkan default model untuk tipe tertentu"""
        return self.normalize_model_id(self.default_models.get(model_type, 'google/gemini-2.5-pro'))

    def normalize_model_id(self, model_id: Optional[str]) -> str:
        """Normalisasi ID model ke bentuk yang valid di OpenRouter (gunakan -latest)."""
        if not model_id:
            return 'google/gemini-2.5-pro'
        mapping = {
            # Flash variants - use valid OpenRouter model IDs
            'google/gemini-2.5-flash-preview-09-2025': 'google/gemini-2.5-flash-preview-09-2025',
            'google/gemini-2.5-flash-preview-09-2025-002': 'google/gemini-2.5-flash-preview-09-2025',
            'google/gemini-2.5-flash-preview-09-2025-latest': 'google/gemini-2.5-flash-preview-09-2025',
            # Pro variants - use valid OpenRouter model IDs
            'google/gemini-1.5-pro': 'google/gemini-2.5-pro',
            'google/gemini-1.5-pro-002': 'google/gemini-2.5-pro',
            'google/gemini-2.5-flash-preview-09-2025': 'google/gemini-2.5-flash-preview-09-2025',
            # Legacy aliases
            'google/gemini-pro': 'google/gemini-2.5-pro',
            'google/gemini-pro-vision': 'google/gemini-2.5-flash-preview-09-2025',
            # Without google/ prefix
            'gemini-1.5-flash': 'google/gemini-2.5-flash-preview-09-2025',
            'gemini-1.5-pro': 'google/gemini-2.5-pro',
            'gemini-1.5-flash-002': 'google/gemini-2.5-flash-preview-09-2025',
            'gemini-1.5-pro-002': 'google/gemini-2.5-pro',
            'gemini-pro': 'google/gemini-2.5-pro',
            'gemini-pro-vision': 'google/gemini-2.5-flash-preview-09-2025',
        }
        normalized = mapping.get(model_id, model_id)
        return normalized
    
    def list_models(self, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List semua model atau filter berdasarkan tipe"""
        if model_type:
            return [
                {'id': model_id, **model_info}
                for model_id, model_info in self.models.items()
                if model_info['type'] == model_type
            ]
        return [
            {'id': model_id, **model_info}
            for model_id, model_info in self.models.items()
        ]
    
    def get_model_parameters(self, model_id: str) -> Dict[str, Any]:
        """Dapatkan parameter default untuk model tertentu"""
        model_info = self.get_model_info(model_id)
        if model_info:
            return model_info.get('parameters', {})
        return {}
    
    def is_vision_supported(self, model_id: str) -> bool:
        """Cek apakah model mendukung vision"""
        model_info = self.get_model_info(model_id)
        return model_info.get('supports_vision', False) if model_info else False
    
    def get_model_cost(self, model_id: str, token_count: int) -> float:
        """Hitung cost untuk jumlah token tertentu"""
        model_info = self.get_model_info(model_id)
        if model_info:
            cost_per_1k = model_info.get('cost_per_1k_tokens', 0)
            return (token_count / 1000) * cost_per_1k
        return 0.0
    
    def validate_model(self, model_id: str) -> bool:
        """Validasi apakah model ID valid"""
        return model_id in self.models
    
    def get_models_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Dapatkan semua model dari provider tertentu"""
        return [
            {'id': model_id, **model_info}
            for model_id, model_info in self.models.items()
            if model_info['provider'] == provider
        ]
    
    def add_custom_model(self, model_id: str, model_config: Dict[str, Any]) -> bool:
        """Tambah custom model ke registry"""
        try:
            if model_id in self.models:
                logger.warning(f"Model {model_id} already exists, updating...")
            
            self.models[model_id] = model_config
            logger.info(f"Custom model {model_id} added successfully")
            return True
        except Exception as e:
            logger.error(f"Error adding custom model {model_id}: {e}")
            return False
    
    def remove_model(self, model_id: str) -> bool:
        """Hapus model dari registry"""
        try:
            if model_id in self.models:
                del self.models[model_id]
                logger.info(f"Model {model_id} removed successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing model {model_id}: {e}")
            return False
    
    def get_cost_effective_model(self, task_type: str, complexity: str = 'medium') -> str:
        """Pilih model berdasarkan cost dan kebutuhan task (Smart Model Selection)"""
        try:
            # Task complexity mapping
            complexity_weights = {
                'low': 1,
                'medium': 2,
                'high': 3,
                'complex': 4
            }
            
            # Model cost effectiveness (lower is better)
            model_scores = {
                'google/gemini-2.5-flash-preview-09-2025': {
                    'cost': 0.0003,
                    'capability': 3,
                    'speed': 5,
                    'vision': True
                },
                'google/gemini-1.5-pro': {
                    'cost': 0.0005,
                    'capability': 5,
                    'speed': 3,
                    'vision': True
                },
                'google/gemini-pro': {
                    'cost': 0.0005,
                    'capability': 4,
                    'speed': 4,
                    'vision': False
                },
                'google/gemini-pro-vision': {
                    'cost': 0.0005,
                    'capability': 4,
                    'speed': 4,
                    'vision': True
                },
                'anthropic/claude-3.5-sonnet': {
                    'cost': 0.0003,
                    'capability': 4,
                    'speed': 4,
                    'vision': False
                },
                'anthropic/claude-3.5-sonnet-20241022': {
                    'cost': 0.0003,
                    'capability': 5,
                    'speed': 4,
                    'vision': True
                }
            }
            
            # Task type requirements
            task_requirements = {
                'simple_chat': {
                    'capability': 2,
                    'vision': False,
                    'speed': 4
                },
                'knowledge_base': {
                    'capability': 3,
                    'vision': False,
                    'speed': 3
                },
                'complex_analysis': {
                    'capability': 5,
                    'vision': False,
                    'speed': 2
                },
                'vision_analysis': {
                    'capability': 4,
                    'vision': True,
                    'speed': 3
                },
                'pdf_processing': {
                    'capability': 4,
                    'vision': True,
                    'speed': 3
                },
                'multimodal': {
                    'capability': 4,
                    'vision': True,
                    'speed': 3
                },
                'telegram_chat': {
                    'capability': 3,
                    'vision': True,
                    'speed': 4
                }
            }
            
            # Get task requirements
            task_req = task_requirements.get(task_type, task_requirements['simple_chat'])
            complexity_weight = complexity_weights.get(complexity, 2)
            
            # Calculate scores for each model
            best_model = 'google/gemini-2.5-flash-preview-09-2025'  # default
            best_score = float('inf')
            
            for model_id, model_info in model_scores.items():
                # Check if model meets vision requirement
                if task_req['vision'] and not model_info['vision']:
                    continue
                
                # Calculate weighted score (lower is better)
                cost_score = model_info['cost'] * 1000  # Scale cost
                capability_score = (task_req['capability'] - model_info['capability']) ** 2
                speed_score = (task_req['speed'] - model_info['speed']) ** 2
                
                # Weight by complexity
                total_score = (cost_score * 0.4 + 
                             capability_score * 0.3 * complexity_weight + 
                             speed_score * 0.3)
                
                if total_score < best_score:
                    best_score = total_score
                    best_model = model_id
            
            logger.info(f"🎯 Smart Model Selection: {task_type} ({complexity}) → {best_model} (score: {best_score:.2f})")
            return best_model
            
        except Exception as e:
            logger.error(f"❌ Error in smart model selection: {e}")
            return 'google/gemini-2.5-flash-preview-09-2025'  # fallback
    
    def get_optimized_parameters(self, model_id: str, task_type: str) -> Dict[str, Any]:
        """Dapatkan parameter yang dioptimalkan untuk hemat token"""
        try:
            base_params = self.get_model_parameters(model_id)
            
            # Task-specific optimizations
            optimizations = {
                'simple_chat': {
                    'temperature': 0.3,
                    'top_p': 0.8,
                    'max_tokens': 1024,
                    'presence_penalty': 0.1,
                    'frequency_penalty': 0.1
                },
                'knowledge_base': {
                    'temperature': 0.2,
                    'top_p': 0.7,
                    'max_tokens': 2048,
                    'presence_penalty': 0.2,
                    'frequency_penalty': 0.1
                },
                'complex_analysis': {
                    'temperature': 0.4,
                    'top_p': 0.9,
                    'max_tokens': 4096,
                    'presence_penalty': 0.1,
                    'frequency_penalty': 0.1
                },
                'vision_analysis': {
                    'temperature': 0.3,
                    'top_p': 0.8,
                    'max_tokens': 2048,
                    'presence_penalty': 0.1,
                    'frequency_penalty': 0.1
                },
                'pdf_processing': {
                    'temperature': 0.2,
                    'top_p': 0.7,
                    'max_tokens': 4096,
                    'presence_penalty': 0.2,
                    'frequency_penalty': 0.1
                },
                'telegram_chat': {
                    'temperature': 0.3,
                    'top_p': 0.8,
                    'max_tokens': 1024,
                    'presence_penalty': 0.1,
                    'frequency_penalty': 0.1
                }
            }
            
            # Merge base parameters with optimizations
            optimized_params = base_params.copy()
            task_optimization = optimizations.get(task_type, optimizations['simple_chat'])
            optimized_params.update(task_optimization)
            
            logger.info(f"🔧 Optimized parameters for {model_id} ({task_type}): {optimized_params}")
            return optimized_params
            
        except Exception as e:
            logger.error(f"❌ Error getting optimized parameters: {e}")
            return self.get_model_parameters(model_id)
    
    def analyze_token_usage(self, model_id: str, input_tokens: int, output_tokens: int) -> Dict[str, Any]:
        """Analisis penggunaan token dan cost"""
        try:
            model_info = self.get_model_info(model_id)
            if not model_info:
                return {'error': 'Model not found'}
            
            cost_per_1k = model_info.get('cost_per_1k_tokens', 0)
            total_tokens = input_tokens + output_tokens
            total_cost = (total_tokens / 1000) * cost_per_1k
            
            # Efficiency metrics
            efficiency_score = 100 - (total_cost * 1000)  # Higher is better
            if efficiency_score < 0:
                efficiency_score = 0
            
            return {
                'model_id': model_id,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'cost_per_1k_tokens': cost_per_1k,
                'total_cost': round(total_cost, 6),
                'efficiency_score': round(efficiency_score, 2),
                'cost_breakdown': {
                    'input_cost': round((input_tokens / 1000) * cost_per_1k, 6),
                    'output_cost': round((output_tokens / 1000) * cost_per_1k, 6)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing token usage: {e}")
            return {'error': str(e)}

# Global instance
ai_model_registry = AIModelRegistry()

def get_model_registry() -> AIModelRegistry:
    """Get global model registry instance"""
    return ai_model_registry
