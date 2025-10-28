"""Timeout management utilities for LLM and preprocessing operations."""

import asyncio
import signal
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Callable, Optional, TypeVar

from .error_handler import ErrorType, ProcessingError

T = TypeVar('T')


class TimeoutManager:
    """Manages timeouts for various processing operations."""
    
    def __init__(self, default_timeout: int = 60):
        self.default_timeout = default_timeout
    
    @asynccontextmanager
    async def async_timeout(self, timeout_seconds: Optional[int] = None):
        """Async context manager for timeout operations."""
        timeout = timeout_seconds or self.default_timeout
        
        try:
            async with asyncio.timeout(timeout):
                yield
        except asyncio.TimeoutError:
            raise ProcessingError(
                message=f"Operation timed out after {timeout} seconds",
                error_type=ErrorType.LLM_TIMEOUT_ERROR,
                context={"timeout_seconds": timeout}
            )
    
    @contextmanager
    def sync_timeout(self, timeout_seconds: Optional[int] = None):
        """Synchronous context manager for timeout operations."""
        timeout = timeout_seconds or self.default_timeout
        
        def timeout_handler(signum, frame):
            raise ProcessingError(
                message=f"Operation timed out after {timeout} seconds",
                error_type=ErrorType.LLM_TIMEOUT_ERROR,
                context={"timeout_seconds": timeout}
            )
        
        # Set the signal handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            yield
        finally:
            # Cancel the alarm and restore old handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    async def run_with_timeout(
        self,
        coro: Callable[..., Any],
        timeout_seconds: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """Run an async function with timeout."""
        timeout = timeout_seconds or self.default_timeout
        
        try:
            return await asyncio.wait_for(coro(*args, **kwargs), timeout=timeout)
        except asyncio.TimeoutError:
            raise ProcessingError(
                message=f"Operation timed out after {timeout} seconds",
                error_type=ErrorType.LLM_TIMEOUT_ERROR,
                context={
                    "timeout_seconds": timeout,
                    "function": coro.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs)
                }
            )
    
    def run_sync_with_timeout(
        self,
        func: Callable[..., T],
        timeout_seconds: Optional[int] = None,
        *args,
        **kwargs
    ) -> T:
        """Run a synchronous function with timeout."""
        timeout = timeout_seconds or self.default_timeout
        
        def timeout_handler(signum, frame):
            raise ProcessingError(
                message=f"Operation timed out after {timeout} seconds",
                error_type=ErrorType.LLM_TIMEOUT_ERROR,
                context={
                    "timeout_seconds": timeout,
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs)
                }
            )
        
        # Set the signal handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            return func(*args, **kwargs)
        finally:
            # Cancel the alarm and restore old handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


class CircuitBreaker:
    """Circuit breaker pattern for LLM service reliability."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = ProcessingError
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Call function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise ProcessingError(
                    message="Circuit breaker is OPEN - service temporarily unavailable",
                    error_type=ErrorType.LLM_CONNECTION_ERROR,
                    context={
                        "circuit_breaker_state": self.state,
                        "failure_count": self.failure_count,
                        "last_failure_time": self.last_failure_time
                    }
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


# Global instances
timeout_manager = TimeoutManager()
llm_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=ProcessingError
)