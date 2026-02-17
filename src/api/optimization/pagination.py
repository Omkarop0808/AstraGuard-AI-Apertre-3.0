"""
Pagination Handler

Implements consistent pagination across list endpoints with metadata.
"""

import logging
from typing import Any, Dict, Generic, List, TypeVar

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    Query parameters for pagination.
    
    Attributes:
        limit: Maximum number of items to return (default: 100, max: 1000)
        offset: Number of items to skip (default: 0)
    """
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response with metadata.
    
    Attributes:
        items: List of items for current page
        total_count: Total number of items available
        limit: Maximum items per page
        offset: Number of items skipped
        has_more: Whether more items are available
    """
    items: List[T]
    total_count: int
    limit: int
    offset: int
    has_more: bool


class PaginationHandler:
    """
    Utility for applying pagination to lists with metadata.
    
    Features:
    - Consistent pagination across endpoints
    - Automatic metadata calculation
    - Limit clamping (max 1000)
    - Default values (limit=100, offset=0)
    
    Usage:
        result = PaginationHandler.paginate(
            items=all_items,
            limit=50,
            offset=0
        )
    """
    
    @staticmethod
    def paginate(
        items: List[Any],
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Apply pagination to a list of items.
        
        Args:
            items: Complete list of items
            limit: Maximum items to return (default: 100, max: 1000)
            offset: Number of items to skip (default: 0)
            
        Returns:
            Dictionary with paginated items and metadata
        """
        # Validate and clamp parameters
        limit = max(1, min(limit, 1000))
        offset = max(0, offset)
        
        # Calculate pagination
        total_count = len(items)
        start_idx = offset
        end_idx = offset + limit
        
        # Get page items
        page_items = items[start_idx:end_idx]
        
        # Calculate has_more
        has_more = end_idx < total_count
        
        return {
            "items": page_items,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": has_more
        }
