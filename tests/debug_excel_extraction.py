#!/usr/bin/env python3
"""
Debug Excel data extraction.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from src.core.metadata.file_handlers.excel_handler import ExcelHandler

excel_path = Path("data/info_files/The_AI_Risk_Repository_V3_26_03_2025.xlsx")

handler = ExcelHandler()
print(f"Loading: {excel_path}")

# Extract data
datasets = handler.extract_data(excel_path)

print(f"\nExtracted {len(datasets)} datasets")

for i, dataset in enumerate(datasets):
    table_name = dataset['table_name']
    data = dataset['data']
    metadata = dataset.get('metadata', {})
    
    print(f"\n{i+1}. Table: {table_name}")
    print(f"   Rows: {len(data)}")
    print(f"   Metadata: {metadata}")
    
    if data:
        print(f"   Columns: {list(data[0].keys())[:5]}...")
        print(f"   First row sample:")
        for key, value in list(data[0].items())[:3]:
            print(f"     {key}: {value}")