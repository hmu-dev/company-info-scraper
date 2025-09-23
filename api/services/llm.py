from typing import Dict, Any, Optional
import json
import time
import boto3
from botocore.config import Config
from ..utils.retry import retryable, LLMError
from ..utils.logging import log_event


class LLMService:
    def __init__(
        self,
        region: str = "us-west-2",
        model_id: str = "anthropic.claude-instant-v1",
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ):
        """Initialize LLM service"""
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Initialize Bedrock client
        self.bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=region,
            config=Config(
                retries={"max_attempts": 3}, connect_timeout=5, read_timeout=30
            ),
        )

    def _format_prompt(self, system: str, user: str) -> str:
        """Format prompt for Claude"""
        return f"\n\nHuman: {system}\n\nHere is the content to analyze:\n{user}\n\nAssistant: I'll analyze the content and provide the information in the requested format."

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Claude response"""
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

    @retryable(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=True,
    )
    async def extract_content(
        self, text: str, prompt: str, temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Extract content using Bedrock

        Args:
            text: Text to process
            prompt: Extraction prompt
            temperature: Optional temperature override

        Returns:
            Extracted content

        Raises:
            LLMError: If LLM processing fails
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
            prompt_tokens = len(formatted_prompt.split())
            completion_tokens = len(response_body["completion"].split())

            # Log success
            duration = time.time() - start_time
            log_event(
                "llm_success",
                {
                    "model": self.model_id,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "duration": duration,
                    "cost_estimate_usd": (
                        prompt_tokens * 0.00163 / 1000  # Input cost
                        + completion_tokens * 0.00551 / 1000  # Output cost
                    ),
                },
            )

            return result

        except Exception as e:
            # Log error
            log_event(
                "llm_error",
                {
                    "model": self.model_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            # Convert to LLMError
            if isinstance(e, LLMError):
                raise
            else:
                raise LLMError(f"LLM processing failed: {str(e)}")

    def get_token_estimate(self, text: str) -> int:
        """Estimate token count for text"""
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
