"""
API Response Optimization Module

Provides middleware and utilities for optimizing API response performance:
- Response compression (gzip, brotli)
- Fast JSON serialization with orjson
- Field filtering for large responses
- Pagination for list endpoints
- Response caching with Redis
- ETag support for conditional requests
"""

# Configuration constants
COMPRESSION_MIN_SIZE = 500  # Minimum response size for compression (bytes)
COMPRESSION_LEVEL = 6  # Gzip compression level (1-9)
BROTLI_QUALITY = 4  # Brotli compression quality (0-11)

CACHE_DEFAULT_TTL = 60  # Default cache TTL (seconds)
CACHE_LIST_TTL = 60  # Cache TTL for list endpoints (seconds)
CACHE_ITEM_TTL = 300  # Cache TTL for single-item endpoints (seconds)

SLOW_REQUEST_THRESHOLD_MS = 100  # Threshold for logging slow requests (ms)

__all__ = [
    'COMPRESSION_MIN_SIZE',
    'COMPRESSION_LEVEL',
    'BROTLI_QUALITY',
    'CACHE_DEFAULT_TTL',
    'CACHE_LIST_TTL',
    'CACHE_ITEM_TTL',
    'SLOW_REQUEST_THRESHOLD_MS',
]
