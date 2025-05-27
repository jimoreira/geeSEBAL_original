# Configurable Seasonal Date Detection Guide

## Overview

The Field Time Series Generator now includes **configurable seasonal date detection** that allows you to:

1. **Auto-detect years** from table names (e.g., `ver2122` → 2021-2022)
2. **Configure months and days** for each season according to your agricultural region
3. **Customize seasonal periods** via command-line arguments or configuration

## Key Features

### ✅ Flexible Year Detection
- Automatically extracts years from table name patterns
- Summer: `ver2122` → years 2021-2022
- Winter: `inv21` → year 2021

### ⚙️ Configurable Seasonal Periods
- You control the start/end months and days
- Different regions can use different seasonal calendars
- No more hardcoded December-March for summer!

### 🔧 Multiple Configuration Methods
- Command-line arguments for quick customization
- Configuration objects for programmatic use
- Sensible defaults for common agricultural seasons

## Usage Examples

### Example 1: Default Configuration (Southern Hemisphere)
```bash
python field_timeseries_generator.py --schema carballal --season ver
```

**Default Summer Settings:**
- Start: December 1st (year 1)  
- End: March 31st (year 2)
- `ver2122` → 2021-12-01 to 2022-03-31

**Default Winter Settings:**
- Start: June 1st
- End: September 30th  
- `inv21` → 2021-06-01 to 2021-09-30

### Example 2: Custom Seasonal Configuration
```bash
python field_timeseries_generator.py \
  --schema carballal \
  --season ver \
  --summer_start_month 10 --summer_start_day 15 \
  --summer_end_month 2 --summer_end_day 28 \
  --winter_start_month 4 --winter_start_day 10 \
  --winter_end_month 8 --winter_end_day 20
```

**Custom Configuration Results:**
- `ver2122` → 2021-10-15 to 2022-02-28 (custom summer)
- `inv21` → 2021-04-10 to 2021-08-20 (custom winter)

### Example 3: Northern Hemisphere Configuration
```bash
python field_timeseries_generator.py \
  --schema northern_farm \
  --season ver \
  --summer_start_month 6 --summer_start_day 1 \
  --summer_end_month 8 --summer_end_day 31 \
  --winter_start_month 12 --winter_start_day 1 \
  --winter_end_month 2 --winter_end_day 28
```

## Command Line Arguments

### Seasonal Configuration Options

| Argument | Description | Default | Range |
|----------|-------------|---------|-------|
| `--summer_start_month` | Summer season start month | 12 (December) | 1-12 |
| `--summer_start_day` | Summer season start day | 1 | 1-31 |
| `--summer_end_month` | Summer season end month | 3 (March) | 1-12 |
| `--summer_end_day` | Summer season end day | 31 | 1-31 |
| `--winter_start_month` | Winter season start month | 6 (June) | 1-12 |
| `--winter_start_day` | Winter season start day | 1 | 1-31 |
| `--winter_end_month` | Winter season end month | 9 (September) | 1-12 |
| `--winter_end_day` | Winter season end day | 30 | 1-31 |

### Core Arguments (Unchanged)

| Argument | Description | Default |
|----------|-------------|---------|
| `--schema` | Database schema name | Required |
| `--output_dir` | Output directory | `./output_tifs` |
| `--start_date` | Fallback start date | `2024-10-01` |
| `--end_date` | Fallback end date | `2025-04-30` |
| `--season` | Season filter | None (all tables) |
| `--table` | Table filter | None (all tables) |

## Console Output

The system provides clear feedback about the configuration being used:

### Default Configuration
```
🚀 Starting OPTIMIZED Field Time Series Generation
📂 Schema: carballal
📅 Date Range: 2024-10-01 to 2025-04-30

🌞 Detected summer season 2021-2022
📅 Auto-detected date range: 2021-12-01 to 2022-03-31
⚙️  Using summer config: 12/1 to 3/31
✅ Using auto-detected dates for table 'carballal_ver2122_consolidado'
```

### Custom Configuration  
```
⚙️  CUSTOM SEASONAL CONFIGURATION:
   🌞 Summer: 10/15 to 2/28
   ❄️  Winter: 4/10 to 8/20

🌞 Detected summer season 2021-2022  
📅 Auto-detected date range: 2021-10-15 to 2022-02-28
⚙️  Using summer config: 10/15 to 2/28
✅ Using auto-detected dates for table 'carballal_ver2122_consolidado'
```

## Programmatic Usage

### Using Custom Season Configuration in Code

```python
from field_timeseries_generator import FieldTimeSeriesGenerator

# Define custom seasonal periods
custom_seasons = {
    'summer': {
        'start_month': 10,  # October
        'start_day': 15,
        'end_month': 2,     # February  
        'end_day': 28,
        'span_years': True  # Summer spans two years
    },
    'winter': {
        'start_month': 4,   # April
        'start_day': 10, 
        'end_month': 8,     # August
        'end_day': 20,
        'span_years': False # Winter stays in same year
    }
}

# Initialize with custom configuration
generator = FieldTimeSeriesGenerator(
    schema_name="carballal",
    output_dir="./output_custom",
    season_config=custom_seasons
)

# Run with automatic date detection
generator.generate_time_series(
    start_date="2024-10-01",  # Fallback if no pattern detected
    end_date="2025-04-30",    # Fallback if no pattern detected
    season_filter="ver"
)
```

## Regional Adaptations

### Southern Hemisphere (Default)
- **Summer**: December - March (spans years)
- **Winter**: June - September (same year)
- Suitable for: Argentina, Uruguay, Southern Brazil, Australia, etc.

### Northern Hemisphere
```bash
--summer_start_month 6 --summer_end_month 8    # Jun-Aug
--winter_start_month 12 --winter_end_month 2   # Dec-Feb  
```

### Mediterranean Climate
```bash
--summer_start_month 5 --summer_end_month 9    # May-Sep
--winter_start_month 11 --winter_end_month 3   # Nov-Mar
```

### Tropical Climate
```bash
--summer_start_month 11 --summer_end_month 4   # Wet season
--winter_start_month 5 --winter_end_month 10   # Dry season
```

## Benefits

### 🎯 Accurate Date Matching
- No more mismatched dates between table names and satellite imagery
- `ver2122` tables now correctly use 2021-2022 dates instead of 2024-2025

### 🌍 Regional Flexibility  
- Adapt to any agricultural calendar worldwide
- Support for different hemisphere conventions
- Customizable seasonal boundaries

### 🔧 Easy Configuration
- Command-line arguments for quick changes
- Programmatic configuration for complex workflows
- Sensible defaults require no configuration

### ⚡ Performance Maintained
- All optimization benefits preserved
- Single collection creation per table
- Intelligent intersection checking

## Testing

Test your configuration with the test script:

```bash
python test_date_detection.py
```

This will show how your table names are interpreted with both default and custom configurations.

## Compatibility

- ✅ **Backward Compatible**: Works with existing table naming conventions
- ✅ **Season Filtering**: Compatible with `--season inv/ver` arguments  
- ✅ **Optimization**: Maintains all performance improvements
- ✅ **Fallback Support**: Uses provided dates if no pattern matches

---

**Note**: The intelligent date detection ensures your satellite imagery collections are created for the correct time periods, matching the actual agricultural seasons represented in your database tables, while giving you full control over what those seasonal periods actually are for your specific region.
