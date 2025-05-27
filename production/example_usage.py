#!/usr/bin/env python3
"""
Example usage of the Field Time Series Generator

This script shows different ways to use the field time series generator tools.
"""

import ee
from field_timeseries_utils import generate_field_timeseries

def main():
    # Initialize Earth Engine (you may need to authenticate first)
    try:
        ee.Initialize(project='tercero')
        print("Earth Engine initialized successfully")
    except Exception as e:
        print(f"Earth Engine initialization failed: {e}")
        print("Please run: ee.Authenticate()")
        return
    
    # Example 1: Process all tables in carballal schema with default dates
    print("Example 1: Processing all tables in carballal schema with default dates")
    generate_field_timeseries(
        schema='carballal',
        output_dir='./output_carballal'
    )
    
    # Example 2: Process a specific table with custom date range
    print("\nExample 2: Processing specific table with custom date range")
    generate_field_timeseries(
        schema='carballal',
        output_dir='./output_specific',
        table_name='your_specific_table_consolidado',  # Replace with actual table name
        start_year=2023,
        start_month=6,
        start_day=1,
        end_year=2024,
        end_month=12,
        end_day=31,
        cloud_cover=15
    )
    
    # Example 3: Use with different schema and seasonal analysis
    print("\nExample 3: Processing different schema for summer season")
    generate_field_timeseries(
        schema='inia',  # Replace with your desired schema
        output_dir='./output_inia_summer',
        start_year=2024,
        start_month=12,  # Summer season
        start_day=1,
        end_year=2025,
        end_month=3,
        end_day=31
    )

if __name__ == "__main__":
    main()
