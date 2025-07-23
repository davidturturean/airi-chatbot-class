#!/usr/bin/env python3
"""
Test the enhanced response formatter with Gemini integration.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
from src.core.metadata.metadata_service_v2 import flexible_metadata_service
from src.core.metadata.response_formatter import ResponseMode

def test_formatted_responses():
    """Test various queries with the new response formatter."""
    
    print("=" * 80)
    print("TESTING RESPONSE FORMATTER WITH GEMINI")
    print("=" * 80)
    
    # Initialize the service
    print("\n1. Initializing metadata service...")
    start = time.time()
    flexible_metadata_service.initialize(force_reload=False)
    print(f"✓ Initialized in {time.time() - start:.2f}s")
    
    # Test queries with different modes
    test_cases = [
        # Query, Mode, Debug
        ("How many risks are in the database?", ResponseMode.STANDARD, False),
        ("How many risks are in the database?", ResponseMode.EXECUTIVE, False),
        ("List all domains", ResponseMode.STANDARD, False),
        ("Show risks in domain 7", ResponseMode.STANDARD, False),
        ("Show risks in domain 7", ResponseMode.STANDARD, True),  # With debug
    ]
    
    for query, mode, debug in test_cases:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"Mode: {mode.value}")
        print(f"Debug: {debug}")
        print("-" * 60)
        
        start = time.time()
        response, raw_data = flexible_metadata_service.query(query, mode=mode, debug=debug)
        duration = time.time() - start
        
        print(f"\nResponse ({duration:.2f}s):")
        print(response)
        
        print(f"\nRaw data count: {len(raw_data)}")
        if debug:
            print("Debug info included in response above")
        
        print("-" * 60)
        input("Press Enter to continue...")

def test_comparison():
    """Compare old vs new formatting for the same query."""
    
    print("\n" + "=" * 80)
    print("COMPARISON: OLD VS NEW FORMATTING")
    print("=" * 80)
    
    query = "Show risks in domain 7"
    
    # Get raw results
    print(f"\nQuery: {query}")
    
    # Old formatting (by temporarily disabling formatter)
    print("\n--- OLD FORMATTING ---")
    response_old, data = flexible_metadata_service.query(query)
    
    # Show first part of old response
    lines = response_old.split('\n')
    for i, line in enumerate(lines[:20]):
        print(line)
    if len(lines) > 20:
        print(f"... ({len(lines) - 20} more lines)")
    
    # New formatting with Gemini
    print("\n--- NEW FORMATTING (STANDARD MODE) ---")
    response_new, _ = flexible_metadata_service.query(query, mode=ResponseMode.STANDARD)
    print(response_new)
    
    print("\n--- NEW FORMATTING (EXECUTIVE MODE) ---")
    response_exec, _ = flexible_metadata_service.query(query, mode=ResponseMode.EXECUTIVE)
    print(response_exec)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        test_comparison()
    else:
        test_formatted_responses()