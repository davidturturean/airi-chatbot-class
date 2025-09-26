#!/usr/bin/env python3
"""
Quick test script to validate all new features are working.
"""
import sys
import json
import requests
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_single_query(api_url="http://localhost:8090", message="Hello, what are AI risks even about?"):
    """Test a single query and display results."""
    print(f"\n🔍 Testing query: '{message}'")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        # Test streaming endpoint
        response = requests.post(
            f"{api_url}/api/v1/stream",
            json={
                "message": message,
                "session_id": f"quick_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            },
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if isinstance(data, str):
                            full_response += data
                        elif isinstance(data, dict):
                            if 'metrics' in data:
                                print(f"\n📊 Metrics:")
                                print(f"  Latency: {data['metrics'].get('latency_ms', 0)}ms")
                                print(f"  Citations: {data['metrics'].get('citations_count', 0)}")
                    except json.JSONDecodeError:
                        pass
            
            elapsed = (time.time() - start_time) * 1000
            print(f"\n✅ SUCCESS - Response received in {elapsed:.0f}ms")
            print(f"\n📝 Response preview:")
            print(full_response[:500] + "..." if len(full_response) > 500 else full_response)
            
            # Check if it's correctly answering about AI risks (not out-of-scope)
            if "I can only help" in full_response or "out of my scope" in full_response:
                print("\n⚠️  WARNING: Response indicates out-of-scope (should be repository_related)")
                return False
            else:
                print("\n✅ Response correctly addresses AI risks")
                return True
                
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def run_quick_tests():
    """Run a series of quick tests."""
    print("="*70)
    print("🚀 QUICK VALIDATION TEST SUITE")
    print("="*70)
    
    api_url = "http://localhost:8090"
    
    # Test cases to validate fixes
    test_cases = [
        {
            "name": "AI Risk with Greeting",
            "query": "Hello, what are AI risks even about?",
            "expected": "repository_related"
        },
        {
            "name": "Direct AI Risk Query",
            "query": "What are the main categories of AI risks?",
            "expected": "repository_related"
        },
        {
            "name": "Employment Impact",
            "query": "How does AI affect employment?",
            "expected": "repository_related"
        },
        {
            "name": "Multilingual Query",
            "query": "¿Cuáles son los riesgos de IA?",
            "expected": "repository_related"
        },
        {
            "name": "Pure Greeting",
            "query": "Hello!",
            "expected": "chit_chat"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📌 Test {i}/{len(test_cases)}: {test['name']}")
        success = test_single_query(api_url, test['query'])
        results.append({
            "test": test['name'],
            "query": test['query'],
            "passed": success
        })
        time.sleep(2)  # Brief pause between tests
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status} - {result['test']}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The system is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the logs.")
    
    return passed == total

def check_database():
    """Check if database is recording metrics."""
    print("\n📦 Checking database...")
    
    try:
        from src.core.storage.metrics_database import MetricsDatabase
        db = MetricsDatabase()
        
        recent = db.get_recent_metrics(hours=1)
        print(f"✅ Database has {len(recent)} metrics from the last hour")
        
        if recent:
            gates = db.calculate_deployment_gates(hours=24)
            print("\n🚦 Current Gate Status:")
            print(f"  Groundedness: {gates.get('groundedness_score', 0):.2%}")
            print(f"  Latency P50: {gates.get('latency_p50', 0)}ms")
            print(f"  Error Rate: {gates.get('error_rate', 0):.2%}")
        
        return True
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick test for AIRI chatbot features')
    parser.add_argument('--api-url', default='http://localhost:8090', help='API URL')
    parser.add_argument('--check-db', action='store_true', help='Also check database')
    
    args = parser.parse_args()
    
    # Run tests
    tests_passed = run_quick_tests()
    
    # Optionally check database
    if args.check_db:
        db_ok = check_database()
        tests_passed = tests_passed and db_ok
    
    sys.exit(0 if tests_passed else 1)