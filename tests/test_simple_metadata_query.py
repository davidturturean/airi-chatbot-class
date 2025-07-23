#!/usr/bin/env python3
"""
Test a simple metadata query.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata.metadata_service_v2 import flexible_metadata_service

# Initialize
print("Initializing...")
flexible_metadata_service.initialize()

# Test simple query
query = "How many risks are in the database?"
print(f"\nQuery: {query}")
response, data = flexible_metadata_service.query(query)
print(f"Response: {response}")
print(f"Data: {data}")