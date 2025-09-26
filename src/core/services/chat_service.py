"""
Chat service that orchestrates the entire conversation flow.
"""
import json
from typing import List, Dict, Any, Tuple, Optional
from langchain.docstore.document import Document

from ..models.gemini import GeminiModel
from ..storage.vector_store import VectorStore
from ..query.processor import QueryProcessor
from .citation_service import CitationService
# Import intent classifier at module level to ensure it initializes at startup
from ..query.intent_classifier import intent_classifier, IntentCategory
# Import these locally to avoid import errors
# from ..validation.response_validator import validation_chain
# from ..metadata import metadata_service
# from ..query.technical_handler import get_technical_handler
# from .smart_web_search import smart_web_search
# from .language_service import language_service
from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

class ChatService:
    """Main service for handling chat interactions."""
    
    def __init__(self, 
                 gemini_model: Optional[GeminiModel] = None,
                 vector_store: Optional[VectorStore] = None,
                 query_monitor: Optional[Any] = None):
        """
        Initialize the chat service.
        
        Args:
            gemini_model: Gemini model instance
            vector_store: Vector store instance
            query_monitor: Query monitor for advanced analysis
        """
        self.gemini_model = gemini_model
        self.vector_store = vector_store
        self.query_processor = QueryProcessor(query_monitor)
        self.citation_service = CitationService()
        
        # Initialize language service with Gemini model
        if gemini_model:
            try:
                from .language_service import language_service
                language_service.gemini_model = gemini_model
            except Exception as e:
                logger.warning(f"Could not initialize language service: {e}")
        
        # Session language tracking
        self.session_languages: Dict[str, Dict[str, Any]] = {}
        
        # Conversation storage (in production, use a proper database)
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
    
    def process_query(self, message: str, conversation_id: str, session_id: str = None, language_code: str = None) -> Tuple[str, List[Any], Optional[Dict[str, Any]]]:
        """
        Process a user query with intent classification and pre-filtering.
        
        Args:
            message: User message
            conversation_id: Conversation identifier
            session_id: Session identifier for snippet storage and language tracking
            language_code: Optional manually selected language code
            
        Returns:
            Tuple of (response_text, retrieved_documents, language_info)
        """
        try:
            # Handle language selection priority
            if language_code:
                # User explicitly selected a language - use it and store for session
                try:
                    from .language_service import language_service
                    language_info = language_service.get_language_info(language_code)
                    if session_id and language_info:
                        self.session_languages[session_id] = language_info
                except Exception as lang_error:
                    logger.warning(f"Failed to get language info for code '{language_code}': {lang_error}")
                    # Fallback to session language or default
                    if session_id and session_id in self.session_languages:
                        language_info = self.session_languages[session_id]
                    else:
                        language_info = self._get_default_language_info()
            else:
                # No explicit selection, check session or detect
                language_info = self._get_or_detect_language(message, session_id)
            # 1. Intent classification (Phase 2.1) - Using working version from copy folder
            # Intent classifier is now imported at module level for proper initialization
            intent_result = intent_classifier.classify_intent(message)
            
            # 2. Route based on intent category
            # 2.1 Handle taxonomy queries with highest priority
            if intent_result.category == IntentCategory.TAXONOMY_QUERY:
                logger.info(f"Processing taxonomy query (confidence: {intent_result.confidence:.2f})")
                
                try:
                    logger.info("Attempting to import TaxonomyHandler...")
                    from ..taxonomy.taxonomy_handler import TaxonomyHandler
                    logger.info("TaxonomyHandler imported successfully")
                    
                    # Create taxonomy handler instance
                    logger.info("Creating TaxonomyHandler instance...")
                    taxonomy_handler = TaxonomyHandler()
                    logger.info("TaxonomyHandler instance created successfully")
                    
                    # Get structured taxonomy response
                    logger.info(f"Calling handle_taxonomy_query with message: {message[:100]}...")
                    taxonomy_response = taxonomy_handler.handle_taxonomy_query(message)
                    logger.info("Taxonomy response generated successfully")
                    
                    # Handle language translation if needed
                    response_content = taxonomy_response.content
                    if self.gemini_model and language_info and language_info.get('code', 'en') != 'en':
                        try:
                            from ..services.language_service import language_service
                            language_code = language_info.get('code', 'en')
                            language_name = language_info.get('english_name', 'English')
                            special_prompt = language_service.get_language_prompt(language_code)
                            
                            translation_prompt = f"""Translate this taxonomy information to {language_name}:

{response_content}

{special_prompt}
Keep all formatting, headings, and structure intact.
Translate technical terms appropriately for {language_name} speakers."""
                            
                            response_content = self.gemini_model.generate(translation_prompt, [])
                            logger.info(f"Translated taxonomy response to {language_name}")
                        except Exception as e:
                            logger.warning(f"Failed to translate taxonomy response: {e}")
                    
                    # Create source citation for the preprint
                    sources = [{
                        'metadata': {
                            'title': taxonomy_response.source,
                            'rid': 'PREPRINT-001',
                            'type': 'preprint'
                        },
                        'page_content': 'AI Risk Repository Preprint - Comprehensive taxonomy reference'
                    }]
                    
                    # Update conversation history
                    self._update_conversation_history(conversation_id, message, response_content)
                    return response_content, sources, language_info
                    
                except Exception as e:
                    import traceback
                    logger.error(f"Failed to handle taxonomy query: {e}")
                    logger.error(f"Exception type: {type(e).__name__}")
                    logger.error(f"Full traceback:\n{traceback.format_exc()}")
                    # Fall through to metadata handler as backup
                    intent_result.category = IntentCategory.METADATA_QUERY
            
            # 2.2 Handle metadata queries
            if intent_result.category == IntentCategory.METADATA_QUERY:
                logger.info(f"Processing metadata query (confidence: {intent_result.confidence:.2f})")
                
                try:
                    from ..metadata import metadata_service
                    
                    # Initialize metadata service if needed
                    if not metadata_service._initialized:
                        metadata_service.initialize()
                    
                    # Set gemini model for language-aware messages
                    if self.gemini_model:
                        metadata_service.gemini_model = self.gemini_model
                    
                    # Execute metadata query
                    response, raw_results = metadata_service.query(message)
                except ImportError as e:
                    logger.error(f"Failed to import metadata service: {e}")
                    response = "Metadata service is currently unavailable."
                    raw_results = []
                
                # Update conversation history
                self._update_conversation_history(conversation_id, message, response)
                return response, raw_results, language_info
            
            elif intent_result.category == IntentCategory.TECHNICAL_AI_QUERY:
                logger.info(f"Processing technical AI query (confidence: {intent_result.confidence:.2f})")
                
                try:
                    from ..query.technical_handler import get_technical_handler
                    
                    # Get technical handler
                    technical_handler = get_technical_handler()
                    
                    # Set up Gemini model
                    if self.gemini_model:
                        technical_handler.gemini_model = self.gemini_model
                    
                    # Execute technical query with language info
                    response, sources = technical_handler.handle_technical_query(message, language_info)
                except ImportError as e:
                    logger.error(f"Failed to import technical handler: {e}")
                    response = "Technical query handler is currently unavailable."
                    sources = []
                
                # Update conversation history
                self._update_conversation_history(conversation_id, message, response)
                return response, sources, language_info
            
            elif intent_result.category == IntentCategory.CROSS_DB_QUERY:
                logger.info(f"Processing cross-database query (confidence: {intent_result.confidence:.2f})")
                
                try:
                    from ..metadata import metadata_service
                    
                    # Initialize metadata service if needed
                    if not metadata_service._initialized:
                        metadata_service.initialize()
                    
                    # Set gemini model for language-aware messages
                    if self.gemini_model:
                        metadata_service.gemini_model = self.gemini_model
                    
                    # First, try to get structured data from metadata service
                    metadata_response, raw_results = metadata_service.query(message)
                except ImportError as e:
                    logger.error(f"Failed to import metadata service: {e}")
                    metadata_response = "Metadata service is currently unavailable."
                    raw_results = []
                
                # Also get related documents from vector store for context
                query_type, domain = self.query_processor.analyze_query(message, conversation_id)
                
                # For cross-domain queries, get documents from multiple domains
                if 'between' in message.lower() or 'cross-domain' in message.lower() or 'cross domain' in message.lower():
                    # Extract domains mentioned in query
                    domains_mentioned = []
                    for d in ['healthcare', 'finance', 'education', 'military', 'legal']:
                        if d in message.lower():
                            domains_mentioned.append(d)
                    
                    # Get documents for each domain
                    docs = []
                    if domains_mentioned and self.vector_store:
                        for domain_term in domains_mentioned:
                            # Search for privacy risks in each specific domain
                            search_query = f"{domain} risks {domain_term}"
                            domain_docs = self.vector_store.get_relevant_documents(
                                search_query, k=3
                            )
                            docs.extend(domain_docs)
                        # Remove duplicates
                        seen = set()
                        unique_docs = []
                        for doc in docs:
                            doc_id = doc.metadata.get('rid', doc.page_content[:50])
                            if doc_id not in seen:
                                seen.add(doc_id)
                                unique_docs.append(doc)
                        docs = unique_docs[:6]  # Limit to 6 docs total
                    else:
                        docs = self.vector_store.get_relevant_documents(message, k=4) if self.vector_store else []
                else:
                    docs = self.vector_store.get_relevant_documents(message, k=3) if self.vector_store else []
                
                # Combine results if we have both
                if docs and raw_results:
                    # Create enriched response combining both sources
                    combined_response = f"{metadata_response}\n\n**Related Repository Documents:**\n"
                    for i, doc in enumerate(docs[:3], 1):
                        rid = doc.metadata.get('rid', 'Unknown')
                        title = doc.metadata.get('title', 'Untitled')
                        combined_response += f"\n{i}. {title} ({rid})"
                    
                    # Combine sources for Related Documents tab
                    combined_sources = raw_results + docs
                    
                    self._update_conversation_history(conversation_id, message, combined_response)
                    return combined_response, combined_sources
                else:
                    # Return just metadata results if no documents found
                    self._update_conversation_history(conversation_id, message, metadata_response)
                    return metadata_response, raw_results
            
            # 3. Multi-stage classification for better taxonomy detection
            # Check taxonomy relevance if initial classification is uncertain
            if intent_result.confidence < 0.7 and intent_result.category != IntentCategory.TAXONOMY_QUERY:
                # Check taxonomy relevance
                taxonomy_relevance = intent_classifier.check_taxonomy_relevance(message)
                logger.info(f"Taxonomy relevance check: {taxonomy_relevance:.2f} for uncertain query")
                
                # Lower threshold and add concept checking for better coverage
                if taxonomy_relevance > 0.4 or intent_classifier.contains_taxonomy_concepts(message):
                    # Route to taxonomy handler
                    logger.info(f"Routing to taxonomy handler based on relevance score: {taxonomy_relevance:.2f}")
                    try:
                        from ..taxonomy.taxonomy_handler import TaxonomyHandler
                        taxonomy_handler = TaxonomyHandler()
                        taxonomy_response = taxonomy_handler.handle_taxonomy_query(message)
                        
                        # Handle language translation if needed
                        response_content = taxonomy_response.content
                        if self.gemini_model and language_info and language_info.get('code', 'en') != 'en':
                            try:
                                from ..services.language_service import language_service
                                language_code = language_info.get('code', 'en')
                                language_name = language_info.get('english_name', 'English')
                                special_prompt = language_service.get_language_prompt(language_code)
                                
                                translation_prompt = f"""Translate this taxonomy information to {language_name}:

{response_content}

{special_prompt}
Keep all formatting, headings, and structure intact."""
                                
                                response_content = self.gemini_model.generate(translation_prompt, [])
                            except Exception as e:
                                logger.warning(f"Failed to translate taxonomy response: {e}")
                        
                        sources = [{
                            'metadata': {'title': taxonomy_response.source, 'rid': 'PREPRINT-001'},
                            'page_content': 'AI Risk Repository Preprint - Taxonomy reference'
                        }]
                        
                        self._update_conversation_history(conversation_id, message, response_content)
                        return response_content, sources, language_info
                    except Exception as e:
                        logger.error(f"Failed to handle as taxonomy query: {e}")
            
            # 4. Handle non-repository queries
            elif not intent_result.should_process:
                logger.info(f"Query filtered by intent classifier: {intent_result.category.value} (confidence: {intent_result.confidence:.2f})")
                
                # Before returning generic response, check if it contains taxonomy concepts
                if intent_classifier.contains_taxonomy_concepts(message):
                    logger.info("Query contains taxonomy concepts despite low confidence - routing to taxonomy handler")
                    try:
                        from ..taxonomy.taxonomy_handler import TaxonomyHandler
                        taxonomy_handler = TaxonomyHandler()
                        taxonomy_response = taxonomy_handler.handle_taxonomy_query(message)
                        
                        response_content = taxonomy_response.content
                        if self.gemini_model and language_info and language_info.get('code', 'en') != 'en':
                            try:
                                from ..services.language_service import language_service
                                language_code = language_info.get('code', 'en')
                                language_name = language_info.get('english_name', 'English')
                                special_prompt = language_service.get_language_prompt(language_code)
                                
                                translation_prompt = f"""Translate to {language_name}: {response_content}"""
                                response_content = self.gemini_model.generate(translation_prompt, [])
                            except Exception as e:
                                logger.warning(f"Translation failed: {e}")
                        
                        sources = [{
                            'metadata': {'title': 'AI Risk Repository Preprint', 'rid': 'PREPRINT-001'},
                            'page_content': 'Taxonomy reference'
                        }]
                        
                        self._update_conversation_history(conversation_id, message, response_content)
                        return response_content, sources, language_info
                    except Exception as e:
                        logger.error(f"Taxonomy fallback failed: {e}")
                
                if intent_result.suggested_response:
                    # Use session language instead of detecting from query
                    if self.gemini_model and language_info:
                        try:
                            # Get language details
                            from ..services.language_service import language_service
                            language_code = language_info.get('code', 'en')
                            language_name = language_info.get('english_name', 'English')
                            special_prompt = language_service.get_language_prompt(language_code)
                            
                            language_prompt = f"""English response template: {intent_result.suggested_response}

CRITICAL INSTRUCTION: 
You MUST translate the entire English response template above to {language_name}.
{special_prompt}
Maintain the same helpful tone and all the AI risk topic suggestions.
Do NOT add any extra text or explanations.

Your response must be ONLY the translated text, nothing else."""
                            
                            response = self.gemini_model.generate(language_prompt, [])
                            logger.info(f"Generated {language_name} out-of-scope response")
                        except Exception as e:
                            logger.warning(f"Failed to translate out-of-scope response: {e}")
                            # Fallback to English template
                            response = intent_result.suggested_response
                    else:
                        response = intent_result.suggested_response
                else:
                    # Use prompt manager to get language-aware out-of-scope response
                    from ...config.prompts import prompt_manager
                    out_of_scope_prompt = prompt_manager._handle_out_of_scope(message, language_info)
                    
                    # Generate response using Gemini to ensure correct language
                    if self.gemini_model:
                        try:
                            response = self.gemini_model.generate(out_of_scope_prompt, [])
                        except Exception as e:
                            logger.warning(f"Failed to generate out-of-scope response: {e}")
                            # Fallback to generic message
                            response = "This topic is outside the AI Risk Repository's scope."
                    else:
                        response = "This topic is outside the AI Risk Repository's scope."
                
                # Update conversation history even for filtered queries
                self._update_conversation_history(conversation_id, message, response)
                return response, [], language_info
            
            # 4. Process repository-related queries
            logger.info(f"Processing repository query (intent confidence: {intent_result.confidence:.2f})")
            
            # 4. Query refinement check (Phase 2.2) - handle over-broad queries
            try:
                from ...core.query.refinement import query_refiner
                refinement_result = query_refiner.analyze_query(message)
            except ImportError as e:
                logger.warning(f"Failed to import query refiner: {e}")
                refinement_result = None
            
            # 5. Handle over-broad queries with suggestions (less aggressive)
            if refinement_result and refinement_result.needs_refinement and refinement_result.complexity.value == 'very_broad':
                logger.info(f"Query is very broad and needs refinement: {refinement_result.complexity.value}")
                
                # Use auto-refined query if available
                if refinement_result.refined_query:
                    logger.info(f"Using auto-refined query: {refinement_result.refined_query}")
                    message = refinement_result.refined_query
                elif refinement_result.suggestions:
                    # Only block very_broad queries with suggestions, let broad queries proceed
                    suggestion_response = query_refiner.format_suggestions_response(refinement_result, language_info)
                    self._update_conversation_history(conversation_id, message, suggestion_response)
                    return suggestion_response, [], language_info
            elif refinement_result and refinement_result.needs_refinement and refinement_result.complexity.value == 'broad':
                # For broad queries, use auto-refined query if available, but don't block with suggestions
                if refinement_result.refined_query:
                    logger.info(f"Using auto-refined query for broad query: {refinement_result.refined_query}")
                    message = refinement_result.refined_query
                # Let broad queries proceed to retrieval even if they have suggestions
            
            # 6. Analyze the query
            query_type, domain = self.query_processor.analyze_query(message)
            
            # 7. Retrieve relevant documents
            docs = self._retrieve_documents(message, query_type, domain)
            
            # 8. Format context
            context = self._format_context(docs, query_type)
            
            # 9. Generate response
            response = self._generate_response(message, query_type, domain, context, conversation_id, docs, language_info)
            
            # 10. Check if web search needed and append results
            try:
                from .smart_web_search import smart_web_search
                web_results = smart_web_search.search_if_needed(message, context, len(docs), domain)
                if web_results:
                    web_context = smart_web_search.format_search_results(web_results)
                    response += web_context
                    logger.info(f"Added {len(web_results)} web search results to response")
            except ImportError as e:
                logger.warning(f"Failed to import smart web search: {e}")
            
            # 11. Clean response to remove any unprompted additions
            # Remove any "Risk Taxonomies" or similar sections that weren't asked for
            response_lines = response.split('\n')
            cleaned_lines = []
            skip_section = False
            
            for line in response_lines:
                # Detect start of unprompted sections
                if any(trigger in line for trigger in ['Risk Taxonomies', 'Additional Information:', 'You might also be interested']):
                    skip_section = True
                    logger.info(f"Removing unprompted section starting with: {line[:50]}")
                    continue
                
                # Reset skip flag on new paragraph/section that looks legitimate
                if skip_section and line.strip() == '':
                    skip_section = False
                
                if not skip_section:
                    cleaned_lines.append(line)
            
            response = '\n'.join(cleaned_lines).strip()
            
            # 12. Enhance with citations
            enhanced_response = self.citation_service.enhance_response_with_citations(response, docs, session_id)
            
            # 13. Self-validation chain for quality assurance
            try:
                from ..validation.response_validator import validation_chain
                validated_response, validation_results = validation_chain.validate_and_improve(
                    response=enhanced_response,
                    query=message,
                    documents=docs,
                    domain=domain
                )
            except ImportError as e:
                logger.warning(f"Failed to import validation chain: {e}")
                validated_response = enhanced_response
                validation_results = None
            
            # Log validation results
            if validation_results:
                logger.info(f"Response validation: {validation_results.overall_result.value} "
                           f"(score: {validation_results.overall_score:.2f})")
                
                if validation_results.overall_score < 0.6:
                    logger.warning(f"Low quality response detected. Recommendations: {validation_results.recommendations}")
            
            # 14. Update conversation history
            self._update_conversation_history(conversation_id, message, validated_response)
            
            return validated_response, docs, language_info
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            # Try to get language info safely
            language_info = None
            if session_id and session_id in self.session_languages:
                language_info = self.session_languages.get(session_id)
            if not language_info:
                language_info = self._get_default_language_info()
            # Translate error message
            english_error = f"I encountered an error while processing your question: {str(e)}"
            error_response = self._translate_error_message(english_error, language_info)
            return error_response, [], language_info
    
    def _retrieve_documents(self, message: str, query_type: str, domain: str = None) -> List[Document]:
        """Retrieve relevant documents with relevance threshold filtering."""
        if not self.vector_store:
            logger.warning("No vector store available")
            return []
        
        try:
            # Special handling for TASRA Type queries (e.g., "Type 3", "Type 1")
            # to prevent confusion with database IDs
            import re
            type_pattern = re.match(r'.*\btype\s*(\d+)\b.*', message.lower())
            if type_pattern:
                type_num = type_pattern.group(1)
                # Map common TASRA types to their full names
                tasra_types = {
                    '1': 'Type 1: Diffusion of responsibility',
                    '2': 'Type 2: Bigger than expected',
                    '3': 'Type 3: Worse than expected',
                    '4': 'Type 4',  # Add more as discovered
                    '5': 'Type 5: Criminal weaponization'
                }
                if type_num in tasra_types:
                    # Replace the query with the full TASRA type name
                    full_type_name = tasra_types[type_num]
                    message = message.lower().replace(f'type {type_num}', full_type_name)
                    logger.info(f"Detected TASRA Type query, searching for: {full_type_name}")
            
            # Use the domain already determined by query_processor (don't override with rule-based)
            # The domain was already correctly classified by LLM in analyze_query()
            if not domain:
                # Only use rule-based as fallback if no domain was determined
                try:
                    from ...config.domains import domain_classifier
                    domain = domain_classifier.classify_domain(message)
                    logger.info(f"Using fallback rule-based domain classification: {domain}")
                except ImportError as e:
                    logger.warning(f"Failed to import domain classifier: {e}")
                    domain = "general"
            else:
                logger.info(f"Using LLM domain classification: {domain}")
            
            # Special handling for biosecurity-related queries
            biosecurity_keywords = ['biosecurity', 'biosafety', 'biological', 'bioweapon', 'pathogen', 'cbrn']
            if any(keyword in message.lower() for keyword in biosecurity_keywords):
                logger.info("Detected biosecurity-related query, expanding search")
                # Expand search to include CBRN and biological threat terms
                all_docs = []
                search_terms = [
                    message,
                    "CBRN biological threat AI",
                    "biological agent AI misuse"
                ]
                for search_query in search_terms:
                    try:
                        bio_docs = self.vector_store.get_relevant_documents(search_query, k=3)
                        all_docs.extend(bio_docs)
                    except Exception as e:
                        logger.warning(f"Error searching for '{search_query}': {e}")
                
                # Remove duplicates based on content
                seen_contents = set()
                unique_docs = []
                for doc in all_docs:
                    content_hash = hash(doc.page_content[:200] if len(doc.page_content) > 200 else doc.page_content)
                    if content_hash not in seen_contents:
                        seen_contents.add(content_hash)
                        unique_docs.append(doc)
                
                logger.info(f"Retrieved {len(unique_docs)} unique documents for biosecurity query")
                return unique_docs[:8]  # Return top 8 unique docs
            
            # Check if domain supports enhanced search
            try:
                from ...config.domains import domain_classifier
                domain_config = domain_classifier.get_domain_config(domain)
            except ImportError as e:
                logger.warning(f"Failed to import domain classifier: {e}")
                domain_config = None
            
            if domain_config and domain_config.enhanced_search:
                if domain == "socioeconomic":
                    # Use existing employment-specific enhancement
                    enhanced_query = self.query_processor.enhance_query(message, query_type)
                else:
                    # For other domains, use domain-specific search queries
                    try:
                        enhanced_queries = domain_classifier.get_domain_queries(domain)
                    except Exception as e:
                        logger.warning(f"Failed to get domain queries: {e}")
                        enhanced_queries = None
                    if enhanced_queries:
                        # Choose the best enhanced query based on the original message
                        enhanced_query = self._select_best_enhanced_query(message, enhanced_queries)
                        logger.info(f"Using enhanced search query for {domain}: {enhanced_query}")
                    else:
                        enhanced_query = message
                
                docs = self.vector_store.get_relevant_documents(
                    enhanced_query, 
                    k=settings.DOMAIN_DOCS_RETRIEVED, 
                    domain=domain
                )
                
                # Filter and prioritize domain-specific documents
                docs = self.query_processor.filter_documents_by_relevance(docs, query_type, domain)
                
                logger.info(f"Retrieved {len(docs)} documents using enhanced {domain} search")
            else:
                # Standard retrieval for domains without enhanced search
                docs = self.vector_store.get_relevant_documents(
                    message, 
                    k=settings.DEFAULT_DOCS_RETRIEVED, 
                    domain=domain
                )
                
                # If no docs above threshold, this is likely out-of-scope
                if not docs:
                    logger.info(f"No relevant documents found above threshold for query: {message[:50]}...")
                    return []
                
                logger.info(f"Retrieved {len(docs)} documents using standard search")
            
            return docs
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []
    
    def _format_context(self, docs: List[Document], query_type: str) -> str:
        """Format retrieved documents into context string."""
        if not docs:
            return ""
        
        try:
            if self.vector_store:
                return self.vector_store.format_context_from_docs(docs)
            else:
                # Fallback formatting
                context = "INFORMATION FROM THE AI RISK REPOSITORY:\\n\\n"
                for i, doc in enumerate(docs, 1):
                    context += f"SECTION {i}:\\n{doc.page_content}\\n\\n"
                return context
                
        except Exception as e:
            logger.error(f"Error formatting context: {str(e)}")
            return ""
    
    def _generate_response(self, message: str, query_type: str, domain: str, context: str, conversation_id: str, docs: List[Document] = None, language_info: Dict[str, Any] = None) -> str:
        """Generate response using the AI model."""
        if not self.gemini_model:
            logger.warning("No Gemini model available")
            return self._create_fallback_response(context, message, language_info)
        
        try:
            # Prepare conversation history (with topic change detection)
            history = self._get_conversation_history(conversation_id, query_type)
            
            # Generate enhanced prompt with session awareness, RID information, and language
            prompt = self.query_processor.generate_prompt(message, query_type, domain, context, conversation_id, docs, language_info)
            
            # DEBUG: Log the actual prompt being sent to Gemini
            logger.info(f"=== GEMINI PROMPT DEBUG ===")
            logger.info(f"Query: {message}")
            logger.info(f"Query Type: {query_type}")
            logger.info(f"Context length: {len(context) if context else 0}")
            logger.info(f"Documents count: {len(docs) if docs else 0}")
            logger.info(f"Prompt preview (first 500 chars): {prompt[:500]}...")
            logger.info(f"=== END GEMINI PROMPT DEBUG ===")
            
            # Generate response
            response = self.gemini_model.generate(prompt, history)
            
            # DEBUG: Log the raw response from Gemini
            logger.info(f"=== GEMINI RESPONSE DEBUG ===")
            logger.info(f"Raw response length: {len(response)}")
            logger.info(f"Response preview (first 200 chars): {response[:200]}...")
            logger.info(f"=== END GEMINI RESPONSE DEBUG ===")
            
            return response
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if this is a safety/policy refusal
            if any(term in error_str for term in ['safety', 'policy', 'harmful', 'refused', 'violate', 'inappropriate']):
                logger.warning(f"Gemini refused query due to safety filters. Query: {message[:100]}...")
                logger.warning(f"Refusal reason: {str(e)}")
                
                # Try once more with educational context
                try:
                    educational_prompt = f"""Context: Analyzing documented AI risks from the MIT AI Risk Repository for research purposes.
                    
{prompt}

Focus on: risk assessment, prevention strategies, and safety measures."""
                    
                    logger.info("Retrying with educational context...")
                    response = self.gemini_model.generate(educational_prompt, history)
                    logger.info("Successfully generated response with educational context")
                    return response
                    
                except Exception as retry_error:
                    logger.error(f"Gemini refused even with educational context: {retry_error}")
                    # Return a helpful message to the user in their language
                    english_msg = ("I apologize, but I'm unable to provide detailed information on this specific topic due to content restrictions. "
                                  "Please try rephrasing your question to focus on risk prevention, safety measures, or policy considerations. "
                                  "You can also explore related topics like AI safety frameworks, risk mitigation strategies, or ethical guidelines.")
                    return self._translate_error_message(english_msg, language_info)
            else:
                # For non-safety errors, return the original error in user's language
                logger.error(f"Error generating response: {str(e)}")
                english_error = f"I encountered an error while generating a response: {str(e)}"
                return self._translate_error_message(english_error, language_info)
    
    def _create_fallback_response(self, context: str, message: str, language_info: Dict[str, Any] = None) -> str:
        """Create a fallback response when AI model is not available."""
        if context:
            english_msg = f"Based on the AI Risk Repository, here's what I found:\\n\\n{context[:1000]}..."
            return self._translate_error_message(english_msg, language_info)
        else:
            english_msg = "I'm sorry, but I couldn't find specific information in the AI Risk Repository for your query. The repository covers risks related to discrimination, privacy, misinformation, malicious use, human-computer interaction, socioeconomic impacts, and system safety."
            return self._translate_error_message(english_msg, language_info)
    
    def _get_conversation_history(self, conversation_id: str, current_query_type: str = None) -> List[Dict[str, Any]]:
        """Get conversation history for the model.
        
        Args:
            conversation_id: The conversation ID
            current_query_type: The type of the current query (to detect topic changes)
        """
        if conversation_id not in self.conversations:
            return []
        
        # Get last N messages
        history = self.conversations[conversation_id][-settings.MAX_CONVERSATION_HISTORY:]
        
        # If this appears to be a completely different topic, limit history
        # to avoid contamination between unrelated queries
        if current_query_type and len(history) > 0:
            last_message = history[-1]['content'] if history else ""
            
            # Check for obvious topic changes (very different queries)
            topic_change_indicators = [
                "when we all fall asleep" in last_message.lower() and "customer service" in current_query_type,
                "philosophical" in str(last_message).lower() and "technical" in current_query_type,
                len(last_message) < 50 and current_query_type == "technical"  # Short previous query, now technical
            ]
            
            if any(topic_change_indicators):
                logger.info("Topic change detected - limiting conversation history")
                # Only keep system context, not previous unrelated conversation
                return []
        
        # Convert to model format
        model_history = []
        for msg in history:
            if msg['role'] == 'user':
                model_history.append({"role": "user", "parts": [{"text": msg['content']}]})
            elif msg['role'] == 'assistant':
                model_history.append({"role": "model", "parts": [{"text": msg['content']}]})
        
        return model_history
    
    def _select_best_enhanced_query(self, original_message: str, enhanced_queries: List[str]) -> str:
        """Select the best enhanced query based on keyword matching with original message."""
        original_lower = original_message.lower()
        
        # Define keyword mappings for better query selection
        keyword_mappings = {
            'cybersecurity': ['security threats', 'cyber attacks', 'security vulnerabilities'],
            'cyber': ['security threats', 'cyber attacks', 'security vulnerabilities'],
            'security': ['security threats', 'security vulnerabilities'],
            'attack': ['cyber attacks', 'security threats'],
            'vulnerability': ['security vulnerabilities'],
            'privacy': ['privacy risks', 'data protection'],
            'bias': ['bias and discrimination', 'fairness and equity'],
            'discrimination': ['bias and discrimination', 'fairness and equity'],
            'governance': ['governance and policy', 'regulatory approaches'],
            'policy': ['governance and policy', 'regulatory approaches'],
            'regulation': ['regulatory approaches', 'governance and policy']
        }
        
        # Score each enhanced query based on keyword matches
        best_query = enhanced_queries[0]  # Default to first query
        best_score = 0
        
        for query in enhanced_queries:
            score = 0
            query_lower = query.lower()
            
            # Check direct keyword matches
            for word in original_lower.split():
                if word in query_lower:
                    score += 2
            
            # Check mapped keyword matches
            for keyword, mapped_terms in keyword_mappings.items():
                if keyword in original_lower:
                    for term in mapped_terms:
                        if term in query_lower:
                            score += 3
                            break
            
            if score > best_score:
                best_score = score
                best_query = query
        
        return best_query
    
    def _get_default_language_info(self) -> Dict[str, Any]:
        """
        Get default language info (English) safely.
        
        Returns:
            Default English language info dict
        """
        try:
            from .language_service import language_service
            return language_service.get_language_info("en")
        except Exception as e:
            logger.warning(f"Failed to get language info from service: {e}")
            # Return minimal English language info as fallback
            return {
                'code': 'en',
                'native_name': 'English',
                'english_name': 'English',
                'confidence': 1.0
            }
    
    def _get_or_detect_language(self, message: str, session_id: Optional[str]) -> Dict[str, Any]:
        """
        Get session language or detect from message.
        
        Args:
            message: User message
            session_id: Session identifier
            
        Returns:
            Language info dict
        """
        # If no session ID, default to English
        if not session_id:
            return self._get_default_language_info()
        
        # Check if we already have a language for this session
        if session_id in self.session_languages:
            return self.session_languages[session_id]
        
        # Try to detect language from the first message
        try:
            from .language_service import language_service
            language_info = language_service.detect_language(message)
            
            # Store for future use
            self.session_languages[session_id] = language_info
            
            logger.info(f"Detected language for session {session_id}: {language_info['english_name']} (confidence: {language_info.get('confidence', 0.9):.2f})")
            
            return language_info
        except Exception as e:
            logger.warning(f"Failed to detect language: {e}")
            # Fallback to English
            language_info = self._get_default_language_info()
            self.session_languages[session_id] = language_info
            return language_info
    
    def set_session_language(self, session_id: str, language_code: str) -> bool:
        """
        Manually set language for a session.
        
        Args:
            session_id: Session identifier
            language_code: Language code to set
            
        Returns:
            True if successful
        """
        try:
            from .language_service import language_service
            language_info = language_service.get_language_info(language_code)
            if language_info:
                self.session_languages[session_id] = language_info
                logger.info(f"Manually set language for session {session_id}: {language_info['english_name']}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to set session language: {e}")
            return False
    
    def get_session_language(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current language for a session."""
        return self.session_languages.get(session_id)
    
    def _translate_error_message(self, english_message: str, language_info: Dict[str, Any]) -> str:
        """
        Translate an error message to the user's session language.
        
        Args:
            english_message: The error message in English
            language_info: Language information for the session
            
        Returns:
            Translated error message or original if translation fails
        """
        # If no language info or already English, return as-is
        if not language_info or language_info.get('code') == 'en':
            return english_message
        
        # Try to translate using Gemini
        if self.gemini_model:
            try:
                from ..services.language_service import language_service
                language_code = language_info.get('code', 'en')
                language_name = language_info.get('english_name', 'English')
                special_prompt = language_service.get_language_prompt(language_code)
                
                translation_prompt = f"""Translate this error message to {language_name}:

{english_message}

CRITICAL INSTRUCTIONS:
1. Translate the ENTIRE message to {language_name}
2. Maintain the same helpful and apologetic tone
3. Keep any technical details if present
4. {special_prompt}
5. Return ONLY the translated message, no explanations

Translated message:"""
                
                translated = self.gemini_model.generate(translation_prompt, [])
                logger.info(f"Translated error message to {language_name}")
                return translated
                
            except Exception as e:
                logger.warning(f"Failed to translate error message: {e}")
                return english_message
        
        return english_message
    
    def _update_conversation_history(self, conversation_id: str, message: str, response: str) -> None:
        """Update conversation history."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        # Add user message and assistant response
        self.conversations[conversation_id].extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": response}
        ])
        
        # Keep only recent messages to avoid memory issues
        max_messages = settings.MAX_CONVERSATION_HISTORY * 2  # *2 for user+assistant pairs
        if len(self.conversations[conversation_id]) > max_messages:
            self.conversations[conversation_id] = self.conversations[conversation_id][-max_messages:]
    
    def generate_use_cases(self, domain: str) -> List[str]:
        """Generate use cases for a given domain."""
        if not self.gemini_model:
            logger.warning("No Gemini model available for use case generation")
            return [f"Use case 1 for {domain}", f"Use case 2 for {domain}", f"Use case 3 for {domain}"]

        try:
            prompt = f"Given the domain of {domain}, generate three concise and relevant use cases for an AI Risk Repository chatbot. The use cases should be short, to the point, and should be phrased as questions that a user might ask the chatbot. For example, for the domain 'finance', a good use case would be 'What are the risks of using AI in credit scoring?'. The use cases should be returned as a JSON object with a single key 'use_cases' which is a list of strings. For example: {{\"use_cases\": [\"What are the risks of using AI in credit scoring?\", \"How can I mitigate the risks of using AI in algorithmic trading?\", \"What are the best practices for using AI in fraud detection?\"]}}"
            response = self.gemini_model.generate(prompt, history=[])
            # The response is a string that looks like a dictionary, so we need to parse it
            # The response may contain markdown, so we need to remove it
            response = response.replace("```json", "").replace("```", "")
            use_cases = json.loads(response)['use_cases']
            return use_cases
        except Exception as e:
            logger.error(f"Error generating use cases: {str(e)}")
            return [f"Error generating use cases for {domain}"]

    def reset_conversation(self, conversation_id: str) -> None:
        """Reset conversation history."""
        if conversation_id in self.conversations:
            self.conversations[conversation_id] = []
        
        # Also reset the model if it supports it
        if self.gemini_model and hasattr(self.gemini_model, 'reset_conversation'):
            self.gemini_model.reset_conversation()