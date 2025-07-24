"""
Query processing and enhancement for domain-specific searches.
"""
from typing import List, Dict, Any, Tuple, Optional
from langchain.docstore.document import Document
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from ...config.logging import get_logger

logger = get_logger(__name__)

class QueryProcessor:
    """Handles query analysis and processing."""
    
    def __init__(self, query_monitor=None):
        self.query_monitor = query_monitor
        
        # Import domain classifier for generic domain detection
        from ...config.domains import domain_classifier
        from ...config.prompts import prompt_manager
        self.domain_classifier = domain_classifier
        self.prompt_manager = prompt_manager
        
        # Initialize session tracking for reset guard
        self.session_queries = {}  # session_id -> last_query
        self.sentence_transformer = None  # Lazy initialization
    
    def analyze_query(self, message: str, session_id: str = "default") -> Tuple[str, Optional[str]]:
        """
        Analyze query to determine type and domain with confidence weighting.
        
        Args:
            message: User query
            session_id: Session identifier for reset guard
            
        Returns:
            Tuple of (query_type, domain)
        """
        query_type = "general"
        domain = None
        
        # Session reset guard - check if query is significantly different from previous
        should_reset_session = self._should_reset_session(message, session_id)
        if should_reset_session:
            logger.info(f"Session reset triggered for session {session_id}")
        
        # Update session tracking
        self.session_queries[session_id] = message
        
        # Try advanced analysis first
        if self.query_monitor:
            try:
                if hasattr(self.query_monitor, 'analyze_query'):
                    query_analysis = self.query_monitor.analyze_query(message)
                    query_type = query_analysis.get('query_type', 'general')
                elif hasattr(self.query_monitor, 'determine_inquiry_type'):
                    inquiry_result = self.query_monitor.determine_inquiry_type(message)
                    
                    # Safe type conversion with fallbacks
                    query_type = str(inquiry_result.get('inquiry_type', 'GENERAL')).lower()
                    domain = str(inquiry_result.get('primary_domain', 'OTHER')).lower()
                    
                    # Handle confidence - could be string or numeric
                    confidence_raw = inquiry_result.get('confidence', 'MEDIUM')
                    if isinstance(confidence_raw, str):
                        confidence = confidence_raw.lower()
                    else:
                        # Convert numeric confidence to string
                        if isinstance(confidence_raw, (int, float)):
                            if confidence_raw >= 0.8:
                                confidence = 'high'
                            elif confidence_raw >= 0.5:
                                confidence = 'medium'
                            else:
                                confidence = 'low'
                        else:
                            confidence = 'medium'  # fallback
                    
                    reasoning = inquiry_result.get('reasoning', '')
                    
                    # Map inquiry types to our internal types
                    if query_type == "employment_risk":
                        query_type = "employment"
                    elif query_type == "safety_risk":
                        query_type = "safety"
                    elif query_type == "privacy_risk":
                        query_type = "privacy"
                    elif query_type == "bias_risk":
                        query_type = "bias"
                    elif query_type == "technical_risk":
                        query_type = "technical"
                    elif query_type == "governance_risk":
                        query_type = "governance"
                    elif query_type.endswith("_risk"):
                        # Default mapping for any other _risk patterns
                        query_type = query_type.replace("_risk", "")
                    
                    # Enhanced logging with confidence and reasoning
                    logger.info(f"LLM classification - Domain: {domain}, Confidence: {confidence}")
                    if reasoning:
                        logger.info(f"LLM reasoning: {reasoning}")
                    
                    # Smart fallback: if LLM confidence is LOW, only reset if domain is actually unknown
                    if confidence == 'low' and domain == 'other':
                        logger.info(f"LLM confidence is LOW and domain is unknown, attempting keyword fallback...")
                        domain = None  # This will trigger keyword classification below
                    elif confidence == 'low' and domain in ['bias', 'socioeconomic', 'safety', 'privacy', 'governance', 'technical']:
                        logger.info(f"LLM confidence is LOW but domain '{domain}' is valid, keeping classification")
                
                logger.info(f"Query type detected: {query_type}")
                if domain:
                    logger.info(f"Domain detected: {domain}")
            except Exception as e:
                logger.error(f"Error analyzing query: {str(e)}")
        
        # Enhanced domain-based detection using confidence weighting
        # Only use rule-based fallback if LLM completely failed (domain is None)
        if domain is None:
            # Get confidence-weighted domain distribution
            domain_distribution = self.domain_classifier.classify_domain_with_confidence(message)
            
            if domain_distribution and domain_distribution[0][0] != "other":
                # Use weighted combination of top domains
                primary_domain, primary_confidence = domain_distribution[0]
                
                # If we have a secondary domain with reasonable confidence, log it
                if len(domain_distribution) > 1:
                    secondary_domain, secondary_confidence = domain_distribution[1]
                    logger.info(f"Domain distribution: {primary_domain} ({primary_confidence:.2f}), {secondary_domain} ({secondary_confidence:.2f})")
                else:
                    logger.info(f"Domain detected: {primary_domain} (confidence: {primary_confidence:.2f})")
                
                domain = primary_domain
                query_type = primary_domain
                logger.info(f"Enhanced detection found {primary_domain} related query")
            else:
                # If rule-based also returns "other", keep it
                domain = "other"
                logger.info(f"Both LLM and rule-based classification returned 'other' domain")
        
        return query_type, domain
    
    def _should_reset_session(self, current_query: str, session_id: str) -> bool:
        """Determine if session should be reset based on query similarity."""
        if session_id not in self.session_queries:
            return False
        
        previous_query = self.session_queries[session_id]
        
        try:
            # Lazy initialization of sentence transformer
            if self.sentence_transformer is None:
                try:
                    self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
                except Exception as e:
                    logger.warning(f"Could not load sentence transformer: {e}")
                    return False
            
            # Calculate semantic similarity
            embeddings = self.sentence_transformer.encode([previous_query, current_query])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            
            # Check for domain change as additional reset trigger
            prev_domain = self.domain_classifier.classify_domain(previous_query)
            curr_domain = self.domain_classifier.classify_domain(current_query)
            domain_changed = prev_domain != curr_domain and prev_domain != "other" and curr_domain != "other"
            
            # Reset if similarity < 0.3 (moderately different) OR domains significantly changed
            should_reset = similarity < 0.3 or domain_changed
            
            # Enhanced logging
            logger.info(f"Session reset check - Similarity: {similarity:.3f}, "
                       f"Domain change: {prev_domain} → {curr_domain}, "
                       f"Reset: {should_reset}")
            
            return should_reset
            
        except Exception as e:
            logger.error(f"Error calculating query similarity: {e}")
            return False
    
    def enhance_query(self, message: str, query_type: str) -> str:
        """
        Enhance query with additional keywords for better retrieval.
        
        Args:
            message: Original query
            query_type: Detected query type
            
        Returns:
            Enhanced query string
        """
        enhanced_query = message
        
        # Use generic domain keywords for enhancement
        if query_type != "general":
            domain_keywords = self.domain_classifier.get_domain_keywords(query_type)
            if domain_keywords:
                enhanced_query += " " + " ".join(domain_keywords[:6])  # Limit to first 6 keywords
        
        return enhanced_query
    
    def filter_documents_by_relevance(self, docs: List[Document], query_type: str, domain: str = None) -> List[Document]:
        """
        Filter and prioritize documents based on domain (preferred) or query type.
        
        Args:
            docs: Retrieved documents
            query_type: Query type (fallback)
            domain: Domain classification (preferred for filtering)
            
        Returns:
            Filtered and prioritized documents
        """
        # Use domain for filtering if provided, otherwise fall back to query_type
        filter_key = domain if domain else query_type
        
        # Generic domain-based document filtering
        if filter_key == "general" or not self.domain_classifier.is_domain_enabled(filter_key):
            return docs
        
        domain_docs = []
        other_docs = []
        
        # Get domain keywords for matching using the filter key
        domain_keywords = self.domain_classifier.get_domain_keywords(filter_key)
        
        for doc in docs:
            doc_domain = doc.metadata.get('domain', '').lower()
            doc_subdomain = doc.metadata.get('subdomain', '').lower()
            doc_specific_domain = doc.metadata.get('specific_domain', '').lower()
            
            # Check if this document is domain-related
            is_domain_related = any(
                keyword in doc_domain + doc_subdomain + doc_specific_domain 
                for keyword in domain_keywords
            )
            
            if is_domain_related:
                domain_docs.append(doc)
            else:
                other_docs.append(doc)
        
        # Prioritize domain docs, but include some others for context
        filtered_docs = domain_docs[:6] + other_docs[:2]
        
        logger.info(f"Filtered to {len(domain_docs)} {filter_key}-specific documents and {min(2, len(other_docs))} general documents")
        
        return filtered_docs
    
    def generate_prompt(self, message: str, query_type: str, domain: str, context: str, session_id: str = "default", docs: List[Document] = None) -> str:
        """
        Generate enhanced prompt using the new prompt management system.

        Args:
            message: User query
            query_type: Detected query type
            domain: Detected domain (e.g., 'safety', 'privacy', 'bias')
            context: Retrieved context
            session_id: Session ID for intro tracking
            docs: Retrieved documents for RID extraction
            
        Returns:
            Enhanced prompt with brevity rules and domain-specific guidance
        """
        # Use the provided domain, fallback to classifier if needed
        if not domain or domain == 'other':
            # Only use classifier as fallback if no domain was provided or it's 'other'
            detected_domain = self.domain_classifier.classify_domain(message)
            if detected_domain != 'other':
                domain = detected_domain
            else:
                domain = 'general'
        
        # Ensure domain is valid for prompt templates
        if domain not in ['socioeconomic', 'safety', 'privacy', 'bias', 'governance', 'technical']:
            domain = 'general'
        
        # Extract available RIDs from documents
        available_rids = []
        if docs:
            for doc in docs:
                rid = doc.metadata.get('rid')
                if rid and rid not in available_rids:
                    available_rids.append(rid)
        
        # Debug logging for prompt generation
        logger.info(f"=== PROMPT GENERATION DEBUG ===")
        logger.info(f"Final domain passed to prompt manager: {domain}")
        logger.info(f"Final query_type: {query_type}")
        logger.info(f"Context available: {'Yes' if context else 'No'}")
        logger.info(f"=== END PROMPT GENERATION DEBUG ===")
        
        # Use the new prompt manager for advanced, context-aware prompts
        return self.prompt_manager.get_prompt(
            query=message,
            domain=domain,
            context=context,
            session_id=session_id,
            query_type=query_type,
            available_rids=available_rids
        )