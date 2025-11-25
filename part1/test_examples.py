#!/usr/bin/env python3
"""
Test script to verify the implementation with examples from the problem statement.
"""

import pandas as pd
import sys
import os

# Add part1 directory to path to enable imports
part1_dir = os.path.dirname(os.path.abspath(__file__))
if part1_dir not in sys.path:
    sys.path.insert(0, part1_dir)

from src.processor import GeoProcessor


def test_examples():
    """Test with the examples from the problem statement."""
    
    # Initialize processor
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'portugal.json')
    processor = GeoProcessor(json_path)
    
    # Define test cases from the problem statement table
    test_cases = [
        {
            'name': 'Row 1: Different states (valadares viseu vs valadares porto)',
            'city_1': 'valadares',
            'state_1': 'viseu',
            'city_2': 'valadares',
            'state_2': 'porto',
            'expected_level': 2,
            'is_ambiguous': 0
        },
        {
            'name': 'Row 2: Missing state_2 (valadares viseu vs valadares ?)',
            'city_1': 'valadares',
            'state_1': 'viseu',
            'city_2': 'valadares',
            'state_2': None,
            'expected_level': 8,
            'is_ambiguous': 1
        },
        {
            'name': 'Row 3: Both missing states (valadares ? vs valadares ?)',
            'city_1': 'valadares',
            'state_1': None,
            'city_2': 'valadares',
            'state_2': None,
            'expected_level': 8,
            'is_ambiguous': 1
        },
        {
            'name': 'Row 4: Non-existent city',
            'city_1': 'lugar que nao existe',
            'state_1': None,
            'city_2': 'valadares',
            'state_2': 'viseu',
            'expected_level': 2,
            'is_ambiguous': 0
        },
        {
            'name': 'Row 5: Hierarchy - valadares in sao pedro do sul',
            'city_1': 'valadares',
            'state_1': 'viseu',
            'city_2': 'sao pedro do sul',
            'state_2': 'viseu',
            'expected_level': 7,
            'is_ambiguous': 0
        },
        {
            'name': 'Row 6: Unique state inference (sao pedro do sul without state)',
            'city_1': 'valadares',
            'state_1': 'viseu',
            'city_2': 'sao pedro do sul',
            'state_2': None,
            'expected_level': 7,
            'is_ambiguous': 0
        },
        {
            'name': 'Row 7: Ambiguous city_1 (valadares ? vs sao pedro do sul viseu)',
            'city_1': 'valadares',
            'state_1': None,
            'city_2': 'sao pedro do sul',
            'state_2': 'viseu',
            'expected_level': 7,
            'is_ambiguous': 1
        }
    ]
    
    # Create DataFrame
    df = pd.DataFrame([
        {
            'id_1': i + 1,
            'id_2': i + 2,
            'city_1': tc['city_1'],
            'city_2': tc['city_2'],
            'state_1': tc['state_1'],
            'state_2': tc['state_2']
        }
        for i, tc in enumerate(test_cases)
    ])
    
    # Process
    result = processor.process(df)
    
    # Verify each test case
    print("=" * 100)
    print("Testing Part 1 - Geographic Location Matching")
    print("=" * 100)
    print()
    
    all_passed = True
    for i, tc in enumerate(test_cases):
        actual_level = result.iloc[i]['expected_level']
        actual_ambiguous = result.iloc[i]['is_ambiguous']
        expected_level = tc['expected_level']
        expected_ambiguous = tc['is_ambiguous']
        
        level_match = actual_level == expected_level
        ambiguous_match = actual_ambiguous == expected_ambiguous
        passed = level_match and ambiguous_match
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {tc['name']}")
        print(f"  Input:  city_1='{tc['city_1']}' state_1='{tc['state_1']}' | "
              f"city_2='{tc['city_2']}' state_2='{tc['state_2']}'")
        print(f"  Expected: expected_level={expected_level}, is_ambiguous={expected_ambiguous}")
        print(f"  Actual:   expected_level={actual_level}, is_ambiguous={actual_ambiguous}")
        
        if not passed:
            all_passed = False
            if not level_match:
                print(f"  ❌ expected_level mismatch: expected {expected_level}, got {actual_level}")
            if not ambiguous_match:
                print(f"  ❌ is_ambiguous mismatch: expected {expected_ambiguous}, got {actual_ambiguous}")
        
        print()
    
    print("=" * 100)
    if all_passed:
        print("🎉 All tests passed!")
        print("=" * 100)
        return 0
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        print("=" * 100)
        return 1


if __name__ == '__main__':
    sys.exit(test_examples())
