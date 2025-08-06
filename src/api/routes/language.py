"""
Language-related API routes.
"""
from flask import Blueprint, request, jsonify
from typing import Optional

from ...core.services.language_service import language_service
from ...config.logging import get_logger

logger = get_logger(__name__)

# Create blueprint
language_bp = Blueprint('language', __name__)

# This will be injected by the app factory
chat_service = None

def init_language_routes(chat_service_instance):
    """Initialize language routes with chat service dependency."""
    global chat_service
    chat_service = chat_service_instance

@language_bp.route('/api/detect-language', methods=['POST'])
def detect_language():
    """Detect language from text."""
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        # Detect language
        language_info = language_service.detect_language(text)
        
        return jsonify({
            "code": language_info['code'],
            "native_name": language_info['native_name'],
            "english_name": language_info['english_name'],
            "category": language_info.get('category', 'major'),
            "confidence": language_info.get('confidence', 0.9)
        })
        
    except Exception as e:
        logger.error(f"Error detecting language: {e}")
        return jsonify({"error": str(e)}), 500

@language_bp.route('/api/set-session-language', methods=['POST'])
def set_session_language():
    """Manually set language for a session."""
    try:
        data = request.json
        session_id = data.get('session_id')
        language_code = data.get('language_code')
        
        if not session_id or not language_code:
            return jsonify({"error": "session_id and language_code are required"}), 400
        
        if not chat_service:
            return jsonify({"error": "Chat service not initialized"}), 500
        
        # Set language
        success = chat_service.set_session_language(session_id, language_code)
        
        if success:
            language_info = language_service.get_language_info(language_code)
            return jsonify({
                "success": True,
                "language": {
                    "code": language_info['code'],
                    "native_name": language_info['native_name'],
                    "english_name": language_info['english_name'],
                    "category": language_info.get('category', 'major')
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "Invalid language code"
            }), 400
            
    except Exception as e:
        logger.error(f"Error setting session language: {e}")
        return jsonify({"error": str(e)}), 500

@language_bp.route('/api/session-language/<session_id>', methods=['GET'])
def get_session_language(session_id: str):
    """Get current language for a session."""
    try:
        if not chat_service:
            return jsonify({"error": "Chat service not initialized"}), 500
        
        language_info = chat_service.get_session_language(session_id)
        
        if language_info:
            return jsonify({
                "code": language_info['code'],
                "native_name": language_info['native_name'],
                "english_name": language_info['english_name'],
                "category": language_info.get('category', 'major')
            })
        else:
            # Default to English if no language set
            return jsonify({
                "code": "en",
                "native_name": "English",
                "english_name": "English",
                "category": "major"
            })
            
    except Exception as e:
        logger.error(f"Error getting session language: {e}")
        return jsonify({"error": str(e)}), 500

@language_bp.route('/api/supported-languages', methods=['GET'])
def get_supported_languages():
    """Get all supported languages."""
    try:
        # Optional filtering by category
        category = request.args.get('category')
        
        if category:
            languages = language_service.get_languages_by_category(category)
        else:
            languages = language_service.get_all_languages()
        
        # Format for frontend
        formatted_languages = [
            {
                "code": lang['code'],
                "native_name": lang['native_name'],
                "english_name": lang['english_name'],
                "category": lang.get('category', 'major'),
                "display_name": f"{lang['native_name']} ({lang['english_name']})" if lang['code'] != 'en' else lang['english_name']
            }
            for lang in languages
        ]
        
        return jsonify({"languages": formatted_languages})
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        return jsonify({"error": str(e)}), 500

@language_bp.route('/api/autocomplete-language', methods=['POST'])
def autocomplete_language():
    """Get autocomplete suggestions for language search."""
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', 10)
        
        # Get suggestions
        suggestions = language_service.autocomplete_languages(query, limit)
        
        # Format for frontend
        formatted_suggestions = [
            {
                "code": lang['code'],
                "native_name": lang['native_name'],
                "english_name": lang['english_name'],
                "category": lang.get('category', 'major'),
                "display_name": f"{lang['native_name']} ({lang['english_name']})" if lang['code'] != 'en' else lang['english_name']
            }
            for lang in suggestions
        ]
        
        return jsonify({"suggestions": formatted_suggestions})
        
    except Exception as e:
        logger.error(f"Error getting language suggestions: {e}")
        return jsonify({"error": str(e)}), 500

@language_bp.route('/api/validate-language', methods=['POST'])
def validate_language():
    """Validate and get info for a language input."""
    try:
        data = request.json
        user_input = data.get('input', '')
        
        if not user_input:
            return jsonify({"error": "Input is required"}), 400
        
        # Validate input
        language_info = language_service.validate_language_input(user_input)
        
        if language_info:
            return jsonify({
                "valid": True,
                "language": {
                    "code": language_info['code'],
                    "native_name": language_info['native_name'],
                    "english_name": language_info['english_name'],
                    "category": language_info.get('category', 'major'),
                    "display_name": f"{language_info['native_name']} ({language_info['english_name']})" if language_info['code'] != 'en' else language_info['english_name']
                }
            })
        else:
            # Try to get suggestions
            suggestions = language_service.autocomplete_languages(user_input, 3)
            return jsonify({
                "valid": False,
                "suggestions": [
                    {
                        "code": lang['code'],
                        "native_name": lang['native_name'],
                        "english_name": lang['english_name'],
                        "display_name": f"{lang['native_name']} ({lang['english_name']})" if lang['code'] != 'en' else lang['english_name']
                    }
                    for lang in suggestions
                ]
            })
            
    except Exception as e:
        logger.error(f"Error validating language: {e}")
        return jsonify({"error": str(e)}), 500