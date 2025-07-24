"""
Smart web search service with strict criteria to avoid becoming a generic search bot.
Only searches when repository synthesis is inadequate and specific conditions are met.
"""
from typing import List, Tuple, Optional, Dict, Any
import re
from datetime import datetime

from .web_search import WebSearchService, SearchResult
from ...config.logging import get_logger

logger = get_logger(__name__)

class SmartWebSearchService:
    """Web search with strict criteria to maintain focus on AI Risk Repository."""
    
    def __init__(self, web_search_service: Optional[WebSearchService] = None):
        self.web_search = web_search_service or WebSearchService()
        
        # Patterns that indicate current/recent information needs
        self.temporal_patterns = [
            r'\b(latest|recent|current|today|now|2024|2025)\b',
            r'\b(state of the art|cutting edge|emerging|new)\b',
            r'\b(trend|development|update|progress)\b'
        ]
        
        # Patterns that indicate external context needs
        self.external_patterns = [
            r'\b(industry standard|best practice|benchmark)\b',
            r'\b(compared to|versus|vs\.?|against)\b',
            r'\b(other companies|competitors|market)\b',
            r'\b(regulation|law|policy|compliance)\s+\b(in|for|of)\s+\w+'
        ]
        
        # Topics well-covered by repository (no search needed)
        self.repository_topics = [
            'bias', 'discrimination', 'fairness', 'privacy', 'surveillance',
            'safety', 'security', 'employment', 'job displacement', 'governance',
            'regulation', 'ethics', 'transparency', 'accountability', 'risk'
        ]
    
    def should_search(self, 
                     query: str, 
                     repository_content_length: int,
                     documents_found: int) -> Tuple[bool, str]:
        """
        Determine if web search should be performed based on strict criteria.
        
        Returns:
            Tuple of (should_search, reason)
        """
        query_lower = query.lower()
        
        # Check 1: Never search for general AI risk concepts
        for topic in self.repository_topics:
            if topic in query_lower and not any(re.search(p, query_lower) for p in self.temporal_patterns):
                return False, f"Repository covers {topic} extensively"
        
        # Check 2: Requires current/recent information
        needs_current = any(re.search(p, query_lower) for p in self.temporal_patterns)
        
        # Check 3: Requires external context
        needs_external = any(re.search(p, query_lower) for p in self.external_patterns)
        
        # Check 4: Repository has inadequate content
        inadequate_content = repository_content_length < 100 or documents_found == 0
        
        # Check 5: Specific domain + current info (e.g., "latest healthcare AI regulations")
        specific_current = needs_current and re.search(r'\b(healthcare|finance|legal|military)\b', query_lower)
        
        # Decision logic
        if specific_current:
            return True, "Query needs current domain-specific information"
        
        if needs_current and inadequate_content:
            return True, "Query needs current information not in repository"
        
        if needs_external and inadequate_content:
            return True, "Query needs external context not in repository"
        
        # Default: Don't search
        return False, "Repository content is sufficient"
    
    def search_if_needed(self,
                        query: str,
                        repository_content: str,
                        documents_found: int) -> Optional[List[SearchResult]]:
        """
        Perform web search only if strict criteria are met.
        
        Args:
            query: User query
            repository_content: Content found in repository
            documents_found: Number of documents retrieved
            
        Returns:
            Search results if criteria met, None otherwise
        """
        should_search, reason = self.should_search(
            query, 
            len(repository_content),
            documents_found
        )
        
        if not should_search:
            logger.info(f"Web search skipped: {reason}")
            return None
        
        logger.info(f"Web search triggered: {reason}")
        
        # Perform search with AI-focused domains
        allowed_domains = [
            'mit.edu', 'arxiv.org', 'nature.com', 'science.org',
            'ieee.org', 'acm.org', 'nist.gov', 'europa.eu',
            'brookings.edu', 'rand.org', 'cnas.org'
        ]
        
        # Add query refinement for AI focus
        refined_query = f"AI artificial intelligence {query}"
        
        try:
            results = self.web_search.search(
                refined_query,
                allowed_domains=allowed_domains,
                num_results=5  # Limited results
            )
            
            # Check for results (no 'success' key in response)
            if results and 'results' in results and results['results']:
                return [
                    SearchResult(
                        title=r['title'],
                        url=r['url'],
                        snippet=r['snippet'],
                        domain=r['domain']
                    ) for r in results['results']
                ]
        except Exception as e:
            logger.error(f"Web search failed: {e}")
        
        return None
    
    def format_search_results(self, results: List[SearchResult]) -> str:
        """Format search results for inclusion in response."""
        if not results:
            return ""
        
        formatted = "\n\n**Additional Context from Web Search:**\n"
        for i, result in enumerate(results[:3], 1):  # Max 3 results
            formatted += f"\n{i}. {result.title}\n"
            formatted += f"   Source: {result.domain}\n"
            formatted += f"   {result.snippet}\n"
        
        formatted += "\n*Note: Web search used to supplement repository information with current data.*"
        return formatted

# Global instance
smart_web_search = SmartWebSearchService()