#!/usr/bin/env python3
"""Test API responses in detail."""

import requests
import json

def test_query_detailed(query):
    """Test a query and show detailed response."""
    url = "http://localhost:8090/api/v1/sendMessage"
    payload = {
        "message": query,
        "conversationId": f"debug-test"
    }
    
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            
            # Check for key terms
            has_limitation = 'limitation' in response_text.lower()
            has_weidinger = 'weidinger' in response_text.lower()
            has_gabriel = 'gabriel' in response_text.lower()
            has_scope = 'scope' in response_text.lower()
            has_boundary = 'boundary' in response_text.lower() or 'boundaries' in response_text.lower()
            
            print(f"Response length: {len(response_text)} chars")
            print(f"Contains 'limitation': {has_limitation}")
            print(f"Contains 'Weidinger': {has_weidinger}")
            print(f"Contains 'Gabriel': {has_gabriel}")
            print(f"Contains 'scope': {has_scope}")
            print(f"Contains 'boundary': {has_boundary}")
            
            # Show first 500 chars of response
            print(f"\nResponse preview:")
            print(response_text[:500])
            
            # Check if it's falling back to synthesis
            if "repository doesn't contain" in response_text.lower() or "cannot provide" in response_text.lower():
                print("\n⚠️ WARNING: Response indicates missing content (shouldn't happen)")
            
            return response_text
        else:
            print(f"Error: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    # Test the problematic queries
    queries = [
        "What are the limitations of this research?",
        "How does this compare to Weidinger framework?",
        "How does this compare to Gabriel et al framework?",
        "Tell me about the limitations section of the preprint",
        "What frameworks are compared in the preprint?"
    ]
    
    for query in queries:
        test_query_detailed(query)

if __name__ == "__main__":
    main()