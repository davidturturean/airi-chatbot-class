"""
Chat routes for the AIRI chatbot API.
"""
import json
import time
import os
from flask import Blueprint, request, jsonify, Response, stream_with_context

from ...core.services.chat_service import ChatService
from ...core.services.metrics_service import metrics_service
from ...config.logging import get_logger

logger = get_logger(__name__)

# Create blueprint
chat_bp = Blueprint('chat', __name__)

# This will be injected by the app factory
chat_service: ChatService = None

def init_chat_routes(chat_service_instance: ChatService):
    """Initialize chat routes with service dependency."""
    global chat_service
    chat_service = chat_service_instance

@chat_bp.route('/api/v1/sendMessage', methods=['POST'])
def send_message():
    """Non-streaming chat endpoint with metrics logging."""
    start_time = time.time()
    
    try:
        data = request.json
        
        # Log the incoming request
        logger.info(f"Received message: {data}")
        message = data.get('message', '')
        conversation_id = data.get('conversationId', 'default')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Get session ID and language from request
        session_id = data.get('session_id') or request.headers.get('X-Session-ID') or 'default'
        language_code = data.get('language_code')  # Get manually selected language
        
        # Get user identifiers for privacy-preserving tracking
        user_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        # Process the query
        result = chat_service.process_query(message, conversation_id, session_id, language_code)
        
        # Handle both old (2-tuple) and new (3-tuple) return formats
        if len(result) == 3:
            response_text, docs, language_info = result
        else:
            response_text, docs = result
            language_info = None
        
        # Calculate processing time
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Log metrics
        query_metrics = metrics_service.log_query(
            session_id=session_id,
            query=message,
            response=response_text,
            latency_ms=latency_ms,
            docs_retrieved=docs,
            intent=data.get('intent', 'general'),
            language=language_code or (language_info.get('code') if language_info else 'en'),
            user_ip=user_ip,
            user_agent=user_agent
        )
        
        response_data = {
            "id": conversation_id,
            "response": response_text,
            "status": "complete",
            "metrics": {
                "latency_ms": latency_ms,
                "citations_count": query_metrics.citations_count,
                "query_number": len(metrics_service.session_metrics.get(session_id, {}).get("queries", []))
            }
        }
        
        # Add language info if available
        if language_info:
            response_data["language"] = {
                "code": language_info.get('code'),
                "native_name": language_info.get('native_name'),
                "english_name": language_info.get('english_name'),
                "category": language_info.get('category', 'major')
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        
        # Log error metrics
        latency_ms = int((time.time() - start_time) * 1000)
        metrics_service.log_query(
            session_id=session_id if 'session_id' in locals() else 'error',
            query=message if 'message' in locals() else 'unknown',
            response="",
            latency_ms=latency_ms,
            error=e,
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@chat_bp.route('/api/v1/stream', methods=['POST'])
def stream_message():
    """Streaming chat endpoint with metrics logging."""
    start_time = time.time()
    
    try:
        data = request.json
        
        # Log the incoming request
        logger.info(f"Received stream request: {data}")
        message = data.get('message', '')
        conversation_id = data.get('conversationId', 'default')
        session_id = data.get('session_id') or request.headers.get('X-Session-ID') or 'default'
        language_code = data.get('language_code')  # Get manually selected language
        
        # Get user identifiers for metrics
        user_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Define a streaming response generator
        def generate():
            try:
                # Initialize variables
                query_type = "general"
                domain = None
                docs = []
                status_messages = []
                
                # Helper function to send status updates
                def send_status(message: str, stage: str = None):
                    status_data = {"status": message, "type": "status"}
                    if stage:
                        status_data["stage"] = stage
                    status_json = json.dumps(status_data) + '\n'
                    return status_json
                
                # Initial status update
                yield send_status("Initializing query processing...", "init")
                
                # Add system version info to logs
                from ...config.settings import settings
                logger.info(f"🔧 Processing with Field-Aware Hybrid: {settings.USE_FIELD_AWARE_HYBRID}")
                if chat_service.vector_store and hasattr(chat_service.vector_store, 'hybrid_retriever'):
                    if chat_service.vector_store.hybrid_retriever:
                        retriever_class = chat_service.vector_store.hybrid_retriever.__class__.__name__
                        logger.info(f"🎯 Using retriever: {retriever_class}")
                
                time.sleep(0.1)
                
                # Send initial analyzing status
                yield send_status("Analyzing your query...", "analysis")
                time.sleep(0.1)
                
                # Check query type first
                yield send_status("Classifying intent...", "classification") 
                time.sleep(0.1)
                
                # 1. Process the query through chat service
                # Process query and get language info
                yield send_status("Searching the AI Risk Repository...", "retrieval")
                time.sleep(0.1)
                
                result = chat_service.process_query(message, conversation_id, session_id, language_code)
                
                # After processing, indicate we're formatting the response
                yield send_status("Generating response...", "generation")
                time.sleep(0.1)
                
                # Handle both old (2-tuple) and new (3-tuple) return formats
                if len(result) == 3:
                    response_text, docs, language_info = result
                else:
                    response_text, docs = result
                    language_info = None
                
                # Check what type of results we got
                is_metadata_query = isinstance(docs, list) and docs and isinstance(docs[0], dict)
                is_technical_query = hasattr(docs, '__iter__') and docs and hasattr(docs[0], 'title') and hasattr(docs[0], 'url')
                
                # Stream the response while preserving paragraph formatting
                # Use character-based chunking instead of word-based to preserve newlines
                chunk_size = 100  # Send 100 characters at a time
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i+chunk_size]
                    yield json.dumps(chunk) + '\n'
                    time.sleep(0.05)  # Slightly faster streaming
                
                # Format documents for Related Documents tab
                related_docs = []
                
                if is_metadata_query:
                    # Import snippet_db at the top of generate function if not already imported
                    from ...core.storage.snippet_database import snippet_db
                    from datetime import datetime
                    
                    # Convert metadata results to document format and save as snippets
                    for i, result in enumerate(docs[:10]):  # Limit to 10 documents
                        # Generate a special RID for metadata results
                        meta_rid = f"META-{i:05d}"
                        
                        # Try to extract meaningful title
                        title = "Metadata Result"
                        if 'risk_id' in result:
                            title = f"Risk {result['risk_id']}"
                        elif 'domain' in result:
                            title = f"Domain: {result['domain']}"
                        elif 'category' in result:
                            title = f"Category: {result['category']}"
                        elif 'category_level' in result:
                            title = f"{result['category_level']}"
                        
                        # Add first non-null field value as subtitle
                        for key, value in result.items():
                            if value and key not in ['risk_id', 'domain', 'category', 'category_level']:
                                title += f" - {str(value)[:50]}"
                                break
                        
                        # Create snippet data for metadata result
                        snippet_data = {
                            "rid": meta_rid,
                            "title": title,
                            "content": json.dumps(result, indent=2),
                            "metadata": {
                                "type": "metadata_query_result",
                                "domain": result.get('domain', ''),
                                "category": result.get('category', ''),
                                "risk_id": result.get('risk_id', ''),
                                "source_file": "Metadata Query Result",
                            },
                            "highlights": [],
                            "created_at": datetime.now().isoformat()
                        }
                        
                        # Save to database
                        snippet_db.save_snippet(session_id, meta_rid, snippet_data)
                        
                        # Use RID-based URL
                        url = f"local-file://snippet/{meta_rid}"
                        related_docs.append({"title": title, "url": url})
                
                elif is_technical_query:
                    # Convert technical sources to document format
                    for source in docs:
                        related_docs.append({
                            "title": source.title,
                            "url": source.url
                        })
                
                elif docs and hasattr(docs[0], 'metadata'):
                    # Regular documents from vector store
                    for doc in docs:
                        rid = doc.metadata.get("rid")
                        if rid:
                            # Use RID-based URL that the frontend expects
                            url = f"local-file://snippet/{rid}"
                            title = doc.metadata.get("title", f"Document {rid}")
                        else:
                            # Fallback to original behavior
                            url = doc.metadata.get("url", "#")
                            if os.path.exists(url):
                                url = f"local-file://{url}"
                            title = doc.metadata.get("title", "Unknown Title")
                        
                        related_docs.append({
                            "title": title, 
                            "url": url
                        })
                
                # Send the related documents
                if related_docs:
                    yield json.dumps({"related_documents": related_docs}) + '\n'
                
                # Send language info if available
                if language_info:
                    yield json.dumps({"language": {
                        "code": language_info.get('code'),
                        "native_name": language_info.get('native_name'),
                        "english_name": language_info.get('english_name'),
                        "category": language_info.get('category', 'major')
                    }}) + '\n'
                
                # Calculate and log metrics after streaming completes
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Log metrics
                query_metrics = metrics_service.log_query(
                    session_id=session_id,
                    query=message,
                    response=response_text if 'response_text' in locals() else "",
                    latency_ms=latency_ms,
                    docs_retrieved=docs if 'docs' in locals() else [],
                    intent=query_type,
                    language=language_code or (language_info.get('code') if language_info else 'en'),
                    user_ip=user_ip,
                    user_agent=user_agent
                )
                
                # Send metrics as final message
                yield json.dumps({"metrics": {
                    "latency_ms": latency_ms,
                    "citations_count": query_metrics.citations_count,
                    "query_number": len(metrics_service.session_metrics.get(session_id, {}).get("queries", []))
                }}) + '\n'
                
            except Exception as e:
                logger.error(f"Error in streaming generator: {str(e)}")
                
                # Log error metrics
                latency_ms = int((time.time() - start_time) * 1000)
                metrics_service.log_query(
                    session_id=session_id,
                    query=message,
                    response="",
                    latency_ms=latency_ms,
                    error=e,
                    user_ip=user_ip,
                    user_agent=user_agent
                )
                
                yield json.dumps(f"An error occurred: {str(e)}") + '\n'
        
        # Set proper headers for SSE
        return Response(
            stream_with_context(generate()), 
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
                'Content-Type': 'text/event-stream'
            }
        )
        
    except Exception as e:
        logger.error(f"Error in stream_message: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@chat_bp.route('/api/v1/use_cases', methods=['POST'])
def get_use_cases():
    """Endpoint to generate use cases for a given domain."""
    try:
        data = request.json
        domain = data.get('domain', '')

        if not domain:
            return jsonify({"error": "Domain is required"}), 400

        use_cases = chat_service.generate_use_cases(domain)

        return jsonify({
            "use_cases": use_cases
        })

    except Exception as e:
        logger.error(f"Error in get_use_cases: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@chat_bp.route('/api/v1/reset', methods=['POST'])
def reset_conversation():
    """Reset conversation endpoint."""
    try:
        data = request.json or {}
        conversation_id = data.get('conversationId', 'default')
        
        # Reset the conversation
        chat_service.reset_conversation(conversation_id)
        
        return jsonify({
            "success": True, 
            "message": "Conversation reset successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in reset_conversation: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500