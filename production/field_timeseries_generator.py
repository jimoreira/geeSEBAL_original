#!/usr/bin/env python3
"""
Field Time Series Generator - OPTIMIZED VERSION
This script generates time series images for each field (campo and lote) combination
from a PostGIS database using geeSEBAL and Google Earth Engine.

OPTIMIZATION: Creates image collections once per table using table bounds geometry,
then subsets for individual fields, significantly improving performance.

Usage:
    python field_timeseries_generator.py --schema carballal --output_dir ./output_tifs

Author: Ing. Agr. Javier Moreira
Optimized: AI Assistant
"""

import os
import sys
import argparse
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
import geemap
import wxee
import ee
from datetime import datetime
from pathlib import Path

# Import our optimized utility functions
from field_timeseries_utils import (
    load_env_file,
    create_database_connection,
    get_field_data,
    get_table_bounds_geometry,
    create_image_collection,
    check_geometry_intersection,
    process_field_timeseries
)


class FieldTimeSeriesGenerator:
    """
    OPTIMIZED Field Time Series Generator
    
    Generates ET time series for agricultural fields using an optimized workflow:
    1. Creates image collections once per table using table bounds
    2. Subsets collections for individual field geometries    3. Includes intersection checking and performance logging
    """
    
    def __init__(self, schema_name, output_dir, season_config=None):
        """
        Initialize the generator with schema and output directory.
        
        Args:
            schema_name (str): PostgreSQL schema containing field data
            output_dir (str): Directory to save generated time series images
            season_config (dict, optional): Custom seasonal date configurations
        """
        self.schema_name = schema_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurable seasonal settings - you can customize these!
        self.season_config = season_config or {
            'summer': {
                'start_month': 12,  # December
                'start_day': 1,
                'end_month': 3,     # March
                'end_day': 31,
                'span_years': True  # Summer spans two years (Dec year1 - Mar year2)
            },
            'winter': {
                'start_month': 6,   # June
                'start_day': 1,
                'end_month': 9,     # September
                'end_day': 30,
                'span_years': False # Winter stays in same year
            }
        }
        
        # Load environment variables and initialize connections
        load_env_file()
        self.engine = create_database_connection()
        
        # Initialize Earth Engine
        try:
            ee.Initialize()
            print("✅ Earth Engine initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Earth Engine: {e}")
            sys.exit(1)
    
    def get_all_tables(self, season_filter=None):
        """
        Get all tables in the specified schema that contain field data.
        
        Following the notebook pattern, looks for tables ending with '_consolidado'.
        
        Args:
            season_filter (str, optional): Filter by season 'inv' (winter) or 'ver' (summer)
        
        Returns:
            list: List of table names containing geographic data
        """
        query = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema_name
            AND table_name LIKE '%_consolidado'
            ORDER BY table_name        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query, {"schema_name": self.schema_name})
            tables = [row[0] for row in result.fetchall()]
        
        if not tables:
            print(f"⚠️  No '_consolidado' tables found in schema '{self.schema_name}'")
            print("   Falling back to all tables with potential field keywords...")
            
            # Fallback: look for any tables with field-related keywords
            query_fallback = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema_name 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query_fallback, {"schema_name": self.schema_name})
                all_tables = [row[0] for row in result.fetchall()]
            
            # Filter tables that likely contain field data
            tables = [t for t in all_tables if any(keyword in t.lower() 
                               for keyword in ['campo', 'lote', 'field', 'parcela', 'consolidado'])]
        
        # Apply season filtering if specified
        if season_filter:
            season_filter = season_filter.lower()
            if season_filter not in ['inv', 'ver']:
                print(f"⚠️  Warning: Invalid season filter '{season_filter}'. Valid options: 'inv' (winter), 'ver' (summer)")
                print("   Proceeding without season filtering...")
            else:
                original_count = len(tables)
                # Filter tables by season pattern: schema_season_consolidado
                tables = [t for t in tables if f"_{season_filter}" in t.lower()]
                season_name = "winter" if season_filter == "inv" else "summer"
                print(f"🌱 Season filter applied: {season_name} ({season_filter})")
                print(f"📊 Filtered from {original_count} to {len(tables)} tables")
        print(f"📋 Found {len(tables)} tables in schema '{self.schema_name}': {tables}")
        return tables
    
    def extract_date_range_from_table(self, table_name):
        """
        Extract appropriate date range from table name patterns using configurable seasons.
        
        Only auto-detects YEARS from table names. Months/days come from season_config.
        
        Examples:
        - carballal_ver2122_consolidado -> Summer 2021-2022 (uses summer config)
        - carballal_inv21_consolidado -> Winter 2021 (uses winter config)
        - carballal_ver2425_consolidado -> Summer 2024-2025 (uses summer config)
        
        Args:
            table_name (str): Table name with season/year pattern
            
        Returns:
            tuple: (start_date, end_date) as strings in YYYY-MM-DD format
        """
        import re
        
        # Extract season and year information from table name
        # Pattern: schema_season[year(s)]_consolidado
        
        # Try summer pattern first (ver2122, ver2223, etc.)
        summer_match = re.search(r'_ver(\d{2})(\d{2})_', table_name.lower())
        if summer_match:
            year1 = int("20" + summer_match.group(1))
            year2 = int("20" + summer_match.group(2))
            
            # Get summer configuration
            summer_config = self.season_config['summer']
            
            # Summer season spans years: start_month/day of year1 to end_month/day of year2
            start_year = year1 if not summer_config.get('span_years') else year1
            end_year = year2 if summer_config.get('span_years') else year1
            
            start_date = f"{start_year}-{summer_config['start_month']:02d}-{summer_config['start_day']:02d}"
            end_date = f"{end_year}-{summer_config['end_month']:02d}-{summer_config['end_day']:02d}"
            
            print(f"🌞 Detected summer season {year1}-{year2}")
            print(f"📅 Auto-detected date range: {start_date} to {end_date}")
            print(f"⚙️  Using summer config: {summer_config['start_month']}/{summer_config['start_day']} to {summer_config['end_month']}/{summer_config['end_day']}")
            return start_date, end_date
        
        # Try winter pattern (inv21, inv22, etc.)
        winter_match = re.search(r'_inv(\d{2})_', table_name.lower())
        if winter_match:
            year = int("20" + winter_match.group(1))
            
            # Get winter configuration
            winter_config = self.season_config['winter']
            
            # Winter season stays in same year
            start_date = f"{year}-{winter_config['start_month']:02d}-{winter_config['start_day']:02d}"
            end_date = f"{year}-{winter_config['end_month']:02d}-{winter_config['end_day']:02d}"
            
            print(f"❄️ Detected winter season {year}")
            print(f"📅 Auto-detected date range: {start_date} to {end_date}")
            print(f"⚙️  Using winter config: {winter_config['start_month']}/{winter_config['start_day']} to {winter_config['end_month']}/{winter_config['end_day']}")
            return start_date, end_date
        
        # If no pattern matches, return None to use provided dates
        print(f"⚠️  Could not extract date range from table name: {table_name}")
        print(f"   Using provided date range instead")
        return None, None

    def process_table_optimized(self, table_name, start_date, end_date, auto_detect_dates=True):
        """
        OPTIMIZED: Process all fields in a table using a single image collection.
        
        This is the key optimization - creates collection once per table using
        table bounds, then subsets for individual fields.
        
        Args:
            table_name (str): Name of the table to process
            start_date (str): Start date for time series (YYYY-MM-DD)
            end_date (str): End date for time series (YYYY-MM-DD)
            auto_detect_dates (bool): If True, try to extract dates from table name
        """
        # SMART DATE DETECTION: Extract appropriate dates from table name
        if auto_detect_dates:
            detected_start, detected_end = self.extract_date_range_from_table(table_name)
            if detected_start and detected_end:
                start_date = detected_start
                end_date = detected_end
                print(f"✅ Using auto-detected dates for table '{table_name}'")
            else:
                print(f"⚠️  Using provided dates for table '{table_name}'")
        
        print(f"\n🚀 OPTIMIZED PROCESSING: Starting table '{table_name}'")
        print(f"📅 Date range: {start_date} to {end_date}")
        
        # Step 1: Get all field data from the table
        field_data = get_field_data(self.engine, self.schema_name, table_name)
        
        if field_data.empty:
            print(f"⚠️  No field data found in table '{table_name}'")
            return
        
        print(f"📊 Found {len(field_data)} fields in table '{table_name}'")
        
        # Step 2: OPTIMIZATION - Get table bounds geometry (once per table)
        print("🔧 OPTIMIZATION: Creating table bounds geometry...")
        table_bounds_geom = get_table_bounds_geometry(
            self.engine, self.schema_name, table_name
        )
        
        if table_bounds_geom is None:
            print(f"❌ Could not create bounds geometry for table '{table_name}'")
            return
        
        # Step 3: OPTIMIZATION - Create image collection once using table bounds
        print("🔧 OPTIMIZATION: Creating image collection for entire table...")
        collection_result = create_image_collection(
            table_bounds_geom, start_date, end_date
        )
        
        if collection_result is None:
            print(f"❌ Failed to create image collection for table '{table_name}'")
            return
        
        # Unpack the result
        image_collection, collection_bounds_geom = collection_result
        collection_size = image_collection.size().getInfo()
        
        print(f"✅ OPTIMIZATION SUCCESS: Created collection with {collection_size} images")
        print(f"🎯 Collection will be reused for all {len(field_data)} fields in this table")
        
        # Step 4: Process each field using the shared collection
        successful_fields = 0
        skipped_fields = 0
        
        for idx, field_row in field_data.iterrows():
            campo = field_row['campo']
            lote = field_row['lote']
            geometry = field_row['geometry']
            
            print(f"\n📍 Processing field {idx+1}/{len(field_data)}: {campo}_{lote}")
            
            # OPTIMIZATION: Check if field geometry intersects with collection bounds
            if not check_geometry_intersection(geometry, collection_bounds_geom):
                print(f"⚠️  WARNING: Field {campo}_{lote} does not intersect with collection bounds")
                print(f"   This field will be skipped to prevent errors")
                skipped_fields += 1
                continue
            
            # Process the field using the shared collection
            try:
                success = process_field_timeseries(
                    campo=campo,
                    lote=lote,
                    geometry=geometry,
                    image_collection=image_collection,  # Reused collection!
                    output_dir=self.output_dir,
                    start_date=start_date,
                    end_date=end_date                )
                
                if success:
                    successful_fields += 1
                    print(f"✅ Successfully processed {campo}_{lote}")
                else:
                    print(f"❌ Failed to process {campo}_{lote}")
            except Exception as e:
                print(f"❌ Error processing field {campo}_{lote}: {e}")
                continue
        
        # Summary for this table
        print(f"\n📊 TABLE '{table_name}' SUMMARY:")
        print(f"   ✅ Successfully processed: {successful_fields} fields")
        print(f"   ⚠️  Skipped (no intersection): {skipped_fields} fields")
        print(f"   ❌ Failed: {len(field_data) - successful_fields - skipped_fields} fields")
        print(f"   🚀 OPTIMIZATION: Used 1 collection for {len(field_data)} fields")
    
    def generate_time_series(self, start_date, end_date, table_filter=None, season_filter=None):
        """
        Generate time series for all fields in the schema.
        
        Args:
            start_date (str): Start date for time series (YYYY-MM-DD)
            end_date (str): End date for time series (YYYY-MM-DD)
            table_filter (str, optional): Process only specific table
            season_filter (str, optional): Filter by season 'inv' (winter) or 'ver' (summer)
        """
        print(f"🚀 Starting OPTIMIZED Field Time Series Generation")
        print(f"📂 Schema: {self.schema_name}")
        print(f"📅 Date Range: {start_date} to {end_date}")
        print(f"💾 Output Directory: {self.output_dir}")
        
        if season_filter:
            season_name = "winter" if season_filter.lower() == "inv" else "summer" if season_filter.lower() == "ver" else season_filter
            print(f"🌱 Season Filter: {season_name} ({season_filter})")
          # Get tables to process
        all_tables = self.get_all_tables(season_filter=season_filter)
        
        if table_filter:
            tables_to_process = [t for t in all_tables if table_filter.lower() in t.lower()]
            if not tables_to_process:
                print(f"❌ No tables found matching filter: {table_filter}")
                return
        else:
            tables_to_process = all_tables
        
        print(f"📋 Processing {len(tables_to_process)} tables: {tables_to_process}")
        
        # Process each table with optimization
        total_start_time = datetime.now()
        for table_idx, table_name in enumerate(tables_to_process, 1):
            print(f"\n{'='*60}")
            print(f"📊 PROCESSING TABLE {table_idx}/{len(tables_to_process)}: {table_name}")
            print(f"{'='*60}")
            
            table_start_time = datetime.now()
            
            try:
                self.process_table_optimized(table_name, start_date, end_date, auto_detect_dates=True)
                
                table_duration = datetime.now() - table_start_time
                print(f"⏱️  Table '{table_name}' completed in: {table_duration}")
                
            except Exception as e:
                print(f"❌ Error processing table '{table_name}': {e}")
                continue
        
        # Final summary
        total_duration = datetime.now() - total_start_time
        print(f"\n{'='*60}")
        print(f"🎉 OPTIMIZED PROCESSING COMPLETE!")
        print(f"⏱️  Total Duration: {total_duration}")
        print(f"📂 Output Directory: {self.output_dir}")
        print(f"🚀 Used optimized workflow with collection reuse")
        print(f"{'='*60}")


