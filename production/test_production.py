#!/usr/bin/env python3
"""
Test Production Setup

This script tests the production setup without requiring Earth Engine authentication.
"""

import os
import sys
from field_timeseries_utils import load_consolidado_tables

def test_database_connection():
    """Test database connection and table listing"""
    print("Testing database connection...")
    
    database_uri = 'postgresql://postgres:Sinergia7@ec2-3-134-97-6.us-east-2.compute.amazonaws.com/shiny_actbiologico'
    schema = 'carballal'
    
    try:
        table_list, engine = load_consolidado_tables(schema, database_uri)
        print(f"✓ Successfully connected to database")
        print(f"✓ Found {len(table_list)} consolidado tables in schema '{schema}':")
        for table in table_list:
            print(f"  - {table}")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_imports():
    """Test all necessary imports"""
    print("\nTesting imports...")
    
    try:
        # Test geeSEBAL import
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from etbrasil.geesebal import Collection
        print("✓ Successfully imported geeSEBAL Collection")
        
        # Test utility functions
        from field_timeseries_utils import generate_field_timeseries
        print("✓ Successfully imported field_timeseries_utils")
        
        # Test required packages
        import pandas as pd
        import geopandas as gpd
        import numpy as np
        import geemap
        import wxee
        print("✓ All required packages imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_production_structure():
    """Test production directory structure"""
    print("\nTesting production directory structure...")
    
    current_dir = os.getcwd()
    expected_files = [
        'field_timeseries_generator.py',
        'field_timeseries_utils.py', 
        'example_usage.py',
        'README.md'
    ]
    
    missing_files = []
    for file in expected_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    else:
        print("✓ All production files present")
        print(f"✓ Working directory: {current_dir}")
        return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING PRODUCTION SETUP")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Production structure
    if test_production_structure():
        tests_passed += 1
    
    # Test 2: Imports
    if test_imports():
        tests_passed += 1
    
    # Test 3: Database connection
    if test_database_connection():
        tests_passed += 1
    
    print(f"\n" + "=" * 60)
    print(f"TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✓ Production setup is working correctly!")
        print("\nYou can now use the tools:")
        print("1. Command line: python field_timeseries_generator.py --schema carballal --output_dir ./output")
        print("2. Python module: from field_timeseries_utils import generate_field_timeseries")
        print("3. See example_usage.py for detailed examples")
        print("\nNote: You'll need to authenticate Earth Engine before actual processing:")
        print("import ee; ee.Authenticate(); ee.Initialize(project='tercero')")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
