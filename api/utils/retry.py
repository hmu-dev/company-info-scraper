import asyncio
import random
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .logging import log_event

T = TypeVar("T")


class RetryConfig:
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize retry configuration

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class RetryableError(Exception):
    """Base class for retryable errors"""

    pass


class LLMError(RetryableError):
    """Error during LLM processing"""

    pass


class MediaProcessingError(RetryableError):
    """Error during media processing"""

    pass


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for retry attempt"""
    delay = min(
        config.initial_delay * (config.exponential_base ** (attempt - 1)),
        config.max_delay,
    )

    if config.jitter:
        # Add random jitter between -25% and +25%
        jitter = random.uniform(-0.25, 0.25)
        delay = delay * (1 + jitter)

    return delay


async def retry_async(
    func: Callable[..., T], config: RetryConfig, *args, **kwargs
) -> T:
    """
    Retry an async function with exponential backoff

    Args:
        func: Async function to retry
        config: Retry configuration
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result from successful function call

    Raises:
        Exception from last failed attempt
    """
    last_error = None

    for attempt in range(1, config.max_attempts + 1):
        try:
            start_time = time.time()
            result = await func(*args, **kwargs)

            # Log successful attempt
            duration = time.time() - start_time
            log_event(
                "retry_success",
                {"function": func.__name__, "attempt": attempt, "duration": duration},
            )

            return result

        except Exception as e:
            last_error = e

            # Log failed attempt
            log_event(
                "retry_failure",
                {
                    "function": func.__name__,
                    "attempt": attempt,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            # Check if error is retryable
            if not isinstance(e, RetryableError):
                raise

            # Check if more attempts remain
            if attempt == config.max_attempts:
                break

            # Calculate and apply delay
            delay = calculate_delay(attempt, config)
            await asyncio.sleep(delay)

    raise last_error


def retryable(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
):
    """
    Decorator for retryable async functions

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_async(func, config, *args, **kwargs)

        return wrapper

    return decorator


class RetryContext:
    """Context manager for retry operations"""

    def __init__(
        self,
        name: str,
        config: Optional[RetryConfig] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.config = config or RetryConfig()
        self.context = context or {}
        self.start_time = None
        self.attempt = 0

    async def __aenter__(self):
        """Enter retry context"""
        self.attempt += 1
        self.start_time = time.time()

        # Log attempt start
        log_event(
            "retry_attempt_start",
            {"name": self.name, "attempt": self.attempt, "context": self.context},
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit retry context"""
        duration = time.time() - self.start_time

        if exc_val is None:
            # Log successful attempt
            log_event(
                "retry_attempt_success",
                {
                    "name": self.name,
                    "attempt": self.attempt,
                    "duration": duration,
                    "context": self.context,
                },
            )
            return True

        # Log failed attempt
        log_event(
            "retry_attempt_failure",
            {
                "name": self.name,
                "attempt": self.attempt,
                "duration": duration,
                "error": str(exc_val),
                "error_type": type(exc_val).__name__,
                "context": self.context,
            },
        )

        # Check if error is retryable
        if not isinstance(exc_val, RetryableError):
            return False

        # Check if more attempts remain
        if self.attempt >= self.config.max_attempts:
            return False

        # Calculate and apply delay
        delay = calculate_delay(self.attempt, self.config)
        await asyncio.sleep(delay)

        return True
