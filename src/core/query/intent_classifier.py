"""
Lightweight intent classification pipeline for pre-retrieval filtering.
Classifies queries into categories to optimize processing and prevent waste.
"""
import time
from typing import Dict, Tuple, Optional, List
from enum import Enum
from dataclasses import dataclass

from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

class IntentCategory(Enum):
    """Categories for query intent classification."""
    REPOSITORY_RELATED = "repository_related"
    TAXONOMY_QUERY = "taxonomy_query"  # New category for taxonomy-specific queries
    METADATA_QUERY = "metadata_query"
    TECHNICAL_AI_QUERY = "technical_ai"
    CROSS_DB_QUERY = "cross_database"
    CHIT_CHAT = "chit_chat"
    GENERAL_KNOWLEDGE = "general_knowledge"
    JUNK = "junk"
    PROFANITY = "profanity"
    OVERRIDE_ATTEMPT = "override_attempt"

@dataclass
class IntentResult:
    """Result of intent classification."""
    category: IntentCategory
    confidence: float
    reasoning: str
    should_process: bool
    suggested_response: Optional[str] = None

class IntentClassifier:
    """Lightweight intent classifier using pattern matching and heuristics."""
    
    def __init__(self, use_gemini: bool = True):
        self.use_gemini = use_gemini
        self.gemini_model = None
        self._init_patterns()
        
        # Performance tracking
        self.classification_times = []
        self.classification_count = 0
        
        # Cache for recent classifications
        self._cache = {}
        self._cache_max_size = 1000
        
        # Defer embedding initialization - will happen on first use
        self._embeddings_initialized = False
    
    def _init_patterns(self):
        """Initialize semantic intent classification with reference embeddings."""
        
        # Category reference texts for semantic similarity
        self.category_references = {
            IntentCategory.REPOSITORY_RELATED: [
                "AI risks and safety concerns in artificial intelligence systems",
                "Machine learning bias, fairness, and discrimination issues", 
                "Employment impacts and job displacement from automation",
                "Privacy violations and security risks in AI systems",
                "AI governance, regulation, and policy frameworks",
                "Autonomous systems ethics and safety protocols",
                # Add research methodology and academic queries
                "PRISMA methodology systematic review process",
                "Research limitations and future work directions",
                "Comparative analysis with other frameworks",
                "Screening criteria and document selection",
                "Methodology for systematic literature review",
                "How this research was conducted",
                "Comparison with Weidinger Gabriel Yampolskiy frameworks",
                "Study limitations and scope boundaries",  
                "Corporate AI deployment assessments and audits",
                "Government studies on AI impacts and risks",
                "Cross-domain analysis of AI risks",
                "Comparing risks between different sectors",
                "Privacy risks in healthcare and finance",
                "How can I mitigate bias in AI systems?",
                "What are best practices for preventing AI risks?",
                "How to address privacy concerns in healthcare AI?",
                "Strategies for reducing employment displacement from AI"
            ],
            IntentCategory.TAXONOMY_QUERY: [
                # Direct taxonomy questions
                "What is the causal taxonomy?",
                "Describe the domain taxonomy",
                "What are the 7 domains?",
                "List the 24 subdomains",
                "What are the main risk categories in the AI Risk Database v3?",
                "Explain the entity intentionality timing structure",
                "Show the taxonomy structure",
                "What domains are in the repository?",
                
                # Natural variations
                "How does the repository organize AI risks?",
                "What's the structure of the AI risk categories?",
                "Explain how risks are classified in the repository",
                "Tell me about the risk classification system",
                "How are AI risks categorized?",
                "What types of AI risks are documented?",
                
                # Timing-related queries
                "Find AI risk papers related to pre-deployment timing",
                "What risks occur before AI is deployed?",
                "Tell me about post-deployment risks",
                "When do AI risks typically occur?",
                "Explain the timing of AI risks",
                "What happens before deployment vs after?",
                
                # Domain-specific queries
                "Tell me about privacy and security risks",
                "Explain the discrimination and toxicity domain",
                "What is domain 3 about?",
                "Describe the misinformation category",
                "Tell me about human-computer interaction risks",
                "What are socioeconomic AI risks?",
                
                # Statistical/percentage queries
                "What percentage of risks are caused by humans?",
                "How many risks are intentional vs unintentional?",
                "What proportion of risks occur post-deployment?",
                "Statistics about AI risk categories",
                "How many risks are in each domain?",
                
                # Causal factor queries
                "What's the difference between intentional and unintentional risks?",
                "Who or what causes AI risks?",
                "Explain human vs AI caused risks",
                "What does entity mean in the taxonomy?",
                "How does intentionality affect risk classification?",
                
                # Structural/framework queries
                "Describe the framework for categorizing AI risks",
                "What's the overall structure of the risk repository?",
                "How is the AI risk database organized?",
                "Explain the two-taxonomy system",
                "What are the main classification systems used?"
            ],
            IntentCategory.METADATA_QUERY: [
                "How many risks are in the database?",
                "How many papers are included?",
                "What is the earliest publication year?",
                "Who maintains this repository?",
                "Database statistics and counts",
                "Repository structure and organization"
            ],
            IntentCategory.TECHNICAL_AI_QUERY: [
                "How do transformer models work?",
                "Explain neural network architecture",
                "What is backpropagation in deep learning?",
                "How does attention mechanism work?",
                "Technical details of machine learning algorithms",
                "AI model implementation and training",
                "Computer vision techniques and methods",
                "Natural language processing algorithms"
            ],
            IntentCategory.CROSS_DB_QUERY: [
                "Show risks with their specific mitigation IDs",
                "List all risk IDs in domain 7 with their categories", 
                "Which experts work on bias issues with their paper IDs?",
                "Show risk database entries with related document excerpts",
                "Find all governance entries cross-referenced with policy documents",
                "Display risk metadata alongside relevant research papers",
                "Cross-reference structured data with document content",
                "Show database records with supporting document evidence"
            ],
            IntentCategory.CHIT_CHAT: [
                "Hello, how are you today?",
                "Good morning, nice to meet you",
                "Thanks, goodbye, have a great day",
                "Casual greetings and pleasantries"
            ],
            IntentCategory.GENERAL_KNOWLEDGE: [
                "Weather forecasts and climate information",
                "Cooking recipes and food preparation",
                "Movies, music, and entertainment topics",
                "Sports scores and athletic competitions",
                "Historical events and geography facts",
                "Health, medicine, and fitness advice"
            ]
        }
        
        # Keep minimal hardcoded patterns for obvious spam/junk - only unambiguous gibberish
        self.junk_patterns = [
            'lorem ipsum', 'qwerty', 'asdf', 'gibberish'
        ]
        
        # Security patterns (keep hardcoded for safety)
        self.override_patterns = [
            'ignore previous', 'forget instructions', 'system prompt',
            'you are now', 'pretend to be', 'roleplay', 'act as',
            'override', 'bypass', 'jailbreak', 'developer mode'
        ]
        
        # Taxonomy query patterns for quick detection
        self.taxonomy_patterns = [
            'causal taxonomy', 'domain taxonomy', '7 domains', '24 subdomains',
            'risk categories', 'ai risk database v3', 'taxonomy structure',
            'entity intentionality timing', 'pre-deployment post-deployment',
            'discrimination toxicity privacy security misinformation',
            'human-computer interaction socioeconomic environmental',
            # Add more specific patterns for failing queries
            'subdomains under', 'all the subdomains', 'privacy & security',
            'discrimination & toxicity', 'ai system safety',
            'complete structure', 'risk categorization',
            'percentage of risks', 'each causal category',
            'malicious actors', 'human-computer'
        ]
        
        # Metadata query patterns for quick detection - only specific terms
        self.metadata_patterns = [
            'how many', 'count', 'total number', 'statistics',
            'list all', 'show all', 'repository',
            'database', 'who maintains'
        ]
        
        # Technical AI patterns - only specific technical terms
        self.technical_patterns = [
            'transformer', 'neural network', 'deep learning',
            'attention', 'backpropagation', 'architecture',
            'algorithm', 'model', 'training'
        ]
        
        # Initialize embeddings lazily
        self._category_embeddings = None
        self._embedding_model = None
    
    def classify_intent(self, query: str) -> IntentResult:
        """Classify the intent of a user query."""
        start_time = time.time()
        
        try:
            # 1. Quick security/junk check first (hardcoded for safety)
            security_result = self._check_security_patterns(query)
            if security_result:
                self._log_performance(time.time() - start_time, "security")
                return security_result
            
            # 2. Check for taxonomy patterns first (high priority)
            taxonomy_result = self._check_taxonomy_patterns(query)
            if taxonomy_result:
                self._log_performance(time.time() - start_time, "taxonomy")
                return taxonomy_result
            
            # 3. Semantic similarity classification
            semantic_result = self._classify_by_semantics(query)
            
            # If semantic classification is confident, return it
            if semantic_result.confidence >= 0.7:
                self._log_performance(time.time() - start_time, "semantic")
                return semantic_result
            
            # 3. For ambiguous cases, use Gemini if available
            if self.use_gemini and self._should_use_gemini(query):
                gemini_result = self._classify_with_gemini(query)
                if gemini_result:
                    self._log_performance(time.time() - start_time, "gemini")
                    return gemini_result
            
            # 4. Fallback to semantic result
            self._log_performance(time.time() - start_time, "semantic_fallback")
            return semantic_result
            
        except Exception as e:
            logger.error(f"Error in intent classification: {str(e)}")
            # Safe fallback
            return IntentResult(
                category=IntentCategory.REPOSITORY_RELATED,
                confidence=0.3,
                reasoning="Error in classification - defaulting to repository",
                should_process=True
            )
    
    def _check_taxonomy_patterns(self, query: str) -> Optional[IntentResult]:
        """Check for taxonomy-specific patterns and semantic relevance."""
        query_lower = query.lower().strip()
        
        # Check for strong taxonomy indicators
        for pattern in self.taxonomy_patterns:
            if pattern in query_lower:
                return IntentResult(
                    category=IntentCategory.TAXONOMY_QUERY,
                    confidence=0.95,
                    reasoning=f"Taxonomy pattern detected: {pattern}",
                    should_process=True
                )
        
        # Check for domain/category questions
        if any(phrase in query_lower for phrase in ['main risk categories', 'risk categories', 'main categories']):
            if 'ai risk' in query_lower or 'database' in query_lower or 'repository' in query_lower:
                return IntentResult(
                    category=IntentCategory.TAXONOMY_QUERY,
                    confidence=0.9,
                    reasoning="Query about risk categories/taxonomy",
                    should_process=True
                )
        
        # Special check for subdomain queries
        if 'subdomain' in query_lower and any(domain in query_lower for domain in 
            ['privacy', 'security', 'discrimination', 'toxicity', 'misinformation', 
             'malicious', 'human-computer', 'socioeconomic', 'environmental', 'ai system']):
            return IntentResult(
                category=IntentCategory.TAXONOMY_QUERY,
                confidence=0.95,
                reasoning="Query about specific domain subdomains",
                should_process=True
            )
        
        # Check for structure/categorization queries
        if ('structure' in query_lower or 'categorization' in query_lower) and \
           ('ai risk' in query_lower or 'risk' in query_lower):
            return IntentResult(
                category=IntentCategory.TAXONOMY_QUERY,
                confidence=0.9,
                reasoning="Query about AI risk structure/categorization",
                should_process=True
            )
        
        # Check for percentage/statistics about causal categories
        if 'percentage' in query_lower and ('causal' in query_lower or 
            any(term in query_lower for term in ['entity', 'intentionality', 'timing', 
                                                   'human', 'ai caused', 'pre-deployment', 'post-deployment'])):
            return IntentResult(
                category=IntentCategory.TAXONOMY_QUERY,
                confidence=0.9,
                reasoning="Query about causal taxonomy statistics",
                should_process=True
            )
        
        return None
    
    def check_taxonomy_relevance(self, query: str) -> float:
        """Calculate taxonomy relevance score for a query using semantic similarity."""
        try:
            # Initialize embeddings on first use if needed
            if not self._embeddings_initialized:
                self._ensure_embeddings_initialized()
            
            # Check if embeddings are available
            if self._embedding_model is None or not self._category_embeddings:
                # Use keyword-based relevance as primary fallback
                return self._keyword_taxonomy_relevance(query)
            
            # Get query embedding
            query_embedding = self._embedding_model.encode([query.lower()])
            
            # Calculate similarity to taxonomy reference examples
            if IntentCategory.TAXONOMY_QUERY in self._category_embeddings:
                taxonomy_embeddings = self._category_embeddings[IntentCategory.TAXONOMY_QUERY]
                similarities = self._cosine_similarity(query_embedding, taxonomy_embeddings)
                
                # Check if similarities were calculated successfully
                if similarities is not None and similarities.size > 0:
                    # Get max similarity score
                    max_similarity = float(max(similarities[0]))
                    
                    # Boost score if query contains specific taxonomy concepts
                    concept_boost = self._get_taxonomy_concept_boost(query.lower())
                    
                    # Combine semantic similarity with concept detection
                    final_score = min(1.0, max_similarity + concept_boost)
                    
                    return final_score
            
            # Fallback to keyword-based relevance
            return self._keyword_taxonomy_relevance(query)
        except Exception as e:
            logger.debug(f"Error in taxonomy relevance check (using fallback): {e}")
            # Fallback to keyword-based relevance
            return self._keyword_taxonomy_relevance(query)
    
    def _keyword_taxonomy_relevance(self, query: str) -> float:
        """Fallback keyword-based taxonomy relevance scoring."""
        query_lower = query.lower()
        score = 0.0
        
        # High-value taxonomy keywords
        high_value = ['taxonomy', 'causal', 'domain', 'categories', 'classification', 
                     'pre-deployment', 'post-deployment', 'entity', 'intentionality']
        
        # Medium-value keywords
        medium_value = ['timing', 'risks', 'organize', 'structure', 'framework',
                       'discrimination', 'privacy', 'security', 'misinformation']
        
        for keyword in high_value:
            if keyword in query_lower:
                score += 0.3
        
        for keyword in medium_value:
            if keyword in query_lower:
                score += 0.15
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_taxonomy_concept_boost(self, query: str) -> float:
        """Calculate boost score based on presence of taxonomy concepts."""
        boost = 0.0
        
        # Strong taxonomy indicators
        strong_concepts = [
            'intentional', 'unintentional', 'entity', 'timing',
            'pre-deployment', 'post-deployment', 'causal taxonomy',
            'domain taxonomy', '7 domains', '24 subdomains'
        ]
        
        # Check for strong concept pairs (e.g., "intentional vs unintentional")
        if 'intentional' in query and 'unintentional' in query:
            boost += 0.3
        elif any(concept in query for concept in strong_concepts):
            boost += 0.2
        
        # Check for comparison patterns with taxonomy terms
        if ('difference' in query or 'compare' in query or 'vs' in query):
            if any(term in query for term in ['intentional', 'entity', 'timing', 'domain']):
                boost += 0.2
        
        return boost
    
    def contains_taxonomy_concepts(self, query: str) -> bool:
        """Check if query contains taxonomy-related concepts."""
        query_lower = query.lower()
        
        # Taxonomy concept keywords 
        taxonomy_concepts = [
            'domain', 'category', 'taxonomy', 'classification', 'organize',
            'pre-deployment', 'post-deployment', 'timing', 'entity',
            'intentional', 'unintentional', 'human', 'ai caused',
            'discrimination', 'privacy', 'security', 'misinformation',
            'malicious', 'socioeconomic', 'environmental', 'safety',
            'percentage', 'statistics', 'how many risks', 'proportion'
        ]
        
        # Check for any concept presence
        for concept in taxonomy_concepts:
            if concept in query_lower:
                return True
        
        # Only check semantic similarity if embeddings are available
        # Avoid calling check_taxonomy_relevance to prevent potential recursion
        if self._embedding_model is not None and self._category_embeddings:
            try:
                relevance_score = self._keyword_taxonomy_relevance(query)
                return relevance_score > 0.3  # Lower threshold for concept detection
            except:
                pass
        
        return False
    
    def _check_security_patterns(self, query: str) -> Optional[IntentResult]:
        """Quick security and junk pattern check."""
        query_lower = query.lower().strip()
        
        # Basic structural junk detection
        if len(query_lower) < 2:
            return IntentResult(
                category=IntentCategory.JUNK,
                confidence=0.9,
                reasoning="Query too short",
                should_process=False,
                suggested_response="Please provide a more specific question about AI risks."
            )
        
        # All caps gibberish (but allow legitimate all-caps acronyms)
        if query.isupper() and len(query) > 10 and not any(word.lower() in ['ai', 'ml', 'api', 'gpu', 'cpu'] for word in query.split()):
            return IntentResult(
                category=IntentCategory.JUNK,
                confidence=0.85,
                reasoning="All caps gibberish detected",
                should_process=False,
                suggested_response="Please provide a more specific question about AI risks."
            )
        
        # Excessive repetition (same word/char repeated many times)
        words = query_lower.split()
        if len(words) > 1:
            # Check for repeated words
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            max_repetition = max(word_counts.values()) if word_counts else 0
            if max_repetition >= 4:  # Same word 4+ times
                return IntentResult(
                    category=IntentCategory.JUNK,
                    confidence=0.9,
                    reasoning="Excessive word repetition detected",
                    should_process=False,
                    suggested_response="Please provide a more specific question about AI risks."
                )
        
        # Only punctuation or single characters
        if len(query.strip()) > 0 and all(not c.isalnum() for c in query.strip()):
            return IntentResult(
                category=IntentCategory.JUNK,
                confidence=0.95,
                reasoning="Only punctuation detected",
                should_process=False,
                suggested_response="Please provide a more specific question about AI risks."
            )
        
        # Check for override attempts (security)
        if any(pattern in query_lower for pattern in self.override_patterns):
            return IntentResult(
                category=IntentCategory.OVERRIDE_ATTEMPT,
                confidence=0.95,
                reasoning="Detected override attempt",
                should_process=False,
                suggested_response="I can only help with questions about AI risks from the MIT AI Risk Repository."
            )
        
        # Check for obvious junk/test queries
        junk_matches = sum(1 for pattern in self.junk_patterns if pattern in query_lower)
        if junk_matches > 0 or query_lower in ['hello world']:
            return IntentResult(
                category=IntentCategory.JUNK,
                confidence=min(1.0, 0.8 + (junk_matches * 0.1)),
                reasoning=f"Matches {junk_matches} junk patterns",
                should_process=False,
                suggested_response="Try asking about AI employment impacts, safety risks, privacy concerns, or bias issues."
            )
        
        # Quick check for metadata queries - require more patterns to reduce false positives
        metadata_matches = sum(1 for pattern in self.metadata_patterns if pattern in query_lower)
        if metadata_matches >= 3:  # Need at least 3 patterns for quick match
            return IntentResult(
                category=IntentCategory.METADATA_QUERY,
                confidence=min(0.9, 0.7 + (metadata_matches * 0.1)),
                reasoning=f"Matches {metadata_matches} metadata patterns",
                should_process=True
            )
        
        # Quick check for technical queries - require more patterns to reduce false positives
        technical_matches = sum(1 for pattern in self.technical_patterns if pattern in query_lower)
        if technical_matches >= 3 and any(ai_term in query_lower for ai_term in ['ai', 'ml', 'neural', 'model']):
            return IntentResult(
                category=IntentCategory.TECHNICAL_AI_QUERY,
                confidence=min(0.9, 0.7 + (technical_matches * 0.1)),
                reasoning=f"Matches {technical_matches} technical patterns",
                should_process=True
            )
        
        return None  # No security issues detected
    
    def _classify_by_semantics(self, query: str) -> IntentResult:
        """Classify intent using semantic similarity to reference texts."""
        try:
            # Initialize embeddings on first use if needed
            if not self._embeddings_initialized:
                self._ensure_embeddings_initialized()
            
            # Check if embeddings are available
            if not self._category_embeddings or self._embedding_model is None:
                return self._fallback_classification(query)
            
            # Get query embedding
            query_embedding = self._get_embedding(query)
            if query_embedding is None:
                return self._fallback_classification(query)
            
            # Calculate similarities to each category
            similarities = {}
            for category, category_embedding in self._category_embeddings.items():
                similarity = self._cosine_similarity(query_embedding, category_embedding)
                similarities[category] = similarity
            
            # Find best match
            best_category = max(similarities, key=similarities.get)
            best_score = similarities[best_category]
            
            # Map to intent result
            return self._similarity_to_intent_result(query, best_category, best_score, similarities)
            
        except Exception as e:
            logger.warning(f"Semantic classification failed: {e}")
            return self._fallback_classification(query)
    
    def _ensure_embeddings_initialized(self):
        """Ensure embeddings are initialized, but only once."""
        if not self._embeddings_initialized:
            logger.info("Initializing intent classifier embeddings on first use...")
            self._initialize_embeddings_with_timeout()
            self._embeddings_initialized = True
    
    def _initialize_embeddings_with_timeout(self, timeout: float = 10.0):
        """Initialize embeddings with timeout protection."""
        import concurrent.futures
        import signal
        
        # Initialize to None first
        self._embedding_model = None
        self._category_embeddings = {}
        
        def init_embeddings():
            """Inner function to initialize embeddings."""
            try:
                # Try to use sentence-transformers for embeddings
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("SentenceTransformer model loaded successfully")
                
                category_embeddings = {}
                for category, reference_texts in self.category_references.items():
                    if reference_texts:
                        # Get embeddings for all reference texts at once
                        embeddings = model.encode(reference_texts)
                        category_embeddings[category] = embeddings
                
                return model, category_embeddings
            except ImportError:
                logger.warning("SentenceTransformer not available, embeddings disabled")
                return None, {}
            except Exception as e:
                logger.error(f"Failed to initialize embeddings: {e}")
                return None, {}
        
        try:
            # Try to initialize with timeout
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(init_embeddings)
                try:
                    model, embeddings = future.result(timeout=timeout)
                    self._embedding_model = model
                    self._category_embeddings = embeddings
                    if model:
                        logger.info("Embeddings initialized successfully")
                    else:
                        logger.warning("Embeddings initialization returned None - using keyword fallback")
                except concurrent.futures.TimeoutError:
                    logger.warning(f"Embedding initialization timed out after {timeout}s - using keyword fallback")
                    future.cancel()
        except Exception as e:
            logger.error(f"Error during embedding initialization: {e}")
            logger.info("Will use keyword-based classification as fallback")
    
    def _initialize_embeddings(self):
        """Initialize category reference embeddings (legacy method for compatibility)."""
        # This method is now called only if lazy initialization is still needed
        # It delegates to the timeout-protected version
        if self._embedding_model is None and self._category_embeddings == {}:
            self._initialize_embeddings_with_timeout()
    
    def _get_embedding(self, text: str):
        """Get embedding for text."""
        try:
            if self._embedding_model:
                return self._embedding_model.encode([text])
        except Exception as e:
            logger.warning(f"Failed to get embedding: {e}")
        return None
    
    def _cosine_similarity(self, query_embedding, reference_embeddings):
        """Calculate cosine similarity between query and reference embeddings."""
        import numpy as np
        
        # Handle single vector vs matrix
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        if len(reference_embeddings.shape) == 1:
            reference_embeddings = reference_embeddings.reshape(1, -1)
        
        # Calculate cosine similarities
        similarities = []
        for ref_emb in reference_embeddings:
            dot_product = np.dot(query_embedding[0], ref_emb)
            norm_product = np.linalg.norm(query_embedding[0]) * np.linalg.norm(ref_emb)
            if norm_product > 0:
                similarities.append(dot_product / norm_product)
            else:
                similarities.append(0.0)
        
        return np.array(similarities).reshape(1, -1)
    
    def _similarity_to_intent_result(self, query: str, best_category: IntentCategory, 
                                   best_score: float, all_similarities: dict) -> IntentResult:
        """Convert similarity scores to IntentResult."""
        
        # Adjust confidence based on similarity score and relative difference
        confidence = min(0.95, best_score * 1.2)  # Scale up similarity to confidence
        
        # Check for metadata queries
        if best_category == IntentCategory.METADATA_QUERY and confidence >= 0.6:
            return IntentResult(
                category=IntentCategory.METADATA_QUERY,
                confidence=confidence,
                reasoning=f"Semantic similarity to metadata queries: {best_score:.2f}",
                should_process=True
            )
        
        # Check for technical AI queries
        elif best_category == IntentCategory.TECHNICAL_AI_QUERY and confidence >= 0.6:
            return IntentResult(
                category=IntentCategory.TECHNICAL_AI_QUERY,
                confidence=confidence,
                reasoning=f"Semantic similarity to technical AI topics: {best_score:.2f}",
                should_process=True
            )
        
        # Check for cross-database queries
        elif best_category == IntentCategory.CROSS_DB_QUERY and confidence >= 0.65:
            return IntentResult(
                category=IntentCategory.CROSS_DB_QUERY,
                confidence=confidence,
                reasoning=f"Semantic similarity to cross-database queries: {best_score:.2f}",
                should_process=True
            )
        
        # Check if it's clearly repository-related
        elif best_category == IntentCategory.REPOSITORY_RELATED and confidence >= 0.6:
            return IntentResult(
                category=IntentCategory.REPOSITORY_RELATED,
                confidence=confidence,
                reasoning=f"Semantic similarity to AI risk topics: {best_score:.2f}",
                should_process=True
            )
        
        # Check for chit-chat
        elif best_category == IntentCategory.CHIT_CHAT and confidence >= 0.7:
            return IntentResult(
                category=IntentCategory.CHIT_CHAT,
                confidence=confidence,
                reasoning=f"Semantic similarity to greetings: {best_score:.2f}",
                should_process=False,
                suggested_response="Hello! I'm here to help you understand AI risks. What would you like to know about AI safety, employment impacts, privacy concerns, or bias issues?"
            )
        
        # Check for general knowledge
        elif best_category == IntentCategory.GENERAL_KNOWLEDGE and confidence >= 0.7:
            import random
            responses = [
                "I specialize in AI risks. Try asking about AI impacts on employment, safety concerns, privacy issues, or algorithmic bias.",
                "My focus is AI risk analysis. Consider questions about workforce disruption, system failures, data privacy, or discriminatory algorithms.",
                "I provide AI risk insights. Explore topics like automation impacts, safety incidents, surveillance concerns, or fairness issues.",
                "The repository covers AI risks. Ask about job displacement, operational hazards, security breaches, or equity challenges.",
                "I assist with AI risk queries. Topics include economic effects, safety protocols, privacy violations, or bias patterns.",
                "My expertise is AI risks. Inquire about employment changes, accident risks, data misuse, or algorithmic discrimination.",
                "I handle AI risk information. Try questions about labor impacts, system safety, information security, or fairness metrics."
            ]
            
            return IntentResult(
                category=IntentCategory.GENERAL_KNOWLEDGE,
                confidence=confidence,
                reasoning=f"Semantic similarity to general topics: {best_score:.2f}",
                should_process=False,
                suggested_response=random.choice(responses)
            )
        
        # Default to repository with lower confidence
        else:
            return IntentResult(
                category=IntentCategory.REPOSITORY_RELATED,
                confidence=max(0.4, confidence * 0.8),
                reasoning=f"Uncertain classification - defaulting to repository (similarity: {best_score:.2f})",
                should_process=True
            )
    
    def _fallback_classification(self, query: str) -> IntentResult:
        """Simple fallback when semantic classification fails."""
        query_lower = query.lower()
        
        # Simple chit-chat detection
        if any(word in query_lower for word in ['hello', 'hi', 'thanks', 'goodbye']):
            return IntentResult(
                category=IntentCategory.CHIT_CHAT,
                confidence=0.8,
                reasoning="Simple greeting detection",
                should_process=False,
                suggested_response="Hello! I'm here to help you understand AI risks. What would you like to know about AI safety, employment impacts, privacy concerns, or bias issues?"
            )
        
        # Assume repository-related for anything else
        return IntentResult(
            category=IntentCategory.REPOSITORY_RELATED,
            confidence=0.5,
            reasoning="Fallback classification - assuming repository query",
            should_process=True
        )
    
    def _should_use_gemini(self, query: str) -> bool:
        """Determine if we should use Gemini for classification."""
        # Use Gemini for ambiguous cases, complex queries, or new patterns
        return (
            len(query) > 50 and  # Longer queries might need deeper analysis
            len(query) < 500 and  # But not too long (cost control)
            not any(word in query.lower() for word in ['test', 'hello', 'hi'])  # Skip obvious cases
        )
    
    def _classify_with_gemini(self, query: str) -> Optional[IntentResult]:
        """Use Gemini for more sophisticated intent classification."""
        try:
            if not self.gemini_model:
                from ...core.models.gemini import GeminiModel
                self.gemini_model = GeminiModel(settings.GEMINI_API_KEY)
            
            prompt = f"""Classify this user query into one of these categories:
1. REPOSITORY_RELATED - Questions about AI risks, safety, employment impacts, bias, privacy, governance
2. METADATA_QUERY - Questions about the repository structure, statistics, counts, taxonomy
3. TECHNICAL_AI_QUERY - Technical questions about how AI/ML works (transformers, neural nets, etc)
4. CROSS_DB_QUERY - Questions that span multiple databases (risks with mitigations, etc)
5. CHIT_CHAT - Greetings, pleasantries, casual conversation
6. GENERAL_KNOWLEDGE - Questions about topics unrelated to AI risks
7. JUNK - Test messages, gibberish, spam
8. OVERRIDE_ATTEMPT - Trying to change system behavior or bypass instructions

Query: "{query}"

Respond with just the category name and confidence (0.0-1.0):
Format: CATEGORY_NAME confidence"""
            
            response = self.gemini_model.generate(prompt)
            
            # Parse response
            parts = response.strip().split()
            if len(parts) >= 2:
                category_name = parts[0]
                try:
                    confidence = float(parts[1])
                    category = IntentCategory(category_name.lower())
                    
                    return IntentResult(
                        category=category,
                        confidence=confidence,
                        reasoning="Gemini classification",
                        should_process=category == IntentCategory.REPOSITORY_RELATED
                    )
                except (ValueError, KeyError):
                    logger.warning(f"Could not parse Gemini response: {response}")
            
        except Exception as e:
            logger.error(f"Error in Gemini classification: {str(e)}")
        
        return None
    
    def _log_performance(self, duration: float, method: str):
        """Track classification performance."""
        self.classification_times.append(duration)
        self.classification_count += 1
        
        if duration > 0.5:  # Log slow classifications
            logger.warning(f"Slow intent classification: {duration:.3f}s using {method}")
        
        # Log performance stats every 100 classifications
        if self.classification_count % 100 == 0:
            avg_time = sum(self.classification_times[-100:]) / min(100, len(self.classification_times))
            logger.info(f"Intent classification avg time (last 100): {avg_time:.3f}s")
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics."""
        if not self.classification_times:
            return {}
        
        return {
            "total_classifications": self.classification_count,
            "average_time": sum(self.classification_times) / len(self.classification_times),
            "min_time": min(self.classification_times),
            "max_time": max(self.classification_times)
        }

# Global intent classifier instance
intent_classifier = IntentClassifier()