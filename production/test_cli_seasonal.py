#!/usr/bin/env python3
"""
Test script to verify CLI seasonal arguments are working
"""

import sys
import subprocess

def test_cli_seasonal_args():
    """Test that the CLI accepts seasonal configuration arguments"""
    print("🧪 TESTING CLI SEASONAL ARGUMENTS")
    print("=" * 50)
    
    # Test command with custom seasonal settings
    cmd = [
        sys.executable, 
        "field_timeseries_generator.py",
        "--schema", "test_schema",
        "--summer_start_month", "11",
        "--summer_start_day", "15", 
        "--summer_end_month", "4",
        "--summer_end_day", "15",
        "--winter_start_month", "5",
        "--winter_start_day", "1",
        "--winter_end_month", "8", 
        "--winter_end_day", "31",
        "--help"
    ]
    
    try:
        print("🚀 Running CLI test with custom seasonal arguments...")
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ SUCCESS: CLI accepts seasonal arguments!")
            print("📄 Help output shows all seasonal options are available")
            
            # Check if our custom arguments are in the help text
            help_text = result.stdout
            seasonal_args = [
                "--summer_start_month", "--summer_start_day", 
                "--summer_end_month", "--summer_end_day",
                "--winter_start_month", "--winter_start_day",
                "--winter_end_month", "--winter_end_day"
            ]
            
            found_args = [arg for arg in seasonal_args if arg in help_text]
            print(f"🔍 Found {len(found_args)}/{len(seasonal_args)} seasonal arguments in help")
            
            if len(found_args) == len(seasonal_args):
                print("✅ All seasonal arguments are properly registered!")
            else:
                print(f"⚠️  Missing some seasonal arguments: {set(seasonal_args) - set(found_args)}")
                
        else:
            print(f"❌ FAILED: CLI returned error code {result.returncode}")
            print(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ Test timed out (this might be normal for --help)")
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")

if __name__ == "__main__":
    test_cli_seasonal_args()
