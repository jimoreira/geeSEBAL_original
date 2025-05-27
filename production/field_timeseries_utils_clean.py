"""
Optimized Field Time Series Generator Module

This module provides functions to generate time series images for fields
using the geeSEBAL workflow with optimized collection creation.

Key optimization: Creates the collection once per table using table bounds,
then subsets it for each individual field.
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
from datetime import datetime, timedelta

# Add parent directory to path for geeSEBAL import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etbrasil.geesebal import Collection


def load_env_file():
    """
    Load environment variables from .env file if it exists.
    
    Returns:
        bool: True if .env file was found and loaded, False otherwise
    """
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ Loaded environment variables from .env file")
        return True
    else:
        print("⚠️  No .env file found. Make sure to set environment variables manually.")
        return False


def create_database_connection():
    """
    Create a database connection using environment variables.
    
    Returns:
        sqlalchemy.Engine: Database engine for connections
        
    Raises:
        ValueError: If required environment variables are missing
    """
    # Get credentials from environment variables for security
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    
    if not db_password or not db_host or not db_name:
        raise ValueError(
            "Database credentials must be set via environment variables: "
            "DB_PASSWORD, DB_HOST, DB_NAME (DB_USER defaults to 'postgres')"
        )
    
    database_uri = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'
    
    try:
        engine = create_engine(database_uri)
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection established successfully")
        return engine
    except Exception as e:
        raise ConnectionError(f"Failed to connect to database: {e}")


def get_field_data(engine, schema_name, table_name):
    """
    Get field data from a specific table in the database.
    
    Args:
        engine: SQLAlchemy database engine
        schema_name (str): Database schema name
        table_name (str): Table name to query
        
    Returns:
        geopandas.GeoDataFrame: DataFrame with field data and geometries
    """
    query = f"""
        SELECT 
            campo,
            lote,
            ST_AsText(geom) as geometry_wkt,
            geom
        FROM {schema_name}.{table_name}
        WHERE geom IS NOT NULL
        ORDER BY campo, lote
    """
    
    try:
        # Load data using geopandas for automatic geometry handling
        gdf = gpd.read_postgis(
            query, 
            engine, 
            geom_col='geom',
            crs='EPSG:4326'  # Assuming WGS84
        )
        
        print(f"📊 Loaded {len(gdf)} records from {schema_name}.{table_name}")
        return gdf
        
    except Exception as e:
        print(f"❌ Error loading data from {schema_name}.{table_name}: {e}")
        return pd.DataFrame()


def get_table_bounds_geometry(engine, schema_name, table_name):
    """
    OPTIMIZATION: Create a bounding box geometry that encompasses all features in the table.
    
    This is the key optimization - instead of creating collections for each individual field,
    we create one collection using the bounds of the entire table.
    
    Args:
        engine: SQLAlchemy database engine
        schema_name (str): Database schema name
        table_name (str): Table name
        
    Returns:
        ee.Geometry: Earth Engine geometry representing table bounds with buffer
    """
    try:
        # Get the bounds of all geometries in the table
        query = text(f"""
            SELECT 
                ST_XMin(ST_Extent(geom)) as minx,
                ST_YMin(ST_Extent(geom)) as miny,
                ST_XMax(ST_Extent(geom)) as maxx,
                ST_YMax(ST_Extent(geom)) as maxy
            FROM {schema_name}.{table_name}
            WHERE geom IS NOT NULL
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query).fetchone()
            
        if result is None or any(x is None for x in result):
            print(f"❌ Could not get bounds for table {schema_name}.{table_name}")
            return None
            
        minx, miny, maxx, maxy = result
        
        # Add a buffer to ensure we capture edge effects (buffer in degrees ~1km)
        buffer = 0.01  
        bounds_buffered = [
            minx - buffer,  # minx
            miny - buffer,  # miny  
            maxx + buffer,  # maxx
            maxy + buffer   # maxy
        ]
        
        # Create Earth Engine rectangle geometry
        bounds_geom = ee.Geometry.Rectangle(bounds_buffered)
        
        print(f"🎯 Table bounds: [{minx:.6f}, {miny:.6f}, {maxx:.6f}, {maxy:.6f}]")
        print(f"🔧 Buffered collection area: {bounds_buffered}")
        
        return bounds_geom
        
    except Exception as e:
        print(f"❌ Error getting table bounds: {e}")
        return None


