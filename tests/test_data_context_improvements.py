#!/usr/bin/env python3
"""
Test the improved metadata system with data context.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
from src.core.metadata.metadata_service_v2 import flexible_metadata_service
from src.core.query.intent_classifier import intent_classifier

def test_metadata_queries():
    """Test various metadata queries with full data context."""
    
    print("=" * 80)
    print("TESTING METADATA SYSTEM WITH DATA CONTEXT")
    print("=" * 80)
    
    # Initialize the service
    print("\n1. Initializing metadata service...")
    start = time.time()
    flexible_metadata_service.initialize(force_reload=True)
    print(f"✓ Initialized in {time.time() - start:.2f}s")
    
    # Test queries
    test_queries = [
        # Basic queries
        ("How many risks are in the database?", "Should count all risks"),
        ("What are the main risk categories?", "Should list distinct categories"),
        ("List all domains", "Should show all domains"),
        
        # Specific domain queries
        ("How many risks are in domain 7?", "Should find domain '7. AI System Safety...'"),
        ("Show risks in domain 7", "Should filter by domain 7"),
        
        # Entity queries
        ("Count risks by entity type", "Should group by entity (1=Human, 2=AI)"),
        ("How many AI entity risks?", "Should filter entity=2"),
        
        # Year queries
        ("What is the earliest publication year?", "Should find minimum year"),
        ("Show risks from 2024", "Should filter by year 2024"),
        
        # Complex queries
        ("List the top 5 risk categories by count", "Should aggregate and order"),
        ("Show domain 7 risks with entity type 2", "Should combine filters"),
    ]
    
    print(f"\n2. Testing {len(test_queries)} queries with data context...")
    print("-" * 80)
    
    for query, expected in test_queries:
        print(f"\nQuery: {query}")
        print(f"Expected: {expected}")
        
        # First classify intent
        start = time.time()
        intent = intent_classifier.classify_intent(query)
        classify_time = time.time() - start
        print(f"Intent: {intent.category.value} (confidence: {intent.confidence:.2f}) in {classify_time:.2f}s")
        
        if intent.should_process and intent.category.value == "metadata_query":
            # Execute query
            start = time.time()
            response, data = flexible_metadata_service.query(query)
            query_time = time.time() - start
            
            print(f"Response ({query_time:.2f}s):")
            print(response)
            
            if data:
                print(f"Data rows: {len(data)}")
                if len(data) <= 3:
                    for row in data:
                        print(f"  {row}")
        else:
            print(f"Skipped: Intent={intent.category.value}, should_process={intent.should_process}")
        
        print("-" * 40)
    
    # Show data context summary
    print("\n3. Data Context Summary:")
    if flexible_metadata_service._data_context:
        context = flexible_metadata_service._data_context
        print(f"Tables analyzed: {len(context['tables'])}")
        for table_name, info in list(context['tables'].items())[:5]:
            print(f"\n  {table_name}:")
            print(f"    Rows: {info['row_count']:,}")
            print(f"    Purpose: {info['purpose']}")
            print(f"    Key columns: {', '.join(info['primary_columns'][:5])}")

if __name__ == "__main__":
    test_metadata_queries()