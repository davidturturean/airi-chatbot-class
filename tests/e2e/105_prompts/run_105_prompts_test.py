#!/usr/bin/env python3
"""
Run the 105 prompts test from the previous stakeholder test results
Tests the updated domain classification and response generation logic
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.services.chat_service import ChatService
from src.core.models.gemini import GeminiModel
from src.core.storage.vector_store import VectorStore
from src.core.query.monitor import Monitor
from src.config.settings import settings
from src.config.logging import get_logger

logger = get_logger(__name__)

def load_test_queries():
    """Load the 105 test queries from the previous test results"""
    test_file = Path(__file__).parent / "stakeholder_test_results_20250722_202329.json"
    
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    # Extract queries and metadata from the detailed results
    queries = []
    for result in data['detailed_results']:
        queries.append({
            'query_num': result['query_num'],
            'query': result['query'],
            'stakeholder': result['stakeholder'],
            'category': result['category'],
            'complexity': result['complexity']
        })
    
    return queries

def initialize_services():
    """Initialize all services as done in the web app"""
    print("Initializing services...")
    
    # Initialize Gemini model with fallback support
    gemini_model = GeminiModel(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL_NAME,
        use_fallback=True
    )
    
    # Initialize vector store with proper parameters
    vector_store = VectorStore(
        api_key=settings.GEMINI_API_KEY,
        repository_path=str(settings.INFO_FILES_DIR),
        persist_directory=str(settings.CHROMA_DB_DIR),
        use_hybrid_search=settings.USE_HYBRID_SEARCH
    )
    
    # Initialize query monitor
    query_monitor = Monitor(settings.GEMINI_API_KEY)
    
    # Initialize chat service with all dependencies
    chat_service = ChatService(
        gemini_model=gemini_model,
        vector_store=vector_store,
        query_monitor=query_monitor
    )
    
    print("Services initialized successfully!")
    return chat_service

def process_query(chat_service, query_data, conversation_id="test-session", verbose=True):
    """Process a single query through the updated pipeline"""
    query = query_data['query']
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"QUERY #{query_data['query_num']} - {query_data['stakeholder']} ({query_data['category']})")
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
    
    # Log query details for debugging
    logger.info(f"=== PROCESSING QUERY #{query_data['query_num']} ===")
    logger.info(f"Query: {query}")
    logger.info(f"Stakeholder: {query_data['stakeholder']}")
    logger.info(f"Category: {query_data['category']}")
    
    start_time = time.time()
    
    try:
        # Process through chat service - this uses the updated logic
        response_text, docs = chat_service.process_query(query, conversation_id)
        
        # Get domain classification from the query processor
        query_type, domain = chat_service.query_processor.analyze_query(query, conversation_id)
        
        # Log backend processing details
        logger.info(f"Domain classified: {domain}")
        logger.info(f"Query type: {query_type}")
        logger.info(f"Documents retrieved: {len(docs)}")
        if docs:
            # Handle both regular documents and technical sources
            doc_info = []
            for doc in docs[:5]:
                if hasattr(doc, 'metadata'):
                    doc_info.append(doc.metadata.get('rid', 'N/A'))
                elif hasattr(doc, 'title'):
                    doc_info.append(f"Tech: {doc.title[:30]}")
                else:
                    doc_info.append('Unknown')
            logger.info(f"Document RIDs: {doc_info}")
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Analyze response quality
        has_citations = 'RID-' in response_text
        is_out_of_scope = any(phrase in response_text for phrase in [
            "doesn't contain information about",
            "I specialize in AI risks",
            "Try asking about",
            "doesn't have information on"
        ])
        
        if verbose:
            print(f"\nDomain: {domain}")
            print(f"Query Type: {query_type}")
            print(f"Documents Found: {len(docs)}")
            print(f"Response Time: {response_time:.2f}s")
            print(f"Out of Scope: {is_out_of_scope}")
            print(f"\nFULL RESPONSE:")
            print(f"{'-'*80}")
            print(response_text)
            print(f"{'-'*80}")
        
        result = {
            'query_num': query_data['query_num'],
            'query': query,
            'stakeholder': query_data['stakeholder'],
            'category': query_data['category'],
            'complexity': query_data['complexity'],
            'domain_classified': domain,
            'query_type': query_type,
            'response_length': len(response_text),
            'response_time': response_time,
            'documents_found': len(docs),
            'has_citations': has_citations,
            'is_out_of_scope': is_out_of_scope,
            'response_full': response_text,  # Store full response
            'response_preview': response_text[:300] + '...' if len(response_text) > 300 else response_text,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error processing query {query_data['query_num']}: {str(e)}")
        if verbose:
            print(f"\nERROR: {str(e)}")
        result = {
            'query_num': query_data['query_num'],
            'query': query,
            'error': str(e),
            'success': False
        }
    
    return result

def analyze_results(results):
    """Analyze and summarize test results"""
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    
    # Domain distribution
    domain_counts = {}
    for r in results:
        if r.get('success') and r.get('domain_classified'):
            domain = r['domain_classified']
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    # Response metrics
    avg_response_time = sum(r.get('response_time', 0) for r in results if r.get('success')) / max(successful, 1)
    avg_response_length = sum(r.get('response_length', 0) for r in results if r.get('success')) / max(successful, 1)
    
    # Quality metrics
    with_citations = sum(1 for r in results if r.get('has_citations', False))
    out_of_scope = sum(1 for r in results if r.get('is_out_of_scope', False))
    with_docs = sum(1 for r in results if r.get('documents_found', 0) > 0)
    
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY - 105 PROMPTS TEST")
    print("="*80)
    print(f"Total queries: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    print(f"\nPerformance Metrics:")
    print(f"  Average response time: {avg_response_time:.2f}s")
    print(f"  Average response length: {avg_response_length:.0f} chars")
    
    print(f"\nQuality Metrics:")
    print(f"  With citations: {with_citations} ({with_citations/successful*100:.1f}%)")
    print(f"  With documents: {with_docs} ({with_docs/successful*100:.1f}%)")
    print(f"  Out of scope: {out_of_scope} ({out_of_scope/successful*100:.1f}%)")
    
    print(f"\nDomain Classification Distribution:")
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {domain}: {count} ({count/successful*100:.1f}%)")
    
    # Stakeholder analysis
    print(f"\nBy Stakeholder Type:")
    stakeholder_stats = {}
    for r in results:
        if r.get('success'):
            stakeholder = r['stakeholder']
            if stakeholder not in stakeholder_stats:
                stakeholder_stats[stakeholder] = {'count': 0, 'out_of_scope': 0}
            stakeholder_stats[stakeholder]['count'] += 1
            if r.get('is_out_of_scope', False):
                stakeholder_stats[stakeholder]['out_of_scope'] += 1
    
    for stakeholder, stats in sorted(stakeholder_stats.items()):
        out_rate = stats['out_of_scope'] / stats['count'] * 100
        print(f"  {stakeholder}: {stats['count']} queries, {stats['out_of_scope']} out-of-scope ({out_rate:.1f}%)")

def save_results(results):
    """Save detailed results to file"""
    output_file = project_root / f"test_results_105_prompts_updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    output_data = {
        'test_date': datetime.now().isoformat(),
        'test_description': '105 prompts test with updated domain classification logic',
        'total_queries': len(results),
        'summary': {
            'successful': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'avg_response_time': sum(r.get('response_time', 0) for r in results if r.get('success')) / max(sum(1 for r in results if r['success']), 1),
            'out_of_scope_count': sum(1 for r in results if r.get('is_out_of_scope', False))
        },
        'detailed_results': results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")

def main():
    """Run the 105 prompts test"""
    print("🚀 Running 105 Prompts Test with Updated Logic")
    print("="*60)
    
    # Load test queries
    queries = load_test_queries()
    print(f"Loaded {len(queries)} test queries")
    
    # Initialize services
    chat_service = initialize_services()
    
    # Process all queries
    results = []
    print("\nProcessing ALL 105 queries...\n")
    
    # Set up logging to capture backend debug info
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'debug_105_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    
    for i, query_data in enumerate(queries, 1):
        # Use unique conversation ID for each query to prevent mixing
        conversation_id = f"test-query-{i}"
        result = process_query(chat_service, query_data, conversation_id=conversation_id, verbose=True)
        results.append(result)
        
        # Add small delay to avoid rate limiting
        time.sleep(0.1)
    
    print("\n\nProcessing complete!")
    
    # Analyze results
    analyze_results(results)
    
    # Save results
    save_results(results)
    
    # If we didn't show verbose output, show some examples
    if len(results) < 10:  # Only show if we processed a small number
        print("\n" + "="*80)
        print("RESULTS SUMMARY")
        print("="*80)
        
        for result in results:
            print(f"\nQuery {result['query_num']}: {result['query'][:80]}...")
            print(f"  Domain: {result.get('domain_classified', 'N/A')}")
            print(f"  Out of scope: {result.get('is_out_of_scope', False)}")
            print(f"  Response time: {result.get('response_time', 0):.2f}s")

if __name__ == "__main__":
    main()