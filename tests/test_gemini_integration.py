#!/usr/bin/env python3
"""
Test Gemini integration in metadata service.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force fresh import to get new initialization
if 'src.core.metadata.metadata_service_v2' in sys.modules:
    del sys.modules['src.core.metadata.metadata_service_v2']

from src.core.metadata.metadata_service_v2 import flexible_metadata_service

print("Testing Gemini Integration")
print("=" * 60)

# Initialize service (should now have Gemini)
print("Initializing metadata service with Gemini...")
flexible_metadata_service.initialize()

# Check if Gemini is available
has_gemini = flexible_metadata_service.response_formatter.gemini_model is not None
print(f"Gemini model available: {has_gemini}")

if has_gemini:
    # Test count query with Gemini
    print("\n1. Count query (should use Gemini):")
    print("-" * 40)
    response, _ = flexible_metadata_service.query("How many risks in domain 7?")
    print(response)
    
    # Test list query
    print("\n2. List query (should use Gemini):")
    print("-" * 40)
    response, _ = flexible_metadata_service.query("List all domains")
    print(response)
    
    # Test aggregate query
    print("\n3. Aggregate query (should use Gemini):")
    print("-" * 40)
    response, _ = flexible_metadata_service.query("Count risks by entity type")
    print(response)
else:
    print("WARNING: Gemini not available, using fallback formatting")