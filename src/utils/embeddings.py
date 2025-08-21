"""
Google Embeddings Service for replacing SentenceTransformers.
Provides the same interface but uses Google's API instead of local models.
"""
from typing import List, Union
import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

from ..config.settings import settings
from ..config.logging import get_logger

logger = get_logger(__name__)

class GoogleEmbeddingService:
    """
    Singleton service for Google embeddings with caching.
    Mimics SentenceTransformer's interface for drop-in replacement.
    """
    _instance = None
    _embeddings = None
    _cache = {}
    _max_cache_size = 1000
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Google embeddings API client."""
        try:
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.EMBEDDING_MODEL_NAME,
                google_api_key=settings.GEMINI_API_KEY,
                task_type="retrieval_query"
            )
            logger.info("Google Embedding Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Embedding Service: {e}")
            self._embeddings = None
    
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Encode texts to embeddings, mimicking SentenceTransformer's encode() interface.
        
        Args:
            texts: Single string or list of strings to encode
            
        Returns:
            numpy array of embeddings
        """
        if self._embeddings is None:
            logger.error("Google embeddings not initialized")
            return np.array([])
        
        # Convert single string to list for uniform processing
        if isinstance(texts, str):
            texts = [texts]
            single_text = True
        else:
            single_text = False
        
        embeddings = []
        
        try:
            for text in texts:
                # Check cache first
                cache_key = hash(text) % (10 ** 8)  # Simple hash for cache key
                
                if cache_key in self._cache:
                    embeddings.append(self._cache[cache_key])
                else:
                    # Get embedding from Google API
                    embedding = self._embeddings.embed_query(text)
                    embedding_array = np.array(embedding)
                    
                    # Cache the result (with size limit)
                    if len(self._cache) < self._max_cache_size:
                        self._cache[cache_key] = embedding_array
                    elif len(self._cache) >= self._max_cache_size:
                        # Clear oldest entries (simple FIFO)
                        self._cache.pop(next(iter(self._cache)))
                        self._cache[cache_key] = embedding_array
                    
                    embeddings.append(embedding_array)
            
            # Convert to numpy array
            result = np.array(embeddings)
            
            # If single text was provided, return 1D array for compatibility
            if single_text and result.shape[0] == 1:
                return result
            
            return result
            
        except Exception as e:
            logger.error(f"Error encoding texts with Google embeddings: {e}")
            # Return empty array with proper shape on error
            return np.array([[]] * len(texts))
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self._cache.clear()
        logger.info("Embedding cache cleared")

# Create singleton instance
google_embedding_service = GoogleEmbeddingService()