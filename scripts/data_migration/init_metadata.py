#!/usr/bin/env python3
"""
Initialize metadata service and load data.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata import metadata_service
from src.config.logging import get_logger

logger = get_logger(__name__)

def main():
    """Initialize metadata service with data."""
    print("🚀 Initializing metadata service...")
    
    try:
        # Force reload to ensure fresh data
        metadata_service.initialize(force_reload=True)
        
        # Get statistics
        stats = metadata_service.get_statistics()
        
        print("\n✅ Metadata service initialized successfully!")
        print(f"\nStatistics:")
        print(f"- Total databases: {len(stats['databases'])}")
        print(f"- Total rows: {stats['total_rows']}")
        
        for db_name, db_stats in stats['databases'].items():
            print(f"\nDatabase: {db_name}")
            print(f"  - Table: {db_stats['table_name']}")
            print(f"  - Rows: {db_stats['row_count']}")
            print(f"  - ID Prefix: {db_stats['id_prefix']}")
            
    except Exception as e:
        print(f"\n❌ Error initializing metadata service: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())