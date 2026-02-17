"""
ORJson Response Class

Fast JSON serialization using orjson library for improved API performance.
Provides 2-3x faster serialization compared to standard json library.
"""

import logging
from typing import Any
from datetime import datetime
from enum import Enum

from fastapi.responses import JSONResponse
import orjson

logger = logging.getLogger(__name__)


def _default_serializer(obj: Any) -> Any:
    """
    Default serializer for objects that orjson cannot serialize natively.
    
    Handles:
    - datetime objects -> ISO 8601 strings
    - Enum objects -> string values
    - Other objects -> str() representation
    
    Args:
        obj: Object to serialize
        
    Returns:
        Serializable representation of the object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Enum):
        return obj.value
    else:
        return str(obj)


class ORJSONResponse(JSONResponse):
    """
    FastAPI response class using orjson for fast JSON serialization.
    
    Features:
    - 2-3x faster serialization than standard json
    - Automatic datetime serialization to ISO 8601
    - Automatic Enum serialization to string values
    - Fallback to standard JSON on serialization errors
    - Compatible with Pydantic models
    
    Usage:
        app = FastAPI(default_response_class=ORJSONResponse)
    """
    
    media_type = "application/json"
    
    def render(self, content: Any) -> bytes:
        """
        Render content to JSON bytes using orjson.
        
        Args:
            content: Content to serialize (dict, list, Pydantic model, etc.)
            
        Returns:
            JSON bytes
            
        Raises:
            TypeError: If content cannot be serialized (falls back to standard JSON)
        """
        try:
            # orjson.dumps returns bytes directly
            # OPT_SERIALIZE_NUMPY: Support numpy arrays
            # OPT_NON_STR_KEYS: Allow non-string dict keys
            # OPT_PASSTHROUGH_DATETIME: Let default handler process datetimes
            return orjson.dumps(
                content,
                default=_default_serializer,
                option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
            )
        except (TypeError, ValueError) as e:
            # Fallback to standard JSON serialization
            logger.warning(
                f"ORJson serialization failed, falling back to standard JSON: {e}",
                extra={
                    "error_type": type(e).__name__,
                    "content_type": type(content).__name__
                }
            )
            
            # Use standard JSONResponse render method as fallback
            import json
            return json.dumps(
                content,
                default=str,
                ensure_ascii=False,
                allow_nan=False,
                indent=None,
                separators=(",", ":")
            ).encode("utf-8")
