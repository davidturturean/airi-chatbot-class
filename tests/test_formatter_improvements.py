#!/usr/bin/env python3
"""
Test improved formatter functionality.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata.metadata_service_v2 import flexible_metadata_service
from src.core.metadata.response_formatter import ResponseMode

# Test specific problematic queries
print("=" * 80)
print("TESTING FORMATTER IMPROVEMENTS")
print("=" * 80)

# Initialize
print("\nInitializing...")
flexible_metadata_service.initialize()

# Test 1: Aggregation with nulls
print("\n1. Testing aggregation formatting...")
print("-" * 60)
response, data = flexible_metadata_service.query("Count risks by entity type")
print("Response:")
print(response)

# Test 2: Domain list (should be sorted)
print("\n\n2. Testing domain list (should be sorted)...")
print("-" * 60)
response, data = flexible_metadata_service.query("List all domains")
print("Response:")
print(response)

# Test 3: Top N query
print("\n\n3. Testing top N query...")
print("-" * 60)
response, data = flexible_metadata_service.query("Show top 5 risks in domain 7")
print("Response (first 1000 chars):")
print(response[:1000])
if len(response) > 1000:
    print(f"... [{len(response) - 1000} more characters]")
print(f"\nRaw data sample:")
for i, row in enumerate(data[:2]):
    print(f"Row {i+1} keys: {list(row.keys())[:5]}...")

# Test 4: Count with Gemini formatting
print("\n\n4. Testing count with context...")
print("-" * 60)
response, data = flexible_metadata_service.query("How many risks in domain 7?", debug=True)
print("Response:")
print(response)