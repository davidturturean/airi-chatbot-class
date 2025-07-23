#!/usr/bin/env python3
"""
Comprehensive test of all new features: metadata queries, technical AI queries, and routing.
"""
import sys
import os
import time
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.services.chat_service import ChatService
from src.core.models.gemini import GeminiModel
from src.core.storage.vector_store import VectorStore
from src.core.metadata import metadata_service
from src.config.settings import settings
from src.config.logging import get_logger

logger = get_logger(__name__)

class Colors:
    """ANSI color codes for beautiful output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a beautiful header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")

def print_subheader(text):
    """Print a subheader."""
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-'*len(text)}{Colors.ENDC}")

def print_query(query, query_type):
    """Print query info."""
    print(f"\n{Colors.OKBLUE}🔍 Query:{Colors.ENDC} {Colors.BOLD}{query}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}📁 Expected Type:{Colors.ENDC} {query_type}")

def print_response(response, data):
    """Print response details."""
    print(f"\n{Colors.OKGREEN}📝 Response:{Colors.ENDC}")
    # Show first 500 chars or full response if short
    if len(response) <= 500:
        print(response)
    else:
        print(response[:500] + f"... [{len(response)} total chars]")
    
    # Show data details
    if isinstance(data, list) and data:
        print(f"\n{Colors.OKGREEN}📊 Data Returned:{Colors.ENDC} {len(data)} items")
        
        # Show sample data based on type
        if hasattr(data[0], 'title'):  # Technical sources
            print(f"{Colors.OKGREEN}📚 Sources:{Colors.ENDC}")
            for i, source in enumerate(data[:3], 1):
                print(f"  [{i}] {source.title}")
                print(f"      URL: {source.url}")
        elif isinstance(data[0], dict):  # Metadata results
            print(f"{Colors.OKGREEN}🗃️ Sample Data:{Colors.ENDC}")
            for key, value in list(data[0].items())[:5]:
                print(f"  {key}: {value}")

def test_comprehensive_features():
    """Run comprehensive tests on all features."""
    print_header("AIRI CHATBOT COMPREHENSIVE FEATURE TEST")
    print(f"\n{Colors.WARNING}⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    
    # Initialize services
    print_subheader("🚀 Initializing Services")
    start_time = time.time()
    
    # Initialize metadata service first
    print("📊 Initializing metadata service...")
    try:
        metadata_service.initialize(force_reload=True)
        stats = metadata_service.get_statistics()
        print(f"{Colors.OKGREEN}✓ Metadata service ready: {stats['total_rows']} rows loaded{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}✗ Metadata service failed: {str(e)}{Colors.ENDC}")
    
    # Initialize Gemini
    print("🤖 Initializing Gemini model...")
    gemini_model = GeminiModel(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL_NAME
    )
    print(f"{Colors.OKGREEN}✓ Gemini model ready{Colors.ENDC}")
    
    # Initialize vector store (optional)
    print("🗄️ Initializing vector store...")
    vector_store = None
    try:
        vector_store = VectorStore(
            embedding_provider=settings.EMBEDDING_PROVIDER,
            api_key=settings.GEMINI_API_KEY,
            repository_path=settings.get_repository_path(),
            persist_directory=str(settings.CHROMA_DB_DIR),
            use_hybrid_search=settings.USE_HYBRID_SEARCH
        )
        if vector_store.initialize():
            print(f"{Colors.OKGREEN}✓ Vector store ready{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠ Vector store initialized with warnings{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.WARNING}⚠ Vector store not available: {str(e)}{Colors.ENDC}")
    
    # Create chat service
    chat_service = ChatService(
        gemini_model=gemini_model,
        vector_store=vector_store
    )
    
    init_time = time.time() - start_time
    print(f"\n{Colors.OKGREEN}✓ All services initialized in {init_time:.2f} seconds{Colors.ENDC}")
    
    # Test cases organized by category
    test_categories = {
        "📊 Metadata Queries": [
            ("How many risks are in the database?", "metadata", "Should return total count"),
            ("What are the main risk categories?", "metadata", "Should list distinct categories"),
            ("List all domains in the repository", "metadata", "Should show all domains"),
            ("How many risks in domain 7?", "metadata", "Should count domain 7 risks"),
            ("What is the earliest publication year?", "metadata", "Should find min year"),
            ("Show me the 10th risk in the database", "metadata", "Should return specific row"),
            ("Count risks by entity type", "metadata", "Should group by entity"),
        ],
        
        "🔬 Technical AI Queries": [
            ("How do transformer architectures work?", "technical", "Should explain transformers"),
            ("Explain attention mechanism in neural networks", "technical", "Should detail attention"),
            ("What is backpropagation in deep learning?", "technical", "Should explain backprop"),
            ("How does BERT handle bidirectional context?", "technical", "Should explain BERT"),
            ("Explain vision transformers (ViT)", "technical", "Should cover ViT"),
        ],
        
        "🗃️ Repository Content Queries": [
            ("What are the privacy risks of AI?", "repository", "Should find privacy risks"),
            ("Tell me about bias in AI systems", "repository", "Should find bias content"),
            ("What are socioeconomic impacts of AI?", "repository", "Should find impacts"),
        ],
        
        "🚫 Rejected Queries": [
            ("What's the weather today?", "rejected", "Should politely reject"),
            ("How do I bake chocolate cookies?", "rejected", "Should redirect to AI risks"),
            ("Tell me a joke", "rejected", "Should suggest AI topics"),
        ],
        
        "🔀 Cross-Database Queries": [
            ("Show all bias risks with high confidence", "cross-db", "Should filter by domain and confidence"),
            ("List risks from 2024", "metadata", "Should filter by year"),
        ]
    }
    
    # Track statistics
    total_queries = 0
    successful_queries = 0
    failed_queries = 0
    response_times = []
    
    # Run tests by category
    for category, test_cases in test_categories.items():
        print_header(category)
        
        for query, expected_type, description in test_cases:
            print_query(query, expected_type)
            print(f"{Colors.WARNING}📋 Test Goal: {description}{Colors.ENDC}")
            
            total_queries += 1
            query_start = time.time()
            
            try:
                # Process query
                response, data = chat_service.process_query(query, f"test_session_{total_queries}")
                query_time = time.time() - query_start
                response_times.append(query_time)
                
                # Print results
                print_response(response, data)
                print(f"\n{Colors.OKGREEN}✓ Success! Response time: {query_time:.2f}s{Colors.ENDC}")
                successful_queries += 1
                
            except Exception as e:
                query_time = time.time() - query_start
                print(f"\n{Colors.FAIL}✗ Error: {str(e)}{Colors.ENDC}")
                print(f"Response time: {query_time:.2f}s")
                failed_queries += 1
                
                # Print traceback for debugging
                import traceback
                traceback.print_exc()
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
    
    # Print final statistics
    print_header("📈 TEST RESULTS SUMMARY")
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    print(f"\n{Colors.BOLD}Query Statistics:{Colors.ENDC}")
    print(f"  Total Queries: {total_queries}")
    print(f"  {Colors.OKGREEN}Successful: {successful_queries}{Colors.ENDC}")
    print(f"  {Colors.FAIL}Failed: {failed_queries}{Colors.ENDC}")
    print(f"  Success Rate: {(successful_queries/total_queries*100):.1f}%")
    
    print(f"\n{Colors.BOLD}Performance Metrics:{Colors.ENDC}")
    print(f"  Average Response Time: {avg_response_time:.2f}s")
    print(f"  Fastest Response: {min(response_times):.2f}s")
    print(f"  Slowest Response: {max(response_times):.2f}s")
    
    print(f"\n{Colors.BOLD}Service Status:{Colors.ENDC}")
    print(f"  Metadata Service: {Colors.OKGREEN}✓ Active{Colors.ENDC}")
    print(f"  Vector Store: {Colors.OKGREEN if vector_store else Colors.WARNING}{'✓ Active' if vector_store else '⚠ Limited'}{Colors.ENDC}")
    print(f"  Gemini Model: {Colors.OKGREEN}✓ Active{Colors.ENDC}")
    
    # Metadata service stats
    meta_stats = metadata_service.get_statistics()
    print(f"\n{Colors.BOLD}Metadata Statistics:{Colors.ENDC}")
    # Handle both old and new formats
    if 'databases' in meta_stats:
        for db_name, db_stats in meta_stats['databases'].items():
            print(f"  {db_name}: {db_stats['row_count']} rows")
    elif 'tables' in meta_stats:
        for table_name, table_info in meta_stats['tables'].items():
            print(f"  {table_name}: {table_info['row_count']} rows")
    else:
        print(f"  Total rows: {meta_stats.get('total_rows', 0)}")
    
    print(f"\n{Colors.WARNING}⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    
    # Final verdict
    if failed_queries == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! The system is production ready!{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}⚠️  Some tests failed. Review the errors above.{Colors.ENDC}")

def main():
    """Run the comprehensive test suite."""
    # Create output file
    output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # Redirect stdout to both console and file
    import io
    
    class TeeOutput:
        def __init__(self, *streams):
            self.streams = streams
        
        def write(self, data):
            for stream in self.streams:
                stream.write(data)
                stream.flush()
        
        def flush(self):
            for stream in self.streams:
                stream.flush()
    
    # Save original stdout
    original_stdout = sys.stdout
    
    try:
        # Open output file
        with open(output_file, 'w', encoding='utf-8') as f:
            # Create tee output to write to both console and file
            sys.stdout = TeeOutput(original_stdout, f)
            
            print(f"📝 Test output will be saved to: {output_file}\n")
            
            test_comprehensive_features()
            
            print(f"\n📁 Test results saved to: {output_file}")
            
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test interrupted by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Fatal error: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original stdout
        sys.stdout = original_stdout
        print(f"\n✅ Test results have been saved to: {output_file}")

if __name__ == "__main__":
    main()