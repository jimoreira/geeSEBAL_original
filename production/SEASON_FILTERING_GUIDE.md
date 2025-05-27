# Season Filtering Guide

## Overview
The Field Time Series Generator now includes season filtering functionality to process only winter (inv) or summer (ver) season tables.

## Season Pattern Recognition
The tool recognizes tables with the pattern: `schema_season_consolidado`

### Winter Tables (inv)
- `carballal_inv21_consolidado`
- `carballal_inv22_consolidado` 
- `carballal_inv24_consolidado`

### Summer Tables (ver)
- `carballal_ver2122_consolidado`
- `carballal_ver2223_consolidado`
- `carballal_ver2324_consolidado`
- `carballal_ver2425_consolidado`

## Usage Examples

### Process All Summer Tables
```bash
python field_timeseries_generator.py --schema carballal --output_dir C:\Users\javie\OneDrive\CLISCO\ET --season ver
```

### Process All Winter Tables  
```bash
python field_timeseries_generator.py --schema carballal --output_dir C:\Users\javie\OneDrive\CLISCO\ET --season inv
```

### Process All Tables (No Season Filter)
```bash
python field_timeseries_generator.py --schema carballal --output_dir C:\Users\javie\OneDrive\CLISCO\ET
```

### Process with Custom Date Range and Season
```bash
python field_timeseries_generator.py --schema carballal --output_dir C:\Users\javie\OneDrive\CLISCO\ET --start_date 2024-10-01 --end_date 2025-04-30 --season ver
```

## Command Line Arguments

| Argument | Description | Options | Default |
|----------|-------------|---------|---------|
| `--season` | Filter by season | `inv` (winter), `ver` (summer) | None (all tables) |
| `--schema` | Database schema | Required | - |
| `--output_dir` | Output directory | Any valid path | `./output_tifs` |
| `--start_date` | Start date | YYYY-MM-DD format | `2024-10-01` |
| `--end_date` | End date | YYYY-MM-DD format | `2025-04-30` |
| `--table` | Specific table filter | Table name pattern | None |

## Implementation Details

### Season Filter Logic
1. **Discovery**: Tool finds all `*_consolidado` tables in the schema
2. **Filtering**: If `--season` is specified, filters tables containing `_inv` or `_ver` pattern
3. **Validation**: Warns if invalid season option is provided and proceeds without filtering
4. **Reporting**: Shows filtered table count and lists selected tables

### Sample Output
```
🌱 Season filter applied: summer (ver)
📊 Filtered from 7 to 4 tables
📋 Found 4 tables in schema 'carballal': ['carballal_ver2122_consolidado', 'carballal_ver2223_consolidado', 'carballal_ver2324_consolidado', 'carballal_ver2425_consolidado']
```

## Error Handling
- Invalid season options (`--season invalid`) display warning and process all tables
- Empty filter results show clear error message
- No matching tables found displays helpful feedback

## Integration with Existing Features
- Season filtering works with all existing optimizations
- Compatible with `--table` filter for further refinement
- Maintains collection reuse optimization within each selected table
- Full intersection checking and performance logging preserved
