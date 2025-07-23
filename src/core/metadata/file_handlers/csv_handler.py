"""
CSV file handler.
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from .base_handler import BaseFileHandler
from ....config.logging import get_logger

logger = get_logger(__name__)

class CSVHandler(BaseFileHandler):
    """Handler for CSV files."""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.csv']
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this is a CSV file."""
        return file_path.suffix.lower() in self.supported_extensions
    
    def extract_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract data from CSV file."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    logger.info(f"Successfully read CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error reading CSV with {encoding}: {str(e)}")
                    continue
            
            if df is None:
                logger.error(f"Could not read CSV file with any encoding")
                return []
            
            # Clean up the dataframe
            df = df.dropna(how='all')  # Remove empty rows
            df = df.dropna(axis=1, how='all')  # Remove empty columns
            
            if df.empty:
                logger.warning(f"CSV file is empty: {file_path}")
                return []
            
            # Convert to records
            data = df.replace({np.nan: None}).to_dict('records')
            
            # Clean column names and data
            cleaned_data = []
            for row in data:
                cleaned_row = {}
                for key, value in row.items():
                    clean_key = self._clean_column_name(key)
                    if clean_key:
                        cleaned_row[clean_key] = value
                if cleaned_row:
                    cleaned_data.append(cleaned_row)
            
            if cleaned_data:
                table_name = self.sanitize_table_name(file_path.stem)
                return [{
                    "table_name": table_name,
                    "data": cleaned_data,
                    "metadata": {
                        "source_file": str(file_path),
                        "row_count": len(cleaned_data),
                        "column_count": len(cleaned_data[0]) if cleaned_data else 0
                    }
                }]
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting data from CSV {file_path}: {str(e)}")
            return []
    
    def _clean_column_name(self, name: Any) -> str:
        """Clean and standardize column name."""
        if pd.isna(name) or name is None:
            return ""
        
        name = str(name).strip()
        
        # Replace problematic characters
        import re
        name = re.sub(r'[^a-zA-Z0-9_\s]', '', name)
        name = name.replace(' ', '_')
        name = re.sub(r'_+', '_', name)
        name = name.strip('_').lower()
        
        # Ensure valid
        if not name:
            return ""
        if not name[0].isalpha():
            name = f"col_{name}"
        
        return name