#!/usr/bin/env python3
"""Debug script to inspect loaded data."""

import sys
import os

part1_dir = os.path.dirname(os.path.abspath(__file__))
if part1_dir not in sys.path:
    sys.path.insert(0, part1_dir)

from src.loader import GeoDataLoader
from src.utils import normalize_name

# Load data
json_path = os.path.join(part1_dir, 'data', 'portugal.json')
loader = GeoDataLoader(json_path)

# Find "valadares" entries
valadares_norm = normalize_name("valadares")
print(f"Looking for '{valadares_norm}'...")
print()

if valadares_norm in loader.by_city:
    valadares_ids = loader.by_city[valadares_norm]
    print(f"Found {len(valadares_ids)} locations named 'valadares':")
    print()
    
    for i, loc_id in enumerate(valadares_ids):
        loc = loader.locations_by_id[loc_id]
        print(f"  {i+1}. ID={loc.id}, Level={loc.admin_level}")
        print(f"     Ancestors: {' > '.join(loc.ancestors_names)}")
        print()
else:
    print("❌ 'valadares' not found in index!")
    print()

# Find "sao pedro do sul"
sps_norm = normalize_name("sao pedro do sul")
print(f"Looking for '{sps_norm}'...")
print()

if sps_norm in loader.by_city:
    sps_ids = loader.by_city[sps_norm]
    print(f"Found {len(sps_ids)} locations named 'sao pedro do sul':")
    print()
    
    for i, loc_id in enumerate(sps_ids):
        loc = loader.locations_by_id[loc_id]
        print(f"  {i+1}. ID={loc.id}, Level={loc.admin_level}")
        print(f"     Ancestors: {' > '.join(loc.ancestors_names)}")
        if loc.admin_level == 7:
            print(f"     Children: {len([l for l in loader.locations if l.parent_id == loc.id])} locations")
        print()
else:
    print("❌ 'sao pedro do sul' not found in index!")
    print()

# Check if any valadares is inside sao pedro do sul
print("Checking hierarchy...")
print()

if valadares_norm in loader.by_city and sps_norm in loader.by_city:
    for v_id in loader.by_city[valadares_norm]:
        v_loc = loader.locations_by_id[v_id]
        for s_id in loader.by_city[sps_norm]:
            s_loc = loader.locations_by_id[s_id]
            if s_id in v_loc.ancestors:
                print(f"✅ Valadares (ID={v_id}) is inside Sao Pedro do Sul (ID={s_id})")
                print(f"   Valadares path: {' > '.join(v_loc.ancestors_names)}")
                print()

# Stats
print(f"Total locations: {len(loader.locations)}")
print(f"Unique city names: {len(loader.by_city)}")
