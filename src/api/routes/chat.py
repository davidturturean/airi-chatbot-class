"""
Chat routes for the AIRI chatbot API.
"""
import json
import time
import os
from flask import Blueprint, request, jsonify, Response, stream_with_context

from ...core.services.chat_service import ChatService
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
    """Non-streaming chat endpoint."""
    try:
        data = request.json
        
        # Log the incoming request
        logger.info(f"Received message: {data}")
        message = data.get('message', '')
        conversation_id = data.get('conversationId', 'default')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Process the query
        response_text, docs = chat_service.process_query(message, conversation_id)
        
        return jsonify({
            "id": conversation_id,
            "response": response_text,
            "status": "complete"
        })
        
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@chat_bp.route('/api/v1/stream', methods=['POST'])
def stream_message():
    """Streaming chat endpoint."""
    try:
        data = request.json
        
        # Log the incoming request
        logger.info(f"Received stream request: {data}")
        message = data.get('message', '')
        conversation_id = data.get('conversationId', 'default')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Define a streaming response generator
        def generate():
            try:
                # Initialize variables
                query_type = "general"
                domain = None
                docs = []
                
                # Initial status update with system info
                yield json.dumps("Processing your query...") + '\n'
                
                # Add system version info to logs
                from ...config.settings import settings
                logger.info(f"🔧 Processing with Field-Aware Hybrid: {settings.USE_FIELD_AWARE_HYBRID}")
                if chat_service.vector_store and hasattr(chat_service.vector_store, 'hybrid_retriever'):
                    if chat_service.vector_store.hybrid_retriever:
                        retriever_class = chat_service.vector_store.hybrid_retriever.__class__.__name__
                        logger.info(f"🎯 Using retriever: {retriever_class}")
                
                time.sleep(0.3)
                
                # 1. Process the query through chat service
                response_text, docs = chat_service.process_query(message, conversation_id)
                
                # Check what type of results we got
                is_metadata_query = isinstance(docs, list) and docs and isinstance(docs[0], dict)
                is_technical_query = hasattr(docs, '__iter__') and docs and hasattr(docs[0], 'title') and hasattr(docs[0], 'url')
                
                # Stream the response
                words = response_text.split()
                for i in range(0, len(words), 5):  # Send 5 words at a time
                    chunk = ' '.join(words[i:i+5]) + ' '
                    yield json.dumps(chunk) + '\n'
                    time.sleep(0.1)
                
                # Format documents for Related Documents tab
                related_docs = []
                
                if is_metadata_query:
                    # Convert metadata results to document format
                    for i, result in enumerate(docs[:10]):  # Limit to 10 documents
                        # Try to extract meaningful title and create reference
                        title = "Metadata Result"
                        if 'risk_id' in result:
                            title = f"Risk {result['risk_id']}"
                        elif 'domain' in result:
                            title = f"Domain: {result['domain']}"
                        elif 'category' in result:
                            title = f"Category: {result['category']}"
                        
                        # Create a pseudo-URL for metadata results
                        url = f"metadata://result/{i}"
                        
                        # Add first non-null field value as subtitle
                        for key, value in result.items():
                            if value and key not in ['risk_id', 'domain', 'category']:
                                title += f" - {str(value)[:50]}"
                                break
                        
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
                        url = doc.metadata.get("url", "#")
                        if os.path.exists(url):
                            url = f"local-file://{url}"
                        related_docs.append({
                            "title": doc.metadata.get("title", "Unknown Title"), 
                            "url": url
                        })
                
                # Send the related documents
                if related_docs:
                    yield json.dumps({"related_documents": related_docs}) + '\n'
                
            except Exception as e:
                logger.error(f"Error in streaming generator: {str(e)}")
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