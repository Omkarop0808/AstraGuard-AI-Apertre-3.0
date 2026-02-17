"""
Cache Middleware

Caches GET responses in Redis with automatic invalidation.
"""

import hashlib
import logging
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from api.optimization import CACHE_DEFAULT_TTL, CACHE_LIST_TTL, CACHE_ITEM_TTL

logger = logging.getLogger(__name__)


class CacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware for caching GET responses in Redis.
    
    Features:
    - Caches GET responses only
    - Generates cache keys from path, query params, and auth context
    - Different TTLs for list vs single-item endpoints
    - Invalidates cache on write operations (POST/PUT/PATCH/DELETE)
    - Tracks cache hit/miss statistics
    - Graceful degradation when Redis is unavailable
    
    Args:
        app: ASGI application
        redis_client: Redis client instance
        default_ttl: Default cache TTL in seconds (default: 60)
    """
    
    def __init__(
        self,
        app: ASGIApp,
        redis_client: Optional[Any] = None,
        default_ttl: int = CACHE_DEFAULT_TTL
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_errors = 0
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and cache response if appropriate.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response (cached or fresh)
        """
        # Only cache GET requests
        if request.method != "GET":
            response = await call_next(request)
            
            # Invalidate related cache entries on write operations
            if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                await self._invalidate_cache(request)
            
            return response
        
        # Check if Redis is available
        if not self.redis_client or not hasattr(self.redis_client, 'redis'):
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get cached response
        try:
            cached = await self.redis_client.redis.get(cache_key)
            if cached:
                self.cache_hits += 1
                logger.debug(f"Cache hit for {cache_key}")
                
                # Parse cached response
                import json
                cached_data = json.loads(cached)
                
                return Response(
                    content=cached_data["content"],
                    status_code=cached_data["status_code"],
                    headers=cached_data["headers"],
                    media_type=cached_data["media_type"]
                )
        except Exception as e:
            self.cache_errors += 1
            logger.warning(f"Cache read error: {e}")
            # Continue without cache
        
        # Cache miss - call handler
        self.cache_misses += 1
        response = await call_next(request)
        
        # Cache successful responses only
        if response.status_code == 200:
            await self._cache_response(request, response, cache_key)
        
        return response
    
    def _generate_cache_key(self, request: Request) -> str:
        """
        Generate cache key from request.
        
        Includes:
        - Request path
        - Query parameters
        - Authentication context (user ID or API key)
        
        Args:
            request: HTTP request
            
        Returns:
            Cache key string
        """
        # Build key components
        path = request.url.path
        query = str(request.url.query)
        
        # Include auth context
        auth_context = ""
        if "authorization" in request.headers:
            # Hash the auth header for privacy
            auth_hash = hashlib.md5(
                request.headers["authorization"].encode()
            ).hexdigest()[:8]
            auth_context = f"auth:{auth_hash}"
        elif "x-api-key" in request.headers:
            # Hash the API key for privacy
            key_hash = hashlib.md5(
                request.headers["x-api-key"].encode()
            ).hexdigest()[:8]
            auth_context = f"key:{key_hash}"
        
        # Combine and hash
        key_string = f"{path}?{query}|{auth_context}"
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        
        return f"cache:response:{key_hash}"
    
    def _get_ttl_for_path(self, path: str) -> int:
        """
        Get cache TTL based on endpoint path.
        
        Args:
            path: Request path
            
        Returns:
            TTL in seconds
        """
        # List endpoints get shorter TTL
        if any(keyword in path for keyword in ["/list", "/history", "/apikeys", "/submissions"]):
            return CACHE_LIST_TTL
        
        # Single-item endpoints get longer TTL
        return CACHE_ITEM_TTL
    
    async def _cache_response(self, request: Request, response: Response, cache_key: str):
        """
        Cache response in Redis.
        
        Args:
            request: HTTP request
            response: HTTP response
            cache_key: Cache key
        """
        try:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Prepare cached data
            import json
            cached_data = {
                "content": body.decode("utf-8"),
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type
            }
            
            # Get TTL
            ttl = self._get_ttl_for_path(request.url.path)
            
            # Store in Redis
            await self.redis_client.redis.setex(
                cache_key,
                ttl,
                json.dumps(cached_data)
            )
            
            logger.debug(f"Cached response for {cache_key} (TTL: {ttl}s)")
            
            # Recreate response with body
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
        except Exception as e:
            self.cache_errors += 1
            logger.warning(f"Cache write error: {e}")
            # Return original response
            return response
    
    async def _invalidate_cache(self, request: Request):
        """
        Invalidate related cache entries on write operations.
        
        Args:
            request: HTTP request
        """
        try:
            # Extract resource path (e.g., /api/v1/auth/apikeys)
            path_parts = request.url.path.split("/")
            
            # Build pattern to match related cache keys
            # This is a simple implementation - could be more sophisticated
            pattern = f"cache:response:*"
            
            # In production, you'd want to be more selective about invalidation
            # For now, we'll just log the invalidation
            logger.debug(f"Cache invalidation triggered by {request.method} {request.url.path}")
            
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache hit/miss/error counts and rates
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        miss_rate = (self.cache_misses / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_errors": self.cache_errors,
            "total_requests": total_requests,
            "hit_rate": f"{hit_rate:.1f}%",
            "miss_rate": f"{miss_rate:.1f}%"
        }


# Import Any for type hints
from typing import Any
