"""
Processor module to process DataFrames and add expected_level and is_ambiguous columns.
"""

import pandas as pd
from .loader import GeoDataLoader
from .resolver import LocationResolver


class GeoProcessor:
    """Processes DataFrames to add geographic matching information."""
    
    def __init__(self, json_path: str):
        """
        Initialize processor by loading geographic data.
        
        Args:
            json_path: Path to portugal.json file
        """
        self.loader = GeoDataLoader(json_path)
        self.resolver = LocationResolver(self.loader)
    
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process a DataFrame to add expected_level and is_ambiguous columns.
        
        Expected input columns:
        - id_1, id_2: Identifiers
        - city_1, city_2: City names
        - state_1, state_2: State/district names (can be empty/None)
        
        Adds columns:
        - expected_level: Highest admin_level where the two locations match
        - is_ambiguous: 1 if at least one location is ambiguous, 0 otherwise
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with added columns
        """
        # Create a copy to avoid modifying original
        result = df.copy()
        
        # Process each row
        expected_levels = []
        is_ambiguous_flags = []
        
        for _, row in result.iterrows():
            expected_level, is_ambiguous = self._process_row(row)
            expected_levels.append(expected_level)
            is_ambiguous_flags.append(is_ambiguous)
        
        result['expected_level'] = expected_levels
        result['is_ambiguous'] = is_ambiguous_flags
        
        return result
    
    def _process_row(self, row: pd.Series) -> tuple:
        """
        Process a single row to determine expected_level and is_ambiguous.
        
        Args:
            row: DataFrame row with city_1, city_2, state_1, state_2
            
        Returns:
            Tuple of (expected_level, is_ambiguous)
        """
        # Extract values
        city_1 = row.get('city_1')
        city_2 = row.get('city_2')
        state_1 = row.get('state_1')
        state_2 = row.get('state_2')
        
        # Resolve locations
        matches_1 = self.resolver.resolve(city_1, state_1)
        matches_2 = self.resolver.resolve(city_2, state_2)
        
        # Determine ambiguity
        is_ambiguous = self._is_ambiguous(matches_1, matches_2)
        
        # Calculate expected_level (best case scenario)
        expected_level = self._calculate_expected_level(matches_1, matches_2)
        
        return expected_level, is_ambiguous
    
    def _is_ambiguous(self, matches_1: list, matches_2: list) -> int:
        """
        Determine if the resolution is ambiguous.
        
        Args:
            matches_1: List of Location matches for city_1
            matches_2: List of Location matches for city_2
            
        Returns:
            1 if ambiguous, 0 otherwise
        """
        # Ambiguous if either location has multiple matches
        return int(len(matches_1) > 1 or len(matches_2) > 1)
    
    def _calculate_expected_level(self, matches_1: list, matches_2: list) -> int:
        """
        Calculate the expected admin level (best case scenario).
        
        Args:
            matches_1: List of Location matches for city_1
            matches_2: List of Location matches for city_2
            
        Returns:
            Expected admin level (2 = country if no matches)
        """
        # If either location has no matches, return country level
        if not matches_1 or not matches_2:
            return 2
        
        # Best case: use first match from each list
        loc_1 = matches_1[0]
        loc_2 = matches_2[0]
        
        # Find common ancestor level
        return self.resolver.find_common_ancestor_level(loc_1, loc_2)
    
    def get_stats(self) -> dict:
        """Get statistics about the loaded geographic data."""
        return self.loader.get_stats()
