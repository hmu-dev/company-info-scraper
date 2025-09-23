import pytest
from unittest.mock import Mock, AsyncMock, patch, ANY
import json
import time
from botocore.exceptions import ClientError
from api.services.llm import LLMService, LLMError


@pytest.fixture
def mock_bedrock():
    """Create a mock Bedrock client."""
    with patch("boto3.client") as mock_client:
        mock_bedrock = Mock()
        mock_client.return_value = mock_bedrock
        yield mock_bedrock


@pytest.fixture
def llm_service(mock_bedrock):
    """Create an LLM service instance with mocked Bedrock client."""
    return LLMService()


def test_init_default_params():
    """Test LLM service initialization with default parameters."""
    service = LLMService()
    assert service.model_id == "anthropic.claude-instant-v1"
    assert service.max_tokens == 1000
    assert service.temperature == 0.7


def test_init_custom_params():
    """Test LLM service initialization with custom parameters."""
    service = LLMService(
        region="us-east-1", model_id="custom-model", max_tokens=500, temperature=0.5
    )
    assert service.model_id == "custom-model"
    assert service.max_tokens == 500
    assert service.temperature == 0.5


def test_format_prompt():
    """Test prompt formatting."""
    service = LLMService()
    prompt = service._format_prompt(system="Extract information", user="Sample text")
    assert "Human: Extract information" in prompt
    assert "Sample text" in prompt
    assert "Assistant:" in prompt


def test_parse_response_success():
    """Test successful response parsing."""
    service = LLMService()
    response = {"completion": '{"key": "value"}'}
    result = service._parse_response(response)
    assert result == {"key": "value"}


def test_parse_response_invalid_json():
    """Test parsing invalid JSON response."""
    service = LLMService()
    response = {"completion": "not json"}
    with pytest.raises(LLMError, match="Invalid JSON response"):
        service._parse_response(response)


def test_parse_response_missing_completion():
    """Test parsing response without completion."""
    service = LLMService()
    response = {}
    with pytest.raises(LLMError, match="Invalid response format"):
        service._parse_response(response)


def test_estimate_tokens():
    """Test token estimation."""
    service = LLMService()
    text = "This is a test" * 10  # 140 characters
    tokens = service._estimate_tokens(text)
    assert tokens == 35  # 140 / 4 = 35


@pytest.mark.asyncio
async def test_extract_content_success(llm_service, mock_bedrock):
    """Test successful content extraction."""
    # Mock response body
    mock_response = {
        "body": Mock(
            read=Mock(return_value=json.dumps({"completion": '{"result": "success"}'}))
        )
    }
    mock_bedrock.invoke_model.return_value = mock_response

    # Call extract_content
    result = await llm_service.extract_content(
        text="Sample text", prompt="Extract info"
    )

    # Check result
    assert result == {"result": "success"}

    # Verify Bedrock call
    mock_bedrock.invoke_model.assert_called_once_with(
        modelId="anthropic.claude-instant-v1", body=ANY
    )
    body = json.loads(mock_bedrock.invoke_model.call_args[1]["body"])
    assert "prompt" in body
    assert body["max_tokens_to_sample"] == 1000
    assert body["temperature"] == 0.7


@pytest.mark.asyncio
async def test_extract_content_custom_temperature(llm_service, mock_bedrock):
    """Test content extraction with custom temperature."""
    # Mock response body
    mock_response = {
        "body": Mock(
            read=Mock(return_value=json.dumps({"completion": '{"result": "success"}'}))
        )
    }
    mock_bedrock.invoke_model.return_value = mock_response

    # Call extract_content with custom temperature
    await llm_service.extract_content(
        text="Sample text", prompt="Extract info", temperature=0.3
    )

    # Verify temperature was used
    body = json.loads(mock_bedrock.invoke_model.call_args[1]["body"])
    assert body["temperature"] == 0.3


