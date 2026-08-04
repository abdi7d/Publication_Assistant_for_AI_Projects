# resilience/circuit_breaker/circuit_breaker.py
"""
Circuit breaker pattern implementation for external service calls.
Prevents cascading failures when external services are down.
"""
import time
import logging
import threading
from enum import Enum, auto
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = auto()  # Normal operation
    OPEN = auto()    # Circuit is open, calls fail fast
    HALF_OPEN = auto()  # Testing if service has recovered


class CircuitBreaker:
    """
    Circuit breaker implementation with configurable thresholds.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Exception = Exception,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to consider as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = CircuitState.CLOSED
        self._lock = threading.local()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker attempting reset")
            else:
                raise Exception("Circuit breaker is OPEN - failing fast")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as exc:
            self._on_failure()
            raise exc
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt circuit reset."""
        if self._last_failure_time is None:
            return True
        return time.time() - self._last_failure_time >= self.recovery_timeout
    
    def _on_success(self) -> None:
        """Handle successful function call."""
        self._failure_count = 0
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            logger.info("Circuit breaker reset to CLOSED")
    
    def _on_failure(self) -> None:
        """Handle failed function call."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker opened after %d failures",
                self._failure_count
            )
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        self._failure_count = 0
        self._last_failure_time = None
        self._state = CircuitState.CLOSED
        logger.info("Circuit breaker manually reset")


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Exception = Exception,
) -> Callable:
    """
    Decorator for circuit breaker protection.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type to consider as failure
        
    Returns:
        Decorated function with circuit breaker protection
    """
    def decorator(func: Callable) -> Callable:
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return breaker.call(func, *args, **kwargs)
        
        # Attach circuit breaker to function for inspection
        wrapper._circuit_breaker = breaker  # type: ignore
        return wrapper
    
    return decorator


__all__ = ["CircuitBreaker", "CircuitState", "circuit_breaker"]