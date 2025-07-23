#!/usr/bin/env python3
"""
Check the actual data in the Excel file by skipping header rows.
"""
import pandas as pd
from pathlib import Path

excel_path = Path("data/info_files/The_AI_Risk_Repository_V3_26_03_2025.xlsx")

if excel_path.exists():
    print(f"Reading Excel file: {excel_path}")
    
    sheet_name = "AI Risk Database v3"
    
    # Try reading with different header row numbers
    for skip_rows in [1, 2, 3, 4]:
        print(f"\n{'='*60}")
        print(f"Trying with skiprows={skip_rows}")
        
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name, skiprows=skip_rows)
            
            print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
            print(f"\nFirst 5 columns:")
            for i, col in enumerate(df.columns[:5]):
                print(f"  {i}: {col}")
            
            print(f"\nFirst row data:")
            if len(df) > 0:
                for col in df.columns[:5]:
                    print(f"  {col}: {df.iloc[0][col]}")
            
            # Look for RID values
            print(f"\nSearching for RID values in all columns:")
            rid_found = False
            for col in df.columns:
                if len(df) > 0:
                    # Check if any value in this column contains 'RID'
                    sample_values = df[col].astype(str).head(10)
                    if any('RID' in str(val) for val in sample_values):
                        print(f"  Found RIDs in column '{col}':")
                        print(f"    Sample: {[v for v in sample_values if 'RID' in str(v)][:3]}")
                        rid_found = True
            
            if rid_found:
                print(f"\n✓ This looks like the correct data format!")
                break
                
        except Exception as e:
            print(f"  Error: {str(e)}")
else:
    print(f"Excel file not found: {excel_path}")