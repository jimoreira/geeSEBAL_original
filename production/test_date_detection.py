"""
Test script to verify intelligent date range detection functionality.
"""

# Mock the FieldTimeSeriesGenerator class to test just the date detection
class TestDateDetection:
    
    def __init__(self, season_config=None):
        """Initialize with configurable seasonal settings."""
        # Default configurable seasonal settings
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


def test_date_detection():
    """Test the date detection functionality with various table name patterns and configurations."""
    
    print("🧪 TESTING INTELLIGENT DATE RANGE DETECTION")
    print("=" * 60)
    
    # Test cases
    test_tables = [
        "carballal_ver2122_consolidado",  # Summer 2021-2022
        "carballal_inv21_consolidado",    # Winter 2021
        "esquema_ver2425_consolidado",    # Summer 2024-2025
        "esquema_inv22_consolidado",      # Winter 2022
        "carballal_ver1920_consolidado",  # Summer 2019-2020
        "carballal_inv25_consolidado",    # Winter 2025
        "invalid_table_name",             # No pattern
        "another_consolidado_table"       # No season pattern
    ]
    
    # TEST 1: Default configuration
    print("\n📊 TEST 1: DEFAULT CONFIGURATION")
    print("🌞 Summer: Dec-Mar | ❄️ Winter: Jun-Sep")
    print("-" * 40)
    
    detector = TestDateDetection()
    
    for i, table_name in enumerate(test_tables, 1):
        print(f"\n📊 Test 1.{i}: {table_name}")
        start_date, end_date = detector.extract_date_range_from_table(table_name)
        
        if start_date and end_date:
            print(f"✅ SUCCESS: {start_date} to {end_date}")
        else:
            print(f"⚠️  NO PATTERN DETECTED: Will use provided dates")
    
    # TEST 2: Custom configuration
    print(f"\n\n📊 TEST 2: CUSTOM CONFIGURATION")
    print("🌞 Summer: Oct-Feb | ❄️ Winter: Apr-Aug")
    print("-" * 40)
    
    custom_config = {
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
    
    custom_detector = TestDateDetection(season_config=custom_config)
    
    # Test a few examples with custom config
    custom_test_tables = [
        "carballal_ver2122_consolidado",  # Should use Oct 2021 - Feb 2022
        "carballal_inv21_consolidado",    # Should use Apr 2021 - Aug 2021
    ]
    
    for i, table_name in enumerate(custom_test_tables, 1):
        print(f"\n📊 Test 2.{i}: {table_name}")
        start_date, end_date = custom_detector.extract_date_range_from_table(table_name)
        
        if start_date and end_date:
            print(f"✅ SUCCESS: {start_date} to {end_date}")
        else:
            print(f"⚠️  NO PATTERN DETECTED: Will use provided dates")
    
    print("\n" + "=" * 60)
    print("🎉 Date detection testing complete!")
    print("💡 Key Benefits:")
    print("   ✅ Auto-detects YEARS from table names (ver2122 → 2021-2022)")
    print("   ⚙️  Uses configurable MONTHS/DAYS from season settings")
    print("   🔧 Fully customizable for different agricultural regions")
    print("   📅 No more hardcoded dates - you control the seasonal periods!")


if __name__ == "__main__":
    test_date_detection()
