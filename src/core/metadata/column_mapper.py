"""
Dynamic column mapping based on actual data values.
"""
from typing import Dict, List, Any, Set, Optional
import re
from collections import defaultdict
from ...config.logging import get_logger

logger = get_logger(__name__)

class ColumnMapper:
    """Maps user query terms to actual database columns based on data analysis."""
    
    def __init__(self):
        self.column_index = defaultdict(set)  # term -> {(table, column)}
        self.value_index = defaultdict(set)   # value -> {(table, column)}
        self.column_types = {}  # (table, column) -> detected_type
        
    def analyze_table(self, table_name: str, data: List[Dict[str, Any]]):
        """Analyze a table's data to build mapping indices."""
        if not data:
            return
            
        # Analyze each column
        for column in data[0].keys():
            # Analyze column name
            self._index_column_name(table_name, column)
            
            # Analyze column values
            values = [row.get(column) for row in data[:100] if row.get(column) is not None]
            if values:
                col_type = self._detect_column_type(values)
                self.column_types[(table_name, column)] = col_type
                
                # Index categorical values
                if col_type == 'categorical':
                    unique_values = set(str(v).lower() for v in values[:50])
                    for value in unique_values:
                        # Index the value
                        self.value_index[value].add((table_name, column))
                        
                        # Also index meaningful words from the value
                        words = re.findall(r'\b[a-zA-Z]+\b', value)
                        for word in words:
                            if len(word) > 2:
                                self.column_index[word.lower()].add((table_name, column))
    
    def _index_column_name(self, table_name: str, column: str):
        """Index column name for searching."""
        # Full column name
        self.column_index[column.lower()].add((table_name, column))
        
        # Split by underscore/camelCase
        parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', column)
        for part in parts:
            if len(part) > 2:
                self.column_index[part.lower()].add((table_name, column))
    
    def _detect_column_type(self, values: List[Any]) -> str:
        """Detect the semantic type of a column from its values."""
        if not values:
            return 'unknown'
            
        # Check if numeric
        numeric_count = sum(1 for v in values if isinstance(v, (int, float)) or 
                           (isinstance(v, str) and v.replace('.', '').replace('-', '').isdigit()))
        if numeric_count > len(values) * 0.8:
            return 'numeric'
            
        # Check if categorical (limited unique values)
        unique_values = set(str(v) for v in values if v)
        if len(unique_values) < len(values) * 0.3 and len(unique_values) < 50:
            return 'categorical'
            
        # Check if text (long strings)
        avg_length = sum(len(str(v)) for v in values if v) / len([v for v in values if v])
        if avg_length > 50:
            return 'text'
            
        return 'mixed'
    
    def find_columns_for_term(self, term: str) -> List[tuple]:
        """Find columns that might contain data related to a term."""
        term_lower = term.lower()
        matches = []
        
        # Direct column name matches
        if term_lower in self.column_index:
            matches.extend(self.column_index[term_lower])
        
        # Value matches
        if term_lower in self.value_index:
            matches.extend(self.value_index[term_lower])
        
        # Partial matches
        for key in self.column_index:
            if term_lower in key or key in term_lower:
                matches.extend(self.column_index[key])
        
        # Semantic mappings
        semantic_map = {
            'entity type': ['entity'],
            'risk type': ['risk_category', 'category'],
            'categories': ['category', 'risk_category', 'domain'],
            'domains': ['domain', 'subdomain'],
            'year': ['year', 'date', 'publication_year'],
            'count': ['*'],  # Special case for counts
        }
        
        if term_lower in semantic_map:
            for col_term in semantic_map[term_lower]:
                if col_term in self.column_index:
                    matches.extend(self.column_index[col_term])
        
        # Remove duplicates and return
        return list(set(matches))
    
    def get_column_info(self, table: str, column: str) -> Dict[str, Any]:
        """Get information about a specific column."""
        return {
            'type': self.column_types.get((table, column), 'unknown'),
            'indexed_terms': [term for term, cols in self.column_index.items() 
                            if (table, column) in cols],
            'sample_values': [val for val, cols in self.value_index.items() 
                            if (table, column) in cols][:10]
        }

# Singleton instance
column_mapper = ColumnMapper()