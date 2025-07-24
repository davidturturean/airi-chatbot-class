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
from ..validation.response_validator import validation_chain
from ..metadata import metadata_service
from ..query.technical_handler import get_technical_handler
from .smart_web_search import smart_web_search
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
        
        # Conversation storage (in production, use a proper database)
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
    
    def process_query(self, message: str, conversation_id: str) -> Tuple[str, List[Any]]:
        """
        Process a user query with intent classification and pre-filtering.
        
        Args:
            message: User message
            conversation_id: Conversation identifier
            
        Returns:
            Tuple of (response_text, retrieved_documents)
        """
        try:
            # 1. Intent classification (Phase 2.1) - Using working version from copy folder
            from ...core.query.intent_classifier import intent_classifier, IntentCategory
            intent_result = intent_classifier.classify_intent(message)
            
            # 2. Route based on intent category
            if intent_result.category == IntentCategory.METADATA_QUERY:
                logger.info(f"Processing metadata query (confidence: {intent_result.confidence:.2f})")
                
                # Initialize metadata service if needed
                if not metadata_service._initialized:
                    metadata_service.initialize()
                
                # Execute metadata query
                response, raw_results = metadata_service.query(message)
                
                # Update conversation history
                self._update_conversation_history(conversation_id, message, response)
                return response, raw_results
            
            elif intent_result.category == IntentCategory.TECHNICAL_AI_QUERY:
                logger.info(f"Processing technical AI query (confidence: {intent_result.confidence:.2f})")
                
                # Get technical handler
                technical_handler = get_technical_handler()
                
                # Set up Gemini model
                if self.gemini_model:
                    technical_handler.gemini_model = self.gemini_model
                
                # Execute technical query
                response, sources = technical_handler.handle_technical_query(message)
                
                # Update conversation history
                self._update_conversation_history(conversation_id, message, response)
                return response, sources
            
            elif intent_result.category == IntentCategory.CROSS_DB_QUERY:
                logger.info(f"Processing cross-database query (confidence: {intent_result.confidence:.2f})")
                
                # Initialize metadata service if needed
                if not metadata_service._initialized:
                    metadata_service.initialize()
                
                # First, try to get structured data from metadata service
                metadata_response, raw_results = metadata_service.query(message)
                
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
            
            # 3. Handle non-repository queries
            elif not intent_result.should_process:
                logger.info(f"Query filtered by intent classifier: {intent_result.category.value} (confidence: {intent_result.confidence:.2f})")
                
                if intent_result.suggested_response:
                    response = intent_result.suggested_response
                else:
                    response = "I can help you understand AI risks from the MIT AI Risk Repository. Try asking about employment impacts, safety concerns, privacy issues, or algorithmic bias."
                
                # Update conversation history even for filtered queries
                self._update_conversation_history(conversation_id, message, response)
                return response, []
            
            # 4. Process repository-related queries
            logger.info(f"Processing repository query (intent confidence: {intent_result.confidence:.2f})")
            
            # 4. Query refinement check (Phase 2.2) - handle over-broad queries
            from ...core.query.refinement import query_refiner
            refinement_result = query_refiner.analyze_query(message)
            
            # 5. Handle over-broad queries with suggestions (less aggressive)
            if refinement_result.needs_refinement and refinement_result.complexity.value == 'very_broad':
                logger.info(f"Query is very broad and needs refinement: {refinement_result.complexity.value}")
                
                # Use auto-refined query if available
                if refinement_result.refined_query:
                    logger.info(f"Using auto-refined query: {refinement_result.refined_query}")
                    message = refinement_result.refined_query
                elif refinement_result.suggestions:
                    # Only block very_broad queries with suggestions, let broad queries proceed
                    suggestion_response = query_refiner.format_suggestions_response(refinement_result)
                    self._update_conversation_history(conversation_id, message, suggestion_response)
                    return suggestion_response, []
            elif refinement_result.needs_refinement and refinement_result.complexity.value == 'broad':
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
            response = self._generate_response(message, query_type, domain, context, conversation_id, docs)
            
            # 10. Check if web search needed and append results
            web_results = smart_web_search.search_if_needed(message, context, len(docs))
            if web_results:
                web_context = smart_web_search.format_search_results(web_results)
                response += web_context
                logger.info(f"Added {len(web_results)} web search results to response")
            
            # 11. Enhance with citations
            enhanced_response = self.citation_service.enhance_response_with_citations(response, docs)
            
            # 12. Self-validation chain for quality assurance
            validated_response, validation_results = validation_chain.validate_and_improve(
                response=enhanced_response,
                query=message,
                documents=docs,
                domain=domain
            )
            
            # Log validation results
            logger.info(f"Response validation: {validation_results.overall_result.value} "
                       f"(score: {validation_results.overall_score:.2f})")
            
            if validation_results.overall_score < 0.6:
                logger.warning(f"Low quality response detected. Recommendations: {validation_results.recommendations}")
            
            # 12. Update conversation history
            self._update_conversation_history(conversation_id, message, validated_response)
            
            return validated_response, docs
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            error_response = f"I encountered an error while processing your question: {str(e)}"
            return error_response, []
    
    def _retrieve_documents(self, message: str, query_type: str, domain: str = None) -> List[Document]:
        """Retrieve relevant documents with relevance threshold filtering."""
        if not self.vector_store:
            logger.warning("No vector store available")
            return []
        
        try:
            # Use the domain already determined by query_processor (don't override with rule-based)
            # The domain was already correctly classified by LLM in analyze_query()
            if not domain:
                # Only use rule-based as fallback if no domain was determined
                from ...config.domains import domain_classifier
                domain = domain_classifier.classify_domain(message)
                logger.info(f"Using fallback rule-based domain classification: {domain}")
            else:
                logger.info(f"Using LLM domain classification: {domain}")
            
            # Check if domain supports enhanced search
            from ...config.domains import domain_classifier
            domain_config = domain_classifier.get_domain_config(domain)
            
            if domain_config and domain_config.enhanced_search:
                # Enhanced search for domains that support it
                if domain == "socioeconomic":
                    # Use existing employment-specific enhancement
                    enhanced_query = self.query_processor.enhance_query(message, query_type)
                else:
                    # For other domains, use domain-specific search queries
                    enhanced_queries = domain_classifier.get_domain_queries(domain)
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
    
    def _generate_response(self, message: str, query_type: str, domain: str, context: str, conversation_id: str, docs: List[Document] = None) -> str:
        """Generate response using the AI model."""
        if not self.gemini_model:
            logger.warning("No Gemini model available")
            return self._create_fallback_response(context, message)
        
        try:
            # Prepare conversation history
            history = self._get_conversation_history(conversation_id)
            
            # Generate enhanced prompt with session awareness and RID information
            prompt = self.query_processor.generate_prompt(message, query_type, domain, context, conversation_id, docs)
            
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
            logger.error(f"Error generating response: {str(e)}")
            return f"I encountered an error while generating a response: {str(e)}"
    
    def _create_fallback_response(self, context: str, message: str) -> str:
        """Create a fallback response when AI model is not available."""
        if context:
            return f"Based on the AI Risk Repository, here's what I found:\\n\\n{context[:1000]}..."
        else:
            return "I'm sorry, but I couldn't find specific information in the AI Risk Repository for your query. The repository covers risks related to discrimination, privacy, misinformation, malicious use, human-computer interaction, socioeconomic impacts, and system safety."
    
    def _get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for the model."""
        if conversation_id not in self.conversations:
            return []
        
        # Get last N messages and convert to model format
        history = self.conversations[conversation_id][-settings.MAX_CONVERSATION_HISTORY:]
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