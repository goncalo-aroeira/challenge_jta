#!/usr/bin/env python3
"""
Main script to demonstrate the geographic matching solution.
"""

import pandas as pd
import sys
import os

# Add part1 directory to path to enable imports
part1_dir = os.path.dirname(os.path.abspath(__file__))
if part1_dir not in sys.path:
    sys.path.insert(0, part1_dir)

from src.processor import GeoProcessor


def main():
    """Run the geographic matching example."""
    
    print("=" * 80)
    print("Part 1 - Geographic Location Matching")
    print("=" * 80)
    print()
    
    # Initialize processor
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'portugal.json')
    print(f"Loading geographic data from: {json_path}")
    processor = GeoProcessor(json_path)
    
    # Display stats
    stats = processor.get_stats()
    print(f"\nLoaded {stats['total_locations']} locations")
    print(f"Unique cities: {stats['unique_cities']}")
    print(f"Admin levels: {stats['levels']}")
    print()
    
    # Create example DataFrame matching the problem statement
    print("Creating example DataFrame with test cases...")
    df = pd.DataFrame({
        'id_1': [1, 1, 3, 4, 7, 1, 8, 1, 8, 10],
        'id_2': [2, 3, 4, 5, 1, 8, 1, 8, 1, 9],
        'city_1': [
            'valadares',          # Row 1
            'valadares',          # Row 2
            'valadares',          # Row 3
            'valadares',          # Row 4
            'lugar que nao existe',  # Row 5
            'valadares',          # Row 6
            'valadares',          # Row 7 (duplicate)
            'valadares',          # Row 8
            'valadares',          # Row 9 (duplicate)
            'valadares'           # Row 10
        ],
        'city_2': [
            'valadares',          # Row 1: different states
            'valadares',          # Row 2: one missing state
            'valadares',          # Row 3: both missing states
            'valadares',          # Row 4: both missing states (duplicate)
            'valadares',          # Row 5: non-existent city
            'sao pedro do sul',   # Row 6: hierarchy
            'sao pedro do sul',   # Row 7: hierarchy (duplicate)
            'sao pedro do sul',   # Row 8: hierarchy
            'sao pedro do sul',   # Row 9: hierarchy (duplicate)
            'sao pedro do sul'    # Row 10: ambiguous city_1
        ],
        'state_1': [
            'viseu',              # Row 1
            'viseu',              # Row 2
            None,                 # Row 3
            None,                 # Row 4
            'viseu',              # Row 5
            'viseu',              # Row 6
            'viseu',              # Row 7
            'viseu',              # Row 8
            'viseu',              # Row 9
            None                  # Row 10
        ],
        'state_2': [
            'porto',              # Row 1
            None,                 # Row 2
            None,                 # Row 3
            None,                 # Row 4
            'viseu',              # Row 5
            'viseu',              # Row 6
            'viseu',              # Row 7
            None,                 # Row 8: missing but unique
            None,                 # Row 9: missing but unique
            'viseu'               # Row 10
        ]
    })
    
    print("\nInput DataFrame:")
    print(df.to_string(index=False))
    print()
    
    # Process DataFrame
    print("Processing...")
    result = processor.process(df)
    
    print("\nResult with expected_level and is_ambiguous:")
    print(result.to_string(index=False))
    print()
    
    # Show expected results from problem statement
    print("=" * 80)
    print("Expected results from problem statement (first 7 unique rows):")
    print("=" * 80)
    expected = pd.DataFrame({
        'Row': [1, 2, 3, 4, 5, 6, 7],
        'Case': [
            'Different states',
            'Missing state_2',
            'Both missing states',
            'Both missing states (dup)',
            'Non-existent city',
            'Hierarchy (contained)',
            'Ambiguous city_1'
        ],
        'expected_level': [2, 8, 8, 8, 2, 7, 7],
        'is_ambiguous': [0, 1, 1, 1, 0, 0, 1]
    })
    print(expected.to_string(index=False))
    print()
    
    # Verify correctness
    print("=" * 80)
    print("Verification:")
    print("=" * 80)
    
    # Remove duplicates for comparison (rows 6-9 are duplicates of earlier rows)
    unique_rows = [0, 1, 2, 4, 5, 7, 9]  # Rows 1, 2, 3, 5, 6, 8, 10
    expected_levels = [2, 8, 8, 2, 7, 7, 7]
    expected_ambiguous = [0, 1, 1, 0, 0, 0, 1]  # Row 8 should be 0 (sao pedro unique)
    
    all_correct = True
    for i, row_idx in enumerate(unique_rows):
        actual_level = result.iloc[row_idx]['expected_level']
        actual_ambiguous = result.iloc[row_idx]['is_ambiguous']
        exp_level = expected_levels[i]
        exp_ambiguous = expected_ambiguous[i]
        
        level_ok = actual_level == exp_level
        ambiguous_ok = actual_ambiguous == exp_ambiguous
        
        if not (level_ok and ambiguous_ok):
            all_correct = False
            print(f"❌ Row {row_idx + 1}: expected_level={exp_level} (got {actual_level}), "
                  f"is_ambiguous={exp_ambiguous} (got {actual_ambiguous})")
        else:
            print(f"✅ Row {row_idx + 1}: Correct")
    
    print()
    if all_correct:
        print("🎉 All test cases passed!")
    else:
        print("⚠️  Some test cases failed. Please review the implementation.")
    
    return 0 if all_correct else 1


if __name__ == '__main__':
    sys.exit(main())
