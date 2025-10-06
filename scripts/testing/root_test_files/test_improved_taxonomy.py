#!/usr/bin/env python3
"""
Test the improved taxonomy handling with semantic query intent analysis.
Focus on the two previously failing queries.
"""

import json
from src.core.services.chat_service import ChatService
from src.config.settings import Settings
from src.core.query.query_intent_analyzer import QueryIntentAnalyzer

def test_failing_queries():
    """Test the queries that were previously failing."""
    
    # Initialize services
    settings = Settings()
    chat_service = ChatService(settings)
    intent_analyzer = QueryIntentAnalyzer()
    
    # Define test queries
    test_queries = [
        {
            'id': 5,
            'query': "List all 24 subdomains organized by domain",
            'expected_elements': ['Discrimination & bias', 'Privacy violations', 'Fraud & deception', 
                                 'Overreliance on AI', 'Environmental impacts', 'Performance issues', 
                                 'Existential risks']
        },
        {
            'id': 11, 
            'query': "What's the difference between intentional and unintentional risks?",
            'expected_elements': ['Intentional', 'Unintentional', 'expected outcome', 
                                 'unexpected outcome', '34%', '35%']
        },
        # Additional test to verify the main query still works
        {
            'id': 7,
            'query': "What are the main risk categories in the AI Risk Database v3?",
            'expected_elements': ['Causal Taxonomy', 'Domain Taxonomy', '7 domains']
        }
    ]
    
    results = []
    
    for test in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing Query {test['id']}: {test['query']}")
        print(f"{'='*60}")
        
        # Analyze query intent
        intent = intent_analyzer.analyze_query(test['query'])
        print(f"\nIntent Analysis:")
        print(f"  - Completeness Level: {intent.completeness_level:.2f}")
        print(f"  - Query Type: {intent.query_type}")
        print(f"  - Enumeration Mode: {intent.enumeration_mode}")
        print(f"  - Comparison Mode: {intent.comparison_mode}")
        print(f"  - Concepts Mentioned: {intent.concepts_mentioned}")
        
        # Get response from chat service
        try:
            response = chat_service.get_response(test['query'], session_id='test')
            response_text = response['response']
            
            # Check for expected elements
            missing_elements = []
            for element in test['expected_elements']:
                if element.lower() not in response_text.lower():
                    missing_elements.append(element)
            
            # Determine pass/fail
            passed = len(missing_elements) == 0
            
            print(f"\nResponse Length: {len(response_text)} characters")
            print(f"Result: {'PASS' if passed else 'FAIL'}")
            if missing_elements:
                print(f"Missing Elements: {missing_elements}")
            
            # Show first 500 chars of response
            print(f"\nResponse Preview:")
            print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
            
            # Store result
            results.append({
                'test_id': test['id'],
                'query': test['query'],
                'passed': passed,
                'missing_elements': missing_elements,
                'response_length': len(response_text),
                'intent_analysis': {
                    'completeness_level': intent.completeness_level,
                    'query_type': intent.query_type,
                    'enumeration_mode': intent.enumeration_mode,
                    'comparison_mode': intent.comparison_mode
                }
            })
            
        except Exception as e:
            print(f"Error: {str(e)}")
            results.append({
                'test_id': test['id'],
                'query': test['query'],
                'passed': False,
                'error': str(e)
            })
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.get('passed', False))
    
    print(f"Tests Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.0f}%)")
    
    for result in results:
        status = "✓ PASS" if result.get('passed', False) else "✗ FAIL"
        print(f"{status} - Test {result['test_id']}: {result['query'][:50]}...")
        if not result.get('passed', False):
            if 'error' in result:
                print(f"       Error: {result['error']}")
            elif result.get('missing_elements'):
                print(f"       Missing: {', '.join(result['missing_elements'][:3])}...")
    
    # Save results
    with open('improved_taxonomy_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = test_failing_queries()
    exit(0 if success else 1)