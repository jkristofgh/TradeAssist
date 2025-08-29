"""
Rate limiting utility for Schwab API requests.

Provides rate limiting functionality to ensure compliance with Schwab's 120 requests
per minute API limits using token bucket algorithm.
"""

import asyncio
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any

from loguru import logger


class RateLimitError(Exception):
    """Exception raised when API rate limit is exceeded."""

    pass


class RateLimiter:
    """
    Rate limiter for Schwab API requests (120 requests per minute).

    Uses token bucket algorithm to ensure API rate limits are respected
    with configurable buffer for safety.
    """

    def __init__(self, max_requests: int = 110, time_window: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed per time window (default: 110 for safety buffer)
            time_window: Time window in seconds (default: 60)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: deque[float] = deque()
        self._lock = asyncio.Lock()

        logger.info(f"RateLimiter initialized: {max_requests} requests per {time_window}s")

    async def acquire(self) -> None:
        """
        Acquire permission to make a request.

        Blocks if rate limit would be exceeded, implementing exponential backoff.
        """
        async with self._lock:
            now = time.time()

            # Remove old requests outside the time window
            while self.requests and self.requests[0] <= now - self.time_window:
                self.requests.popleft()

            # If we're at the limit, wait until we can make another request
            if len(self.requests) >= self.max_requests:
                sleep_time = self.requests[0] + self.time_window - now + 0.1  # Small buffer
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached, waiting {sleep_time:.2f} seconds")
                    await asyncio.sleep(sleep_time)
                    return await self.acquire()  # Recursive call after waiting

            # Record this request
            self.requests.append(now)

    def can_make_request(self) -> bool:
        """
        Check if a request can be made without blocking.

        Returns:
            True if request can be made immediately, False otherwise
        """
        now = time.time()

        # Count recent requests
        recent_requests = sum(1 for req_time in self.requests if req_time > now - self.time_window)

        return recent_requests < self.max_requests

    def get_stats(self) -> dict[str, Any]:
        """
        Get current rate limiter statistics.

        Returns:
            Dictionary with rate limit information
        """
        now = time.time()

        # Count requests in current window
        recent_requests = sum(1 for req_time in self.requests if req_time > now - self.time_window)

        # Calculate time until next request can be made
        time_until_next = 0.0
        if recent_requests >= self.max_requests and self.requests:
            time_until_next = max(0, self.requests[0] + self.time_window - now)

        return {
            "requests_in_window": recent_requests,
            "max_requests": self.max_requests,
            "time_window": self.time_window,
            "capacity_remaining": self.max_requests - recent_requests,
            "capacity_percentage": ((self.max_requests - recent_requests) / self.max_requests)
            * 100,
            "time_until_next_slot": time_until_next,
            "total_requests_made": len(self.requests),
        }

    def reset(self) -> None:
        """Reset the rate limiter by clearing all request history."""
        self.requests.clear()
        logger.debug("Rate limiter reset")


class APIRequestTracker:
    """
    Enhanced request tracker with retry logic and error handling.

    Tracks API requests, implements exponential backoff for retries,
    and provides detailed statistics for monitoring.
    """

    def __init__(self, rate_limiter: RateLimiter | None = None):
        """
        Initialize request tracker.

        Args:
            rate_limiter: Optional rate limiter instance
        """
        self.rate_limiter = rate_limiter or RateLimiter()
        self.request_history: list[dict[str, Any]] = []
        self.error_counts: dict[str, int] = {}
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

        logger.info("APIRequestTracker initialized")

    async def make_request(
        self,
        request_func: Any,
        *args: Any,
        retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        **kwargs: Any,
    ) -> Any:
        """
        Make a rate-limited API request with retry logic.

        Args:
            request_func: Function to call for the API request
            *args: Arguments for the request function
            retries: Number of retry attempts
            base_delay: Base delay for exponential backoff
            max_delay: Maximum delay between retries
            **kwargs: Keyword arguments for the request function

        Returns:
            API response

        Raises:
            RateLimitError: If rate limiting fails
            Exception: If request fails after all retries
        """
        start_time = time.time()
        last_error = None

        for attempt in range(retries + 1):
            try:
                # Apply rate limiting
                await self.rate_limiter.acquire()

                # Make the request
                response = await request_func(*args, **kwargs)

                # Record successful request
                self._record_request(
                    success=True, duration=time.time() - start_time, attempt=attempt + 1
                )

                self.total_requests += 1
                self.successful_requests += 1

                return response

            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

                # Check if we should retry
                if attempt < retries:
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2**attempt), max_delay)

                    # Add jitter to prevent thundering herd
                    import random

                    delay += random.uniform(0, 0.1 * delay)

                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s"
                    )

                    await asyncio.sleep(delay)
                    continue
                else:
                    # Final attempt failed
                    break

        # All retries exhausted
        self._record_request(
            success=False,
            duration=time.time() - start_time,
            attempt=retries + 1,
            error=str(last_error),
        )

        self.total_requests += 1
        self.failed_requests += 1

        if last_error:
            raise last_error
        else:
            raise Exception("Request failed after all retries")

    def _record_request(
        self, success: bool, duration: float, attempt: int, error: str | None = None
    ) -> None:
        """Record request details for monitoring."""
        record = {
            "timestamp": datetime.now(),
            "success": success,
            "duration_ms": duration * 1000,
            "attempt": attempt,
            "error": error,
        }

        self.request_history.append(record)

        # Keep only recent history (last 1000 requests)
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive request statistics.

        Returns:
            Dictionary with detailed statistics
        """
        now = datetime.now()
        recent_cutoff = now - timedelta(minutes=10)

        # Recent requests (last 10 minutes)
        recent_requests = [r for r in self.request_history if r["timestamp"] > recent_cutoff]

        recent_successful = sum(1 for r in recent_requests if r["success"])
        recent_failed = len(recent_requests) - recent_successful

        # Calculate average durations
        successful_durations = [r["duration_ms"] for r in recent_requests if r["success"]]
        avg_duration = (
            sum(successful_durations) / len(successful_durations) if successful_durations else 0
        )

        stats = {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / self.total_requests * 100)
            if self.total_requests > 0
            else 0,
            "recent_requests_10min": len(recent_requests),
            "recent_successful_10min": recent_successful,
            "recent_failed_10min": recent_failed,
            "recent_success_rate": (recent_successful / len(recent_requests) * 100)
            if recent_requests
            else 0,
            "average_duration_ms": avg_duration,
            "error_counts": self.error_counts.copy(),
            "rate_limiter_stats": self.rate_limiter.get_stats(),
        }

        return stats

    def health_check(self) -> dict[str, Any]:
        """
        Perform health check of the request tracker.

        Returns:
            Health check results
        """
        stats = self.get_statistics()
        health: dict[str, Any] = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "issues": [],
            "recommendations": [],
        }

        # Check recent success rate
        if stats["recent_success_rate"] < 90 and stats["recent_requests_10min"] > 5:
            health["status"] = "degraded"
            health["issues"].append(f"Low recent success rate: {stats['recent_success_rate']:.1f}%")
            health["recommendations"].append("Check API connectivity and credentials")

        # Check rate limiter capacity
        rate_stats = stats["rate_limiter_stats"]
        if rate_stats["capacity_remaining"] < 10:
            health["issues"].append("Rate limiter capacity is low")
            health["recommendations"].append("Reduce request frequency")

        # Check for high error rates
        total_errors = sum(stats["error_counts"].values())
        if total_errors > stats["total_requests"] * 0.1:  # More than 10% errors
            health["status"] = "unhealthy"
            health["issues"].append(f"High error rate: {total_errors} errors")
            health["recommendations"].append("Investigate most common error types")

        return health


# Convenience function for creating a configured rate limiter
def create_schwab_rate_limiter(safety_buffer: int = 10) -> RateLimiter:
    """
    Create a rate limiter configured for Schwab API limits.

    Args:
        safety_buffer: Number of requests to reserve as buffer (default: 10)

    Returns:
        Configured RateLimiter for Schwab API
    """
    # Schwab allows 120 requests per minute, we use a buffer for safety
    max_requests = 120 - safety_buffer

    return RateLimiter(max_requests=max_requests, time_window=60)


# Export key classes
__all__ = ["RateLimiter", "APIRequestTracker", "RateLimitError", "create_schwab_rate_limiter"]
