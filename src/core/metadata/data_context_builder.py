"""
Builds comprehensive data context for Gemini including actual data samples.
"""
import json
from typing import Dict, List, Any, Optional
from collections import defaultdict
import duckdb
from ...config.logging import get_logger

logger = get_logger(__name__)

class DataContextBuilder:
    """Builds rich context about the actual data for better SQL generation."""
    
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self.connection = connection
        
    def build_full_context(self, sample_size: int = 100, 
                          max_distinct_values: int = 50) -> Dict[str, Any]:
        """
        Build comprehensive context including actual data samples.
        
        Args:
            sample_size: Number of sample rows to include per table
            max_distinct_values: Max distinct values to show per column
            
        Returns:
            Complete data context dictionary
        """
        context = {
            "tables": {},
            "total_rows": 0,
            "summary": ""
        }
        
        # Get all tables
        tables = self.connection.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        
        for (table_name,) in tables:
            try:
                table_context = self._analyze_table(
                    table_name, 
                    sample_size, 
                    max_distinct_values
                )
                
                if table_context["row_count"] > 0:  # Only include non-empty tables
                    context["tables"][table_name] = table_context
                    context["total_rows"] += table_context["row_count"]
                    
            except Exception as e:
                logger.warning(f"Error analyzing table {table_name}: {str(e)}")
                continue
        
        # Add summary
        context["summary"] = self._generate_summary(context)
        
        return context
    
    def _analyze_table(self, table_name: str, sample_size: int, 
                      max_distinct_values: int) -> Dict[str, Any]:
        """Analyze a single table in detail."""
        
        # Get row count
        row_count = self.connection.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]
        
        # Get column info
        columns = self.connection.execute(
            f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
            """
        ).fetchall()
        
        # Get sample data
        sample_data = []
        if row_count > 0:
            sample_rows = self.connection.execute(
                f'SELECT * FROM "{table_name}" LIMIT {sample_size}'
            ).fetchall()
            
            column_names = [col[0] for col in columns]
            sample_data = [
                dict(zip(column_names, row)) 
                for row in sample_rows
            ]
        
        # Analyze each column
        column_analysis = {}
        for col_name, col_type in columns:
            col_info = {
                "type": col_type,
                "distinct_count": 0,
                "null_count": 0,
                "sample_values": [],
                "distinct_values": []
            }
            
            try:
                # Count nulls
                null_count = self.connection.execute(
                    f'SELECT COUNT(*) FROM "{table_name}" WHERE "{col_name}" IS NULL'
                ).fetchone()[0]
                col_info["null_count"] = null_count
                
                # Count distinct values
                distinct_count = self.connection.execute(
                    f'SELECT COUNT(DISTINCT "{col_name}") FROM "{table_name}"'
                ).fetchone()[0]
                col_info["distinct_count"] = distinct_count
                
                # Get distinct values if reasonable count
                if distinct_count > 0 and distinct_count <= max_distinct_values:
                    distinct_values = self.connection.execute(
                        f"""
                        SELECT DISTINCT "{col_name}" 
                        FROM "{table_name}" 
                        WHERE "{col_name}" IS NOT NULL
                        ORDER BY "{col_name}"
                        LIMIT {max_distinct_values}
                        """
                    ).fetchall()
                    col_info["distinct_values"] = [v[0] for v in distinct_values]
                
                # Get sample values
                elif distinct_count > 0:
                    samples = self.connection.execute(
                        f"""
                        SELECT DISTINCT "{col_name}" 
                        FROM "{table_name}" 
                        WHERE "{col_name}" IS NOT NULL
                        LIMIT 10
                        """
                    ).fetchall()
                    col_info["sample_values"] = [v[0] for v in samples]
                    
            except Exception as e:
                logger.debug(f"Error analyzing column {table_name}.{col_name}: {str(e)}")
            
            column_analysis[col_name] = col_info
        
        # Determine table purpose
        table_purpose = self._infer_table_purpose(table_name, column_analysis, sample_data)
        
        return {
            "row_count": row_count,
            "columns": column_analysis,
            "sample_data": sample_data[:10],  # Limit sample for context size
            "purpose": table_purpose,
            "primary_columns": self._identify_primary_columns(column_analysis)
        }
    
    def _infer_table_purpose(self, table_name: str, columns: Dict[str, Any], 
                            sample_data: List[Dict[str, Any]]) -> str:
        """Infer the purpose of a table from its structure and data."""
        
        # Check table name patterns
        if "risk" in table_name.lower():
            if "database" in table_name.lower():
                return "Main AI risk database with detailed risk information"
            elif "taxonomy" in table_name.lower():
                return "Risk classification and categorization"
        
        if "domain" in table_name.lower():
            return "Domain classification for AI risks"
            
        if "change" in table_name.lower() or "log" in table_name.lower():
            return "Change history and updates log"
            
        if "content" in table_name.lower():
            return "Text content and descriptions"
        
        # Check by columns
        col_names = set(columns.keys())
        if "risk_category" in col_names or "risk_subcategory" in col_names:
            return "Risk categorization data"
        
        if "entity" in col_names and "intent" in col_names:
            return "Risk classification by entity and intent"
            
        # Check data patterns
        if len(columns) == 1:
            return "Single-column reference data"
        elif len(columns) > 10:
            return "Detailed records with multiple attributes"
        
        return "General data table"
    
    def _identify_primary_columns(self, columns: Dict[str, Any]) -> List[str]:
        """Identify the most important columns in a table."""
        primary = []
        
        for col_name, col_info in columns.items():
            # Skip columns with mostly nulls
            if col_info["null_count"] > col_info.get("row_count", 0) * 0.8:
                continue
                
            # Primary candidates
            if any(term in col_name.lower() for term in 
                   ["id", "title", "name", "category", "domain", "entity", "risk"]):
                primary.append(col_name)
            
            # Columns with reasonable distinct values
            elif 0 < col_info["distinct_count"] < 100:
                primary.append(col_name)
        
        return primary[:10]  # Limit to top 10
    
    def _generate_summary(self, context: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the data."""
        
        summaries = []
        
        # Find main tables
        main_tables = []
        for table_name, info in context["tables"].items():
            if info["row_count"] > 100:
                main_tables.append((table_name, info))
        
        # Sort by row count
        main_tables.sort(key=lambda x: x[1]["row_count"], reverse=True)
        
        # Summarize main tables
        for table_name, info in main_tables[:5]:
            summaries.append(
                f"- {table_name}: {info['row_count']:,} rows - {info['purpose']}"
            )
        
        summary = f"""Database contains {len(context['tables'])} tables with {context['total_rows']:,} total rows.

Main tables:
""" + "\n".join(summaries)
        
        return summary
    
    def export_context_for_prompt(self, context: Dict[str, Any], 
                                 max_chars: int = 50000) -> str:
        """
        Export context in a format suitable for including in prompts.
        
        Args:
            context: Full context dictionary
            max_chars: Maximum characters to include
            
        Returns:
            Formatted string for prompt inclusion
        """
        output = ["=== DATABASE CONTEXT ===\n"]
        output.append(context["summary"])
        output.append("\n\n=== TABLE DETAILS ===\n")
        
        # Prioritize tables by importance
        tables_by_rows = sorted(
            context["tables"].items(), 
            key=lambda x: x[1]["row_count"], 
            reverse=True
        )
        
        for table_name, table_info in tables_by_rows:
            if len("\n".join(output)) > max_chars * 0.8:
                output.append("\n... (truncated for space)")
                break
                
            output.append(f"\n### Table: {table_name}")
            output.append(f"Purpose: {table_info['purpose']}")
            output.append(f"Rows: {table_info['row_count']:,}")
            output.append("Key Columns:")
            
            # Show important columns with examples
            for col_name in table_info["primary_columns"][:8]:
                col_info = table_info["columns"][col_name]
                output.append(f"  - {col_name} ({col_info['type']})")
                
                if col_info["distinct_values"]:
                    # Show all distinct values if not too many
                    if len(col_info["distinct_values"]) <= 10:
                        values_str = ", ".join(
                            f'"{v}"' if isinstance(v, str) else str(v) 
                            for v in col_info["distinct_values"]
                        )
                        output.append(f"    Values: {values_str}")
                    else:
                        # Show sample
                        sample = col_info["distinct_values"][:5]
                        values_str = ", ".join(
                            f'"{v}"' if isinstance(v, str) else str(v) 
                            for v in sample
                        )
                        output.append(f"    Sample values: {values_str}... ({col_info['distinct_count']} distinct)")
                elif col_info["sample_values"]:
                    sample = col_info["sample_values"][:3]
                    values_str = ", ".join(
                        f'"{v}"' if isinstance(v, str) else str(v) 
                        for v in sample
                    )
                    output.append(f"    Examples: {values_str}")
            
            # Show sample rows
            if table_info["sample_data"] and len("\n".join(output)) < max_chars * 0.7:
                output.append("\nSample rows:")
                for i, row in enumerate(table_info["sample_data"][:3]):
                    row_str = ", ".join(
                        f"{k}={repr(v)[:50]}" 
                        for k, v in row.items() 
                        if k in table_info["primary_columns"]
                    )
                    output.append(f"  Row {i+1}: {row_str}")
        
        return "\n".join(output)