def create_image_collection(geometry, start_date, end_date):
    """
    OPTIMIZATION: Create image collection for the given geometry and date range.
    
    Returns both the collection and the bounds geometry for intersection checking.
    
    Args:
        geometry: Earth Engine geometry
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        tuple: (image_collection, collection_bounds_geom) or None if failed
    """
    try:
        print(f"🚀 Creating optimized image collection...")
        print(f"   📅 Date range: {start_date} to {end_date}")
        
        # Create the geeSEBAL collection using the provided geometry
        col = Collection(
            date_start=start_date,
            date_end=end_date,
            cloud_cover=70,
            geometry=geometry
        )
        
        # Get the Landsat collection
        landsat_collection = col.landsat_collection
        
        if landsat_collection is None:
            print("❌ Failed to create Landsat collection")
            return None
            
        # Check collection size
        collection_size = landsat_collection.size()
        
        if collection_size.getInfo() == 0:
            print("⚠️  No images found for the specified criteria")
            return None
            
        print(f"✅ Created collection with {collection_size.getInfo()} images")
        
        return (landsat_collection, geometry)
        
    except Exception as e:
        print(f"❌ Error creating image collection: {e}")
        return None


def check_geometry_intersection(field_geom, collection_bounds):
    """
    OPTIMIZATION: Check if a field geometry intersects with the collection bounds.
    
    This prevents errors when trying to process fields that don't overlap
    with the image collection coverage area.
    
    Args:
        field_geom: Shapely or GeoPandas geometry of the field
        collection_bounds: Earth Engine geometry of collection bounds
        
    Returns:
        bool: True if geometries intersect, False otherwise
    """
    try:
        # Convert field geometry to Earth Engine geometry
        if hasattr(field_geom, '__geo_interface__'):
            # GeoPandas/Shapely geometry
            field_ee_geom = ee.Geometry(field_geom.__geo_interface__)
        else:
            # Already an Earth Engine geometry
            field_ee_geom = field_geom
        
        # Check intersection
        intersection = field_ee_geom.intersects(collection_bounds, ee.ErrorMargin(1))
        return intersection.getInfo()
        
    except Exception as e:
        print(f"⚠️  Warning: Could not check geometry intersection: {e}")
        # If we can't check, assume it intersects to avoid skipping fields
        return True


def process_field_timeseries(campo, lote, geometry, image_collection, output_dir, start_date, end_date):
    """
    Process time series for a single field using the provided image collection.
    
    This function uses the OPTIMIZED approach where the image collection
    is created once and reused for all fields.
    
    Args:
        campo (str): Campo (field) identifier
        lote (str): Lote (plot) identifier  
        geometry: Field geometry
        image_collection: Pre-created Earth Engine image collection
        output_dir (Path): Output directory for TIF files
        start_date (str): Start date
        end_date (str): End date
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert geometry to Earth Engine format
        if hasattr(geometry, '__geo_interface__'):
            ee_geom = ee.Geometry(geometry.__geo_interface__)
        else:
            ee_geom = geometry
            
        # Create geeSEBAL collection instance for this field
        # Note: We're reusing the image_collection instead of creating a new one
        field_col = Collection(
            date_start=start_date,
            date_end=end_date,
            cloud_cover=70,
            geometry=ee_geom
        )
        
        # Override the collection with our pre-created one
        field_col.landsat_collection = image_collection.filterBounds(ee_geom)
        
        # Check if there are images for this field
        field_collection_size = field_col.landsat_collection.size().getInfo()
        
        if field_collection_size == 0:
            print(f"⚠️  No images found for field {campo}_{lote}")
            return False
            
        print(f"📊 Processing {field_collection_size} images for field {campo}_{lote}")
        
        # Process the timeseries  
        field_col.get_timeseries()
        
        # Create output directory for this field
        field_output_dir = output_dir / f"{campo}_{lote}"
        field_output_dir.mkdir(exist_ok=True)
        
        # Export each image in the timeseries
        timeseries_info = field_col.timeseries.getInfo()
        
        for i, image_info in enumerate(timeseries_info.get('features', [])):
            date_str = image_info['properties'].get('date', f'image_{i}')
            
            # Clean up date string for filename
            if isinstance(date_str, str) and len(date_str) >= 10:
                clean_date = date_str[:10]  # Take first 10 chars (YYYY-MM-DD)
            else:
                clean_date = f"image_{i}"
                
            filename = f"{campo}_{lote}_{clean_date}.tif"
            filepath = field_output_dir / filename
            
            # Get the image for this date
            image = field_col.timeseries.filter(ee.Filter.eq('date', date_str)).first()
            
            if image:
                # Export the image
                geemap.ee_export_image(
                    image.select(['ET']),  # Export ET band
                    filename=str(filepath),
                    scale=30,
                    region=ee_geom,
                    file_per_band=False
                )
                
        print(f"✅ Exported timeseries for {campo}_{lote} to {field_output_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing field {campo}_{lote}: {e}")
        return False