@pytest.mark.asyncio
async def test_extract_content_bedrock_error(llm_service, mock_bedrock):
    """Test handling of Bedrock API errors."""
    # Mock Bedrock error
    mock_bedrock.invoke_model.side_effect = ClientError(
        error_response={"Error": {"Message": "API error"}},
        operation_name="invoke_model",
    )

    # Call extract_content and check error
    with pytest.raises(LLMError, match="LLM processing failed"):
        await llm_service.extract_content(text="Sample text", prompt="Extract info")


@pytest.mark.asyncio
async def test_extract_content_invalid_response(llm_service, mock_bedrock):
    """Test handling of invalid response format."""
    # Mock invalid response
    mock_response = {
        "body": Mock(read=Mock(return_value=json.dumps({"completion": "not json"})))
    }
    mock_bedrock.invoke_model.return_value = mock_response

    # Call extract_content and check error
    with pytest.raises(LLMError, match="Invalid JSON response"):
        await llm_service.extract_content(text="Sample text", prompt="Extract info")


@pytest.mark.asyncio
async def test_extract_content_retries(llm_service, mock_bedrock):
    """Test automatic retries on failure."""
    # Mock temporary failure then success
    mock_response = {
        "body": Mock(
            read=Mock(return_value=json.dumps({"completion": '{"result": "success"}'}))
        )
    }
    mock_bedrock.invoke_model.side_effect = [
        ClientError(
            error_response={"Error": {"Message": "Temporary error"}},
            operation_name="invoke_model",
        ),
        mock_response,
    ]

    # Call extract_content
    result = await llm_service.extract_content(
        text="Sample text", prompt="Extract info"
    )

    # Check result and retry count
    assert result == {"result": "success"}
    assert mock_bedrock.invoke_model.call_count == 2


@pytest.mark.asyncio
async def test_extract_content_max_retries(llm_service, mock_bedrock):
    """Test maximum retry limit."""
    # Mock persistent failure
    error = ClientError(
        error_response={"Error": {"Message": "API error"}},
        operation_name="invoke_model",
    )
    mock_bedrock.invoke_model.side_effect = error

    # Call extract_content and check error
    with pytest.raises(LLMError, match="LLM processing failed"):
        await llm_service.extract_content(text="Sample text", prompt="Extract info")

    # Check retry count
    assert mock_bedrock.invoke_model.call_count == 3  # Initial + 2 retries


@pytest.mark.asyncio
async def test_extract_content_metrics(llm_service, mock_bedrock):
    """Test metrics logging for successful extraction."""
    # Mock response
    mock_response = {
        "body": Mock(
            read=Mock(return_value=json.dumps({"completion": '{"result": "success"}'}))
        )
    }
    mock_bedrock.invoke_model.return_value = mock_response

    # Mock logging
    with patch("api.services.llm.log_event") as mock_log:
        # Call extract_content
        await llm_service.extract_content(text="Sample text", prompt="Extract info")

        # Check metrics logging
        mock_log.assert_called_with(
            "llm_success",
            {
                "model": "anthropic.claude-instant-v1",
                "prompt_tokens": ANY,
                "completion_tokens": ANY,
                "duration": ANY,
                "cost_estimate_usd": ANY,
            },
        )


@pytest.mark.asyncio
async def test_extract_content_error_logging(llm_service, mock_bedrock):
    """Test error logging."""
    # Mock error
    error = ClientError(
        error_response={"Error": {"Message": "API error"}},
        operation_name="invoke_model",
    )
    mock_bedrock.invoke_model.side_effect = error

    # Mock logging
    with patch("api.services.llm.log_event") as mock_log:
        # Call extract_content
        with pytest.raises(LLMError):
            await llm_service.extract_content(text="Sample text", prompt="Extract info")

        # Check error logging
        mock_log.assert_called_with(
            "llm_error",
            {
                "model": "anthropic.claude-instant-v1",
                "error": ANY,
                "error_type": "ClientError",
            },
        )
