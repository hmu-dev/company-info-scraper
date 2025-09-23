from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any

class ScrapeRequest(BaseModel):
    url: HttpUrl
    openai_api_key: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    include_base64: bool = False
    cursor: Optional[str] = None
    limit: Optional[int] = Field(default=10, ge=1, le=100)

class CompanyProfile(BaseModel):
    about_us: str
    our_culture: str
    our_team: str
    noteworthy_and_differentiated: str
    locations: str

class MediaMetadata(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: Optional[int] = None
    format: Optional[str] = None
    content_type: Optional[str] = None
    upload_date: Optional[str] = None

class MediaItem(BaseModel):
    url: str
    type: str  # "image" or "video"
    context: str
    metadata: MediaMetadata
    base64_data: Optional[str] = None
    filename: str
    priority: int

class PaginationMeta(BaseModel):
    total_count: int
    remaining_count: int
    has_more: bool
    next_cursor: Optional[str] = None
    previous_cursor: Optional[str] = None

class ProfileResponse(BaseModel):
    success: bool
    url_scraped: str
    profile: CompanyProfile
    error: Optional[str] = None

class MediaResponse(BaseModel):
    success: bool
    url_scraped: str
    media: List[MediaItem]
    pagination: Optional[PaginationMeta] = None
    error: Optional[str] = None

class CombinedResponse(BaseModel):
    success: bool
    url_scraped: str
    profile: CompanyProfile
    media: List[MediaItem]
    pagination: Optional[PaginationMeta] = None
    error: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_type: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
