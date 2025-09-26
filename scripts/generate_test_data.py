#!/usr/bin/env python3
"""
Generate REAL test data by submitting actual queries to the API.
This creates REAL metrics in the database - NO MOCK DATA.
"""
import sys
import time
import requests
import random
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# API configuration
API_BASE_URL = "http://localhost:8090"
API_ENDPOINT = f"{API_BASE_URL}/api/v1/sendMessage"

# Test queries covering different topics
TEST_QUERIES = [
    # AI Risk queries
    "What are the main AI risks?",
    "How does AI affect employment?",
    "What privacy concerns exist with AI?",
    "What are existential risks from AI?",
    "How can we ensure AI safety?",
    
    # Domain-specific queries
    "What are the economic impacts of AI?",
    "How does AI affect healthcare?",
    "What are AI risks in transportation?",
    "How does AI impact education?",
    "What are social risks of AI?",
    
    # Technical queries
    "What is alignment in AI safety?",
    "How do large language models pose risks?",
    "What are adversarial attacks in AI?",
    "What is reward hacking?",
    "How can AI systems be made more robust?",
    
    # Multilingual queries
    "¿Cuáles son los riesgos de IA?",
    "Quels sont les risques de l'IA?",
    "Was sind die Risiken von KI?",
]

def submit_query(query: str, session_id: str) -> dict:
    """Submit a single query to the API and return the response."""
    try:
        print(f"  Submitting: {query[:50]}...")
        
        start_time = time.time()
        response = requests.post(
            API_ENDPOINT,
            json={
                "message": query,
                "session_id": session_id,
                "language": "auto"  # Auto-detect language
            },
            headers={
                "Content-Type": "application/json",
                "X-Session-ID": session_id
            },
            timeout=30
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            result = response.json()
            print(f"    ✅ Success! Latency: {latency_ms}ms")
            
            # Extract metrics info
            if 'response' in result:
                response_text = result['response']
                citations = response_text.count('RID-')
                print(f"    Citations: {citations} | Length: {len(response_text)} chars")
            
            return {
                "success": True,
                "latency_ms": latency_ms,
                "response": result
            }
        else:
            print(f"    ❌ Error: {response.status_code}")
            return {
                "success": False,
                "error": f"Status {response.status_code}",
                "latency_ms": latency_ms
            }
            
    except requests.exceptions.Timeout:
        print(f"    ⏱️ Timeout after 30s")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"    ❌ Error: {str(e)}")
        return {"success": False, "error": str(e)}

def generate_test_data(num_queries: int = None):
    """Generate test data by submitting queries."""
    print("="*70)
    print("GENERATING REAL TEST DATA FOR METRICS")
    print("="*70)
    
    # Check if API is running
    try:
        health_check = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if health_check.status_code != 200:
            print("❌ API is not responding. Please start the Flask server first.")
            print("   Run: python src/api/app.py")
            return False
    except:
        print("❌ Cannot connect to API at", API_BASE_URL)
        print("   Please start the Flask server first: python src/api/app.py")
        return False
    
    print("✅ API is running")
    print()
    
    # Generate session IDs
    session_ids = [
        f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
        for i in range(3)
    ]
    
    # Select queries to run
    queries_to_run = TEST_QUERIES[:num_queries] if num_queries else TEST_QUERIES
    
    print(f"📊 Submitting {len(queries_to_run)} queries across {len(session_ids)} sessions")
    print()
    
    # Track statistics
    total_queries = 0
    successful_queries = 0
    total_latency = 0
    
    # Submit queries
    for i, query in enumerate(queries_to_run, 1):
        # Rotate through session IDs
        session_id = session_ids[i % len(session_ids)]
        
        print(f"Query {i}/{len(queries_to_run)} (Session: {session_id.split('_')[-1]})")
        result = submit_query(query, session_id)
        
        total_queries += 1
        if result['success']:
            successful_queries += 1
            total_latency += result.get('latency_ms', 0)
        
        # Small delay to avoid overwhelming the API
        time.sleep(random.uniform(0.5, 1.5))
        print()
    
    # Print summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total queries submitted: {total_queries}")
    print(f"Successful queries: {successful_queries}")
    print(f"Failed queries: {total_queries - successful_queries}")
    if successful_queries > 0:
        avg_latency = total_latency / successful_queries
        print(f"Average latency: {avg_latency:.0f}ms")
    print()
    
    # Test metrics endpoints
    print("📊 Testing metrics endpoints...")
    
    try:
        # Test dashboard endpoint
        dashboard_resp = requests.get(f"{API_BASE_URL}/api/metrics/dashboard?hours=1")
        if dashboard_resp.status_code == 200:
            data = dashboard_resp.json()
            print(f"  ✅ Dashboard endpoint: {data.get('global_metrics', {}).get('total_queries', 0)} queries recorded")
        
        # Test hourly endpoint
        hourly_resp = requests.get(f"{API_BASE_URL}/api/metrics/hourly?hours=1")
        if hourly_resp.status_code == 200:
            data = hourly_resp.json()
            print(f"  ✅ Hourly endpoint: {len(data.get('hourly_breakdown', []))} hours of data")
        
        # Test gates endpoint
        gates_resp = requests.get(f"{API_BASE_URL}/api/metrics/gates?hours=1")
        if gates_resp.status_code == 200:
            data = gates_resp.json()
            passing = data.get('gates_passing', 0)
            total = data.get('gates_total', 10)
            print(f"  ✅ Gates endpoint: {passing}/{total} gates passing")
            
    except Exception as e:
        print(f"  ❌ Error testing metrics endpoints: {e}")
    
    print()
    print("✅ Test data generation complete!")
    print("📊 View metrics at: http://localhost:8090/dashboard")
    
    return successful_queries > 0

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate real test data for metrics')
    parser.add_argument('-n', '--num-queries', type=int, 
                       help='Number of queries to submit (default: all)')
    parser.add_argument('--quick', action='store_true',
                       help='Quick test with 5 queries')
    
    args = parser.parse_args()
    
    if args.quick:
        num_queries = 5
    else:
        num_queries = args.num_queries
    
    success = generate_test_data(num_queries)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()