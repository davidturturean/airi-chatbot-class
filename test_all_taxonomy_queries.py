#!/usr/bin/env python3
"""Test all 20 taxonomy queries through the actual API and log chat responses."""

import requests
import json
import time
from datetime import datetime

# API endpoint
url = "http://localhost:8090/api/v1/sendMessage"

# All 20 test queries from the comprehensive test suite
TEST_QUERIES = [
    {
        'id': 1,
        'query': 'List all 24 subdomains organized by domain',
        'category': 'enumeration'
    },
    {
        'id': 2,
        'query': "What's the difference between intentional and unintentional risks?",
        'category': 'comparison'
    },
    {
        'id': 3,
        'query': 'Show me every domain in the AI risk taxonomy',
        'category': 'enumeration'
    },
    {
        'id': 4,
        'query': 'What are all the subdomains under Privacy & Security?',
        'category': 'enumeration'
    },
    {
        'id': 5,
        'query': 'Give me complete statistics for all risk categories',
        'category': 'statistics'
    },
    {
        'id': 6,
        'query': 'Compare pre-deployment vs post-deployment risks',
        'category': 'comparison'
    },
    {
        'id': 7,
        'query': 'What is the difference between human and AI caused risks?',
        'category': 'comparison'
    },
    {
        'id': 8,
        'query': 'Compare the causal taxonomy with the domain taxonomy',
        'category': 'comparison'
    },
    {
        'id': 9,
        'query': 'List the 3 dimensions of the causal taxonomy',
        'category': 'enumeration'
    },
    {
        'id': 10,
        'query': 'Show all subdomains related to AI System Safety',
        'category': 'enumeration'
    },
    {
        'id': 11,
        'query': 'What are the main risk categories in the AI Risk Database v3?',
        'category': 'mixed'
    },
    {
        'id': 12,
        'query': 'Explain the complete structure of AI risk categorization',
        'category': 'mixed'
    },
    {
        'id': 13,
        'query': 'Provide full details about the Discrimination & Toxicity domain',
        'category': 'detail'
    },
    {
        'id': 14,
        'query': 'Give me all information about timing in the causal taxonomy',
        'category': 'detail'
    },
    {
        'id': 15,
        'query': 'How many risks are in each of the 7 domains?',
        'category': 'statistics'
    },
    {
        'id': 16,
        'query': 'What percentage of risks fall into each causal category?',
        'category': 'statistics'
    },
    {
        'id': 17,
        'query': 'Tell me everything about how AI risks are organized',
        'category': 'natural'
    },
    {
        'id': 18,
        'query': 'I need a complete list of all risk subcategories',
        'category': 'natural'
    },
    {
        'id': 19,
        'query': 'Show the full breakdown of unintentional AI-caused post-deployment risks',
        'category': 'edge'
    },
    {
        'id': 20,
        'query': 'List every single subdomain across all 7 domains with their percentages',
        'category': 'edge'
    }
]

def test_query(query_info):
    """Test a single query through the API."""
    payload = {
        "message": query_info['query'],
        "conversationId": f"test-taxonomy-{query_info['id']}",
        "session_id": f"test-session-{datetime.now().timestamp()}"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'id': query_info['id'],
                'category': query_info['category'],
                'query': query_info['query'],
                'response': data.get('response', ''),
                'status': 'success',
                'response_time': response.elapsed.total_seconds()
            }
        else:
            return {
                'id': query_info['id'],
                'category': query_info['category'],
                'query': query_info['query'],
                'response': f"Error: Status {response.status_code} - {response.text}",
                'status': 'error',
                'error_code': response.status_code
            }
            
    except requests.exceptions.Timeout:
        return {
            'id': query_info['id'],
            'category': query_info['category'],
            'query': query_info['query'],
            'response': "Timeout after 30 seconds",
            'status': 'timeout'
        }
    except Exception as e:
        return {
            'id': query_info['id'],
            'category': query_info['category'],
            'query': query_info['query'],
            'response': f"Error: {str(e)}",
            'status': 'error',
            'error': str(e)
        }

def main():
    """Run all taxonomy queries and save results."""
    print("=" * 80)
    print("TESTING ALL 20 TAXONOMY QUERIES THROUGH API")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = []
    
    for i, query_info in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/20] Testing Query ID {query_info['id']} ({query_info['category']})")
        print(f"Query: \"{query_info['query']}\"")
        print("-" * 40)
        
        result = test_query(query_info)
        results.append(result)
        
        if result['status'] == 'success':
            print(f"✓ Success ({result['response_time']:.2f}s)")
            print(f"Response preview: {result['response'][:200]}...")
        else:
            print(f"✗ {result['status']}: {result['response'][:100]}")
        
        # Small delay between requests
        time.sleep(0.5)
    
    # Save all results
    output_file = f'taxonomy_queries_responses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'total_queries': len(results),
            'successful': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] != 'success'),
            'results': results
        }, f, indent=2)
    
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"Total: {len(results)} queries")
    print(f"Success: {sum(1 for r in results if r['status'] == 'success')}")
    print(f"Failed: {sum(1 for r in results if r['status'] != 'success')}")
    print(f"\nFull results saved to: {output_file}")
    
    # Also create a markdown file with formatted responses
    md_file = f'taxonomy_queries_responses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    with open(md_file, 'w') as f:
        f.write("# Taxonomy Query Test Results\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for result in results:
            f.write(f"## Query {result['id']}: {result['category']}\n\n")
            f.write(f"**Question:** {result['query']}\n\n")
            f.write(f"**Status:** {result['status']}\n\n")
            f.write("**Response:**\n\n")
            f.write(result['response'])
            f.write("\n\n---\n\n")
    
    print(f"Markdown file saved to: {md_file}")

if __name__ == "__main__":
    try:
        # Test if server is running
        test_response = requests.get("http://localhost:8090/api/health", timeout=2)
        if test_response.status_code != 200:
            print("⚠️  Server health check failed")
    except:
        print("✗ Cannot connect to API. Is the Flask server running?")
        print("Start it with: source .venv/bin/activate && python -m src.api.app")
        exit(1)
    
    main()