"""
Dynamic schema generation based on actual data.
"""
from typing import Dict, List, Any, Optional
import re
from dataclasses import dataclass
from ...config.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DynamicColumn:
    """Represents a dynamically detected column."""
    name: str
    sql_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    is_indexed: bool = False
    
class DynamicSchema:
    """Schema generated dynamically from data."""
    
    def __init__(self, table_name: str, columns: Dict[str, str], data_sample: List[Dict[str, Any]]):
        self.table_name = table_name
        self.columns = columns
        self.data_sample = data_sample
        self._analyze_columns()
    
    def _analyze_columns(self):
        """Analyze columns to determine indexing and key strategies."""
        self.column_defs = {}
        
        for col_name, sql_type in self.columns.items():
            column = DynamicColumn(name=col_name, sql_type=sql_type)
            
            # Check if this could be a primary key
            if self._is_potential_id(col_name, self.data_sample):
                column.is_primary_key = True
                column.is_nullable = False
            
            # Check if this should be indexed
            if self._should_index(col_name, sql_type):
                column.is_indexed = True
            
            self.column_defs[col_name] = column
    
    def _is_potential_id(self, col_name: str, data_sample: List[Dict[str, Any]]) -> bool:
        """Check if column looks like an ID field."""
        # Only check very specific ID patterns to avoid false positives
        col_lower = col_name.lower()
        
        # Must be exactly one of these names (not just contain them)
        exact_id_names = ['id', 'rid', '_id', 'uuid', 'pk', 'primary_key']
        if col_lower in exact_id_names:
            # Verify uniqueness in sample
            if data_sample and len(data_sample) > 1:
                values = [row.get(col_name) for row in data_sample if row.get(col_name) is not None]
                if len(values) == len(set(values)) and len(values) > 0:  # All unique and not empty
                    return True
        
        # Check if values look like IDs (e.g., RID-001) AND column name suggests ID
        if ('id' in col_lower or col_lower.startswith('rid')) and data_sample and len(data_sample) > 3:
            sample_values = [str(row.get(col_name, '')) for row in data_sample[:10] if row.get(col_name)]
            if len(sample_values) >= 3:  # Need enough samples
                id_pattern = re.compile(r'^[A-Z]{2,}-\d+$|^\d+$|^[a-f0-9-]{8,}$', re.IGNORECASE)
                if all(id_pattern.match(val) for val in sample_values if val):
                    # Final check - must be unique
                    all_values = [row.get(col_name) for row in data_sample if row.get(col_name)]
                    if len(all_values) == len(set(all_values)):
                        return True
        
        return False
    
    def _should_index(self, col_name: str, sql_type: str) -> bool:
        """Determine if column should be indexed."""
        # Index foreign key-like columns
        if col_name.endswith('_id') or col_name.endswith('_key'):
            return True
        
        # Index commonly queried fields
        common_indexed = ['domain', 'category', 'type', 'status', 'created', 'updated', 
                         'date', 'year', 'name', 'title', 'entity', 'intent']
        if any(field in col_name.lower() for field in common_indexed):
            return True
        
        # Don't index large text fields
        if sql_type in ['TEXT', 'BLOB']:
            return False
        
        return False
    
    def get_create_table_sql(self) -> str:
        """Generate CREATE TABLE SQL."""
        columns_sql = []
        
        # Find primary key
        primary_key = None
        for col_name, col_def in self.column_defs.items():
            if col_def.is_primary_key:
                primary_key = col_name
                break
        
        # If no primary key found, add sequence-based ID
        if not primary_key:
            # DuckDB uses sequences for auto-increment
            columns_sql.insert(0, "id INTEGER DEFAULT nextval('seq_" + self.table_name + "')")
        
        # Add column definitions
        for col_name, col_def in self.column_defs.items():
            parts = [f'"{col_name}"', col_def.sql_type]
            
            if col_def.is_primary_key:
                parts.append("PRIMARY KEY")
            elif not col_def.is_nullable:
                parts.append("NOT NULL")
            
            columns_sql.append(" ".join(parts))
        
        return f"CREATE TABLE IF NOT EXISTS {self.table_name} (\n  " + ",\n  ".join(columns_sql) + "\n)"
    
    def get_index_sql(self) -> List[str]:
        """Generate CREATE INDEX SQL statements."""
        indices = []
        
        for col_name, col_def in self.column_defs.items():
            if col_def.is_indexed and not col_def.is_primary_key:
                index_name = f"idx_{self.table_name}_{col_name}"
                indices.append(f"CREATE INDEX IF NOT EXISTS {index_name} ON {self.table_name} (\"{col_name}\")")
        
        return indices
    
    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a row to match the schema."""
        transformed = {}
        
        for col_name, col_def in self.column_defs.items():
            value = row.get(col_name)
            
            # Handle None values
            if value is None:
                if col_def.is_nullable:
                    transformed[col_name] = None
                else:
                    # Provide default based on type
                    if col_def.sql_type in ['INTEGER', 'BIGINT']:
                        transformed[col_name] = 0
                    elif col_def.sql_type == 'DOUBLE':
                        transformed[col_name] = 0.0
                    elif col_def.sql_type == 'BOOLEAN':
                        transformed[col_name] = False
                    else:
                        transformed[col_name] = ''
            else:
                # Type conversion with robust handling
                try:
                    if col_def.sql_type in ['INTEGER', 'BIGINT']:
                        # Try to convert to int
                        try:
                            # Handle float strings like "1.0"
                            if isinstance(value, str) and '.' in value:
                                transformed[col_name] = int(float(value))
                            else:
                                transformed[col_name] = int(value)
                        except (ValueError, TypeError):
                            # If it's clearly not a number, set to NULL
                            str_val = str(value).strip()
                            if str_val and not str_val.replace('.', '').replace('-', '').isdigit():
                                transformed[col_name] = None
                                logger.debug(f"Non-numeric value '{value}' in INTEGER column '{col_name}', using NULL")
                            else:
                                transformed[col_name] = None
                    
                    elif col_def.sql_type == 'DOUBLE':
                        try:
                            transformed[col_name] = float(value)
                        except (ValueError, TypeError):
                            transformed[col_name] = None
                            logger.debug(f"Non-numeric value '{value}' in DOUBLE column '{col_name}', using NULL")
                    
                    elif col_def.sql_type == 'BOOLEAN':
                        if isinstance(value, str):
                            transformed[col_name] = value.lower() in ['true', '1', 'yes', 'y', 't']
                        else:
                            transformed[col_name] = bool(value)
                    
                    elif col_def.sql_type in ['DATE', 'TIMESTAMP']:
                        # Handle various date formats
                        import pandas as pd
                        from datetime import datetime
                        
                        if isinstance(value, (datetime, pd.Timestamp)):
                            # Already a date object
                            transformed[col_name] = str(value)
                        elif isinstance(value, str):
                            # Check if it's a valid date string
                            str_val = value.strip()
                            if any(char.isdigit() for char in str_val) and any(char in str_val for char in ['-', '/', ':']):
                                transformed[col_name] = str_val
                            else:
                                # Not a date - use NULL
                                transformed[col_name] = None
                                logger.debug(f"Non-date value '{value}' in {col_def.sql_type} column '{col_name}', using NULL")
                        else:
                            transformed[col_name] = str(value) if value is not None else None
                    
                    else:
                        # VARCHAR/TEXT - convert to string
                        transformed[col_name] = str(value) if value is not None else None
                        
                except Exception as e:
                    # Ultimate fallback
                    logger.debug(f"Unexpected error converting {col_name}={value}: {str(e)}")
                    transformed[col_name] = None
        
        return transformed