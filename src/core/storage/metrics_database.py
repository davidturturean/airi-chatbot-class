"""
SQLite database for persistent metrics storage.
Stores all metrics, sessions, and gate history for the AIRI chatbot.
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import hashlib
from contextlib import contextmanager

@dataclass
class QueryMetric:
    """Individual query metric record."""
    session_id: str
    timestamp: str
    query: str
    response: str
    latency_ms: int
    tokens_used: int
    cost_estimate: float
    citations_count: int
    groundedness_score: float
    language: str
    intent: str
    user_hash: str
    error_type: Optional[str] = None
    feedback: Optional[str] = None

class MetricsDatabase:
    """Persistent storage for metrics using SQLite."""
    
    def __init__(self, db_path: str = "data/metrics.db"):
        """Initialize the metrics database."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Metrics table for individual queries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    tokens_used INTEGER NOT NULL,
                    cost_estimate REAL NOT NULL,
                    citations_count INTEGER NOT NULL,
                    groundedness_score REAL NOT NULL,
                    language TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    user_hash TEXT NOT NULL,
                    error_type TEXT,
                    feedback TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sessions table for user sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    total_queries INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0,
                    avg_latency_ms INTEGER DEFAULT 0,
                    user_hash TEXT NOT NULL,
                    language TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Feedback table for user feedback
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    query_id INTEGER,
                    feedback_type TEXT NOT NULL,
                    feedback_text TEXT,
                    found_answer TEXT,
                    would_recommend INTEGER,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES metrics(id)
                )
            """)
            
            # Gates history table for tracking deployment gates over time
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gates_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    gate_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    threshold REAL NOT NULL,
                    passing INTEGER NOT NULL,
                    period_hours INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Aggregated metrics table for performance
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aggregated_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    period_type TEXT NOT NULL,
                    total_queries INTEGER NOT NULL,
                    unique_sessions INTEGER NOT NULL,
                    avg_latency_ms INTEGER NOT NULL,
                    p95_latency_ms INTEGER NOT NULL,
                    total_cost REAL NOT NULL,
                    avg_groundedness REAL NOT NULL,
                    error_rate REAL NOT NULL,
                    satisfaction_rate REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_session ON metrics(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_session ON sessions(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_session ON feedback(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_gates_timestamp ON gates_history(timestamp)")
    
    def log_metric(self, metric: QueryMetric) -> int:
        """Log a single query metric to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO metrics (
                    session_id, timestamp, query, response, latency_ms,
                    tokens_used, cost_estimate, citations_count, groundedness_score,
                    language, intent, user_hash, error_type, feedback
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.session_id, metric.timestamp, metric.query, metric.response,
                metric.latency_ms, metric.tokens_used, metric.cost_estimate,
                metric.citations_count, metric.groundedness_score, metric.language,
                metric.intent, metric.user_hash, metric.error_type, metric.feedback
            ))
            return cursor.lastrowid
    
    def update_session(self, session_id: str, user_hash: str, language: str = 'en'):
        """Create or update a session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if session exists
            cursor.execute("SELECT id FROM sessions WHERE session_id = ?", (session_id,))
            exists = cursor.fetchone()
            
            if not exists:
                # Create new session
                cursor.execute("""
                    INSERT INTO sessions (session_id, started_at, user_hash, language)
                    VALUES (?, ?, ?, ?)
                """, (session_id, datetime.now().isoformat(), user_hash, language))
            else:
                # Update existing session stats
                cursor.execute("""
                    UPDATE sessions 
                    SET total_queries = (
                        SELECT COUNT(*) FROM metrics WHERE session_id = ?
                    ),
                    total_cost = (
                        SELECT COALESCE(SUM(cost_estimate), 0) FROM metrics WHERE session_id = ?
                    ),
                    avg_latency_ms = (
                        SELECT COALESCE(AVG(latency_ms), 0) FROM metrics WHERE session_id = ?
                    )
                    WHERE session_id = ?
                """, (session_id, session_id, session_id, session_id))
    
    def log_feedback(self, session_id: str, feedback_type: str, 
                     query_id: Optional[int] = None, feedback_text: Optional[str] = None,
                     found_answer: Optional[str] = None, would_recommend: Optional[int] = None):
        """Log user feedback."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedback (
                    session_id, query_id, feedback_type, feedback_text,
                    found_answer, would_recommend, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, query_id, feedback_type, feedback_text,
                found_answer, would_recommend, datetime.now().isoformat()
            ))
    
    def log_gate_status(self, gate_name: str, value: float, threshold: float, 
                       passing: bool, period_hours: int = 24):
        """Log deployment gate status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO gates_history (
                    timestamp, gate_name, value, threshold, passing, period_hours
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(), gate_name, value, threshold,
                1 if passing else 0, period_hours
            ))
    
    def get_recent_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get all metrics from the last N hours - REAL DATA ONLY."""
        return self.get_metrics_for_period(hours)
    
    def get_session_metrics(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all metrics for a specific session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM metrics 
                WHERE session_id = ?
                ORDER BY timestamp DESC
            """, (session_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_summary_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary statistics for the last N hours."""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_queries,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    AVG(latency_ms) as avg_latency_ms,
                    MIN(latency_ms) as min_latency_ms,
                    MAX(latency_ms) as max_latency_ms,
                    AVG(groundedness_score) as avg_groundedness,
                    AVG(tokens_used) as avg_tokens,
                    SUM(cost_estimate) as total_cost
                FROM metrics
                WHERE timestamp > ?
            """, (cutoff,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {}
    
    def get_language_stats(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """Get language breakdown statistics."""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    language,
                    COUNT(*) as count,
                    AVG(latency_ms) as avg_latency
                FROM metrics
                WHERE timestamp > ?
                GROUP BY language
            """, (cutoff,))
            
            stats = {}
            for row in cursor.fetchall():
                lang = row['language'] or 'unknown'
                stats[lang] = {
                    'count': row['count'],
                    'avg_latency': row['avg_latency'] or 0
                }
            return stats
    
    def get_intent_stats(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """Get intent classification statistics."""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    intent,
                    COUNT(*) as count,
                    AVG(groundedness_score) as avg_groundedness
                FROM metrics
                WHERE timestamp > ?
                GROUP BY intent
            """, (cutoff,))
            
            stats = {}
            for row in cursor.fetchall():
                intent = row['intent'] or 'unknown'
                stats[intent] = {
                    'count': row['count'],
                    'avg_groundedness': row['avg_groundedness'] or 0
                }
            return stats
    
    def get_hourly_breakdown(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics aggregated by hour for charts - REAL DATA ONLY."""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m-%d %H:00', timestamp) as hour,
                    COUNT(*) as query_count,
                    AVG(latency_ms) as avg_latency,
                    MIN(latency_ms) as min_latency,
                    MAX(latency_ms) as max_latency,
                    GROUP_CONCAT(latency_ms) as all_latencies
                FROM metrics
                WHERE timestamp > ?
                GROUP BY hour
                ORDER BY hour
            """, (cutoff,))
            
            results = []
            for row in cursor.fetchall():
                latencies = [int(l) for l in row['all_latencies'].split(',') if l] if row['all_latencies'] else []
                latencies.sort()
                
                median = latencies[len(latencies)//2] if latencies else 0
                p95_index = int(len(latencies) * 0.95)
                p95 = latencies[p95_index] if latencies and p95_index < len(latencies) else latencies[-1] if latencies else 0
                
                results.append({
                    'hour': row['hour'],
                    'query_count': row['query_count'],
                    'avg_latency': row['avg_latency'],
                    'min_latency': row['min_latency'],
                    'max_latency': row['max_latency'],
                    'median_latency': median,
                    'p95_latency': p95
                })
            
            return results
    
    def get_metrics_for_period(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get all metrics for a specified time period."""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM metrics 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            """, (cutoff,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def calculate_deployment_gates(self, hours: int = 24) -> Dict[str, Any]:
        """Calculate all deployment gate values from stored metrics."""
        metrics = self.get_metrics_for_period(hours)
        
        if not metrics:
            return {
                'ready': False,
                'gates': {},
                'recommendation': 'No data available. Start using the chatbot to generate metrics.'
            }
        
        # Calculate gate values
        total_queries = len(metrics)
        errors = [m for m in metrics if m['error_type']]
        
        # Calculate groundedness
        groundedness_scores = [m['groundedness_score'] for m in metrics if m['groundedness_score'] > 0]
        avg_groundedness = sum(groundedness_scores) / len(groundedness_scores) if groundedness_scores else 0
        
        # Calculate latencies
        latencies = [m['latency_ms'] for m in metrics if not m['error_type']]
        if latencies:
            latencies.sort()
            median_latency = latencies[len(latencies) // 2]
            p95_index = int(len(latencies) * 0.95)
            p95_latency = latencies[p95_index] if p95_index < len(latencies) else latencies[-1]
        else:
            median_latency = p95_latency = 0
        
        # Calculate costs
        costs = [m['cost_estimate'] for m in metrics]
        avg_cost = sum(costs) / len(costs) if costs else 0
        
        # Get feedback stats
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN feedback_type = 'thumbs_up' THEN 1 ELSE 0 END) as positive
                FROM feedback
                WHERE timestamp > ?
            """, (cutoff,))
            
            feedback_stats = cursor.fetchone()
            satisfaction_rate = (feedback_stats['positive'] / feedback_stats['total'] 
                               if feedback_stats['total'] else 0)
        
        # Define gates with current values and thresholds
        gates = {
            'groundedness': {
                'value': avg_groundedness,
                'threshold': 0.95,
                'passing': avg_groundedness >= 0.95
            },
            'hallucination_rate': {
                'value': 1 - avg_groundedness if avg_groundedness else 1,
                'threshold': 0.02,
                'passing': (1 - avg_groundedness) <= 0.02 if avg_groundedness else False
            },
            'retrieval_hit_rate': {
                'value': 0.85,  # Placeholder - need to implement retrieval tracking
                'threshold': 0.90,
                'passing': False
            },
            'latency_median': {
                'value': median_latency / 1000,  # Convert to seconds
                'threshold': 3,
                'passing': median_latency <= 3000
            },
            'latency_p95': {
                'value': p95_latency / 1000,  # Convert to seconds
                'threshold': 7,
                'passing': p95_latency <= 7000
            },
            'containment_rate': {
                'value': 0.5,  # Placeholder - need to implement containment tracking
                'threshold': 0.60,
                'passing': False
            },
            'satisfaction_score': {
                'value': satisfaction_rate,
                'threshold': 0.70,
                'passing': satisfaction_rate >= 0.70
            },
            'cost_per_query': {
                'value': avg_cost,
                'threshold': 0.30,
                'passing': avg_cost <= 0.30
            },
            'safety_violations': {
                'value': 0,  # Placeholder - need to implement safety tracking
                'threshold': 0,
                'passing': True
            },
            'freshness_hours': {
                'value': 12,  # Placeholder - need to implement freshness tracking
                'threshold': 24,
                'passing': True
            }
        }
        
        # Log gate status
        for gate_name, gate_data in gates.items():
            self.log_gate_status(gate_name, gate_data['value'], gate_data['threshold'],
                               gate_data['passing'], hours)
        
        # Calculate overall readiness
        gates_passing = sum(1 for g in gates.values() if g['passing'])
        gates_total = len(gates)
        ready = gates_passing >= 8  # Need 8/10 for canary
        
        # Generate recommendation
        if gates_passing >= 10:
            recommendation = "All gates passing! Ready for full deployment."
        elif gates_passing >= 8:
            recommendation = "Ready for canary deployment (5-10% traffic)."
        elif gates_passing >= 6:
            recommendation = "Ready for expanded beta testing."
        else:
            recommendation = "Continue internal testing and optimization."
        
        return {
            'ready': ready,
            'gates': gates,
            'gates_passing': gates_passing,
            'gates_total': gates_total,
            'recommendation': recommendation,
            'total_queries': total_queries,
            'period_hours': hours
        }
    
    def create_aggregated_metrics(self, period_type: str = 'hourly'):
        """Create aggregated metrics for a period."""
        if period_type == 'hourly':
            period_start = (datetime.now() - timedelta(hours=1)).isoformat()
        elif period_type == 'daily':
            period_start = (datetime.now() - timedelta(days=1)).isoformat()
        else:
            period_start = (datetime.now() - timedelta(weeks=1)).isoformat()
        
        period_end = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate aggregated stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_queries,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    AVG(latency_ms) as avg_latency,
                    SUM(cost_estimate) as total_cost,
                    AVG(groundedness_score) as avg_groundedness,
                    SUM(CASE WHEN error_type IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as error_rate
                FROM metrics
                WHERE timestamp > ? AND timestamp <= ?
            """, (period_start, period_end))
            
            stats = cursor.fetchone()
            
            # Calculate P95 latency
            cursor.execute("""
                SELECT latency_ms FROM metrics
                WHERE timestamp > ? AND timestamp <= ?
                ORDER BY latency_ms
            """, (period_start, period_end))
            
            latencies = [row[0] for row in cursor.fetchall()]
            p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0
            
            # Store aggregated metrics
            cursor.execute("""
                INSERT INTO aggregated_metrics (
                    period_start, period_end, period_type, total_queries,
                    unique_sessions, avg_latency_ms, p95_latency_ms, total_cost,
                    avg_groundedness, error_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                period_start, period_end, period_type, stats['total_queries'],
                stats['unique_sessions'], int(stats['avg_latency'] or 0),
                p95_latency, stats['total_cost'] or 0, stats['avg_groundedness'] or 0,
                stats['error_rate'] or 0
            ))

# Create singleton instance
metrics_db = MetricsDatabase()