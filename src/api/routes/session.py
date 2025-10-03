"""
Session management routes for conversation persistence across widget and full page.
Enables seamless conversation transfer between different chatbot interfaces.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Optional
import json
from src.core.storage.snippet_database import snippet_db

session_bp = Blueprint('session', __name__)

# In-memory session storage (replace with Redis/database in production)
# Structure: {session_id: {"messages": [...], "created_at": datetime, "last_accessed": datetime}}
session_store: Dict[str, dict] = {}

# Configuration
SESSION_EXPIRY_HOURS = 24
MAX_SESSIONS = 1000
MAX_MESSAGES_PER_SESSION = 100


def cleanup_old_sessions():
    """Remove expired sessions from memory."""
    current_time = datetime.now()
    expired_sessions = []
    
    for session_id, session_data in session_store.items():
        if current_time - session_data['last_accessed'] > timedelta(hours=SESSION_EXPIRY_HOURS):
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del session_store[session_id]
    
    # Also cleanup if too many sessions
    if len(session_store) > MAX_SESSIONS:
        # Remove oldest sessions
        sorted_sessions = sorted(
            session_store.items(),
            key=lambda x: x[1]['last_accessed']
        )
        for session_id, _ in sorted_sessions[:len(session_store) - MAX_SESSIONS]:
            del session_store[session_id]


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return f"session_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"


@session_bp.route('/api/session/create', methods=['POST'])
def create_session():
    """
    Create a new session for conversation tracking.
    Returns a unique session ID that can be used across widget and full page.
    """
    try:
        session_id = generate_session_id()
        
        # Initialize session
        session_store[session_id] = {
            'messages': [],
            'created_at': datetime.now(),
            'last_accessed': datetime.now(),
            'metadata': request.json.get('metadata', {}) if request.json else {}
        }
        
        # Cleanup old sessions periodically
        if len(session_store) % 10 == 0:
            cleanup_old_sessions()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'expires_in_hours': SESSION_EXPIRY_HOURS
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@session_bp.route('/api/session/<session_id>/messages', methods=['GET'])
def get_session_messages(session_id: str):
    """
    Retrieve all messages for a given session.
    Used when transitioning from widget to full page.
    """
    try:
        if session_id not in session_store:
            return jsonify({
                'success': False,
                'error': 'Session not found or expired'
            }), 404
        
        # Update last accessed time
        session_store[session_id]['last_accessed'] = datetime.now()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'messages': session_store[session_id]['messages'],
            'created_at': session_store[session_id]['created_at'].isoformat(),
            'message_count': len(session_store[session_id]['messages'])
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@session_bp.route('/api/session/<session_id>/messages', methods=['POST'])
def add_session_message(session_id: str):
    """
    Add a new message to the session.
    Called whenever a user sends a query or receives a response.
    """
    try:
        if session_id not in session_store:
            # Auto-create session if it doesn't exist
            session_store[session_id] = {
                'messages': [],
                'created_at': datetime.now(),
                'last_accessed': datetime.now(),
                'metadata': {}
            }
        
        data = request.json
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message content required'
            }), 400
        
        # Create message object
        message = {
            'id': str(uuid.uuid4().hex[:8]),
            'content': data['message'],
            'role': data.get('role', 'user'),  # 'user' or 'assistant'
            'timestamp': datetime.now().isoformat(),
            'metadata': data.get('metadata', {})
        }
        
        # Add to session
        session_store[session_id]['messages'].append(message)
        session_store[session_id]['last_accessed'] = datetime.now()
        
        # Limit messages per session
        if len(session_store[session_id]['messages']) > MAX_MESSAGES_PER_SESSION:
            session_store[session_id]['messages'] = \
                session_store[session_id]['messages'][-MAX_MESSAGES_PER_SESSION:]
        
        return jsonify({
            'success': True,
            'message_id': message['id'],
            'session_id': session_id,
            'total_messages': len(session_store[session_id]['messages'])
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@session_bp.route('/api/session/<session_id>/clear', methods=['DELETE'])
def clear_session(session_id: str):
    """
    Delete the current session and create a new one.
    Also clears associated snippets.
    Returns a new session ID for the frontend to use.
    """
    try:
        # Clear snippets for this session
        snippet_db.clear_session(session_id)
        print(f"Cleared snippets for session: {session_id}")

        # Delete old session entirely (not just clear messages)
        if session_id in session_store:
            del session_store[session_id]
            print(f"Deleted session: {session_id}")

        # Generate a new session ID
        new_session_id = generate_session_id()

        # Create new empty session
        session_store[new_session_id] = {
            'messages': [],
            'created_at': datetime.now(),
            'last_accessed': datetime.now(),
            'metadata': {
                'cleared_from': session_id,
                'timestamp': datetime.now().isoformat()
            }
        }

        print(f"Created new session: {new_session_id}")

        return jsonify({
            'success': True,
            'old_session_id': session_id,
            'new_session_id': new_session_id,
            'message': 'Session deleted and new session created'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@session_bp.route('/api/session/<session_id>/exists', methods=['GET'])
def check_session_exists(session_id: str):
    """
    Check if a session exists and is valid.
    """
    exists = session_id in session_store
    
    if exists:
        session_store[session_id]['last_accessed'] = datetime.now()
    
    return jsonify({
        'success': True,
        'exists': exists,
        'session_id': session_id if exists else None
    }), 200


@session_bp.route('/api/session/cleanup', methods=['POST'])
def trigger_cleanup():
    """
    Manually trigger cleanup of old sessions.
    Should be called periodically or by admin.
    """
    try:
        before_count = len(session_store)
        cleanup_old_sessions()
        after_count = len(session_store)
        
        return jsonify({
            'success': True,
            'sessions_removed': before_count - after_count,
            'active_sessions': after_count
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Optional: WebSocket support for real-time sync
# This would require additional setup with Flask-SocketIO
"""
from flask_socketio import emit, join_room, leave_room

@socketio.on('join_session')
def handle_join_session(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        emit('joined', {'session_id': session_id}, room=session_id)

@socketio.on('new_message')
def handle_new_message(data):
    session_id = data.get('session_id')
    if session_id:
        # Broadcast to all clients in this session
        emit('message_added', data, room=session_id, broadcast=True)
"""