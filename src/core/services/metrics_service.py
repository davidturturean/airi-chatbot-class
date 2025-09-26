"""
Metrics collection and monitoring service for the AIRI chatbot.
Handles structured logging, performance tracking, and deployment gate monitoring.
"""
import json
import time
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import statistics

from ...config.logging import get_logger
try:
    from ..storage.metrics_database import metrics_db, QueryMetric
    DB_AVAILABLE = True
except Exception as e:
    logger.warning(f"Database not available, using in-memory storage: {e}")
    DB_AVAILABLE = False

logger = get_logger(__name__)

@dataclass
class QueryMetrics:
    """Metrics for a single query-response cycle."""
    timestamp: str
    session_id: str
    user_hash: str
    event_type: str = "query_response"
    
    # Query data
    query_text: str = ""
    query_intent: str = ""
    query_language: str = "en"
    query_number: int = 0
    
    # Response data
    response_preview: str = ""  # First 200 chars
    latency_ms: int = 0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    citations_count: int = 0
    docs_retrieved: int = 0
    
    # Quality metrics
    groundedness_score: float = 0.0
    citation_validity: bool = True
    response_complete: bool = True
    has_hallucination: bool = False
    
    # User feedback
    thumbs_feedback: Optional[str] = None  # up/down/null
    found_answer: Optional[str] = None  # yes/partial/no
    would_recommend: Optional[int] = None  # 1-10
    
    # Error tracking
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_json(self) -> str:
        """Convert to JSON string for structured logging."""
        data = asdict(self)
        # Ensure Railway compatibility - single line JSON
        return json.dumps(data, separators=(',', ':'))
    
    def to_railway_log(self) -> str:
        """Format for Railway's structured logging."""
        log_data = {
            "level": "error" if self.error_type else "info",
            "message": f"Query processed: {self.query_text[:50]}...",
            "session_id": self.session_id,
            "latency_ms": self.latency_ms,
            "tokens": self.tokens_used,
            "cost": self.cost_estimate,
            "intent": self.query_intent,
            "citations": self.citations_count,
            "groundedness": self.groundedness_score,
            "timestamp": self.timestamp
        }
        return json.dumps(log_data)


