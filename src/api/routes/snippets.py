"""
Document snippet routes for the AIRI chatbot API.
"""
from flask import Blueprint, jsonify, request, send_file, redirect, url_for
import os

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
    """Retrieve a document snippet by its ID and redirect to the file content route."""
    try:
        # Redirect to the file-content endpoint, assuming doc_id is the filename
        return redirect(url_for('snippets.get_file_content', path=doc_id))
    except Exception as e:
        logger.error(f"Error redirecting to file content for {doc_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@snippets_bp.route('/api/snippet/<rid>/raw', methods=['GET'])
def get_snippet_raw(rid):
    """Get raw snippet content for RID (plain text)."""
    try:
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

@snippets_bp.route('/api/file-content', methods=['GET'])
def get_file_content():
    """Retrieve the content of a file from the info_files directory."""
    filename = request.args.get('path')
    if not filename:
        return jsonify({"error": "Filename is required"}), 400

    # Securely join path components
    info_files_dir = os.path.abspath(os.path.join(os.getcwd(), 'data', 'info_files'))
    file_path = os.path.join(info_files_dir, filename)

    # Security check to prevent directory traversal
    if not os.path.abspath(file_path).startswith(info_files_dir):
        return jsonify({"error": "Invalid file path"}), 400

    if not os.path.exists(file_path):
        return jsonify({"error": f"File not found at {file_path}"}), 404

    return send_file(file_path)