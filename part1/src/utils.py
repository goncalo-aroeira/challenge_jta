"""
Utility functions for geographic location processing.
"""

import unicodedata


def normalize_name(name: str) -> str:
    """
    Normalize location name for matching.
    
    - Converts to lowercase
    - Removes accents/diacritics
    - Strips whitespace
    
    Args:
        name: Original location name
        
    Returns:
        Normalized name
        
    Examples:
        >>> normalize_name("São Pedro")
        'sao pedro'
        >>> normalize_name("  VALADARES  ")
        'valadares'
    """
    if not name or not isinstance(name, str):
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove accents using Unicode normalization
    # NFD = Canonical Decomposition
    name = unicodedata.normalize('NFD', name)
    # Filter out combining characters (accents)
    name = ''.join(char for char in name if unicodedata.category(char) != 'Mn')
    
    # Strip whitespace
    name = name.strip()
    
    return name


def is_empty(value) -> bool:
    """
    Check if a value is empty (None, NaN, empty string, or whitespace).
    
    Args:
        value: Value to check
        
    Returns:
        True if empty, False otherwise
    """
    if value is None:
        return True
    
    if isinstance(value, float):
        import math
        return math.isnan(value)
    
    if isinstance(value, str):
        return len(value.strip()) == 0
    
    return False
