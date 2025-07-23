#!/usr/bin/env python3
"""
Debug DuckDB loading process.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from src.core.metadata.file_handlers.excel_handler import ExcelHandler
from src.core.metadata.dynamic_schema import DynamicSchema
import duckdb

# Test with the AI Risk Database sheet
excel_path = Path("data/info_files/The_AI_Risk_Repository_V3_26_03_2025.xlsx")
handler = ExcelHandler()
datasets = handler.extract_data(excel_path)

# Find AI Risk Database
ai_risk_data = None
for dataset in datasets:
    if dataset['table_name'] == 'ai_risk_database_v3':
        ai_risk_data = dataset
        break

if not ai_risk_data:
    print("AI Risk Database not found!")
    sys.exit(1)

print(f"Found AI Risk Database with {len(ai_risk_data['data'])} rows")

# Test schema detection
data = ai_risk_data['data']
schema_dict = handler.detect_schema(data)

print(f"\nDetected schema:")
for col, dtype in list(schema_dict.items())[:10]:
    print(f"  {col}: {dtype}")

# Test dynamic schema creation
schema = DynamicSchema('test_table', schema_dict, data[:100])
create_sql = schema.get_create_table_sql()
print(f"\nGenerated SQL:")
print(create_sql)

# Test actual loading
conn = duckdb.connect(':memory:')
try:
    # Create table
    conn.execute(create_sql)
    print("\n✓ Table created successfully")
    
    # Try inserting one row
    test_row = data[0]
    transformed = schema.transform_row(test_row)
    
    # Remove id if present
    columns = list(transformed.keys())
    if 'id' in columns:
        columns.remove('id')
    
    print(f"\nInserting row with {len(columns)} columns")
    print(f"Sample values: {list(transformed.items())[:3]}")
    
    # Insert
    quoted_columns = [f'"{col}"' for col in columns]
    placeholders = ', '.join(['?' for _ in columns])
    insert_sql = f"INSERT INTO test_table ({', '.join(quoted_columns)}) VALUES ({placeholders})"
    
    values = tuple(transformed.get(col) for col in columns)
    conn.execute(insert_sql, values)
    
    # Check count
    result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
    print(f"\n✓ Rows in table: {result[0]}")
    
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()