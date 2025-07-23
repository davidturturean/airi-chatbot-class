#!/usr/bin/env python3
"""
Simple test to check initialization.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata.metadata_service_v2 import flexible_metadata_service

print("Starting initialization...")
flexible_metadata_service.initialize(force_reload=True)
print("Done!")

# Show statistics
stats = flexible_metadata_service.get_statistics()
print(f"\nLoaded {stats['table_count']} tables with {stats['total_rows']} total rows")
for table_name, info in list(stats['tables'].items())[:5]:
    print(f"  {table_name}: {info['row_count']} rows")