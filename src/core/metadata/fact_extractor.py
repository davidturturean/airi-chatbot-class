"""
Fact extraction from documents for structured metadata.
Extracts key facts like numbers, authors, methodologies during ingestion.
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from langchain.docstore.document import Document

from ...config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedFacts:
    """Container for facts extracted from a document."""
    numbers: Dict[str, List[str]]  # number -> contexts where it appears
    authors: List[str]
    methodologies: List[str]
    dates: List[str]
    organizations: List[str]
    key_terms: List[str]
    statistics: Dict[str, Any]  # stat type -> value
    

class FactExtractor:
    """
    Extracts structured facts from documents for metadata enrichment.
    No hardcoding - all extraction is pattern-based and contextual.
    """
    
    def __init__(self):
        """Initialize fact extractor with patterns."""
        self._init_patterns()
        
    def _init_patterns(self):
        """Initialize extraction patterns."""
        # Number patterns with context
        self.number_patterns = [
            # "X documents" pattern
            (r'(\d+)\s+(?:documents?|papers?|studies|articles?)', 'document_count'),
            # "total: X" pattern
            (r'total[:\s]+(\d+)', 'total_count'),
            # "N = X" pattern (common in research)
            (r'[Nn]\s*=\s*(\d+)', 'sample_size'),
            # Percentage patterns
            (r'(\d+(?:\.\d+)?)\s*%', 'percentage'),
            # Year patterns
            (r'\b(19\d{2}|20\d{2})\b', 'year'),
        ]
        
        # Author name patterns (research paper style)
        self.author_patterns = [
            # "LastName et al" pattern
            r'([A-Z][a-z]+)\s+et\s+al\.?',
            # "FirstName LastName" at document start (common for author lists)
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+)',
            # Citation style "LastName (Year)"
            r'([A-Z][a-z]+)\s*\(\d{4}\)',
        ]
        
        # Methodology patterns
        self.methodology_patterns = [
            # Systematic review methodologies
            r'(PRISMA|Cochrane|systematic\s+review|meta-analysis)',
            # Statistical methods
            r'(regression|ANOVA|t-test|chi-square|correlation)',
            # ML methods
            r'(machine\s+learning|deep\s+learning|neural\s+network|classification|clustering)',
            # Research methods
            r'(qualitative|quantitative|mixed\s+methods|case\s+study|survey)',
        ]
        
    def extract_facts(self, document: Document) -> Dict[str, Any]:
        """
        Extract facts from a document and return structured metadata.
        
        Args:
            document: Document to extract facts from
            
        Returns:
            Dictionary of extracted facts for metadata
        """
        content = document.page_content
        existing_metadata = document.metadata or {}
        
        facts = ExtractedFacts(
            numbers={},
            authors=[],
            methodologies=[],
            dates=[],
            organizations=[],
            key_terms=[],
            statistics={}
        )
        
        # Extract numbers with context
        facts.numbers = self._extract_numbers_with_context(content)
        
        # Extract authors
        facts.authors = self._extract_authors(content)
        
        # Extract methodologies
        facts.methodologies = self._extract_methodologies(content)
        
        # Build FLAT metadata dictionary (ChromaDB doesn't support nested dicts)
        metadata = {}
        
        # Add specific high-value extractions as flat fields
        if facts.numbers.get('document_count'):
            metadata['document_count'] = facts.numbers['document_count'][0]
            
        if facts.numbers.get('sample_size'):
            metadata['sample_size'] = facts.numbers['sample_size'][0]
            
        if facts.numbers.get('total_count'):
            metadata['total_count'] = facts.numbers['total_count'][0]
            
        if facts.authors:
            # Store as comma-separated string for ChromaDB compatibility
            metadata['extracted_authors'] = ', '.join(facts.authors[:5])  # Top 5 authors
            
        if facts.methodologies:
            # Store as comma-separated string for ChromaDB compatibility
            metadata['extracted_methods'] = ', '.join(facts.methodologies[:3])  # Top 3 methods
        
        # Store a flag to indicate this document has extracted facts
        if facts.authors or facts.methodologies or facts.numbers:
            metadata['has_extracted_facts'] = True
        
        # Merge with existing metadata
        return {**existing_metadata, **metadata}
    
    def _extract_numbers_with_context(self, text: str) -> Dict[str, List[str]]:
        """Extract numbers with their surrounding context."""
        numbers = {}
        
        for pattern, category in self.number_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                number = match.group(1)
                
                # Get context around the number (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                if category not in numbers:
                    numbers[category] = []
                    
                numbers[category].append(number)
                
                # Log significant numbers for debugging
                if category == 'document_count' and int(number) > 100:
                    logger.debug(f"Found significant document count: {number} in context: {context}")
        
        return numbers
    
    def _extract_authors(self, text: str) -> List[str]:
        """Extract author names from text."""
        authors = set()
        
        for pattern in self.author_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                author = match.group(1)
                # Filter out common false positives
                if len(author) > 2 and author not in ['The', 'This', 'These', 'That']:
                    authors.add(author)
        
        return list(authors)
    
    def _extract_methodologies(self, text: str) -> List[str]:
        """Extract methodology mentions from text."""
        methodologies = set()
        
        for pattern in self.methodology_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                methodology = match.group(1)
                methodologies.add(methodology.lower())
        
        return list(methodologies)
    
    def enrich_document(self, document: Document) -> Document:
        """
        Enrich a document with extracted facts in its metadata.
        
        Args:
            document: Document to enrich
            
        Returns:
            Document with enriched metadata
        """
        # Extract facts
        enriched_metadata = self.extract_facts(document)
        
        # Update document metadata
        document.metadata = enriched_metadata
        
        return document