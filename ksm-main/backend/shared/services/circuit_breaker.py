#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Circuit Breaker untuk KSM-Main
Implementasi circuit breaker pattern untuk service-to-service communication
"""

import os
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import functools

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service is back

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5          # Number of failures before opening
    recovery_timeout: int = 60          # Seconds before trying half-open
    success_threshold: int = 3          # Successes needed to close from half-open
    timeout: int = 30                   # Request timeout in seconds
    max_retries: int = 3                # Max retries for failed requests
    retry_delay: float = 1.0            # Delay between retries

@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_time: Optional[datetime]
    last_success_time: Optional[datetime]
    total_requests: int
    total_failures: int
    total_successes: int
    last_state_change: datetime

class CircuitBreaker:
    """Circuit breaker implementation untuk service-to-service communication"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.last_state_change = datetime.now()
        
        # Statistics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        
        logger.info(f"🔧 Circuit Breaker '{self.name}' initialized with config: {asdict(self.config)}")
    
    def _can_execute(self) -> bool:
        """Check if request can be executed based on current state"""
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (self.last_failure_time and 
                datetime.now() - self.last_failure_time >= timedelta(seconds=self.config.recovery_timeout)):
                self._transition_to_half_open()
                return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        if self.state != CircuitState.OPEN:
            logger.warning(f"🔴 Circuit Breaker '{self.name}' transitioning to OPEN state")
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
            self.success_count = 0
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        if self.state != CircuitState.HALF_OPEN:
            logger.info(f"🟡 Circuit Breaker '{self.name}' transitioning to HALF_OPEN state")
            self.state = CircuitState.HALF_OPEN
            self.last_state_change = datetime.now()
            self.success_count = 0
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        if self.state != CircuitState.CLOSED:
            logger.info(f"🟢 Circuit Breaker '{self.name}' transitioning to CLOSED state")
            self.state = CircuitState.CLOSED
            self.last_state_change = datetime.now()
            self.failure_count = 0
    
    def _record_success(self):
        """Record successful request"""
        self.success_count += 1
        self.total_successes += 1
        self.last_success_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
    
    def _record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.total_failures += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        self.total_requests += 1
        
        # Check if circuit allows execution
        if not self._can_execute():
            error_msg = f"Circuit breaker '{self.name}' is OPEN - request rejected"
            logger.warning(f"🚫 {error_msg}")
            raise CircuitBreakerOpenException(error_msg)
        
        # Execute function with retry logic
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
                else:
                    result = func(*args, **kwargs)
                
                # Record success
                self._record_success()
                logger.debug(f"✅ Circuit Breaker '{self.name}' - Request successful (attempt {attempt + 1})")
                return result
                
            except asyncio.TimeoutError:
                last_exception = asyncio.TimeoutError(f"Request timeout after {self.config.timeout}s")
                logger.warning(f"⏰ Circuit Breaker '{self.name}' - Timeout (attempt {attempt + 1})")
                
            except Exception as e:
                last_exception = e
                logger.warning(f"❌ Circuit Breaker '{self.name}' - Error (attempt {attempt + 1}): {e}")
            
            # Wait before retry (except on last attempt)
            if attempt < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
        
        # All attempts failed
        self._record_failure()
        logger.error(f"💥 Circuit Breaker '{self.name}' - All attempts failed")
        raise last_exception or Exception("Circuit breaker execution failed")
    
    def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics"""
        return CircuitBreakerStats(
            state=self.state,
            failure_count=self.failure_count,
            success_count=self.success_count,
            last_failure_time=self.last_failure_time,
            last_success_time=self.last_success_time,
            total_requests=self.total_requests,
            total_failures=self.total_failures,
            total_successes=self.total_successes,
            last_state_change=self.last_state_change
        )
    
    def reset(self):
        """Reset circuit breaker to initial state"""
        logger.info(f"🔄 Circuit Breaker '{self.name}' reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.last_state_change = datetime.now()
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreakerManager:
    """Manager untuk multiple circuit breakers"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        logger.info("🔧 Circuit Breaker Manager initialized")
    
    def get_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
            logger.info(f"🔧 Created new circuit breaker: {name}")
        
        return self.circuit_breakers[name]
    
    def get_all_stats(self) -> Dict[str, CircuitBreakerStats]:
        """Get statistics for all circuit breakers"""
        return {name: cb.get_stats() for name, cb in self.circuit_breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for cb in self.circuit_breakers.values():
            cb.reset()
        logger.info("🔄 All circuit breakers reset")

# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()

# Convenience function untuk Agent AI communication
def get_agent_ai_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for Agent AI communication"""
    config = CircuitBreakerConfig(
        failure_threshold=int(os.getenv('AGENT_AI_CB_FAILURE_THRESHOLD', '5')),
        recovery_timeout=int(os.getenv('AGENT_AI_CB_RECOVERY_TIMEOUT', '60')),
        success_threshold=int(os.getenv('AGENT_AI_CB_SUCCESS_THRESHOLD', '3')),
        timeout=int(os.getenv('AGENT_AI_CB_TIMEOUT', '30')),
        max_retries=int(os.getenv('AGENT_AI_CB_MAX_RETRIES', '3')),
        retry_delay=float(os.getenv('AGENT_AI_CB_RETRY_DELAY', '1.0'))
    )
    
    return circuit_breaker_manager.get_circuit_breaker('agent_ai', config)

def get_circuit_breaker(name: str = 'default', config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """Get circuit breaker instance"""
    return circuit_breaker_manager.get_circuit_breaker(name, config)

def call_with_circuit_breaker(func, *args, **kwargs):
    """Call function with circuit breaker"""
    cb = circuit_breaker_manager.get_circuit_breaker('default')
    return asyncio.run(cb.call(func, *args, **kwargs))

# Decorator untuk circuit breaker
def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator untuk circuit breaker"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            cb = circuit_breaker_manager.get_circuit_breaker(name, config)
            return await cb.call(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            cb = circuit_breaker_manager.get_circuit_breaker(name, config)
            return asyncio.run(cb.call(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
