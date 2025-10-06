#!/usr/bin/env python3
"""
Test the query intent analyzer to verify it correctly identifies completeness requirements.
"""

import sys
sys.path.append('.')

from src.core.query.query_intent_analyzer import QueryIntentAnalyzer

def test_intent_analysis():
    """Test query intent analysis for our failing queries."""
    
    analyzer = QueryIntentAnalyzer()
    
    test_queries = [
        "List all 24 subdomains organized by domain",
        "What's the difference between intentional and unintentional risks?",
        "What are the main risk categories in the AI Risk Database v3?",
        "Show me the 7 domains",
        "Explain the taxonomy",
        "Compare human vs AI caused risks"
    ]
    
    print("Query Intent Analysis Results")
    print("=" * 80)
    
    for query in test_queries:
        intent = analyzer.analyze_query(query)
        
        print(f"\nQuery: '{query}'")
        print(f"  Completeness Level: {intent.completeness_level:.2f}")
        print(f"  Query Type: {intent.query_type}")
        print(f"  Enumeration Mode: {intent.enumeration_mode}")
        print(f"  Comparison Mode: {intent.comparison_mode}")
        print(f"  Specificity Markers: {intent.specificity_markers}")
        print(f"  Concepts: {intent.concepts_mentioned[:3] if intent.concepts_mentioned else []}")
        print(f"  Requires Complete Response: {analyzer.requires_complete_response(intent)}")
        print(f"  Detail Level: {analyzer.get_response_detail_level(intent)}")

if __name__ == "__main__":
    test_intent_analysis()