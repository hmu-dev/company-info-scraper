"""
API Utilities Package

This package contains utility classes and functions for the AI Web Scraper service.
"""

from .cache import Cache
from .logging import (
    log_cache_metrics,
    log_event,
    log_llm_request,
    log_media_metrics,
    publish_metrics,
)
from .pagination import PaginatedResult, decode_cursor, paginate_items
from .retry import (
    LLMError,
    MediaProcessingError,
    RetryableError,
    RetryConfig,
    retry_async,
    retryable,
)
from .storage import MediaStorage
from .versioning import setup_versioning

__all__ = [
    "Cache",
    "log_event",
    "publish_metrics",
    "log_llm_request",
    "log_media_metrics",
    "log_cache_metrics",
    "PaginatedResult",
    "paginate_items",
    "decode_cursor",
    "retry_async",
    "retryable",
    "RetryConfig",
    "RetryableError",
    "LLMError",
    "MediaProcessingError",
    "MediaStorage",
    "setup_versioning",
]
