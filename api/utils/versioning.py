from fastapi import FastAPI, Request, Response
from typing import Dict, Any, Optional, List, Callable
import re
import semver
from ..utils.logging import log_event

class VersionManager:
    def __init__(self, 
                 current_version: str = "1.0.0",
                 min_version: str = "1.0.0",
                 max_version: str = "2.0.0"):
        """
        Initialize version manager
        
        Args:
            current_version: Current API version
            min_version: Minimum supported version
            max_version: Maximum supported version
        """
        self.current_version = semver.VersionInfo.parse(current_version)
        self.min_version = semver.VersionInfo.parse(min_version)
        self.max_version = semver.VersionInfo.parse(max_version)
        
        # Store version-specific handlers
        self.handlers: Dict[str, Dict[str, Callable]] = {}
        
        # Store deprecation notices
        self.deprecation_notices: Dict[str, str] = {}
    
    def register_handler(self, 
                        version: str,
                        path: str,
                        handler: Callable,
                        deprecation_notice: Optional[str] = None):
        """
        Register a version-specific handler
        
        Args:
            version: API version (e.g., "1.0.0")
            path: API path (e.g., "/media")
            handler: Handler function
            deprecation_notice: Optional deprecation notice
        """
        if version not in self.handlers:
            self.handlers[version] = {}
        
        self.handlers[version][path] = handler
        
        if deprecation_notice:
            self.deprecation_notices[f"{version}:{path}"] = deprecation_notice
    
    def get_handler(self, version: str, path: str) -> Optional[Callable]:
        """Get handler for specific version and path"""
        if version in self.handlers and path in self.handlers[version]:
            return self.handlers[version][path]
        return None
    
    def get_deprecation_notice(self, version: str, path: str) -> Optional[str]:
        """Get deprecation notice for specific version and path"""
        return self.deprecation_notices.get(f"{version}:{path}")
    
    def parse_version(self, version_str: str) -> Optional[semver.VersionInfo]:
        """Parse version string into semver object"""
        try:
            # Handle v prefix
            if version_str.startswith('v'):
                version_str = version_str[1:]
            
            # Parse version
            return semver.VersionInfo.parse(version_str)
        except ValueError:
            return None
    
    def is_version_supported(self, version: semver.VersionInfo) -> bool:
        """Check if version is supported"""
        return self.min_version <= version < self.max_version
    
    def get_latest_compatible_version(self, path: str, 
                                    requested_version: semver.VersionInfo) -> Optional[str]:
        """Get latest compatible version for path"""
        compatible_versions = []
        
        for version in self.handlers.keys():
            version_obj = semver.VersionInfo.parse(version)
            if (version_obj <= requested_version and 
                path in self.handlers[version]):
                compatible_versions.append(version_obj)
        
        if compatible_versions:
            return str(max(compatible_versions))
        
        return None

class VersionedAPI:
    def __init__(self, app: FastAPI, version_manager: VersionManager):
        """
        Initialize versioned API
        
        Args:
            app: FastAPI application
            version_manager: Version manager instance
        """
        self.app = app
        self.version_manager = version_manager
    
    async def handle_request(self, request: Request) -> Response:
        """Handle versioned request"""
        # Extract version from path
        path_parts = request.url.path.split('/')
        if len(path_parts) < 3 or not path_parts[1].startswith('v'):
            return Response(
                content='{"error": "Invalid API version format"}',
                status_code=400,
                media_type="application/json"
            )
        
        version_str = path_parts[1][1:]  # Remove 'v' prefix
        path = '/' + '/'.join(path_parts[2:])
        
        # Parse and validate version
        version = self.version_manager.parse_version(version_str)
        if not version:
            return Response(
                content='{"error": "Invalid version format"}',
                status_code=400,
                media_type="application/json"
            )
        
        if not self.version_manager.is_version_supported(version):
            return Response(
                content='{"error": "Version not supported"}',
                status_code=400,
                media_type="application/json"
            )
        
        # Get latest compatible version
        latest_version = self.version_manager.get_latest_compatible_version(
            path, version)
        
        if not latest_version:
            return Response(
                content='{"error": "No compatible handler found"}',
                status_code=404,
                media_type="application/json"
            )
        
        # Get handler
        handler = self.version_manager.get_handler(latest_version, path)
        if not handler:
            return Response(
                content='{"error": "Handler not found"}',
                status_code=404,
                media_type="application/json"
            )
        
        # Check for deprecation
        deprecation_notice = self.version_manager.get_deprecation_notice(
            latest_version, path)
        
        # Add version headers
        headers = {
            "X-API-Version": latest_version,
            "X-API-Latest-Version": str(self.version_manager.current_version)
        }
        
        if deprecation_notice:
            headers["Warning"] = f'299 - "{deprecation_notice}"'
        
        # Log request
        log_event("api_request", {
            "path": path,
            "requested_version": version_str,
            "used_version": latest_version,
            "deprecated": bool(deprecation_notice)
        })
        
        # Call handler
        response = await handler(request)
        
        # Add version headers to response
        for key, value in headers.items():
            response.headers[key] = value
        
        return response

def setup_versioning(
    app: FastAPI,
    current_version: str = "1.0.0",
    min_version: str = "1.0.0",
    max_version: str = "2.0.0"
) -> VersionManager:
    """
    Set up API versioning
    
    Args:
        app: FastAPI application
        current_version: Current API version
        min_version: Minimum supported version
        max_version: Maximum supported version
        
    Returns:
        Version manager instance
    """
    version_manager = VersionManager(
        current_version=current_version,
        min_version=min_version,
        max_version=max_version
    )
    
    versioned_api = VersionedAPI(app, version_manager)
    
    @app.middleware("http")
    async def version_middleware(request: Request, call_next):
        if request.url.path.startswith('/v'):
            return await versioned_api.handle_request(request)
        return await call_next(request)
    
    return version_manager
