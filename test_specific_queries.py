#!/usr/bin/env python3
"""Test specific problematic queries."""

import requests
import json
import time

def test_query(query, expected_content=None):
    """Test a single query."""
    url = "http://localhost:8090/api/v1/sendMessage"
    payload = {
        "message": query,
        "conversationId": f"test-{int(time.time())}"
    }
    
    print(f"\nQuery: {query}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            
            if expected_content:
                found = any(word.lower() in response_text.lower() for word in expected_content)
                if found:
                    print(f"✅ SUCCESS - Found expected content")
                else:
                    print(f"❌ FAILED - Missing: {expected_content}")
            
            # Check response quality
            if len(response_text) < 200:
                print(f"⚠️  Short response: {len(response_text)} chars")
            else:
                print(f"✅ Response length: {len(response_text)} chars")
            
            # Show preview
            print(f"Preview: {response_text[:300]}...")
            
            return response_text
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    print("=" * 60)
    print("TESTING SPECIFIC PROBLEMATIC QUERIES")
    print("=" * 60)
    
    # Test variations of the problematic queries
    test_queries = [
        # Direct questions
        ("What are the limitations of this research?", ["limitation"]),
        ("What are the limitations of the AI Risk Repository research?", ["limitation"]),
        ("Tell me about research limitations", ["limitation"]),
        
        # Framework comparisons
        ("How does this compare to Weidinger framework?", ["Weidinger"]),
        ("Compare with Weidinger's framework", ["Weidinger"]),
        ("Weidinger framework comparison", ["Weidinger"]),
        
        # Gabriel comparisons
        ("How does this compare to Gabriel et al framework?", ["Gabriel"]),
        ("Gabriel framework comparison", ["Gabriel"]),
        
        # Alternative phrasings that might work
        ("What frameworks are compared in the preprint?", ["Weidinger", "Gabriel"]),
        ("Describe the comparative analysis with other frameworks", ["framework"]),
        ("What are the study boundaries and limitations?", ["limitation", "boundary"])
    ]
    
    for query, expected in test_queries:
        test_query(query, expected)
        time.sleep(1)  # Don't overwhelm the server

if __name__ == "__main__":
    main()