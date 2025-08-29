"""
Circuit Breaker Pattern Implementation.

Provides fault tolerance and resilience for external API calls
with automatic failure detection, circuit breaking, and recovery.
"""

import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Callable, Optional, Awaitable, List
from enum import Enum
from dataclasses import dataclass, field
from collections import deque

import structlog

logger = structlog.get_logger()


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Blocking requests (failure)
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: int = 60          # Seconds to wait before half-open
    success_threshold: int = 3          # Successes to close from half-open
    request_timeout: float = 30.0       # Request timeout in seconds
    sliding_window_size: int = 100      # Size of metrics sliding window
    minimum_throughput: int = 10        # Minimum requests before evaluation
    error_percentage: float = 50.0      # Error percentage threshold


@dataclass
class CircuitBreakerMetrics:
    """Circuit breaker metrics and statistics."""
    name: str
    state: CircuitState
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    total_requests: int = 0
    recent_requests: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_errors: deque = field(default_factory=lambda: deque(maxlen=100))
    state_changes: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_error_rate(self) -> float:
        """Calculate current error rate percentage."""
        if not self.recent_requests:
            return 0.0
        
        recent_errors = len(self.recent_errors)
        recent_requests = len(self.recent_requests)
        
        if recent_requests == 0:
            return 0.0
        
        return (recent_errors / recent_requests) * 100.0
    
    def get_success_rate(self) -> float:
        """Calculate current success rate percentage."""
        return 100.0 - self.get_error_rate()


class CircuitBreakerException(Exception):
    """Exception raised when circuit breaker is open."""
    
    def __init__(self, circuit_name: str, state: CircuitState):
        self.circuit_name = circuit_name
        self.state = state
        super().__init__(f"Circuit breaker '{circuit_name}' is {state.value}")


