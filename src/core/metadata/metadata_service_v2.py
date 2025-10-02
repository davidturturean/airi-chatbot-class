"""
Flexible metadata service that works with any data format.
"""
import time
import threading
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from .metadata_loader_v2 import FlexibleMetadataLoader
from .query_generator import QueryGenerator
from .semantic_registry import semantic_registry
from .data_context_builder import DataContextBuilder
from .response_formatter import ResponseFormatter, ResponseMode
from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

class FlexibleMetadataService:
    """Service for handling metadata queries across dynamically loaded data."""

    def __init__(self):
        self.loader = FlexibleMetadataLoader()
        self.query_generator = QueryGenerator()

        # Initialize Gemini model for response formatting
        try:
            from ...core.models.gemini import GeminiModel
            gemini_model = GeminiModel(settings.GEMINI_API_KEY)
            self.response_formatter = ResponseFormatter(gemini_model=gemini_model, mode=ResponseMode.STANDARD)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini for formatter: {e}")
            self.response_formatter = ResponseFormatter(mode=ResponseMode.STANDARD)

        self._initialized = False
        self._total_rows = 0
        self._data_context = None  # Cached data context
        self._context_builder = None
        self._initialization_lock = threading.Lock()  # Thread safety for lazy loading
        self._initialization_error = None  # Track initialization errors
    
    def initialize(self, data_directories: Optional[List[str]] = None, force_reload: bool = False):
        """
        Initialize by loading data from specified directories.
        
        Args:
            data_directories: List of directories to scan. If None, uses default.
            force_reload: Whether to force reload all data
        """
        if self._initialized and not force_reload:
            logger.info("Metadata service already initialized")
            return
        
        start_time = time.time()
        
        # Default directories to scan
        if not data_directories:
            data_directories = [
                str(settings.DATA_DIR / "info_files"),
                str(settings.DATA_DIR / "doc_snippets"),
                str(settings.DATA_DIR)
            ]
        
        # Remove duplicates and non-existent paths
        valid_dirs = []
        for dir_path in data_directories:
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                if path not in valid_dirs:
                    valid_dirs.append(path)
        
        logger.info(f"Scanning {len(valid_dirs)} directories for data files")
        
        # Load data from each directory
        total_tables = 0
        total_rows = 0
        
        for directory in valid_dirs:
            logger.info(f"Loading data from: {directory}")
            results = self.loader.load_directory(directory, recursive=False)
            
            for table_name, row_count in results.items():
                total_tables += 1
                total_rows += row_count
                logger.info(f"  - {table_name}: {row_count} rows")
        
        self._initialized = True
        self._total_rows = total_rows
        
        # Build data context for better query generation
        self._build_data_context()
        
        elapsed = time.time() - start_time
        logger.info(f"Metadata service initialized: {total_tables} tables, {total_rows} total rows in {elapsed:.2f}s")

    def ensure_initialized(self) -> bool:
        """
        Ensure metadata is initialized. Thread-safe lazy loading.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        logger.info("Lazy loading metadata on first query...")

        with self._initialization_lock:
            # Double-check after acquiring lock
            if self._initialized:
                return True

            try:
                self.initialize()
                return True
            except Exception as e:
                self._initialization_error = str(e)
                logger.error(f"Lazy initialization failed: {e}")
                return False

    def _build_data_context(self):
        """Build comprehensive data context for query generation."""
        logger.info("Building data context for query generation...")
        
        try:
            # Create context builder with loader's connection
            self._context_builder = DataContextBuilder(self.loader.connection)
            
            # Build full context with samples
            self._data_context = self._context_builder.build_full_context(
                sample_size=100,
                max_distinct_values=50
            )
            
            logger.info(f"Data context built: {len(self._data_context['tables'])} tables analyzed")
            
        except Exception as e:
            logger.error(f"Error building data context: {str(e)}")
            self._data_context = None
    
    def load_file(self, file_path: str) -> Dict[str, int]:
        """Load a specific file into the metadata service."""
        return self.loader.load_file(file_path)
    
    def query(self, natural_query: str, mode: Optional[ResponseMode] = None,
              debug: bool = False) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Execute a natural language query against the metadata.

        Args:
            natural_query: User's natural language query
            mode: Response formatting mode (defaults to service's mode)
            debug: Whether to include debug information

        Returns:
            Tuple of (formatted_response, raw_results)
        """
        # Ensure initialized with lazy loading
        if not self.ensure_initialized():
            error_msg = self._initialization_error or "Metadata service initialization failed"
            logger.error(f"Query blocked: {error_msg}")
            return f"The metadata service is not ready: {error_msg}", []
        
        # Safety check: Detect if this is actually a taxonomy query
        query_lower = natural_query.lower()
        taxonomy_indicators = [
            'subdomain', 'causal taxonomy', 'domain taxonomy', '7 domains', '24 subdomains',
            'risk categories', 'ai risk database v3', 'taxonomy structure',
            'privacy & security', 'discrimination & toxicity', 'ai system safety',
            'complete structure', 'risk categorization', 'percentage of risks',
            'each causal category', 'entity intentionality timing'
        ]
        
        if any(indicator in query_lower for indicator in taxonomy_indicators):
            # This looks like a taxonomy query that shouldn't be here
            logger.warning(f"Detected probable taxonomy query in metadata service: {natural_query[:100]}")
            return "This appears to be a taxonomy query. Please try rephrasing your question about the AI Risk Repository taxonomy.", []
        
        start_time = time.time()
        
        try:
            # Get table info for context
            table_info = self.loader.get_table_info()
            
            if not table_info:
                return "No data has been loaded into the metadata service.", []
            
            # Find relevant tables based on query intent
            relevant_tables = semantic_registry.find_tables_for_query(natural_query)
            
            # If no specific tables found, use all tables
            if not relevant_tables:
                logger.info("No specific tables found for query, using all tables")
                available_schemas = []
                for table_name, info in table_info.items():
                    schema = {
                        'table_name': table_name,
                        'columns': info['columns'],
                        'row_count': info['row_count'],
                        'description': semantic_registry.get_table_description(table_name) or ""
                    }
                    available_schemas.append(schema)
            else:
                # Use only relevant tables
                logger.info(f"Found {len(relevant_tables)} relevant tables for query")
                available_schemas = []
                for semantics in relevant_tables[:5]:  # Limit to top 5 matches
                    if semantics.table_name in table_info:
                        info = table_info[semantics.table_name]
                        schema = {
                            'table_name': semantics.table_name,
                            'columns': info['columns'],
                            'row_count': info['row_count'],
                            'description': semantics.description,
                            'semantic_type': semantics.semantic_type
                        }
                        available_schemas.append(schema)
            
            if not available_schemas:
                return "No relevant tables found for your query.", []
            
            # Generate SQL from natural language with semantic context AND data context
            sql_query = self.query_generator.generate_sql(
                natural_query=natural_query,
                available_schemas=available_schemas,
                data_context=self._data_context
            )
            
            if not sql_query:
                return "I couldn't understand your query. Please try rephrasing.", []
            
            # Execute query
            result = self.loader.execute_query(sql_query.sql)
            
            # Convert to list of dicts
            if hasattr(result, 'df'):
                df = result.df()
                data = df.to_dict('records')
            else:
                # Handle other result types
                data = []
                columns = [desc[0] for desc in result.description] if hasattr(result, 'description') else []
                for row in result.fetchall():
                    data.append(dict(zip(columns, row)))
            
            execution_time = time.time() - start_time
            
            # Use ResponseFormatter for intelligent formatting
            if mode:
                self.response_formatter.mode = mode
            
            formatted_response = self.response_formatter.format_response(
                query=natural_query,
                raw_results=data,
                sql_query=sql_query.sql,
                execution_time=execution_time,
                tables_used=sql_query.target_tables,
                data_context=self._data_context,
                debug=debug
            )
            
            # Combine all parts of the formatted response
            response_text = formatted_response.formatted_content
            
            # Add insights if available
            if formatted_response.insights:
                response_text += "\n\n**Key Insights:**\n"
                for insight in formatted_response.insights:
                    response_text += f"- {insight.key_finding}\n"
            
            # Add visualizations if available (but skip for metadata queries)
            # Check if this is a metadata query by looking for specific fields
            is_metadata_result = False
            if data and isinstance(data[0], dict):
                metadata_fields = {'risk_id', 'domain', 'category', 'category_level', 'risk_category'}
                if any(field in data[0] for field in metadata_fields):
                    is_metadata_result = True
            
            # Only add visualizations for non-metadata queries
            if formatted_response.visualizations and not is_metadata_result:
                response_text += "\n"
                for viz in formatted_response.visualizations:
                    response_text += f"\n{viz}\n"
            
            # Add debug info if requested
            if debug and formatted_response.debug_info:
                response_text += f"\n\n---\n**Debug Information:**\n"
                response_text += f"SQL: {formatted_response.debug_info.raw_sql}\n"
                response_text += f"Execution Time: {execution_time:.2f}s\n"
            
            return response_text, data
            
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            return f"Error executing query: {str(e)}", []
    
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded data."""
        table_info = self.loader.get_table_info()
        
        stats = {
            'total_rows': sum(info['row_count'] for info in table_info.values()),
            'table_count': len(table_info),
            'tables': {}
        }
        
        for table_name, info in table_info.items():
            stats['tables'][table_name] = {
                'row_count': info['row_count'],
                'column_count': len(info['columns']),
                'columns': list(info['columns'].keys())
            }
        
        return stats
    
    def list_tables(self) -> List[str]:
        """List all available tables."""
        return list(self.loader.get_table_info().keys())
    
    def describe_table(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a table."""
        table_info = self.loader.get_table_info()
        
        if table_name not in table_info:
            return {'error': f"Table '{table_name}' not found"}
        
        return table_info[table_name]

# Create singleton instance
flexible_metadata_service = FlexibleMetadataService()