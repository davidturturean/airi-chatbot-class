"""
Flexible metadata loader that supports any file format and schema.
"""
import time
import duckdb
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from .dynamic_schema import DynamicSchema
from .semantic_registry import semantic_registry
from .column_mapper import column_mapper
from .file_handlers import ExcelHandler, CSVHandler, TextHandler, DocxHandler, JSONHandler
from .file_handlers.base_handler import BaseFileHandler
from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

class FlexibleMetadataLoader:
    """Loads data from any supported file format into DuckDB with dynamic schemas."""
    
    def __init__(self, db_path: Optional[str] = None):
        # Use in-memory database for Railway compatibility
        self.db_path = db_path or ":memory:"
        self.connection = duckdb.connect(self.db_path)
        
        # Initialize file handlers
        self.handlers = [
            ExcelHandler(),
            CSVHandler(),
            TextHandler(),
            DocxHandler(),
            JSONHandler()
        ]
        
        # Track loaded tables
        self.loaded_tables = {}
    
    def load_file(self, file_path: Union[str, Path]) -> Dict[str, int]:
        """
        Load any supported file into DuckDB.
        
        Returns:
            Dict mapping table_name -> row_count
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return {}
        
        # Find appropriate handler
        handler = self._get_handler(file_path)
        if not handler:
            logger.error(f"No handler found for file type: {file_path.suffix}")
            return {}
        
        logger.info(f"Loading file: {file_path.name} using {handler.__class__.__name__}")
        
        # Extract data from file
        extracted_data = handler.extract_data(file_path)
        
        if not extracted_data:
            logger.warning(f"No data extracted from {file_path}")
            return {}
        
        # Load each extracted dataset
        results = {}
        for dataset in extracted_data:
            table_name = dataset['table_name']
            data = dataset['data']
            metadata = dataset.get('metadata', {})
            
            if not data:
                logger.warning(f"Empty dataset for table '{table_name}'")
                continue
            
            # Load into database
            row_count = self._load_table(table_name, data, handler, metadata)
            if row_count > 0:
                results[table_name] = row_count
                logger.info(f"Loaded {row_count} rows into table '{table_name}'")
        
        return results
    
    def load_directory(self, directory_path: Union[str, Path], 
                      recursive: bool = True,
                      file_patterns: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Load all supported files from a directory.
        
        Args:
            directory_path: Path to directory
            recursive: Whether to search subdirectories
            file_patterns: Optional list of glob patterns (e.g., ['*.xlsx', '*.csv'])
        
        Returns:
            Dict mapping table_name -> row_count
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists() or not directory_path.is_dir():
            logger.error(f"Directory not found: {directory_path}")
            return {}
        
        # Get list of supported extensions
        supported_extensions = set()
        for handler in self.handlers:
            supported_extensions.update(handler.supported_extensions)
        
        # Find files to load
        files_to_load = []
        
        if file_patterns:
            # Use provided patterns
            for pattern in file_patterns:
                if recursive:
                    files_to_load.extend(directory_path.rglob(pattern))
                else:
                    files_to_load.extend(directory_path.glob(pattern))
        else:
            # Load all supported files
            for ext in supported_extensions:
                if recursive:
                    files_to_load.extend(directory_path.rglob(f'*{ext}'))
                else:
                    files_to_load.extend(directory_path.glob(f'*{ext}'))
        
        # Remove duplicates and sort
        files_to_load = sorted(set(files_to_load))
        
        # Filter out temporary files
        files_to_load = [f for f in files_to_load if not f.name.startswith('~$')]
        
        logger.info(f"Found {len(files_to_load)} files to load")
        
        # Load each file
        all_results = {}
        for file_path in files_to_load:
            try:
                results = self.load_file(file_path)
                all_results.update(results)
            except Exception as e:
                logger.error(f"Error loading {file_path}: {str(e)}")
                continue
        
        return all_results
    
    def _get_handler(self, file_path: Path) -> Optional[BaseFileHandler]:
        """Get appropriate handler for file."""
        for handler in self.handlers:
            if handler.can_handle(file_path):
                return handler
        return None
    
    def _load_table(self, table_name: str, data: List[Dict[str, Any]], 
                   handler: BaseFileHandler, metadata: Dict[str, Any]) -> int:
        """Load data into a table with dynamic schema."""
        if not data:
            return 0
        
        try:
            # Handle table name conflicts - make unique
            original_table_name = table_name
            suffix = 1
            while table_name in self.loaded_tables:
                table_name = f"{original_table_name}_{suffix}"
                suffix += 1
            
            # Detect schema from data
            schema_dict = handler.detect_schema(data)
            
            if not schema_dict:
                logger.error(f"Could not detect schema for table '{table_name}'")
                return 0
            
            # Create dynamic schema
            schema = DynamicSchema(table_name, schema_dict, data[:100])
            
            # Drop table if exists (for reloading)
            try:
                self.connection.execute(f"DROP TABLE IF EXISTS {table_name}")
                self.connection.execute(f"DROP SEQUENCE IF EXISTS seq_{table_name}")
            except:
                pass
            
            # Create sequence for auto-increment if no primary key
            has_primary_key = any(col.is_primary_key for col in schema.column_defs.values())
            if not has_primary_key:
                self.connection.execute(f"CREATE SEQUENCE seq_{table_name} START 1")
            
            # Create table
            create_sql = schema.get_create_table_sql()
            self.connection.execute(create_sql)
            
            # Create indices
            for index_sql in schema.get_index_sql():
                self.connection.execute(index_sql)
            
            # Insert data with row-by-row error handling
            inserted = 0
            failed = 0
            batch_size = 100  # Smaller batches for better error isolation
            
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                
                # Process each row individually for better error handling
                for row_idx, row in enumerate(batch):
                    try:
                        # Transform row
                        transformed = schema.transform_row(row)
                        
                        # Insert single row
                        columns = list(transformed.keys())
                        if 'id' in columns:
                            columns.remove('id')
                        
                        quoted_columns = [f'"{col}"' for col in columns]
                        placeholders = ', '.join(['?' for _ in columns])
                        insert_sql = f"INSERT INTO {table_name} ({', '.join(quoted_columns)}) VALUES ({placeholders})"
                        
                        values = tuple(transformed.get(col) for col in columns)
                        
                        try:
                            self.connection.execute(insert_sql, values)
                            inserted += 1
                        except Exception as insert_error:
                            # Log specific insert error with row details
                            logger.debug(f"Insert error for row {i + row_idx}: {str(insert_error)}")
                            logger.debug(f"Problematic values: {values}")
                            failed += 1
                            
                    except Exception as e:
                        logger.debug(f"Transform error for row {i + row_idx}: {str(e)}")
                        failed += 1
                        continue
            
            if failed > 0:
                logger.warning(f"Table '{table_name}': {inserted} rows loaded, {failed} rows failed")
            
            # Store table info
            self.loaded_tables[table_name] = {
                'row_count': inserted,
                'schema': schema_dict,
                'metadata': metadata,
                'loaded_at': time.time()
            }
            
            # Register with semantic registry
            semantic_registry.register_table(
                table_name=table_name,
                metadata={**metadata, 'row_count': inserted},
                sample_data=data[:10] if data else None
            )
            
            # Analyze for column mapping
            column_mapper.analyze_table(table_name, data[:100] if data else [])
            
            return inserted
            
        except Exception as e:
            logger.error(f"Error loading table '{table_name}': {str(e)}")
            import traceback
            traceback.print_exc()
            return 0
    
    def execute_query(self, sql: str, params: Optional[List[Any]] = None) -> Any:
        """Execute a SQL query."""
        try:
            if params:
                result = self.connection.execute(sql, params)
            else:
                result = self.connection.execute(sql)
            return result
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            raise
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about loaded tables."""
        info = {}
        
        # Get actual table info from database
        tables_result = self.connection.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_catalog = 'memory' 
            AND table_schema = 'main'
        """).fetchall()
        
        for (table_name,) in tables_result:
            # Get row count
            count_result = self.connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            row_count = count_result[0] if count_result else 0
            
            # Get columns
            columns_result = self.connection.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """).fetchall()
            
            columns = {col_name: data_type for col_name, data_type in columns_result}
            
            info[table_name] = {
                'row_count': row_count,
                'columns': columns,
                'metadata': self.loaded_tables.get(table_name, {}).get('metadata', {})
            }
        
        return info
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()