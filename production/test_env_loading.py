#!/usr/bin/env python3
"""
Test Environment Variables Loading
"""
import os

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
        return True
    else:
        print("⚠️  No .env file found. Make sure to set environment variables manually.")
        return False

def test_env_variables():
    """Test if environment variables are properly loaded"""
    print("Testing environment variable loading...")
    
    # Load .env file
    load_env_file()
    
    # Check if variables are loaded
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    
    print("\nEnvironment Variables Status:")
    print(f"DB_USER: {'✓ Set' if db_user else '❌ Missing'} {f'({db_user})' if db_user else ''}")
    print(f"DB_PASSWORD: {'✓ Set' if db_password else '❌ Missing'} {f'(length: {len(db_password)})' if db_password else ''}")
    print(f"DB_HOST: {'✓ Set' if db_host else '❌ Missing'} {f'({db_host})' if db_host else ''}")
    print(f"DB_NAME: {'✓ Set' if db_name else '❌ Missing'} {f'({db_name})' if db_name else ''}")
    
    if all([db_user, db_password, db_host, db_name]):
        # Construct database URI
        database_uri = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'
        print(f"\n✓ Database URI can be constructed:")
        print(f"postgresql://{db_user}:{'*' * len(db_password)}@{db_host}/{db_name}")
        return True
    else:
        print("\n❌ Some environment variables are missing!")
        return False

if __name__ == "__main__":
    test_env_variables()
