"""
Unit tests for the versioning utility.

This module tests the API versioning implementation, including version
parsing, validation, and deprecation handling.
"""

from unittest.mock import Mock, AsyncMock
import pytest
from fastapi import Request, Response
from api.utils.versioning import (
    APIVersion,
    VersionError,
    VersionHeader,
    VersionManager,
    parse_version
)


def test_parse_version_valid():
    """Test valid version parsing."""
    # Given/When
    version = parse_version('1.2.3')

    # Then
    assert str(version) == '1.2.3'


def test_parse_version_invalid():
    """Test invalid version parsing."""
    # Given/When/Then
    with pytest.raises(VersionError):
        parse_version('invalid')


def test_version_comparison():
    """Test version comparison."""
    # Given
    v1 = parse_version('1.2.3')
    v2 = parse_version('1.3.0')
    v3 = parse_version('2.0.0')

    # Then
    assert v1 < v2 < v3
    assert v3 > v2 > v1
    assert v1 <= v1
    assert v1 >= v1
    assert v1 == parse_version('1.2.3')
    assert v1 != v2


@pytest.mark.asyncio
async def test_version_middleware_no_version():
    """Test middleware with no version in path."""
    # Given
    manager = VersionManager(
        current_version='2.0.0',
        min_version='1.0.0',
        max_version='3.0.0'
    )
    request = Mock(spec=Request)
    request.url = Mock()
    request.url.path = "/test"
    response = Mock(spec=Response)
    response.headers = {}
    call_next = AsyncMock(return_value=response)
    app = Mock()
    app.middleware = Mock()

    # When
    middleware = manager.version_middleware(app)
    result = await middleware(request, call_next)

    # Then
    assert result == response
    assert response.headers[VersionHeader.CURRENT] == '2.0.0'
    assert response.headers[VersionHeader.LATEST] == '3.0.0'


@pytest.mark.asyncio
async def test_version_middleware_valid_version():
    """Test middleware with valid version in path."""
    # Given
    manager = VersionManager(
        current_version='2.0.0',
        min_version='1.0.0',
        max_version='3.0.0'
    )
    request = Mock(spec=Request)
    request.url = Mock()
    request.url.path = "/v1.5.0/test"
    response = Mock(spec=Response)
    response.headers = {}
    call_next = AsyncMock(return_value=response)
    app = Mock()
    app.middleware = Mock()

    # When
    middleware = manager.version_middleware(app)
    result = await middleware(request, call_next)

    # Then
    assert result == response
    assert response.headers[VersionHeader.CURRENT] == '2.0.0'
    assert response.headers[VersionHeader.LATEST] == '3.0.0'


@pytest.mark.asyncio
async def test_version_middleware_deprecated_version():
    """Test middleware with deprecated version in path."""
    # Given
    manager = VersionManager(
        current_version='2.0.0',
        min_version='1.0.0',
        max_version='3.0.0'
    )
    request = Mock(spec=Request)
    request.url = Mock()
    request.url.path = "/v1.0.0/test"
    response = Mock(spec=Response)
    response.headers = {}
    call_next = AsyncMock(return_value=response)
    app = Mock()
    app.middleware = Mock()

    # Register handler with deprecation notice
    manager.register_handler(
        version='1.0.0',
        path='/test',
        handler=Mock(),
        deprecation_notice='This version will be deprecated'
    )

    # When
    middleware = manager.version_middleware(app)
    result = await middleware(request, call_next)

    # Then
    assert result == response
    assert response.headers[VersionHeader.CURRENT] == '2.0.0'
    assert response.headers[VersionHeader.LATEST] == '3.0.0'
    assert response.headers[VersionHeader.DEPRECATION] == 'This version will be deprecated'


@pytest.mark.asyncio
async def test_version_middleware_unsupported_version():
    """Test middleware with unsupported version in path."""
    # Given
    manager = VersionManager(
        current_version='2.0.0',
        min_version='1.0.0',
        max_version='3.0.0'
    )
    app = Mock()
    app.middleware = Mock()

    # When/Then
    middleware = manager.version_middleware(app)
    request = Mock(spec=Request)
    request.url = Mock()
    request.url.path = "/v0.9.0/test"
    call_next = AsyncMock()

    with pytest.raises(VersionError) as exc_info:
        await middleware(request, call_next)

    assert str(exc_info.value) == "Version 0.9.0 is not supported"


def test_register_handler():
    """Test handler registration."""
    # Given
    manager = VersionManager(
        current_version='2.0.0',
        min_version='1.0.0',
        max_version='3.0.0'
    )
    handler = Mock()
    path = '/test'
    version = '1.0.0'
    notice = 'Deprecation notice'

    # When
    manager.register_handler(version, path, handler, notice)

    # Then
    handler_info = manager.get_handler(version, path)
    assert handler_info is not None
    assert handler_info['handler'] == handler
    assert handler_info['deprecation_notice'] == notice


def test_get_handler_not_found():
    """Test handler lookup for non-existent path."""
    # Given
    manager = VersionManager(
        current_version='2.0.0',
        min_version='1.0.0',
        max_version='3.0.0'
    )

    # When
    handler_info = manager.get_handler('1.0.0', '/nonexistent')

    # Then
    assert handler_info is None