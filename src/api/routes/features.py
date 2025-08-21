"""
API routes for feature flag management.
"""
from flask import Blueprint, jsonify, request
from typing import Dict, Any

from ...config.feature_flags import feature_flags
from ...config.logging import get_logger

logger = get_logger(__name__)

# Create blueprint
features_bp = Blueprint('features', __name__, url_prefix='/api')


@features_bp.route('/features', methods=['GET'])
def get_features():
    """
    Get current feature flag values.
    
    Returns:
        JSON response with all feature flags
    """
    try:
        flags = feature_flags.get_all()
        return jsonify({
            "success": True,
            "features": flags,
            "isSidebarEnabled": feature_flags.is_sidebar_enabled()
        })
    except Exception as e:
        logger.error(f"Error getting feature flags: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@features_bp.route('/features', methods=['POST'])
def update_features():
    """
    Update feature flag values.
    
    Request body:
        {
            "features": {
                "FEATURE_NAME": value,
                ...
            }
        }
    
    Returns:
        JSON response with update results
    """
    try:
        data = request.get_json()
        
        if not data or 'features' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'features' in request body"
            }), 400
        
        updates = data['features']
        results = feature_flags.update_multiple(updates)
        
        # Check if all updates succeeded
        all_success = all(results.values())
        
        return jsonify({
            "success": all_success,
            "results": results,
            "features": feature_flags.get_all(),
            "isSidebarEnabled": feature_flags.is_sidebar_enabled()
        })
        
    except Exception as e:
        logger.error(f"Error updating feature flags: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@features_bp.route('/features/config', methods=['GET'])
def get_feature_config():
    """
    Get feature configuration with metadata for UI.
    
    Returns:
        JSON response with feature configuration and metadata
    """
    try:
        config = feature_flags.get_frontend_config()
        return jsonify({
            "success": True,
            "config": config,
            "isSidebarEnabled": feature_flags.is_sidebar_enabled()
        })
    except Exception as e:
        logger.error(f"Error getting feature config: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@features_bp.route('/features/reset', methods=['POST'])
def reset_features():
    """
    Reset all feature flags to default values.
    
    Returns:
        JSON response with reset confirmation
    """
    try:
        feature_flags.reset_to_defaults()
        return jsonify({
            "success": True,
            "message": "Feature flags reset to defaults",
            "features": feature_flags.get_all()
        })
    except Exception as e:
        logger.error(f"Error resetting feature flags: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@features_bp.route('/features/<flag_name>', methods=['GET'])
def get_feature(flag_name: str):
    """
    Get a specific feature flag value.
    
    Args:
        flag_name: Name of the feature flag
    
    Returns:
        JSON response with feature flag value
    """
    try:
        value = feature_flags.get(flag_name)
        
        if value is None:
            return jsonify({
                "success": False,
                "error": f"Unknown feature flag: {flag_name}"
            }), 404
        
        return jsonify({
            "success": True,
            "flag": flag_name,
            "value": value
        })
    except Exception as e:
        logger.error(f"Error getting feature flag {flag_name}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@features_bp.route('/features/<flag_name>', methods=['POST'])
def update_feature(flag_name: str):
    """
    Update a specific feature flag value.
    
    Args:
        flag_name: Name of the feature flag
    
    Request body:
        {
            "value": new_value
        }
    
    Returns:
        JSON response with update result
    """
    try:
        data = request.get_json()
        
        if not data or 'value' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'value' in request body"
            }), 400
        
        success = feature_flags.set(flag_name, data['value'])
        
        if not success:
            return jsonify({
                "success": False,
                "error": f"Unknown feature flag: {flag_name}"
            }), 404
        
        return jsonify({
            "success": True,
            "flag": flag_name,
            "value": data['value'],
            "isSidebarEnabled": feature_flags.is_sidebar_enabled()
        })
        
    except Exception as e:
        logger.error(f"Error updating feature flag {flag_name}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def init_features_routes():
    """
    Initialize feature routes.
    Called during app initialization.
    """
    logger.info("Feature flag routes initialized")