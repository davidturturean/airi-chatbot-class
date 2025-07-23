#!/usr/bin/env python3
"""
Final test of all formatting improvements.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata.metadata_service_v2 import flexible_metadata_service
from src.core.metadata.response_formatter import ResponseMode

print("=" * 80)
print("FINAL FORMATTING TEST - ALL QUERY TYPES")
print("=" * 80)

# Initialize
print("\nInitializing with Gemini...")
flexible_metadata_service.initialize()

# Test all query types
queries = [
    ("How many risks are in the database?", "COUNT"),
    ("List all domains", "LIST"),
    ("Count risks by entity type", "AGGREGATE"),
    ("Show top 3 risks in domain 7", "SEARCH"),
]

for query, query_type in queries:
    print(f"\n{'='*60}")
    print(f"Query Type: {query_type}")
    print(f"Query: {query}")
    print("-" * 60)
    
    response, data = flexible_metadata_service.query(query)
    
    # Show response
    if len(response) > 1000:
        print(response[:1000])
        print(f"\n... [{len(response) - 1000} more characters]")
    else:
        print(response)
    
    print(f"\n[Data rows: {len(data)}]")

# Test different modes
print("\n\n" + "=" * 80)
print("TESTING RESPONSE MODES")
print("=" * 80)

query = "How many risks in domain 7?"

for mode in [ResponseMode.STANDARD, ResponseMode.EXECUTIVE]:
    print(f"\n{'='*60}")
    print(f"Mode: {mode.value}")
    print(f"Query: {query}")
    print("-" * 60)
    
    response, _ = flexible_metadata_service.query(query, mode=mode)
    print(response)