"""
Base file handler for all data formats.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib

class BaseFileHandler(ABC):
    """Abstract base class for file handlers."""
    
    def __init__(self):
        self.supported_extensions = []
        
    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file."""
        pass
    
    @abstractmethod
    def extract_data(self, file_path: Path) -> List[Dict[str, Dict[str, Any]]]:
        """
        Extract data from file.
        
        Returns:
            List of dictionaries, each containing:
            {
                "table_name": str,  # Name for the table
                "data": List[Dict[str, Any]],  # List of row dictionaries
                "metadata": Dict[str, Any]  # Optional metadata about the data
            }
        """
        pass
    
    def detect_schema(self, data: List[Dict[str, Any]], sample_size: int = 100) -> Dict[str, str]:
        """
        Detect column types from sample data.
        
        Returns mapping of column_name -> sql_type
        """
        if not data:
            return {}
        
        # Sample data for type detection
        sample = data[:sample_size]
        column_types = {}
        
        # Get all columns
        all_columns = set()
        for row in sample:
            all_columns.update(row.keys())
        
        # Detect type for each column
        for col in all_columns:
            col_type = self._detect_column_type(sample, col)
            column_types[col] = col_type
        
        return column_types
    
    def _detect_column_type(self, sample: List[Dict[str, Any]], column: str) -> str:
        """Detect SQL type for a column based on sample values."""
        import pandas as pd
        from datetime import datetime, date
        
        values = [row.get(column) for row in sample if row.get(column) is not None]
        
        if not values:
            return "TEXT"
        
        # Check for pandas datetime objects FIRST
        if any(isinstance(v, (datetime, date, pd.Timestamp)) for v in values):
            return "TIMESTAMP"
            
        # Check if it's a pandas datetime type
        if any(hasattr(v, 'dtype') and pd.api.types.is_datetime64_any_dtype(v) for v in values):
            return "TIMESTAMP"
        
        # Check for date/datetime patterns in strings
        if all(self._is_date(v) for v in values):
            if any(self._has_time(v) for v in values):
                return "TIMESTAMP"
            else:
                return "DATE"
        
        # Check for boolean
        if all(isinstance(v, bool) or str(v).lower() in ['true', 'false', '0', '1'] for v in values):
            return "BOOLEAN"
        
        # Check for integer (but exclude date-like strings)
        if all(self._is_integer(v) and not self._is_date(v) for v in values):
            max_val = max(int(v) for v in values)
            min_val = min(int(v) for v in values)
            if min_val >= -2147483648 and max_val <= 2147483647:
                return "INTEGER"
            else:
                return "BIGINT"
        
        # Check for float
        if all(self._is_float(v) and not self._is_date(v) for v in values):
            return "DOUBLE"
        
        # Check string length for VARCHAR vs TEXT
        max_length = max(len(str(v)) for v in values)
        if max_length <= 255:
            return "VARCHAR"
        else:
            return "TEXT"
    
    def _is_integer(self, value: Any) -> bool:
        """Check if value can be an integer."""
        try:
            int(str(value))
            return '.' not in str(value)
        except:
            return False
    
    def _is_float(self, value: Any) -> bool:
        """Check if value can be a float."""
        try:
            float(str(value))
            return True
        except:
            return False
    
    def _is_date(self, value: Any) -> bool:
        """Check if value appears to be a date."""
        import re
        import pandas as pd
        from datetime import datetime, date
        
        # Check if it's a datetime object
        if isinstance(value, (datetime, date, pd.Timestamp)):
            return True
            
        # Check if it's a pandas datetime type
        if hasattr(value, 'dtype') and pd.api.types.is_datetime64_any_dtype(value):
            return True
        
        # Check string patterns
        str_val = str(value).strip()
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}$',  # DD-MM-YYYY
            r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',  # YYYY-MM-DD HH:MM:SS
            r'^\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
        ]
        return any(re.match(pattern, str_val) for pattern in date_patterns)
    
    def _has_time(self, value: Any) -> bool:
        """Check if date value includes time."""
        return ':' in str(value)
    
    def sanitize_table_name(self, name: str) -> str:
        """Convert any string to a valid SQL table name."""
        import re
        # Replace spaces and special chars with underscore
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # Remove consecutive underscores
        name = re.sub(r'_+', '_', name)
        # Remove leading/trailing underscores
        name = name.strip('_')
        # Ensure it starts with a letter
        if name and not name[0].isalpha():
            name = f"table_{name}"
        # Lowercase for consistency
        name = name.lower()
        # Ensure not empty
        if not name:
            name = "unnamed_table"
        return name
    
    def generate_table_id(self, file_path: Path, table_name: str) -> str:
        """Generate unique table ID based on file and table name."""
        combined = f"{file_path.absolute()}:{table_name}"
        hash_obj = hashlib.md5(combined.encode())
        return f"tbl_{hash_obj.hexdigest()[:8]}"