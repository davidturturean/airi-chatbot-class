#!/usr/bin/env python3
"""
Real-time metrics monitoring script.
Displays live deployment gates and metrics status.
"""
import sys
import time
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.services.metrics_service import metrics_service
from src.core.storage.metrics_database import MetricsDatabase

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def format_gate_status(value, target, comparison=">="):
    """Format gate status with color indicators."""
    if comparison == ">=":
        meets_target = value >= target
    elif comparison == "<=":
        meets_target = value <= target
    else:
        meets_target = False
    
    status = "✅ PASS" if meets_target else "❌ FAIL"
    return status

def monitor_metrics(refresh_interval=5):
    """Monitor metrics in real-time."""
    print("Starting real-time metrics monitoring...")
    print("Press Ctrl+C to stop")
    print("-" * 70)
    
    db = MetricsDatabase()
    
    try:
        while True:
            clear_screen()
            
            # Header
            print("="*70)
            print("🎯 AIRI CHATBOT - REAL-TIME METRICS DASHBOARD")
            print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*70)
            
            # Get current metrics from database
            try:
                gates = db.calculate_deployment_gates(hours=24)
                summary = db.get_summary_stats(hours=24)
                recent_metrics = db.get_recent_metrics(hours=1)
                
                # Display summary stats
                print("\n📊 SUMMARY (Last 24 Hours)")
                print("-"*40)
                print(f"Total Queries:      {summary.get('total_queries', 0):,}")
                print(f"Unique Sessions:    {summary.get('unique_sessions', 0):,}")
                print(f"Total Cost:         ${summary.get('total_cost', 0):.4f}")
                print(f"Avg Response Time:  {summary.get('avg_latency_ms', 0):.0f}ms")
                
                # Display deployment gates
                print("\n🚦 DEPLOYMENT GATES")
                print("-"*40)
                
                # Groundedness
                groundedness = gates.get('groundedness_score', 0)
                status = format_gate_status(groundedness, 0.95, ">=")
                print(f"Groundedness:       {groundedness:6.2%}  (≥95%)  {status}")
                
                # Hallucination Rate
                hallucination = gates.get('hallucination_rate', 0)
                status = format_gate_status(hallucination, 0.02, "<=")
                print(f"Hallucination:      {hallucination:6.2%}  (≤2%)   {status}")
                
                # Retrieval Hit Rate
                retrieval = gates.get('retrieval_hit_rate', 0)
                status = format_gate_status(retrieval, 0.90, ">=")
                print(f"Retrieval Hit:      {retrieval:6.2%}  (≥90%)  {status}")
                
                # Latency P50
                latency_p50 = gates.get('latency_p50', 0)
                status = format_gate_status(latency_p50, 3000, "<=")
                print(f"Latency P50:        {latency_p50:5.0f}ms  (≤3s)   {status}")
                
                # Latency P95
                latency_p95 = gates.get('latency_p95', 0)
                status = format_gate_status(latency_p95, 7000, "<=")
                print(f"Latency P95:        {latency_p95:5.0f}ms  (≤7s)   {status}")
                
                # Error Rate
                error_rate = gates.get('error_rate', 0)
                status = format_gate_status(error_rate, 0.05, "<=")
                print(f"Error Rate:         {error_rate:6.2%}  (≤5%)   {status}")
                
                # Recent activity (last hour)
                print(f"\n⏱️  RECENT ACTIVITY (Last Hour)")
                print("-"*40)
                print(f"Queries:            {len(recent_metrics)}")
                if recent_metrics:
                    recent_latencies = [m['latency_ms'] for m in recent_metrics if m['latency_ms']]
                    if recent_latencies:
                        print(f"Avg Latency:        {sum(recent_latencies)/len(recent_latencies):.0f}ms")
                    
                    # Show language distribution
                    languages = {}
                    for m in recent_metrics:
                        lang = m.get('language', 'unknown')
                        languages[lang] = languages.get(lang, 0) + 1
                    
                    print("\nLanguages:")
                    for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                        print(f"  {lang:10s}: {count:3d} ({count/len(recent_metrics)*100:.0f}%)")
                
                # Intent distribution
                intent_stats = db.get_intent_stats(hours=1)
                if intent_stats:
                    print("\nIntent Distribution:")
                    for intent, stats in sorted(intent_stats.items()):
                        print(f"  {intent:20s}: {stats['count']:3d}")
                
                # Last 5 queries
                print(f"\n📝 LAST 5 QUERIES")
                print("-"*40)
                for metric in recent_metrics[:5]:
                    query = metric.get('query', 'N/A')[:50]
                    latency = metric.get('latency_ms', 0)
                    print(f"• {query:50s} ({latency}ms)")
                
                # Footer
                print("\n" + "="*70)
                print(f"Refreshing every {refresh_interval} seconds... (Ctrl+C to exit)")
                
            except Exception as e:
                print(f"\n⚠️  Error fetching metrics: {e}")
                print("Retrying in next interval...")
            
            time.sleep(refresh_interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped by user")
        return

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor AIRI chatbot metrics in real-time')
    parser.add_argument('--interval', type=int, default=5, help='Refresh interval in seconds')
    
    args = parser.parse_args()
    
    monitor_metrics(refresh_interval=args.interval)