#!/usr/bin/env python3
"""
Test production features: metadata queries and technical AI queries.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.services.chat_service import ChatService
from src.core.models.gemini import GeminiModel
from src.core.storage.vector_store import VectorStore
from src.config.settings import settings
from src.config.logging import get_logger

logger = get_logger(__name__)

def test_production_queries():
    """Test the full integration with real services."""
    print("\n" + "="*50)
    print("TESTING PRODUCTION FEATURES")
    print("="*50)
    
    # Initialize services
    print("\nInitializing services...")
    
    # Initialize Gemini
    gemini_model = GeminiModel(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL_NAME
    )
    
    # Initialize vector store (may be None if no data)
    vector_store = None
    try:
        vector_store = VectorStore(
            embedding_provider=settings.EMBEDDING_PROVIDER,
            api_key=settings.GEMINI_API_KEY,
            repository_path=settings.get_repository_path(),
            persist_directory=str(settings.CHROMA_DB_DIR),
            use_hybrid_search=settings.USE_HYBRID_SEARCH
        )
        vector_store.initialize()
    except Exception as e:
        print(f"Vector store initialization failed: {e}")
    
    # Create chat service
    chat_service = ChatService(
        gemini_model=gemini_model,
        vector_store=vector_store
    )
    
    # Test cases
    test_cases = [
        # Metadata queries
        ("How many risks are in the database?", "metadata"),
        ("What are the main risk categories?", "metadata"),
        ("List all domains in the repository", "metadata"),
        ("How many risks in domain 7?", "metadata"),
        
        # Technical queries
        ("How do transformer architectures work?", "technical"),
        ("Explain attention mechanism in neural networks", "technical"),
        ("What is backpropagation?", "technical"),
        
        # Repository queries
        ("What are the privacy risks of AI?", "repository"),
        ("Tell me about bias in AI systems", "repository"),
        
        # Should be rejected
        ("What's the weather today?", "rejected"),
        ("How do I bake cookies?", "rejected"),
    ]
    
    for query, expected_type in test_cases:
        print(f"\n{'='*60}")
        print(f"🔍 Query: {query}")
        print(f"Expected type: {expected_type}")
        print("-" * 60)
        
        try:
            response, data = chat_service.process_query(query, "test_session")
            
            print(f"\n📝 Response preview (first 500 chars):")
            print(response[:500])
            
            if isinstance(data, list) and data:
                if hasattr(data[0], 'title'):  # Technical sources
                    print(f"\n📚 Sources found: {len(data)}")
                    for i, source in enumerate(data[:3], 1):
                        print(f"  [{i}] {source.title}")
                else:  # Metadata results
                    print(f"\n📊 Data points returned: {len(data)}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

def main():
    """Run production tests."""
    print("🚀 Starting production feature tests...")
    test_production_queries()
    print("\n✅ Tests completed!")

if __name__ == "__main__":
    main()