def main():
    """Main function to run the field time series generator."""
    parser = argparse.ArgumentParser(
        description="Generate optimized time series images for agricultural fields"
    )
    parser.add_argument(
        "--schema", 
        required=True, 
        help="PostgreSQL schema name containing field data"
    )
    parser.add_argument(
        "--output_dir", 
        default="./output_tifs",
        help="Output directory for time series images (default: ./output_tifs)"
    )
    parser.add_argument(
        "--start_date", 
        default="2024-10-01",
        help="Start date for time series (YYYY-MM-DD, default: 2024-10-01)"
    )
    parser.add_argument(
        "--end_date", 
        default="2025-04-30",
        help="End date for time series (YYYY-MM-DD, default: 2025-04-30)"
    )
    parser.add_argument(
        "--table", 
        help="Process only specific table (optional filter)"
    )
    parser.add_argument(
        "--season", 
        choices=['inv', 'ver'], 
        help="Filter tables by season: 'inv' for winter, 'ver' for summer"
    )
    
    # Seasonal configuration arguments
    parser.add_argument(
        "--summer_start_month", 
        type=int, 
        default=12,
        help="Summer season start month (1-12, default: 12 for December)"
    )
    parser.add_argument(
        "--summer_start_day", 
        type=int, 
        default=1,
        help="Summer season start day (1-31, default: 1)"
    )
    parser.add_argument(
        "--summer_end_month", 
        type=int, 
        default=3,
        help="Summer season end month (1-12, default: 3 for March)"
    )
    parser.add_argument(
        "--summer_end_day", 
        type=int, 
        default=31,
        help="Summer season end day (1-31, default: 31)"
    )
    parser.add_argument(
        "--winter_start_month", 
        type=int, 
        default=6,
        help="Winter season start month (1-12, default: 6 for June)"
    )
    parser.add_argument(
        "--winter_start_day", 
        type=int, 
        default=1,
        help="Winter season start day (1-31, default: 1)"
    )
    parser.add_argument(
        "--winter_end_month", 
        type=int, 
        default=9,
        help="Winter season end month (1-12, default: 9 for September)"
    )
    parser.add_argument(
        "--winter_end_day", 
        type=int, 
        default=30,
        help="Winter season end day (1-31, default: 30)"
    )
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.start_date, "%Y-%m-%d")
        datetime.strptime(args.end_date, "%Y-%m-%d")
    except ValueError as e:
        print(f"❌ Invalid date format: {e}")
        print("Please use YYYY-MM-DD format")
        sys.exit(1)
    
    # Build custom season configuration from command line arguments
    season_config = {
        'summer': {
            'start_month': args.summer_start_month,
            'start_day': args.summer_start_day,
            'end_month': args.summer_end_month,
            'end_day': args.summer_end_day,
            'span_years': True  # Summer spans two years by default
        },
        'winter': {
            'start_month': args.winter_start_month,
            'start_day': args.winter_start_day,
            'end_month': args.winter_end_month,
            'end_day': args.winter_end_day,
            'span_years': False # Winter stays in same year by default
        }
    }
    
    # Display configuration if custom values are used
    default_summer = (args.summer_start_month == 12 and args.summer_start_day == 1 and 
                     args.summer_end_month == 3 and args.summer_end_day == 31)
    default_winter = (args.winter_start_month == 6 and args.winter_start_day == 1 and 
                     args.winter_end_month == 9 and args.winter_end_day == 30)
    
    if not (default_summer and default_winter):
        print(f"⚙️  CUSTOM SEASONAL CONFIGURATION:")
        print(f"   🌞 Summer: {args.summer_start_month}/{args.summer_start_day} to {args.summer_end_month}/{args.summer_end_day}")
        print(f"   ❄️  Winter: {args.winter_start_month}/{args.winter_start_day} to {args.winter_end_month}/{args.winter_end_day}")
        print()
    
    # Create and run generator
    try:
        generator = FieldTimeSeriesGenerator(args.schema, args.output_dir, season_config=season_config)
        generator.generate_time_series(
            start_date=args.start_date,
            end_date=args.end_date,
            table_filter=args.table,
            season_filter=args.season
        )
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()