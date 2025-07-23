"""
Excel file handler with multi-sheet support.
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from .base_handler import BaseFileHandler
from ....config.logging import get_logger

logger = get_logger(__name__)

class ExcelHandler(BaseFileHandler):
    """Handler for Excel files (.xlsx, .xls) with multi-sheet support."""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.xlsx', '.xls']
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this is an Excel file."""
        # Skip temporary Excel files
        if file_path.name.startswith('~$'):
            return False
        return file_path.suffix.lower() in self.supported_extensions
    
    def extract_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract data from ALL sheets in Excel file."""
        results = []
        
        try:
            # Check if openpyxl is available
            try:
                import openpyxl
            except ImportError:
                logger.error("openpyxl not installed. Install with: pip install openpyxl")
                return []
            
            # Open Excel file
            excel_file = pd.ExcelFile(file_path)
            logger.info(f"Found {len(excel_file.sheet_names)} sheets in {file_path.name}")
            
            # Process each sheet
            for sheet_name in excel_file.sheet_names:
                logger.info(f"Processing sheet: {sheet_name}")
                
                try:
                    # Try to read sheet with automatic header detection
                    df = self._read_sheet_smart(excel_file, sheet_name)
                    
                    if df is None or df.empty:
                        logger.warning(f"Sheet '{sheet_name}' is empty or could not be read")
                        continue
                    
                    # Convert to list of dicts
                    data = df.replace({np.nan: None}).to_dict('records')
                    
                    # Clean column names
                    cleaned_data = []
                    for row in data:
                        cleaned_row = {}
                        for key, value in row.items():
                            # Clean column name
                            clean_key = self._clean_column_name(key)
                            if clean_key:  # Skip empty column names
                                cleaned_row[clean_key] = value
                        if cleaned_row:  # Only add non-empty rows
                            cleaned_data.append(cleaned_row)
                    
                    if cleaned_data:
                        results.append({
                            "table_name": self.sanitize_table_name(sheet_name),
                            "data": cleaned_data,
                            "metadata": {
                                "source_file": str(file_path),
                                "sheet_name": sheet_name,
                                "row_count": len(cleaned_data),
                                "column_count": len(cleaned_data[0]) if cleaned_data else 0
                            }
                        })
                        logger.info(f"Extracted {len(cleaned_data)} rows from sheet '{sheet_name}'")
                    
                except Exception as e:
                    logger.error(f"Error processing sheet '{sheet_name}': {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error reading Excel file {file_path}: {str(e)}")
            return []
    
    def _read_sheet_smart(self, excel_file: pd.ExcelFile, sheet_name: str) -> Optional[pd.DataFrame]:
        """Smart sheet reading with header detection."""
        try:
            # First, read without headers to analyze structure
            df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
            
            if df_raw.empty:
                return None
            
            # Find the header row (row with most non-null values that look like headers)
            header_row = self._find_header_row(df_raw)
            
            if header_row is None:
                # No clear header, use first row
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
            else:
                # Read with detected header row
                df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)
            
            # Drop rows where all values are NaN
            df = df.dropna(how='all')
            
            # Drop columns where all values are NaN
            df = df.dropna(axis=1, how='all')
            
            return df
            
        except Exception as e:
            logger.error(f"Error in smart sheet reading: {str(e)}")
            # Fallback to simple reading
            try:
                return pd.read_excel(excel_file, sheet_name=sheet_name)
            except:
                return None
    
    def _find_header_row(self, df: pd.DataFrame, max_rows: int = 10) -> Optional[int]:
        """Find the most likely header row in first N rows."""
        best_row = None
        best_score = 0
        
        for i in range(min(max_rows, len(df))):
            row = df.iloc[i]
            
            # Count non-null values
            non_null_count = row.notna().sum()
            
            # Check if values look like headers (strings, not numbers)
            string_count = sum(1 for val in row if isinstance(val, str) and val.strip())
            
            # Score based on non-null count and string count
            score = non_null_count + (string_count * 2)
            
            # Check if this row has mostly unique values (good for headers)
            if non_null_count > 0:
                unique_ratio = len(row.dropna().unique()) / non_null_count
                score *= unique_ratio
            
            if score > best_score:
                best_score = score
                best_row = i
        
        # Only return if we found a good header row
        if best_score > len(df.columns) * 0.5:  # At least 50% score
            return best_row
        
        return None
    
    def _clean_column_name(self, name: Any) -> str:
        """Clean and standardize column name."""
        if pd.isna(name) or name is None:
            return ""
        
        name = str(name).strip()
        
        # Remove common Excel artifacts
        if name.startswith("Unnamed:"):
            return ""
        
        # Replace problematic characters
        name = name.replace('\n', ' ').replace('\r', ' ')
        name = ' '.join(name.split())  # Normalize whitespace
        
        # Convert to valid SQL column name
        import re
        name = re.sub(r'[^a-zA-Z0-9_\s]', '', name)
        name = name.replace(' ', '_')
        name = re.sub(r'_+', '_', name)
        name = name.strip('_').lower()
        
        # Ensure not empty and valid
        if not name:
            return ""
        if not name[0].isalpha():
            name = f"col_{name}"
        
        return name