"""
Handler for technical AI/ML queries using web search.
"""
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import re

from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

@dataclass
class TechnicalSource:
    """Represents a source for technical information."""
    title: str
    url: str
    snippet: str
    relevance_score: float

class TechnicalAIHandler:
    """Handles technical AI/ML queries by searching authoritative sources."""
    
    def __init__(self, web_search_tool=None, gemini_model=None):
        self.web_search = web_search_tool
        self.gemini_model = gemini_model
        
        # Authoritative domains for AI/ML content
        self.trusted_domains = [
            "arxiv.org",
            "paperswithcode.com",
            "huggingface.co",
            "github.com",
            "openai.com",
            "anthropic.com",
            "deepmind.com",
            "ai.googleblog.com",
            "distill.pub",
            "pytorch.org",
            "tensorflow.org"
        ]
        
        # Academic and research domains
        self.academic_domains = [
            "arxiv.org",
            "paperswithcode.com",
            "proceedings.neurips.cc",
            "proceedings.mlr.press",
            "aclanthology.org"
        ]
    
    def handle_technical_query(self, query: str) -> Tuple[str, List[TechnicalSource]]:
        """
        Handle a technical AI/ML query by searching and synthesizing information.
        
        Returns:
            Tuple of (formatted_response, sources)
        """
        try:
            # 1. Search for technical information
            search_results = self._search_technical_info(query)
            
            if not search_results:
                return self._create_no_results_response(query)
            
            # 2. Extract and rank sources
            sources = self._extract_sources(search_results)
            
            # 3. Synthesize response using Gemini
            response = self._synthesize_response(query, sources)
            
            # 4. Format with proper citations
            formatted_response = self._format_with_citations(response, sources)
            
            return (formatted_response, sources)
            
        except Exception as e:
            logger.error(f"Error handling technical query: {str(e)}")
            return self._create_error_response(query, str(e))
    
    def _search_technical_info(self, query: str) -> Dict[str, Any]:
        """Search for technical information using web search."""
        # Enhance query with technical context
        enhanced_query = f"{query} technical explanation implementation"
        
        try:
            if self.web_search:
                # Use the actual WebSearch service
                results = self.web_search.search(
                    query=enhanced_query,
                    allowed_domains=self.trusted_domains,
                    num_results=10
                )
                return results
            else:
                # Use the web search service singleton
                from ...core.services.web_search import web_search_service
                results = web_search_service.search(
                    query=enhanced_query,
                    allowed_domains=self.trusted_domains,
                    num_results=10
                )
                return results
                
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return {}
    
    def _extract_sources(self, search_results: Dict[str, Any]) -> List[TechnicalSource]:
        """Extract and rank sources from search results."""
        sources = []
        
        # Handle different possible result formats
        if isinstance(search_results, dict):
            if 'results' in search_results:
                results_list = search_results['results']
            elif 'items' in search_results:
                results_list = search_results['items']
            else:
                results_list = []
        else:
            results_list = search_results if isinstance(search_results, list) else []
        
        for result in results_list:
            try:
                # Extract fields with various possible keys
                title = result.get('title', result.get('name', 'Untitled'))
                url = result.get('url', result.get('link', ''))
                snippet = result.get('snippet', result.get('description', ''))
                
                # Calculate relevance score based on domain
                domain = self._extract_domain(url)
                relevance = self._calculate_relevance(domain, title, snippet)
                
                source = TechnicalSource(
                    title=title,
                    url=url,
                    snippet=snippet,
                    relevance_score=relevance
                )
                sources.append(source)
                
            except Exception as e:
                logger.warning(f"Error processing search result: {str(e)}")
                continue
        
        # Sort by relevance
        sources.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Return top sources
        return sources[:5]
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        import re
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else ''
    
    def _calculate_relevance(self, domain: str, title: str, snippet: str) -> float:
        """Calculate relevance score for a source."""
        score = 0.5  # Base score
        
        # Domain scoring
        if domain in self.academic_domains:
            score += 0.3
        elif domain in self.trusted_domains:
            score += 0.2
        
        # Title relevance
        ai_keywords = ['neural', 'transformer', 'attention', 'deep learning', 'machine learning']
        title_lower = title.lower()
        keyword_matches = sum(1 for kw in ai_keywords if kw in title_lower)
        score += min(0.2, keyword_matches * 0.05)
        
        return min(1.0, score)
    
    def _synthesize_response(self, query: str, sources: List[TechnicalSource]) -> str:
        """Synthesize a comprehensive response using Gemini."""
        # Build context from sources
        source_context = self._build_source_context(sources)
        
        prompt = f"""Based on the following authoritative sources, provide a comprehensive technical explanation for this question:

Question: {query}

Sources:
{source_context}

Instructions:
1. Provide a clear, technical explanation
2. Include key concepts and terminology
3. Mention recent developments if relevant
4. Structure the response with clear sections
5. Be accurate and cite specific details from sources
6. If the sources don't fully answer the question, acknowledge what's missing

Response:"""
        
        try:
            if self.gemini_model:
                response = self.gemini_model.generate(prompt)
                return response
            else:
                # Fallback response
                return self._create_fallback_response(query, sources)
                
        except Exception as e:
            logger.error(f"Error synthesizing response: {str(e)}")
            return self._create_fallback_response(query, sources)
    
    def _build_source_context(self, sources: List[TechnicalSource]) -> str:
        """Build context string from sources."""
        context_parts = []
        
        for i, source in enumerate(sources, 1):
            context = f"[{i}] {source.title}\n"
            context += f"URL: {source.url}\n"
            context += f"Content: {source.snippet}\n"
            context_parts.append(context)
        
        return "\n".join(context_parts)
    
    def _format_with_citations(self, response: str, sources: List[TechnicalSource]) -> str:
        """Format response with proper source citations."""
        # Add source citations at the end
        formatted = response + "\n\n**Sources:**\n"
        
        for i, source in enumerate(sources, 1):
            formatted += f"[{i}] [{source.title}]({source.url})\n"
        
        # Add note about currency
        formatted += "\n*Note: This information is based on current web sources. "
        formatted += "AI/ML is a rapidly evolving field, so details may change.*"
        
        return formatted
    
    def _create_no_results_response(self, query: str) -> Tuple[str, List[TechnicalSource]]:
        """Create response when no results found."""
        response = f"I couldn't find specific technical information about '{query}'. "
        response += "This might be because:\n\n"
        response += "1. The topic is very new or specialized\n"
        response += "2. The search terms need refinement\n"
        response += "3. The information is in non-indexed sources\n\n"
        response += "Try rephrasing your question or asking about related concepts."
        
        return (response, [])
    
    def _create_error_response(self, query: str, error: str) -> Tuple[str, List[TechnicalSource]]:
        """Create error response."""
        response = f"I encountered an error while searching for technical information.\n\n"
        response += f"Query: {query}\n"
        response += f"Error: {error}\n\n"
        response += "Please try again or rephrase your question."
        
        return (response, [])
    
    def _create_fallback_response(self, query: str, sources: List[TechnicalSource]) -> str:
        """Create fallback response when synthesis fails."""
        response = f"Here's what I found about '{query}':\n\n"
        
        for i, source in enumerate(sources, 1):
            response += f"**{i}. {source.title}**\n"
            response += f"{source.snippet}\n"
            response += f"Read more: {source.url}\n\n"
        
        return response
    

# Global technical handler instance (initialized when needed)
technical_ai_handler = None

def get_technical_handler():
    """Get or create the technical handler instance."""
    global technical_ai_handler
    if technical_ai_handler is None:
        technical_ai_handler = TechnicalAIHandler()
    return technical_ai_handler