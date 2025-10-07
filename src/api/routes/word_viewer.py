"""
Word document viewer routes for the Interactive Reference Visualization system.
Converts .docx files to HTML using mammoth with formatting preservation.
Performance target: <500ms for typical Word documents
"""
from flask import Blueprint, jsonify, request
import mammoth
import bleach
from datetime import datetime
from pathlib import Path
import re
from ...core.storage.snippet_database import snippet_db
from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

# Create blueprint
word_viewer_bp = Blueprint('word_viewer', __name__)

# This will be injected by the app factory
chat_service = None

def init_word_routes(chat_service_instance):
    """Initialize Word viewer routes with service dependency."""
    global chat_service
    chat_service = chat_service_instance

@word_viewer_bp.route('/api/document/<rid>/word', methods=['GET'])
def get_word_data(rid):
    """
    Convert Word document to HTML and return with metadata.
    Performance target: <500ms
    """
    try:
        start_time = datetime.now()

        # Get session ID
        session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400

        # Get document metadata
        snippet_data = snippet_db.get_snippet(session_id, rid)
        if not snippet_data:
            return jsonify({"error": "Document not found"}), 404

        # Get file path from metadata
        source_file = snippet_data.get('metadata', {}).get('source_file', '')
        if not source_file:
            return jsonify({"error": "No source file specified"}), 404

        # Resolve file path
        file_path = _resolve_file_path(source_file)
        if not file_path or not file_path.exists():
            return jsonify({"error": f"File not found: {source_file}"}), 404

        # Convert Word to HTML
        word_data = _convert_word_to_html(file_path)

        # Add metadata
        word_data['rid'] = rid
        word_data['title'] = snippet_data.get('title', file_path.stem)
        word_data['metadata'] = snippet_data.get('metadata', {})

        # Calculate performance
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        if duration_ms > 500:
            logger.warning(f"Word conversion exceeded target: {duration_ms:.2f}ms for {rid}")

        return jsonify(word_data)

    except Exception as e:
        logger.error(f"Error converting Word document for {rid}: {str(e)}")
        return jsonify({"error": f"Failed to convert Word document: {str(e)}"}), 500

def _resolve_file_path(source_file: str) -> Path:
    """Resolve file path from source file reference."""
    # Try direct path
    file_path = Path(source_file)
    if file_path.exists():
        return file_path

    # Try relative to repository
    repo_path = settings.get_repository_path()
    if repo_path:
        file_path = Path(repo_path) / source_file
        if file_path.exists():
            return file_path

    # Try relative to data directory
    data_dir = settings.DATA_DIR
    if data_dir:
        file_path = data_dir / source_file
        if file_path.exists():
            return file_path

    return None

def _convert_word_to_html(file_path: Path):
    """
    Convert Word document to HTML using mammoth.
    Includes table of contents extraction and sanitization.
    """
    try:
        # Convert to HTML
        with open(str(file_path), 'rb') as docx_file:
            result = mammoth.convert_to_html(
                docx_file,
                convert_image=mammoth.images.inline(lambda image: {
                    'src': f'data:{image.content_type};base64,{image.data.decode("ascii")}'
                })
            )

        html_content = result.value
        messages = result.messages  # Conversion warnings/errors

        # Log any conversion issues
        for message in messages:
            if message.type == 'warning':
                logger.warning(f"Mammoth warning: {message.message}")
            elif message.type == 'error':
                logger.error(f"Mammoth error: {message.message}")

        # Sanitize HTML
        sanitized_html = _sanitize_html(html_content)

        # Add IDs to headings for TOC navigation
        sanitized_html, toc = _add_heading_ids_and_extract_toc(sanitized_html)

        # Estimate word and page count
        text_content = re.sub(r'<[^>]+>', '', html_content)
        word_count = len(text_content.split())
        page_count = max(1, word_count // 250)  # Approximate 250 words per page

        return {
            'html_content': sanitized_html,
            'toc': toc,
            'word_count': word_count,
            'page_count': page_count
        }

    except Exception as e:
        logger.error(f"Error in Word conversion: {str(e)}")
        raise

def _sanitize_html(html: str) -> str:
    """
    Sanitize HTML to prevent XSS while preserving document formatting.
    """
    return bleach.clean(
        html,
        tags=[
            'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li',
            'strong', 'b', 'em', 'i', 'u', 's',
            'a', 'br', 'hr',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'img', 'span', 'div',
            'blockquote', 'pre', 'code'
        ],
        attributes={
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title'],
            'table': ['class'],
            'td': ['colspan', 'rowspan'],
            'th': ['colspan', 'rowspan'],
            '*': ['id', 'class']
        },
        strip=True
    )

def _add_heading_ids_and_extract_toc(html: str):
    """
    Add IDs to headings and extract table of contents.
    Returns: (modified_html, toc_structure)
    """
    toc = []
    heading_counter = {}

    def replace_heading(match):
        level = int(match.group(1))
        text = match.group(2)

        # Generate unique ID
        base_id = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
        if base_id in heading_counter:
            heading_counter[base_id] += 1
            heading_id = f"{base_id}-{heading_counter[base_id]}"
        else:
            heading_counter[base_id] = 0
            heading_id = base_id

        # Add to TOC
        toc.append({
            'id': heading_id,
            'title': text,
            'level': level
        })

        return f'<h{level} id="{heading_id}">{text}</h{level}>'

    # Replace headings with IDs
    modified_html = re.sub(
        r'<h([1-6])>(.*?)</h[1-6]>',
        replace_heading,
        html
    )

    # Build hierarchical TOC structure
    hierarchical_toc = _build_toc_hierarchy(toc)

    return modified_html, hierarchical_toc

def _build_toc_hierarchy(flat_toc):
    """
    Convert flat TOC list to hierarchical structure.
    """
    if not flat_toc:
        return []

    hierarchical = []
    stack = []

    for item in flat_toc:
        # Create a copy of the item
        toc_item = {
            'id': item['id'],
            'title': item['title'],
            'level': item['level'],
            'children': []
        }

        # Find correct parent level
        while stack and stack[-1]['level'] >= item['level']:
            stack.pop()

        if not stack:
            # Top level item
            hierarchical.append(toc_item)
        else:
            # Nested item
            stack[-1]['children'].append(toc_item)

        stack.append(toc_item)

    # Remove empty children arrays
    def clean_empty_children(items):
        for item in items:
            if not item['children']:
                del item['children']
            else:
                clean_empty_children(item['children'])

    clean_empty_children(hierarchical)

    return hierarchical
