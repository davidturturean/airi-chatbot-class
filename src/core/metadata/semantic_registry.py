"""
Semantic table registry for intelligent query routing.
"""
import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from ...config.logging import get_logger

logger = get_logger(__name__)

@dataclass
class TableSemantics:
    """Semantic information about a table."""
    table_name: str
    semantic_type: str  # e.g., "risks", "taxonomy", "statistics", "changelog"
    domain_keywords: Set[str] = field(default_factory=set)
    description: str = ""
    example_content: Optional[str] = None
    primary_entity: Optional[str] = None  # e.g., "ai_risk", "resource", "category"
    data_quality: Dict[str, Any] = field(default_factory=dict)  # row count, completeness, etc.
    
class SemanticTableRegistry:
    """Registry that maps tables to their semantic meaning."""
    
    def __init__(self):
        self.registry: Dict[str, TableSemantics] = {}
        self.semantic_patterns = self._init_semantic_patterns()
        
    def _init_semantic_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for semantic detection."""
        return {
            "risks": {
                "patterns": [
                    r"risk", r"hazard", r"threat", r"danger", r"vulnerability",
                    r"rid[-_]?\d+", r"ai_risk", r"risk_database", r"causal.*taxonom"
                ],
                "keywords": {"risk", "hazard", "threat", "safety", "danger", "vulnerability", "harm", 
                           "entity", "intent", "timing", "causal"},
                "entity": "ai_risk",
                "priority": 10  # Highest priority for main risk data
            },
            "taxonomy": {
                "patterns": [r"taxonomy", r"classification", r"categorization", r"hierarchy", r"domain.*taxonom"],
                "keywords": {"taxonomy", "category", "classification", "domain", "type", "subdomain"},
                "entity": "category",
                "priority": 8
            },
            "statistics": {
                "patterns": [r"statistic", r"stats", r"count", r"summary", r"metric"],
                "keywords": {"statistics", "count", "total", "summary", "metrics", "analysis"},
                "entity": "metric",
                "priority": 5
            },
            "resources": {
                "patterns": [r"resource", r"source", r"reference", r"paper", r"document"],
                "keywords": {"resource", "source", "paper", "document", "reference", "publication"},
                "entity": "resource",
                "priority": 6
            },
            "changelog": {
                "patterns": [r"change", r"log", r"history", r"update", r"revision"],
                "keywords": {"change", "update", "history", "version", "revision", "log"},
                "entity": "change_entry",
                "priority": 3
            },
            "content": {
                "patterns": [r"content", r"text", r"description", r"snippet", r"^contents$"],
                "keywords": {"content", "text", "description", "snippet", "excerpt"},
                "entity": "content",
                "priority": 7
            },
            "metadata": {
                "patterns": [r"explainer", r"what_we", r"metadata", r"about"],
                "keywords": {"explainer", "metadata", "coded", "extracted", "about"},
                "entity": "metadata",
                "priority": 2  # Low priority - use only if no better match
            }
        }
    
    def register_table(self, table_name: str, metadata: Dict[str, Any], 
                      sample_data: Optional[List[Dict[str, Any]]] = None):
        """Register a table with semantic information."""
        # Detect semantic type
        semantic_type = self._detect_semantic_type(table_name, metadata, sample_data)
        
        # Build keywords from actual data
        keywords = self._extract_keywords(table_name, metadata, sample_data)
        
        # Add data-based keywords
        if sample_data:
            # Extract keywords from actual column values
            data_keywords = self._extract_data_keywords(sample_data)
            keywords.update(data_keywords)
        
        # Generate description
        description = self._generate_description(table_name, semantic_type, metadata, sample_data)
        
        # Analyze data quality
        data_quality = self._analyze_data_quality(sample_data) if sample_data else {}
        
        # Create semantic entry
        semantics = TableSemantics(
            table_name=table_name,
            semantic_type=semantic_type,
            domain_keywords=keywords,
            description=description,
            primary_entity=self.semantic_patterns.get(semantic_type, {}).get("entity"),
            data_quality=data_quality
        )
        
        self.registry[table_name] = semantics
        logger.info(f"Registered table '{table_name}' as type '{semantic_type}' with {len(keywords)} keywords")
        
    def _detect_semantic_type(self, table_name: str, metadata: Dict[str, Any], 
                             sample_data: Optional[List[Dict[str, Any]]]) -> str:
        """Detect the semantic type of a table."""
        table_lower = table_name.lower()
        
        # Check metadata for clues
        source_file = metadata.get("source_file", "").lower()
        sheet_name = metadata.get("sheet_name", "").lower()
        
        # Combine all text for pattern matching
        combined_text = f"{table_lower} {source_file} {sheet_name}"
        
        # Check against patterns
        best_match = "general"
        best_score = 0
        
        for sem_type, config in self.semantic_patterns.items():
            score = 0
            for pattern in config["patterns"]:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    score += 2
            
            # Check column names if we have sample data
            if sample_data and len(sample_data) > 0:
                columns = list(sample_data[0].keys())
                for col in columns:
                    for pattern in config["patterns"]:
                        if re.search(pattern, col.lower(), re.IGNORECASE):
                            score += 1
            
            if score > best_score:
                best_score = score
                best_match = sem_type
        
        return best_match
    
    def _extract_keywords(self, table_name: str, metadata: Dict[str, Any],
                         sample_data: Optional[List[Dict[str, Any]]]) -> Set[str]:
        """Extract semantic keywords from table information."""
        keywords = set()
        
        # Add words from table name
        words = re.findall(r'\w+', table_name.lower())
        keywords.update(words)
        
        # Add from metadata
        if "sheet_name" in metadata:
            sheet_words = re.findall(r'\w+', metadata["sheet_name"].lower())
            keywords.update(sheet_words)
        
        # Add column names
        if sample_data and len(sample_data) > 0:
            columns = list(sample_data[0].keys())
            for col in columns:
                col_words = re.findall(r'\w+', col.lower())
                keywords.update(col_words)
        
        # Remove common words
        stopwords = {"id", "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        keywords -= stopwords
        
        return keywords
    
    def _extract_data_keywords(self, sample_data: List[Dict[str, Any]]) -> Set[str]:
        """Extract keywords from actual data values."""
        keywords = set()
        
        # Sample first 10 rows
        for row in sample_data[:10]:
            for col, value in row.items():
                if value and isinstance(value, str):
                    # Extract meaningful words from values
                    value_words = re.findall(r'\b[a-zA-Z]{3,}\b', str(value).lower())
                    # Only add if it appears to be categorical (not long text)
                    if len(value_words) <= 5:
                        keywords.update(value_words)
        
        # Common AI risk terms found in data
        risk_terms = {"human", "ai", "discrimination", "privacy", "security", 
                     "misinformation", "malicious", "socioeconomic", "safety"}
        keywords &= risk_terms  # Keep only relevant terms
        
        return keywords
    
    def _analyze_data_quality(self, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data quality metrics."""
        if not sample_data:
            return {}
        
        total_rows = len(sample_data)
        columns = list(sample_data[0].keys()) if sample_data else []
        
        # Calculate completeness
        non_null_counts = {col: 0 for col in columns}
        for row in sample_data:
            for col in columns:
                if row.get(col) is not None and str(row.get(col)).strip():
                    non_null_counts[col] += 1
        
        completeness = {
            col: count / total_rows if total_rows > 0 else 0
            for col, count in non_null_counts.items()
        }
        
        # Find columns with actual data
        data_columns = [col for col, score in completeness.items() if score > 0.1]
        
        return {
            'row_count': total_rows,
            'column_count': len(columns),
            'data_columns': len(data_columns),
            'avg_completeness': sum(completeness.values()) / len(completeness) if completeness else 0,
            'has_meaningful_data': len(data_columns) > 1  # More than just ID column
        }
    
    def _generate_description(self, table_name: str, semantic_type: str,
                             metadata: Dict[str, Any], sample_data: Optional[List[Dict[str, Any]]]) -> str:
        """Generate a human-readable description of the table."""
        row_count = metadata.get("row_count", 0)
        source = metadata.get("source_file", "unknown source")
        
        descriptions = {
            "risks": f"Contains {row_count} AI risk entries with detailed information about potential hazards and threats",
            "taxonomy": f"Hierarchical classification system with {row_count} categories for organizing AI risks",
            "statistics": f"Statistical summary data with {row_count} metrics about AI risk distributions",
            "resources": f"Collection of {row_count} resources, papers, and references about AI safety",
            "changelog": f"Historical record of {row_count} changes and updates to the repository",
            "content": f"Text content and descriptions with {row_count} entries",
            "general": f"Data table with {row_count} rows from {source}"
        }
        
        return descriptions.get(semantic_type, descriptions["general"])
    
    def find_tables_for_query(self, query: str) -> List[TableSemantics]:
        """Find relevant tables based on query intent."""
        query_lower = query.lower()
        matches = []
        
        # Extract key terms from query
        query_terms = set(re.findall(r'\w+', query_lower))
        query_terms -= {"the", "a", "an", "how", "many", "what", "where", "when", "which", "show", "list", "get", "me", "all"}
        
        # Special handling for common query patterns
        is_count_query = any(term in query_lower for term in ["how many", "count", "total", "number of"])
        is_category_query = any(term in query_lower for term in ["categories", "types", "kinds", "classifications"])
        is_domain_query = any(term in query_lower for term in ["domain", "domains"])
        
        # Score each table
        for table_name, semantics in self.registry.items():
            score = 0
            
            # Check if query mentions table name directly
            if table_name.lower() in query_lower:
                score += 15
            
            # Check semantic type patterns
            sem_config = self.semantic_patterns.get(semantics.semantic_type, {})
            priority = sem_config.get("priority", 5)
            
            for pattern in sem_config.get("patterns", []):
                if re.search(pattern, query_lower, re.IGNORECASE):
                    score += 5 * (priority / 5)  # Scale by priority
            
            # Special boosts for query types
            if is_count_query and semantics.semantic_type == "risks":
                score += 10
            elif is_category_query and semantics.semantic_type == "taxonomy":
                score += 10
            elif is_domain_query and "domain" in semantics.domain_keywords:
                score += 10
            
            # Check keywords overlap
            keyword_overlap = query_terms & semantics.domain_keywords
            score += len(keyword_overlap) * 2
            
            # Check for entity mentions
            if semantics.primary_entity and semantics.primary_entity in query_lower:
                score += 3
            
            # Boost based on data quality
            if hasattr(semantics, 'data_quality'):
                quality = semantics.data_quality
                # Prefer tables with more rows
                if quality.get('row_count', 0) > 100:
                    score += 5
                elif quality.get('row_count', 0) > 1000:
                    score += 10
                
                # Prefer tables with meaningful data
                if quality.get('has_meaningful_data', False):
                    score += 8
                
                # Prefer tables with good completeness
                if quality.get('avg_completeness', 0) > 0.5:
                    score += 3
            
            # Penalize metadata/explainer tables unless specifically asked
            if semantics.semantic_type == "metadata" and "explainer" not in query_lower:
                score *= 0.3
            
            # Penalize tables with too few rows for general queries
            if hasattr(semantics, 'data_quality') and semantics.data_quality.get('row_count', 0) < 50:
                if not table_name.lower() in query_lower:  # Unless specifically mentioned
                    score *= 0.5
            
            if score > 0:
                matches.append((score, semantics))
        
        # Sort by score and return
        matches.sort(key=lambda x: x[0], reverse=True)
        
        # Log the top matches for debugging
        if matches:
            logger.info(f"Top table matches for '{query[:50]}...':")
            for score, sem in matches[:3]:
                logger.info(f"  - {sem.table_name} (type: {sem.semantic_type}, score: {score:.2f})")
        
        return [sem for _, sem in matches]
    
    def get_table_description(self, table_name: str) -> Optional[str]:
        """Get description for a specific table."""
        if table_name in self.registry:
            return self.registry[table_name].description
        return None
    
    def get_semantic_type(self, table_name: str) -> Optional[str]:
        """Get semantic type for a specific table."""
        if table_name in self.registry:
            return self.registry[table_name].semantic_type
        return None

# Singleton instance
semantic_registry = SemanticTableRegistry()