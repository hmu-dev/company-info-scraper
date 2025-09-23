"""
LLM service for content extraction using AWS Bedrock.

This module provides a service for extracting structured company information
from website content using AWS Bedrock's Claude-Instant model. It handles
prompt formatting, response parsing, token usage tracking, and error handling.

Classes:
    LLMService: Main service class for LLM interactions

Functions:
    _format_prompt: Format system and user prompts for Claude
    _parse_response: Parse and validate Claude's JSON response
    _estimate_tokens: Estimate token count for text
    extract_content: Extract structured content from text
"""

import json
import time
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config

from ..utils.logging import log_event
from ..utils.retry import LLMError, retryable


class LLMService:
    """
    Service for extracting content using AWS Bedrock.

    This class handles interactions with AWS Bedrock's Claude-Instant model,
    including prompt formatting, response parsing, and error handling.

    Attributes:
        model_id (str): Bedrock model identifier
        max_tokens (int): Maximum tokens in completion
        temperature (float): Model temperature (0-1)
        bedrock (boto3.client): Bedrock runtime client
    """

    def __init__(
        self,
        region: str = "us-west-2",
        model_id: str = "anthropic.claude-instant-v1",
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> None:
        """
        Initialize LLM service.

        Args:
            region: AWS region for Bedrock
            model_id: Bedrock model identifier
            max_tokens: Maximum tokens in completion
            temperature: Model temperature (0-1)
        """
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Initialize Bedrock client with retries and timeouts
        self.bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=region,
            config=Config(
                retries={"max_attempts": 3}, connect_timeout=5, read_timeout=30
            ),
        )

    def _format_prompt(self, system: str, user: str) -> str:
        """
        Format prompt for Claude.

        Combines system instructions and user content into Claude's
        expected prompt format.

        Args:
            system: System prompt with instructions
            user: User content to analyze

        Returns:
            Formatted prompt string
        """
        return (
            f"\n\nHuman: {system}\n\n"
            f"Here is the content to analyze:\n{user}\n\n"
            f"Assistant: I'll analyze the content and provide "
            f"the information in the requested format."
        )

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Claude response.

        Extracts and validates the JSON response from Claude's completion.

        Args:
            response: Raw response from Bedrock

        Returns:
            Parsed JSON response

        Raises:
            LLMError: If response is invalid or malformed
        """
        try:
            # Extract completion
            completion = response["completion"]

            # Parse JSON from completion
            try:
                result = json.loads(completion)
                return result
            except json.JSONDecodeError as e:
                raise LLMError(f"Invalid JSON response: {str(e)}")

        except KeyError as e:
            raise LLMError(f"Invalid response format: {str(e)}")

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses a simple character-based heuristic to estimate tokens.
        Actual token count may vary based on the tokenizer.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4

    @retryable(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=0.3,
        exponential_base=2.0,
        jitter=False,
    )
    async def extract_content(
        self, text: str, prompt: str, temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Extract content using Bedrock.

        Sends text to Bedrock for analysis and returns structured information
        based on the provided prompt. Includes automatic retries, token tracking,
        and cost estimation.

        Args:
            text: Text to process
            prompt: Extraction prompt
            temperature: Optional temperature override

        Returns:
            Extracted content as dictionary

        Raises:
            LLMError: If LLM processing fails after retries
        """
        try:
            start_time = time.time()

            # Format prompt
            formatted_prompt = self._format_prompt(prompt, text)

            # Prepare request body
            request_body = {
                "prompt": formatted_prompt,
                "max_tokens_to_sample": self.max_tokens,
                "temperature": temperature or self.temperature,
                "stop_sequences": ["\n\nHuman:"],
            }

            # Call Bedrock
            response = self.bedrock.invoke_model(
                modelId=self.model_id, body=json.dumps(request_body)
            )

            # Parse response
            response_body = json.loads(response["body"].read())
            result = self._parse_response(response_body)

            # Calculate token usage (approximate)
            prompt_tokens = self._estimate_tokens(formatted_prompt)
            completion_tokens = self._estimate_tokens(response_body["completion"])

            # Calculate cost estimate
            # Claude-Instant pricing:
            # Input: $0.00163 per 1K tokens
            # Output: $0.00551 per 1K tokens
            cost_estimate = (
                prompt_tokens * 0.00163 / 1000  # Input cost
                + completion_tokens * 0.00551 / 1000  # Output cost
            )

            # Log success with metrics
            duration = time.time() - start_time
            log_event(
                "llm_success",
                {
                    "model": self.model_id,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "duration": duration,
                    "cost_estimate_usd": cost_estimate,
                },
            )

            return result

        except Exception as e:
            # Log error with details
            log_event(
                "llm_error",
                {
                    "model": self.model_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            # Convert to LLMError for consistent error handling
            if isinstance(e, LLMError):
                raise
            else:
                raise LLMError(f"LLM processing failed: {str(e)}")
