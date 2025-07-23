#!/usr/bin/env python3
"""
Test simple query on loaded data.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata import metadata_service

# Initialize
print("Initializing metadata service...")
metadata_service.initialize(force_reload=True)

# Get table info
stats = metadata_service.get_statistics()
print(f"\nLoaded {stats['total_rows']} rows across {stats['table_count']} tables")

# Show tables
print("\nTables:")
for table_name in metadata_service.list_tables():
    table_info = metadata_service.describe_table(table_name)
    print(f"  - {table_name}: {table_info.get('row_count', 0)} rows")

# Try direct SQL query
print("\nTesting direct SQL query...")
try:
    result = metadata_service.loader.execute_query("SELECT COUNT(*) as total FROM change_log")
    print(f"Direct query result: {result.fetchone()}")
except Exception as e:
    print(f"Error: {e}")

# Find AI risk database table
ai_table = None
for table_name in metadata_service.list_tables():
    if 'ai_risk' in table_name and 'v3' in table_name:
        ai_table = table_name
        break

if ai_table:
    print(f"\nFound AI risk table: {ai_table}")
    try:
        result = metadata_service.loader.execute_query(f"SELECT COUNT(*) FROM {ai_table}")
        count = result.fetchone()[0]
        print(f"Rows in {ai_table}: {count}")
    except Exception as e:
        print(f"Error querying {ai_table}: {e}")