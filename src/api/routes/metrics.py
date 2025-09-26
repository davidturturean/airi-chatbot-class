"""
Metrics and feedback API routes for monitoring and deployment gates.
"""
from flask import Blueprint, request, jsonify
from datetime import datetime

from ...core.services.metrics_service import metrics_service
from ...config.logging import get_logger

logger = get_logger(__name__)

# Create blueprint
metrics_bp = Blueprint('metrics', __name__)


@metrics_bp.route('/api/v1/feedback', methods=['POST'])
def submit_feedback():
    """Submit user feedback for a query."""
    try:
        data = request.json
        
        session_id = data.get('session_id') or request.headers.get('X-Session-ID')
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400
        
        query_index = data.get('query_index', -1)  # Default to last query
        
        # Log feedback
        metrics_service.log_feedback(
            session_id=session_id,
            query_index=query_index,
            thumbs=data.get('thumbs'),  # 'up' or 'down'
            found_answer=data.get('found_answer'),  # 'yes', 'partial', 'no'
            would_recommend=data.get('would_recommend')  # 1-10
        )
        
        logger.info(f"Feedback received for session {session_id}, query {query_index}")
        
        return jsonify({
            "status": "success",
            "message": "Feedback recorded",
            "session_id": session_id
        })
        
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}")
        return jsonify({"error": str(e)}), 500


@metrics_bp.route('/api/metrics/dashboard', methods=['GET'])
def metrics_dashboard():
    """Get current metrics dashboard data."""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        # Get global metrics
        global_metrics = metrics_service.get_global_metrics(hours)
        
        # Check deployment gates
        gates_status = metrics_service.check_deployment_gates(hours)
        
        # Get recent sessions summary
        recent_sessions = []
        for session_id, session_data in list(metrics_service.session_metrics.items())[-10:]:
            session_summary = metrics_service.get_session_metrics(session_id)
            recent_sessions.append(session_summary)
        
        return jsonify({
            "timestamp": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "global_metrics": global_metrics,
            "deployment_gates": gates_status,
            "recent_sessions": recent_sessions,
            "status": "healthy"
        })
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}")
        return jsonify({"error": str(e)}), 500


@metrics_bp.route('/api/metrics/export', methods=['GET'])
def export_metrics():
    """Export metrics in specified format."""
    try:
        format = request.args.get('format', 'json')
        hours = request.args.get('hours', 168, type=int)  # Default 1 week
        
        export_data = metrics_service.export_metrics(format, hours)
        
        if format == 'csv':
            # Return as downloadable CSV
            from flask import Response
            return Response(
                export_data,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment;filename=metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
            )
        else:
            # Return as JSON
            return Response(export_data, mimetype='application/json')
            
    except Exception as e:
        logger.error(f"Error exporting metrics: {str(e)}")
        return jsonify({"error": str(e)}), 500


@metrics_bp.route('/api/metrics/gates', methods=['GET'])
def check_gates():
    """Check deployment gates status."""
    try:
        hours = request.args.get('hours', 24, type=int)
        gates_status = metrics_service.check_deployment_gates(hours)
        
        # Add visual indicators
        gates_status['visual'] = {
            'color': 'green' if gates_status['ready'] else 'yellow' if gates_status['gates_passing'] >= 6 else 'red',
            'icon': '✅' if gates_status['ready'] else '⚠️' if gates_status['gates_passing'] >= 6 else '❌',
            'message': gates_status['recommendation']
        }
        
        return jsonify(gates_status)
        
    except Exception as e:
        logger.error(f"Error checking gates: {str(e)}")
        return jsonify({"error": str(e)}), 500


@metrics_bp.route('/api/metrics/session/<session_id>', methods=['GET'])
def get_session_metrics(session_id):
    """Get metrics for a specific session."""
    try:
        session_metrics = metrics_service.get_session_metrics(session_id)
        
        if not session_metrics:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify(session_metrics)
        
    except Exception as e:
        logger.error(f"Error getting session metrics: {str(e)}")
        return jsonify({"error": str(e)}), 500


