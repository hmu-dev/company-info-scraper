"""
Unit tests for the retry utility.

This module tests the retry decorator and error classes, including
exponential backoff, jitter, and error handling.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock

from api.utils.retry import retryable, RetryableError, LLMError


class TestError(RetryableError):
    """Test error class."""
    pass


@pytest.mark.asyncio
async def test_retryable_success():
    """Test successful function execution."""
    # Given
    mock_func = Mock(return_value=42)

    @retryable()
    async def test_func():
        return mock_func()

    # When
    result = await test_func()

    # Then
    assert result == 42
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_retryable_retry_success():
    """Test successful retry after failures."""
    # Given
    mock_func = Mock(side_effect=[TestError(), TestError(), 42])

    @retryable(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=1.0,
        exponential_base=2.0,
        jitter=False
    )
    async def test_func():
        return mock_func()

    # When
    result = await test_func()

    # Then
    assert result == 42
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_retryable_max_attempts():
    """Test maximum retry attempts."""
    # Given
    mock_func = Mock(side_effect=TestError())

    @retryable(max_attempts=3)
    async def test_func():
        return mock_func()

    # When/Then
    with pytest.raises(TestError):
        await test_func()
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_retryable_non_retryable_error():
    """Test non-retryable error."""
    # Given
    mock_func = Mock(side_effect=ValueError())

    @retryable()
    async def test_func():
        return mock_func()

    # When/Then
    with pytest.raises(ValueError):
        await test_func()
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_retryable_custom_exceptions():
    """Test custom retryable exceptions."""
    # Given
    mock_func = Mock(side_effect=[ValueError(), ValueError(), 42])

    @retryable(retryable_exceptions=(ValueError,))
    async def test_func():
        return mock_func()

    # When
    result = await test_func()

    # Then
    assert result == 42
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_retryable_exponential_backoff():
    """Test exponential backoff delays."""
    # Given
    mock_func = Mock(side_effect=[TestError(), TestError(), 42])
    @retryable(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=0.3,
        exponential_base=2.0,
        jitter=False
    )
    async def test_func():
        return mock_func()

    # When
    mock_sleep = AsyncMock()

    with patch('asyncio.sleep', mock_sleep):
        result = await test_func()

    # Then
    assert result == 42
    assert mock_func.call_count == 3
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(0.1)  # First retry
    mock_sleep.assert_any_call(0.2)  # Second retry


@pytest.mark.asyncio
async def test_retryable_max_delay():
    """Test maximum delay cap."""
    # Given
    mock_func = Mock(side_effect=[TestError(), TestError(), 42])
    @retryable(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=0.2,
        exponential_base=2.0,
        jitter=False
    )
    async def test_func():
        return mock_func()

    # When
    mock_sleep = AsyncMock()

    with patch('asyncio.sleep', mock_sleep):
        result = await test_func()

    # Then
    assert result == 42
    assert mock_func.call_count == 3
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(0.1)  # First retry
    mock_sleep.assert_any_call(0.2)  # Second retry (capped)
