#!/usr/bin/env python3
"""Test the actual API endpoint with taxonomy query."""

import requests
import json

# API endpoint
url = "http://localhost:5001/api/chat"

# Test query
payload = {
    "message": "What are the main risk categories in the AI Risk Database v3?",
    "conversation_id": "test-taxonomy-123",
    "session_id": "test-session-456"
}

print("Testing taxonomy query via API...")
print(f"Query: {payload['message']}")
print("-" * 50)

try:
    # Send request
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        
        # Check the response
        response_text = data.get('response', '')
        
        print("✓ API responded successfully")
        print(f"Response length: {len(response_text)} characters")
        
        # Check for key content
        checks = {
            "Contains '7 domains'": "7 domains" in response_text or "seven domains" in response_text.lower(),
            "Contains '24 subdomains'": "24 subdomain" in response_text,
            "Contains 'Discrimination'": "Discrimination" in response_text,
            "Contains 'Privacy'": "Privacy" in response_text,
            "Contains 'Misinformation'": "Misinformation" in response_text,
            "Contains 'Socioeconomic'": "Socioeconomic" in response_text or "socioeconomic" in response_text,
            "Contains 'Human-Computer'": "Human-Computer" in response_text or "human-computer" in response_text,
            "Contains percentages": "%" in response_text,
            "Is structured response": "##" in response_text or "###" in response_text
        }
        
        print("\nContent checks:")
        all_passed = True
        for check, result in checks.items():
            status = "✓" if result else "✗"
            print(f"  {status} {check}")
            if not result:
                all_passed = False
        
        print("\nFirst 1000 characters of response:")
        print("-" * 50)
        print(response_text[:1000])
        print("-" * 50)
        
        if all_passed:
            print("\n✅ SUCCESS: Taxonomy query is working properly!")
        else:
            print("\n⚠️  WARNING: Response missing expected content")
            
    else:
        print(f"✗ API error: Status {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("✗ Cannot connect to API. Is the Flask server running?")
    print("Start it with: source .venv/bin/activate && python -m src.api.app")
except Exception as e:
    print(f"✗ Error: {e}")