#!/usr/bin/env python3
"""
Test domain queries with data context.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata.metadata_service_v2 import flexible_metadata_service

# Initialize
print("Initializing...")
flexible_metadata_service.initialize()

# Test domain queries
queries = [
    "List all domains",
    "How many risks are in domain 7?",
    "Show risks in domain 7. AI System Safety, Failures, & Limitations"
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    response, data = flexible_metadata_service.query(query)
    print(f"Response: {response}")
    if data and len(data) <= 5:
        print(f"Data ({len(data)} rows):")
        for row in data:
            print(f"  {row}")
    elif data:
        print(f"Data: {len(data)} rows (showing first 3)")
        for row in data[:3]:
            print(f"  {row}")