"""
Document preview routes for the Interactive Reference Visualization system.
Provides lightweight preview data for hover cards and panels.
Performance target: <200ms response time
"""
from flask import Blueprint, jsonify, request
import os
from datetime import datetime
from ...core.storage.snippet_database import snippet_db
from ...config.logging import get_logger

logger = get_logger(__name__)

# Create blueprint
document_preview_bp = Blueprint('document_preview', __name__)

# This will be injected by the app factory
chat_service = None

def init_preview_routes(chat_service_instance):
    """Initialize document preview routes with service dependency."""
    global chat_service
    chat_service = chat_service_instance

@document_preview_bp.route('/api/document/<rid>/preview', methods=['GET'])
def get_document_preview(rid):
    """
    Get lightweight preview data for a document.
    Returns: JSON with preview data optimized for hover cards.
    Performance target: <200ms
    """
    try:
        start_time = datetime.now()

        # Get session ID from query parameter or header
        session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')

        if not session_id:
            logger.warning("No session ID provided for preview")
            return jsonify({"error": "Session ID required"}), 400

        if not chat_service or not chat_service.citation_service:
            return jsonify({"error": "Citation service not available"}), 503

        # Check database first for cached snippet
        snippet_data = snippet_db.get_snippet(session_id, rid)

        if snippet_data:
            preview_data = _convert_snippet_to_preview(snippet_data)

            # Calculate performance
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            if duration_ms > 200:
                logger.warning(f"Preview load exceeded target: {duration_ms:.2f}ms for {rid}")

            return jsonify(preview_data)

        # Fallback to citation service for RID format
        if rid.startswith('RID-') and len(rid) == 9:
            snippet = chat_service.citation_service.get_snippet_by_rid(rid, include_metadata=True)

            if snippet and "not found" not in str(snippet).lower():
                # Convert to preview format
                preview_data = _create_preview_from_snippet(rid, snippet)

                # Save to database for future requests
                snippet_db.save_snippet(session_id, rid, preview_data)

                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                if duration_ms > 200:
                    logger.warning(f"Preview load exceeded target: {duration_ms:.2f}ms for {rid}")

                return jsonify(preview_data)

        return jsonify({"error": "Document not found"}), 404

    except Exception as e:
        logger.error(f"Error getting preview for {rid}: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@document_preview_bp.route('/api/document/<rid>/type', methods=['GET'])
def get_document_type(rid):
    """
    Quickly determine document type without loading full content.
    Used for optimizing preview rendering.
    """
    try:
        session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')

        if not session_id:
            return jsonify({"error": "Session ID required"}), 400

        # Check database
        snippet_data = snippet_db.get_snippet(session_id, rid)

        if snippet_data:
            doc_type = _determine_document_type(snippet_data)
            return jsonify({
                "rid": rid,
                "type": doc_type,
                "file_type": snippet_data.get('metadata', {}).get('file_type', 'text')
            })

        # Default to text if not found
        return jsonify({
            "rid": rid,
            "type": "text",
            "file_type": "text"
        })

    except Exception as e:
        logger.error(f"Error getting document type for {rid}: {str(e)}")
        return jsonify({"error": str(e)}), 500

def _convert_snippet_to_preview(snippet_data):
    """Convert snippet database format to preview format."""
    metadata = snippet_data.get('metadata', {})

    # Determine preview type from file type or content
    preview_type = _determine_preview_type(metadata, snippet_data.get('content', ''))

    preview = {
        "rid": snippet_data.get('rid', ''),
        "title": snippet_data.get('title', 'Untitled'),
        "content": snippet_data.get('content', ''),
        "metadata": metadata,
        "highlights": snippet_data.get('highlights', []),
        "created_at": snippet_data.get('created_at', datetime.now().isoformat()),
        "preview_type": preview_type,
        "thumbnail": None  # TODO: Generate thumbnails for images/PDFs
    }

    # Add source_location if available (for Excel files)
    if 'source_location' in snippet_data:
        preview['source_location'] = snippet_data['source_location']

    return preview

def _create_preview_from_snippet(rid, snippet):
    """Create preview data from citation service snippet."""
    # Handle both dict and string formats
    if isinstance(snippet, str):
        content = snippet
        metadata = {}
    else:
        content = snippet.get('content', '')
        metadata = snippet.get('metadata', {})

    # Parse content for title
    lines = content.split('\n') if content else []
    title = rid  # Default title

    for line in lines:
        if line.startswith('Title:'):
            title = line.replace('Title:', '').strip()
            break

    preview_type = _determine_preview_type(metadata, content)

    return {
        "rid": rid,
        "title": title,
        "content": content[:1000],  # Truncate for preview
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
        "created_at": datetime.now().isoformat(),
        "preview_type": preview_type,
        "thumbnail": None
    }

def _determine_preview_type(metadata, content):
    """Determine the preview type based on metadata and content."""
    # Check file extension from source_file
    source_file = metadata.get('source_file', metadata.get('url', ''))

    if source_file:
        ext = os.path.splitext(source_file)[1].lower()

        if ext in ['.xlsx', '.xls', '.csv']:
            return 'excel'
        elif ext in ['.docx', '.doc']:
            return 'word'
        elif ext in ['.pdf']:
            return 'pdf'
        elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
            return 'image'

    # Check metadata type
    if metadata.get('type') == 'metadata_query_result':
        return 'excel'  # Metadata results are typically tabular

    # Default to text
    return 'text'

def _determine_document_type(snippet_data):
    """Determine document type from snippet data."""
    metadata = snippet_data.get('metadata', {})
    content = snippet_data.get('content', '')

    return _determine_preview_type(metadata, content)
