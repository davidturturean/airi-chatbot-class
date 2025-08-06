"""
Metadata service for handling meta-structural queries about databases.
"""
import time
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from pathlib import Path

from .database_registry import database_registry, DatabaseInfo
from .metadata_loader import MetadataLoader
from .query_generator import QueryGenerator, SQLQuery
from .schemas.risk_schema import RiskSchema
from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

class MetadataService:
    """Service for handling metadata queries across multiple databases."""
    
    def __init__(self, gemini_model=None):
        self.loader = MetadataLoader()
        self.query_generator = QueryGenerator()
        self.gemini_model = gemini_model  # Optional for language-aware messages
        self._initialized = False
        self._cache = {}
        self._cache_ttl = 1800  # 30 minutes
        
        # Register default databases
        self._register_default_databases()
    
    def _register_default_databases(self):
        """Register the default AI Risk Repository database."""
        # Register AI Risks database
        risk_schema = RiskSchema()
        excel_path = settings.DATA_DIR / "info_files" / "The_AI_Risk_Repository_V3_26_03_2025.xlsx"
        
        if excel_path.exists():
            database_registry.register_database(
                name="ai_risks",
                source_path=str(excel_path),
                schema=risk_schema,
                metadata={
                    "description": "MIT AI Risk Repository",
                    "version": "3.0",
                    "last_updated": "2025-03-26"
                }
            )
            logger.info("Registered AI Risk Repository database")
    
    def initialize(self, force_reload: bool = False):
        """Initialize all registered databases."""
        if self._initialized and not force_reload:
            logger.info("Metadata service already initialized")
            return
        
        start_time = time.time()
        total_rows = 0
        
        # Load all registered databases
        for db_name, db_info in database_registry.get_all_databases().items():
            try:
                row_count = self.loader.load_database(
                    name=db_name,
                    source_path=db_info.source_path,
                    schema=db_info.schema,
                    force_reload=force_reload
                )
                total_rows += row_count
                logger.info(f"Loaded database '{db_name}': {row_count} rows")
                
            except Exception as e:
                logger.error(f"Failed to load database '{db_name}': {str(e)}")
        
        self._initialized = True
        elapsed = time.time() - start_time
        logger.info(f"Metadata service initialized: {total_rows} total rows in {elapsed:.2f}s")
    
    def query(self, natural_query: str, language_info: Optional[Dict[str, Any]] = None, target_databases: Optional[List[str]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Execute a natural language query against the metadata.
        
        Args:
            natural_query: The natural language query
            language_info: Language information for response generation
            target_databases: Optional list of target databases
        
        Returns:
            Tuple of (formatted_response, raw_results)
        """
        # Ensure initialized
        if not self._initialized:
            self.initialize()
        
        # Check cache
        cache_key = f"{natural_query}:{target_databases}"
        cached = self._get_cached_result(cache_key)
        if cached:
            return cached
        
        try:
            # Determine target databases if not specified
            if not target_databases:
                relevant_dbs = database_registry.get_schema_for_query(natural_query)
                target_databases = [db.name for db in relevant_dbs]
            
            # Get schemas for SQL generation
            schemas = self._get_schemas_for_databases(target_databases)
            
            # Generate SQL
            sql_query = self.query_generator.generate_sql(
                natural_query=natural_query,
                available_schemas=schemas,
                allow_joins=len(target_databases) > 1
            )
            
            logger.info(f"Generated SQL: {sql_query.sql}")
            
            # Execute query
            results_df = self.loader.execute_query(sql_query.sql)
            
            # Format response
            formatted_response = self._format_response(
                query=natural_query,
                sql_query=sql_query,
                results=results_df,
                databases=target_databases
            )
            
            # Convert results to list of dicts
            raw_results = results_df.to_dict('records') if not results_df.empty else []
            
            # Cache result
            result = (formatted_response, raw_results)
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing metadata query: {str(e)}")
            # Fallback response
            return self._create_error_response(natural_query, str(e))
    
    def _get_schemas_for_databases(self, db_names: List[str]) -> List[Dict[str, Any]]:
        """Get schema information for specified databases."""
        schemas = []
        
        for db_name in db_names:
            db_info = database_registry.get_database(db_name)
            if db_info:
                schema_dict = {
                    'table_name': db_info.table_name,
                    'description': db_info.schema.description,
                    'columns': [
                        {
                            'name': col.name,
                            'sql_type': col.sql_type,
                            'description': col.description
                        }
                        for col in db_info.schema.get_columns()
                    ]
                }
                schemas.append(schema_dict)
        
        return schemas
    
    def _format_response(self, 
                        query: str, 
                        sql_query: SQLQuery,
                        results: pd.DataFrame,
                        databases: List[str]) -> str:
        """Format query results into natural language response."""
        
        # Start with explanation
        response_parts = [sql_query.explanation]
        
        if results.empty:
            # Use language-aware message for no results
            from ...utils.language_helper import get_no_results_message
            no_results_msg = get_no_results_message(query, self.gemini_model)
            response_parts.append(f"\n{no_results_msg}")
        else:
            # Format based on query type
            if sql_query.is_aggregation:
                # Format aggregation results
                response_parts.append(self._format_aggregation_results(results))
            else:
                # Format row results
                response_parts.append(self._format_row_results(results, sql_query))
        
        # Add citation
        db_citation = f"(META-DB:{','.join(databases)})"
        response_parts.append(f"\n{db_citation}")
        
        return "\n".join(response_parts)
    
    def _format_aggregation_results(self, results: pd.DataFrame) -> str:
        """Format aggregation query results."""
        if len(results) == 1 and len(results.columns) == 1:
            # Single value result
            value = results.iloc[0, 0]
            col_name = results.columns[0]
            return f"\n**Result**: {value}"
        else:
            # Multiple aggregations or group by
            formatted = "\n**Results**:\n"
            for _, row in results.iterrows():
                row_str = " | ".join([f"{col}: {row[col]}" for col in results.columns])
                formatted += f"- {row_str}\n"
            return formatted
    
    def _format_row_results(self, results: pd.DataFrame, sql_query: SQLQuery) -> str:
        """Format row-based query results."""
        num_results = len(results)
        
        if num_results == 0:
            return "\nNo matching records found."
        
        formatted = f"\n**Found {num_results} result{'s' if num_results != 1 else ''}**:\n\n"
        
        # Show first 10 results
        for idx, row in results.head(10).iterrows():
            # Format based on available columns
            if 'rid' in row:
                formatted += f"- **{row['rid']}**: "
            elif 'id' in row:
                formatted += f"- **{row['id']}**: "
            else:
                formatted += f"- "
            
            # Add title/name if available
            if 'title' in row:
                formatted += f"{row['title'][:100]}..."
            elif 'name' in row:
                formatted += f"{row['name']}"
            
            # Add other relevant fields
            relevant_fields = ['domain', 'risk_category', 'year', 'count']
            field_parts = []
            for field in relevant_fields:
                if field in row and pd.notna(row[field]):
                    field_parts.append(f"{field}: {row[field]}")
            
            if field_parts:
                formatted += f" ({', '.join(field_parts)})"
            
            formatted += "\n"
        
        if num_results > 10:
            formatted += f"\n... and {num_results - 10} more results."
        
        return formatted
    
    def _get_cached_result(self, key: str) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
        """Get cached result if available and not expired."""
        if key in self._cache:
            cached_time, result = self._cache[key]
            if time.time() - cached_time < self._cache_ttl:
                logger.info(f"Using cached result for query: {key[:50]}...")
                return result
            else:
                del self._cache[key]
        return None
    
    def _cache_result(self, key: str, result: Tuple[str, List[Dict[str, Any]]]):
        """Cache query result."""
        self._cache[key] = (time.time(), result)
        
        # Clean old cache entries
        if len(self._cache) > 100:
            current_time = time.time()
            expired_keys = [
                k for k, (t, _) in self._cache.items() 
                if current_time - t > self._cache_ttl
            ]
            for k in expired_keys:
                del self._cache[k]
    
    def _create_error_response(self, query: str, error: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Create an error response."""
        response = f"I encountered an error while processing your metadata query.\n\n"
        response += f"Query: {query}\n"
        response += f"Error: {error}\n\n"
        response += "Please try rephrasing your question or check the available databases."
        
        return (response, [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded databases."""
        stats = {
            "databases": {},
            "total_rows": 0,
            "initialized": self._initialized
        }
        
        for db_name, db_info in database_registry.get_all_databases().items():
            stats["databases"][db_name] = {
                "table_name": db_info.table_name,
                "row_count": db_info.row_count,
                "last_loaded": db_info.last_loaded,
                "id_prefix": db_info.id_prefix
            }
            stats["total_rows"] += db_info.row_count
        
        return stats

# Global metadata service instance
# Global instance - gemini_model will be set by chat_service when available
metadata_service = MetadataService()