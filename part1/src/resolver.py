"""
Resolver module for location lookup and disambiguation.
"""

from typing import List, Optional, Tuple
from .loader import GeoDataLoader, Location
from .utils import normalize_name, is_empty


class LocationResolver:
    """Resolves location names to Location objects."""
    
    def __init__(self, loader: GeoDataLoader):
        """
        Initialize resolver with a loaded GeoDataLoader.
        
        Args:
            loader: GeoDataLoader instance with parsed data
        """
        self.loader = loader
    
    def resolve(self, city: str, state: Optional[str] = None) -> List[Location]:
        """
        Resolve a city name (and optional state) to possible Location objects.
        
        Args:
            city: City name (will be normalized)
            state: Optional state/district name (will be normalized)
            
        Returns:
            List of matching Location objects. Empty list if no matches.
            Multiple entries indicate ambiguity.
        """
        # Handle empty city
        if is_empty(city):
            return []
        
        city_norm = normalize_name(city)
        
        # If state is provided and not empty
        if not is_empty(state):
            state_norm = normalize_name(state)
            
            # Try (city, state) lookup first
            key = (city_norm, state_norm)
            if key in self.loader.by_city_state:
                location_ids = self.loader.by_city_state[key]
                return [self.loader.locations_by_id[lid] for lid in location_ids]
            
            # Fallback: find cities that have state in their ancestry
            if city_norm in self.loader.by_city:
                location_ids = self.loader.by_city[city_norm]
                matches = []
                for lid in location_ids:
                    loc = self.loader.locations_by_id[lid]
                    # Check if state is in ancestors
                    if state_norm in loc.ancestors_names:
                        matches.append(loc)
                if matches:
                    return matches
        
        # No state or state lookup failed: return all cities with that name
        if city_norm in self.loader.by_city:
            location_ids = self.loader.by_city[city_norm]
            return [self.loader.locations_by_id[lid] for lid in location_ids]
        
        # No matches found
        return []
    
    def is_ambiguous(self, matches: List[Location]) -> bool:
        """
        Check if a location resolution is ambiguous.
        
        Args:
            matches: List of Location matches from resolve()
            
        Returns:
            True if ambiguous (multiple matches), False otherwise
        """
        return len(matches) > 1
    
    def find_common_ancestor_level(self, loc1: Location, loc2: Location) -> int:
        """
        Find the highest admin_level where two locations share a common ancestor.
        
        This handles three cases:
        1. Same location: return its level
        2. One contains the other: return the container's level
        3. Different locations: return highest common ancestor level
        
        Args:
            loc1: First location
            loc2: Second location
            
        Returns:
            Admin level of the highest common ancestor (2 = country if no common ancestor)
        """
        # Case 1: Same location
        if loc1.id == loc2.id:
            return loc1.admin_level
        
        # Case 2: Check if one contains the other
        # loc1 is ancestor of loc2
        if loc1.id in loc2.ancestors:
            return loc1.admin_level
        
        # loc2 is ancestor of loc1
        if loc2.id in loc1.ancestors:
            return loc2.admin_level
        
        # Case 3: Find common ancestors
        common_ancestor_ids = set(loc1.ancestors) & set(loc2.ancestors)
        
        if not common_ancestor_ids:
            # No common ancestors (shouldn't happen in valid data)
            return 2  # Country level
        
        # Find the common ancestor with the highest (deepest) admin_level
        max_level = 2
        for anc_id in common_ancestor_ids:
            anc = self.loader.locations_by_id[anc_id]
            max_level = max(max_level, anc.admin_level)
        
        return max_level
