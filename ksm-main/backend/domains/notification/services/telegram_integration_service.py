#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Integration Service - Menghubungkan bot Telegram dengan Agent AI
"""

import requests
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import threading
import os

# RAG integration (gantikan unified_rag_service dengan qdrant_service langsung)
from domains.knowledge.services.qdrant_service import get_qdrant_service
from domains.knowledge.services.openai_embedding_service import OpenAIEmbeddingService
from config.config import Config

logger = logging.getLogger(__name__)

class TelegramIntegrationService:
    """Service untuk integrasi Telegram dengan Agent AI + Webhook handling"""
    
    def __init__(self):
        # Use environment variable with fallback to config or default
        self.agent_ai_url = os.getenv('AGENT_AI_URL', 'http://localhost:5000')
        self.webhook_url = None
        self.bot_token = None
        self.bot_info = None  # Store real bot info
        self.is_active = False
        self.last_health_check = None
        self.health_check_interval = 30  # seconds
        # Polling mode controls
        self._polling_enabled = False
        self._polling_thread = None
        self._last_update_id = None
        
        # Agent AI Sync Service untuk health check dan forward
        try:
            from domains.integration.services.agent_ai_sync_service import agent_ai_sync
            self.agent_ai_sync = agent_ai_sync
            logger.info("[SUCCESS] Agent AI Sync Service imported for Telegram integration")
        except ImportError as e:
            logger.warning(f"[WARNING] Agent AI Sync Service not available: {e}")
            self.agent_ai_sync = None
        
        # Start health check thread
        self._start_health_check_thread()
    
    def _start_health_check_thread(self):
        """Start thread untuk health check Agent AI"""
        def health_check_loop():
            while True:
                try:
                    self._check_agent_ai_health()
                    time.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"Health check error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        thread = threading.Thread(target=health_check_loop, daemon=True)
        thread.start()
        logger.info("Agent AI health check thread started")
    
    def _check_agent_ai_health(self):
        """Check kesehatan Agent AI"""
        try:
            # Try /status first (always returns 200 if service is running)
            response = requests.get(f"{self.agent_ai_url}/status", timeout=5)
            if response.status_code == 200:
                self.last_health_check = datetime.now()
                logger.debug("Agent AI health check successful (via /status)")
                return
            
            # Fallback to /health endpoint
            response = requests.get(f"{self.agent_ai_url}/health", timeout=5)
            if response.status_code == 200:
                self.last_health_check = datetime.now()
                logger.debug("Agent AI health check successful (via /health)")
            elif response.status_code == 503:
                # Check if it's just LLM service not initialized (expected)
                try:
                    data = response.json()
                    components = data.get('components', {})
                    llm_status = components.get('llm_service', {})
                    if llm_status.get('status') == 'not_initialized':
                        # This is expected, service is running but LLM not initialized yet
                        self.last_health_check = datetime.now()
                        logger.debug("Agent AI is running (LLM service not initialized yet)")
                        return
                except:
                    pass
                logger.warning(f"Agent AI health check failed: {response.status_code}")
            else:
                logger.warning(f"Agent AI health check failed: {response.status_code}")
        except Exception as e:
            logger.warning(f"Agent AI health check error: {e}")
    
    def set_bot_token(self, bot_token: str) -> bool:
        """Set bot token dan setup webhook"""
        try:
            self.bot_token = bot_token
            
            # Test koneksi ke Telegram API
            response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
            if response.status_code != 200:
                logger.error(f"Invalid bot token: {response.status_code}")
                return False
            
            bot_data = response.json()
            if bot_data.get('ok'):
                self.bot_info = bot_data.get('result', {})
                bot_name = self.bot_info.get('first_name', 'Unknown')
                bot_username = self.bot_info.get('username', 'unknown')
                logger.info(f"Bot connected: {bot_name} (@{bot_username})")
            else:
                logger.error(f"Telegram API error: {bot_data}")
                return False
            
            # Setup webhook
            if self._setup_webhook():
                self.is_active = True
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error setting bot token: {e}")
            return False
    
    def _setup_webhook(self) -> bool:
        """Setup webhook untuk bot"""
        try:
            if not self.bot_token:
                logger.error("Bot token not set")
                return False
            
            # Untuk development, coba gunakan ngrok URL jika tersedia
            # Jika tidak ada, skip webhook dan gunakan polling mode
            ngrok_url = self._get_ngrok_url()
            
            if ngrok_url:
                webhook_url = f"{ngrok_url}/api/telegram/webhook"
                logger.info(f"Using ngrok URL for webhook: {webhook_url}")
            else:
                # Untuk development tanpa ngrok, hapus webhook dan gunakan mode polling
                logger.info("No HTTPS URL available, removing webhook and using polling mode")
                ok = self._remove_webhook_for_polling()
                if ok:
                    self._start_polling_thread()
                    self.is_active = True
                return ok
            
            # Set webhook di Telegram
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/setWebhook",
                json={'url': webhook_url},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.webhook_url = webhook_url
                    logger.info(f"Webhook set successfully: {webhook_url}")
                    # Webhook set: aktifkan bot dan matikan polling jika ada
                    self.is_active = True
                    self._stop_polling()
                    return True
                else:
                    logger.error(f"Failed to set webhook: {result}")
                    # Fallback ke polling mode
                    ok = self._remove_webhook_for_polling()
                    if ok:
                        self._start_polling_thread()
                        self.is_active = True
                    return ok
            else:
                logger.error(f"Failed to set webhook: {response.status_code}")
                # Fallback ke polling mode
                ok = self._remove_webhook_for_polling()
                if ok:
                    self._start_polling_thread()
                    self.is_active = True
                return ok
                
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            # Fallback ke polling mode
            return self._remove_webhook_for_polling()
    
    def _get_ngrok_url(self) -> Optional[str]:
        """Cek apakah ngrok sedang running dan dapatkan URL"""
        try:
            # Cek ngrok API untuk mendapatkan URL
            response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                for tunnel in tunnels:
                    if tunnel.get('proto') == 'https':
                        public_url = tunnel.get('public_url')
                        if public_url:
                            logger.info(f"Found ngrok HTTPS URL: {public_url}")
                            return public_url
            return None
        except Exception as e:
            logger.debug(f"Ngrok not available: {e}")
            return None
    
    def _remove_webhook_for_polling(self) -> bool:
        """Hapus webhook untuk menggunakan polling mode"""
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/deleteWebhook",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.webhook_url = None
                    logger.info("Webhook removed, bot ready for polling mode")
                    return True
                else:
                    logger.warning(f"Failed to remove webhook: {result}")
                    # Tetap return True karena bot masih bisa berfungsi
                    return True
            else:
                logger.warning(f"Failed to remove webhook: {response.status_code}")
                # Tetap return True karena bot masih bisa berfungsi
                return True
                
        except Exception as e:
            logger.warning(f"Error removing webhook: {e}")
            # Tetap return True karena bot masih bisa berfungsi
            return True
    
    def remove_webhook(self) -> bool:
        """Remove webhook dari bot"""
        try:
            if not self.bot_token:
                return True
            
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/deleteWebhook",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.webhook_url = None
                    self.is_active = False
                    self._stop_polling()
                    logger.info("Webhook removed successfully")
                    return True
                else:
                    logger.error(f"Failed to remove webhook: {result}")
                    return False
            else:
                logger.error(f"Failed to remove webhook: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing webhook: {e}")
            return False
    
    def send_message_to_agent(self, user_id: int, message: str, session_id: str = None, company_id: str = None) -> Dict[str, Any]:
        """Forward pesan ke Agent AI telegram endpoint untuk diproses dengan RAG context dan caching"""
        try:
            if not self.is_active:
                return {
                    'success': False,
                    'message': 'Bot tidak aktif'
                }
            
            # Use default company_id if not provided
            if company_id is None:
                company_id = Config.DEFAULT_COMPANY_ID
            
            # Check cache terlebih dahulu
            message_hash = self._generate_message_hash(message)
            cached_response = self.get_cached_response(user_id, message_hash)
            if cached_response:
                return {
                    **cached_response,
                    'cached': True,
                    'method': 'cached_response'
                }
            
            # Check Agent AI health terlebih dahulu
            if not self.agent_ai_sync:
                return {
                    'success': False,
                    'message': 'Agent AI sync service tidak tersedia'
                }
            
            # Check Agent AI connection
            health_status = self.agent_ai_sync.check_agent_ai_health()
            if not health_status.get('success'):
                return {
                    'success': False,
                    'message': f'Agent AI tidak tersedia: {health_status.get("status", "unknown")}'
                }
            
            # Build RAG context sebelum mengirim ke Agent AI (menggunakan qdrant_service)
            rag_context = self._build_rag_context(company_id, message)
            
            # Prepare data untuk Agent AI telegram endpoint dengan RAG context
            chat_data = {
                'user_id': user_id,
                'message': message,
                'session_id': session_id or f'telegram_{user_id}',
                'source': 'KSM_main_telegram',
                'timestamp': datetime.now().isoformat(),
                'company_id': company_id,
                'rag_context': rag_context  # Include RAG context
            }
            
            # Forward ke Agent AI telegram endpoint
            start_time = time.time()
            response = requests.post(
                f"{self.agent_ai_url}/api/telegram/chat",
                json=chat_data,
                headers={
                    'Content-Type': 'application/json',
                    'X-API-Key': 'KSM_api_key_2ptybn'  # Default API key
                },
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    response_data = {
                        'success': True,
                        'data': result.get('data', {}),
                        'message': 'Pesan berhasil diproses oleh Agent AI',
                        'response_time': response_time,
                        'method': 'agent_ai_forward'
                    }
                    
                    # Cache response untuk future use
                    self.cache_response(user_id, message_hash, response_data)
                    
                    return response_data
                else:
                    logger.warning(f"Agent AI response failed: {result.get('message', 'Unknown error')}")
                    return {
                        'success': False,
                        'message': f'Agent AI response error: {result.get("message", "Unknown error")}'
                    }
            else:
                logger.error(f"Agent AI request failed with status {response.status_code}")
                return {
                    'success': False,
                    'message': f'Gagal memproses pesan di Agent AI (Status: {response.status_code})'
                }
                
        except requests.exceptions.Timeout:
            logger.error("Timeout saat forward ke Agent AI")
            return {
                'success': False,
                'message': 'Timeout: Agent AI tidak merespons'
            }
        except Exception as e:
            logger.error(f"Error forwarding message to Agent AI: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def get_bot_status(self) -> Dict[str, Any]:
        """Get status bot dan integrasi"""
        mode = 'webhook' if self.webhook_url else 'polling'
        return {
            'bot_active': self.is_active,
            'bot_token_set': bool(self.bot_token),
            'bot_info': self.bot_info,
            'webhook_url': self.webhook_url,
            'mode': mode,
            'agent_ai_url': self.agent_ai_url,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'ngrok_available': self._get_ngrok_url() is not None,
            'timestamp': datetime.now().isoformat()
        }
    
    def test_agent_ai_connection(self) -> Dict[str, Any]:
        """Test koneksi ke Agent AI"""
        try:
            response = requests.get(f"{self.agent_ai_url}/health", timeout=5)
            if response.status_code == 200:
                return {
                    'success': True,
                    'status': 'connected',
                    'response_time': response.elapsed.total_seconds(),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'status': 'error',
                    'error_code': response.status_code,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'success': False,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_cached_response(self, user_id: int, message_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached response untuk user dan message tertentu"""
        try:
            # Simple in-memory cache (bisa di-upgrade ke Redis/database nanti)
            cache_key = f"telegram_cache_{user_id}_{message_hash}"
            
            # Check cache expiration (5 menit)
            if hasattr(self, '_response_cache') and cache_key in self._response_cache:
                cached_data = self._response_cache[cache_key]
                if time.time() - cached_data['timestamp'] < 300:  # 5 menit
                    logger.info(f"Cache hit untuk user {user_id}")
                    return cached_data['response']
                else:
                    # Remove expired cache
                    del self._response_cache[cache_key]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached response: {e}")
            return None
    
    def cache_response(self, user_id: int, message_hash: str, response: Dict[str, Any]) -> bool:
        """Cache response untuk user dan message tertentu"""
        try:
            if not hasattr(self, '_response_cache'):
                self._response_cache = {}
            
            cache_key = f"telegram_cache_{user_id}_{message_hash}"
            self._response_cache[cache_key] = {
                'response': response,
                'timestamp': time.time()
            }
            
            # Cleanup old cache entries (keep only last 100)
            if len(self._response_cache) > 100:
                oldest_keys = sorted(self._response_cache.keys(), 
                                   key=lambda k: self._response_cache[k]['timestamp'])[:50]
                for key in oldest_keys:
                    del self._response_cache[key]
            
            logger.info(f"Response cached untuk user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching response: {e}")
            return False
    
    def _generate_message_hash(self, message: str) -> str:
        """Generate hash untuk message untuk cache key"""
        import hashlib
        return hashlib.md5(message.encode()).hexdigest()[:8]
    
    # --- Webhook handling methods ---
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Proses webhook data dari Telegram"""
        try:
            logger.info(f"Processing webhook: {webhook_data.get('update_id', 'unknown')}")
            
            # Extract message data
            message_data = self._extract_message_data(webhook_data)
            if not message_data:
                logger.warning("No valid message data found in webhook")
                return {'success': False, 'message': 'No valid message data'}
            
            # Process message
            result = self._process_message(message_data)
            
            # Send response back to user via Telegram API
            if result['success']:
                self._send_telegram_response(
                    chat_id=message_data['chat_id'],
                    text=result['data']['response']
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def _extract_message_data(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract data message dari webhook"""
        try:
            # Check if it's a message update
            if 'message' in webhook_data:
                message = webhook_data['message']
                
                # Check if it's a text message
                if 'text' in message and message['text']:
                    return {
                        'update_id': webhook_data.get('update_id'),
                        'message_id': message.get('message_id'),
                        'chat_id': message.get('chat', {}).get('id'),
                        'user_id': message.get('from', {}).get('id'),
                        'username': message.get('from', {}).get('username'),
                        'first_name': message.get('from', {}).get('first_name'),
                        'text': message.get('text'),
                        'timestamp': message.get('date'),
                        'chat_type': message.get('chat', {}).get('type')
                    }
                
                # Check if it's a photo message
                elif 'photo' in message and message['photo']:
                    photo = message['photo'][-1]  # Get highest quality photo
                    return {
                        'update_id': webhook_data.get('update_id'),
                        'message_id': message.get('message_id'),
                        'chat_id': message.get('chat', {}).get('id'),
                        'user_id': message.get('from', {}).get('id'),
                        'username': message.get('from', {}).get('username'),
                        'first_name': message.get('from', {}).get('first_name'),
                        'photo_file_id': photo.get('file_id'),
                        'photo_width': photo.get('width'),
                        'photo_height': photo.get('height'),
                        'timestamp': message.get('date'),
                        'chat_type': message.get('chat', {}).get('type')
                    }
            
            # Check if it's a callback query (button press)
            elif 'callback_query' in webhook_data:
                callback_query = webhook_data['callback_query']
                message = callback_query.get('message', {})
                
                return {
                    'update_id': webhook_data.get('update_id'),
                    'callback_query_id': callback_query.get('id'),
                    'chat_id': message.get('chat', {}).get('id'),
                    'user_id': callback_query.get('from', {}).get('id'),
                    'username': callback_query.get('from', {}).get('username'),
                    'first_name': callback_query.get('from', {}).get('first_name'),
                    'data': callback_query.get('data'),
                    'timestamp': callback_query.get('date'),
                    'chat_type': message.get('chat', {}).get('type')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting message data: {e}")
            return None
    
    def _process_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process message data dan forward ke Agent AI"""
        try:
            # Prepare data untuk Agent AI
            agent_data = {
                'message': message_data.get('text', ''),
                'user_id': message_data.get('user_id'),
                'username': message_data.get('username'),
                'first_name': message_data.get('first_name'),
                'chat_id': message_data.get('chat_id'),
                'message_id': message_data.get('message_id'),
                'timestamp': message_data.get('timestamp'),
                'chat_type': message_data.get('chat_type')
            }
            
            # Add photo data if available
            if 'photo_file_id' in message_data:
                agent_data['photo_file_id'] = message_data['photo_file_id']
                agent_data['photo_width'] = message_data.get('photo_width')
                agent_data['photo_height'] = message_data.get('photo_height')
            
            # Add callback query data if available
            if 'callback_query_id' in message_data:
                agent_data['callback_query_id'] = message_data['callback_query_id']
                agent_data['callback_data'] = message_data.get('data')
            
            # Forward ke Agent AI
            if self.agent_ai_sync:
                result = self.agent_ai_sync.forward_telegram_message(agent_data)
                return result
            else:
                # Fallback jika Agent AI tidak tersedia
                return {
                    'success': True,
                    'data': {
                        'response': 'Maaf, layanan AI sedang tidak tersedia. Silakan coba lagi nanti.',
                        'method': 'fallback'
                    }
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                'success': False,
                'message': f'Error processing message: {str(e)}'
            }
    
    def _send_telegram_response(self, chat_id: int, text: str) -> bool:
        """Send response ke Telegram user dengan optimisasi"""
        try:
            if not self.bot_token:
                logger.warning("Bot token not set, cannot send response")
                return False
            
            # Optimize response untuk Telegram
            optimized_text = self._optimize_telegram_response(text)
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': optimized_text,
                'parse_mode': 'HTML'
            }
            
            # Retry mechanism untuk menghindari timeout
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, json=data, timeout=15)  # Increased timeout
                    
                    if response.status_code == 200:
                        logger.info(f"Response sent to chat {chat_id}")
                        return True
                    else:
                        logger.warning(f"Attempt {attempt + 1}: Failed to send response: {response.status_code} - {response.text}")
                        if attempt < max_retries - 1:
                            time.sleep(1)  # Wait before retry
                        else:
                            logger.error(f"Failed to send response after {max_retries} attempts")
                            return False
                            
                except requests.exceptions.Timeout:
                    logger.warning(f"Attempt {attempt + 1}: Telegram API timeout")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait before retry
                    else:
                        logger.error(f"Telegram API timeout after {max_retries} attempts")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending Telegram response: {e}")
            return False
    
    def _build_rag_context(self, company_id: str, query: str) -> Dict[str, Any]:
        """Build RAG context menggunakan Qdrant service + OpenAI embeddings (tanpa unified_rag_service)."""
        try:
            # Konfigurasi Telegram RAG
            top_k = int(os.getenv('TELEGRAM_RAG_TOP_K', '5'))
            similarity_threshold = float(os.getenv('TELEGRAM_RAG_SIMILARITY_THRESHOLD', '0.3'))

            logger.info(f"🔍 Building RAG context for query: {query[:50]}... (top_k={top_k}, threshold={similarity_threshold})")

            qdrant_service = get_qdrant_service()
            embedding_service = OpenAIEmbeddingService()

            # Generate embedding
            query_embedding = embedding_service.embed_text(query)
            if not query_embedding:
                return {
                    'rag_results': [],
                    'total_chunks': 0,
                    'avg_similarity': 0.0,
                    'context_available': False
                }

            # Qdrant search
            results = qdrant_service.search_documents(
                company_id=company_id,
                query=query,
                top_k=top_k,
                collection='default',
                query_embedding=query_embedding
            ) or []

            # Normalisasi dan filter threshold
            normalized = []
            total_similarity = 0.0
            for r in results:
                text = r.get('text') if isinstance(r, dict) else ''
                metadata = r.get('metadata') if isinstance(r, dict) else {}
                sim = r.get('similarity_score') if isinstance(r, dict) else 0.0
                if sim is None:
                    sim = 0.0
                if float(sim) >= similarity_threshold:
                    normalized.append({
                        'content': text or '',
                        'similarity': float(sim),
                        'source_document': str((metadata or {}).get('document_id') or ''),
                        'chunk_id': str((metadata or {}).get('chunk_id') or ''),
                        'metadata': metadata or {}
                    })
                    total_similarity += float(sim)

            # Fallback adaptif jika semua tersaring
            if not normalized and results:
                logger.info("⚠️ No results passed threshold (telegram integration), using adaptive fallback with top results")
                for r in results[:3]:
                    text = r.get('text') if isinstance(r, dict) else ''
                    metadata = r.get('metadata') if isinstance(r, dict) else {}
                    sim = r.get('similarity_score') if isinstance(r, dict) else 0.0
                    sim = float(sim or 0.0)
                    normalized.append({
                        'content': text or '',
                        'similarity': sim,
                        'source_document': str((metadata or {}).get('document_id') or ''),
                        'chunk_id': str((metadata or {}).get('chunk_id') or ''),
                        'metadata': metadata or {}
                    })
                    total_similarity += sim

            avg_similarity = (total_similarity / len(normalized)) if normalized else 0.0

            logger.info(f"[SUCCESS] RAG context built: {len(normalized)} chunks, avg_similarity: {avg_similarity:.3f}")

            return {
                'rag_results': normalized,
                'total_chunks': len(normalized),
                'avg_similarity': round(avg_similarity, 3),
                'context_available': len(normalized) > 0,
                'query': query,
                'company_id': company_id
            }

        except Exception as e:
            logger.error(f"[ERROR] Error building RAG context: {e}")
            return {
                'rag_results': [],
                'total_chunks': 0,
                'avg_similarity': 0.0,
                'context_available': False,
                'error': str(e)
            }
    
    def _optimize_telegram_response(self, text: str) -> str:
        """Optimize response text untuk Telegram"""
        try:
            # Telegram memiliki batasan 4096 karakter per pesan
            max_length = 4000  # Leave some buffer
            
            if len(text) <= max_length:
                return text
            
            # Jika terlalu panjang, potong dan tambahkan indikator
            truncated = text[:max_length - 100]  # Leave space for indicator
            
            # Cari titik potong yang baik (akhir kalimat)
            last_period = truncated.rfind('.')
            last_newline = truncated.rfind('\n')
            
            if last_period > max_length * 0.8:  # Jika ada titik di 80% terakhir
                truncated = truncated[:last_period + 1]
            elif last_newline > max_length * 0.8:  # Jika ada newline di 80% terakhir
                truncated = truncated[:last_newline]
            
            # Tambahkan indikator
            truncated += "\n\n<i>... (respons dipotong karena terlalu panjang)</i>"
            
            return truncated
            
        except Exception as e:
            logger.warning(f"Error optimizing Telegram response: {e}")
            # Fallback: potong sederhana
            return text[:4000] + "\n\n<i>... (respons dipotong)</i>" if len(text) > 4000 else text

# ---------------- Polling mode ----------------
    def _start_polling_thread(self):
        try:
            if self._polling_thread and self._polling_thread.is_alive():
                return
            self._polling_enabled = True
            self._polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
            self._polling_thread.start()
            logger.info("Telegram polling thread started")
        except Exception as e:
            logger.error(f"Failed to start polling thread: {e}")

    def _stop_polling(self):
        self._polling_enabled = False
        try:
            if self._polling_thread and self._polling_thread.is_alive():
                logger.info("Stopping polling thread...")
        except Exception:
            pass

    def ensure_polling_active(self):
        """Start polling if no webhook and token is available."""
        try:
            if self.bot_token and not self.webhook_url:
                self._start_polling_thread()
                self.is_active = True
                return True
            return False
        except Exception as e:
            logger.error(f"ensure_polling_active error: {e}")
            return False

    def _polling_loop(self):
        """Long-polling getUpdates jika webhook tidak tersedia (dev environment)."""
        import requests as _req
        # telegram_rag_service removed - using Agent AI directly
        # rag = get_telegram_rag_service()  # Removed
        while self._polling_enabled and self.bot_token and not self.webhook_url:
            try:
                params = {
                    'timeout': 25,
                    'allowed_updates': json.dumps(["message", "callback_query"])  # type: ignore
                }
                if self._last_update_id is not None:
                    params['offset'] = self._last_update_id + 1
                resp = _req.get(f"https://api.telegram.org/bot{self.bot_token}/getUpdates", params=params, timeout=30)
                if resp.status_code != 200:
                    time.sleep(2)
                    continue
                data = resp.json()
                if not data.get('ok'):
                    time.sleep(2)
                    continue
                for update in data.get('result', []):
                    self._last_update_id = update.get('update_id', self._last_update_id)
                    # Extract minimal fields
                    message = None
                    chat_id = None
                    if 'message' in update and 'text' in update['message']:
                        message = update['message']['text']
                        chat_id = update['message']['chat']['id']
                    elif 'callback_query' in update:
                        message = update['callback_query'].get('data', '')
                        chat_id = update['callback_query']['message']['chat']['id']
                    if not message or chat_id is None:
                        continue
                    # Use default company_id from config
                    company_id = Config.DEFAULT_COMPANY_ID
                    user_id = chat_id  # Use chat_id as user_id
                    # Forward to Agent AI directly with company_id
                    agent_result = self.send_message_to_agent(
                        user_id=user_id,
                        message=message,
                        session_id=f'telegram_{user_id}',
                        company_id=company_id
                    )
                    if agent_result.get('success') and 'data' in agent_result:
                        response_text = agent_result['data'].get('response', 'Maaf, tidak ada respons dari AI.')
                        self._send_telegram_response(chat_id, response_text)
                # slight delay to avoid tight loop
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Polling loop error: {e}")
                time.sleep(3)

# Global instances
telegram_integration = TelegramIntegrationService()
telegram_webhook = telegram_integration  # Use same instance with webhook support
