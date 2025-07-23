"""
SQL query generation using Gemini for natural language to SQL conversion.
"""
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from ...config.logging import get_logger
from ...config.settings import settings
from .column_mapper import column_mapper
from .data_context_builder import DataContextBuilder

logger = get_logger(__name__)

@dataclass
class SQLQuery:
    """Represents a generated SQL query with metadata."""
    sql: str
    confidence: float
    target_tables: List[str]
    explanation: str
    is_aggregation: bool = False
    is_join: bool = False

class QueryGenerator:
    """Generates SQL queries from natural language using Gemini."""
    
    def __init__(self, gemini_model=None):
        self.gemini_model = gemini_model
        self._sql_patterns = self._init_sql_patterns()
    
    def _init_sql_patterns(self) -> Dict[str, List[str]]:
        """Initialize common SQL patterns for validation."""
        return {
            'dangerous': [
                'drop', 'delete', 'truncate', 'alter', 'create',
                'insert', 'update', 'grant', 'revoke'
            ],
            'aggregations': [
                'count', 'sum', 'avg', 'max', 'min', 'group by'
            ],
            'joins': [
                'join', 'inner join', 'left join', 'right join', 'cross join'
            ]
        }
    
    def _preprocess_query(self, query: str) -> str:
        """Pre-process query to improve semantic understanding."""
        # Create semantic mappings
        term_mappings = {
            # Entity mappings
            'entity type': 'entity (1=Human, 2=AI)',
            'entity types': 'entity values',
            'by entity': 'grouped by entity',
            
            # Category mappings
            'risk categories': 'distinct risk_category values',
            'main categories': 'distinct category or risk_category values',
            'types of risks': 'distinct risk categories',
            
            # Domain mappings
            'domain 7': 'domain containing "7" or domain = "7. AI System Safety, Failures, & Limitations"',
            'in domain': 'where domain contains',
            'risks in domain': 'count of risks where domain contains',
            
            # Year/date mappings
            'publication year': 'year or date field',
            'earliest year': 'minimum year or earliest date',
            'from 2024': 'where year = 2024 or date contains "2024"',
            
            # General improvements
            'how many risks': 'count all rows in risk-related tables',
            'list all': 'select distinct',
            'show me the': 'select the',
            'what are the': 'list distinct',
            
            # Top N queries
            'show top': 'select all columns for top',
            'show risks': 'select * from risks where',
            'top 5': 'limit 5',
            'top 10': 'limit 10',
        }
        
        # Apply mappings
        processed = query.lower()
        for term, replacement in term_mappings.items():
            if term in processed:
                logger.info(f"Query preprocessing: '{term}' → '{replacement}'")
                processed = processed.replace(term, replacement)
        
        # Preserve original case for proper nouns
        if processed != query.lower():
            # Try to maintain some original formatting
            return query + f" (interpreted as: {processed})"
        
        return query
    
    def generate_sql(self, 
                    natural_query: str, 
                    available_schemas: List[Dict[str, Any]],
                    allow_joins: bool = True,
                    data_context: Optional[Dict[str, Any]] = None) -> SQLQuery:
        """Generate SQL from natural language query."""
        
        # Pre-process query to improve semantic understanding
        processed_query = self._preprocess_query(natural_query)
        
        # Build schema context
        schema_context = self._build_schema_context(available_schemas)
        
        # Generate SQL using Gemini with data context
        prompt = self._build_generation_prompt(
            processed_query, 
            schema_context, 
            allow_joins,
            data_context
        )
        
        try:
            if not self.gemini_model:
                from ...core.models.gemini import GeminiModel
                self.gemini_model = GeminiModel(settings.GEMINI_API_KEY)
            
            response = self.gemini_model.generate(prompt)
            
            # Parse and validate response
            sql_query = self._parse_sql_response(response, available_schemas)
            
            # Additional safety validation
            if self._is_dangerous_query(sql_query.sql):
                raise ValueError("Generated SQL contains dangerous operations")
            
            return sql_query
            
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            # Return a safe fallback query
            return self._create_fallback_query(natural_query, available_schemas)
    
    def _build_schema_context(self, schemas: List[Dict[str, Any]]) -> str:
        """Build schema context for the prompt."""
        context_parts = []
        
        for schema in schemas:
            table_info = f"Table: {schema['table_name']}\n"
            
            # Add description if available
            if schema.get('description'):
                table_info += f"Description: {schema['description']}\n"
            
            # Add semantic type if available
            if schema.get('semantic_type'):
                table_info += f"Type: {schema['semantic_type']} data\n"
            
            # Add row count
            table_info += f"Rows: {schema.get('row_count', 'unknown')}\n"
            
            # Add columns
            table_info += "Columns:\n"
            columns = schema.get('columns', {})
            
            # Handle both dict and list formats
            if isinstance(columns, dict):
                for col_name, col_type in columns.items():
                    col_info = f"  - {col_name} ({col_type})"
                    
                    # Add column mapping hints
                    col_data = column_mapper.get_column_info(schema['table_name'], col_name)
                    if col_data['sample_values']:
                        samples = col_data['sample_values'][:3]
                        col_info += f" [examples: {', '.join(samples)}]"
                    
                    table_info += col_info + "\n"
            elif isinstance(columns, list):
                for col in columns:
                    col_line = f"  - {col['name']} ({col['sql_type']})"
                    if col.get('description'):
                        col_line += f": {col['description']}"
                    table_info += col_line + "\n"
            
            context_parts.append(table_info)
        
        return "\n\n".join(context_parts)
    
    def _build_generation_prompt(self, query: str, schema: str, allow_joins: bool, 
                               data_context: Optional[Dict[str, Any]] = None) -> str:
        """Build the prompt for SQL generation."""
        join_instruction = "You may use JOINs between tables if needed." if allow_joins else "Do NOT use JOINs."
        
        # Add data context if available
        context_section = ""
        if data_context:
            # Use context builder to format the data
            context_builder = DataContextBuilder(None)  # Don't need connection for formatting
            context_str = context_builder.export_context_for_prompt(data_context, max_chars=30000)
            context_section = f"\n{context_str}\n"
        
        return f"""You are an intelligent SQL query generator. Convert the natural language question into a SQL query.
{context_section if context_section else ''}

IMPORTANT CONTEXT:
- When the user asks about "risks", they mean AI risk data which could be in tables containing risk-related information
- When asked about "domains" or "categories", look for tables with taxonomy or classification data
- When asked about counts or statistics, look for appropriate aggregation tables or compute from raw data
- The user doesn't know internal table names, so interpret their intent semantically

AVAILABLE SCHEMA:
{schema}

QUERY INTERPRETATION RULES:
1. Understand user intent, not just literal words
2. "How many risks" → COUNT(*) from appropriate risk tables
3. "List domains" → SELECT DISTINCT domain from tables with domain column
4. "Show categories" → SELECT DISTINCT from category/risk_category columns
5. "Entity type" → refers to entity column (1=Human, 2=AI)
6. "Domain 7" → domain LIKE '%7%' or full domain name match
7. "Count by X" → SELECT X, COUNT(*) GROUP BY X
8. Match semantic meaning, not exact table/column names

SQL GENERATION RULES:
1. Return ONLY valid SQL that can be executed
2. Use appropriate aggregate functions (COUNT, AVG, etc) when needed
3. {join_instruction}
4. For text searches, use LIKE with % wildcards
5. Table and column names should be quoted with double quotes if they contain special characters
6. ONLY use SELECT statements (no INSERT, UPDATE, DELETE, etc)
7. Include ORDER BY when appropriate
8. Limit results to 100 rows unless specifically asked for more
9. For getting Nth row, use LIMIT 1 OFFSET N-1
10. IMPORTANT: When using LIKE on numeric columns, cast to VARCHAR first: CAST(column AS VARCHAR) LIKE '%pattern%'
11. When comparing different types, use explicit casting
12. For date comparisons, ensure proper date format
13. String literals MUST be in single quotes: WHERE column = 'value' (NOT double quotes)
14. Double quotes are ONLY for identifiers (table/column names)
15. Look at the actual distinct values shown in the data context above to understand what values exist
16. For partial matches, consider the actual format of values (e.g., if domains are "1. Topic Name", search appropriately)
17. Use the exact column values shown in the examples when filtering
18. When asked to "show risks", always SELECT * or multiple important columns (id, title, description, risk_category, domain, etc.)
19. Never select just title unless specifically asked for titles only

QUESTION: "{query}"

Return your response in this format:
SQL: <your sql query here>
EXPLANATION: <brief explanation of what the query does>
TABLES: <comma-separated list of tables used>
CONFIDENCE: <0.0-1.0 confidence score>"""
    
    def _parse_sql_response(self, response: str, schemas: List[Dict[str, Any]]) -> SQLQuery:
        """Parse Gemini's response into SQLQuery object."""
        # Extract components using regex
        sql_match = re.search(r'SQL:\s*(.+?)(?=EXPLANATION:|$)', response, re.DOTALL | re.IGNORECASE)
        explanation_match = re.search(r'EXPLANATION:\s*(.+?)(?=TABLES:|$)', response, re.DOTALL | re.IGNORECASE)
        tables_match = re.search(r'TABLES:\s*(.+?)(?=CONFIDENCE:|$)', response, re.DOTALL | re.IGNORECASE)
        confidence_match = re.search(r'CONFIDENCE:\s*(\d*\.?\d+)', response, re.IGNORECASE)
        
        if not sql_match:
            raise ValueError("No SQL query found in response")
        
        sql = sql_match.group(1).strip()
        explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided"
        tables_str = tables_match.group(1).strip() if tables_match else ""
        confidence = float(confidence_match.group(1)) if confidence_match else 0.7
        
        # Parse tables
        target_tables = [t.strip() for t in tables_str.split(',') if t.strip()]
        
        # Validate tables exist
        valid_tables = {schema['table_name'] for schema in schemas}
        target_tables = [t for t in target_tables if t in valid_tables]
        
        # Detect query type
        sql_lower = sql.lower()
        is_aggregation = any(pattern in sql_lower for pattern in self._sql_patterns['aggregations'])
        is_join = any(pattern in sql_lower for pattern in self._sql_patterns['joins'])
        
        return SQLQuery(
            sql=sql,
            confidence=confidence,
            target_tables=target_tables,
            explanation=explanation,
            is_aggregation=is_aggregation,
            is_join=is_join
        )
    
    def _is_dangerous_query(self, sql: str) -> bool:
        """Check if SQL contains dangerous operations."""
        sql_lower = sql.lower()
        
        # More precise checking - only flag if these are actual SQL commands
        for pattern in self._sql_patterns['dangerous']:
            # Check for pattern as a SQL command (not part of table/column names)
            if re.search(r'\b' + pattern + r'\b\s+(table|database|index|view)', sql_lower):
                return True
            # Check for DML operations
            if pattern in ['insert', 'update', 'delete'] and re.search(r'^\s*' + pattern + r'\b', sql_lower):
                return True
        
        return False
    
    def _create_fallback_query(self, query: str, schemas: List[Dict[str, Any]]) -> SQLQuery:
        """Create a safe fallback query when generation fails."""
        query_lower = query.lower()
        
        # Default to first available table
        if not schemas:
            raise ValueError("No schemas available for fallback query")
        
        # Try to pick the most relevant table based on query
        selected_table = schemas[0]['table_name']
        for schema in schemas:
            table_name = schema['table_name'].lower()
            if 'risk' in query_lower and 'risk' in table_name:
                selected_table = schema['table_name']
                break
            elif 'domain' in query_lower and 'domain' in table_name:
                selected_table = schema['table_name']
                break
            elif 'categor' in query_lower and ('categor' in table_name or 'taxonom' in table_name):
                selected_table = schema['table_name']
                break
        
        # Find relevant columns
        schema = next((s for s in schemas if s['table_name'] == selected_table), schemas[0])
        columns = schema.get('columns', {})
        
        # Simple count query
        if 'count' in query_lower or 'how many' in query_lower:
            sql = f'SELECT COUNT(*) as total FROM "{selected_table}"'
            explanation = f"Count all records in {selected_table}"
        # Categories query
        elif 'categor' in query_lower:
            # Look for category column
            cat_col = None
            for col in columns:
                if 'categor' in col.lower():
                    cat_col = col
                    break
            if cat_col:
                sql = f'SELECT DISTINCT "{cat_col}" FROM "{selected_table}"'
                explanation = f"List distinct categories from {selected_table}"
            else:
                sql = f'SELECT * FROM "{selected_table}" LIMIT 10'
                explanation = f"Sample records from {selected_table}"
        # List query
        elif 'list' in query_lower or 'show' in query_lower:
            sql = f'SELECT * FROM "{selected_table}" LIMIT 10'
            explanation = f"List first 10 records from {selected_table}"
        # Default
        else:
            sql = f'SELECT * FROM "{selected_table}" LIMIT 5'
            explanation = f"Sample 5 records from {selected_table}"
        
        return SQLQuery(
            sql=sql,
            confidence=0.3,
            target_tables=[selected_table],
            explanation=explanation + " (fallback query)",
            is_aggregation='count' in sql.lower(),
            is_join=False
        )