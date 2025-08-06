"""
Intelligent response formatter using Gemini for natural language formatting.
Transforms raw query results into user-friendly, insightful responses.
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from collections import Counter, defaultdict

from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

class ResponseMode(Enum):
    """Different formatting modes for various user needs."""
    STANDARD = "standard"
    EXECUTIVE = "executive"
    RESEARCH = "research"
    TECHNICAL = "technical"

class QueryType(Enum):
    """Types of queries for specialized formatting."""
    COUNT = "count"
    LIST = "list"
    DETAIL = "detail"
    AGGREGATE = "aggregate"
    SEARCH = "search"
    UNKNOWN = "unknown"

@dataclass
class Insight:
    """Represents an analytical insight derived from data."""
    key_finding: str
    supporting_data: Dict[str, Any]
    significance: float  # 0-1 score
    category: str  # e.g., "trend", "anomaly", "pattern"

@dataclass
class ResponseMetadata:
    """Metadata about the query and response."""
    query_type: QueryType
    row_count: int
    execution_time: float
    confidence: float
    tables_used: List[str]

@dataclass
class DebugInfo:
    """Debug information for troubleshooting."""
    raw_sql: str
    gemini_prompt: str
    gemini_response: str
    formatting_decisions: Dict[str, Any]

@dataclass
class FormattedResponse:
    """Complete formatted response with all layers of information."""
    raw_data: List[Dict[str, Any]]
    summary: str
    formatted_content: str
    insights: List[Insight] = field(default_factory=list)
    visualizations: List[str] = field(default_factory=list)
    metadata: Optional[ResponseMetadata] = None
    debug_info: Optional[DebugInfo] = None

class ResponseFormatter:
    """Transforms raw query results into intelligent, formatted responses."""
    
    def __init__(self, gemini_model=None, mode: ResponseMode = ResponseMode.STANDARD):
        self.gemini_model = gemini_model
        self.mode = mode
        self._query_patterns = self._init_query_patterns()
        
    def _init_query_patterns(self) -> Dict[QueryType, List[re.Pattern]]:
        """Initialize patterns for query type detection."""
        return {
            QueryType.COUNT: [
                re.compile(r'how many', re.I),
                re.compile(r'count.*?(?:of|the|all)', re.I),
                re.compile(r'total number', re.I),
                re.compile(r'number of', re.I)
            ],
            QueryType.LIST: [
                re.compile(r'list (?:all |the )?', re.I),
                re.compile(r'show (?:all |me |the )?', re.I),
                re.compile(r'what are (?:all |the )?', re.I),
                re.compile(r'give me (?:all |the )?', re.I)
            ],
            QueryType.DETAIL: [
                re.compile(r'show (?:me )?(?:details|info|information)', re.I),
                re.compile(r'tell me about', re.I),
                re.compile(r'describe', re.I),
                re.compile(r'explain', re.I)
            ],
            QueryType.AGGREGATE: [
                re.compile(r'group by', re.I),
                re.compile(r'by (?:category|domain|type|entity)', re.I),
                re.compile(r'breakdown', re.I),
                re.compile(r'distribution', re.I),
                re.compile(r'count.*?by\s+\w+', re.I)  # "count X by Y"
            ],
            QueryType.SEARCH: [
                re.compile(r'find.*?(?:with|where|that)', re.I),
                re.compile(r'search for', re.I),
                re.compile(r'filter.*?by', re.I),
                re.compile(r'risks? (?:in|from|about)', re.I)
            ]
        }
    
    def format_response(self, 
                       query: str,
                       raw_results: List[Dict[str, Any]],
                       sql_query: Optional[str] = None,
                       execution_time: float = 0.0,
                       tables_used: Optional[List[str]] = None,
                       data_context: Optional[Dict[str, Any]] = None,
                       debug: bool = False) -> FormattedResponse:
        """
        Format raw query results into a user-friendly response.
        
        Args:
            query: Original user query
            raw_results: Raw database results
            sql_query: SQL query that was executed
            execution_time: Query execution time
            tables_used: Tables involved in the query
            data_context: Additional context about the data
            debug: Whether to include debug information
            
        Returns:
            FormattedResponse with all formatting layers
        """
        # Detect query type
        query_type = self._detect_query_type(query)
        
        # Create metadata
        metadata = ResponseMetadata(
            query_type=query_type,
            row_count=len(raw_results),
            execution_time=execution_time,
            confidence=0.95,  # Will be updated by Gemini
            tables_used=tables_used or []
        )
        
        # Handle empty results
        if not raw_results:
            return self._format_empty_results(query, metadata, debug)
        
        # Format based on query type and mode
        logger.info(f"Formatting query type: {query_type.value}, mode: {self.mode.value}, gemini_available: {self.gemini_model is not None}")
        
        if query_type == QueryType.COUNT:
            formatted = self._format_count_response(query, raw_results, data_context)
        elif query_type == QueryType.LIST:
            formatted = self._format_list_response(query, raw_results, data_context)
        elif query_type == QueryType.DETAIL:
            formatted = self._format_detail_response(query, raw_results, data_context)
        elif query_type == QueryType.AGGREGATE:
            formatted = self._format_aggregate_response(query, raw_results, data_context)
        elif query_type == QueryType.SEARCH:
            formatted = self._format_search_response(query, raw_results, data_context)
        else:
            formatted = self._format_generic_response(query, raw_results, data_context)
        
        # Generate insights
        insights = self._generate_insights(raw_results, query_type, data_context)
        
        # Add debug info if requested
        debug_info = None
        if debug:
            debug_info = DebugInfo(
                raw_sql=sql_query or "N/A",
                gemini_prompt="",  # Will be filled when using Gemini
                gemini_response="",
                formatting_decisions={
                    "query_type": query_type.value,
                    "mode": self.mode.value,
                    "row_count": len(raw_results)
                }
            )
        
        return FormattedResponse(
            raw_data=raw_results,
            summary=formatted.get("summary", ""),
            formatted_content=formatted.get("content", ""),
            insights=insights,
            visualizations=formatted.get("visualizations", []),
            metadata=metadata,
            debug_info=debug_info
        )
    
    def _detect_query_type(self, query: str) -> QueryType:
        """Detect the type of query from the natural language."""
        query_lower = query.lower()
        
        # Check each pattern type
        for query_type, patterns in self._query_patterns.items():
            for pattern in patterns:
                if pattern.search(query_lower):
                    return query_type
        
        return QueryType.UNKNOWN
    
    def _format_count_response(self, query: str, results: List[Dict[str, Any]], 
                              context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Format count/statistical queries."""
        # Extract count value
        if results and len(results) == 1:
            # Find the count column (could be count(*), count_star(), etc.)
            count_col = None
            count_value = 0
            
            for key, value in results[0].items():
                if 'count' in key.lower() or key == 'total':
                    count_col = key
                    count_value = value
                    break
            
            # If no count column found, assume single value
            if count_col is None and len(results[0]) == 1:
                count_col, count_value = list(results[0].items())[0]
            
            # Use Gemini to create natural response
            if self.gemini_model:
                formatted = self._format_with_gemini_count(
                    query, count_value, context
                )
            else:
                # Fallback formatting
                formatted = self._fallback_count_format(
                    query, count_value, context
                )
            
            return formatted
        
        return {
            "summary": f"Found {len(results)} results",
            "content": str(results),
            "visualizations": []
        }
    
    def _format_list_response(self, query: str, results: List[Dict[str, Any]], 
                             context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Format list/enumeration queries."""
        if not results:
            return {"summary": "No items found", "content": "", "visualizations": []}
        
        # Determine what column(s) to display
        display_columns = self._identify_display_columns(results)
        
        if self.gemini_model:
            formatted = self._format_with_gemini_list(
                query, results, display_columns, context
            )
        else:
            formatted = self._fallback_list_format(
                query, results, display_columns, context
            )
        
        return formatted
    
    def _format_detail_response(self, query: str, results: List[Dict[str, Any]], 
                               context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Format detailed information queries."""
        if self.gemini_model:
            formatted = self._format_with_gemini_detail(query, results, context)
        else:
            formatted = self._fallback_detail_format(query, results, context)
        
        return formatted
    
    def _format_aggregate_response(self, query: str, results: List[Dict[str, Any]], 
                                  context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Format aggregation/grouping queries."""
        if self.gemini_model:
            formatted = self._format_with_gemini_aggregate(query, results, context)
        else:
            formatted = self._fallback_aggregate_format(query, results, context)
        
        return formatted
    
    def _format_search_response(self, query: str, results: List[Dict[str, Any]], 
                               context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Format search/filter queries."""
        summary = f"Found {len(results)} matching items"
        
        if len(results) > 10:
            summary += f" (showing first 10)"
            display_results = results[:10]
        else:
            display_results = results
        
        if self.gemini_model:
            formatted = self._format_with_gemini_search(
                query, display_results, len(results), context
            )
        else:
            formatted = self._fallback_search_format(
                query, display_results, len(results), context
            )
        
        return formatted
    
    def _format_generic_response(self, query: str, results: List[Dict[str, Any]], 
                                context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generic formatting for unknown query types."""
        if self.gemini_model:
            formatted = self._format_with_gemini_generic(query, results, context)
        else:
            formatted = self._fallback_generic_format(query, results, context)
        
        return formatted
    
    def _format_empty_results(self, query: str, metadata: ResponseMetadata, 
                             debug: bool) -> FormattedResponse:
        """Handle empty result sets."""
        suggestions = self._generate_query_suggestions(query)
        
        content = "No results found for your query.\n\n"
        if suggestions:
            content += "Try these alternative queries:\n"
            for i, suggestion in enumerate(suggestions, 1):
                content += f"{i}. {suggestion}\n"
        
        return FormattedResponse(
            raw_data=[],
            summary="No results found",
            formatted_content=content,
            insights=[],
            visualizations=[],
            metadata=metadata,
            debug_info=None
        )
    
    def _identify_display_columns(self, results: List[Dict[str, Any]]) -> List[str]:
        """Identify which columns are most important to display."""
        if not results:
            return []
        
        # Get all columns
        all_columns = list(results[0].keys())
        
        # Prioritize certain column names
        priority_patterns = [
            'name', 'title', 'domain', 'category', 'type', 
            'description', 'risk', 'count', 'total'
        ]
        
        display_cols = []
        
        # First pass: exact matches
        for col in all_columns:
            if col.lower() in priority_patterns:
                display_cols.append(col)
        
        # Second pass: partial matches
        if not display_cols:
            for col in all_columns:
                for pattern in priority_patterns:
                    if pattern in col.lower():
                        display_cols.append(col)
                        break
        
        # If still no columns, just take first few
        if not display_cols:
            display_cols = all_columns[:3]
        
        return display_cols
    
    def _generate_insights(self, results: List[Dict[str, Any]], 
                          query_type: QueryType,
                          context: Optional[Dict[str, Any]]) -> List[Insight]:
        """Generate analytical insights from the results."""
        insights = []
        
        if not results:
            return insights
        
        # Different insight generation based on query type
        if query_type == QueryType.COUNT:
            insights.extend(self._generate_count_insights(results, context))
        elif query_type == QueryType.AGGREGATE:
            insights.extend(self._generate_aggregate_insights(results, context))
        elif len(results) > 10:
            insights.extend(self._generate_pattern_insights(results, context))
        
        return insights
    
    def _generate_count_insights(self, results: List[Dict[str, Any]], 
                                context: Optional[Dict[str, Any]]) -> List[Insight]:
        """Generate insights for count queries."""
        insights = []
        
        if results and context and 'tables' in context:
            # Get the count value
            count_value = 0
            for key, value in results[0].items():
                if 'count' in key.lower():
                    count_value = value
                    break
            
            # Compare to total rows in table
            for table_name, table_info in context['tables'].items():
                if 'row_count' in table_info:
                    total = table_info['row_count']
                    if total > 0:
                        percentage = (count_value / total) * 100
                        if percentage < 100:
                            insights.append(Insight(
                                key_finding=f"This represents {percentage:.1f}% of all records",
                                supporting_data={"count": count_value, "total": total},
                                significance=0.7,
                                category="proportion"
                            ))
                        break
        
        return insights
    
    def _generate_aggregate_insights(self, results: List[Dict[str, Any]], 
                                    context: Optional[Dict[str, Any]]) -> List[Insight]:
        """Generate insights for aggregate queries."""
        insights = []
        
        # Find the top categories
        if len(results) > 3:
            # Assume first column is category, second is count
            if len(results[0]) >= 2:
                cols = list(results[0].keys())
                cat_col = cols[0]
                count_col = cols[1]
                
                # Get top 3
                sorted_results = sorted(results, 
                                      key=lambda x: x.get(count_col, 0), 
                                      reverse=True)
                top_3 = sorted_results[:3]
                
                top_categories = [r[cat_col] for r in top_3]
                top_counts = [r[count_col] for r in top_3]
                
                insights.append(Insight(
                    key_finding=f"Top 3 categories: {', '.join(str(c) for c in top_categories)}",
                    supporting_data={"categories": top_categories, "counts": top_counts},
                    significance=0.8,
                    category="ranking"
                ))
        
        return insights
    
    def _generate_pattern_insights(self, results: List[Dict[str, Any]], 
                                  context: Optional[Dict[str, Any]]) -> List[Insight]:
        """Generate insights about patterns in large result sets."""
        insights = []
        
        # Analyze common values in results
        for col in results[0].keys():
            if col.lower() in ['domain', 'category', 'type', 'entity']:
                values = [r.get(col) for r in results if r.get(col)]
                if values:
                    value_counts = Counter(values)
                    most_common = value_counts.most_common(1)[0]
                    if most_common[1] > len(results) * 0.3:  # > 30% of results
                        insights.append(Insight(
                            key_finding=f"Most common {col}: {most_common[0]} ({most_common[1]} occurrences)",
                            supporting_data={"column": col, "value": most_common[0], "count": most_common[1]},
                            significance=0.6,
                            category="pattern"
                        ))
        
        return insights
    
    def _generate_query_suggestions(self, original_query: str) -> List[str]:
        """Generate alternative query suggestions for empty results."""
        suggestions = []
        
        # Simple suggestions based on query type
        if "domain" in original_query.lower():
            suggestions.append("List all domains")
            suggestions.append("Show risk categories")
        elif "risk" in original_query.lower():
            suggestions.append("How many risks are in the database?")
            suggestions.append("Show all risk categories")
        elif "count" in original_query.lower() or "how many" in original_query.lower():
            suggestions.append("Show database statistics")
            suggestions.append("List all tables")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    # Fallback formatting methods (when Gemini is not available)
    
    def _fallback_count_format(self, query: str, count: int, 
                              context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple count formatting without Gemini."""
        return {
            "summary": f"Count result: {count}",
            "content": f"**Result**: {count}",
            "visualizations": []
        }
    
    def _fallback_list_format(self, query: str, results: List[Dict[str, Any]], 
                             display_cols: List[str], 
                             context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple list formatting without Gemini."""
        # Filter out None/null values
        filtered_results = []
        for result in results:
            # Check if all display columns are None
            has_value = False
            for col in display_cols:
                if result.get(col) is not None:
                    has_value = True
                    break
            if has_value:
                filtered_results.append(result)
        
        # Sort results if they look like domains (start with number)
        if filtered_results and display_cols:
            first_col = display_cols[0]
            # Check if values start with numbers
            sample_val = str(filtered_results[0].get(first_col, ''))
            if sample_val and sample_val[0].isdigit():
                try:
                    filtered_results.sort(key=lambda x: int(str(x.get(first_col, '999'))[0]) if str(x.get(first_col, '')).strip() and str(x.get(first_col, ''))[0].isdigit() else 999)
                except:
                    pass
        
        content_lines = [f"Found {len(filtered_results)} items:\n"]
        
        for i, result in enumerate(filtered_results, 1):
            if display_cols:
                values = [str(result.get(col, 'N/A')) for col in display_cols if result.get(col) is not None]
                content_lines.append(f"{i}. {' - '.join(values)}")
            else:
                content_lines.append(f"{i}. {result}")
        
        return {
            "summary": f"Found {len(filtered_results)} items",
            "content": '\n'.join(content_lines),
            "visualizations": []
        }
    
    def _fallback_detail_format(self, query: str, results: List[Dict[str, Any]], 
                               context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple detail formatting without Gemini."""
        if len(results) == 1:
            content_lines = ["**Details:**\n"]
            for key, value in results[0].items():
                if value is not None:
                    content_lines.append(f"- {key}: {value}")
        else:
            content_lines = [f"Found {len(results)} items. Showing first 5:\n"]
            for i, result in enumerate(results[:5], 1):
                content_lines.append(f"\n**Item {i}:**")
                for key, value in result.items():
                    if value is not None:
                        content_lines.append(f"  - {key}: {value}")
        
        return {
            "summary": f"Showing details for {len(results)} item(s)",
            "content": '\n'.join(content_lines),
            "visualizations": []
        }
    
    def _fallback_aggregate_format(self, query: str, results: List[Dict[str, Any]], 
                                  context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple aggregate formatting without Gemini."""
        if not results:
            return {"summary": "No results", "content": "No aggregated data found.", "visualizations": []}
        
        # Calculate total for percentages
        count_col = None
        for key in results[0].keys():
            if 'count' in key.lower():
                count_col = key
                break
        
        total = 0
        if count_col:
            total = sum(r.get(count_col, 0) for r in results)
        
        # Sort by count if possible
        if count_col:
            results = sorted(results, key=lambda x: x.get(count_col, 0), reverse=True)
        
        content_lines = [f"**Aggregated Results** ({len(results)} groups, {total} total):\n"]
        
        for result in results:
            line_parts = []
            for key, value in result.items():
                if value is None:
                    display_value = "Not specified"
                else:
                    display_value = str(value)
                    # Add percentage if this is the count column
                    if key == count_col and total > 0:
                        percentage = (value / total) * 100
                        display_value += f" ({percentage:.1f}%)"
                line_parts.append(f"{key}: {display_value}")
            content_lines.append("- " + ", ".join(line_parts))
        
        return {
            "summary": f"Aggregated into {len(results)} groups",
            "content": '\n'.join(content_lines),
            "visualizations": []
        }
    
    def _fallback_search_format(self, query: str, results: List[Dict[str, Any]], 
                               total_count: int, 
                               context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple search result formatting without Gemini."""
        content_lines = [f"**Search Results** ({total_count} total matches):\n"]
        
        if total_count > len(results):
            content_lines.append(f"Showing first {len(results)} results:\n")
        
        for i, result in enumerate(results, 1):
            # Try to show title/name and description
            title = result.get('title') or result.get('name') or f"Result {i}"
            desc = result.get('description', '')
            if desc and len(desc) > 100:
                desc = desc[:100] + "..."
            
            content_lines.append(f"{i}. **{title}**")
            if desc:
                content_lines.append(f"   {desc}")
            content_lines.append("")
        
        return {
            "summary": f"Found {total_count} matches",
            "content": '\n'.join(content_lines),
            "visualizations": []
        }
    
    def _fallback_generic_format(self, query: str, results: List[Dict[str, Any]], 
                                context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generic fallback formatting."""
        if len(results) <= 5:
            content = json.dumps(results, indent=2)
        else:
            content = f"Found {len(results)} results. Showing first 5:\n\n"
            content += json.dumps(results[:5], indent=2)
        
        return {
            "summary": f"Query returned {len(results)} results",
            "content": content,
            "visualizations": []
        }
    
    # Gemini-powered formatting methods (to be implemented)
    
    def _format_with_gemini_count(self, query: str, count: int, 
                                 context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Use Gemini to format count responses intelligently."""
        try:
            # Initialize Gemini if needed
            if not self.gemini_model:
                from ...core.models.gemini import GeminiModel
                self.gemini_model = GeminiModel(settings.GEMINI_API_KEY)
            
            # Build context for Gemini
            context_info = ""
            if context and 'tables' in context:
                # Find relevant table info
                for table_name, table_info in context['tables'].items():
                    if 'row_count' in table_info:
                        total = table_info['row_count']
                        percentage = (count / total * 100) if total > 0 else 0
                        context_info += f"\nTotal {table_name} records: {total}"
                        if percentage < 100:
                            context_info += f" ({percentage:.1f}% of total)"
            
            # Create prompt based on mode
            mode_instructions = {
                ResponseMode.STANDARD: "Be clear and informative",
                ResponseMode.EXECUTIVE: "Be very concise, focus on business impact",
                ResponseMode.RESEARCH: "Include detailed context and methodology notes",
                ResponseMode.TECHNICAL: "Include technical details and data structure info"
            }
            
            prompt = f"""Format this count query result into a natural, professional response.

User Query: "{query}"
Count Result: {count}
{context_info}

Instructions:
- {mode_instructions.get(self.mode, mode_instructions[ResponseMode.STANDARD])}
- Do NOT use emojis or casual language
- Include the count prominently
- Add relevant context if available
- For executive mode, limit to 2-3 sentences max
- For research mode, explain what the count represents

Provide the response in this JSON format:
{{
    "summary": "One-line summary of the finding",
    "content": "Full formatted response with markdown formatting",
    "key_insight": "Most important takeaway (optional)"
}}"""

            response = self.gemini_model.generate(prompt)
            
            # Parse JSON response
            import json
            try:
                # Handle case where Gemini returns JSON in code blocks
                if '```json' in response:
                    json_start = response.find('```json') + 7
                    json_end = response.find('```', json_start)
                    json_str = response[json_start:json_end].strip()
                    formatted_data = json.loads(json_str)
                else:
                    formatted_data = json.loads(response)
                
                visualizations = []
                # Add simple text visualization if percentage is available
                if context_info and "%" in context_info:
                    percentage = float(context_info.split("(")[1].split("%")[0])
                    bar_length = 20
                    filled = int(percentage / 100 * bar_length)
                    bar = "[" + "█" * filled + "░" * (bar_length - filled) + f"] {percentage:.1f}%"
                    visualizations.append(bar)
                
                return {
                    "summary": formatted_data.get("summary", f"Count: {count}"),
                    "content": formatted_data.get("content", f"**Result**: {count}"),
                    "visualizations": visualizations
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, use the response as content
                return {
                    "summary": f"Count result: {count}",
                    "content": response,
                    "visualizations": []
                }
                
        except Exception as e:
            logger.warning(f"Gemini formatting failed: {str(e)}")
            return self._fallback_count_format(query, count, context)
    
    def _format_with_gemini_list(self, query: str, results: List[Dict[str, Any]], 
                                display_cols: List[str], 
                                context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Use Gemini to format list responses intelligently."""
        try:
            if not self.gemini_model:
                from ...core.models.gemini import GeminiModel
                self.gemini_model = GeminiModel(settings.GEMINI_API_KEY)
            
            # Prepare data for Gemini
            sample_results = results[:20] if len(results) > 20 else results
            
            # Extract unique values from display columns
            unique_values = {}
            for col in display_cols:
                values = [r.get(col) for r in results if r.get(col) is not None]
                unique_values[col] = list(set(values))[:10]  # Limit to 10 unique values
            
            prompt = f"""Format this list query result into a well-organized, professional response.

User Query: "{query}"
Total Items: {len(results)}
Display Columns: {display_cols}
Sample Data: {json.dumps(sample_results, indent=2)}
Unique Values per Column: {json.dumps(unique_values, indent=2)}

Instructions:
- Create a clean, scannable list
- If the data represents categories/domains, number them appropriately
- Remove null/None values from display
- Sort logically (alphabetically or by importance)
- For domains like "1. Topic", "2. Topic", maintain the numeric order
- Use markdown formatting for clarity
- Mode: {self.mode.value} - adjust detail level accordingly
- NO emojis or casual language

Provide the response in this JSON format:
{{
    "summary": "Brief description of what was found",
    "content": "Formatted list with appropriate markdown",
    "organization": "How the list is organized (e.g., 'Sorted by domain number')"
}}"""

            response = self.gemini_model.generate(prompt)
            
            try:
                # Handle case where Gemini returns JSON in code blocks
                if '```json' in response:
                    json_start = response.find('```json') + 7
                    json_end = response.find('```', json_start)
                    json_str = response[json_start:json_end].strip()
                    formatted_data = json.loads(json_str)
                else:
                    formatted_data = json.loads(response)
                return {
                    "summary": formatted_data.get("summary", f"Found {len(results)} items"),
                    "content": formatted_data.get("content", self._fallback_list_format(query, results, display_cols, context)["content"]),
                    "visualizations": []
                }
            except json.JSONDecodeError:
                return {
                    "summary": f"Found {len(results)} items",
                    "content": response,
                    "visualizations": []
                }
                
        except Exception as e:
            logger.warning(f"Gemini list formatting failed: {str(e)}")
            return self._fallback_list_format(query, results, display_cols, context)
    
    def _format_with_gemini_detail(self, query: str, results: List[Dict[str, Any]], 
                                  context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Use Gemini to format detail responses intelligently."""
        # TODO: Implement Gemini formatting
        return self._fallback_detail_format(query, results, context)
    
    def _format_with_gemini_aggregate(self, query: str, results: List[Dict[str, Any]], 
                                     context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Use Gemini to format aggregate responses intelligently."""
        try:
            if not self.gemini_model:
                from ...core.models.gemini import GeminiModel
                self.gemini_model = GeminiModel(settings.GEMINI_API_KEY)
            
            # Prepare aggregation data
            total_count = sum(r.get(list(r.keys())[1], 0) if len(r) > 1 else 0 for r in results)
            
            prompt = f"""Format this aggregation query result into a clear, professional response.

User Query: "{query}"
Aggregated Results: {json.dumps(results, indent=2)}
Total Count: {total_count}

Instructions:
- Create a well-formatted table or list showing the aggregated data
- Replace null/None values with "Not specified" or similar
- Include percentages for each group
- Sort by count (descending) or logical order
- Add a summary line with the total
- Mode: {self.mode.value}
- Professional tone, no emojis

Provide the response in this JSON format:
{{
    "summary": "Brief summary of the aggregation",
    "content": "Formatted table/list with markdown",
    "key_finding": "Most important insight from the data"
}}"""

            response = self.gemini_model.generate(prompt)
            
            try:
                # Handle JSON in code blocks
                if '```json' in response:
                    json_start = response.find('```json') + 7
                    json_end = response.find('```', json_start)
                    json_str = response[json_start:json_end].strip()
                    formatted_data = json.loads(json_str)
                else:
                    formatted_data = json.loads(response)
                
                return {
                    "summary": formatted_data.get("summary", f"Aggregated into {len(results)} groups"),
                    "content": formatted_data.get("content", ""),
                    "visualizations": []
                }
            except json.JSONDecodeError:
                return {
                    "summary": f"Aggregated into {len(results)} groups",
                    "content": response,
                    "visualizations": []
                }
                
        except Exception as e:
            logger.warning(f"Gemini aggregate formatting failed: {str(e)}")
            return self._fallback_aggregate_format(query, results, context)
    
    def _format_with_gemini_search(self, query: str, results: List[Dict[str, Any]], 
                                  total_count: int, 
                                  context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Use Gemini to format search responses intelligently."""
        try:
            if not self.gemini_model:
                from ...core.models.gemini import GeminiModel
                self.gemini_model = GeminiModel(settings.GEMINI_API_KEY)
            
            # Identify key fields
            key_fields = []
            for field in ['title', 'risk_category', 'domain', 'subdomain', 'description', 
                         'entity', 'timing', 'intent']:
                if results and field in results[0]:
                    key_fields.append(field)
            
            prompt = f"""Format these AI risk search results into a clear, organized response.

User Query: "{query}"
Total Results: {total_count}
Showing: {len(results)} results
Key Fields Available: {key_fields}
Sample Results: {json.dumps(results[:3], indent=2)}

Instructions:
- Create a well-structured summary of the search results
- For each risk, show: title/ID, category, domain, and brief description
- Group by subdomain or category if patterns emerge
- Truncate long descriptions to ~100 characters
- Highlight the most relevant information based on the query
- If showing a subset, mention how many total results exist
- Use markdown for formatting (bold titles, bullet points)
- Mode: {self.mode.value}
- Professional tone, no emojis

Format as JSON:
{{
    "summary": "Executive summary of findings",
    "content": "Formatted results with markdown",
    "patterns": "Any patterns noticed in the results (optional)"
}}"""

            response = self.gemini_model.generate(prompt)
            
            try:
                # Handle case where Gemini returns JSON in code blocks
                if '```json' in response:
                    json_start = response.find('```json') + 7
                    json_end = response.find('```', json_start)
                    json_str = response[json_start:json_end].strip()
                    formatted_data = json.loads(json_str)
                else:
                    formatted_data = json.loads(response)
                
                # Add visualization if we have category distribution
                visualizations = []
                if len(results) > 5:
                    # Count by domain or category
                    domain_counts = Counter(r.get('domain', 'Unknown') for r in results)
                    if domain_counts:
                        viz = "Domain Distribution:\n"
                        for domain, count in domain_counts.most_common(5):
                            if domain:
                                bar_length = int(count / len(results) * 20)
                                viz += f"{domain[:30]:30} [{'█' * bar_length:20}] {count}\n"
                        visualizations.append(viz)
                
                return {
                    "summary": formatted_data.get("summary", f"Found {total_count} matching risks"),
                    "content": formatted_data.get("content", ""),
                    "visualizations": visualizations
                }
            except json.JSONDecodeError:
                return {
                    "summary": f"Found {total_count} matching risks",
                    "content": response,
                    "visualizations": []
                }
                
        except Exception as e:
            logger.warning(f"Gemini search formatting failed: {str(e)}")
            return self._fallback_search_format(query, results, total_count, context)
    
    def _format_with_gemini_generic(self, query: str, results: List[Dict[str, Any]], 
                                   context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Use Gemini to format generic responses intelligently."""
        try:
            # Prepare data sample for Gemini
            sample_results = results[:3]  # Use first 3 results as examples
            total_count = len(results)
            
            # Extract field names and types to help Gemini understand the data structure
            field_info = {}
            if results:
                for key, value in results[0].items():
                    field_info[key] = type(value).__name__
            
            # Create a focused prompt for response synthesis
            prompt = f"""You are helping analyze AI risk data. A user asked: "{query}"

The query found {total_count} results. Here are the first few examples:

{json.dumps(sample_results, indent=2)}

Field types: {field_info}

Please create a clear, informative response that:
1. Summarizes what was found in natural language
2. Highlights the most important insights
3. Uses specific examples from the data
4. Avoids dumping raw JSON - synthesize the information

Focus on the content that would be most relevant to someone asking about "{query}".

Respond in this JSON format:
{{
    "summary": "Brief overview of findings",
    "content": "Detailed explanation with specific examples and insights"
}}"""

            # Generate response with Gemini
            response = self.gemini_model.generate(prompt)
            
            # Parse Gemini response
            try:
                # Clean up the response to extract JSON
                response_clean = response.strip()
                if response_clean.startswith('```json'):
                    response_clean = response_clean.replace('```json', '', 1)
                    response_clean = response_clean.replace('```', '', 1)
                
                formatted_data = json.loads(response_clean.strip())
                
                # Validate the response structure
                if not isinstance(formatted_data, dict) or 'content' not in formatted_data:
                    raise ValueError("Invalid response structure")
                
                # Add metadata and visualizations if applicable
                response_dict = {
                    "summary": formatted_data.get("summary", f"Found {total_count} results"),
                    "content": formatted_data.get("content", ""),
                    "visualizations": []
                }
                
                # Only add visualization for non-metadata queries with large datasets
                # Check if this is a metadata query by looking for specific fields
                is_metadata_query = False
                if results and isinstance(results[0], dict):
                    # Check for metadata-specific fields
                    metadata_fields = {'risk_id', 'domain', 'category', 'category_level', 'risk_category'}
                    if any(field in results[0] for field in metadata_fields):
                        is_metadata_query = True
                
                # Only add statistics for non-metadata queries
                if total_count > 10 and not is_metadata_query:
                    viz_text = f"Dataset Statistics:\n"
                    viz_text += f"Total Results: {total_count}\n"
                    viz_text += f"Showing Analysis: {min(10, total_count)} samples analyzed\n"
                    
                    # Add field distribution if meaningful
                    if results and isinstance(results[0], dict):
                        field_count = len(results[0].keys())
                        viz_text += f"Data Fields: {field_count} attributes per record"
                    
                    response_dict["visualizations"] = [viz_text]
                
                return response_dict
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse Gemini response for generic formatting: {e}")
                # Create a fallback that still uses the Gemini content but with safe structure
                return {
                    "summary": f"Found {total_count} results for: {query}",
                    "content": response.strip(),
                    "visualizations": []
                }
                
        except Exception as e:
            logger.error(f"Gemini generic formatting failed: {e}")
            # Fall back to the original method but with better formatting
            return self._enhanced_generic_fallback(query, results, context)
    
    def _enhanced_generic_fallback(self, query: str, results: List[Dict[str, Any]], 
                                  context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhanced fallback formatting that's better than raw JSON."""
        total_count = len(results)
        
        if not results:
            return {
                "summary": "No results found",
                "content": f"Your query '{query}' didn't return any matching data.",
                "visualizations": []
            }
        
        # Create a more readable summary
        content_lines = [f"Found {total_count} results for your query about: **{query}**\n"]
        
        # Show key fields from first few results
        display_results = results[:5]
        
        for i, result in enumerate(display_results, 1):
            content_lines.append(f"**Result {i}:**")
            
            # Format each field nicely
            for key, value in result.items():
                if value is not None and str(value).strip():
                    # Clean up the key name
                    clean_key = key.replace('_', ' ').title()
                    
                    # Format the value based on type
                    if isinstance(value, str) and len(value) > 100:
                        # Truncate long strings
                        clean_value = value[:100] + "..."
                    else:
                        clean_value = str(value)
                    
                    content_lines.append(f"  - **{clean_key}**: {clean_value}")
            
            content_lines.append("")  # Add spacing between results
        
        if total_count > 5:
            content_lines.append(f"*({total_count - 5} additional results available)*")
        
        return {
            "summary": f"Query returned {total_count} results",
            "content": '\n'.join(content_lines),
            "visualizations": []
        }