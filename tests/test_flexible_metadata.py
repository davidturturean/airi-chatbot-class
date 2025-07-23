#!/usr/bin/env python3
"""
Test the new flexible metadata system.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata import metadata_service
from src.config.settings import settings

def test_flexible_loading():
    """Test loading various file formats."""
    print("=" * 80)
    print("TESTING FLEXIBLE METADATA SYSTEM")
    print("=" * 80)
    
    # Check Python and packages
    print(f"\nPython: {sys.executable}")
    print(f"Version: {sys.version}")
    
    # Initialize metadata service
    print("\n1. Initializing metadata service...")
    try:
        metadata_service.initialize(force_reload=True)
        print("✓ Metadata service initialized")
        
        # Get statistics
        stats = metadata_service.get_statistics()
        print(f"\nLoaded Statistics:")
        print(f"  Total rows: {stats['total_rows']}")
        print(f"  Total tables: {stats['table_count']}")
        
        # Show loaded tables
        print(f"\nLoaded Tables:")
        for table_name, table_info in stats['tables'].items():
            print(f"  - {table_name}:")
            print(f"    Rows: {table_info['row_count']}")
            print(f"    Columns: {table_info['column_count']}")
            print(f"    Fields: {', '.join(table_info['columns'][:5])}")
            if len(table_info['columns']) > 5:
                print(f"            ... and {len(table_info['columns']) - 5} more")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Test queries
    print("\n" + "=" * 80)
    print("2. Testing Queries")
    print("=" * 80)
    
    test_queries = [
        "How many rows are in the database?",
        "Show all tables",
        "Count rows in ai_risk_database_v3",
        "What columns are in the first table?",
        "Show me data from any table with 'risk' in the name"
    ]
    
    for query in test_queries:
        print(f"\n📍 Query: {query}")
        try:
            response, data = metadata_service.query(query)
            print(f"Response: {response}")
            if data:
                print(f"Data points: {len(data)}")
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    # Test loading a specific file
    print("\n" + "=" * 80)
    print("3. Testing Direct File Loading")
    print("=" * 80)
    
    # Try to load a CSV if exists
    csv_path = settings.DATA_DIR / "test.csv"
    if csv_path.exists():
        print(f"\nLoading CSV: {csv_path}")
        results = metadata_service.load_file(str(csv_path))
        print(f"Results: {results}")
    
    # Create a test markdown file
    test_md = settings.DATA_DIR / "test_flexible.md"
    with open(test_md, 'w') as f:
        f.write("""# Test Document

## Section 1
This is a test section with some content.

| ID | Name | Value |
|----|------|-------|
| 1  | Test | 100   |
| 2  | Demo | 200   |

## Key-Value Data
RID-001: First risk item
RID-002: Second risk item
Category: Testing
Status: Active
""")
    
    print(f"\nLoading Markdown: {test_md}")
    results = metadata_service.load_file(str(test_md))
    print(f"Results: {results}")
    
    # Clean up
    test_md.unlink()
    
    # Final stats
    print("\n" + "=" * 80)
    final_stats = metadata_service.get_statistics()
    print(f"Final Statistics:")
    print(f"  Total tables: {final_stats['table_count']}")
    print(f"  Total rows: {final_stats['total_rows']}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_flexible_loading()