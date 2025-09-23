"""
Unit tests for lambda_handler.py
"""

import json
from unittest.mock import Mock, patch

import pytest

from api.lambda_handler import lambda_handler


@pytest.fixture
def mock_context():
    context = Mock()
    context.aws_request_id = "test-request-id"
    return context


@pytest.fixture
def mock_event():
    return {
        "httpMethod": "POST",
        "path": "/v1/profile",
        "body": json.dumps({"url": "https://example.com"}),
    }


@pytest.fixture
def mock_handler():
    return Mock(
        return_value={
            "statusCode": 200,
            "body": json.dumps(
                {
                    "success": True,
                    "token_usage": {"prompt_tokens": 100, "completion_tokens": 50},
                    "model": "anthropic.claude-instant-v1",
                    "duration": 0.5,
                }
            ),
        }
    )


@pytest.fixture
def mock_media_response():
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "success": True,
                "media": [
                    {
                        "url": "https://example.com/image.jpg",
                        "type": "image",
                        "metadata": {"size_bytes": 1024},
                    }
                ],
                "duration": 0.3,
            }
        ),
    }


@pytest.fixture
def mock_cache_response():
    return {
        "statusCode": 200,
        "body": json.dumps(
            {"success": True, "cache_info": {"hit": True, "duration": 0.1}}
        ),
    }


@patch("api.lambda_handler.handler")
@patch("api.lambda_handler.log_llm_request")
def test_lambda_handler_llm_metrics(
    mock_log_llm, mock_handler, mock_event, mock_context
):
    """Test that LLM metrics are logged correctly"""
    # Setup
    mock_handler.return_value = {
        "statusCode": 200,
        "body": json.dumps(
            {
                "success": True,
                "token_usage": {"prompt_tokens": 100, "completion_tokens": 50},
                "model": "anthropic.claude-instant-v1",
                "duration": 0.5,
            }
        ),
    }

    # Execute
    response = lambda_handler(mock_event, mock_context)

    # Assert
    assert response["statusCode"] == 200
    mock_log_llm.assert_called_once_with(
        {
            "model": "anthropic.claude-instant-v1",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "duration": 0.5,
            "success": True,
        },
        "test-request-id",
    )


@patch("api.lambda_handler.handler")
@patch("api.lambda_handler.log_media_metrics")
def test_lambda_handler_media_metrics(
    mock_log_media, mock_handler, mock_event, mock_context, mock_media_response
):
    """Test that media metrics are logged correctly"""
    # Setup
    mock_handler.return_value = mock_media_response

    # Execute
    response = lambda_handler(mock_event, mock_context)

    # Assert
    assert response["statusCode"] == 200
    mock_log_media.assert_called_once_with(
        {
            "url": "https://example.com/image.jpg",
            "type": "image",
            "size": 1024,
            "duration": 0.3,
            "success": True,
        },
        "test-request-id",
    )


@patch("api.lambda_handler.handler")
@patch("api.lambda_handler.log_cache_metrics")
def test_lambda_handler_cache_metrics(
    mock_log_cache, mock_handler, mock_event, mock_context, mock_cache_response
):
    """Test that cache metrics are logged correctly"""
    # Setup
    mock_handler.return_value = mock_cache_response

    # Execute
    response = lambda_handler(mock_event, mock_context)

    # Assert
    assert response["statusCode"] == 200
    mock_log_cache.assert_called_once_with(
        {"operation": "Hit", "success": True, "duration": 0.1}, "test-request-id"
    )


@patch("api.lambda_handler.handler")
def test_lambda_handler_error(mock_handler, mock_event, mock_context):
    """Test that errors are handled correctly"""
    # Setup
    mock_handler.side_effect = Exception("Test error")

    # Execute
    response = lambda_handler(mock_event, mock_context)

    # Assert
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert body["success"] is False
    assert body["error"] == "Test error"
    assert body["error_type"] == "Exception"


@patch("api.lambda_handler.handler")
def test_lambda_handler_invalid_body(mock_handler, mock_event, mock_context):
    """Test handling of invalid response body"""
    # Setup
    mock_handler.return_value = {"statusCode": 200, "body": "invalid json"}

    # Execute
    response = lambda_handler(mock_event, mock_context)

    # Assert
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert body["success"] is False
    assert "error" in body
    assert body["error_type"] == "JSONDecodeError"
