#!/usr/bin/env python3
"""
Test import functionality for the production tools
"""

import sys
import os

# Add parent directory to path for geeSEBAL import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from etbrasil.geesebal import Collection
    print("✓ Successfully imported Collection from etbrasil.geesebal")
    
    from field_timeseries_utils import generate_field_timeseries
    print("✓ Successfully imported generate_field_timeseries from field_timeseries_utils")
    
    print("✓ All imports working correctly!")
    print(f"✓ Python version: {sys.version}")
    print(f"✓ Current working directory: {os.getcwd()}")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Available paths:")
    for path in sys.path:
        print(f"  - {path}")
