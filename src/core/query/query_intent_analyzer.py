"""
Semantic query intent analyzer for understanding user request completeness and structure.
Analyzes queries to determine how detailed and complete responses should be.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
from ...config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class QueryIntent:
    """Represents the analyzed intent of a query."""
    completeness_level: float  # 0.0 (summary) to 1.0 (exhaustive)
    comparison_mode: bool      # Is this comparing concepts?
    enumeration_mode: bool     # Is this listing items?
    specificity_markers: List[str]  # Numbers, "all", "every", etc.
    query_type: str  # 'overview', 'specific', 'comparison', 'enumeration'
    concepts_mentioned: List[str]  # Taxonomy concepts found in query


class QueryIntentAnalyzer:
    """Analyzes query intent to determine response completeness requirements."""
    
    def __init__(self):
        """Initialize the query intent analyzer."""
        self._init_semantic_patterns()
        self._init_taxonomy_vocabulary()
    
    def _init_semantic_patterns(self):
        """Initialize semantic pattern indicators."""
        # Completeness indicators (not hardcoded patterns, but semantic signals)
        self.completeness_signals = {
            'exhaustive': ['all', 'every', 'complete', 'full', 'entire', 'comprehensive', 'each'],
            'enumeration': ['list', 'enumerate', 'show', 'provide', 'display', 'what are'],
            'specific': ['specific', 'particular', 'exact', 'precisely'],
            'comparison': ['difference', 'compare', 'versus', 'vs', 'between', 'distinguish'],
            'explanation': ['explain', 'describe', 'what is', 'tell me about', 'how']
        }
        
        # Verb analysis for understanding action intent
        self.action_verbs = {
            'enumerate': ['list', 'enumerate', 'itemize', 'catalog', 'index'],
            'compare': ['compare', 'contrast', 'differentiate', 'distinguish'],
            'explain': ['explain', 'describe', 'elaborate', 'clarify'],
            'summarize': ['summarize', 'overview', 'brief', 'outline']
        }
    
    def _init_taxonomy_vocabulary(self):
        """Initialize taxonomy-specific vocabulary for concept detection."""
        self.taxonomy_concepts = {
            'causal': ['entity', 'intentionality', 'timing', 'causal', 
                      'human', 'ai', 'intentional', 'unintentional',
                      'pre-deployment', 'post-deployment'],
            'domain': ['domain', 'subdomain', 'discrimination', 'toxicity',
                      'privacy', 'security', 'misinformation', 'malicious',
                      'human-computer', 'interaction', 'socioeconomic',
                      'environmental', 'safety', 'failures', 'limitations'],
            'statistical': ['percentage', 'proportion', 'statistics', 'count',
                           'number', 'how many', 'distribution'],
            'structural': ['taxonomy', 'structure', 'framework', 'organization',
                          'categorization', 'classification']
        }
    
    def analyze_query(self, query: str) -> QueryIntent:
        """
        Analyze a query to understand its intent and completeness requirements.
        
        Args:
            query: The user's query string
            
        Returns:
            QueryIntent object with analysis results
        """
        query_lower = query.lower()
        
        # Detect comparison mode
        comparison_mode = self._detect_comparison_mode(query_lower)
        
        # Detect enumeration mode
        enumeration_mode = self._detect_enumeration_mode(query_lower)
        
        # Extract specificity markers
        specificity_markers = self._extract_specificity_markers(query_lower)
        
        # Calculate completeness level
        completeness_level = self._calculate_completeness_level(
            query_lower, specificity_markers, comparison_mode, enumeration_mode
        )
        
        # Determine query type
        query_type = self._determine_query_type(
            comparison_mode, enumeration_mode, completeness_level
        )
        
        # Extract mentioned concepts
        concepts_mentioned = self._extract_concepts(query_lower)
        
        return QueryIntent(
            completeness_level=completeness_level,
            comparison_mode=comparison_mode,
            enumeration_mode=enumeration_mode,
            specificity_markers=specificity_markers,
            query_type=query_type,
            concepts_mentioned=concepts_mentioned
        )
    
    def _detect_comparison_mode(self, query: str) -> bool:
        """Detect if query is asking for comparison between concepts."""
        comparison_patterns = [
            r'difference between',
            r'compare\s+\w+\s+(and|with|to)',
            r'\w+\s+vs\.?\s+\w+',
            r'versus',
            r'distinguish between',
            r'what\'s the difference'
        ]
        
        for pattern in comparison_patterns:
            if re.search(pattern, query):
                return True
        
        # Check for semantic comparison signals
        comparison_count = sum(1 for signal in self.completeness_signals['comparison'] 
                              if signal in query)
        return comparison_count >= 1
    
    def _detect_enumeration_mode(self, query: str) -> bool:
        """Detect if query is asking for a list or enumeration."""
        # Check for enumeration verbs
        for verb in self.action_verbs['enumerate']:
            if verb in query:
                return True
        
        # Check for enumeration signals
        enumeration_count = sum(1 for signal in self.completeness_signals['enumeration']
                               if signal in query)
        
        # Check for number + plural noun pattern (e.g., "7 domains", "24 subdomains")
        number_pattern = r'\b\d+\s+\w+s\b'
        if re.search(number_pattern, query):
            return True
        
        return enumeration_count >= 1
    
    def _extract_specificity_markers(self, query: str) -> List[str]:
        """Extract markers indicating specific completeness requirements."""
        markers = []
        
        # Extract numbers
        numbers = re.findall(r'\b\d+\b', query)
        markers.extend(numbers)
        
        # Extract exhaustive signals
        for signal in self.completeness_signals['exhaustive']:
            if signal in query:
                markers.append(signal)
        
        # Extract specific signals
        for signal in self.completeness_signals['specific']:
            if signal in query:
                markers.append(signal)
        
        return markers
    
    def _calculate_completeness_level(self, query: str, markers: List[str],
                                     comparison: bool, enumeration: bool) -> float:
        """
        Calculate how complete/exhaustive the response should be.
        
        Returns:
            float between 0.0 (summary) and 1.0 (exhaustive)
        """
        score = 0.3  # Base score
        
        # Boost for exhaustive signals
        exhaustive_count = sum(1 for signal in self.completeness_signals['exhaustive']
                              if signal in query)
        score += exhaustive_count * 0.2
        
        # Boost for specific numbers mentioned
        if any(char.isdigit() for char in query):
            score += 0.2
        
        # Boost for enumeration mode
        if enumeration:
            score += 0.2
        
        # Boost for comparison mode (needs complete info for both sides)
        if comparison:
            score += 0.15
        
        # Boost for words like "all", "every", "complete"
        if any(word in markers for word in ['all', 'every', 'complete', 'full']):
            score += 0.3
        
        # Check for explicit completeness requests
        if 'all' in query and any(num in query for num in ['24', '7', 'seven']):
            score = max(score, 0.9)  # Strong signal for complete enumeration
        
        # Cap at 1.0
        return min(1.0, score)
    
    def _determine_query_type(self, comparison: bool, enumeration: bool,
                             completeness: float) -> str:
        """Determine the primary type of query."""
        if comparison:
            return 'comparison'
        elif enumeration:
            return 'enumeration'
        elif completeness >= 0.7:
            return 'specific'
        else:
            return 'overview'
    
    def _extract_concepts(self, query: str) -> List[str]:
        """Extract taxonomy concepts mentioned in the query."""
        concepts = []
        
        for category, terms in self.taxonomy_concepts.items():
            for term in terms:
                if term in query:
                    concepts.append(term)
        
        return list(set(concepts))  # Remove duplicates
    
    def requires_complete_response(self, intent: QueryIntent) -> bool:
        """
        Determine if the query requires a complete/exhaustive response.
        
        Args:
            intent: The analyzed query intent
            
        Returns:
            True if complete response needed, False for summary
        """
        return (
            intent.completeness_level >= 0.7 or
            intent.enumeration_mode and intent.completeness_level >= 0.5 or
            any(marker in ['all', 'every', 'complete'] for marker in intent.specificity_markers)
        )
    
    def get_response_detail_level(self, intent: QueryIntent) -> str:
        """
        Get recommended detail level for response.
        
        Returns:
            'summary', 'moderate', or 'exhaustive'
        """
        if intent.completeness_level >= 0.7:
            return 'exhaustive'
        elif intent.completeness_level >= 0.4:
            return 'moderate'
        else:
            return 'summary'