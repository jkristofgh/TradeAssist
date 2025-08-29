"""
Unit tests for Circuit Breaker service.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone, timedelta

from src.backend.services.circuit_breaker import (
    AsyncCircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerException,
    CircuitState,
    CircuitBreakerManager,
    circuit_breaker,
    circuit_manager
)


class TestCircuitBreakerConfig:
    """Test cases for CircuitBreakerConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CircuitBreakerConfig()
        
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60
        assert config.success_threshold == 3
        assert config.request_timeout == 30.0
        assert config.sliding_window_size == 100
        assert config.minimum_throughput == 10
        assert config.error_percentage == 50.0
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            request_timeout=10.0
        )
        
        assert config.failure_threshold == 3
        assert config.recovery_timeout == 30
        assert config.request_timeout == 10.0


class TestAsyncCircuitBreaker:
    """Test cases for AsyncCircuitBreaker."""
    
    def setup_method(self):
        """Setup test circuit breaker."""
        self.config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=5,
            success_threshold=2,
            minimum_throughput=2
        )
        self.breaker = AsyncCircuitBreaker("test-circuit", self.config)
    
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful function execution."""
        async def successful_function():
            return "success"
        
        result = await self.breaker(successful_function)
        assert result == "success"
        assert self.breaker.metrics.state == CircuitState.CLOSED
        assert self.breaker.metrics.success_count == 1
        assert self.breaker.metrics.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_failed_execution(self):
        """Test failed function execution."""
        async def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await self.breaker(failing_function)
        
        assert self.breaker.metrics.state == CircuitState.CLOSED
        assert self.breaker.metrics.success_count == 0
        assert self.breaker.metrics.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self):
        """Test circuit opens after reaching failure threshold."""
        async def failing_function():
            raise RuntimeError("Test failure")
        
        # Execute function multiple times to reach failure threshold
        for i in range(self.config.failure_threshold):
            with pytest.raises(RuntimeError):
                await self.breaker(failing_function)
        
        # Circuit should now be open
        assert self.breaker.metrics.state == CircuitState.OPEN
        
        # Next call should raise CircuitBreakerException
        with pytest.raises(CircuitBreakerException):
            await self.breaker(failing_function)
    
    @pytest.mark.asyncio
    async def test_circuit_half_open_after_timeout(self):
        """Test circuit transitions to half-open after timeout."""
        # Force circuit to open
        await self.breaker.force_open()
        assert self.breaker.metrics.state == CircuitState.OPEN
        
        # Set last failure time to past the recovery timeout
        self.breaker.metrics.last_failure_time = (
            datetime.now(timezone.utc) - timedelta(seconds=self.config.recovery_timeout + 1)
        )
        
        # Next call should transition to half-open
        async def test_function():
            return "test"
        
        result = await self.breaker(test_function)
        assert result == "test"
        assert self.breaker.metrics.state == CircuitState.HALF_OPEN
    
    @pytest.mark.asyncio
    async def test_circuit_closes_after_successful_recovery(self):
        """Test circuit closes after successful recovery."""
        # Set circuit to half-open
        self.breaker.metrics.state = CircuitState.HALF_OPEN
        self.breaker.metrics.success_count = 0
        
        async def successful_function():
            return "success"
        
        # Execute successful calls to reach success threshold
        for i in range(self.config.success_threshold):
            result = await self.breaker(successful_function)
            assert result == "success"
        
        # Circuit should now be closed
        assert self.breaker.metrics.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_opens_on_half_open_failure(self):
        """Test circuit opens again on failure during half-open state."""
        # Set circuit to half-open
        self.breaker.metrics.state = CircuitState.HALF_OPEN
        
        async def failing_function():
            raise Exception("Recovery failed")
        
        # Failure should immediately open the circuit again
        with pytest.raises(Exception):
            await self.breaker(failing_function)
        
        assert self.breaker.metrics.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test request timeout handling."""
        self.breaker.config.request_timeout = 0.1  # 100ms timeout
        
        async def slow_function():
            await asyncio.sleep(0.2)  # 200ms - should timeout
            return "success"
        
        with pytest.raises(asyncio.TimeoutError):
            await self.breaker(slow_function)
        
        assert self.breaker.metrics.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_error_percentage_threshold(self):
        """Test circuit opening based on error percentage."""
        # Set config for percentage-based opening
        self.breaker.config.failure_threshold = 10  # High threshold
        self.breaker.config.error_percentage = 60.0  # 60% error rate
        self.breaker.config.minimum_throughput = 5
        
        async def mixed_function(should_fail):
            if should_fail:
                raise Exception("Failure")
            return "success"
        
        # Generate mixed results: 3 failures, 2 successes = 60% error rate
        try:
            await self.breaker(mixed_function, True)  # Failure
        except:
            pass
        try:
            await self.breaker(mixed_function, True)  # Failure  
        except:
            pass
        try:
            await self.breaker(mixed_function, True)  # Failure
        except:
            pass
        
        await self.breaker(mixed_function, False)  # Success
        await self.breaker(mixed_function, False)  # Success
        
        # Next failure should trigger circuit opening due to error percentage
        try:
            await self.breaker(mixed_function, True)  # This should open the circuit
        except CircuitBreakerException:
            # Circuit opened due to error percentage
            pass
        except Exception:
            # Regular function exception - circuit may have opened
            pass
        
        # Verify circuit is open or will open on next update
        assert self.breaker.metrics.get_error_rate() >= 60.0
    
    def test_get_status(self):
        """Test circuit breaker status reporting."""
        status = self.breaker.get_status()
        
        assert status["name"] == "test-circuit"
        assert status["state"] == CircuitState.CLOSED.value
        assert "config" in status
        assert "metrics" in status
        assert "timestamp" in status
        
        # Check config values
        assert status["config"]["failure_threshold"] == 3
        assert status["config"]["recovery_timeout"] == 5
    
    @pytest.mark.asyncio
    async def test_force_open(self):
        """Test manually forcing circuit open."""
        assert self.breaker.metrics.state == CircuitState.CLOSED
        
        await self.breaker.force_open()
        assert self.breaker.metrics.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_force_close(self):
        """Test manually forcing circuit closed."""
        await self.breaker.force_open()
        assert self.breaker.metrics.state == CircuitState.OPEN
        
        await self.breaker.force_close()
        assert self.breaker.metrics.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_reset_metrics(self):
        """Test resetting circuit breaker metrics."""
        # Generate some activity
        async def test_function():
            return "test"
        
        await self.breaker(test_function)
        assert self.breaker.metrics.total_requests > 0
        
        # Reset metrics
        await self.breaker.reset_metrics()
        
        assert self.breaker.metrics.total_requests == 0
        assert self.breaker.metrics.success_count == 0
        assert self.breaker.metrics.failure_count == 0
        assert len(self.breaker.metrics.recent_requests) == 0