class AsyncCircuitBreaker:
    """
    Async circuit breaker for external API calls.
    
    Implements the circuit breaker pattern to provide resilience
    against cascading failures in distributed systems.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.metrics = CircuitBreakerMetrics(name=name, state=CircuitState.CLOSED)
        self._lock = asyncio.Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized", config=self.config.__dict__)
    
    async def __call__(
        self,
        func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute.
            *args: Function arguments.
            **kwargs: Function keyword arguments.
            
        Returns:
            Function result.
            
        Raises:
            CircuitBreakerException: If circuit is open.
            Exception: Original function exceptions when circuit is closed/half-open.
        """
        async with self._lock:
            await self._update_state()
            
            if self.metrics.state == CircuitState.OPEN:
                raise CircuitBreakerException(self.name, self.metrics.state)
        
        start_time = time.time()
        success = False
        error = None
        
        try:
            # Execute function with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.request_timeout
            )
            success = True
            return result
            
        except asyncio.TimeoutError as e:
            error = e
            logger.warning(
                f"Circuit breaker '{self.name}' timeout",
                timeout=self.config.request_timeout
            )
            raise
        except Exception as e:
            error = e
            logger.error(f"Circuit breaker '{self.name}' function error: {e}")
            raise
        finally:
            execution_time = time.time() - start_time
            await self._record_result(success, error, execution_time)
    
    async def _update_state(self) -> None:
        """Update circuit breaker state based on current conditions."""
        now = datetime.now(timezone.utc)
        current_state = self.metrics.state
        
        if current_state == CircuitState.CLOSED:
            # Check if we should open the circuit
            if await self._should_open_circuit():
                await self._change_state(CircuitState.OPEN, now)
                
        elif current_state == CircuitState.OPEN:
            # Check if we should try half-open
            if self._should_attempt_reset():
                await self._change_state(CircuitState.HALF_OPEN, now)
                
        elif current_state == CircuitState.HALF_OPEN:
            # In half-open, we let a few requests through to test
            # State changes are handled in _record_result
            pass
    
    async def _should_open_circuit(self) -> bool:
        """Check if circuit should be opened based on failure conditions."""
        # Need minimum throughput to make decisions
        if len(self.metrics.recent_requests) < self.config.minimum_throughput:
            return False
        
        # Check failure threshold
        if self.metrics.failure_count >= self.config.failure_threshold:
            return True
        
        # Check error percentage
        error_rate = self.metrics.get_error_rate()
        if error_rate >= self.config.error_percentage:
            logger.warning(
                f"Circuit breaker '{self.name}' error rate threshold exceeded",
                error_rate=error_rate,
                threshold=self.config.error_percentage
            )
            return True
        
        return False
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset from open to half-open."""
        if not self.metrics.last_failure_time:
            return True
        
        time_since_last_failure = datetime.now(timezone.utc) - self.metrics.last_failure_time
        return time_since_last_failure.total_seconds() >= self.config.recovery_timeout
    
    async def _record_result(
        self,
        success: bool,
        error: Optional[Exception],
        execution_time: float
    ) -> None:
        """Record the result of a function execution."""
        now = datetime.now(timezone.utc)
        
        async with self._lock:
            # Update metrics
            self.metrics.total_requests += 1
            self.metrics.recent_requests.append({
                "timestamp": now,
                "success": success,
                "execution_time": execution_time,
                "error": str(error) if error else None
            })
            
            if success:
                self.metrics.success_count += 1
                self.metrics.last_success_time = now
                
                # If in half-open state, check if we can close
                if self.metrics.state == CircuitState.HALF_OPEN:
                    if self.metrics.success_count >= self.config.success_threshold:
                        await self._change_state(CircuitState.CLOSED, now)
            else:
                self.metrics.failure_count += 1
                self.metrics.last_failure_time = now
                self.metrics.recent_errors.append({
                    "timestamp": now,
                    "error": str(error) if error else "Unknown error",
                    "execution_time": execution_time
                })
                
                # If in half-open state, go back to open on any failure
                if self.metrics.state == CircuitState.HALF_OPEN:
                    await self._change_state(CircuitState.OPEN, now)
    
    async def _change_state(self, new_state: CircuitState, timestamp: datetime) -> None:
        """Change circuit breaker state and record the change."""
        old_state = self.metrics.state
        self.metrics.state = new_state
        
        # Reset counters based on state change
        if new_state == CircuitState.HALF_OPEN:
            self.metrics.success_count = 0
            self.metrics.failure_count = 0
        elif new_state == CircuitState.CLOSED:
            self.metrics.success_count = 0
            self.metrics.failure_count = 0
        
        # Record state change
        state_change = {
            "from_state": old_state.value,
            "to_state": new_state.value,
            "timestamp": timestamp,
            "reason": self._get_state_change_reason(old_state, new_state)
        }
        self.metrics.state_changes.append(state_change)
        
        # Keep only recent state changes
        if len(self.metrics.state_changes) > 50:
            self.metrics.state_changes = self.metrics.state_changes[-50:]
        
        logger.info(
            f"Circuit breaker '{self.name}' state changed",
            from_state=old_state.value,
            to_state=new_state.value,
            reason=state_change["reason"]
        )
    
    def _get_state_change_reason(self, old_state: CircuitState, new_state: CircuitState) -> str:
        """Get human-readable reason for state change."""
        if old_state == CircuitState.CLOSED and new_state == CircuitState.OPEN:
            return f"Failure threshold exceeded ({self.metrics.failure_count} failures)"
        elif old_state == CircuitState.OPEN and new_state == CircuitState.HALF_OPEN:
            return f"Recovery timeout elapsed ({self.config.recovery_timeout}s)"
        elif old_state == CircuitState.HALF_OPEN and new_state == CircuitState.CLOSED:
            return f"Recovery successful ({self.metrics.success_count} successes)"
        elif old_state == CircuitState.HALF_OPEN and new_state == CircuitState.OPEN:
            return "Recovery failed"
        else:
            return "State transition"
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current circuit breaker status and metrics.
        
        Returns:
            Dict with comprehensive status information.
        """
        return {
            "name": self.name,
            "state": self.metrics.state.value,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "request_timeout": self.config.request_timeout,
                "error_percentage": self.config.error_percentage,
            },
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "success_count": self.metrics.success_count,
                "failure_count": self.metrics.failure_count,
                "error_rate": self.metrics.get_error_rate(),
                "success_rate": self.metrics.get_success_rate(),
                "last_failure": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
                "last_success": self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
                "recent_requests": len(self.metrics.recent_requests),
                "recent_errors": len(self.metrics.recent_errors),
            },
            "state_changes": self.metrics.state_changes[-10:],  # Last 10 changes
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def force_open(self) -> None:
        """Manually force circuit breaker to open state."""
        async with self._lock:
            await self._change_state(CircuitState.OPEN, datetime.now(timezone.utc))
    
    async def force_close(self) -> None:
        """Manually force circuit breaker to closed state."""
        async with self._lock:
            await self._change_state(CircuitState.CLOSED, datetime.now(timezone.utc))
    
    async def reset_metrics(self) -> None:
        """Reset all metrics and counters."""
        async with self._lock:
            self.metrics.failure_count = 0
            self.metrics.success_count = 0
            self.metrics.total_requests = 0
            self.metrics.recent_requests.clear()
            self.metrics.recent_errors.clear()
            self.metrics.last_failure_time = None
            self.metrics.last_success_time = None
            logger.info(f"Circuit breaker '{self.name}' metrics reset")


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.
    
    Provides centralized management and monitoring of circuit breakers
    across different external services and APIs.
    """
    
    def __init__(self):
        self._breakers: Dict[str, AsyncCircuitBreaker] = {}
        self._default_config = CircuitBreakerConfig()
    
    def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> AsyncCircuitBreaker:
        """
        Get existing circuit breaker or create new one.
        
        Args:
            name: Circuit breaker name.
            config: Optional configuration (uses default if None).
            
        Returns:
            CircuitBreaker instance.
        """
        if name not in self._breakers:
            self._breakers[name] = AsyncCircuitBreaker(
                name, config or self._default_config
            )
            logger.info(f"Created circuit breaker: {name}")
        
        return self._breakers[name]
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all circuit breakers.
        
        Returns:
            Dict mapping circuit breaker names to their status.
        """
        return {
            name: breaker.get_status()
            for name, breaker in self._breakers.items()
        }
    
    def get_unhealthy_circuits(self) -> List[str]:
        """
        Get list of circuit breakers that are not in CLOSED state.
        
        Returns:
            List of circuit breaker names that are open or half-open.
        """
        return [
            name for name, breaker in self._breakers.items()
            if breaker.metrics.state != CircuitState.CLOSED
        ]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all circuit breakers.
        
        Returns:
            Dict with aggregate statistics.
        """
        total_breakers = len(self._breakers)
        closed_count = sum(
            1 for b in self._breakers.values()
            if b.metrics.state == CircuitState.CLOSED
        )
        open_count = sum(
            1 for b in self._breakers.values()
            if b.metrics.state == CircuitState.OPEN
        )
        half_open_count = sum(
            1 for b in self._breakers.values()
            if b.metrics.state == CircuitState.HALF_OPEN
        )
        
        total_requests = sum(b.metrics.total_requests for b in self._breakers.values())
        total_failures = sum(b.metrics.failure_count for b in self._breakers.values())
        
        return {
            "total_circuit_breakers": total_breakers,
            "healthy_circuits": closed_count,
            "unhealthy_circuits": open_count + half_open_count,
            "open_circuits": open_count,
            "half_open_circuits": half_open_count,
            "total_requests": total_requests,
            "total_failures": total_failures,
            "overall_success_rate": (
                ((total_requests - total_failures) / total_requests * 100)
                if total_requests > 0 else 0.0
            ),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global circuit breaker manager
circuit_manager = CircuitBreakerManager()


def circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
):
    """
    Decorator for applying circuit breaker pattern to async functions.
    
    Args:
        name: Circuit breaker name.
        config: Optional configuration.
        
    Example:
        @circuit_breaker("external_api", config=CircuitBreakerConfig(failure_threshold=3))
        async def call_external_api():
            # API call implementation
            pass
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        breaker = circuit_manager.get_or_create(name, config)
        
        async def wrapper(*args, **kwargs):
            return await breaker(func, *args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.circuit_breaker = breaker  # Expose breaker for testing
        
        return wrapper
    
    return decorator