#!/usr/bin/env python3
"""
Test script to run 105 prompts through the full AIRI chatbot pipeline
Simulates the exact flow as if queries were sent through the web interface
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.services.chat_service import ChatService
from src.core.models.gemini import GeminiModel
from src.core.storage.vector_store import VectorStore
from src.core.query.monitor import QueryMonitor
from src.config.settings import settings
from src.config.logging import get_logger

logger = get_logger(__name__)

def load_test_prompts(file_path):
    """Load test prompts from JSON file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data.get('prompts', [])

def initialize_services():
    """Initialize all services as done in the web app"""
    print("Initializing services...")
    
    # Initialize Gemini model
    gemini_model = GeminiModel(settings.GEMINI_API_KEY)
    
    # Initialize vector store
    vector_store = VectorStore()
    vector_store.initialize()
    
    # Initialize query monitor
    query_monitor = QueryMonitor(gemini_model)
    
    # Initialize chat service with all dependencies
    chat_service = ChatService(
        gemini_model=gemini_model,
        vector_store=vector_store,
        query_monitor=query_monitor
    )
    
    print("Services initialized successfully!")
    return chat_service

def process_prompt(chat_service, prompt_data, conversation_id="test-session"):
    """Process a single prompt through the full pipeline"""
    prompt = prompt_data['prompt']
    expected_domain = prompt_data.get('expected_domain', 'unknown')
    
    try:
        # Process through chat service - this is the exact same flow as the API
        response_text, docs = chat_service.process_query(prompt, conversation_id)
        
        # Extract actual domain from the processing
        # The domain is determined in the query processor
        actual_domain = "unknown"
        if hasattr(chat_service.query_processor, 'session_queries'):
            # Try to get the domain from the last analysis
            query_type, domain = chat_service.query_processor.analyze_query(prompt, conversation_id)
            actual_domain = domain if domain else "unknown"
        
        # Determine if documents were retrieved
        has_docs = len(docs) > 0
        
        # Check if response indicates out-of-scope
        is_out_of_scope = any(phrase in response_text for phrase in [
            "doesn't contain information about",
            "I specialize in AI risks",
            "Try asking about",
            "doesn't have information on"
        ])
        
        result = {
            'prompt': prompt,
            'expected_domain': expected_domain,
            'actual_domain': actual_domain,
            'response_preview': response_text[:200] + '...' if len(response_text) > 200 else response_text,
            'has_documents': has_docs,
            'doc_count': len(docs),
            'is_out_of_scope': is_out_of_scope,
            'response_length': len(response_text),
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error processing prompt: {str(e)}")
        result = {
            'prompt': prompt,
            'expected_domain': expected_domain,
            'actual_domain': 'error',
            'error': str(e),
            'success': False
        }
    
    return result

def analyze_results(results):
    """Analyze test results and print summary"""
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    
    # Domain accuracy
    domain_matches = sum(1 for r in results if r.get('success') and r['expected_domain'] == r['actual_domain'])
    
    # Out-of-scope analysis
    out_of_scope = sum(1 for r in results if r.get('is_out_of_scope', False))
    
    # Document retrieval
    with_docs = sum(1 for r in results if r.get('has_documents', False))
    
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    print(f"Total prompts tested: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"\nDomain Classification:")
    print(f"  Correct: {domain_matches}/{successful} ({domain_matches/successful*100:.1f}%)")
    print(f"\nDocument Retrieval:")
    print(f"  With documents: {with_docs}")
    print(f"  Out-of-scope: {out_of_scope}")
    
    # Domain breakdown
    print("\nDomain Distribution:")
    domain_counts = {}
    for r in results:
        if r.get('success'):
            domain = r['actual_domain']
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    for domain, count in sorted(domain_counts.items()):
        print(f"  {domain}: {count}")
    
    # Error analysis
    if failed > 0:
        print("\nErrors:")
        for r in results:
            if not r['success']:
                print(f"  Prompt: {r['prompt'][:50]}...")
                print(f"  Error: {r.get('error', 'Unknown error')}")

def save_detailed_results(results, output_file):
    """Save detailed results to JSON file"""
    output_data = {
        'test_date': datetime.now().isoformat(),
        'total_prompts': len(results),
        'results': results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")

def main():
    """Main test execution"""
    # Load test prompts
    prompts_file = project_root / "data" / "test_prompts_105.json"
    if not prompts_file.exists():
        print(f"Error: Test prompts file not found at {prompts_file}")
        print("Please ensure the test_prompts_105.json file is in the data directory")
        return
    
    prompts = load_test_prompts(prompts_file)
    print(f"Loaded {len(prompts)} test prompts")
    
    # Initialize services
    chat_service = initialize_services()
    
    # Process all prompts
    results = []
    print("\nProcessing prompts...")
    for i, prompt_data in enumerate(prompts, 1):
        print(f"\rProcessing prompt {i}/{len(prompts)}", end='', flush=True)
        result = process_prompt(chat_service, prompt_data)
        results.append(result)
        
        # Reset conversation every 10 prompts to avoid context buildup
        if i % 10 == 0:
            chat_service.reset_conversation("test-session")
    
    print("\n\nProcessing complete!")
    
    # Analyze results
    analyze_results(results)
    
    # Save detailed results
    output_file = project_root / f"test_results_105_prompts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_detailed_results(results, output_file)
    
    # Print a few example results
    print("\n" + "="*80)
    print("EXAMPLE RESULTS (First 5)")
    print("="*80)
    for i, result in enumerate(results[:5], 1):
        print(f"\n{i}. Prompt: {result['prompt']}")
        print(f"   Expected: {result['expected_domain']}, Actual: {result.get('actual_domain', 'N/A')}")
        print(f"   Documents: {result.get('doc_count', 0)}, Out-of-scope: {result.get('is_out_of_scope', False)}")
        if result.get('success'):
            print(f"   Response preview: {result.get('response_preview', 'N/A')}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()