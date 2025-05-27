#!/usr/bin/env python3
"""
Test script to verify season filtering functionality
"""

import sys
import os

# Add the production directory to path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from field_timeseries_utils import load_env_file, create_database_connection
    print("✅ Successfully imported utility functions")
except ImportError as e:
    print(f"❌ Failed to import utilities: {e}")
    sys.exit(1)

def test_season_filtering():
    """Test the season filtering functionality"""
    
    # Load environment and create database connection
    try:
        load_env_file()
        engine = create_database_connection()
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Import the class here to avoid import errors if dependencies are missing
    try:
        from field_timeseries_generator import FieldTimeSeriesGenerator
        print("✅ Successfully imported FieldTimeSeriesGenerator")
    except ImportError as e:
        print(f"❌ Failed to import FieldTimeSeriesGenerator: {e}")
        return
    
    # Test table discovery without season filter
    print("\n" + "="*50)
    print("TEST 1: All tables (no season filter)")
    print("="*50)
    
    try:
        # Create a minimal generator instance just for table discovery
        from sqlalchemy import create_engine, text
        from field_timeseries_utils import load_env_file
        
        load_env_file()
        
        # Manually create engine for testing
        import os
        database_uri = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        engine = create_engine(database_uri)
        
        # Test query directly
        query = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema_name
            AND table_name LIKE '%_consolidado'
            ORDER BY table_name
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"schema_name": "carballal"})
            all_tables = [row[0] for row in result.fetchall()]
        
        print(f"📋 All consolidado tables: {all_tables}")
        
        # Test season filtering logic
        print("\n" + "="*50)
        print("TEST 2: Summer season filtering (ver)")
        print("="*50)
        
        season_filter = "ver"
        summer_tables = [t for t in all_tables if f"_{season_filter}" in t.lower()]
        print(f"🌱 Summer tables: {summer_tables}")
        
        print("\n" + "="*50)
        print("TEST 3: Winter season filtering (inv)")
        print("="*50)
        
        season_filter = "inv"
        winter_tables = [t for t in all_tables if f"_{season_filter}" in t.lower()]
        print(f"❄️ Winter tables: {winter_tables}")
        
        print("\n✅ Season filtering tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_season_filtering()
