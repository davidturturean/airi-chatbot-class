#!/usr/bin/env python3
"""
Test Excel loading specifically.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata import metadata_service
from src.config.settings import settings

def test_excel_loading():
    """Test loading the AI Risk Repository Excel file."""
    print("=" * 80)
    print("TESTING EXCEL LOADING")
    print("=" * 80)
    
    excel_path = settings.DATA_DIR / "info_files" / "The_AI_Risk_Repository_V3_26_03_2025.xlsx"
    
    if not excel_path.exists():
        print(f"Excel file not found: {excel_path}")
        return
    
    print(f"\nLoading Excel file: {excel_path}")
    print(f"File size: {excel_path.stat().st_size:,} bytes")
    
    # Load just this file
    print("\nLoading file...")
    results = metadata_service.load_file(str(excel_path))
    
    print(f"\nResults:")
    for table_name, row_count in results.items():
        print(f"  - {table_name}: {row_count} rows")
    
    # Get overall statistics
    stats = metadata_service.get_statistics()
    print(f"\nTotal Statistics:")
    print(f"  Tables: {stats['table_count']}")
    print(f"  Total Rows: {stats['total_rows']}")
    
    # Show details of AI Risk Database table
    print("\n" + "=" * 80)
    print("AI Risk Database Table Details")
    print("=" * 80)
    
    # Find the AI risk database table
    ai_risk_table = None
    for table_name in stats['tables']:
        if 'ai_risk_database' in table_name.lower():
            ai_risk_table = table_name
            break
    
    if ai_risk_table:
        table_info = metadata_service.describe_table(ai_risk_table)
        print(f"\nTable: {ai_risk_table}")
        print(f"Rows: {table_info['row_count']}")
        print(f"Columns ({len(table_info['columns'])}):")
        
        # Show first 10 columns
        for i, (col_name, col_type) in enumerate(list(table_info['columns'].items())[:10]):
            print(f"  {i+1}. {col_name} ({col_type})")
        
        if len(table_info['columns']) > 10:
            print(f"  ... and {len(table_info['columns']) - 10} more columns")
    
    # Test a simple query
    print("\n" + "=" * 80)
    print("Testing Queries")
    print("=" * 80)
    
    queries = [
        f"How many rows in {ai_risk_table or 'the database'}?",
        "What tables were loaded?",
        "Show me 5 rows from any table"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        try:
            response, data = metadata_service.query(query)
            print(f"Response: {response[:200]}...")
            if data:
                print(f"Data returned: {len(data)} items")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_excel_loading()