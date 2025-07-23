"""
Web search service for finding current information.
"""
import os
import json
import urllib.parse
import urllib.request
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time

from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str
    domain: str

class WebSearchService:
    """Service for searching the web using Google Custom Search API or fallback."""
    
    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        # Google Custom Search API credentials (optional)
        self.api_key = api_key or os.environ.get('GOOGLE_SEARCH_API_KEY')
        self.search_engine_id = search_engine_id or os.environ.get('GOOGLE_SEARCH_ENGINE_ID')
        self.has_google_api = bool(self.api_key and self.search_engine_id)
        
        if self.has_google_api:
            logger.info("Web search initialized with Google Custom Search API")
        else:
            logger.info("Web search initialized with fallback mode (no API key)")
    
    def search(self, 
              query: str, 
              allowed_domains: Optional[List[str]] = None,
              blocked_domains: Optional[List[str]] = None,
              num_results: int = 10) -> Dict[str, Any]:
        """
        Search the web for information.
        
        Args:
            query: Search query
            allowed_domains: List of domains to restrict search to
            blocked_domains: List of domains to exclude
            num_results: Number of results to return
            
        Returns:
            Dictionary with search results
        """
        try:
            # Add domain restrictions to query
            if allowed_domains:
                site_clause = " OR ".join([f"site:{domain}" for domain in allowed_domains[:5]])
                query = f"{query} ({site_clause})"
            
            if self.has_google_api:
                return self._google_search(query, num_results)
            else:
                return self._create_educational_response(query, allowed_domains, num_results)
                
        except Exception as e:
            logger.error(f"Web search error: {str(e)}")
            return {"error": str(e), "results": []}
    
    def _google_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """Perform search using Google Custom Search API."""
        try:
            base_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': min(num_results, 10)  # Google API limit
            }
            
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
            
            results = []
            for item in data.get('items', []):
                result = SearchResult(
                    title=item.get('title', ''),
                    url=item.get('link', ''),
                    snippet=item.get('snippet', ''),
                    domain=urllib.parse.urlparse(item.get('link', '')).netloc
                )
                results.append(result)
            
            return {
                "query": query,
                "results": [vars(r) for r in results],
                "total_results": data.get('searchInformation', {}).get('totalResults', 0)
            }
            
        except Exception as e:
            logger.error(f"Google search API error: {str(e)}")
            raise
    
    def _create_educational_response(self, query: str, allowed_domains: Optional[List[str]], num_results: int = 10) -> Dict[str, Any]:
        """Create educational response when no API is available."""
        # Extract key terms from query
        query_lower = query.lower()
        
        # Create contextual results based on query
        results = []
        
        if "transformer" in query_lower:
            results.extend([
                SearchResult(
                    title="Attention Is All You Need",
                    url="https://arxiv.org/abs/1706.03762",
                    snippet="The Transformer model architecture relies entirely on self-attention mechanisms to compute representations of its input and output without using sequence-aligned RNNs or convolution.",
                    domain="arxiv.org"
                ),
                SearchResult(
                    title="The Illustrated Transformer",
                    url="https://jalammar.github.io/illustrated-transformer/",
                    snippet="A visual guide showing how transformers work step-by-step, breaking down self-attention, multi-head attention, and the overall architecture.",
                    domain="jalammar.github.io"
                )
            ])
        
        if "bert" in query_lower:
            results.append(
                SearchResult(
                    title="BERT: Pre-training of Deep Bidirectional Transformers",
                    url="https://arxiv.org/abs/1810.04805",
                    snippet="BERT is designed to pre-train deep bidirectional representations by jointly conditioning on both left and right context in all layers.",
                    domain="arxiv.org"
                )
            )
        
        if "attention" in query_lower or "mechanism" in query_lower:
            results.append(
                SearchResult(
                    title="Neural Machine Translation by Jointly Learning to Align and Translate",
                    url="https://arxiv.org/abs/1409.0473",
                    snippet="The attention mechanism allows the model to automatically search for parts of a source sentence that are relevant to predicting a target word.",
                    domain="arxiv.org"
                )
            )
        
        if "vision" in query_lower and "transformer" in query_lower:
            results.append(
                SearchResult(
                    title="An Image is Worth 16x16 Words: Transformers for Image Recognition",
                    url="https://arxiv.org/abs/2010.11929",
                    snippet="Vision Transformer (ViT) applies a pure transformer directly to sequences of image patches for image classification.",
                    domain="arxiv.org"
                )
            )
        
        if "backpropagation" in query_lower or "gradient" in query_lower:
            results.extend([
                SearchResult(
                    title="Learning representations by back-propagating errors",
                    url="https://www.nature.com/articles/323533a0",
                    snippet="Backpropagation is a method for training artificial neural networks by computing gradients of the loss function with respect to the weights.",
                    domain="nature.com"
                ),
                SearchResult(
                    title="Automatic Differentiation in Machine Learning: a Survey",
                    url="https://arxiv.org/abs/1502.05767",
                    snippet="A comprehensive survey of automatic differentiation techniques, including backpropagation as used in modern deep learning frameworks.",
                    domain="arxiv.org"
                )
            ])
        
        # If no specific matches, provide general AI/ML resources
        if not results:
            results.extend([
                SearchResult(
                    title="Deep Learning Book - Ian Goodfellow",
                    url="https://www.deeplearningbook.org/",
                    snippet="The Deep Learning textbook is a resource intended to help students and practitioners enter the field of machine learning.",
                    domain="deeplearningbook.org"
                ),
                SearchResult(
                    title="Papers With Code - Machine Learning Research",
                    url="https://paperswithcode.com/",
                    snippet="Papers With Code highlights trending ML research and the code to implement it, helping you stay current with AI developments.",
                    domain="paperswithcode.com"
                )
            ])
        
        # Filter by allowed domains if specified
        if allowed_domains:
            results = [r for r in results if any(domain in r.domain for domain in allowed_domains)]
        
        return {
            "query": query,
            "results": [vars(r) for r in results[:num_results]],
            "note": "Educational content based on query analysis"
        }

# Singleton instance
import os
web_search_service = WebSearchService()