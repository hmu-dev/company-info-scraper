"""
Models for the About Us Scraper Service API.

This module defines the Pydantic models used for request/response validation
and serialization in the API. It includes models for company profiles,
media assets, pagination, and error responses.

Models:
    - CompanyProfile: Company information extracted from websites
    - MediaAsset: Image or video asset with metadata
    - PaginationMeta: Pagination information for media responses
    - ScrapeRequest: Base request model for scraping endpoints
    - ProfileResponse: Response model for profile endpoint
    - MediaResponse: Response model for media endpoint
    - ErrorResponse: Standard error response model
"""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, HttpUrl, constr, field_validator
from datetime import datetime


class CompanyProfile(BaseModel):
    """
    Company information extracted from a website.

    Attributes:
        about_us (str): General company description and history
        our_culture (str): Company culture and values
        our_team (str): Team information and leadership
        noteworthy_and_differentiated (str): Unique company features
        locations (str): Company location information
    """
    about_us: str = Field(
        description="General company description and history"
    )
    our_culture: str = Field(
        description="Company culture and values"
    )
    our_team: str = Field(
        description="Team information and leadership"
    )
    noteworthy_and_differentiated: str = Field(
        description="Unique company features"
    )
    locations: str = Field(
        description="Company location information"
    )


class MediaMetadata(BaseModel):
    """
    Metadata for media assets.

    Attributes:
        width (Optional[int]): Image/video width in pixels
        height (Optional[int]): Image/video height in pixels
        size_bytes (int): File size in bytes
        format (str): File format (e.g., jpeg, png, mp4)
        priority (float): Relevance score (0-1)
        duration_seconds (Optional[float]): Video duration in seconds
    """
    width: Optional[int] = Field(
        description="Image/video width in pixels"
    )
    height: Optional[int] = Field(
        description="Image/video height in pixels"
    )
    size_bytes: int = Field(
        description="File size in bytes",
        gt=0
    )
    format: str = Field(
        description="File format (e.g., jpeg, png, mp4)"
    )
    priority: int = Field(
        description="Relevance score (0-100)",
        ge=0,
        le=100
    )
    duration_seconds: Optional[float] = Field(
        description="Video duration in seconds",
        gt=0
    )


class MediaAsset(BaseModel):
    """
    Media asset extracted from a website.

    Attributes:
        url (HttpUrl): URL of the media asset
        type (str): Asset type (image or video)
        metadata (MediaMetadata): Asset metadata
        context (str): Context in which the media appears
    """
    url: HttpUrl = Field(
        description="URL of the media asset"
    )
    type: str = Field(
        description="Asset type (image or video)",
        pattern="^(image|video)$"
    )
    metadata: MediaMetadata = Field(
        description="Asset metadata"
    )
    context: str = Field(
        description="Context in which the media appears"
    )


class PaginationMeta(BaseModel):
    """
    Pagination metadata for responses.

    Attributes:
        next_cursor (Optional[str]): Token for next page
        has_more (bool): Whether more items exist
        total_count (int): Total number of items
        remaining_count (int): Number of items remaining
    """
    next_cursor: Optional[str] = Field(
        description="Token for next page"
    )
    has_more: bool = Field(
        description="Whether more items exist"
    )
    total_count: int = Field(
        description="Total number of items",
        ge=0
    )
    remaining_count: int = Field(
        description="Number of items remaining",
        ge=0
    )


class ScrapeRequest(BaseModel):
    """
    Base request model for scraping endpoints.

    Attributes:
        url (HttpUrl): Website URL to scrape
        cursor (Optional[str]): Pagination cursor
        limit (Optional[int]): Number of items per page
        model (str): LLM model to use
        openai_api_key (Optional[str]): OpenAI API key (deprecated)
    """
    url: HttpUrl = Field(
        description="Website URL to scrape"
    )
    cursor: Optional[str] = Field(
        description="Pagination cursor",
        default=None
    )
    limit: Optional[int] = Field(
        description="Number of items per page",
        ge=1,
        le=50,
        default=10
    )
    model: str = Field(
        description="LLM model to use",
        pattern="^(anthropic\\.claude-instant-v1|gpt-3\\.5-turbo|gpt-4)$"
    )
    openai_api_key: Optional[str] = Field(
        description="OpenAI API key (deprecated)",
        default=None
    )

    @field_validator("url")
    @classmethod
    def validate_url_length(cls, v: str) -> str:
        """Validate URL length."""
        if len(str(v)) > 2048:
            raise ValueError("URL too long (max 2048 characters)")
        return v


class TokenUsage(BaseModel):
    """
    LLM token usage information.

    Attributes:
        prompt_tokens (int): Number of tokens in prompt
        completion_tokens (int): Number of tokens in completion
    """
    prompt_tokens: int = Field(
        description="Number of tokens in prompt",
        ge=0
    )
    completion_tokens: int = Field(
        description="Number of tokens in completion",
        ge=0
    )


class BaseResponse(BaseModel):
    """
    Base response model with common fields.

    Attributes:
        success (bool): Whether the request succeeded
        duration (float): Processing time in seconds
    """
    success: bool = Field(
        description="Whether the request succeeded"
    )
    duration: float = Field(
        description="Processing time in seconds",
        ge=0
    )


class ProfileResponse(BaseResponse):
    """
    Response model for profile endpoint.

    Attributes:
        data (CompanyProfile): Extracted company information
        token_usage (TokenUsage): LLM token usage stats
    """
    data: CompanyProfile = Field(
        description="Extracted company information"
    )
    token_usage: TokenUsage = Field(
        description="LLM token usage stats"
    )


class MediaResponse(BaseResponse):
    """
    Response model for media endpoint.

    Attributes:
        success (bool): Whether the request succeeded
        duration (float): Processing time in seconds
        url_scraped (HttpUrl): URL that was scraped
        media (List[MediaAsset]): List of media assets
        pagination (PaginationMeta): Pagination metadata
    """
    url_scraped: HttpUrl = Field(
        description="URL that was scraped"
    )
    media: List[MediaAsset] = Field(
        description="List of media assets"
    )
    pagination: PaginationMeta = Field(
        description="Pagination metadata"
    )


class ErrorResponse(BaseModel):
    """
    Standard error response model.

    Attributes:
        success (bool): Always False for errors
        error (str): Error message
        error_type (str): Type of error
        request_id (str): Unique request identifier
        timestamp (datetime): Error timestamp
    """
    success: bool = Field(
        description="Always False for errors",
        default=False
    )
    error: str = Field(
        description="Error message"
    )
    error_type: str = Field(
        description="Type of error"
    )
    request_id: str = Field(
        description="Unique request identifier"
    )
    timestamp: datetime = Field(
        description="Error timestamp",
        default_factory=datetime.utcnow
    )
