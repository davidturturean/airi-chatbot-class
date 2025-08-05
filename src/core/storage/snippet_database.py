"""
Database management for JSON snippet storage with session support.
"""
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid

from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

class SnippetDatabase:
    """Manages snippet storage in SQLite database with session support."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the database connection."""
        self.db_path = db_path or settings.DATA_DIR / "snippets.db"
        self._init_database()
    
    def _init_database(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snippet_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    rid TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(session_id, rid)
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON snippet_sessions(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON snippet_sessions(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rid ON snippet_sessions(rid)")
            
            # Table for session management
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info(f"Snippet database initialized at {self.db_path}")
    
    def save_snippet(self, session_id: str, rid: str, snippet_data: Dict[str, Any]) -> bool:
        """
        Save a snippet for a specific session.
        
        Args:
            session_id: User session identifier
            rid: Repository ID (e.g., "RID-00073")
            snippet_data: Dictionary containing snippet information
            
        Returns:
            True if saved successfully
        """
        try:
            # Ensure session exists
            self._ensure_session(session_id)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO snippet_sessions (session_id, rid, data, accessed_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (session_id, rid, json.dumps(snippet_data)))
                
                conn.commit()
                logger.info(f"Saved snippet {rid} for session {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving snippet {rid}: {str(e)}")
            return False
    
    def get_snippet(self, session_id: str, rid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a snippet for a specific session.
        
        Args:
            session_id: User session identifier
            rid: Repository ID
            
        Returns:
            Snippet data or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT data FROM snippet_sessions 
                    WHERE session_id = ? AND rid = ?
                """, (session_id, rid))
                
                row = cursor.fetchone()
                if row:
                    # Update access time
                    conn.execute("""
                        UPDATE snippet_sessions 
                        SET accessed_at = CURRENT_TIMESTAMP 
                        WHERE session_id = ? AND rid = ?
                    """, (session_id, rid))
                    
                    # Update session activity
                    self._update_session_activity(session_id)
                    
                    return json.loads(row['data'])
                    
        except Exception as e:
            logger.error(f"Error retrieving snippet {rid}: {str(e)}")
            
        return None
    
    def get_session_snippets(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all snippets for a session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT rid, data, created_at, accessed_at 
                    FROM snippet_sessions 
                    WHERE session_id = ?
                    ORDER BY accessed_at DESC
                """, (session_id,))
                
                snippets = []
                for row in cursor:
                    snippet = json.loads(row['data'])
                    snippet['_metadata'] = {
                        'created_at': row['created_at'],
                        'accessed_at': row['accessed_at']
                    }
                    snippets.append(snippet)
                
                return snippets
                
        except Exception as e:
            logger.error(f"Error getting session snippets: {str(e)}")
            return []
    
    def clear_session(self, session_id: str) -> bool:
        """Clear all snippets for a session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM snippet_sessions WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM user_sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                logger.info(f"Cleared all snippets for session {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing session: {str(e)}")
            return False
    
    def cleanup_old_sessions(self, days: int = 1) -> int:
        """
        Clean up sessions older than specified days.
        
        Args:
            days: Number of days to keep sessions
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                # Get sessions to delete
                cursor = conn.execute("""
                    SELECT session_id FROM user_sessions 
                    WHERE last_activity < ?
                """, (cutoff_date,))
                
                old_sessions = [row[0] for row in cursor]
                
                if old_sessions:
                    # Delete snippets for old sessions
                    placeholders = ','.join('?' * len(old_sessions))
                    conn.execute(f"""
                        DELETE FROM snippet_sessions 
                        WHERE session_id IN ({placeholders})
                    """, old_sessions)
                    
                    # Delete the sessions
                    conn.execute(f"""
                        DELETE FROM user_sessions 
                        WHERE session_id IN ({placeholders})
                    """, old_sessions)
                    
                    conn.commit()
                    
                logger.info(f"Cleaned up {len(old_sessions)} old sessions")
                return len(old_sessions)
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {str(e)}")
            return 0
    
    def _ensure_session(self, session_id: str):
        """Ensure a session exists in the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO user_sessions (session_id)
                VALUES (?)
            """, (session_id,))
            conn.commit()
    
    def _update_session_activity(self, session_id: str):
        """Update the last activity timestamp for a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE user_sessions 
                SET last_activity = CURRENT_TIMESTAMP 
                WHERE session_id = ?
            """, (session_id,))
            conn.commit()
    
    def generate_session_id(self) -> str:
        """Generate a new unique session ID."""
        return str(uuid.uuid4())

# Global instance
snippet_db = SnippetDatabase()