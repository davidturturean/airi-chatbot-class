"""
Document snippet routes for the AIRI chatbot API with session support.
"""
from flask import Blueprint, jsonify, request, send_file, redirect, url_for, Response
import os
import json
from datetime import datetime

from ...core.storage.snippet_database import snippet_db
from ...config.logging import get_logger

logger = get_logger(__name__)

# Create blueprint
snippets_bp = Blueprint('snippets', __name__)

# This will be injected by the app factory
chat_service = None

def init_snippet_routes(chat_service_instance):
    """Initialize snippet routes with service dependency."""
    global chat_service
    chat_service = chat_service_instance

@snippets_bp.route('/api/snippet/<doc_id>', methods=['GET'])
def get_snippet(doc_id):
    """Retrieve a document snippet by its ID with session support."""
    try:
        # Get session ID from query parameter or header
        session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
        
        if not session_id:
            logger.warning("No session ID provided")
            return jsonify({"error": "Session ID required"}), 400
        
        if not chat_service or not chat_service.citation_service:
            return jsonify({"error": "Citation service not available"}), 503

        # Check if this is a file request
        if '.' in doc_id:
            return redirect(url_for('file_content.get_file_content', path=doc_id))

        # Check if this is a RID format (RID-#####) or META format (META-#####)
        if (doc_id.startswith('RID-') and len(doc_id) == 9) or (doc_id.startswith('META-') and len(doc_id) == 10):
            # First try to get from database
            snippet_data = snippet_db.get_snippet(session_id, doc_id)
            
            if snippet_data:
                logger.info(f"Retrieved snippet {doc_id} from database for session {session_id}")
                return jsonify(snippet_data)
            
            # For RID format, try legacy citation service
            if doc_id.startswith('RID-'):
                # If not in database, try to get from citation service (legacy)
                snippet = chat_service.citation_service.get_snippet_by_rid(doc_id, include_metadata=True)
                
                if snippet and "not found" not in str(snippet).lower():
                    # Convert legacy format to new JSON format and save
                    json_snippet = _convert_to_json_format(doc_id, snippet)
                    snippet_db.save_snippet(session_id, doc_id, json_snippet)
                    return jsonify(json_snippet)
        else:
            # Legacy format support
            snippet = chat_service.citation_service.get_snippet_content(doc_id, include_metadata=True)
            if snippet and "not found" not in str(snippet).lower():
                json_snippet = _convert_to_json_format(doc_id, snippet)
                return jsonify(json_snippet)

        return jsonify({"error": "Snippet not found"}), 404

    except Exception as e:
        logger.error(f"Error retrieving snippet {doc_id}: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@snippets_bp.route('/api/snippet/<rid>/raw', methods=['GET'])
def get_snippet_raw(rid):
    """Get raw snippet content for RID (plain text)."""
    try:
        session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
        
        if session_id:
            # Try database first
            snippet_data = snippet_db.get_snippet(session_id, rid)
            if snippet_data:
                return snippet_data.get('content', ''), 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
        if not chat_service or not chat_service.citation_service:
            return "Citation service not available", 503
            
        if not rid.startswith('RID-'):
            return "Invalid RID format", 400
            
        content = chat_service.citation_service.get_snippet_by_rid(rid)
        
        if "not found" in content.lower():
            return "Snippet not found", 404
        
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        logger.error(f"Error retrieving raw snippet {rid}: {str(e)}")
        return "Internal server error", 500

# New endpoints for session management
@snippets_bp.route('/api/session/new', methods=['POST'])
def create_session():
    """Create a new session ID."""
    session_id = snippet_db.generate_session_id()
    return jsonify({"session_id": session_id})

@snippets_bp.route('/api/session/<session_id>/clear', methods=['DELETE'])
def clear_session(session_id):
    """Clear all snippets for a session."""
    success = snippet_db.clear_session(session_id)
    if success:
        return jsonify({"message": "Session cleared successfully"})
    else:
        return jsonify({"error": "Failed to clear session"}), 500

@snippets_bp.route('/api/session/<session_id>/snippets', methods=['GET'])
def get_session_snippets(session_id):
    """Get all snippets for a session."""
    snippets = snippet_db.get_session_snippets(session_id)
    return jsonify({"snippets": snippets})

@snippets_bp.route('/api/cleanup', methods=['POST'])
def cleanup_old_sessions():
    """Clean up old sessions (admin endpoint)."""
    days = request.json.get('days', 1) if request.json else 1
    count = snippet_db.cleanup_old_sessions(days)
    return jsonify({"cleaned_up": count})

def _convert_to_json_format(rid: str, legacy_snippet: dict) -> dict:
    """Convert legacy snippet format to new JSON format."""
    # Handle both dict and string formats
    if isinstance(legacy_snippet, str):
        content = legacy_snippet
        metadata = {}
    else:
        content = legacy_snippet.get('content', '')
        metadata = legacy_snippet.get('metadata', {})
    
    # Parse content for title and other info if needed
    lines = content.split('\n') if content else []
    title = rid  # Default title
    
    # Try to extract title from content
    for line in lines:
        if line.startswith('Title:'):
            title = line.replace('Title:', '').strip()
            break
    
    return {
        "rid": rid,
        "title": title,
        "content": content,
        "metadata": {
            "domain": metadata.get('domain', ''),
            "subdomain": metadata.get('subdomain', ''),
            "risk_category": metadata.get('risk_category', ''),
            "entity": metadata.get('entity', ''),
            "intent": metadata.get('intent', ''),
            "timing": metadata.get('timing', ''),
            "description": metadata.get('description', ''),
            "source_file": metadata.get('url', metadata.get('source_file', '')),
            "row_number": metadata.get('row', None)
        },
        "highlights": metadata.get('search_terms', []),
        "created_at": datetime.now().isoformat()
    }