"""
Simple Field Time Series Generator Module

This module provides functions to generate time series images for fields
using the geeSEBAL workflow.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
import geemap
import wxee
import ee

# Add parent directory to path for geeSEBAL import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etbrasil.geesebal import Collection


def load_consolidado_tables(schema, database_uri):
    """Load all consolidado tables from the specified schema"""
    engine = create_engine(database_uri)
    
    query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :schema
        AND table_name LIKE '%_consolidado';
    """).bindparams(schema=schema)
    
    with engine.connect() as connection:
        result = connection.execute(query)
        rows = result.fetchall()
        tables_df = pd.DataFrame(rows, columns=['table_name'])
    
    return tables_df['table_name'].tolist(), engine


def load_table_data(table_name, schema, engine):
    """Load spatial data from a specific table"""
    print(f"Loading table: {table_name}")
    
    gdf = gpd.read_postgis(
        f'SELECT * FROM "{schema}"."{table_name}"', 
        engine, 
        geom_col='geom'
    )
    
    if 'fecha_siembra' in gdf.columns:
        gdf['fecha_siembra'] = gdf['fecha_siembra'].astype(str)
    
    print(f"Loaded {len(gdf)} rows from {table_name}")
    return gdf if not gdf.empty else None


def get_filtered_geometry(gdf):
    """Filter GeoDataFrame and convert to Earth Engine geometry"""
    if gdf is None:
        return None, None

    # Filter out rows where 'fecha_siembra' is NaN or 'NaT'
    filtered_gdf = gdf[gdf['fecha_siembra'].notna() & (gdf['fecha_siembra'] != 'NaT')]
    
    if filtered_gdf.empty:
        print("No valid fecha_siembra data found!")
        return None, None
    
    # Convert to Earth Engine geometry
    geojson = json.loads(filtered_gdf.to_json())
    subset_asset = geemap.geojson_to_ee(geojson)
    geom = subset_asset.geometry()
    
    return filtered_gdf, geom


def create_image_collection(geom, start_year=2024, start_month=11, start_day=1,
                           end_year=2025, end_month=4, end_day=21, cloud_cover=20):
    """Create geeSEBAL collection and convert to image collection
    
    Args:
        geom: Earth Engine geometry object
        start_year (int): Starting year for the collection
        start_month (int): Starting month for the collection
        start_day (int): Starting day for the collection
        end_year (int): Ending year for the collection
        end_month (int): Ending month for the collection
        end_day (int): Ending day for the collection
        cloud_cover (int): Maximum cloud cover percentage
    """
    print(f"Creating geeSEBAL Collection from {start_year}-{start_month:02d}-{start_day:02d} to {end_year}-{end_month:02d}-{end_day:02d}...")
    
    geeSEBAL_Collection = Collection(
        start_year, start_month, start_day,
        end_year, end_month, end_day,
        cloud_cover, geom
    )
    
    collection_et = geeSEBAL_Collection.Collection_ET
    
    if not collection_et:
        print("No valid ET bands were added to the collection.")
        return None
    
    # Transform to image collection
    bands = collection_et.bandNames().getInfo()
    image_list = []
    
    for band in bands:
        single_band_image = collection_et.select([band])
        date_str = band.split('_')[-1]
        date = ee.Date.parse('YYYYMMdd', date_str)
        single_band_image = single_band_image.set('system:time_start', date.millis())
        single_band_image = single_band_image.rename('etr')
        image_list.append(single_band_image)
    
    return ee.ImageCollection.fromImages(image_list)


