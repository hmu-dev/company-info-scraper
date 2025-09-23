import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from api.middleware.tracing import (
    TracingMiddleware,
    setup_tracing,
    get_current_trace_context,
    request_id,
    trace_id,
    parent_id
)
import uuid
import json
import re

@pytest.fixture
def app():
    """Create a FastAPI app with tracing middleware for testing."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")
    
    setup_tracing(app)
    return app

@pytest.fixture
def client(app):
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)

def test_get_trace_headers():
    """Test extracting trace headers from request."""
    middleware = TracingMiddleware(None)
    
    # Create mock request with headers
    headers = {
        'x-request-id': 'test-request-id',
        'x-b3-traceid': 'test-trace-id',
        'x-b3-spanid': 'test-span-id',
        'x-b3-parentspanid': 'test-parent-id'
    }
    request = Mock(spec=Request)
    request.headers = headers
    
    trace_headers = middleware.get_trace_headers(request)
    assert trace_headers['x-request-id'] == 'test-request-id'
    assert trace_headers['x-b3-traceid'] == 'test-trace-id'
    assert trace_headers['x-b3-spanid'] == 'test-span-id'
    assert trace_headers['x-b3-parentspanid'] == 'test-parent-id'

def test_generate_ids_with_existing_headers():
    """Test ID generation with existing trace headers."""
    middleware = TracingMiddleware(None)
    
    trace_headers = {
        'x-request-id': 'test-request-id',
        'x-b3-traceid': 'test-trace-id',
        'x-b3-spanid': 'test-span-id'
    }
    
    ids = middleware.generate_ids(trace_headers)
    assert ids['request_id'] == 'test-request-id'
    assert ids['trace_id'] == 'test-trace-id'
    assert len(ids['span_id']) == 16  # New span ID is always generated
    assert ids['parent_id'] == 'test-span-id'

def test_generate_ids_without_headers():
    """Test ID generation without trace headers."""
    middleware = TracingMiddleware(None)
    
    ids = middleware.generate_ids({})
    
    # Check UUID format
    assert uuid.UUID(ids['request_id'])
    
    # Check trace ID format (16 hex chars)
    assert len(ids['trace_id']) == 16
    assert all(c in '0123456789abcdef' for c in ids['trace_id'])
    
    # Check span ID format (16 hex chars)
    assert len(ids['span_id']) == 16
    assert all(c in '0123456789abcdef' for c in ids['span_id'])
    
    # Parent ID should be None
    assert ids['parent_id'] is None

def test_set_trace_context():
    """Test setting trace context variables."""
    middleware = TracingMiddleware(None)
    
    ids = {
        'request_id': 'test-request-id',
        'trace_id': 'test-trace-id',
        'parent_id': 'test-parent-id'
    }
    
    middleware.set_trace_context(ids)
    
    assert request_id.get() == 'test-request-id'
    assert trace_id.get() == 'test-trace-id'
    assert parent_id.get() == 'test-parent-id'

def test_get_trace_response_headers():
    """Test generating trace response headers."""
    middleware = TracingMiddleware(None)
    
    ids = {
        'request_id': 'test-request-id',
        'trace_id': 'test-trace-id',
        'span_id': 'test-span-id',
        'parent_id': 'test-parent-id'
    }
    
    headers = middleware.get_trace_response_headers(ids)
    assert headers['x-request-id'] == 'test-request-id'
    assert headers['x-b3-traceid'] == 'test-trace-id'
    assert headers['x-b3-spanid'] == 'test-span-id'
    assert headers['x-b3-parentspanid'] == 'test-parent-id'

def test_get_trace_response_headers_no_parent():
    """Test generating trace response headers without parent ID."""
    middleware = TracingMiddleware(None)
    
    ids = {
        'request_id': 'test-request-id',
        'trace_id': 'test-trace-id',
        'span_id': 'test-span-id',
        'parent_id': None
    }
    
    headers = middleware.get_trace_response_headers(ids)
    assert headers['x-request-id'] == 'test-request-id'
    assert headers['x-b3-traceid'] == 'test-trace-id'
    assert headers['x-b3-spanid'] == 'test-span-id'
    assert 'x-b3-parentspanid' not in headers

def test_middleware_success(client):
    """Test successful request tracing."""
    response = client.get("/test")
    assert response.status_code == 200
    
    # Check response headers
    assert 'x-request-id' in response.headers
    assert 'x-b3-traceid' in response.headers
    assert 'x-b3-spanid' in response.headers
    
    # Check UUID format
    assert uuid.UUID(response.headers['x-request-id'])
    
    # Check trace ID format (16 hex chars)
    assert len(response.headers['x-b3-traceid']) == 16
    assert all(c in '0123456789abcdef' for c in response.headers['x-b3-traceid'])
    
    # Check span ID format (16 hex chars)
    assert len(response.headers['x-b3-spanid']) == 16
    assert all(c in '0123456789abcdef' for c in response.headers['x-b3-spanid'])

def test_middleware_error(client):
    """Test error request tracing."""
    with pytest.raises(ValueError, match="Test error"):
        client.get("/error")

def test_middleware_with_existing_headers(client):
    """Test request tracing with existing headers."""
    headers = {
        'x-request-id': 'test-request-id',
        'x-b3-traceid': 'test-trace-id',
        'x-b3-spanid': 'test-span-id',
        'x-b3-parentspanid': 'test-parent-id'
    }
    
    response = client.get("/test", headers=headers)
    assert response.status_code == 200
    
    # Check that existing headers were preserved
    assert response.headers['x-request-id'] == 'test-request-id'
    assert response.headers['x-b3-traceid'] == 'test-trace-id'
    assert response.headers['x-b3-parentspanid'] == 'test-span-id'
    
    # Check that a new span ID was generated
    assert 'x-b3-spanid' in response.headers
    assert response.headers['x-b3-spanid'] != 'test-span-id'
    assert len(response.headers['x-b3-spanid']) == 16

def test_get_current_trace_context():
    """Test getting current trace context."""
    # Set context variables
    request_id.set('test-request-id')
    trace_id.set('test-trace-id')
    parent_id.set('test-parent-id')
    
    context = get_current_trace_context()
    assert context['request_id'] == 'test-request-id'
    assert context['trace_id'] == 'test-trace-id'
    assert context['parent_id'] == 'test-parent-id'

def test_setup_tracing():
    """Test tracing middleware setup."""
    app = FastAPI()
    setup_tracing(app)
    
    # Check that middleware was added
    middleware = next(
        m for m in app.user_middleware
        if isinstance(m.cls, type) and m.cls.__name__ == "TracingMiddleware"
    )
    assert middleware is not None

@pytest.mark.asyncio
async def test_middleware_non_http():
    """Test handling of non-HTTP requests."""
    middleware = TracingMiddleware(AsyncMock())
    scope = {
        "type": "websocket",
        "headers": [],
        "client": ("127.0.0.1", 1234),
        "query_string": b"",
        "scheme": "ws",
        "server": ("testserver", 80)
    }
    receive = AsyncMock()
    send = AsyncMock()
    
    await middleware(scope, receive, send)
    middleware.app.assert_called_once_with(scope, receive, send)

@pytest.mark.asyncio
async def test_middleware_response_body_before_start():
    """Test error when response body is sent before response start."""
    middleware = TracingMiddleware(AsyncMock())
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "client": ("127.0.0.1", 1234),
        "query_string": b"",
        "scheme": "http",
        "server": ("testserver", 80)
    }
    receive = AsyncMock()
    send = AsyncMock()
    
    # Mock app to send response body before start
    async def mock_app(scope, receive, send):
        await send({"type": "http.response.body", "body": b"test"})
    
    middleware.app = mock_app
    
    with pytest.raises(RuntimeError, match="Response body sent before response start."):
        await middleware(scope, receive, send)
