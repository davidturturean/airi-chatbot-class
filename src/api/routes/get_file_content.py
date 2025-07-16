"""
File content routes for the AIRI chatbot API.
"""
from flask import Blueprint, jsonify, request, send_file
import os
import mimetypes

from ...config.logging import get_logger

logger = get_logger(__name__)

# Create blueprint
file_content_bp = Blueprint('file_content', __name__)

@file_content_bp.route('/api/file-content', methods=['GET'])
def get_file_content():
    """Retrieve the content of a file."""
    file_path = request.args.get('path')
    if not file_path:
        return jsonify({"error": "File path is required"}), 400

    # Security check to prevent directory traversal
    base_dir = os.path.abspath(os.path.join(os.getcwd(), "data", "info_files"))
    requested_path = os.path.abspath(os.path.join(base_dir, file_path))

    if not requested_path.startswith(base_dir):
        return jsonify({"error": "Invalid file path"}), 400

    if not os.path.exists(requested_path):
        return jsonify({"error": "File not found"}), 404

    mimetype, _ = mimetypes.guess_type(requested_path)
    if mimetype:
        return send_file(requested_path, mimetype=mimetype)
    else:
        return send_file(requested_path)