def process_field_combination(gdf, image_collection, campo_value, lote_value, output_dir):
    """Process a single campo-lote combination"""
    print(f"Processing: {campo_value}-{lote_value}")
    
    # Subset the GeoDataFrame
    subset_gdf = gdf[(gdf['campo'] == campo_value) & (gdf['lote'] == lote_value)]
    
    if subset_gdf.empty:
        print(f"No data found for {campo_value}-{lote_value}")
        return False
    
    # Get field geometry
    dissolved_geometry = subset_gdf.dissolve().geometry.iloc[0]
    
    # Convert to xarray
    try:
        ds = image_collection.wx.to_xarray(
            region=dissolved_geometry.bounds,
            scale=30
        )
        
        # Process time series
        original_time_series = ds.chunk('auto')
        time_series_resampled = original_time_series.resample(time='15D').max()
        time_series_resampled.attrs = original_time_series.attrs.copy()
        time_series_interpolated = time_series_resampled.chunk(dict(time=-1)).interpolate_na('time', use_coordinate=False)
        
        # Clip to field
        subset_da = time_series_interpolated.etr.rio.clip([dissolved_geometry], subset_gdf.crs)
        
        # Save as TIFs
        save_timeseries_tifs(subset_da, campo_value, lote_value, output_dir)
        return True
        
    except Exception as e:
        print(f"Error processing {campo_value}-{lote_value}: {e}")
        return False


def save_timeseries_tifs(subset_da, campo_value, lote_value, output_dir):
    """Save time series as TIF files"""
    field_dir = os.path.join(output_dir, f"{campo_value}_{lote_value}")
    os.makedirs(field_dir, exist_ok=True)
    
    saved_count = 0
    for time in subset_da.time.values:
        image = subset_da.sel(time=time)
        image = image.transpose('y', 'x').rio.write_crs('EPSG:4326')
        
        date = np.datetime_as_string(time, unit='D')
        output_file = f'{campo_value}_{lote_value}_{date}.tif'
        output_path = os.path.join(field_dir, output_file)
        
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
            image.rio.to_raster(output_path, driver='COG')
            saved_count += 1
        except Exception as e:
            print(f"Error saving {output_file}: {e}")
    
    print(f"Saved {saved_count} TIF files for {campo_value}-{lote_value}")


def generate_field_timeseries(schema, output_dir, database_uri=None, table_name=None,
                             start_year=2024, start_month=11, start_day=1,
                             end_year=2025, end_month=4, end_day=21, cloud_cover=20):
    """
    Main function to generate time series for all fields
    
    Args:
        schema (str): Database schema name
        output_dir (str): Output directory for TIF files  
        database_uri (str): Database connection string (optional)
        table_name (str): Specific table to process (optional)
        start_year (int): Starting year for the collection
        start_month (int): Starting month for the collection
        start_day (int): Starting day for the collection
        end_year (int): Ending year for the collection
        end_month (int): Ending month for the collection
        end_day (int): Ending day for the collection
        cloud_cover (int): Maximum cloud cover percentage
    """
    # Default database URI
    if database_uri is None:
        database_uri = 'postgresql://postgres:Sinergia7@ec2-3-134-97-6.us-east-2.compute.amazonaws.com/shiny_actbiologico'
    
    # Initialize Earth Engine
    try:
        ee.Initialize(project='tercero')
    except:
        print("Please authenticate Earth Engine first: ee.Authenticate()")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get tables
    table_list, engine = load_consolidado_tables(schema, database_uri)
    
    if table_name:
        table_list = [table_name] if table_name in table_list else []
    
    if not table_list:
        print(f"No tables found for processing")
        return
    
    print(f"Processing {len(table_list)} tables: {table_list}")
    
    # Process each table
    for table in table_list:
        print(f"\n{'='*50}")
        print(f"Processing table: {table}")
        print(f"{'='*50}")
        
        # Load data
        gdf = load_table_data(table, schema, engine)
        if gdf is None:
            continue
        
        # Get geometry
        filtered_gdf, geom = get_filtered_geometry(gdf)
        if geom is None:
            continue
          # Create image collection
        image_collection = create_image_collection(
            geom, start_year, start_month, start_day,
            end_year, end_month, end_day, cloud_cover
        )
        if image_collection is None:
            continue
        
        # Get campo-lote combinations
        combinations = filtered_gdf[['campo', 'lote']].drop_duplicates()
        print(f"Found {len(combinations)} campo-lote combinations")
        
        # Process each combination
        successful = 0
        for _, row in combinations.iterrows():
            success = process_field_combination(
                filtered_gdf, image_collection, 
                row['campo'], str(row['lote']), 
                output_dir
            )
            if success:
                successful += 1
        
        print(f"Successfully processed {successful}/{len(combinations)} combinations")
    
    print(f"\nProcessing complete! Output saved to: {output_dir}")
