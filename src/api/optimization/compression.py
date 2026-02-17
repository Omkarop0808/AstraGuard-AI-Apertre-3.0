"""
Compression Middleware

Transparently compresses HTTP responses based on client Accept-Encoding header.
Supports gzip and brotli compression with configurable thresholds.
"""

import gzip
import logging
from typing import Optional

try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from api.optimization import COMPRESSION_MIN_SIZE, COMPRESSION_LEVEL, BROTLI_QUALITY

logger = logging.getLogger(__name__)


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for compressing HTTP responses.
    
    Features:
    - Supports gzip and brotli compression
    - Skips compression for small responses (<500 bytes)
    - Skips compression for non-200 status codes
    - Adds Content-Encoding header
    - Adds X-Compression-Ratio header for monitoring
    - Configurable compression levels
    
    Args:
        app: ASGI application
        minimum_size: Minimum response size for compression (default: 500 bytes)
        compression_level: Gzip compression level 1-9 (default: 6)
        brotli_quality: Brotli compression quality 0-11 (default: 4)
    """
    
    def __init__(
        self,
        app: ASGIApp,
        minimum_size: int = COMPRESSION_MIN_SIZE,
        compression_level: int = COMPRESSION_LEVEL,
        brotli_quality: int = BROTLI_QUALITY
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level
        self.brotli_quality = brotli_quality
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and compress response if appropriate.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response (compressed or uncompressed)
        """
        # Get Accept-Encoding header
        accept_encoding = request.headers.get("accept-encoding", "").lower()
        
        # Call next middleware/handler
        response = await call_next(request)
        
        # Check if compression should be applied
        if not self._should_compress(response, accept_encoding):
            return response
        
        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Check minimum size
        if len(body) < self.minimum_size:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        
        # Determine compression method (prefer brotli if available)
        compressed_body: Optional[bytes] = None
        encoding: Optional[str] = None
        
        if "br" in accept_encoding and BROTLI_AVAILABLE:
            compressed_body = self._compress_brotli(body)
            encoding = "br"
        elif "gzip" in accept_encoding:
            compressed_body = self._compress_gzip(body)
            encoding = "gzip"
        
        # If compression failed or not supported, return original
        if compressed_body is None or encoding is None:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        
        # Calculate compression ratio
        original_size = len(body)
        compressed_size = len(compressed_body)
        compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        
        # Build response headers
        headers = dict(response.headers)
        headers["Content-Encoding"] = encoding
        headers["Content-Length"] = str(compressed_size)
        headers["X-Compression-Ratio"] = f"{compression_ratio:.1f}%"
        
        # Remove any existing Content-Length that might be incorrect
        headers.pop("content-length", None)
        
        logger.debug(
            f"Compressed response: {original_size} -> {compressed_size} bytes "
            f"({compression_ratio:.1f}% reduction) using {encoding}"
        )
        
        return Response(
            content=compressed_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type
        )
    
    def _should_compress(self, response: Response, accept_encoding: str) -> bool:
        """
        Determine if response should be compressed.
        
        Args:
            response: HTTP response
            accept_encoding: Accept-Encoding header value
            
        Returns:
            True if compression should be applied
        """
        # Only compress successful responses
        if response.status_code != 200:
            return False
        
        # Check if client accepts compression
        if not accept_encoding or ("gzip" not in accept_encoding and "br" not in accept_encoding):
            return False
        
        # Check if already compressed
        if response.headers.get("content-encoding"):
            return False
        
        # Check content type (only compress text-based content)
        content_type = response.headers.get("content-type", "")
        if content_type and not any(
            ct in content_type.lower()
            for ct in ["json", "text", "xml", "javascript", "html"]
        ):
            return False
        
        return True
    
    def _compress_gzip(self, data: bytes) -> Optional[bytes]:
        """
        Compress data using gzip.
        
        Args:
            data: Data to compress
            
        Returns:
            Compressed data or None on error
        """
        try:
            return gzip.compress(data, compresslevel=self.compression_level)
        except Exception as e:
            logger.warning(f"Gzip compression failed: {e}")
            return None
    
    def _compress_brotli(self, data: bytes) -> Optional[bytes]:
        """
        Compress data using brotli.
        
        Args:
            data: Data to compress
            
        Returns:
            Compressed data or None on error
        """
        if not BROTLI_AVAILABLE:
            return None
        
        try:
            return brotli.compress(data, quality=self.brotli_quality)
        except Exception as e:
            logger.warning(f"Brotli compression failed: {e}")
            return None
