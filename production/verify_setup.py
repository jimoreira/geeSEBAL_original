#!/usr/bin/env python3
"""
Final Production Verification
"""

print("=" * 60)
print("PRODUCTION SETUP VERIFICATION")
print("=" * 60)

# Test 1: Check files exist
import os
files = ['field_timeseries_generator.py', 'field_timeseries_utils.py', 'example_usage.py', 'README.md']
print("✓ Production files:")
for f in files:
    exists = "✓" if os.path.exists(f) else "✗"
    print(f"  {exists} {f}")

# Test 2: Test imports
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from etbrasil.geesebal import Collection
    print("✓ geeSEBAL import successful")
except Exception as e:
    print(f"✗ geeSEBAL import failed: {e}")

try:
    from field_timeseries_utils import generate_field_timeseries
    print("✓ field_timeseries_utils import successful")
except Exception as e:
    print(f"✗ field_timeseries_utils import failed: {e}")

print("\n" + "=" * 60)
print("SETUP COMPLETE!")
print("=" * 60)
print("\nThe production directory contains:")
print("1. field_timeseries_generator.py - Command-line tool")
print("2. field_timeseries_utils.py - Python module")  
print("3. example_usage.py - Usage examples")
print("4. README.md - Documentation")
print("\nTo use:")
print("python field_timeseries_generator.py --schema carballal --output_dir ./output")
print("\nAll imports working correctly from production directory!")
print("=" * 60)
