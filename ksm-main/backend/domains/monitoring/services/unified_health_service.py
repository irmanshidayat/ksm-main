#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Health Service untuk KSM Main Backend
Konsolidasi dari semua health check endpoints yang tersebar
Menggabungkan health check dari:
- app.py health_check()
- monitoring_controller.py health_check()
- knowledge_ai_controller.py health_check()
- unified_rag_controller.py health_check()
- rag_routes.py rag_health()
- vector_routes.py vector_health()
- mobil_routes.py health_check()
- service_routes.py health_check()
- health_routes.py health_check()
"""

import os
import time
import logging
import psutil
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

# Database imports
from config.database import db
from sqlalchemy import text

# Service imports with error handling
try:
    from .unified_ai_service import get_unified_ai_service
    UNIFIED_AI_AVAILABLE = True
except ImportError:
    UNIFIED_AI_AVAILABLE = False

try:
    from .unified_rag_service import get_unified_rag_service
    UNIFIED_RAG_AVAILABLE = True
except ImportError:
    UNIFIED_RAG_AVAILABLE = False

try:
    from domains.knowledge.services.qdrant_service import get_qdrant_service
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    from services.agent_ai_sync_service import AgentAISyncService
    AGENT_AI_SYNC_AVAILABLE = True
except ImportError:
    AGENT_AI_SYNC_AVAILABLE = False

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult:
    """Health check result structure"""
    
    def __init__(self, service: str, status: HealthStatus, message: str = "", 
                 response_time: float = 0.0, details: Dict[str, Any] = None):
        self.service = service
        self.status = status
        self.message = message
        self.response_time = response_time
        self.details = details or {}
        self.timestamp = datetime.now()


class UnifiedHealthService:
    """Unified Health Service yang menggabungkan semua health check logic"""
    
    def __init__(self):
        # Configuration
        self._init_configuration()
        
        # Service initialization
        self._init_services()
        
        # Cache untuk health check results
        self._health_cache = {}
        self._cache_ttl = int(os.getenv('HEALTH_CACHE_TTL', '30'))  # 30 seconds
        self._cache_lock = threading.Lock()
        
        logger.info("🏥 Unified Health Service initialized successfully")
    
    def _init_configuration(self):
        """Initialize service configuration"""
        self.timeout = int(os.getenv('HEALTH_CHECK_TIMEOUT', '10'))
        self.cache_enabled = os.getenv('HEALTH_CACHE_ENABLED', 'true').lower() == 'true'
        self.detailed_checks = os.getenv('HEALTH_DETAILED_CHECKS', 'true').lower() == 'true'
    
    def _init_services(self):
        """Initialize required services"""
        # Unified AI service removed - using Agent AI directly
        self.ai_service = None
        logger.info("Using Agent AI for health checks")
        
        # Unified RAG service
        if UNIFIED_RAG_AVAILABLE:
            try:
                self.rag_service = get_unified_rag_service()
            except Exception as e:
                logger.warning(f"RAG service not available: {e}")
                self.rag_service = None
        else:
            self.rag_service = None
        
        # Qdrant service
        if QDRANT_AVAILABLE:
            try:
                self.qdrant_service = get_qdrant_service()
            except Exception as e:
                logger.warning(f"Qdrant service not available: {e}")
                self.qdrant_service = None
        else:
            self.qdrant_service = None
        
        # Agent AI sync service
        if AGENT_AI_SYNC_AVAILABLE:
            try:
                self.agent_ai_sync = AgentAISyncService()
            except Exception as e:
                logger.warning(f"Agent AI sync service not available: {e}")
                self.agent_ai_sync = None
        else:
            self.agent_ai_sync = None
    
    def get_cached_health(self, service: str) -> Optional[HealthCheckResult]:
        """Get cached health check result"""
        if not self.cache_enabled:
            return None
        
        with self._cache_lock:
            if service in self._health_cache:
                result, timestamp = self._health_cache[service]
                if time.time() - timestamp < self._cache_ttl:
                    return result
                else:
                    del self._health_cache[service]
        return None
    
    def cache_health_result(self, service: str, result: HealthCheckResult):
        """Cache health check result"""
        if not self.cache_enabled:
            return
        
        with self._cache_lock:
            self._health_cache[service] = (result, time.time())
    
    def check_database_health(self) -> HealthCheckResult:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            # Test query performance
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
                table_count = result.fetchone()[0]
            
            response_time = time.time() - start_time
            
            return HealthCheckResult(
                service="database",
                status=HealthStatus.HEALTHY,
                message=f"Database connected successfully. {table_count} tables found.",
                response_time=response_time,
                details={
                    "table_count": table_count,
                    "response_time_ms": round(response_time * 1000, 2)
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                response_time=response_time,
                details={"error": str(e)}
            )
    
    def check_ai_service_health(self) -> HealthCheckResult:
        """Check AI service health"""
        start_time = time.time()
        
        if not self.ai_service:
            return HealthCheckResult(
                service="ai_service",
                status=HealthStatus.UNKNOWN,
                message="AI service not available",
                response_time=0.0
            )
        
        try:
            # Get AI service stats
            stats = self.ai_service.get_service_stats()
            response_time = time.time() - start_time
            
            if stats.get('success'):
                return HealthCheckResult(
                    service="ai_service",
                    status=HealthStatus.HEALTHY,
                    message="AI service is healthy",
                    response_time=response_time,
                    details=stats.get('data', {})
                )
            else:
                return HealthCheckResult(
                    service="ai_service",
                    status=HealthStatus.DEGRADED,
                    message="AI service has issues",
                    response_time=response_time,
                    details=stats
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service="ai_service",
                status=HealthStatus.UNHEALTHY,
                message=f"AI service check failed: {str(e)}",
                response_time=response_time,
                details={"error": str(e)}
            )
    
    def check_rag_service_health(self) -> HealthCheckResult:
        """Check RAG service health"""
        start_time = time.time()
        
        if not self.rag_service:
            return HealthCheckResult(
                service="rag_service",
                status=HealthStatus.UNKNOWN,
                message="RAG service not available",
                response_time=0.0
            )
        
        try:
            # Check RAG service components
            services_status = {
                'qdrant': self.rag_service.qdrant_service is not None and (
                    self.rag_service.qdrant_service.is_available() if hasattr(self.rag_service.qdrant_service, 'is_available') else True
                ),
                'ai_service': self.rag_service.ai_service is not None,
                'embedding_service': self.rag_service.embedding_service is not None and (
                    self.rag_service.embedding_service.is_available() if hasattr(self.rag_service.embedding_service, 'is_available') else True
                ),
                'hybrid_search': self.rag_service.hybrid_search is not None,
                'cache': self.rag_service.intelligent_cache is not None,
                'monitoring': self.rag_service.monitoring is not None
            }
            
            response_time = time.time() - start_time
            
            # Determine overall status
            healthy_services = sum(1 for status in services_status.values() if status)
            total_services = len(services_status)
            
            if healthy_services == total_services:
                status = HealthStatus.HEALTHY
                message = "All RAG services are healthy"
            elif healthy_services >= total_services * 0.7:
                status = HealthStatus.DEGRADED
                message = f"Some RAG services are degraded ({healthy_services}/{total_services})"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Multiple RAG services are unhealthy ({healthy_services}/{total_services})"
            
            return HealthCheckResult(
                service="rag_service",
                status=status,
                message=message,
                response_time=response_time,
                details=services_status
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service="rag_service",
                status=HealthStatus.UNHEALTHY,
                message=f"RAG service check failed: {str(e)}",
                response_time=response_time,
                details={"error": str(e)}
            )
    
    def check_qdrant_health(self) -> HealthCheckResult:
        """Check Qdrant vector database health"""
        start_time = time.time()
        
        if not self.qdrant_service:
            return HealthCheckResult(
                service="qdrant",
                status=HealthStatus.UNKNOWN,
                message="Qdrant service not available",
                response_time=0.0
            )
        
        try:
            health_result = self.qdrant_service.health_check()
            response_time = time.time() - start_time
            
            if health_result.get('success'):
                return HealthCheckResult(
                    service="qdrant",
                    status=HealthStatus.HEALTHY,
                    message="Qdrant is healthy",
                    response_time=response_time,
                    details=health_result.get('data', {})
                )
            else:
                return HealthCheckResult(
                    service="qdrant",
                    status=HealthStatus.DEGRADED,
                    message="Qdrant has issues",
                    response_time=response_time,
                    details=health_result
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service="qdrant",
                status=HealthStatus.UNHEALTHY,
                message=f"Qdrant check failed: {str(e)}",
                response_time=response_time,
                details={"error": str(e)}
            )
    
    def check_agent_ai_health(self) -> HealthCheckResult:
        """Check Agent AI connectivity"""
        start_time = time.time()
        
        if not self.agent_ai_sync:
            return HealthCheckResult(
                service="agent_ai",
                status=HealthStatus.UNKNOWN,
                message="Agent AI sync service not available",
                response_time=0.0
            )
        
        try:
            health_result = self.agent_ai_sync.check_agent_ai_health()
            response_time = time.time() - start_time
            
            if health_result.get('success') and health_result.get('status') == 'connected':
                return HealthCheckResult(
                    service="agent_ai",
                    status=HealthStatus.HEALTHY,
                    message="Agent AI is connected",
                    response_time=response_time,
                    details=health_result
                )
            else:
                return HealthCheckResult(
                    service="agent_ai",
                    status=HealthStatus.DEGRADED,
                    message="Agent AI connection issues",
                    response_time=response_time,
                    details=health_result
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service="agent_ai",
                status=HealthStatus.UNHEALTHY,
                message=f"Agent AI check failed: {str(e)}",
                response_time=response_time,
                details={"error": str(e)}
            )
    
    def check_system_health(self) -> HealthCheckResult:
        """Check system resources"""
        start_time = time.time()
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            response_time = time.time() - start_time
            
            # Determine status based on resource usage
            if cpu_percent < 80 and memory_percent < 80 and disk_percent < 90:
                status = HealthStatus.HEALTHY
                message = "System resources are healthy"
            elif cpu_percent < 90 and memory_percent < 90 and disk_percent < 95:
                status = HealthStatus.DEGRADED
                message = "System resources are under pressure"
            else:
                status = HealthStatus.UNHEALTHY
                message = "System resources are critically low"
            
            return HealthCheckResult(
                service="system",
                status=status,
                message=message,
                response_time=response_time,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service="system",
                status=HealthStatus.UNHEALTHY,
                message=f"System check failed: {str(e)}",
                response_time=response_time,
                details={"error": str(e)}
            )
    
    def get_comprehensive_health(self, include_details: bool = True) -> Dict[str, Any]:
        """Get comprehensive health status for all services"""
        start_time = time.time()
        
        # List of health checks to perform
        health_checks = [
            ("database", self.check_database_health),
            ("ai_service", self.check_ai_service_health),
            ("rag_service", self.check_rag_service_health),
            ("qdrant", self.check_qdrant_health),
            ("agent_ai", self.check_agent_ai_health),
            ("system", self.check_system_health)
        ]
        
        results = {}
        overall_status = HealthStatus.HEALTHY
        healthy_count = 0
        total_count = len(health_checks)
        
        for service_name, check_function in health_checks:
            # Check cache first
            cached_result = self.get_cached_health(service_name)
            if cached_result:
                result = cached_result
            else:
                result = check_function()
                self.cache_health_result(service_name, result)
            
            results[service_name] = {
                "status": result.status.value,
                "message": result.message,
                "response_time": result.response_time,
                "timestamp": result.timestamp.isoformat()
            }
            
            if include_details and result.details:
                results[service_name]["details"] = result.details
            
            # Track overall status
            if result.status == HealthStatus.HEALTHY:
                healthy_count += 1
            elif result.status == HealthStatus.DEGRADED:
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
            elif result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
        
        total_response_time = time.time() - start_time
        
        return {
            "success": True,
            "overall_status": overall_status.value,
            "health_percentage": round((healthy_count / total_count) * 100, 1),
            "healthy_services": healthy_count,
            "total_services": total_count,
            "total_response_time": round(total_response_time, 3),
            "services": results,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0-unified"
        }
    
    def get_simple_health(self) -> Dict[str, Any]:
        """Get simple health status (for basic health checks)"""
        try:
            # Quick database check
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            return {
                "success": True,
                "status": "healthy",
                "message": "Service is running",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "status": "unhealthy",
                "message": f"Service check failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health status for specific service"""
        service_checks = {
            "database": self.check_database_health,
            "ai_service": self.check_ai_service_health,
            "rag_service": self.check_rag_service_health,
            "qdrant": self.check_qdrant_health,
            "agent_ai": self.check_agent_ai_health,
            "system": self.check_system_health
        }
        
        if service_name not in service_checks:
            return {
                "success": False,
                "error": f"Unknown service: {service_name}",
                "available_services": list(service_checks.keys())
            }
        
        try:
            result = service_checks[service_name]()
            return {
                "success": True,
                "service": service_name,
                "status": result.status.value,
                "message": result.message,
                "response_time": result.response_time,
                "details": result.details,
                "timestamp": result.timestamp.isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "service": service_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global service instance
_unified_health_service = None


def get_unified_health_service() -> UnifiedHealthService:
    """Get global unified health service instance"""
    global _unified_health_service
    if _unified_health_service is None:
        _unified_health_service = UnifiedHealthService()
    return _unified_health_service
