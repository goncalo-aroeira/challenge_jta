"""
Part 1 - Geographic Location Matching

This module provides tools to match geographic locations and determine
their hierarchical relationship in the Portuguese administrative structure.
"""

from .loader import GeoDataLoader, Location
from .resolver import LocationResolver
from .processor import GeoProcessor
from .utils import normalize_name, is_empty

__all__ = [
    'GeoDataLoader',
    'Location',
    'LocationResolver',
    'GeoProcessor',
    'normalize_name',
    'is_empty'
]
