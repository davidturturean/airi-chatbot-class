#!/usr/bin/env python3
"""Test that all key preprint content is now retrievable."""

import requests
import json

# Test queries covering different parts of the preprint
TEST_QUERIES = [
    {
        'query': 'How did you use PRISMA methodology?',
        'expected_keywords': ['PRISMA', 'systematic', 'screening'],
        'section': 'Methodology'
    },
    {
        'query': 'How many documents were screened using ASReview?',
        'expected_keywords': ['7,945', '9,343', 'ASReview'],
        'section': 'Screening Process'
    },
    {
        'query': 'What are the limitations of this research?',
        'expected_keywords': ['limitation', 'scope', 'boundary'],
        'section': 'Limitations'
    },
    {
        'query': 'How does this compare to Weidinger framework?',
        'expected_keywords': ['Weidinger', 'taxonomy', 'language model'],
        'section': 'Comparative Analysis'
    },
    {
        'query': 'What future research directions are suggested?',
        'expected_keywords': ['future', 'research', 'direction'],
        'section': 'Future Work'
    },
    {
        'query': 'Describe the search strategy used',
        'expected_keywords': ['search', 'database', 'Scopus'],
        'section': 'Search Strategy'
    },
    {
        'query': 'What was the inclusion and exclusion criteria?',
        'expected_keywords': ['inclusion', 'exclusion', 'criteria'],
        'section': 'Selection Criteria'
    },
    {
        'query': 'How does this compare to Gabriel et al framework?',
        'expected_keywords': ['Gabriel', 'comparison', 'framework'],
        'section': 'Literature Comparison'
    }
]

def test_query(query_info):
    """Test a single query."""
    url = "http://localhost:8090/api/v1/sendMessage"
    payload = {
        "message": query_info['query'],
        "conversationId": f"test-preprint-{query_info['section'].replace(' ', '-').lower()}"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '').lower()
            
            # Check for expected keywords
            found_keywords = []
            for keyword in query_info['expected_keywords']:
                if keyword.lower() in response_text:
                    found_keywords.append(keyword)
            
            return {
                'query': query_info['query'],
                'section': query_info['section'],
                'success': len(found_keywords) > 0,
                'found_keywords': found_keywords,
                'expected_keywords': query_info['expected_keywords'],
                'response_length': len(response_text)
            }
        else:
            return {
                'query': query_info['query'],
                'section': query_info['section'],
                'success': False,
                'error': f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            'query': query_info['query'],
            'section': query_info['section'],
            'success': False,
            'error': str(e)
        }

def main():
    print("=" * 80)
    print("TESTING PREPRINT CONTENT COVERAGE")
    print("=" * 80)
    
    results = []
    
    for query_info in TEST_QUERIES:
        print(f"\nTesting: {query_info['section']}")
        print(f"Query: \"{query_info['query']}\"")
        
        result = test_query(query_info)
        results.append(result)
        
        if result['success']:
            print(f"✅ SUCCESS - Found: {', '.join(result['found_keywords'])}")
            print(f"   Response length: {result['response_length']} chars")
        else:
            if 'error' in result:
                print(f"❌ FAILED - Error: {result['error']}")
            else:
                print(f"❌ FAILED - Expected: {', '.join(result['expected_keywords'])}")
                print(f"   Found: None")
    
    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Results: {successful}/{total} queries successful")
    
    if successful == total:
        print("🎉 ALL PREPRINT CONTENT IS RETRIEVABLE!")
    else:
        print("\nFailed queries:")
        for r in results:
            if not r['success']:
                print(f"  - {r['section']}: {r['query']}")
    
    return successful == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)