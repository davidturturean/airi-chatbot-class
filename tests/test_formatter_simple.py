#!/usr/bin/env python3
"""
Simple test for response formatter.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.metadata.response_formatter import ResponseFormatter, ResponseMode
from src.config.settings import settings

# Test basic formatter initialization
formatter = ResponseFormatter(mode=ResponseMode.STANDARD)

# Test with a simple count result
count_result = [{'count_star()': 371}]
query = "How many risks in domain 7?"

print("Testing count formatting...")
print("-" * 40)

formatted = formatter.format_response(
    query=query,
    raw_results=count_result,
    debug=False
)

print(f"Query: {query}")
print(f"Raw result: {count_result}")
print(f"\nFormatted response:")
print(formatted.formatted_content)

# Test with domain list
print("\n\nTesting list formatting...")
print("-" * 40)

domain_results = [
    {'domain': '1. Discrimination & Toxicity'},
    {'domain': '2. Privacy & Security'},
    {'domain': '3. Misinformation'},
    {'domain': '4. Malicious Actors & Misuse'},
    {'domain': '5. Human-Computer Interaction'},
    {'domain': '6. Socioeconomic and Environmental'},
    {'domain': '7. AI System Safety, Failures, & Limitations'},
    {'domain': None}
]

query2 = "List all domains"
formatted2 = formatter.format_response(
    query=query2,
    raw_results=domain_results,
    debug=False
)

print(f"Query: {query2}")
print(f"\nFormatted response:")
print(formatted2.formatted_content)