#!/usr/bin/env python3
"""
Check what columns are in the Excel file.
"""
import pandas as pd
from pathlib import Path

excel_path = Path("data/info_files/The_AI_Risk_Repository_V3_26_03_2025.xlsx")

if excel_path.exists():
    print(f"Reading Excel file: {excel_path}")
    
    # List all sheets
    excel_file = pd.ExcelFile(excel_path)
    print(f"\nSheets in Excel file:")
    for sheet in excel_file.sheet_names:
        print(f"  - {sheet}")
    
    # Read AI Risk Database v3 sheet
    sheet_name = "AI Risk Database v3"
    if sheet_name in excel_file.sheet_names:
        print(f"\nReading sheet: {sheet_name}")
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        print(f"\nShape: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"\nColumns:")
        for i, col in enumerate(df.columns):
            print(f"  {i}: {col}")
        
        print(f"\nFirst few rows:")
        print(df.head(3))
        
        # Check for RID column
        print(f"\nLooking for RID-like columns:")
        for col in df.columns:
            if 'RID' in str(col).upper() or 'ID' in str(col).upper():
                print(f"  Found: {col}")
                print(f"  Sample values: {df[col].head(3).tolist()}")
else:
    print(f"Excel file not found: {excel_path}")