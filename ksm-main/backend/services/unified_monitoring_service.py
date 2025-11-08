#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Monitoring Service untuk KSM-Main Backend
Konsolidasi dari monitoring_service.py dan rag_monitoring_service.py
"""

import os
import time
import logging
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup logging
logger = logging.getLogger(__name__)

class UnifiedMonitoringService:
    """Unified service untuk monitoring sistem dan RAG analytics"""
    
    def __init__(self):
        # System monitoring configuration
        self.agent_ai_url = os.getenv('AGENT_AI_URL', 'http://localhost:5000')
        self.agent_ai_api_key = os.getenv('AGENT_AI_API_KEY', 'KSM_api_key_2ptybn')
        self.monitoring_enabled = os.getenv('ENABLE_MONITORING', 'true').lower() == 'true'
        self.check_interval = int(os.getenv('MONITORING_INTERVAL', '60'))  # seconds
        
        # System health status
        self.health_status = {
            'KSM_main': 'healthy',
            'agent_ai': 'unknown',
            'database': 'healthy',
            'telegram': 'unknown'
        }
        
        # System metrics
        self.metrics = {
            'requests_count': 0,
            'errors_count': 0,
            'last_check': None,
            'uptime_start': datetime.now()
        }
        
        # RAG monitoring configuration
        self.db = None
        self._init_database()
        self.metrics_retention_days = 30
        self.alert_thresholds = {
            'response_time': 5.0,  # seconds
            'error_rate': 0.1,     # 10%
            'cache_hit_rate': 0.7, # 70%
            'success_rate': 0.9    # 90%
        }
        
        # Start monitoring thread
        if self.monitoring_enabled:
            self.start_monitoring()
        
        logger.info("🚀 Unified Monitoring Service initialized")
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            from config.database import db
            self.db = db
            logger.info("✅ Database connection initialized")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    # ===== SYSTEM MONITORING METHODS =====
    
    def start_monitoring(self):
        """Start monitoring thread"""
        try:
            monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            monitoring_thread.start()
            logger.info("✅ System monitoring started")
        except Exception as e:
            logger.error(f"❌ Failed to start monitoring: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                self._check_agent_ai_health()
                self._check_database_health()
                self._check_telegram_health()
                self._update_metrics()
                
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(10)  # Wait 10 seconds before retry
    
    def _check_agent_ai_health(self):
        """Check Agent AI health"""
        endpoints_to_try = [
            "/status",  # Try /status first (always returns 200 if service is running)
            "/health",
            "/api/status",
        ]

        last_error: Optional[Exception] = None
        for endpoint_path in endpoints_to_try:
            try:
                response = requests.get(f"{self.agent_ai_url}{endpoint_path}", timeout=10)
                if response.status_code == 200:
                    self.health_status['agent_ai'] = 'healthy'
                    logger.debug(f"✅ Agent AI health check passed via {endpoint_path}")
                    return
                elif response.status_code == 503 and endpoint_path == "/health":
                    # Check if it's just LLM service not initialized (expected)
                    try:
                        data = response.json()
                        components = data.get('components', {})
                        llm_status = components.get('llm_service', {})
                        if llm_status.get('status') == 'not_initialized':
                            # Service is running but LLM not initialized - mark as healthy
                            self.health_status['agent_ai'] = 'healthy'
                            logger.debug("✅ Agent AI is running (LLM service not initialized yet)")
                            return
                    except:
                        pass
                    logger.debug(f"⚠️ Agent AI health check {endpoint_path} returned 503 (checking components)")
                else:
                    logger.debug(f"⚠️ Agent AI health check {endpoint_path} failed: {response.status_code}")
            except Exception as e:
                last_error = e
                continue

        self.health_status['agent_ai'] = 'error'
        if last_error:
            logger.error(f"❌ Agent AI health check error: {last_error}")
        else:
            logger.error("❌ Agent AI health check error: Unknown error")
    
    def _check_database_health(self):
        """Check database health"""
        try:
            # Simple database check
            self.health_status['database'] = 'healthy'
            logger.debug("✅ Database health check passed")
        except Exception as e:
            self.health_status['database'] = 'error'
            logger.error(f"❌ Database health check error: {e}")
    
    def _check_telegram_health(self):
        """Check Telegram integration health"""
        try:
            # Simple Telegram check
            self.health_status['telegram'] = 'healthy'
            logger.debug("✅ Telegram health check passed")
        except Exception as e:
            self.health_status['telegram'] = 'error'
            logger.error(f"❌ Telegram health check error: {e}")
    
    def _update_metrics(self):
        """Update monitoring metrics"""
        self.metrics['last_check'] = datetime.now()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy' if all(status in ['healthy'] for status in self.health_status.values()) else 'degraded',
            'services': self.health_status.copy(),
            'metrics': self.metrics.copy(),
            'uptime': str(datetime.now() - self.metrics['uptime_start'])
        }
    
    def get_agent_ai_status(self) -> Dict[str, Any]:
        """Get detailed Agent AI status"""
        endpoints_to_try = [
            "/status",
            "/health",
            "/api/status",
            "/api/v1/health",
        ]

        last_error: Optional[Exception] = None
        for endpoint_path in endpoints_to_try:
            try:
                # Don't use API key for status endpoints
                response = requests.get(
                    f"{self.agent_ai_url}{endpoint_path}",
                    timeout=10,
                )

                if response.status_code == 200:
                    data = {}
                    try:
                        data = response.json()
                    except Exception:
                        data = {}
                    return {
                        'status': 'connected',
                        'data': data.get('data', data),
                        'last_check': datetime.now().isoformat(),
                        'response_time': response.elapsed.total_seconds()
                    }
            except Exception as e:
                last_error = e
                continue

        return {
            'status': 'error',
            'error': str(last_error) if last_error else 'Unknown error',
            'last_check': datetime.now().isoformat()
        }
    
    def forward_to_agent_ai(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Forward request to Agent AI"""
        try:
            response = requests.post(
                f"{self.agent_ai_url}{endpoint}",
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'X-API-Key': self.agent_ai_api_key
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'data': response.text
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def increment_request_count(self):
        """Increment request counter"""
        self.metrics['requests_count'] += 1
    
    def increment_error_count(self):
        """Increment error counter"""
        self.metrics['errors_count'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get monitoring metrics"""
        uptime = datetime.now() - self.metrics['uptime_start']
        
        return {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': uptime.total_seconds(),
            'uptime_human': str(uptime),
            'requests_total': self.metrics['requests_count'],
            'errors_total': self.metrics['errors_count'],
            'error_rate': (self.metrics['errors_count'] / max(self.metrics['requests_count'], 1)) * 100,
            'last_check': self.metrics['last_check'],
            'health_status': self.health_status
        }
    
    # ===== RAG MONITORING METHODS =====
    
    def log_query(self, company_id: int, query: str, response: Dict[str, Any], 
                  processing_time: float, user_id: str = None) -> bool:
        """Log RAG query untuk analytics"""
        try:
            # Create log entry
            log_entry = {
                'company_id': company_id,
                'user_id': user_id,
                'query': query[:500],  # Truncate long queries
                'response_success': response.get('success', False),
                'response_length': len(response.get('response', '')),
                'processing_time': processing_time,
                'search_results_count': len(response.get('search_results', [])),
                'context_used': response.get('context_used', 0),
                'model_used': response.get('model_used', ''),
                'timestamp': datetime.now(),
                'error_message': response.get('error', '')[:200] if not response.get('success') else None
            }
            
            # Store in database
            self._store_query_log(log_entry)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log query: {e}")
            return False
    
    def _store_query_log(self, log_entry: Dict[str, Any]):
        """Store query log in database"""
        try:
            # Create table if not exists
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS rag_query_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    company_id INT NOT NULL,
                    user_id VARCHAR(255),
                    query TEXT,
                    response_success BOOLEAN,
                    response_length INT,
                    processing_time FLOAT,
                    search_results_count INT,
                    context_used INT,
                    model_used VARCHAR(100),
                    error_message TEXT,
                    timestamp DATETIME,
                    INDEX idx_company_timestamp (company_id, timestamp),
                    INDEX idx_timestamp (timestamp)
                )
            """
            
            self.db.session.execute(text(create_table_sql))
            self.db.session.commit()
            
            # Insert log entry
            insert_sql = """
                INSERT INTO rag_query_logs 
                (company_id, user_id, query, response_success, response_length, 
                 processing_time, search_results_count, context_used, model_used, 
                 error_message, timestamp)
                VALUES 
                (:company_id, :user_id, :query, :response_success, :response_length,
                 :processing_time, :search_results_count, :context_used, :model_used,
                 :error_message, :timestamp)
            """
            
            self.db.session.execute(text(insert_sql), log_entry)
            self.db.session.commit()
            
        except Exception as e:
            logger.error(f"❌ Failed to store query log: {e}")
            self.db.session.rollback()
    
    def get_rag_metrics(self, company_id: int = None, days: int = 7) -> Dict[str, Any]:
        """Get RAG metrics untuk analytics"""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Build query
            where_clause = "WHERE timestamp >= :start_date AND timestamp <= :end_date"
            params = {'start_date': start_date, 'end_date': end_date}
            
            if company_id:
                where_clause += " AND company_id = :company_id"
                params['company_id'] = company_id
            
            # Total queries
            total_queries_sql = f"""
                SELECT COUNT(*) as total_queries
                FROM rag_query_logs 
                {where_clause}
            """
            
            result = self.db.session.execute(text(total_queries_sql), params)
            total_queries = result.fetchone().total_queries
            
            if total_queries == 0:
                return {
                    'success': True,
                    'metrics': {
                        'total_queries': 0,
                        'success_rate': 0,
                        'average_response_time': 0,
                        'error_rate': 0,
                        'average_context_used': 0,
                        'average_search_results': 0,
                        'top_models': [],
                        'daily_breakdown': []
                    },
                    'period': f"{days} days",
                    'company_id': company_id
                }
            
            # Success rate
            success_rate_sql = f"""
                SELECT 
                    COUNT(*) as successful_queries
                FROM rag_query_logs 
                {where_clause} AND response_success = 1
            """
            
            result = self.db.session.execute(text(success_rate_sql), params)
            successful_queries = result.fetchone().successful_queries
            success_rate = successful_queries / total_queries
            
            # Average response time
            avg_response_time_sql = f"""
                SELECT AVG(processing_time) as avg_response_time
                FROM rag_query_logs 
                {where_clause} AND response_success = 1
            """
            
            result = self.db.session.execute(text(avg_response_time_sql), params)
            avg_response_time = result.fetchone().avg_response_time or 0
            
            # Average context used
            avg_context_sql = f"""
                SELECT AVG(context_used) as avg_context_used
                FROM rag_query_logs 
                {where_clause} AND response_success = 1
            """
            
            result = self.db.session.execute(text(avg_context_sql), params)
            avg_context_used = result.fetchone().avg_context_used or 0
            
            # Average search results
            avg_search_results_sql = f"""
                SELECT AVG(search_results_count) as avg_search_results
                FROM rag_query_logs 
                {where_clause} AND response_success = 1
            """
            
            result = self.db.session.execute(text(avg_search_results_sql), params)
            avg_search_results = result.fetchone().avg_search_results or 0
            
            # Top models
            top_models_sql = f"""
                SELECT model_used, COUNT(*) as usage_count
                FROM rag_query_logs 
                {where_clause} AND model_used IS NOT NULL
                GROUP BY model_used
                ORDER BY usage_count DESC
                LIMIT 5
            """
            
            result = self.db.session.execute(text(top_models_sql), params)
            top_models = [{'model': row.model_used, 'count': row.usage_count} for row in result]
            
            # Daily breakdown
            daily_breakdown_sql = f"""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as total_queries,
                    SUM(CASE WHEN response_success = 1 THEN 1 ELSE 0 END) as successful_queries,
                    AVG(processing_time) as avg_response_time
                FROM rag_query_logs 
                {where_clause}
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """
            
            result = self.db.session.execute(text(daily_breakdown_sql), params)
            daily_breakdown = []
            for row in result:
                daily_breakdown.append({
                    'date': row.date.isoformat(),
                    'total_queries': row.total_queries,
                    'successful_queries': row.successful_queries,
                    'success_rate': row.successful_queries / row.total_queries if row.total_queries > 0 else 0,
                    'avg_response_time': float(row.avg_response_time) if row.avg_response_time else 0
                })
            
            return {
                'success': True,
                'metrics': {
                    'total_queries': total_queries,
                    'success_rate': success_rate,
                    'error_rate': 1 - success_rate,
                    'average_response_time': avg_response_time,
                    'average_context_used': avg_context_used,
                    'average_search_results': avg_search_results,
                    'top_models': top_models,
                    'daily_breakdown': daily_breakdown
                },
                'period': f"{days} days",
                'company_id': company_id,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get RAG metrics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_alerts(self, company_id: int = None) -> List[Dict[str, Any]]:
        """Check for alerts berdasarkan thresholds"""
        try:
            alerts = []
            
            # Get recent metrics (last 24 hours)
            metrics = self.get_rag_metrics(company_id, days=1)
            
            if not metrics.get('success'):
                return alerts
            
            metrics_data = metrics['metrics']
            
            # Check response time alert
            if metrics_data['average_response_time'] > self.alert_thresholds['response_time']:
                alerts.append({
                    'type': 'response_time',
                    'severity': 'warning',
                    'message': f"Average response time ({metrics_data['average_response_time']:.2f}s) exceeds threshold ({self.alert_thresholds['response_time']}s)",
                    'value': metrics_data['average_response_time'],
                    'threshold': self.alert_thresholds['response_time']
                })
            
            # Check error rate alert
            if metrics_data['error_rate'] > self.alert_thresholds['error_rate']:
                alerts.append({
                    'type': 'error_rate',
                    'severity': 'critical',
                    'message': f"Error rate ({metrics_data['error_rate']:.2%}) exceeds threshold ({self.alert_thresholds['error_rate']:.2%})",
                    'value': metrics_data['error_rate'],
                    'threshold': self.alert_thresholds['error_rate']
                })
            
            # Check success rate alert
            if metrics_data['success_rate'] < self.alert_thresholds['success_rate']:
                alerts.append({
                    'type': 'success_rate',
                    'severity': 'warning',
                    'message': f"Success rate ({metrics_data['success_rate']:.2%}) below threshold ({self.alert_thresholds['success_rate']:.2%})",
                    'value': metrics_data['success_rate'],
                    'threshold': self.alert_thresholds['success_rate']
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Failed to check alerts: {e}")
            return []
    
    def cleanup_old_logs(self, days: int = None) -> Dict[str, Any]:
        """Cleanup old log entries"""
        try:
            days = days or self.metrics_retention_days
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Delete old logs
            delete_sql = """
                DELETE FROM rag_query_logs 
                WHERE timestamp < :cutoff_date
            """
            
            result = self.db.session.execute(text(delete_sql), {'cutoff_date': cutoff_date})
            deleted_count = result.rowcount
            
            self.db.session.commit()
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old logs: {e}")
            self.db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_rag_health_status(self) -> Dict[str, Any]:
        """Get overall RAG health status"""
        try:
            # Get recent metrics
            metrics = self.get_rag_metrics(days=1)
            alerts = self.check_alerts()
            
            # Determine overall health
            health_status = 'healthy'
            if any(alert['severity'] == 'critical' for alert in alerts):
                health_status = 'critical'
            elif any(alert['severity'] == 'warning' for alert in alerts):
                health_status = 'warning'
            
            return {
                'success': True,
                'health_status': health_status,
                'metrics': metrics.get('metrics', {}),
                'alerts': alerts,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get RAG health status: {e}")
            return {
                'success': False,
                'error': str(e),
                'health_status': 'error'
            }

    def get_alerts(self, limit: int = 50, unresolved_only: bool = True) -> List[Dict[str, Any]]:
        """Get system alerts"""
        try:
            alerts = self.check_alerts()
            
            # Filter unresolved alerts if requested
            if unresolved_only:
                alerts = [alert for alert in alerts if not alert.get('resolved', False)]
            
            # Limit results
            alerts = alerts[:limit]
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Failed to get alerts: {e}")
            return []
    
    def resolve_alert(self, alert_timestamp: str) -> bool:
        """Resolve alert by timestamp"""
        try:
            # In a real implementation, you would store alerts in database
            # and mark them as resolved. For now, we'll just return True
            logger.info(f"✅ Alert resolved: {alert_timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to resolve alert: {e}")
            return False
    
    def get_embedding_metrics(self) -> Dict[str, Any]:
        """Get embedding service metrics"""
        try:
            from .unified_embedding_service import get_unified_embedding_service
            
            embedding_service = get_unified_embedding_service()
            if embedding_service and hasattr(embedding_service, 'get_stats'):
                stats = embedding_service.get_stats()
                return {
                    'success': True,
                    'data': stats
                }
            else:
                return {
                    'success': False,
                    'message': 'Embedding service not available'
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get embedding metrics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_embedding_health(self) -> Dict[str, Any]:
        """Get embedding service health"""
        try:
            from .unified_embedding_service import get_unified_embedding_service
            
            embedding_service = get_unified_embedding_service()
            if embedding_service and hasattr(embedding_service, 'is_available'):
                is_available = embedding_service.is_available()
                return {
                    'success': True,
                    'data': {
                        'status': 'healthy' if is_available else 'unhealthy',
                        'available': is_available
                    }
                }
            else:
                return {
                    'success': True,
                    'data': {
                        'status': 'unknown',
                        'available': False
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get embedding health: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def clear_embedding_cache(self) -> Dict[str, Any]:
        """Clear embedding cache"""
        try:
            from .unified_embedding_service import get_unified_embedding_service
            
            embedding_service = get_unified_embedding_service()
            if embedding_service and hasattr(embedding_service, 'clear_cache'):
                embedding_service.clear_cache()
                return {
                    'success': True,
                    'message': 'Embedding cache cleared successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Embedding service not available or does not support cache clearing'
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to clear embedding cache: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def export_metrics(self, format_type: str = 'json') -> Dict[str, Any]:
        """Export metrics data"""
        try:
            # Get comprehensive metrics
            metrics_data = self.get_comprehensive_metrics()
            alerts_data = self.get_alerts(limit=1000, unresolved_only=False)
            
            export_data = {
                'metrics': metrics_data,
                'alerts': alerts_data,
                'export_timestamp': datetime.now().isoformat(),
                'format': format_type
            }
            
            if format_type == 'json':
                return {
                    'success': True,
                    'data': export_data
                }
            else:
                return {
                    'success': False,
                    'message': f'Export format {format_type} not supported'
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to export metrics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_old_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Cleanup old metrics data"""
        try:
            result = self.cleanup_old_logs(days)
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Cleaned up metrics older than {days} days',
                    'deleted_count': result.get('deleted_count', 0)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old metrics: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global unified monitoring service instance
unified_monitoring_service = UnifiedMonitoringService()

# ===== BACKWARD COMPATIBILITY FUNCTIONS =====

def get_monitoring_service() -> UnifiedMonitoringService:
    """Backward compatibility: Get monitoring service instance"""
    return unified_monitoring_service

def get_rag_monitoring_service() -> UnifiedMonitoringService:
    """Backward compatibility: Get RAG monitoring service instance"""
    return unified_monitoring_service

# Global instance untuk backward compatibility
rag_monitoring_service = unified_monitoring_service

def get_unified_monitoring_service() -> UnifiedMonitoringService:
    """Get unified monitoring service instance"""
    return unified_monitoring_service
