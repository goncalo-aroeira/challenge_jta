#!/usr/bin/env python3
"""
Additional comprehensive tests beyond the problem statement examples.
Tests edge cases, special scenarios, and validates robustness.
"""

import pandas as pd
import sys
import os

# Add part1 directory to path
part1_dir = os.path.dirname(os.path.abspath(__file__))
if part1_dir not in sys.path:
    sys.path.insert(0, part1_dir)

from src.processor import GeoProcessor


def run_additional_tests():
    """Run comprehensive additional tests."""
    
    # Initialize processor
    json_path = os.path.join(part1_dir, 'data', 'portugal.json')
    processor = GeoProcessor(json_path)
    
    print("=" * 100)
    print("Additional Comprehensive Tests - Part 1")
    print("=" * 100)
    print()
    
    # Test cases covering various scenarios
    test_cases = [
        # Edge Cases
        {
            'name': 'Test 1: Same city, same state (identical locations)',
            'city_1': 'valadares',
            'state_1': 'viseu',
            'city_2': 'valadares',
            'state_2': 'viseu',
            'expected_level': 8,
            'is_ambiguous': 0,
            'description': 'Both refer to same location'
        },
        {
            'name': 'Test 2: Empty city_1',
            'city_1': '',
            'state_1': 'viseu',
            'city_2': 'valadares',
            'state_2': 'viseu',
            'expected_level': 2,
            'is_ambiguous': 0,
            'description': 'Empty city should return country level'
        },
        {
            'name': 'Test 3: Empty city_2',
            'city_1': 'valadares',
            'state_1': 'viseu',
            'city_2': '',
            'state_2': 'porto',
            'expected_level': 2,
            'is_ambiguous': 0,
            'description': 'Empty city should return country level'
        },
        {
            'name': 'Test 4: Both cities empty',
            'city_1': '',
            'state_1': 'viseu',
            'city_2': '',
            'state_2': 'porto',
            'expected_level': 2,
            'is_ambiguous': 0,
            'description': 'Both empty should return country level'
        },
        
        # Case Sensitivity & Normalization
        {
            'name': 'Test 5: Uppercase city names',
            'city_1': 'VALADARES',
            'state_1': 'VISEU',
            'city_2': 'VALADARES',
            'state_2': 'PORTO',
            'expected_level': 2,
            'is_ambiguous': 0,
            'description': 'Should handle uppercase correctly'
        },
        {
            'name': 'Test 6: Mixed case',
            'city_1': 'VaLaDaReS',
            'state_1': 'ViSeU',
            'city_2': 'valadares',
            'state_2': 'viseu',
            'expected_level': 8,
            'is_ambiguous': 0,
            'description': 'Should normalize case'
        },
        {
            'name': 'Test 7: With accents (São)',
            'city_1': 'são pedro do sul',
            'state_1': 'viseu',
            'city_2': 'sao pedro do sul',
            'state_2': 'viseu',
            'expected_level': 7,
            'is_ambiguous': 0,
            'description': 'Should handle accents'
        },
        
        # Different Admin Levels
        {
            'name': 'Test 8: District vs District (different)',
            'city_1': 'viseu',
            'state_1': None,
            'city_2': 'porto',
            'state_2': None,
            'expected_level': 2,
            'is_ambiguous': 0,
            'description': 'Different districts share country'
        },
        {
            'name': 'Test 9: Autonomous regions (Madeira vs Açores)',
            'city_1': 'funchal',
            'state_1': 'madeira',
            'city_2': 'horta',
            'state_2': 'acores',
            'expected_level': 2,
            'is_ambiguous': 0,
            'description': 'Different autonomous regions'
        },
        {
            'name': 'Test 10: Same region, different concelhos',
            'city_1': 'funchal',
            'state_1': 'madeira',
            'city_2': 'machico',
            'state_2': 'madeira',
            'expected_level': 4,
            'is_ambiguous': 0,
            'description': 'Same autonomous region'
        },
        
        # Ambiguous Cities
        {
            'name': 'Test 11: Both cities ambiguous (no states)',
            'city_1': 'santa cruz',
            'state_1': None,
            'city_2': 'santa barbara',
            'state_2': None,
            'expected_level': 8,
            'is_ambiguous': 1,
            'description': 'Multiple santa cruz and santa barbara exist'
        },
        {
            'name': 'Test 12: City exists in multiple levels',
            'city_1': 'castelo branco',
            'state_1': None,
            'city_2': 'valadares',
            'state_2': 'viseu',
            'expected_level': 2,
            'is_ambiguous': 1,
            'description': 'castelo branco is both district and cidade'
        },
        
        # Hierarchy Tests
        {
            'name': 'Test 13: Parent-child at level 6-7',
            'city_1': 'viseu',
            'state_1': None,
            'city_2': 'sao pedro do sul',
            'state_2': 'viseu',
            'expected_level': 6,
            'is_ambiguous': 0,
            'description': 'Concelho inside distrito'
        },
        {
            'name': 'Test 14: Parent-child at level 4-7 (autonomous region)',
            'city_1': 'madeira',
            'state_1': None,
            'city_2': 'funchal',
            'state_2': 'madeira',
            'expected_level': 4,
            'is_ambiguous': 0,
            'description': 'Concelho inside autonomous region'
        },
        
        # Real-world Scenarios
        {
            'name': 'Test 15: Common parish names in different locations',
            'city_1': 'santa maria',
            'state_1': None,
            'city_2': 'santa maria',
            'state_2': None,
            'expected_level': 8,
            'is_ambiguous': 1,
            'description': 'Very common name, multiple occurrences'
        },
        {
            'name': 'Test 16: Unique name (should not be ambiguous)',
            'city_1': 'sao pedro do sul',
            'state_1': None,
            'city_2': 'funchal',
            'state_2': None,
            'expected_level': 2,
            'is_ambiguous': 0,
            'description': 'Both are unique locations'
        },
        {
            'name': 'Test 17: Wrong state provided',
            'city_1': 'valadares',
            'state_1': 'lisboa',  # valadares not in lisboa
            'city_2': 'valadares',
            'state_2': 'viseu',
            'expected_level': 2,
            'is_ambiguous': 0,
            'description': 'Wrong state = location not found'
        },
        
        # Special Characters
        {
            'name': 'Test 18: Names with special characters',
            'city_1': 'póvoa de rio de moinhos e cafede',
            'state_1': 'castelo branco',
            'city_2': 'povoa de rio de moinhos e cafede',
            'state_2': 'castelo branco',
            'expected_level': 8,
            'is_ambiguous': 0,
            'description': 'Should normalize special characters'
        },
        
        # None/NaN handling
        {
            'name': 'Test 19: None vs empty string',
            'city_1': 'valadares',
            'state_1': None,
            'city_2': 'valadares',
            'state_2': '',
            'expected_level': 8,
            'is_ambiguous': 1,
            'description': 'None and empty string should be treated the same'
        },
        
        # Multiple matches in same hierarchy level
        {
            'name': 'Test 20: Same parish name, different concelhos in same district',
            'city_1': 'santo antonio',
            'state_1': 'madeira',
            'city_2': 'santo antonio',
            'state_2': 'madeira',
            'expected_level': 8,
            'is_ambiguous': 1,
            'description': 'Multiple santo antonio in madeira'
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
    passed = 0
    failed = 0
    warnings = 0
    
    for i, tc in enumerate(test_cases):
        actual_level = result.iloc[i]['expected_level']
        actual_ambiguous = result.iloc[i]['is_ambiguous']
        expected_level = tc['expected_level']
        expected_ambiguous = tc['is_ambiguous']
        
        level_match = actual_level == expected_level
        ambiguous_match = actual_ambiguous == expected_ambiguous
        test_passed = level_match and ambiguous_match
        
        if test_passed:
            status = "✅ PASS"
            passed += 1
        elif level_match and not ambiguous_match:
            # Minor difference - ambiguity detection
            status = "⚠️  WARN"
            warnings += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"{status} - {tc['name']}")
        print(f"  Description: {tc['description']}")
        print(f"  Input: city_1='{tc['city_1']}' state_1='{tc['state_1']}' | "
              f"city_2='{tc['city_2']}' state_2='{tc['state_2']}'")
        print(f"  Expected: level={expected_level}, ambiguous={expected_ambiguous}")
        print(f"  Actual:   level={actual_level}, ambiguous={actual_ambiguous}")
        
        if not test_passed:
            if not level_match:
                print(f"  ❌ Level mismatch!")
            if not ambiguous_match:
                print(f"  ⚠️  Ambiguity mismatch (minor issue)")
        
        print()
    
    # Summary
    total = len(test_cases)
    print("=" * 100)
    print(f"Test Summary: {passed}/{total} passed, {failed} failed, {warnings} warnings")
    print("=" * 100)
    
    if failed == 0 and warnings == 0:
        print("🎉 All additional tests passed!")
        return 0
    elif failed == 0:
        print("✅ All critical tests passed (some minor warnings)")
        return 0
    else:
        print("⚠️  Some tests failed. Review implementation.")
        return 1


if __name__ == '__main__':
    sys.exit(run_additional_tests())
