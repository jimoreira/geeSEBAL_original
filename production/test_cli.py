#!/usr/bin/env python3
"""
Test script to verify the command-line interface is working
"""

import subprocess
import sys

def test_cli():
    """Test the command-line interface of field_timeseries_generator.py"""
    try:
        # Test help command
        result = subprocess.run([
            sys.executable, 
            'field_timeseries_generator.py', 
            '--help'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Command-line interface is working")
            print("Available options:")
            help_lines = result.stdout.split('\n')
            for line in help_lines:
                if line.strip().startswith('--'):
                    print(f"  {line.strip()}")
        else:
            print("✗ Command-line interface has issues")
            print("Error:", result.stderr)
            
    except Exception as e:
        print(f"✗ Error testing CLI: {e}")

if __name__ == "__main__":
    test_cli()
