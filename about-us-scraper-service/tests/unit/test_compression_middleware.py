"""Unit tests for compression middleware."""

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from api.middleware.compression import CompressionMiddleware
import gzip
import brotli
import zlib


@pytest.fixture
def app():
    """Create FastAPI test app."""
    app = FastAPI()

    @app.get("/test")
    def test_endpoint():
        """Test endpoint that returns a large response."""
        return {"data": "x" * 2000}

    @app.get("/small")
    def small_endpoint():
        """Test endpoint that returns a small response."""
        return {"data": "x" * 100}

    @app.get("/image")
    def image_endpoint():
        """Test endpoint that returns an image response."""
        return Response(content=b"fake-image-data", media_type="image/jpeg")

    @app.get("/stream")
    async def stream_endpoint():
        """Test endpoint that returns a streaming response."""
        from starlette.responses import StreamingResponse

        async def stream():
            for i in range(10):
                yield f"chunk{i}".encode()

        return StreamingResponse(stream())

    return app


@pytest.fixture
def client(app):
    """Create test client with compression middleware."""
    app.add_middleware(CompressionMiddleware, minimum_size=1000, compression_level=6)
    return TestClient(app)


def test_no_compression_small_response(client):
    """Test that small responses are not compressed."""
    response = client.get("/small", headers={"accept-encoding": "gzip, deflate, br"})
    assert response.status_code == 200
    assert "content-encoding" not in response.headers


def test_no_compression_excluded_type(client):
    """Test that excluded content types are not compressed."""
    response = client.get("/image", headers={"accept-encoding": "gzip, deflate, br"})
    assert response.status_code == 200
    assert "content-encoding" not in response.headers


def test_no_compression_no_accept_encoding(client):
    """Test that responses are not compressed without accept-encoding."""
    # Remove the default accept-encoding header
    response = client.get("/test", headers={"accept-encoding": ""})
    assert response.status_code == 200
    assert "content-encoding" not in response.headers


def test_brotli_compression(client):
    """Test brotli compression."""
    response = client.get("/test", headers={"accept-encoding": "br"})
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "br"
    # TestClient automatically decompresses the response
    assert b'"data":"' in response.content
    assert b"x" * 2000 in response.content


def test_gzip_compression(client):
    """Test gzip compression."""
    response = client.get("/test", headers={"accept-encoding": "gzip"})
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "gzip"
    # TestClient automatically decompresses the response
    assert b'"data":"' in response.content
    assert b"x" * 2000 in response.content


def test_deflate_compression(client):
    """Test deflate compression."""
    response = client.get("/test", headers={"accept-encoding": "deflate"})
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "deflate"
    # TestClient automatically decompresses the response
    assert b'"data":"' in response.content
    assert b"x" * 2000 in response.content


def test_compression_preference(client):
    """Test compression preference order (br > gzip > deflate)."""
    response = client.get("/test", headers={"accept-encoding": "gzip, deflate, br"})
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "br"


def test_compression_quality(client):
    """Test compression quality values."""
    response = client.get("/test", headers={"accept-encoding": "br;q=0.5, gzip;q=1.0"})
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "gzip"


def test_excluded_path(app):
    """Test that excluded paths are not compressed."""
    app.add_middleware(
        CompressionMiddleware, minimum_size=1000, excluded_paths=["/test"]
    )
    client = TestClient(app)
    response = client.get("/test", headers={"accept-encoding": "gzip, deflate, br"})
    assert response.status_code == 200
    assert "content-encoding" not in response.headers


def test_streaming_response(client):
    """Test that streaming responses are handled correctly."""
    response = client.get("/stream", headers={"accept-encoding": "gzip"})
    assert response.status_code == 200
    content = b"".join(response.iter_bytes())
    assert b"chunk" in content