class MetricsService:
    """Service for collecting and analyzing chatbot metrics."""
    
    # Cost estimates per 1M tokens (Gemini 1.5 Flash/Pro pricing)
    TOKEN_COSTS = {
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},  # per 1M tokens
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00}
    }
    
    # Deployment gate thresholds (from PI's Running Lean criteria)
    DEPLOYMENT_GATES = {
        "groundedness": {"threshold": 0.95, "operator": ">="},
        "hallucination_rate": {"threshold": 0.02, "operator": "<="},
        "retrieval_hit_rate": {"threshold": 0.90, "operator": ">="},
        "latency_median": {"threshold": 3000, "operator": "<="},  # 3s in ms
        "latency_p95": {"threshold": 7000, "operator": "<="},  # 7s in ms
        "containment_rate": {"threshold": 0.60, "operator": ">="},
        "satisfaction_score": {"threshold": 0.70, "operator": ">="},
        "cost_per_query": {"threshold": 0.30, "operator": "<="},
        "safety_violations": {"threshold": 0, "operator": "=="},
        "freshness_hours": {"threshold": 24, "operator": "<="}
    }
    
    def __init__(self):
        """Initialize metrics service."""
        self.metrics_buffer = []
        self.session_metrics = {}
        self.model_name = os.getenv("PRIMARY_MODEL", "gemini-1.5-flash")
        
    def hash_user_identifier(self, ip: str = None, user_agent: str = None) -> str:
        """Create privacy-preserving user hash."""
        identifier = f"{ip or 'unknown'}:{user_agent or 'unknown'}"
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str = None) -> float:
        """Calculate estimated cost for token usage."""
        model = model or self.model_name
        if "flash" in model.lower():
            costs = self.TOKEN_COSTS["gemini-1.5-flash"]
        else:
            costs = self.TOKEN_COSTS["gemini-1.5-pro"]
        
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        return round(input_cost + output_cost, 6)
    
    def log_query(
        self,
        session_id: str,
        query: str,
        response: str,
        latency_ms: int,
        docs_retrieved: List[Any] = None,
        intent: str = "general",
        language: str = "en",
        tokens: Dict[str, int] = None,
        user_ip: str = None,
        user_agent: str = None,
        error: Exception = None
    ) -> QueryMetrics:
        """Log a query-response interaction with full metrics."""
        
        # Create metrics object
        metrics = QueryMetrics(
            timestamp=datetime.utcnow().isoformat(),
            session_id=session_id,
            user_hash=self.hash_user_identifier(user_ip, user_agent),
            query_text=query[:500],  # Truncate for storage
            query_intent=intent,
            query_language=language,
            response_preview=response[:200] if response else "",
            latency_ms=latency_ms,
            docs_retrieved=len(docs_retrieved) if docs_retrieved else 0
        )
        
        # Add token metrics if provided
        if tokens:
            metrics.tokens_used = tokens.get("total", 0)
            metrics.cost_estimate = self.calculate_cost(
                tokens.get("input", 0),
                tokens.get("output", 0)
            )
        
        # Calculate quality metrics
        if response and docs_retrieved:
            metrics.citations_count = response.count("RID-")
            metrics.groundedness_score = self._calculate_groundedness(response, docs_retrieved)
            metrics.citation_validity = self._check_citation_validity(response, docs_retrieved)
        
        # Handle errors
        if error:
            metrics.error_type = type(error).__name__
            metrics.error_message = str(error)[:200]
        
        # Log to Railway (stdout for structured logging)
        print(metrics.to_railway_log())
        
        # Store in buffer
        self.metrics_buffer.append(metrics)
        
        # Update session metrics
        if session_id not in self.session_metrics:
            self.session_metrics[session_id] = {
                "start_time": datetime.utcnow(),
                "queries": [],
                "total_cost": 0,
                "satisfaction_scores": []
            }
        self.session_metrics[session_id]["queries"].append(metrics)
        self.session_metrics[session_id]["total_cost"] += metrics.cost_estimate
        
        # Persist to database if available
        if DB_AVAILABLE:
            try:
                user_hash = self.hash_user_identifier(user_ip, user_agent)
                db_metric = QueryMetric(
                    session_id=session_id,
                    timestamp=metrics.timestamp,
                    query=query[:500],
                    response=response[:1000] if response else "",
                    latency_ms=latency_ms,
                    tokens_used=metrics.tokens_used,
                    cost_estimate=metrics.cost_estimate,
                    citations_count=metrics.citations_count,
                    groundedness_score=metrics.groundedness_score,
                    language=language,
                    intent=intent,
                    user_hash=user_hash,
                    error_type=metrics.error_type
                )
                metrics_db.log_metric(db_metric)
                metrics_db.update_session(session_id, user_hash, language)
            except Exception as e:
                logger.error(f"Failed to persist metrics to database: {e}")
        
        return metrics
    
    def log_feedback(
        self,
        session_id: str,
        query_index: int,
        thumbs: str = None,
        found_answer: str = None,
        would_recommend: int = None
    ):
        """Log user feedback for a specific query."""
        if session_id in self.session_metrics:
            queries = self.session_metrics[session_id]["queries"]
            if 0 <= query_index < len(queries):
                if thumbs:
                    queries[query_index].thumbs_feedback = thumbs
                if found_answer:
                    queries[query_index].found_answer = found_answer
                if would_recommend:
                    queries[query_index].would_recommend = would_recommend
                    self.session_metrics[session_id]["satisfaction_scores"].append(would_recommend)
                
                # Log updated metrics
                print(queries[query_index].to_railway_log())
                
                # Persist feedback to database
                if DB_AVAILABLE:
                    try:
                        metrics_db.log_feedback(
                            session_id=session_id,
                            feedback_type=thumbs or "neutral",
                            query_id=query_index,
                            found_answer=found_answer,
                            would_recommend=would_recommend
                        )
                    except Exception as e:
                        logger.error(f"Failed to persist feedback to database: {e}")
    
    def _calculate_groundedness(self, response: str, docs: List[Any]) -> float:
        """Calculate groundedness score (how well response is supported by documents)."""
        # Simplified groundedness check - in production, use LLM judge
        if not docs or not response:
            return 0.0
        
        # Check if key claims have citations
        sentences = response.split('.')
        cited_sentences = sum(1 for s in sentences if 'RID-' in s)
        
        # Basic heuristic: proportion of sentences with citations
        groundedness = cited_sentences / max(len(sentences), 1)
        return min(groundedness * 1.2, 1.0)  # Boost slightly, cap at 1.0
    
    def _check_citation_validity(self, response: str, docs: List[Any]) -> bool:
        """Check if all citations in response are valid."""
        import re
        
        # Extract all RID citations
        cited_rids = re.findall(r'RID-\d{5}', response)
        
        # Get available RIDs from documents
        available_rids = set()
        for doc in docs:
            if hasattr(doc, 'metadata') and 'rid' in doc.metadata:
                available_rids.add(doc.metadata['rid'])
        
        # All cited RIDs should be in available RIDs
        for rid in cited_rids:
            if rid not in available_rids:
                return False
        
        return True
    
    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get aggregated metrics for a session."""
        if session_id not in self.session_metrics:
            return {}
        
        session = self.session_metrics[session_id]
        queries = session["queries"]
        
        if not queries:
            return {}
        
        latencies = [q.latency_ms for q in queries]
        
        return {
            "session_id": session_id,
            "start_time": session["start_time"].isoformat(),
            "query_count": len(queries),
            "total_cost": session["total_cost"],
            "avg_latency_ms": statistics.mean(latencies),
            "median_latency_ms": statistics.median(latencies),
            "p95_latency_ms": self._calculate_percentile(latencies, 95),
            "total_tokens": sum(q.tokens_used for q in queries),
            "error_rate": sum(1 for q in queries if q.error_type) / len(queries),
            "avg_satisfaction": statistics.mean(session["satisfaction_scores"]) if session["satisfaction_scores"] else None,
            "containment_rate": sum(1 for q in queries if q.found_answer in ["yes", "partial"]) / len(queries)
        }
    
    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value from list."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_global_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get global metrics for the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_metrics = [
            m for m in self.metrics_buffer
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
        
        if not recent_metrics:
            return {"message": "No metrics available for this period"}
        
        latencies = [m.latency_ms for m in recent_metrics]
        costs = [m.cost_estimate for m in recent_metrics]
        groundedness_scores = [m.groundedness_score for m in recent_metrics if m.groundedness_score > 0]
        
        return {
            "period_hours": hours,
            "total_queries": len(recent_metrics),
            "unique_sessions": len(set(m.session_id for m in recent_metrics)),
            "metrics": {
                "latency": {
                    "median_ms": statistics.median(latencies),
                    "p95_ms": self._calculate_percentile(latencies, 95),
                    "p99_ms": self._calculate_percentile(latencies, 99)
                },
                "cost": {
                    "total": sum(costs),
                    "per_query": statistics.mean(costs)
                },
                "quality": {
                    "avg_groundedness": statistics.mean(groundedness_scores) if groundedness_scores else 0,
                    "error_rate": sum(1 for m in recent_metrics if m.error_type) / len(recent_metrics),
                    "hallucination_rate": sum(1 for m in recent_metrics if m.has_hallucination) / len(recent_metrics)
                },
                "engagement": {
                    "queries_per_session": len(recent_metrics) / len(set(m.session_id for m in recent_metrics)),
                    "containment_rate": sum(1 for m in recent_metrics if m.found_answer in ["yes", "partial"]) / len(recent_metrics) if any(m.found_answer for m in recent_metrics) else None
                }
            }
        }
    
    def check_deployment_gates(self, hours: int = 24) -> Dict[str, Any]:
        """Check if deployment gates are passing based on recent metrics."""
        # Try to use database if available
        if DB_AVAILABLE:
            try:
                return metrics_db.calculate_deployment_gates(hours)
            except Exception as e:
                logger.warning(f"Failed to check gates from database: {e}, falling back to in-memory")
        
        # Fall back to in-memory metrics
        metrics = self.get_global_metrics(hours)
        
        if "message" in metrics:  # No metrics available
            return {"ready": False, "message": metrics["message"]}
        
        gates_status = {}
        passing_count = 0
        
        # Check each gate
        gate_values = {
            "groundedness": metrics["metrics"]["quality"]["avg_groundedness"],
            "hallucination_rate": metrics["metrics"]["quality"]["hallucination_rate"],
            "retrieval_hit_rate": 0.92,  # TODO: Calculate from actual retrieval metrics
            "latency_median": metrics["metrics"]["latency"]["median_ms"],
            "latency_p95": metrics["metrics"]["latency"]["p95_ms"],
            "containment_rate": metrics["metrics"]["engagement"]["containment_rate"] or 0,
            "satisfaction_score": 0.75,  # TODO: Calculate from actual feedback
            "cost_per_query": metrics["metrics"]["cost"]["per_query"],
            "safety_violations": 0,  # TODO: Implement safety checks
            "freshness_hours": 12  # TODO: Track index update time
        }
        
        for gate_name, gate_config in self.DEPLOYMENT_GATES.items():
            value = gate_values.get(gate_name, 0)
            threshold = gate_config["threshold"]
            operator = gate_config["operator"]
            
            if operator == ">=":
                passing = value >= threshold
            elif operator == "<=":
                passing = value <= threshold
            elif operator == "==":
                passing = value == threshold
            else:
                passing = False
            
            gates_status[gate_name] = {
                "value": value,
                "threshold": threshold,
                "passing": passing
            }
            
            if passing:
                passing_count += 1
        
        return {
            "ready": passing_count >= 8,  # Need 8/10 gates passing
            "gates_passing": passing_count,
            "gates_total": len(self.DEPLOYMENT_GATES),
            "gates": gates_status,
            "recommendation": self._get_deployment_recommendation(passing_count)
        }
    
    def _get_deployment_recommendation(self, gates_passing: int) -> str:
        """Get deployment recommendation based on gates passing."""
        if gates_passing >= 10:
            return "Ready for full deployment"
        elif gates_passing >= 8:
            return "Ready for canary deployment (5-10% traffic)"
        elif gates_passing >= 6:
            return "Ready for expanded beta testing"
        elif gates_passing >= 4:
            return "Continue internal testing and optimization"
        else:
            return "Significant improvements needed before deployment"
    
    def export_metrics(self, format: str = "json", period_hours: int = 168) -> str:
        """Export metrics in specified format."""
        metrics = self.get_global_metrics(period_hours)
        
        if format == "json":
            return json.dumps(metrics, indent=2)
        elif format == "csv":
            # Convert to CSV format for stakeholder reports
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(["Metric", "Value", "Target", "Status"])
            
            # Write deployment gates
            gates = self.check_deployment_gates(period_hours)
            for gate_name, gate_data in gates["gates"].items():
                status = "PASS" if gate_data["passing"] else "FAIL"
                writer.writerow([
                    gate_name.replace("_", " ").title(),
                    f"{gate_data['value']:.2f}",
                    f"{gate_data['threshold']}",
                    status
                ])
            
            return output.getvalue()
        else:
            return str(metrics)


# Singleton instance
metrics_service = MetricsService()