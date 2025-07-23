#!/usr/bin/env python3
"""
Test query type detection.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata.response_formatter import ResponseFormatter, QueryType

# Test query type detection
formatter = ResponseFormatter()

test_queries = [
    "How many risks are in the database?",
    "Count risks by entity type",
    "List all domains",
    "Show top 5 risks in domain 7",
    "Group risks by category",
    "What are the risk categories?",
    "Breakdown by domain"
]

print("Query Type Detection Test:")
print("-" * 60)

for query in test_queries:
    query_type = formatter._detect_query_type(query)
    print(f"{query:45} -> {query_type.value}")

# Test specific aggregate query
print("\n\nTesting aggregate query formatting:")
print("-" * 60)

aggregate_results = [
    {"entity": "2 - AI", "count_star()": 574},
    {"entity": "1 - Human", "count_star()": 539},
    {"entity": None, "count_star()": 631}
]

formatted = formatter.format_response(
    query="Count risks by entity type",
    raw_results=aggregate_results,
    debug=False
)

print(f"Query type detected: {formatted.metadata.query_type.value}")
print(f"Formatted content:\n{formatted.formatted_content}")