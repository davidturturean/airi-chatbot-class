#!/usr/bin/env python3
"""
Test Gemini-powered formatting.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.models.gemini import GeminiModel
from src.core.metadata.response_formatter import ResponseFormatter, ResponseMode
from src.config.settings import settings

# Initialize Gemini
print("Initializing Gemini model...")
try:
    gemini = GeminiModel(settings.GEMINI_API_KEY)
    print("✓ Gemini initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize Gemini: {e}")
    sys.exit(1)

# Create formatter with Gemini
formatter = ResponseFormatter(gemini_model=gemini, mode=ResponseMode.STANDARD)

# Test count formatting with Gemini
count_result = [{'count_star()': 371}]
query = "How many risks in domain 7?"

print("\nTesting Gemini count formatting...")
print("-" * 60)

# Add context to make response more interesting
context = {
    'tables': {
        'ai_risk_database_v3': {
            'row_count': 2242,
            'purpose': 'Main AI risk database'
        }
    }
}

formatted = formatter.format_response(
    query=query,
    raw_results=count_result,
    data_context=context,
    debug=False
)

print(f"Query: {query}")
print(f"Raw result: {count_result}")
print(f"\nFormatted response:")
print(formatted.formatted_content)
print(f"\nSummary: {formatted.summary}")
if formatted.visualizations:
    print(f"\nVisualizations:")
    for viz in formatted.visualizations:
        print(viz)

# Test domain list formatting
print("\n\nTesting Gemini list formatting...")
print("-" * 60)

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