@metrics_bp.route('/api/metrics/hourly', methods=['GET'])
def get_hourly_metrics():
    """Get REAL hourly metrics from database - NO MOCK DATA."""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        # Import database directly
        from ...core.storage.metrics_database import metrics_db
        
        # Get actual data from database
        hourly_data = metrics_db.get_hourly_breakdown(hours)
        
        # If no data, return empty array, NOT mock data
        if not hourly_data:
            return jsonify({
                "message": "No data available yet. Submit queries to generate metrics.",
                "hourly_breakdown": [],
                "total_hours": hours
            })
        
        return jsonify({
            "hourly_breakdown": hourly_data,
            "total_hours": hours,
            "data_points": len(hourly_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting hourly metrics: {str(e)}")
        return jsonify({"error": str(e)}), 500


@metrics_bp.route('/api/metrics/details/<metric_name>', methods=['GET'])
def get_metric_details(metric_name):
    """Return ACTUAL queries/data that make up a metric."""
    try:
        from ...core.storage.metrics_database import metrics_db
        
        hours = request.args.get('hours', 24, type=int)
        queries = metrics_db.get_recent_metrics(hours)
        
        if metric_name == 'groundedness':
            total = len(queries)
            passing = sum(1 for q in queries if q.get('groundedness_score', 0) >= 0.8)
            
            return jsonify({
                "metric": "groundedness",
                "description": "Percentage of response content that is directly supported by cited documents",
                "total": total,
                "passing": passing,
                "percentage": (passing / total * 100) if total > 0 else 0,
                "threshold": 80,
                "details": [
                    {
                        "query": q['query'][:200],
                        "response": q['response'][:200] + "..." if len(q['response']) > 200 else q['response'],
                        "groundedness_score": q.get('groundedness_score', 0),
                        "citations": q.get('citations_count', 0),
                        "timestamp": q['timestamp'],
                        "latency_ms": q['latency_ms']
                    }
                    for q in queries[:50]  # Limit to 50 most recent
                ]
            })
        
        elif metric_name == 'latency':
            latencies = [q['latency_ms'] for q in queries if q.get('latency_ms')]
            latencies.sort()
            
            return jsonify({
                "metric": "latency",
                "description": "Response time for queries in milliseconds",
                "total": len(latencies),
                "median": latencies[len(latencies)//2] if latencies else 0,
                "p95": latencies[int(len(latencies) * 0.95)] if latencies else 0,
                "details": [
                    {
                        "query": q['query'][:200],
                        "latency_ms": q['latency_ms'],
                        "timestamp": q['timestamp']
                    }
                    for q in sorted(queries, key=lambda x: x.get('latency_ms', 0), reverse=True)[:50]
                ]
            })
        
        elif metric_name == 'containment':
            with_feedback = [q for q in queries if q.get('feedback')]
            contained = sum(1 for q in with_feedback if q.get('feedback') in ['yes', 'partial'])
            
            return jsonify({
                "metric": "containment",
                "description": "Percentage of queries resolved without needing escalation",
                "total": len(with_feedback),
                "contained": contained,
                "percentage": (contained / len(with_feedback) * 100) if with_feedback else 0,
                "note": "Based on user feedback when provided",
                "details": [
                    {
                        "query": q['query'][:200],
                        "feedback": q.get('feedback', 'none'),
                        "timestamp": q['timestamp']
                    }
                    for q in with_feedback[:50]
                ]
            })
        
        else:
            return jsonify({"error": f"Unknown metric: {metric_name}"}), 404
            
    except Exception as e:
        logger.error(f"Error getting metric details: {str(e)}")
        return jsonify({"error": str(e)}), 500


@metrics_bp.route('/api/metrics/test', methods=['POST'])
def test_metrics():
    """Test endpoint to verify metrics collection is working."""
    try:
        # Log a test query
        test_metrics = metrics_service.log_query(
            session_id="test_session",
            query="Test query for metrics validation",
            response="This is a test response with RID-00001 citation.",
            latency_ms=1234,
            docs_retrieved=[{"metadata": {"rid": "RID-00001"}}],
            intent="test",
            language="en",
            tokens={"input": 50, "output": 100, "total": 150}
        )
        
        return jsonify({
            "status": "success",
            "message": "Metrics test successful",
            "metrics": {
                "latency_ms": test_metrics.latency_ms,
                "cost_estimate": test_metrics.cost_estimate,
                "citations_count": test_metrics.citations_count,
                "groundedness_score": test_metrics.groundedness_score
            }
        })
        
    except Exception as e:
        logger.error(f"Error in metrics test: {str(e)}")
        return jsonify({"error": str(e)}), 500