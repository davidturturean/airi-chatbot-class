#!/usr/bin/env python3
"""
Test script to verify preprint integration and methodology query handling.
"""

import sys
import json
from datetime import datetime
from typing import Dict, List, Any

sys.path.append('.')

from src.core.storage.vector_store import VectorStore
from src.core.query.intent_classifier import IntentClassifier
from src.core.taxonomy.taxonomy_handler import TaxonomyHandler
from src.core.query.query_intent_analyzer import QueryIntentAnalyzer
from src.core.retrieval.advanced_retrieval import AdvancedRetriever
from src.config.logging import get_logger

logger = get_logger(__name__)

def test_preprint_retrieval():
    """Test that preprint content is retrievable from vector store."""
    print("\n" + "="*60)
    print("TESTING PREPRINT CONTENT RETRIEVAL")
    print("="*60)
    
    # Initialize vector store
    vector_store = VectorStore()
    success = vector_store.initialize()
    
    if not success:
        print("❌ Failed to initialize vector store")
        return False
    
    print(f"✅ Vector store initialized")
    
    # Test queries that need preprint content
    methodology_queries = [
        {
            'query': 'What systematic review methodology was used?',
            'expected_terms': ['PRISMA', 'systematic review', 'screening'],
            'description': 'Should describe PRISMA methodology'
        },
        {
            'query': 'How many documents were analyzed in the AI Risk Repository?',
            'expected_terms': ['777', 'documents', 'analyzed'],
            'description': 'Should mention 777 documents'
        },
        {
            'query': 'Who are the authors of the AI Risk Repository preprint?',
            'expected_terms': ['Slattery', 'authors'],
            'description': 'Should mention Slattery et al'
        },
        {
            'query': 'What are the limitations of the AI Risk Repository taxonomy?',
            'expected_terms': ['limitation', 'taxonomy'],
            'description': 'Should discuss taxonomy limitations'
        },
        {
            'query': 'What coverage did Gabriel et al provide in their review?',
            'expected_terms': ['Gabriel', 'coverage', 'review'],
            'description': 'Should mention Gabriel et al coverage'
        }
    ]
    
    results = []
    preprint_found_count = 0
    
    print("\nTesting methodology queries:")
    print("-" * 40)
    
    for test in methodology_queries:
        query = test['query']
        expected = test['expected_terms']
        
        # Get relevant documents
        docs = vector_store.get_relevant_documents(query, k=5)
        
        # Check if we got relevant content
        found_terms = []
        preprint_content_found = False
        
        if docs:
            # Combine content from top docs
            combined_content = " ".join([doc.page_content[:500] for doc in docs[:3]])
            
            # Check for expected terms
            for term in expected:
                if term.lower() in combined_content.lower():
                    found_terms.append(term)
            
            # Check if this looks like preprint content
            preprint_indicators = ['systematic', 'prisma', '777', 'slattery', 'methodology', 'meta-review']
            if any(ind in combined_content.lower() for ind in preprint_indicators):
                preprint_content_found = True
                preprint_found_count += 1
        
        # Calculate match percentage
        match_percentage = (len(found_terms) / len(expected)) * 100 if expected else 0
        
        result = {
            'query': query,
            'success': match_percentage >= 50,
            'match_percentage': match_percentage,
            'found_terms': found_terms,
            'expected_terms': expected,
            'preprint_content': preprint_content_found,
            'description': test['description']
        }
        results.append(result)
        
        # Print result
        status = "✅" if result['success'] else "❌"
        preprint_status = "📄" if preprint_content_found else "❓"
        print(f"{status} {preprint_status} {query[:50]}...")
        print(f"   Found terms: {found_terms}")
        print(f"   Match: {match_percentage:.0f}%")
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Success rate: {successful}/{total} ({(successful/total)*100:.0f}%)")
    print(f"Preprint content found: {preprint_found_count}/{total} queries")
    
    # Save detailed results
    results_file = "preprint_integration_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total,
                'successful': successful,
                'preprint_found': preprint_found_count,
                'success_rate': f"{(successful/total)*100:.0f}%"
            },
            'results': results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    return successful == total

def test_full_pipeline():
    """Test the full query pipeline with preprint content."""
    print("\n" + "="*60)
    print("TESTING FULL QUERY PIPELINE")
    print("="*60)
    
    # Initialize components
    vector_store = VectorStore()
    if not vector_store.initialize():
        print("❌ Failed to initialize vector store")
        return False
    
    intent_classifier = IntentClassifier()
    taxonomy_handler = TaxonomyHandler()
    query_analyzer = QueryIntentAnalyzer()
    
    # Test complex queries
    test_queries = [
        "Explain the complete methodology used in the AI Risk Repository systematic review",
        "How many documents were analyzed and what was the screening process?",
        "Compare the AI Risk Repository with Gabriel et al's review",
        "What are all the limitations mentioned in the preprint?",
        "List all 24 subdomains with their associated statistics"
    ]
    
    print("\nTesting full pipeline responses:")
    print("-" * 40)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Classify intent
        intent = intent_classifier.classify_intent(query)
        print(f"Intent: {intent.category.value}")
        
        # Analyze query for completeness
        query_intent = query_analyzer.analyze(query)
        print(f"Completeness required: {query_intent.completeness_level:.1f}")
        
        # Handle taxonomy queries specially
        from src.core.query.intent_classifier import IntentCategory
        if intent.category == IntentCategory.TAXONOMY_QUERY:
            response = taxonomy_handler.get_adaptive_response(query, query_intent)
            if response:
                print(f"Response preview: {response[:200]}...")
                continue
        
        # Get relevant documents for other queries
        docs = vector_store.get_relevant_documents(query, k=5)
        if docs:
            print(f"Retrieved {len(docs)} documents")
            # Check for preprint content
            preprint_found = any('preprint' in str(doc.metadata).lower() or 
                               'systematic' in doc.page_content.lower() 
                               for doc in docs[:2])
            print(f"Preprint content: {'✅ Found' if preprint_found else '❌ Not found'}")
    
    print("\n" + "="*60)
    print("Full pipeline test complete")
    
    return True

def main():
    """Run all preprint integration tests."""
    print("\n" + "="*60)
    print("PREPRINT INTEGRATION TEST SUITE")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run tests
    retrieval_success = test_preprint_retrieval()
    pipeline_success = test_full_pipeline()
    
    # Overall result
    print("\n" + "="*60)
    print("OVERALL RESULTS")
    print("="*60)
    
    if retrieval_success and pipeline_success:
        print("✅ ALL TESTS PASSED - Preprint fully integrated!")
    else:
        print("⚠️ Some tests failed:")
        if not retrieval_success:
            print("  - Preprint retrieval needs improvement")
        if not pipeline_success:
            print("  - Pipeline integration needs work")
    
    return retrieval_success and pipeline_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)