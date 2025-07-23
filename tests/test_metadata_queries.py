#!/usr/bin/env python3
"""
Test script for metadata and technical query features.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata import metadata_service
from src.core.query.intent_classifier import intent_classifier
from src.core.query.technical_handler import get_technical_handler
from src.config.logging import get_logger

logger = get_logger(__name__)

def test_metadata_queries():
    """Test various metadata queries."""
    print("\n" + "="*50)
    print("TESTING METADATA QUERIES")
    print("="*50)
    
    # Initialize metadata service
    print("\nInitializing metadata service...")
    metadata_service.initialize()
    
    # Test queries
    test_queries = [
        "How many risks are in the database?",
        "What are the main risk categories?",
        "List all domains in the repository",
        "How many risks in domain 7?",
        "What is the earliest publication year?",
        "Show me risks with entity type AI",
        "Count risks by domain",
        "What is the 6th risk in the database?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 50)
        
        # Test intent classification
        intent_result = intent_classifier.classify_intent(query)
        print(f"Intent: {intent_result.category.value} (confidence: {intent_result.confidence:.2f})")
        
        # Execute metadata query
        try:
            response, raw_results = metadata_service.query(query)
            print(f"\n📝 Response:\n{response}")
            
            if raw_results:
                print(f"\n📊 Raw results count: {len(raw_results)}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def test_technical_queries():
    """Test technical AI queries."""
    print("\n" + "="*50)
    print("TESTING TECHNICAL AI QUERIES")
    print("="*50)
    
    # Get technical handler
    technical_handler = get_technical_handler()
    
    # Test queries
    test_queries = [
        "How do transformer architectures work?",
        "Explain attention mechanism in neural networks",
        "What is backpropagation in deep learning?",
        "How does BERT work?",
        "Explain vision transformers"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 50)
        
        # Test intent classification
        intent_result = intent_classifier.classify_intent(query)
        print(f"Intent: {intent_result.category.value} (confidence: {intent_result.confidence:.2f})")
        
        # Execute technical query (using mock results since we don't have web search in test)
        try:
            response, sources = technical_handler.handle_technical_query(query)
            print(f"\n📝 Response:\n{response}")
            
            if sources:
                print(f"\n📚 Sources found: {len(sources)}")
                for i, source in enumerate(sources, 1):
                    print(f"  [{i}] {source.title}")
                    
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def test_intent_classification():
    """Test intent classification for various query types."""
    print("\n" + "="*50)
    print("TESTING INTENT CLASSIFICATION")
    print("="*50)
    
    test_cases = [
        # Metadata queries
        ("How many risks are there?", "metadata_query"),
        ("List all risk categories", "metadata_query"),
        ("What's the total count of entries?", "metadata_query"),
        
        # Technical queries
        ("How do transformers work?", "technical_ai"),
        ("Explain neural network architecture", "technical_ai"),
        ("What is deep learning?", "technical_ai"),
        
        # Repository queries
        ("What are the privacy risks of AI?", "repository_related"),
        ("Tell me about bias in machine learning", "repository_related"),
        
        # Cross-database queries
        ("Show risks with their mitigations", "cross_database"),
        
        # General/rejected queries
        ("What's the weather today?", "general_knowledge"),
        ("How do I bake cookies?", "general_knowledge"),
        ("Hello", "chit_chat"),
    ]
    
    for query, expected_category in test_cases:
        intent_result = intent_classifier.classify_intent(query)
        status = "✅" if intent_result.category.value == expected_category else "❌"
        print(f"{status} '{query}' -> {intent_result.category.value} (expected: {expected_category})")
        print(f"   Confidence: {intent_result.confidence:.2f}, Reasoning: {intent_result.reasoning}")

def main():
    """Run all tests."""
    print("🚀 Starting metadata and technical query tests...")
    
    # Test intent classification first
    test_intent_classification()
    
    # Test metadata queries
    test_metadata_queries()
    
    # Test technical queries
    test_technical_queries()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()