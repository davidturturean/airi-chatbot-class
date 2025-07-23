"""
JSON file handler.
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
from .base_handler import BaseFileHandler
from ....config.logging import get_logger

logger = get_logger(__name__)

class JSONHandler(BaseFileHandler):
    """Handler for JSON files."""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.json']
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this is a JSON file."""
        return file_path.suffix.lower() in self.supported_extensions
    
    def extract_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract data from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            extracted_data = []
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Array of objects - perfect for table
                if data and all(isinstance(item, dict) for item in data):
                    extracted_data.append({
                        "table_name": self.sanitize_table_name(file_path.stem),
                        "data": self._normalize_records(data),
                        "metadata": {
                            "source_file": str(file_path),
                            "structure": "array_of_objects",
                            "row_count": len(data)
                        }
                    })
                else:
                    # Array of non-objects
                    records = []
                    for i, item in enumerate(data):
                        records.append({
                            "index": i,
                            "value": str(item),
                            "type": type(item).__name__
                        })
                    
                    extracted_data.append({
                        "table_name": self.sanitize_table_name(f"{file_path.stem}_items"),
                        "data": records,
                        "metadata": {
                            "source_file": str(file_path),
                            "structure": "array_of_values"
                        }
                    })
            
            elif isinstance(data, dict):
                # Single object or nested structure
                
                # Check if it's a wrapper with data array
                for key in ['data', 'items', 'records', 'results', 'rows']:
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        if items and all(isinstance(item, dict) for item in items):
                            extracted_data.append({
                                "table_name": self.sanitize_table_name(key),
                                "data": self._normalize_records(items),
                                "metadata": {
                                    "source_file": str(file_path),
                                    "structure": f"object_with_{key}_array",
                                    "row_count": len(items)
                                }
                            })
                
                # Also extract nested objects as separate tables
                nested_tables = self._extract_nested_objects(data, file_path.stem)
                extracted_data.extend(nested_tables)
                
                # If no nested arrays found, treat the object as a single record
                if not extracted_data:
                    extracted_data.append({
                        "table_name": self.sanitize_table_name(file_path.stem),
                        "data": [self._flatten_object(data)],
                        "metadata": {
                            "source_file": str(file_path),
                            "structure": "single_object"
                        }
                    })
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting data from JSON {file_path}: {str(e)}")
            return []
    
    def _normalize_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize records to ensure consistent columns."""
        if not records:
            return []
        
        # Get all possible keys
        all_keys = set()
        for record in records:
            all_keys.update(record.keys())
        
        # Normalize each record
        normalized = []
        for record in records:
            normalized_record = {}
            for key in all_keys:
                value = record.get(key, None)
                # Convert complex types to strings
                if isinstance(value, (dict, list)):
                    normalized_record[self._clean_key(key)] = json.dumps(value)
                else:
                    normalized_record[self._clean_key(key)] = value
            normalized.append(normalized_record)
        
        return normalized
    
    def _extract_nested_objects(self, data: Dict[str, Any], base_name: str) -> List[Dict[str, Any]]:
        """Extract nested objects as separate tables."""
        tables = []
        
        def extract_nested(obj: Dict[str, Any], path: str = ""):
            for key, value in obj.items():
                current_path = f"{path}_{key}" if path else key
                
                if isinstance(value, list) and value:
                    if all(isinstance(item, dict) for item in value):
                        # Array of objects - create a table
                        tables.append({
                            "table_name": self.sanitize_table_name(current_path),
                            "data": self._normalize_records(value),
                            "metadata": {
                                "structure": "nested_array",
                                "path": current_path,
                                "row_count": len(value)
                            }
                        })
                    elif all(isinstance(item, (str, int, float, bool)) for item in value):
                        # Array of primitives
                        records = []
                        for i, item in enumerate(value):
                            records.append({
                                "index": i,
                                "value": item,
                                f"{key}_id": i
                            })
                        tables.append({
                            "table_name": self.sanitize_table_name(f"{current_path}_values"),
                            "data": records,
                            "metadata": {
                                "structure": "nested_primitive_array",
                                "path": current_path
                            }
                        })
                
                elif isinstance(value, dict):
                    # Recurse into nested objects
                    extract_nested(value, current_path)
        
        extract_nested(data, base_name)
        return tables
    
    def _flatten_object(self, obj: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested object into single level."""
        flattened = {}
        
        for key, value in obj.items():
            new_key = f"{prefix}_{key}" if prefix else key
            new_key = self._clean_key(new_key)
            
            if isinstance(value, dict):
                # Recursively flatten
                flattened.update(self._flatten_object(value, new_key))
            elif isinstance(value, list):
                # Convert list to string
                flattened[new_key] = json.dumps(value)
            else:
                flattened[new_key] = value
        
        return flattened
    
    def _clean_key(self, key: str) -> str:
        """Clean key for use as column name."""
        import re
        # Replace dots and special chars
        key = re.sub(r'[^a-zA-Z0-9_]', '_', str(key))
        key = re.sub(r'_+', '_', key)
        key = key.strip('_').lower()
        
        if not key:
            return "unnamed"
        if not key[0].isalpha():
            key = f"col_{key}"
        
        return key