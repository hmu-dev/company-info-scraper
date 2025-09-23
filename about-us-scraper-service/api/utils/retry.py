"""
Retry mechanism for handling transient failures.

This module provides a retry decorator with exponential backoff and jitter
for handling transient failures in API calls and other operations.

Classes:
    LLMError: Custom exception for LLM-related errors
    RetryableError: Base class for retryable errors

Functions:
    retryable: Decorator for adding retry behavior to functions
"""

import asyncio
import random
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar, Union


class RetryableError(Exception):
    """Base class for retryable errors."""
    pass


class LLMError(RetryableError):
    """Error raised by LLM operations."""
    pass


class MediaProcessingError(RetryableError):
    """Error raised during media processing."""
    pass


T = TypeVar('T')


def retryable(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[tuple[Type[Exception], ...]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        retryable_exceptions: Tuple of exceptions to retry on

    Returns:
        Decorated function with retry behavior

    Example:
        ```python
        @retryable(max_attempts=3, initial_delay=1.0)
        async def api_call():
            # Function that might fail transiently
            pass
        ```
    """
    if retryable_exceptions is None:
        retryable_exceptions = (RetryableError,)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None
            delay = initial_delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)

                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** attempt),
                        max_delay
                    )

                    # Add jitter if enabled
                    if jitter:
                        delay *= (0.5 + random.random())

                    # Wait before retrying
                    await asyncio.sleep(delay)

            # This should never happen due to the raise above
            assert last_exception is not None
            raise last_exception

        return wrapper

    return decorator