#!/usr/bin/env python3
"""
Test the synthesis improvements to verify they work correctly.
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.services.chat_service import ChatService
from src.core.models.gemini import GeminiModel
from src.core.storage.vector_store import VectorStore
from src.core.query.monitor import Monitor
from src.config.settings import settings

def test_synthesis():
    """Test the improved synthesis capabilities."""
    
    print("🧪 Testing Synthesis Improvements")
    print("=" * 60)
    
    # Initialize services
    print("\nInitializing services...")
    gemini_model = GeminiModel(settings.GEMINI_API_KEY)
    vector_store = VectorStore()
    vector_store.initialize()
    query_monitor = Monitor(settings.GEMINI_API_KEY)
    
    chat_service = ChatService(
        gemini_model=gemini_model,
        vector_store=vector_store,
        query_monitor=query_monitor
    )
    
    # Test queries that should trigger synthesis
    test_queries = [
        {
            'query': "What are the risks of AI bias in healthcare applications?",
            'expected_behavior': 'Should synthesize from general bias principles'
        },
        {
            'query': "Show me cross-domain analysis of privacy risks between healthcare and finance",
            'expected_behavior': 'Should pull documents from both domains and synthesize'
        },
        {
            'query': "What are the latest AI regulations in the EU for 2024?",
            'expected_behavior': 'Should trigger web search for current information'
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test['query']}")
        print(f"Expected: {test['expected_behavior']}")
        print(f"{'='*60}")
        
        try:
            response_text, docs = chat_service.process_query(test['query'], f"test-{i}")
            
            print(f"\nDocuments found: {len(docs)}")
            print(f"Response length: {len(response_text)} chars")
            
            # Check for synthesis indicators
            if "While the repository doesn't have" in response_text:
                print("✅ Synthesis approach detected")
            
            # Check for web search
            if "Additional Context from Web Search" in response_text:
                print("✅ Web search triggered")
            
            # Show response preview
            print(f"\nResponse preview:")
            print("-" * 60)
            print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n\n✅ Synthesis test complete!")

if __name__ == "__main__":
    test_synthesis()