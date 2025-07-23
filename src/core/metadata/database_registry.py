"""
Registry for managing multiple databases in the metadata infrastructure.
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from dataclasses import dataclass, field

from .schemas.base_schema import BaseSchema
from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

@dataclass
class DatabaseInfo:
    """Information about a registered database."""
    name: str
    source_path: str
    schema: BaseSchema
    table_name: str
    id_prefix: str
    last_loaded: Optional[float] = None
    row_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class DatabaseRegistry:
    """Manages registration and metadata for multiple databases."""
    
    def __init__(self):
        self.databases: Dict[str, DatabaseInfo] = {}
        self.registry_file = settings.DATA_DIR / "database_registry.json"
        self._load_registry()
    
    def register_database(self, 
                         name: str,
                         source_path: str,
                         schema: BaseSchema,
                         metadata: Optional[Dict[str, Any]] = None) -> DatabaseInfo:
        """Register a new database with the system."""
        if name in self.databases:
            logger.warning(f"Database '{name}' already registered, updating registration")
        
        db_info = DatabaseInfo(
            name=name,
            source_path=source_path,
            schema=schema,
            table_name=schema.table_name,
            id_prefix=schema.id_prefix,
            metadata=metadata or {}
        )
        
        self.databases[name] = db_info
        self._save_registry()
        
        logger.info(f"Registered database '{name}' with schema '{schema.name}'")
        return db_info
    
    def get_database(self, name: str) -> Optional[DatabaseInfo]:
        """Get information about a registered database."""
        return self.databases.get(name)
    
    def list_databases(self) -> List[str]:
        """List all registered database names."""
        return list(self.databases.keys())
    
    def get_all_databases(self) -> Dict[str, DatabaseInfo]:
        """Get all registered databases."""
        return self.databases.copy()
    
    def get_databases_by_prefix(self, prefix: str) -> List[DatabaseInfo]:
        """Get all databases with a specific ID prefix."""
        return [
            db for db in self.databases.values() 
            if db.id_prefix.lower() == prefix.lower()
        ]
    
    def update_database_stats(self, name: str, row_count: int, last_loaded: float):
        """Update statistics for a database after loading."""
        if name in self.databases:
            self.databases[name].row_count = row_count
            self.databases[name].last_loaded = last_loaded
            self._save_registry()
    
    def get_schema_for_query(self, query: str) -> List[DatabaseInfo]:
        """Determine which database schemas might be relevant for a query."""
        query_lower = query.lower()
        relevant_dbs = []
        
        # Check for specific database keywords
        db_keywords = {
            "ai_risks": ["risk", "risks", "repository", "rid-"],
            "mitigations": ["mitigation", "mitigations", "mid-"],
            "experts": ["expert", "experts", "eid-"],
        }
        
        for db_name, keywords in db_keywords.items():
            if db_name in self.databases:
                if any(keyword in query_lower for keyword in keywords):
                    relevant_dbs.append(self.databases[db_name])
        
        # If no specific match, return all databases
        if not relevant_dbs:
            relevant_dbs = list(self.databases.values())
        
        return relevant_dbs
    
    def _save_registry(self):
        """Save registry to disk for persistence."""
        try:
            registry_data = {
                "databases": {
                    name: {
                        "source_path": db.source_path,
                        "schema_name": db.schema.name,
                        "table_name": db.table_name,
                        "id_prefix": db.id_prefix,
                        "last_loaded": db.last_loaded,
                        "row_count": db.row_count,
                        "metadata": db.metadata
                    }
                    for name, db in self.databases.items()
                }
            }
            
            with open(self.registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving database registry: {str(e)}")
    
    def _load_registry(self):
        """Load registry from disk."""
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r') as f:
                    registry_data = json.load(f)
                    
                # Note: We only load metadata here, schemas need to be re-registered
                # This is because schema classes can't be serialized
                logger.info(f"Loaded registry metadata for {len(registry_data.get('databases', {}))} databases")
                
        except Exception as e:
            logger.error(f"Error loading database registry: {str(e)}")

# Global registry instance
database_registry = DatabaseRegistry()