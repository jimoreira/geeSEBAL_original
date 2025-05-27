# Field Time Series Generator

This tool automatically generates time series images for each field (campo and lote) combination from a PostGIS database using geeSEBAL and Google Earth Engine.

## Files in Production Directory

1. **`field_timeseries_generator.py`** - Complete standalone script with command-line interface
2. **`field_timeseries_utils.py`** - Module with reusable functions  
3. **`example_usage.py`** - Examples showing how to use the utilities
4. **`README.md`** - This documentation file

## Prerequisites

- Earth Engine authentication: `ee.Authenticate()`
- Required Python packages: `sqlalchemy`, `pandas`, `geopandas`, `geemap`, `wxee`, `ee`, `numpy`
- Access to the PostGIS database
- geeSEBAL library properly installed in parent directory

## Usage Options

### Option 1: Command Line Script

```bash
# Process all tables in a schema with default dates (Nov 2024 - Apr 2025)
python field_timeseries_generator.py --schema carballal --output_dir ./output_tifs

# Process with custom date range
python field_timeseries_generator.py --schema carballal --output_dir ./output_tifs --start_year 2023 --start_month 6 --start_day 1 --end_year 2024 --end_month 12 --end_day 31

# Process a specific table with custom cloud cover
python field_timeseries_generator.py --schema carballal --table your_table_consolidado --output_dir ./output_tifs --cloud_cover 15

# Process for summer season only
python field_timeseries_generator.py --schema carballal --output_dir ./output_summer --start_year 2024 --start_month 12 --start_day 1 --end_year 2025 --end_month 3 --end_day 31

# Use custom database URI
python field_timeseries_generator.py --schema carballal --output_dir ./output_tifs --database_uri "your_connection_string"
```

### Option 2: Python Module

```python
from field_timeseries_utils import generate_field_timeseries
import ee

# Initialize Earth Engine
ee.Initialize(project='tercero')

# Process all tables with default dates
generate_field_timeseries(
    schema='carballal',
    output_dir='./output_tifs'
)

# Process with custom date range
generate_field_timeseries(
    schema='carballal',
    output_dir='./output_custom_dates',
    start_year=2023,
    start_month=6, 
    start_day=1,
    end_year=2024,
    end_month=12,
    end_day=31,
    cloud_cover=15
)

# Process specific table for seasonal analysis
generate_field_timeseries(
    schema='carballal', 
    output_dir='./output_summer',
    table_name='specific_table_consolidado',
    start_year=2024,
    start_month=12,  # Summer season
    start_day=1,
    end_year=2025,
    end_month=3,
    end_day=31
)
```

## How It Works

1. **Database Query**: Finds all tables ending with `_consolidado` in the specified schema
2. **Data Loading**: Loads spatial data and filters by valid `fecha_siembra` values
3. **Geometry Processing**: Converts GeoDataFrames to Earth Engine geometries
4. **Collection Creation**: Creates geeSEBAL ET collections filtered by the geometry
5. **Time Series Processing**: Converts to xarray datasets and processes time series
6. **Field Processing**: For each campo-lote combination:
   - Clips the time series to the field boundary
   - Resamples and interpolates the data
   - Saves each time step as a separate TIF file

## Output Structure

```
output_dir/
├── campo1_lote1/
│   ├── campo1_lote1_2024-11-01.tif
│   ├── campo1_lote1_2024-11-16.tif
│   └── ...
├── campo1_lote2/
│   ├── campo1_lote2_2024-11-01.tif
│   └── ...
└── campo2_lote1/
    └── ...
```

## Configuration

Default parameters:
- **Time period**: Nov 1, 2024 to Apr 21, 2025 (customizable)
- **Cloud cover**: 20% (customizable)
- **Resampling**: 15-day intervals
- **Scale**: 30m resolution
- **Output format**: Cloud Optimized GeoTIFF (COG)

### Available Command Line Parameters

- `--start_year`: Starting year (default: 2024)
- `--start_month`: Starting month (default: 11) 
- `--start_day`: Starting day (default: 1)
- `--end_year`: Ending year (default: 2025)
- `--end_month`: Ending month (default: 4)
- `--end_day`: Ending day (default: 21)
- `--cloud_cover`: Maximum cloud cover percentage (default: 20)

You can modify these parameters either via command line arguments or by passing them to the Python functions.

## Import Structure

The production directory uses relative imports to access the geeSEBAL library:

```python
# Add parent directory to path for geeSEBAL import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etbrasil.geesebal import Collection
```

This allows the tools to work from the production subdirectory while maintaining access to the geeSEBAL library in the parent directory.

## Error Handling

The tool includes comprehensive error handling:
- Skips empty tables or invalid geometries
- Continues processing other fields if one fails
- Provides detailed logging of progress and errors
- Creates output directories automatically

## Troubleshooting

1. **Earth Engine Authentication**: Run `ee.Authenticate()` before using the tools
2. **Database Connection**: Ensure you have access to the PostGIS database
3. **Import Errors**: Ensure geeSEBAL library is available in the parent directory
4. **Memory Issues**: Large datasets may require adjusting chunk sizes in xarray operations
5. **Geometry Errors**: Invalid geometries are automatically skipped with warnings

## Performance Tips

- Process specific tables instead of all tables for faster execution
- Use smaller date ranges for testing
- Monitor memory usage for large datasets
- Consider running on machines with more RAM for extensive processing

## Examples

See `example_usage.py` for detailed examples including:
- Processing all tables with default settings
- Custom date ranges for specific seasons
- Processing individual tables
- Different cloud cover thresholds
