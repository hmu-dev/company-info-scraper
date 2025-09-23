"""
API Endpoints Package

This package contains the FastAPI endpoint definitions for the AI Web Scraper service.
"""

from .media import router as media_router
from .profile import router as profile_router

__all__ = ["media_router", "profile_router"]
