"""
Multi-strategy retrieval system that uses multiple methods to find documents.
Handles specific fact retrieval, numbers, names, and semantic concepts.
"""

import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from langchain.docstore.document import Document
from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
import numpy as np

from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)


@dataclass
class RetrievalStrategy:
    """Represents a retrieval strategy and its results."""
    name: str
    confidence: float
    documents: List[Document]
    
    
class MultiStrategyRetriever:
    """
    Retrieves documents using multiple strategies and merges results.
    Handles edge cases like numbers with punctuation, exact names, etc.
    """
    
    def __init__(self, vector_store: Chroma, all_documents: List[Document]):
        """
        Initialize multi-strategy retriever.
        
        Args:
            vector_store: ChromaDB vector store
            all_documents: All documents for BM25 and regex search
        """
        self.vector_store = vector_store
        self.all_documents = all_documents
        
        # Create clean versions of documents for better BM25
        self._create_clean_documents()
        
        # Initialize BM25 with clean text
        self._init_bm25()
        
    def _create_clean_documents(self):
        """Create clean versions of documents for keyword matching."""
        self.clean_documents = []
        self.doc_to_clean_map = {}
        
        for doc in self.all_documents:
            # Clean text: remove punctuation around numbers, normalize spaces
            clean_text = doc.page_content
            
            # Fix numbers with punctuation (e.g., "(total: 777)" -> "total 777")
            clean_text = re.sub(r'[^\w\s]', ' ', clean_text)
            
            # Normalize whitespace
            clean_text = ' '.join(clean_text.split())
            
            # Create clean document
            clean_doc = Document(
                page_content=clean_text,
                metadata=doc.metadata
            )
            
            self.clean_documents.append(clean_doc)
            self.doc_to_clean_map[id(clean_doc)] = doc  # Map clean to original
            
    def _init_bm25(self):
        """Initialize BM25 retriever with clean documents."""
        try:
            self.bm25_retriever = BM25Retriever.from_documents(self.clean_documents)
            self.bm25_retriever.k = 10  # Get more results for re-ranking
            logger.info(f"BM25 initialized with {len(self.clean_documents)} clean documents")
        except Exception as e:
            logger.error(f"Failed to initialize BM25: {str(e)}")
            self.bm25_retriever = None
            
    def retrieve(self, query: str, k: int = 5) -> List[Document]:
        """
        Retrieve documents using multiple strategies.
        
        Args:
            query: The search query
            k: Number of documents to return
            
        Returns:
            List of relevant documents
        """
        strategies = []
        
        # Analyze query type
        query_analysis = self._analyze_query(query)
        
        # Strategy 1: If query has numbers, use regex search
        if query_analysis['has_numbers']:
            regex_results = self._regex_number_search(query, query_analysis['numbers'])
            if regex_results:
                strategies.append(RetrievalStrategy(
                    name="regex_number",
                    confidence=0.95,  # High confidence for exact matches
                    documents=regex_results
                ))
        
        # Strategy 2: BM25 keyword search on clean text
        if self.bm25_retriever:
            clean_query = re.sub(r'[^\w\s]', ' ', query)
            bm25_results = self._bm25_search(clean_query)
            if bm25_results:
                strategies.append(RetrievalStrategy(
                    name="bm25_clean",
                    confidence=0.85,
                    documents=bm25_results
                ))
        
        # Strategy 3: Vector similarity search
        vector_results = self._vector_search(query)
        if vector_results:
            strategies.append(RetrievalStrategy(
                name="vector",
                confidence=0.75,
                documents=vector_results
            ))
        
        # Strategy 4: Metadata filtering for specific query types
        if query_analysis['is_methodology']:
            # Search for documents with methodology in extracted facts
            metadata_results = self._extracted_fact_search('methodologies')
            if metadata_results:
                strategies.append(RetrievalStrategy(
                    name="extracted_methodology",
                    confidence=0.85,
                    documents=metadata_results
                ))
        
        if query_analysis['is_author']:
            # Search for documents with authors in extracted facts
            metadata_results = self._extracted_fact_search('authors')
            if metadata_results:
                strategies.append(RetrievalStrategy(
                    name="extracted_author",
                    confidence=0.90,
                    documents=metadata_results
                ))
        
        if query_analysis['needs_document_count']:
            # Search for documents with document counts in extracted facts
            metadata_results = self._extracted_fact_search('document_count')
            if metadata_results:
                strategies.append(RetrievalStrategy(
                    name="extracted_document_count",
                    confidence=0.95,  # Very high confidence for extracted facts
                    documents=metadata_results
                ))
        
        # Merge and re-rank results
        merged_docs = self._merge_strategies(strategies, k)
        
        # Log retrieval stats
        logger.info(f"Query: '{query}' - Used {len(strategies)} strategies, returned {len(merged_docs)} docs")
        
        return merged_docs
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query to determine retrieval strategies."""
        query_lower = query.lower()
        
        # Extract explicit numbers from the query itself
        numbers = re.findall(r'\b\d+\b', query)
        
        # Identify query types
        is_statistics = any(term in query_lower for term in 
                          ['how many', 'number of', 'total', 'count', 'percentage'])
        
        # NO HARDCODING - just analyze what the query is asking for
        return {
            'has_numbers': bool(numbers),  # Only if numbers are IN the query
            'numbers': numbers,  # Only numbers from the query itself
            'is_methodology': any(term in query_lower for term in 
                                ['methodology', 'method', 'systematic', 'prisma', 'approach']),
            'is_author': any(term in query_lower for term in 
                           ['author', 'who wrote', 'who created', 'by whom']),
            'is_statistics': is_statistics,  # Query is asking for statistics
            'needs_document_count': is_statistics and 'document' in query_lower,
        }
    
    def _regex_number_search(self, query: str, numbers: List[str]) -> List[Document]:
        """Search for exact numbers using regex."""
        results = []
        seen_docs = set()  # Track documents we've already added
        
        for number in numbers:
            # Create regex patterns that handle various formats
            patterns = [
                re.compile(rf'\b{number}\b', re.IGNORECASE),  # Word boundary
                re.compile(rf'{number}(?=\D|$)', re.IGNORECASE),  # Number followed by non-digit or end
                re.compile(rf'(?<!\d){number}', re.IGNORECASE),  # Number not preceded by digit
            ]
            
            for doc in self.all_documents:
                doc_id = id(doc)
                if doc_id in seen_docs:
                    continue
                    
                # Try all patterns
                for pattern in patterns:
                    if pattern.search(doc.page_content):
                        results.append(doc)
                        seen_docs.add(doc_id)
                        logger.debug(f"Regex found '{number}' in document")
                        break
                
                # Only get first few matches
                if len(results) >= 5:
                    break
                    
            if len(results) >= 5:
                break
        
        return results
    
    def _bm25_search(self, query: str) -> List[Document]:
        """BM25 keyword search on clean text."""
        try:
            # Get clean documents from BM25
            clean_results = self.bm25_retriever.invoke(query)
            
            # Map back to original documents
            original_results = []
            for clean_doc in clean_results:
                # Find original document
                original = self.doc_to_clean_map.get(id(clean_doc))
                if original:
                    original_results.append(original)
                else:
                    # Fallback: find by content similarity
                    for orig_doc in self.all_documents:
                        if orig_doc.metadata == clean_doc.metadata:
                            original_results.append(orig_doc)
                            break
            
            return original_results
            
        except Exception as e:
            logger.error(f"BM25 search failed: {str(e)}")
            return []
    
    def _vector_search(self, query: str) -> List[Document]:
        """Vector similarity search."""
        try:
            results = self.vector_store.similarity_search(query, k=10)
            return results
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return []
    
    def _metadata_search(self, search_type: str, filters: Dict) -> List[Document]:
        """Search based on metadata filters."""
        results = []
        
        for doc in self.all_documents:
            metadata = doc.metadata
            
            # Check if document matches filters
            match = True
            for key, value in filters.items():
                if value == '*':  # Wildcard - just check if key exists
                    if key not in metadata or not metadata[key]:
                        match = False
                        break
                else:
                    if metadata.get(key) != value:
                        match = False
                        break
            
            if match:
                results.append(doc)
                
                # Limit results
                if len(results) >= 10:
                    break
        
        return results
    
    def _extracted_fact_search(self, fact_type: str) -> List[Document]:
        """Search documents based on extracted facts in metadata."""
        results = []
        seen_docs = set()
        
        for doc in self.all_documents:
            doc_id = id(doc)
            if doc_id in seen_docs:
                continue
                
            metadata = doc.metadata
            
            # Check for extracted facts (now flat fields)
            if fact_type == 'document_count':
                # Look for document count or total count in metadata
                if metadata.get('document_count') or metadata.get('total_count'):
                    results.append(doc)
                    seen_docs.add(doc_id)
                    
            elif fact_type == 'authors':
                # Look for extracted authors (now a comma-separated string)
                if metadata.get('extracted_authors'):
                    results.append(doc)
                    seen_docs.add(doc_id)
                    
            elif fact_type == 'methodologies':
                # Look for extracted methodologies (now a comma-separated string)
                if metadata.get('extracted_methods'):
                    results.append(doc)
                    seen_docs.add(doc_id)
            
            # Limit results
            if len(results) >= 10:
                break
        
        return results
    
    def _merge_strategies(self, strategies: List[RetrievalStrategy], k: int) -> List[Document]:
        """Merge results from multiple strategies with re-ranking."""
        # Score each document based on strategies that found it
        doc_scores = {}
        doc_objects = {}
        doc_strategies = {}  # Track which strategies found each doc
        
        for strategy in strategies:
            for i, doc in enumerate(strategy.documents):
                # Create document key based on content hash
                doc_key = hash(doc.page_content[:200])
                
                if doc_key not in doc_scores:
                    doc_scores[doc_key] = 0
                    doc_objects[doc_key] = doc
                    doc_strategies[doc_key] = []
                
                # Score based on strategy confidence and position
                position_penalty = 1.0 - (i / max(1, len(strategy.documents)))
                score = strategy.confidence * position_penalty
                
                # Boost score if from high-confidence strategy (regex)
                if strategy.name == "regex_number":
                    score *= 2.0  # Double score for exact number matches
                
                doc_scores[doc_key] += score
                doc_strategies[doc_key].append(strategy.name)
        
        # Sort by total score
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top k documents
        result_docs = []
        for doc_key, score in sorted_docs[:k]:
            doc = doc_objects[doc_key]
            # Add retrieval score and strategies to metadata for debugging
            doc.metadata['retrieval_score'] = score
            doc.metadata['retrieval_strategies'] = doc_strategies[doc_key]
            result_docs.append(doc)
        
        return result_docs