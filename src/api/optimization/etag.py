"""
ETag Middleware

Generates ETags from response content and handles conditional requests.
"""

import hashlib
import logging
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class ETagMiddleware(BaseHTTPMiddleware):
    """
    Middleware for generating ETags and handling conditional requests.
    
    Features:
    - Generates ETags from SHA-256 hash of response content
    - Returns 304 Not Modified for matching If-None-Match headers
    - Includes user authentication context in ETag calculation
    - Graceful error handling
    
    Args:
        app: ASGI application
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.etag_validations = 0
        self.etag_matches = 0
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and add ETag support.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response with ETag header or 304 Not Modified
        """
        # Only process GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Get If-None-Match header
        if_none_match = request.headers.get("if-none-match")
        
        # Call next middleware/handler
        response = await call_next(request)
        
        # Only process successful responses
        if response.status_code != 200:
            return response
        
        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Generate ETag
        etag = self._generate_etag(body, request)
        
        if etag is None:
            # ETag generation failed, return response without ETag
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        
        # Check if ETag matches
        if if_none_match:
            self.etag_validations += 1
            if if_none_match == etag or if_none_match == f'"{etag}"':
                self.etag_matches += 1
                logger.debug(f"ETag match: {etag}")
                
                # Return 304 Not Modified
                headers = dict(response.headers)
                headers["ETag"] = f'"{etag}"'
                
                return Response(
                    content=b"",
                    status_code=304,
                    headers=headers
                )
        
        # Add ETag header to response
        headers = dict(response.headers)
        headers["ETag"] = f'"{etag}"'
        
        return Response(
            content=body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type
        )
    
    def _generate_etag(self, content: bytes, request: Request) -> Optional[str]:
        """
        Generate ETag from response content.
        
        Includes:
        - Response content hash
        - Authentication context (for user-specific responses)
        
        Args:
            content: Response body
            request: HTTP request
            
        Returns:
            ETag string or None on error
        """
        try:
            # Start with content hash
            hasher = hashlib.sha256()
            hasher.update(content)
            
            # Include auth context for user-specific responses
            if "authorization" in request.headers:
                hasher.update(request.headers["authorization"].encode())
            elif "x-api-key" in request.headers:
                hasher.update(request.headers["x-api-key"].encode())
            
            # Generate ETag
            etag = hasher.hexdigest()[:16]  # Use first 16 chars for brevity
            
            return etag
            
        except Exception as e:
            logger.warning(f"ETag generation failed: {e}")
            return None
    
    def get_etag_stats(self) -> dict:
        """
        Get ETag statistics.
        
        Returns:
            Dictionary with ETag validation counts and rates
        """
        validation_rate = (
            (self.etag_matches / self.etag_validations * 100)
            if self.etag_validations > 0
            else 0
        )
        
        return {
            "etag_validations": self.etag_validations,
            "etag_matches": self.etag_matches,
            "validation_rate": f"{validation_rate:.1f}%"
        }
