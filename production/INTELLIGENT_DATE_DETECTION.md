# Intelligent Date Range Detection

## Overview

The optimized field time series generator now includes **intelligent date range detection** that automatically extracts appropriate date ranges from table names, eliminating the mismatch between table seasons and image collection dates.

## Features

### Automatic Season Detection

The system automatically detects seasonal patterns in table names and uses appropriate date ranges:

- **Summer Tables** (`ver2122`, `ver2425`, etc.)
  - Pattern: `_ver[YY][YY]_` (e.g., `carballal_ver2122_consolidado`)
  - Date Range: December of first year to March of second year
  - Example: `ver2122` → December 2021 to March 2022

- **Winter Tables** (`inv21`, `inv22`, etc.)
  - Pattern: `_inv[YY]_` (e.g., `carballal_inv21_consolidado`)
  - Date Range: June to September of the same year
  - Example: `inv21` → June 2021 to September 2021

### Smart Fallback

If no seasonal pattern is detected in the table name, the system falls back to using the provided command-line date range arguments.

## Usage Examples

### Example 1: Summer Season Detection
```bash
python field_timeseries_generator.py --schema carballal --season ver
```

For table `carballal_ver2122_consolidado`:
- **Auto-detected**: December 1, 2021 to March 31, 2022
- **Previously used**: 2024-11-01 to 2025-04-21 ❌

### Example 2: Winter Season Detection
```bash
python field_timeseries_generator.py --schema carballal --season inv
```

For table `carballal_inv21_consolidado`:
- **Auto-detected**: June 1, 2021 to September 30, 2021
- **Previously used**: 2024-11-01 to 2025-04-21 ❌

### Example 3: Mixed Seasons
```bash
python field_timeseries_generator.py --schema carballal
```

The system will process all tables and automatically detect dates for each:
- `carballal_ver2122_consolidado` → Dec 2021 - Mar 2022
- `carballal_inv21_consolidado` → Jun 2021 - Sep 2021
- `carballal_ver2425_consolidado` → Dec 2024 - Mar 2025

## Implementation Details

### Date Pattern Recognition

The system uses regular expressions to identify seasonal patterns:

```python
# Summer pattern: _ver[YY][YY]_
summer_match = re.search(r'_ver(\d{2})(\d{2})_', table_name.lower())

# Winter pattern: _inv[YY]_
winter_match = re.search(r'_inv(\d{2})_', table_name.lower())
```

### Automatic Date Calculation

```python
# Summer: December year1 to March year2
if summer_match:
    year1 = int("20" + summer_match.group(1))  # 21 → 2021
    year2 = int("20" + summer_match.group(2))  # 22 → 2022
    start_date = f"{year1}-12-01"              # 2021-12-01
    end_date = f"{year2}-03-31"                # 2022-03-31

# Winter: June to September same year
if winter_match:
    year = int("20" + winter_match.group(1))   # 21 → 2021
    start_date = f"{year}-06-01"               # 2021-06-01
    end_date = f"{year}-09-30"                 # 2021-09-30
```

## Benefits

### 1. Eliminates Date Mismatches
- **Before**: All tables used 2024-2025 dates regardless of actual season
- **After**: Each table uses its correct historical date range

### 2. Accurate Satellite Data
- Ensures Google Earth Engine collections match the agricultural season
- Prevents empty or irrelevant image collections

### 3. Automated Workflow
- No manual date calculation required
- Reduces human error in date selection
- Supports batch processing of multiple seasons

## Console Output

The system provides clear feedback about date detection:

```
🌞 Detected summer season 2021-2022
📅 Auto-detected date range: 2021-12-01 to 2022-03-31
✅ Using auto-detected dates for table 'carballal_ver2122_consolidado'

❄️ Detected winter season 2021
📅 Auto-detected date range: 2021-06-01 to 2021-09-30
✅ Using auto-detected dates for table 'carballal_inv21_consolidado'

⚠️  Could not extract date range from table name: custom_table_name
   Using provided date range instead
```

## Configuration

The intelligent date detection is enabled by default but can be controlled:

```python
# Enable automatic date detection (default)
self.process_table_optimized(table_name, start_date, end_date, auto_detect_dates=True)

# Disable to always use provided dates
self.process_table_optimized(table_name, start_date, end_date, auto_detect_dates=False)
```

## Compatibility

- **Compatible with**: All existing table naming conventions
- **Backward compatible**: Falls back to provided dates if no pattern matches
- **Season filtering**: Works seamlessly with `--season` parameter
- **Optimization**: Maintains all performance improvements

## Testing

Test the date detection with various patterns:

```python
# Test cases
tables = [
    "carballal_ver2122_consolidado",  # → 2021-12-01 to 2022-03-31
    "carballal_inv21_consolidado",    # → 2021-06-01 to 2021-09-30
    "esquema_ver2425_consolidado",    # → 2024-12-01 to 2025-03-31
    "custom_table_name"               # → Uses provided dates
]
```

This feature ensures that satellite imagery collections are created for the correct time periods, matching the actual agricultural seasons represented in your database tables.
