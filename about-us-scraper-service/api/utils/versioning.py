"""
API versioning utilities.

This module provides utilities for managing API versions, including version
comparison, validation, and middleware for handling version headers.
"""

import re
from typing import Callable, Dict, Optional, Union
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import semver


class VersionError(Exception):
    """Base exception for version-related errors."""

    pass


class APIVersion:
    """
    API version representation.

    Attributes:
        version: Semantic version string
    """

    def __init__(self, version: str):
        """
        Initialize API version.

        Args:
            version: Version string (e.g., "1.0.0")

        Raises:
            VersionError: If version string is invalid
        """
        try:
            self.version = str(semver.VersionInfo.parse(version))
        except ValueError as e:
            raise VersionError(f"Invalid version format: {e}")

    def __str__(self) -> str:
        return self.version

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, APIVersion):
            return NotImplemented
        return self.version == other.version

    def __lt__(self, other: "APIVersion") -> bool:
        return semver.compare(self.version, other.version) < 0

    def __le__(self, other: "APIVersion") -> bool:
        return semver.compare(self.version, other.version) <= 0

    def __gt__(self, other: "APIVersion") -> bool:
        return semver.compare(self.version, other.version) > 0

    def __ge__(self, other: "APIVersion") -> bool:
        return semver.compare(self.version, other.version) >= 0


class VersionHeader:
    """Constants for version-related headers."""

    CURRENT = "X-API-Version"
    LATEST = "X-API-Latest-Version"
    DEPRECATION = "Warning"


def parse_version(version_str: Optional[str]) -> Optional[APIVersion]:
    """
    Parse version string into APIVersion object.

    Args:
        version_str: Version string to parse

    Returns:
        APIVersion object or None if version_str is None

    Raises:
        VersionError: If version string is invalid
    """
    if version_str is None:
        return None
    return APIVersion(version_str)


class VersionManager:
    """
    Manages API versions and handlers.

    Attributes:
        current_version: Current API version
        min_version: Minimum supported version
        max_version: Maximum supported version
        handlers: Version-specific handlers
    """

    def __init__(self, current_version: str, min_version: str, max_version: str):
        """
        Initialize version manager.

        Args:
            current_version: Current API version
            min_version: Minimum supported version
            max_version: Maximum supported version
        """
        self.current_version = APIVersion(current_version)
        self.min_version = APIVersion(min_version)
        self.max_version = APIVersion(max_version)
        self.handlers: Dict[str, Dict[str, Callable]] = {}

    def register_handler(
        self,
        version: str,
        path: str,
        handler: Callable,
        deprecation_notice: Optional[str] = None,
    ) -> None:
        """
        Register a version-specific handler.

        Args:
            version: Version string
            path: API path
            handler: Handler function
            deprecation_notice: Optional deprecation notice
        """
        if version not in self.handlers:
            self.handlers[version] = {}
        self.handlers[version][path] = {
            "handler": handler,
            "deprecation_notice": deprecation_notice,
        }

    def get_handler(self, version: Optional[str], path: str) -> Optional[Dict]:
        """
        Get handler for specified version and path.

        Args:
            version: Version string
            path: API path

        Returns:
            Handler info or None if not found
        """
        if version is None:
            return None
        return self.handlers.get(version, {}).get(path)

    def version_middleware(self, app: FastAPI) -> Callable:
        """
        Create version middleware for FastAPI app.

        Args:
            app: FastAPI application

        Returns:
            Middleware function
        """

        async def middleware(request: Request, call_next: Callable) -> Response:
            """
            Middleware for handling API versions.

            Args:
                request: FastAPI request
                call_next: Next middleware/handler

            Returns:
                FastAPI response
            """
            # Skip version check for excluded paths
            if request.url.path in ["/health", "/metrics", "/openapi.json"]:
                return await call_next(request)

            # Extract version from path
            version_match = re.match(r"/v(\d+\.\d+\.\d+)/", request.url.path)
            version = version_match.group(1) if version_match else None

            # Validate version
            if version:
                version_obj = parse_version(version)
                if version_obj < parse_version("1.0.0"):
                    raise VersionError(f"Version {version} is not supported")
                if version_obj < self.min_version:
                    raise VersionError(
                        f"Version {version} is no longer supported. Minimum supported version is {self.min_version}"
                    )
                if version_obj > self.max_version:
                    raise VersionError(
                        f"Version {version} is not yet supported. Maximum supported version is {self.max_version}"
                    )

            # Get handler
            path = (
                request.url.path.replace(f"/v{version}", "")
                if version
                else request.url.path
            )
            handler_info = self.get_handler(version, path)

            # Process request
            response = await call_next(request)

            # Add version headers
            response.headers[VersionHeader.CURRENT] = str(self.current_version)
            response.headers[VersionHeader.LATEST] = str(self.max_version)

            # Add deprecation notice if applicable
            if handler_info and handler_info.get("deprecation_notice"):
                response.headers[VersionHeader.DEPRECATION] = handler_info[
                    "deprecation_notice"
                ]

            return response

        return middleware


def setup_versioning(
    app: FastAPI, current_version: str, min_version: str, max_version: str
) -> VersionManager:
    """
    Set up API versioning for FastAPI app.

    Args:
        app: FastAPI application
        current_version: Current API version
        min_version: Minimum supported version
        max_version: Maximum supported version

    Returns:
        VersionManager instance
    """
    manager = VersionManager(current_version, min_version, max_version)

    # Add version middleware
    app.middleware("http")(manager.version_middleware(app))

    return manager
