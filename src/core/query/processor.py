"""
Query processing and enhancement for domain-specific searches.
"""
from typing import List, Dict, Any, Tuple, Optional
from langchain.docstore.document import Document
import numpy as np
import time
from collections import OrderedDict
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from ...config.logging import get_logger
from ...config.settings import settings

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
        
        # Initialize session tracking for reset guard with TTL and size limits
        self.session_queries = OrderedDict()  # session_id -> (query, timestamp)
        self.session_ttl = getattr(settings, 'SESSION_TTL', 3600)  # 1 hour TTL for sessions
        self.max_sessions = getattr(settings, 'MAX_SESSIONS', 1000)  # Maximum number of sessions to keep
        self.last_cleanup_time = time.time()  # Track last cleanup to avoid excessive cleanup calls
        self.cleanup_interval = 300  # Cleanup every 5 minutes
        self.sentence_transformer = None  # Lazy initialization
        
        logger.info(f"QueryProcessor initialized with session_ttl={self.session_ttl}s, max_sessions={self.max_sessions}")
    
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
        original_domain = None  # Store original LLM classification for fallback
        
        # Session reset guard - check if query is significantly different from previous
        should_reset_session = self._should_reset_session(message, session_id)
        if should_reset_session:
            logger.info(f"Session reset triggered for session {session_id}")
        
        # Update session tracking with periodic cleanup
        try:
            self._periodic_session_cleanup()
            self._update_session(session_id, message)
        except Exception as e:
            logger.error(f"Session management error: {e}")
            # Continue processing even if session management fails
        
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
                    
                    # Progressive fallback strategy based on confidence level
                    domain, original_domain = self._handle_confidence_based_fallback(
                        confidence, domain, message, original_domain
                    )
                
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
                # If rule-based also returns "other", check if we had an original domain from LLM
                if original_domain:
                    domain = original_domain
                    logger.info(f"Both LLM and rule-based classification returned 'other' domain, but query has AI risk terms - defaulting to synthesis mode with 'other' domain")
                else:
                    domain = "other"
                    logger.info(f"Both LLM and rule-based classification returned 'other' domain")
        
        # Final validation and cleanup
        query_type, domain = self._validate_and_cleanup_classification(query_type, domain, message)
        
        return query_type, domain
    
    def _validate_and_cleanup_classification(self, query_type: str, domain: str, message: str) -> tuple:
        """
        Validate and cleanup classification results to ensure consistency.
        
        Args:
            query_type: The classified query type
            domain: The classified domain
            message: The original user message
            
        Returns:
            Tuple of (cleaned_query_type, cleaned_domain)
        """
        # Valid domains from configuration
        valid_domains = ['bias', 'socioeconomic', 'safety', 'privacy', 'governance', 'technical', 'other']
        
        # Valid query types
        valid_query_types = ['general', 'specific_risk', 'employment', 'recommendation', 'out_of_scope']
        
        # Validate and clean domain
        if domain not in valid_domains:
            logger.warning(f"Invalid domain '{domain}' detected, defaulting to 'other'")
            domain = 'other'
        
        # Validate and clean query type
        if query_type not in valid_query_types:
            logger.warning(f"Invalid query_type '{query_type}' detected, defaulting to 'general'")
            query_type = 'general'
        
        # Enhanced 'other' domain handling for multi-domain queries
        if domain == 'other' and query_type != 'out_of_scope':
            enhanced_domain = self._enhance_other_domain_classification(message)
            if enhanced_domain and enhanced_domain != 'other':
                logger.info(f"Enhanced classification: changed 'other' domain to '{enhanced_domain}' for multi-domain query")
                domain = enhanced_domain
            else:
                # Check if this might be a misclassified AI risk query
                ai_risk_terms = ['ai', 'artificial intelligence', 'machine learning', 'algorithm', 'bias', 'safety', 'risk', 'mitigation']
                message_lower = message.lower()
                
                if any(term in message_lower for term in ai_risk_terms):
                    logger.info(f"Query classified as 'other' domain but contains AI risk terms - flagged for synthesis")
                    # Keep domain as 'other' but mark for enhanced synthesis
        
        # Consistency checks
        if query_type == 'employment' and domain != 'socioeconomic':
            logger.warning(f"Employment query type with domain '{domain}' - expected 'socioeconomic'")
            domain = 'socioeconomic'
        
        # Log final classification
        logger.info(f"Final classification: query_type='{query_type}', domain='{domain}'")
        
        return query_type, domain
    
    def _enhance_other_domain_classification(self, message: str) -> str:
        """
        Enhanced classification for queries initially classified as 'other' domain.
        Attempts to identify the most relevant domain for multi-domain queries.
        """
        message_lower = message.lower()
        
        # Multi-domain query patterns - look for combinations that suggest primary domain
        domain_indicators = {
            'safety': [
                'safety', 'security', 'harm', 'danger', 'threat', 'hazard', 'risk', 'attack',
                'vulnerability', 'malicious', 'weaponization', 'accident', 'injury'
            ],
            'governance': [
                'regulation', 'policy', 'governance', 'oversight', 'legal', 'law', 
                'compliance', 'ethics', 'accountability', 'standards', 'framework'
            ],
            'bias': [
                'bias', 'discrimination', 'unfair', 'prejudice', 'fairness', 'equity',
                'representation', 'stereotyping', 'demographic', 'minorities'
            ],
            'privacy': [
                'privacy', 'surveillance', 'monitoring', 'personal information', 'data protection',
                'confidential', 'tracking', 'personal data'
            ],
            'socioeconomic': [
                'employment', 'job', 'work', 'economic', 'inequality', 'automation',
                'labor', 'unemployment', 'displacement', 'workforce'
            ],
            'technical': [
                'algorithm', 'model', 'performance', 'accuracy', 'robustness', 
                'reliability', 'technical', 'system failure', 'training'
            ]
        }
        
        # Count indicators for each domain
        domain_scores = {}
        for domain_name, indicators in domain_indicators.items():
            score = sum(1 for indicator in indicators if indicator in message_lower)
            if score > 0:
                domain_scores[domain_name] = score
        
        # If no clear indicators, check for broader multi-domain patterns
        if not domain_scores:
            # Broad queries that span multiple domains
            broad_patterns = {
                'safety': ['implications', 'consequences', 'effects', 'impact'],
                'governance': ['societal', 'society', 'social', 'long-term']
            }
            
            for domain_name, patterns in broad_patterns.items():
                if any(pattern in message_lower for pattern in patterns):
                    domain_scores[domain_name] = 1
        
        # Return the domain with highest score, if any
        if domain_scores:
            best_domain = max(domain_scores.items(), key=lambda x: x[1])
            logger.info(f"Enhanced classification scores: {domain_scores}, selected: {best_domain[0]}")
            return best_domain[0]
        
        return 'other'
    
    def _handle_confidence_based_fallback(self, confidence: str, domain: str, message: str, original_domain: str) -> tuple:
        """
        Handle confidence-based fallback strategy for query classification.
        
        Returns:
            Tuple of (updated_domain, original_domain)
        """
        ai_risk_indicators = [
            'risk', 'threat', 'bias', 'safety', 'privacy', 'governance', 'technical', 
            'mitigation', 'mitigations', 'control', 'controls', 'safeguard', 'safeguards',
            'protection', 'protections', 'countermeasure', 'countermeasures', 'prevent',
            'solution', 'solutions', 'recommendation', 'recommendations', 'implications',
            'consequences', 'effects', 'impact', 'societal', 'society', 'social'
        ]
        
        query_lower = message.lower()
        has_ai_risk_terms = any(term in query_lower for term in ai_risk_indicators)
        
        if confidence == 'high':
            # High confidence - trust the classification
            logger.info(f"HIGH confidence classification: domain='{domain}' - accepting")
            return domain, original_domain
            
        elif confidence == 'medium':
            if domain == 'other':
                # MEDIUM confidence with 'other' domain - investigate further
                logger.info(f"MEDIUM confidence with 'other' domain - investigating further")
                
                if has_ai_risk_terms:
                    # Try enhanced classification for multi-domain queries
                    enhanced_domain = self._enhance_other_domain_classification(message)
                    if enhanced_domain != 'other':
                        logger.info(f"MEDIUM confidence enhancement: 'other' → '{enhanced_domain}'")
                        return enhanced_domain, domain  # Store original as fallback
                    else:
                        # Use keyword fallback as last resort
                        logger.info(f"MEDIUM confidence with AI risk terms - trying keyword fallback")
                        original_domain = domain
                        return None, original_domain  # Trigger keyword classification
                else:
                    logger.info(f"MEDIUM confidence 'other' domain with no AI risk indicators - keeping as 'other'")
                    return domain, original_domain
            else:
                # MEDIUM confidence with specific domain - verify with keywords
                domain_keywords = self._get_domain_keywords(domain)
                keyword_match = any(keyword in query_lower for keyword in domain_keywords)
                
                if keyword_match:
                    logger.info(f"MEDIUM confidence domain '{domain}' confirmed by keyword match")
                    return domain, original_domain
                else:
                    logger.info(f"MEDIUM confidence domain '{domain}' not confirmed by keywords - trying fallback")
                    original_domain = domain
                    return None, original_domain  # Trigger keyword classification
                    
        elif confidence == 'low':
            if domain == 'other':
                if has_ai_risk_terms:
                    logger.info(f"LOW confidence 'other' domain with AI risk terms - trying keyword fallback")
                    original_domain = domain
                    return None, original_domain  # Trigger keyword classification
                else:
                    logger.info(f"LOW confidence 'other' domain with no AI risk indicators - keeping as 'other'")
                    return domain, original_domain
            else:
                # LOW confidence with specific domain - always try keyword fallback
                logger.info(f"LOW confidence domain '{domain}' - trying keyword fallback for verification")
                original_domain = domain
                return None, original_domain  # Trigger keyword classification
        
        # Default fallback
        logger.warning(f"Unhandled confidence case: {confidence}, domain: {domain}")
        return domain, original_domain
    
    def _get_domain_keywords(self, domain: str) -> List[str]:
        """Get keywords for a specific domain to verify classification."""
        domain_keywords = {
            'safety': ['safety', 'security', 'harm', 'danger', 'threat', 'hazard', 'risk', 'attack'],
            'governance': ['regulation', 'policy', 'governance', 'oversight', 'legal', 'law', 'compliance'],
            'bias': ['bias', 'discrimination', 'unfair', 'prejudice', 'fairness', 'equity'],
            'privacy': ['privacy', 'surveillance', 'monitoring', 'confidential', 'tracking'],
            'socioeconomic': ['employment', 'job', 'work', 'economic', 'inequality', 'automation'],
            'technical': ['algorithm', 'model', 'performance', 'accuracy', 'robustness', 'reliability']
        }
        return domain_keywords.get(domain, [])
    
    def _periodic_session_cleanup(self):
        """Perform periodic cleanup of expired sessions to avoid excessive cleanup calls."""
        current_time = time.time()
        
        # Only cleanup if enough time has passed since last cleanup
        if current_time - self.last_cleanup_time < self.cleanup_interval:
            return
            
        try:
            initial_count = len(self.session_queries)
            
            # Remove expired sessions
            expired_sessions = [
                session_id for session_id, (query, timestamp) in self.session_queries.items()
                if current_time - timestamp > self.session_ttl
            ]
            
            for session_id in expired_sessions:
                del self.session_queries[session_id]
            
            # Enforce maximum session limit (LRU eviction)
            evicted_count = 0
            while len(self.session_queries) > self.max_sessions:
                oldest_session = next(iter(self.session_queries))
                del self.session_queries[oldest_session]
                evicted_count += 1
            
            final_count = len(self.session_queries)
            expired_count = len(expired_sessions)
            
            if expired_count > 0 or evicted_count > 0:
                logger.info(f"Session cleanup: {initial_count} → {final_count} sessions "
                          f"(expired: {expired_count}, evicted: {evicted_count})")
            
            self.last_cleanup_time = current_time
            
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
            # Reset cleanup time to avoid immediate retry
            self.last_cleanup_time = current_time
    
    def _update_session(self, session_id: str, message: str):
        """Update session with new query and current timestamp."""
        try:
            current_time = time.time()
            
            # Validate inputs
            if not isinstance(session_id, str) or not session_id.strip():
                logger.warning("Invalid session_id provided, using default")
                session_id = "default"
                
            if not isinstance(message, str):
                logger.warning("Invalid message type provided")
                message = str(message)
            
            # Remove and re-add to maintain LRU order in OrderedDict
            if session_id in self.session_queries:
                del self.session_queries[session_id]
            
            self.session_queries[session_id] = (message, current_time)
            logger.debug(f"Updated session {session_id} with query: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"Session update failed for {session_id}: {e}")
            # Don't raise exception to avoid breaking query processing
    
    def _should_reset_session(self, current_query: str, session_id: str) -> bool:
        """Determine if session should be reset based on query similarity."""
        if session_id not in self.session_queries:
            return False
        
        previous_query, _ = self.session_queries[session_id]  # Extract query from (query, timestamp) tuple
        
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