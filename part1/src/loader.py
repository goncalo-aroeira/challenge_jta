"""
Loader module to parse portugal.json and build lookup structures.
"""

import json
from typing import Dict, List, Tuple, Optional
from .utils import normalize_name


class Location:
    """Represents a geographic location with its hierarchy."""
    
    def __init__(self, id: int, name: str, admin_level: int, parent_id: Optional[int] = None):
        self.id = id
        self.name = name  # Normalized name
        self.original_name = name  # Keep original for reference
        self.admin_level = admin_level
        self.parent_id = parent_id
        self.ancestors = []  # List of ancestor IDs (including self)
        self.ancestors_names = []  # List of ancestor names
        self.ancestors_levels = []  # List of ancestor levels
    
    def __repr__(self):
        return f"Location(id={self.id}, name='{self.name}', level={self.admin_level})"


class GeoDataLoader:
    """Loads and indexes geographic data from JSON."""
    
    def __init__(self, json_path: str):
        """
        Initialize loader and parse JSON file.
        
        Args:
            json_path: Path to portugal.json file
        """
        self.json_path = json_path
        self.locations: List[Location] = []
        self.locations_by_id: Dict[int, Location] = {}
        self.by_city: Dict[str, List[int]] = {}  # normalized_name -> [location_ids]
        self.by_city_state: Dict[Tuple[str, str], List[int]] = {}  # (city, state) -> [location_ids]
        
        self._load_and_index()
    
    def _load_and_index(self):
        """Load JSON and build all indexes."""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        
        # Parse the tree structure - start with "portugal" as the root
        self._parse_tree(data, parent_id=None, parent_name=None, node_name="portugal")
        
        # Build ancestor chains
        self._build_ancestors()
        
        # Build indexes
        self._build_indexes()
    
    def _parse_tree(self, node: dict, parent_id: Optional[int], parent_name: Optional[str], node_name: Optional[str] = None):
        """
        Recursively parse the JSON tree structure.
        
        Args:
            node: Current node in the tree
            parent_id: ID of the parent location
            parent_name: Name of the parent location (for state context)
            node_name: Name of this node (used when name is a dict key)
        """
        # Determine the name - either from parameter, "name" field, or default
        name = node_name or node.get("name", "")
        admin_level = node.get("admin_level")
        
        # Skip if no admin_level (invalid node)
        if admin_level is None:
            return
        
        # Create location
        loc_id = len(self.locations)
        normalized_name = normalize_name(name)
        loc = Location(id=loc_id, name=normalized_name, admin_level=admin_level, parent_id=parent_id)
        loc.original_name = name
        
        self.locations.append(loc)
        self.locations_by_id[loc_id] = loc
        
        # Process children
        if "children" in node and node["children"]:
            for child_name, child_node in node["children"].items():
                # Recursively process child with its name
                self._parse_tree(child_node, parent_id=loc_id, parent_name=normalized_name, node_name=child_name)
    
    def _build_ancestors(self):
        """Build ancestor chains for all locations."""
        for loc in self.locations:
            # Build ancestor chain from this location up to root
            ancestors = []
            ancestors_names = []
            ancestors_levels = []
            
            current = loc
            while current is not None:
                ancestors.append(current.id)
                ancestors_names.append(current.name)
                ancestors_levels.append(current.admin_level)
                
                # Move to parent
                if current.parent_id is not None:
                    current = self.locations_by_id[current.parent_id]
                else:
                    current = None
            
            loc.ancestors = ancestors
            loc.ancestors_names = ancestors_names
            loc.ancestors_levels = ancestors_levels
    
    def _build_indexes(self):
        """Build lookup indexes."""
        # Index by city name
        for loc in self.locations:
            if loc.name not in self.by_city:
                self.by_city[loc.name] = []
            self.by_city[loc.name].append(loc.id)
        
        # Index by (city, ancestor) for ALL ancestors
        # This allows state to be any level (district, concelho, etc)
        for loc in self.locations:
            # Create index entries for ALL ancestors
            for ancestor_id in loc.ancestors:
                if ancestor_id == loc.id:
                    continue  # Skip self
                
                ancestor = self.locations_by_id[ancestor_id]
                key = (loc.name, ancestor.name)
                if key not in self.by_city_state:
                    self.by_city_state[key] = []
                if loc.id not in self.by_city_state[key]:
                    self.by_city_state[key].append(loc.id)
    
    def _find_state(self, loc: Location) -> Optional[str]:
        """
        Find the primary state/district for a location.
        
        Returns the first ancestor with admin_level in [4, 6, 7]:
        - Level 4: Autonomous regions (Açores, Madeira)
        - Level 6: Districts
        - Level 7: Concelhos (if no district found)
        
        Note: This is used for backwards compatibility. The main lookup
        system now supports ANY ancestor as state via by_city_state index.
        
        Args:
            loc: Location to find state for
            
        Returns:
            State name or None
        """
        # First try to find district or autonomous region (levels 4, 6)
        for ancestor_id in loc.ancestors:
            ancestor = self.locations_by_id[ancestor_id]
            if ancestor.admin_level in [4, 6]:
                return ancestor.name
        
        # Fallback: try concelho (level 7)
        for ancestor_id in loc.ancestors:
            ancestor = self.locations_by_id[ancestor_id]
            if ancestor.admin_level == 7:
                return ancestor.name
        
        return None
    
    def get_stats(self) -> dict:
        """Get statistics about the loaded data."""
        return {
            "total_locations": len(self.locations),
            "unique_cities": len(self.by_city),
            "unique_city_state_pairs": len(self.by_city_state),
            "levels": {level: sum(1 for loc in self.locations if loc.admin_level == level) 
                      for level in set(loc.admin_level for loc in self.locations)}
        }
