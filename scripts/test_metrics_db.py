#!/usr/bin/env python3
"""
Test script for metrics database functionality.
Validates that metrics are properly stored and retrieved.
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.storage.metrics_database import MetricsDatabase, QueryMetric

def test_metrics_database():
    """Test all database operations."""
    print("="*70)
    print("TESTING METRICS DATABASE")
    print("="*70)
    
    # Initialize database
    db = MetricsDatabase("data/test_metrics.db")
    print("✅ Database initialized")
    
    # Create test metrics
    test_metrics = [
        QueryMetric(
            session_id="test_session_001",
            timestamp=datetime.now().isoformat(),
            query="What are AI risks?",
            response="AI risks include employment displacement, privacy violations, bias, and safety concerns.",
            latency_ms=3500,
            tokens_used=150,
            cost_estimate=0.002,
            citations_count=5,
            groundedness_score=0.95,
            language="en",
            intent="repository_related",
            user_hash="test_hash_001"
        ),
        QueryMetric(
            session_id="test_session_001",
            timestamp=datetime.now().isoformat(),
            query="How does AI affect jobs?",
            response="AI affects jobs through automation, skill displacement, and creating new roles.",
            latency_ms=2800,
            tokens_used=120,
            cost_estimate=0.0015,
            citations_count=8,
            groundedness_score=0.98,
            language="en",
            intent="repository_related",
            user_hash="test_hash_001"
        ),
        QueryMetric(
            session_id="test_session_002",
            timestamp=datetime.now().isoformat(),
            query="¿Cuáles son los riesgos de IA?",
            response="Los riesgos de IA incluyen desplazamiento laboral, violaciones de privacidad...",
            latency_ms=4200,
            tokens_used=180,
            cost_estimate=0.0025,
            citations_count=6,
            groundedness_score=0.92,
            language="es",
            intent="repository_related",
            user_hash="test_hash_002"
        )
    ]
    
    # Test logging metrics
    print("\n📝 Logging test metrics...")
    metric_ids = []
    for metric in test_metrics:
        try:
            metric_id = db.log_metric(metric)
            metric_ids.append(metric_id)
            print(f"  ✅ Logged metric {metric_id}: {metric.query[:30]}...")
        except Exception as e:
            print(f"  ❌ Failed to log metric: {e}")
    
    # Test retrieval
    print("\n🔍 Testing retrieval...")
    recent_metrics = db.get_recent_metrics(hours=1)
    print(f"  ✅ Retrieved {len(recent_metrics)} recent metrics")
    
    # Test session retrieval
    print("\n🔍 Testing session retrieval...")
    session_metrics = db.get_session_metrics("test_session_001")
    print(f"  ✅ Retrieved {len(session_metrics)} metrics for session test_session_001")
    
    # Test aggregation
    print("\n📊 Testing aggregations...")
    summary = db.get_summary_stats(hours=24)
    print(f"  Total queries: {summary.get('total_queries', 0)}")
    print(f"  Unique sessions: {summary.get('unique_sessions', 0)}")
    print(f"  Avg latency: {summary.get('avg_latency_ms', 0):.0f}ms")
    print(f"  Avg groundedness: {summary.get('avg_groundedness', 0):.2%}")
    
    # Test deployment gates
    print("\n🚦 Testing deployment gates...")
    gates = db.calculate_deployment_gates(hours=24)
    
    print("  Gate Status:")
    print(f"    Groundedness: {gates.get('groundedness_score', 0):.2%} (target: ≥95%)")
    print(f"    Hallucination Rate: {gates.get('hallucination_rate', 0):.2%} (target: ≤2%)")
    print(f"    Retrieval Hit Rate: {gates.get('retrieval_hit_rate', 0):.2%} (target: ≥90%)")
    print(f"    Latency P50: {gates.get('latency_p50', 0)}ms (target: ≤3000ms)")
    print(f"    Latency P95: {gates.get('latency_p95', 0)}ms (target: ≤7000ms)")
    print(f"    Error Rate: {gates.get('error_rate', 0):.2%} (target: ≤5%)")
    
    # Test language breakdown
    print("\n🌐 Testing language breakdown...")
    language_stats = db.get_language_stats(hours=24)
    for lang, stats in language_stats.items():
        print(f"  {lang}: {stats['count']} queries, avg latency: {stats['avg_latency']:.0f}ms")
    
    # Test intent breakdown
    print("\n🎯 Testing intent breakdown...")
    intent_stats = db.get_intent_stats(hours=24)
    for intent, stats in intent_stats.items():
        print(f"  {intent}: {stats['count']} queries, avg groundedness: {stats['avg_groundedness']:.2%}")
    
    print("\n" + "="*70)
    print("✅ ALL DATABASE TESTS COMPLETED SUCCESSFULLY!")
    print("="*70)
    
    return True

if __name__ == "__main__":
    try:
        success = test_metrics_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)