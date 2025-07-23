#!/usr/bin/env python3
"""
Test improved responses with Gemini formatting.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata.metadata_service_v2 import flexible_metadata_service
from src.core.metadata.response_formatter import ResponseMode

# Test queries to show improved formatting
test_queries = [
    ("How many risks are in the database?", "Basic count query"),
    ("How many risks in domain 7?", "Count with filtering"),
    ("List all domains", "Enumeration query"),
    ("Count risks by entity type", "Aggregation query"),
    ("Show top 5 risks in domain 7", "Search query with limit"),
]

print("=" * 80)
print("IMPROVED METADATA RESPONSES WITH GEMINI")
print("=" * 80)

# Initialize service
print("\nInitializing metadata service...")
flexible_metadata_service.initialize()

for query, description in test_queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"Type: {description}")
    print("-" * 60)
    
    # Get response
    response, data = flexible_metadata_service.query(query)
    
    print("Response:")
    print(response)
    
    print(f"\nRaw data rows: {len(data)}")
    if len(data) <= 3:
        for row in data:
            print(f"  {row}")
    
    print("-" * 60)
    input("Press Enter for next query...")

# Test different modes for the same query
print("\n" + "=" * 80)
print("TESTING DIFFERENT RESPONSE MODES")
print("=" * 80)

query = "Show risks in domain 7"
modes = [ResponseMode.STANDARD, ResponseMode.EXECUTIVE, ResponseMode.TECHNICAL]

for mode in modes:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"Mode: {mode.value}")
    print("-" * 60)
    
    response, data = flexible_metadata_service.query(query, mode=mode)
    
    print("Response:")
    print(response[:1000])  # First 1000 chars
    if len(response) > 1000:
        print(f"... [{len(response) - 1000} more characters]")
    
    print("-" * 60)