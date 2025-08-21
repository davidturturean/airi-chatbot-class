#!/usr/bin/env python3
"""Test the 3 problematic taxonomy queries that were failing."""

import requests
import json

# API endpoint
url = "http://localhost:8090/api/v1/sendMessage"

# The 3 queries that were failing
TEST_QUERIES = [
    {
        'id': 4,
        'query': 'What are all the subdomains under Privacy & Security?',
        'expected': 'Should list Privacy violations, Security vulnerabilities, Data leaks'
    },
    {
        'id': 12,
        'query': 'Explain the complete structure of AI risk categorization',
        'expected': 'Should explain both taxonomies with domains and subdomains'
    },
    {
        'id': 16,
        'query': 'What percentage of risks fall into each causal category?',
        'expected': 'Should show percentages for Entity, Intentionality, Timing'
    }
]

def test_query(query_info):
    """Test a single query through the API."""
    payload = {
        "message": query_info['query'],
        "conversationId": f"test-fix-{query_info['id']}",
        "session_id": f"test-fix-session"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            
            # Check if it's an error
            is_error = 'Error executing query' in response_text or \
                      'Parser Error' in response_text or \
                      "'dict' object" in response_text
            
            return {
                'id': query_info['id'],
                'query': query_info['query'],
                'response': response_text,
                'is_error': is_error,
                'status': 'error' if is_error else 'success'
            }
        else:
            return {
                'id': query_info['id'],
                'query': query_info['query'],
                'response': f"HTTP {response.status_code}",
                'is_error': True,
                'status': 'http_error'
            }
            
    except Exception as e:
        return {
            'id': query_info['id'],
            'query': query_info['query'],
            'response': str(e),
            'is_error': True,
            'status': 'exception'
        }

def main():
    print("=" * 80)
    print("TESTING FIXED TAXONOMY QUERIES")
    print("=" * 80)
    
    results = []
    
    for query_info in TEST_QUERIES:
        print(f"\nQuery {query_info['id']}: \"{query_info['query']}\"")
        print(f"Expected: {query_info['expected']}")
        print("-" * 40)
        
        result = test_query(query_info)
        results.append(result)
        
        if result['is_error']:
            print(f"❌ STILL FAILING: {result['response'][:200]}")
        else:
            print(f"✅ FIXED!")
            print(f"Response preview: {result['response'][:300]}...")
    
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    fixed_count = sum(1 for r in results if not r['is_error'])
    print(f"Fixed: {fixed_count}/{len(results)}")
    
    if fixed_count == len(results):
        print("🎉 All queries are now working!")
    else:
        print("⚠️  Some queries still need fixes")
        for r in results:
            if r['is_error']:
                print(f"  - Query {r['id']}: {r['status']}")

if __name__ == "__main__":
    main()