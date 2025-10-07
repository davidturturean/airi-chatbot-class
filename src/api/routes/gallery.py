"""
Citation gallery routes for the Interactive Reference Visualization system.
Provides gallery view of all citations in a session.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from ...core.storage.snippet_database import snippet_db
from ...config.logging import get_logger

logger = get_logger(__name__)

# Create blueprint
gallery_bp = Blueprint('gallery', __name__)

@gallery_bp.route('/api/session/<session_id>/gallery', methods=['GET'])
def get_session_gallery(session_id):
    """
    Get all citations in a session formatted for gallery view.
    """
    try:
        # Get all snippets for session
        snippets = snippet_db.get_session_snippets(session_id)

        # Convert to gallery items
        gallery_items = []
        for snippet in snippets:
            metadata = snippet.get('metadata', {})

            gallery_items.append({
                'rid': snippet.get('rid', ''),
                'title': snippet.get('title', 'Untitled'),
                'preview_type': _determine_preview_type(metadata, snippet.get('content', '')),
                'thumbnail': None,  # TODO: Generate thumbnails
                'metadata': metadata,
                'relevance_score': None,
                'created_at': snippet.get('created_at', datetime.now().isoformat())
            })

        # Sort by created_at (most recent first)
        gallery_items.sort(key=lambda x: x['created_at'], reverse=True)

        # Extract filter options
        domains = list(set(item['metadata'].get('domain', '') for item in gallery_items if item['metadata'].get('domain')))
        file_types = list(set(item['preview_type'] for item in gallery_items))
        entities = list(set(item['metadata'].get('entity', '') for item in gallery_items if item['metadata'].get('entity')))
        risk_categories = list(set(item['metadata'].get('risk_category', '') for item in gallery_items if item['metadata'].get('risk_category')))

        return jsonify({
            'items': gallery_items,
            'total_count': len(gallery_items),
            'filters': {
                'domains': sorted(domains),
                'file_types': sorted(file_types),
                'entities': sorted(entities),
                'risk_categories': sorted(risk_categories)
            }
        })

    except Exception as e:
        logger.error(f"Error getting gallery for session {session_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

def _determine_preview_type(metadata, content):
    """Determine the preview type based on metadata and content."""
    import os

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
        return 'excel'

    # Default to text
    return 'text'
