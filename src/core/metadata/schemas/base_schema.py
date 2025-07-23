"""
Base schema class that all database schemas inherit from.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ColumnDefinition:
    """Defines a column in the database schema."""
    name: str
    sql_type: str
    is_primary_key: bool = False
    is_indexed: bool = False
    is_searchable: bool = True
    description: str = ""

@dataclass
class BaseSchema(ABC):
    """Base class for all database schemas."""
    name: str
    table_name: str
    id_prefix: str
    description: str
    columns: List[ColumnDefinition] = field(default_factory=list)
    
    @abstractmethod
    def get_columns(self) -> List[ColumnDefinition]:
        """Return the column definitions for this schema."""
        pass
    
    @abstractmethod
    def extract_row_data(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and transform data from a source row."""
        pass
    
    def get_sql_create_table(self) -> str:
        """Generate SQL CREATE TABLE statement."""
        columns = self.get_columns()
        
        col_definitions = []
        for col in columns:
            col_def = f"{col.name} {col.sql_type}"
            if col.is_primary_key:
                col_def += " PRIMARY KEY"
            col_definitions.append(col_def)
        
        return f"CREATE TABLE IF NOT EXISTS {self.table_name} ({', '.join(col_definitions)})"
    
    def get_sql_indices(self) -> List[str]:
        """Generate SQL CREATE INDEX statements."""
        columns = self.get_columns()
        indices = []
        
        for col in columns:
            if col.is_indexed and not col.is_primary_key:
                index_name = f"idx_{self.table_name}_{col.name}"
                indices.append(f"CREATE INDEX IF NOT EXISTS {index_name} ON {self.table_name}({col.name})")
        
        return indices
    
    def get_searchable_columns(self) -> List[str]:
        """Get list of columns that should be searchable."""
        return [col.name for col in self.get_columns() if col.is_searchable]
    
    def validate_row(self, row: Dict[str, Any]) -> bool:
        """Validate that a row has required fields."""
        return True  # Override in subclasses for validation