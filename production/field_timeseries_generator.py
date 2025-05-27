#!/usr/bin/env python3
"""
Field Time Series Generator

This script generates time series images for each field (campo and lote) combination
from a PostGIS database using geeSEBAL and Google Earth Engine.

Usage:
    python field_timeseries_generator.py --schema carballal --output_dir ./output_tifs

Author: Ing. Agr. Javier Moreira
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

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✓ Loaded environment variables from .env file")
    else:
        print("⚠️  No .env file found. Make sure to set environment variables manually.")

# Load environment variables at module level
load_env_file()

# Add parent directory to path for geeSEBAL imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etbrasil.geesebal import Collection

class FieldTimeSeriesGenerator:
    def __init__(self, schema, output_dir, database_uri=None):
        """
        Initialize the Field Time Series Generator
        
        Args:
            schema (str): Database schema name
            output_dir (str): Output directory for generated TIF files
            database_uri (str): Database connection URI (optional)
        """        self.schema = schema
        self.output_dir = output_dir
        
        # Default database connection using environment variables
        if database_uri is None:
            # Get credentials from environment variables for security
            db_user = os.getenv('DB_USER', 'postgres')
            db_password = os.getenv('DB_PASSWORD')
            db_host = os.getenv('DB_HOST')
            db_name = os.getenv('DB_NAME')
            
            if not db_password or not db_host or not db_name:
                raise ValueError("Database credentials must be set via environment variables: DB_PASSWORD, DB_HOST, DB_NAME")
            
            self.database_uri = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'
        else:
            self.database_uri = database_uri
            
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize Earth Engine
        try:
            ee.Initialize(project='tercero')
            print("Earth Engine initialized successfully")
        except Exception as e:
            print(f"Error initializing Earth Engine: {e}")
            print("Please authenticate with: ee.Authenticate()")
            
        # Initialize database connection
        self.engine = create_engine(self.database_uri)
        
    def get_consolidado_tables(self):
        """Get list of consolidated tables from the database schema"""
        query = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema
            AND table_name LIKE '%_consolidado';
        """).bindparams(schema=self.schema)
        
        with self.engine.connect() as connection:
            result = connection.execute(query)
            rows = result.fetchall()
            tables_df = pd.DataFrame(rows, columns=['table_name'])
            
        return tables_df['table_name'].tolist()
    
    def load_table_data(self, table_name):
        """Load spatial data from a specific table"""
        print(f"Loading table: {table_name}")
        
        # Load the table into a GeoDataFrame
        gdf = gpd.read_postgis(
            f'SELECT * FROM "{self.schema}"."{table_name}"', 
            self.engine, 
            geom_col='geom'
        )
        
        # Process the table (convert 'fecha_siembra' to string if it exists)
        if 'fecha_siembra' in gdf.columns:
            gdf['fecha_siembra'] = gdf['fecha_siembra'].astype(str)
        
        print(f"Loaded GeoDataFrame for table: {table_name} with {len(gdf)} rows")
        
        if gdf.empty:
            print("GeoDataFrame is empty!")
            return None
        
        return gdf
    
    def get_filtered_geometry(self, gdf):
        """Filter GeoDataFrame and convert to Earth Engine geometry"""
        if gdf is None:
            print("GeoDataFrame is not loaded yet!")
            return None, None

        # Filter out rows where 'fecha_siembra' is NaN or 'NaT'
        filtered_gdf = gdf[gdf['fecha_siembra'].notna() & (gdf['fecha_siembra'] != 'NaT')]
          if filtered_gdf.empty:
            print("No valid fecha_siembra data found!")
            return None, None
        
        # Convert filtered GeoDataFrame to GeoJSON
        geojson = json.loads(filtered_gdf.to_json())
        # Convert the filtered GeoJSON to an Earth Engine object
        subset_asset = geemap.geojson_to_ee(geojson)
        
        # Extract geometry from the Earth Engine object
        geom = subset_asset.geometry()
        
        return filtered_gdf, geom
    
    def get_table_bounds_geometry(self, gdf):
        """Create a bounding box geometry that encompasses all features in the table"""
        # Get the total bounds of all geometries in the GeoDataFrame
        bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
        
        # Add a buffer to ensure we capture edge effects (buffer in degrees ~1km)
        buffer = 0.01  
        bounds_buffered = [
            bounds[0] - buffer,  # minx
            bounds[1] - buffer,  # miny  
            bounds[2] + buffer,  # maxx
            bounds[3] + buffer   # maxy
        ]
        
        # Create Earth Engine rectangle geometry
        bounds_geom = ee.Geometry.Rectangle(bounds_buffered)
        
        print(f"Table bounds: {bounds}")
        print(f"Buffered collection area: {bounds_buffered}")
        
        return bounds_geom
      def check_geometry_intersection(self, field_geom, collection_bounds):
        """Check if a field geometry intersects with the collection bounds"""
        try:
            # Convert field geometry to Earth Engine geometry
            field_bounds = ee.Geometry.Rectangle([
                field_geom.bounds[0], field_geom.bounds[1], 
                field_geom.bounds[2], field_geom.bounds[3]
            ])
            # Check intersection
            intersects = collection_bounds.intersects(field_bounds).getInfo()
            return intersects
        except Exception as e:
            print(f"Warning: Could not check geometry intersection: {e}")
            return True  # Assume intersection to be safe
    
    def create_image_collection(self, geom, start_year=2024, start_month=11, start_day=1,
                               end_year=2025, end_month=4, end_day=21, cloud_cover=20):
        """Create geeSEBAL collection and convert to image collection
        
        Args:
            geom: Earth Engine geometry object (should be table bounds)
            start_year (int): Starting year for the collection
            start_month (int): Starting month for the collection
            start_day (int): Starting day for the collection
            end_year (int): Ending year for the collection
            end_month (int): Ending month for the collection
            end_day (int): Ending day for the collection
            cloud_cover (int): Maximum cloud cover percentage
        
        Returns:
            tuple: (image_collection, collection_bounds_geom)
        """
        print(f"Creating geeSEBAL Collection from {start_year}-{start_month:02d}-{start_day:02d} to {end_year}-{end_month:02d}-{end_day:02d}...")
        print("Using table bounds geometry for efficient collection creation...")
        
        # Create geeSEBAL Collection filtered by geometry
        geeSEBAL_Collection = Collection(
            start_year, start_month, start_day,
            end_year, end_month, end_day,
            cloud_cover, geom
        )
        
        # Get the Collection_ET object
        collection_et = geeSEBAL_Collection.Collection_ET
        
        if not collection_et:
            print("No valid ET bands were added to the collection.")
            return None, None
        
        bands = collection_et.bandNames().getInfo()
        print(f"Collection ET created with {len(bands)} bands: {bands[:3]}..." if len(bands) > 3 else f"Collection ET bands: {bands}")
        
        # Transform collection to image collection with dates
        image_list = []
        
        for band in bands:
            # Extract the band as a single-band image
            single_band_image = collection_et.select([band])
            
            # Extract the date from the band name
            date_str = band.split('_')[-1]
            date = ee.Date.parse('YYYYMMdd', date_str)
            
            # Set the date as a property for time-sorting
            single_band_image = single_band_image.set('system:time_start', date.millis())
            
            # Rename the band to 'etr'
            single_band_image = single_band_image.rename('etr')
            
            # Add the image to the list
            image_list.append(single_band_image)
          # Create an ImageCollection from the list of images
        image_collection = ee.ImageCollection.fromImages(image_list)
        # Return both the collection and the bounds geometry for intersection checks
        return image_collection, geom
    
    def process_field_timeseries(self, gdf, image_collection, collection_bounds, campo_value, lote_value):
        """Process time series for a specific campo and lote
        
        Args:
            gdf: GeoDataFrame with field data
            image_collection: Earth Engine ImageCollection
            collection_bounds: Earth Engine geometry bounds of the collection
            campo_value: Campo name
            lote_value: Lote number
        """
        print(f"Processing field: {campo_value}, lote: {lote_value}")
        
        # Subset the GeoDataFrame based on campo and lote
        subset_gdf = gdf[(gdf['campo'] == campo_value) & (gdf['lote'] == lote_value)]
        
        if subset_gdf.empty:
            print(f"No data found for campo: {campo_value}, lote: {lote_value}")
            return False
        
        # Dissolve geometry
        dissolved_geometry = subset_gdf.dissolve().geometry.iloc[0]
        
        # Check if field geometry intersects with collection bounds
        intersects = self.check_geometry_intersection(dissolved_geometry, collection_bounds)
        if not intersects:
            print(f"⚠️  WARNING: Field {campo_value}-{lote_value} does not intersect with collection bounds. Skipping...")
            return False
        
        # Convert image collection to xarray using wxee
        print("Converting to xarray dataset...")
        geom_bounds = dissolved_geometry.bounds
        
        # Create a simple bounding box geometry for the region
        region_geom = ee.Geometry.Rectangle([
            geom_bounds[0], geom_bounds[1], geom_bounds[2], geom_bounds[3]
        ])
        
        try:
            ds = image_collection.wx.to_xarray(
                region=region_geom,
                scale=30
            )
            
            # Process time series
            original_time_series = ds.chunk('auto')
            
            time_series_resampled = original_time_series.resample(time='15D').max()
            time_series_resampled.attrs = original_time_series.attrs.copy()
            
            time_series_interpolated = time_series_resampled.chunk(dict(time=-1)).interpolate_na('time', use_coordinate=False)
            
            # Clip to field boundary
            subset_da = time_series_interpolated.etr.rio.clip([dissolved_geometry], subset_gdf.crs)
            
            # Save time series as TIF files
            self.save_timeseries_tifs(subset_da, campo_value, lote_value)
            
            return True
            
        except Exception as e:
            print(f"Error processing field {campo_value}-{lote_value}: {e}")
            return False
    
    def save_timeseries_tifs(self, subset_da, campo_value, lote_value):
        """Save time series data as TIF files"""
        print(f"Saving TIF files for {campo_value}-{lote_value}...")
        
        field_output_dir = os.path.join(self.output_dir, f"{campo_value}_{lote_value}")
        os.makedirs(field_output_dir, exist_ok=True)
        
        saved_count = 0
        
        for time in subset_da.time.values:
            image = subset_da.sel(time=time)
            
            # Transform the image to suit rioxarray format
            image = image.transpose('y', 'x').rio.write_crs('EPSG:4326')
            
            date = np.datetime_as_string(time, unit='D')
            output_file = f'{campo_value}_{lote_value}_{date}.tif'
            output_path = os.path.join(field_output_dir, output_file)
            
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
                
                image.rio.to_raster(output_path, driver='COG')
                saved_count += 1
                print(f"Saved: {output_file}")
                
            except Exception as e:
                print(f"Error saving {output_file}: {e}")
        
        print(f"Saved {saved_count} TIF files for {campo_value}-{lote_value}")
    
    def process_all_fields(self, table_name=None, start_year=2024, start_month=11, start_day=1,
                          end_year=2025, end_month=4, end_day=21, cloud_cover=20):
        """Process all campo-lote combinations from all tables or a specific table
        
        Args:
            table_name (str): Specific table to process (optional)
            start_year (int): Starting year for the collection
            start_month (int): Starting month for the collection
            start_day (int): Starting day for the collection
            end_year (int): Ending year for the collection
            end_month (int): Ending month for the collection
            end_day (int): Ending day for the collection
            cloud_cover (int): Maximum cloud cover percentage
        """
        
        if table_name:
            table_list = [table_name]
        else:
            table_list = self.get_consolidado_tables()
        
        if not table_list:
            print(f"No consolidado tables found in schema: {self.schema}")
            return
          print(f"Found {len(table_list)} consolidado tables: {table_list}")
        
        for table in table_list:
            print(f"\n{'='*50}")
            print(f"Processing table: {table}")
            print(f"{'='*50}")
            
            # Load table data
            gdf = self.load_table_data(table)
            if gdf is None:
                continue
            
            # Get filtered geometry for the entire table
            filtered_gdf, geom = self.get_filtered_geometry(gdf)
            if geom is None:
                continue
            
            # Create a bounding box geometry that encompasses all fields in the table
            # This is more efficient than creating individual collections for each field
            table_bounds_geom = self.get_table_bounds_geometry(filtered_gdf)
            
            # Create image collection using table bounds (OPTIMIZED APPROACH)
            print("🚀 Creating collection once for entire table (optimized approach)...")
            image_collection, collection_bounds = self.create_image_collection(
                table_bounds_geom, start_year, start_month, start_day,
                end_year, end_month, end_day, cloud_cover
            )            if image_collection is None:
                continue
            
            # Get unique campo-lote combinations
            campo_lote_combinations = filtered_gdf[['campo', 'lote']].drop_duplicates()
            
            print(f"Found {len(campo_lote_combinations)} campo-lote combinations")
            print("Now subsetting the collection for each individual field...")
            
            # Process each combination using the same collection (OPTIMIZED APPROACH)
            successful_count = 0
            skipped_count = 0
            for _, row in campo_lote_combinations.iterrows():
                campo_value = row['campo']
                lote_value = str(row['lote'])
                
                try:
                    success = self.process_field_timeseries(
                        filtered_gdf, image_collection, collection_bounds, campo_value, lote_value
                    )
                    if success:
                        successful_count += 1
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    print(f"Error processing {campo_value}-{lote_value}: {e}")
                    skipped_count += 1
                    continue
            
            print(f"\n📊 SUMMARY for table: {table}")
            print(f"✅ Successfully processed: {successful_count}/{len(campo_lote_combinations)} field combinations")
            if skipped_count > 0:
                print(f"⚠️  Skipped (no intersection or errors): {skipped_count}")
            print(f"🎯 Collection created only once for entire table (optimized!)")
        
        print(f"\n🎉 All processing complete! Check output directory: {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Generate time series images for fields from PostGIS database')
    parser.add_argument('--schema', required=True, help='Database schema name')
    parser.add_argument('--output_dir', required=True, help='Output directory for TIF files')
    parser.add_argument('--table', help='Specific table name (optional, processes all if not specified)')
    parser.add_argument('--database_uri', help='Database connection URI (optional)')
    
    # Date range parameters
    parser.add_argument('--start_year', type=int, default=2024, help='Starting year (default: 2024)')
    parser.add_argument('--start_month', type=int, default=11, help='Starting month (default: 11)')
    parser.add_argument('--start_day', type=int, default=1, help='Starting day (default: 1)')
    parser.add_argument('--end_year', type=int, default=2025, help='Ending year (default: 2025)')
    parser.add_argument('--end_month', type=int, default=4, help='Ending month (default: 4)')
    parser.add_argument('--end_day', type=int, default=21, help='Ending day (default: 21)')
    parser.add_argument('--cloud_cover', type=int, default=20, help='Maximum cloud cover percentage (default: 20)')
    
    args = parser.parse_args()
    
    # Create generator instance
    generator = FieldTimeSeriesGenerator(
        schema=args.schema,
        output_dir=args.output_dir,
        database_uri=args.database_uri
    )
    
    # Process all fields with date parameters
    generator.process_all_fields(
        table_name=args.table,
        start_year=args.start_year,
        start_month=args.start_month, 
        start_day=args.start_day,
        end_year=args.end_year,
        end_month=args.end_month,
        end_day=args.end_day,
        cloud_cover=args.cloud_cover
    )
    
    print(f"\nProcessing complete! Check output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
