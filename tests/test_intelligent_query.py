#!/usr/bin/env python3
"""
Test intelligent query routing without hardcoded table names.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata import metadata_service
from src.config.settings import settings

def test_intelligent_queries():
    """Test that the system can understand queries without knowing table names."""
    print("=" * 80)
    print("TESTING INTELLIGENT QUERY ROUTING")
    print("=" * 80)
    
    # First load the Excel file
    excel_path = settings.DATA_DIR / "info_files" / "The_AI_Risk_Repository_V3_26_03_2025.xlsx"
    print(f"\nLoading Excel file: {excel_path}")
    results = metadata_service.load_file(str(excel_path))
    
    print(f"\nLoaded tables:")
    for table, count in results.items():
        print(f"  - {table}: {count} rows")
    
    # Test queries that should work WITHOUT knowing table names
    test_queries = [
        # Risk-related queries
        ("How many risks are in the database?", "Should count risk entries"),
        ("What are the main risk categories?", "Should find distinct categories"),
        ("List all domains in the repository", "Should show domain values"),
        ("Show me risks from domain 1", "Should filter by domain"),
        
        # Statistical queries
        ("How many entries in the statistics?", "Should find stats tables"),
        ("What's in the changelog?", "Should find change log"),
        
        # General queries
        ("How many total records are there?", "Should count all data"),
        ("What tables are available?", "Should list tables"),
        ("Show me some data", "Should return sample data"),
    ]
    
    print("\n" + "=" * 80)
    print("QUERY TESTS")
    print("=" * 80)
    
    for query, expected in test_queries:
        print(f"\n🔍 Query: {query}")
        print(f"📋 Expected: {expected}")
        
        try:
            response, data = metadata_service.query(query)
            
            # Show response
            print(f"✅ Response: {response[:200]}...")
            
            # Show data info
            if data:
                print(f"📊 Data: {len(data)} results")
                if len(data) > 0:
                    # Show first result structure
                    first_item = data[0]
                    print(f"   Columns: {list(first_item.keys())}")
            else:
                print("📊 Data: No results")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 80)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_intelligent_queries()