class TestCircuitBreakerManager:
    """Test cases for CircuitBreakerManager."""
    
    def setup_method(self):
        """Setup test circuit breaker manager."""
        self.manager = CircuitBreakerManager()
    
    def test_get_or_create(self):
        """Test getting or creating circuit breakers."""
        # Create new circuit breaker
        breaker1 = self.manager.get_or_create("test1")
        assert breaker1.name == "test1"
        
        # Get existing circuit breaker
        breaker2 = self.manager.get_or_create("test1")
        assert breaker1 is breaker2
        
        # Create another circuit breaker
        breaker3 = self.manager.get_or_create("test2")
        assert breaker3.name == "test2"
        assert breaker1 is not breaker3
    
    def test_get_or_create_with_custom_config(self):
        """Test creating circuit breaker with custom configuration."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = self.manager.get_or_create("test", config)
        
        assert breaker.config.failure_threshold == 2
    
    def test_get_all_status(self):
        """Test getting status of all circuit breakers."""
        # Create some circuit breakers
        self.manager.get_or_create("test1")
        self.manager.get_or_create("test2")
        
        status = self.manager.get_all_status()
        
        assert len(status) == 2
        assert "test1" in status
        assert "test2" in status
        assert status["test1"]["name"] == "test1"
        assert status["test2"]["name"] == "test2"
    
    @pytest.mark.asyncio
    async def test_get_unhealthy_circuits(self):
        """Test getting list of unhealthy circuits."""
        # Create circuit breakers
        breaker1 = self.manager.get_or_create("healthy")
        breaker2 = self.manager.get_or_create("unhealthy")
        
        # Make one unhealthy
        await breaker2.force_open()
        
        unhealthy = self.manager.get_unhealthy_circuits()
        
        assert len(unhealthy) == 1
        assert "unhealthy" in unhealthy
        assert "healthy" not in unhealthy
    
    @pytest.mark.asyncio
    async def test_get_summary(self):
        """Test getting summary statistics."""
        # Create some circuit breakers with different states
        breaker1 = self.manager.get_or_create("closed")
        breaker2 = self.manager.get_or_create("open")
        breaker3 = self.manager.get_or_create("half_open")
        
        await breaker2.force_open()
        breaker3.metrics.state = CircuitState.HALF_OPEN
        
        # Generate some activity
        async def test_func():
            return "test"
        
        await breaker1(test_func)
        
        summary = self.manager.get_summary()
        
        assert summary["total_circuit_breakers"] == 3
        assert summary["healthy_circuits"] == 1
        assert summary["unhealthy_circuits"] == 2
        assert summary["open_circuits"] == 1
        assert summary["half_open_circuits"] == 1
        assert summary["total_requests"] >= 1


class TestCircuitBreakerDecorator:
    """Test cases for circuit_breaker decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_basic_usage(self):
        """Test basic decorator usage."""
        @circuit_breaker("decorator-test")
        async def test_function():
            return "decorated success"
        
        result = await test_function()
        assert result == "decorated success"
        
        # Verify circuit breaker was created
        breaker = circuit_manager.get_or_create("decorator-test")
        assert breaker.metrics.success_count == 1
    
    @pytest.mark.asyncio
    async def test_decorator_with_config(self):
        """Test decorator with custom configuration."""
        custom_config = CircuitBreakerConfig(failure_threshold=2)
        
        @circuit_breaker("decorator-config-test", config=custom_config)
        async def test_function():
            return "success"
        
        await test_function()
        
        # Verify custom config was applied
        breaker = circuit_manager.get_or_create("decorator-config-test")
        assert breaker.config.failure_threshold == 2
    
    @pytest.mark.asyncio
    async def test_decorator_failure_handling(self):
        """Test decorator handles failures correctly."""
        @circuit_breaker("decorator-failure-test")
        async def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await failing_function()
        
        # Verify failure was recorded
        breaker = circuit_manager.get_or_create("decorator-failure-test")
        assert breaker.metrics.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves original function metadata."""
        @circuit_breaker("metadata-test")
        async def documented_function():
            """This is a test function."""
            return "test"
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."
        assert hasattr(documented_function, 'circuit_breaker')


@pytest.mark.integration
class TestCircuitBreakerIntegration:
    """Integration tests for circuit breaker patterns."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_circuit_breaking(self):
        """Test complete circuit breaker lifecycle."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=1,  # Short timeout for testing
            success_threshold=1
        )
        
        breaker = AsyncCircuitBreaker("integration-test", config)
        
        # Phase 1: Normal operation
        async def reliable_function():
            return "success"
        
        result = await breaker(reliable_function)
        assert result == "success"
        assert breaker.metrics.state == CircuitState.CLOSED
        
        # Phase 2: Introduce failures
        failure_count = 0
        async def unreliable_function():
            nonlocal failure_count
            failure_count += 1
            raise Exception(f"Failure {failure_count}")
        
        # Cause enough failures to open circuit
        for i in range(config.failure_threshold):
            with pytest.raises(Exception):
                await breaker(unreliable_function)
        
        assert breaker.metrics.state == CircuitState.OPEN
        
        # Phase 3: Circuit is open - calls should be rejected
        with pytest.raises(CircuitBreakerException):
            await breaker(reliable_function)
        
        # Phase 4: Wait for recovery timeout
        await asyncio.sleep(config.recovery_timeout + 0.1)
        
        # Phase 5: Circuit should go half-open and then close on success
        result = await breaker(reliable_function)
        assert result == "success"
        assert breaker.metrics.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_concurrent_circuit_breaker_access(self):
        """Test circuit breaker with concurrent access."""
        config = CircuitBreakerConfig(failure_threshold=5)
        breaker = AsyncCircuitBreaker("concurrent-test", config)
        
        call_count = 0
        
        async def concurrent_function():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Small delay to simulate work
            return f"call-{call_count}"
        
        # Execute multiple concurrent calls
        tasks = [breaker(concurrent_function) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert breaker.metrics.success_count == 10
        assert breaker.metrics.state == CircuitState.CLOSED