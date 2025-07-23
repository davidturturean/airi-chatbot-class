#!/usr/bin/env python3
"""
Test metadata loading directly.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata import metadata_service
from src.config.settings import settings

def test_metadata_loading():
    """Test metadata loading and show debug info."""
    print("=" * 60)
    print("METADATA LOADING TEST")
    print("=" * 60)
    
    # Check Python interpreter
    print(f"\nPython executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    # Check if required packages are available
    print("\nChecking required packages:")
    packages = ['pandas', 'duckdb', 'openpyxl']
    for package in packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is NOT installed")
    
    # Check data files
    print("\nChecking data files:")
    excel_path = settings.DATA_DIR / "info_files" / "The_AI_Risk_Repository_V3_26_03_2025.xlsx"
    if excel_path.exists():
        print(f"✓ Excel file exists: {excel_path}")
        print(f"  Size: {excel_path.stat().st_size:,} bytes")
    else:
        print(f"✗ Excel file NOT FOUND: {excel_path}")
    
    # Initialize metadata service
    print("\nInitializing metadata service...")
    try:
        metadata_service.initialize(force_reload=True)
        stats = metadata_service.get_statistics()
        
        print(f"\nMetadata service statistics:")
        print(f"Total rows: {stats['total_rows']}")
        print(f"Tables: {stats.get('table_count', len(stats.get('tables', {})))}")
        
        if 'databases' in stats:
            # Old format
            for db_name, db_stats in stats['databases'].items():
                print(f"\n  {db_name}:")
                print(f"    Rows: {db_stats['row_count']}")
                print(f"    Initialized: {db_stats.get('initialized', True)}")
        elif 'tables' in stats:
            # New format
            for table_name, table_info in stats['tables'].items():
                print(f"\n  {table_name}:")
                print(f"    Rows: {table_info['row_count']}")
                print(f"    Columns: {table_info['column_count']}")
            
    except Exception as e:
        print(f"\n✗ Error initializing metadata service: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Try a simple query
    print("\n" + "=" * 60)
    print("Testing a simple query...")
    try:
        response, data = metadata_service.query("How many risks are in the database?")
        print(f"Response: {response}")
        print(f"Data returned: {len(data)} items")
        if data:
            print(f"Sample data: {data[0]}")
    except Exception as e:
        print(f"✗ Query error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_metadata_loading()