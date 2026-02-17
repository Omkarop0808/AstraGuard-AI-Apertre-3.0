"""
Field Filter Utility

Filters response fields based on query parameters for optimized payload sizes.
Supports inclusion, exclusion, and dot notation for nested fields.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


class FieldFilter:
    """
    Utility for filtering response fields based on inclusion/exclusion patterns.
    
    Features:
    - Field inclusion (fields parameter)
    - Field exclusion (exclude parameter)
    - Dot notation for nested fields (e.g., "user.email")
    - Works with dicts, lists, and Pydantic models
    - Graceful handling of invalid field names
    
    Usage:
        filtered = FieldFilter.apply_filter(
            data=response_data,
            fields="id,name,user.email",
            exclude="internal_id"
        )
    """
    
    @staticmethod
    def apply_filter(
        data: Any,
        fields: Optional[str] = None,
        exclude: Optional[str] = None
    ) -> Any:
        """
        Apply field filtering to data.
        
        Args:
            data: Data to filter (dict, list, or Pydantic model)
            fields: Comma-separated list of fields to include
            exclude: Comma-separated list of fields to exclude
            
        Returns:
            Filtered data
        """
        # If no filtering requested, return original data
        if not fields and not exclude:
            return data
        
        # Parse field lists
        include_fields = set(f.strip() for f in fields.split(",")) if fields else None
        exclude_fields = set(f.strip() for f in exclude.split(",")) if exclude else set()
        
        # Apply filtering
        return FieldFilter._filter_data(data, include_fields, exclude_fields)
    
    @staticmethod
    def _filter_data(
        data: Any,
        include_fields: Optional[Set[str]],
        exclude_fields: Set[str]
    ) -> Any:
        """
        Recursively filter data structure.
        
        Args:
            data: Data to filter
            include_fields: Fields to include (None = include all)
            exclude_fields: Fields to exclude
            
        Returns:
            Filtered data
        """
        # Handle None
        if data is None:
            return None
        
        # Handle lists - apply filtering to each item
        if isinstance(data, list):
            return [
                FieldFilter._filter_data(item, include_fields, exclude_fields)
                for item in data
            ]
        
        # Handle Pydantic models - convert to dict first
        if hasattr(data, "model_dump"):
            data = data.model_dump()
        elif hasattr(data, "dict"):
            data = data.dict()
        
        # Handle dicts
        if isinstance(data, dict):
            return FieldFilter._filter_dict(data, include_fields, exclude_fields)
        
        # Return primitive types as-is
        return data
    
    @staticmethod
    def _filter_dict(
        data: Dict[str, Any],
        include_fields: Optional[Set[str]],
        exclude_fields: Set[str]
    ) -> Dict[str, Any]:
        """
        Filter dictionary fields.
        
        Args:
            data: Dictionary to filter
            include_fields: Fields to include (None = include all)
            exclude_fields: Fields to exclude
            
        Returns:
            Filtered dictionary
        """
        result = {}
        
        for key, value in data.items():
            # Check if field should be included
            if include_fields is not None:
                # Check for exact match or nested field match
                should_include = False
                nested_includes = set()
                
                for field in include_fields:
                    if field == key:
                        should_include = True
                    elif field.startswith(f"{key}."):
                        # Nested field like "user.email"
                        should_include = True
                        nested_field = field[len(key) + 1:]
                        nested_includes.add(nested_field)
                
                if not should_include:
                    continue
                
                # If we have nested includes, filter the nested object
                if nested_includes:
                    result[key] = FieldFilter._filter_data(
                        value,
                        nested_includes,
                        exclude_fields
                    )
                    continue
            
            # Check if field should be excluded
            if key in exclude_fields:
                continue
            
            # Check for nested exclusions
            nested_excludes = set()
            for field in exclude_fields:
                if field.startswith(f"{key}."):
                    nested_field = field[len(key) + 1:]
                    nested_excludes.add(nested_field)
            
            # Recursively filter nested objects
            if nested_excludes and isinstance(value, (dict, list)):
                result[key] = FieldFilter._filter_data(
                    value,
                    None,
                    nested_excludes
                )
            else:
                result[key] = value
        
        return result
