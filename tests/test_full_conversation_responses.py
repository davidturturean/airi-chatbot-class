#!/usr/bin/env python3
"""
Test full conversational responses - what users actually see.
Shows the complete responses the system gives to user queries.
"""
import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_full_conversation_responses():
    """Test full conversational responses to see what users actually get."""
    
    # Diverse test queries that would generate full responses
    test_queries = [
        "Do machine learning systems treat different groups of people fairly?",
        "Who should oversee the development of intelligent systems?",
        "How do we ensure AI systems are fair to everyone?",
        "What happens when AI systems make mistakes?",
        "Can intelligent machines cause physical harm to people?",
        "Do smart systems collect too much personal information?",
        "Will robots replace human workers in the future?",
        "How well do neural networks handle unexpected inputs?",
        "Are there concerns about AI systems affecting different communities?",
        "What measures exist to control AI development?",
        "How might AI systems perpetuate existing inequalities?",
        "What happens to human dignity when AI makes decisions about us?",
        "Could AI systems be weaponized?",
        "Are AI systems transparent enough for public trust?",
        "How do we prevent AI from creating filter bubbles?",
        "What are the unintended consequences of AI automation?",
        "How do AI systems learn from human behavior?",
        "What ethical frameworks should guide AI development?",
        "Can AI systems be held accountable for their decisions?",
        "How do we balance AI innovation with safety?",
        "Are facial recognition systems racially biased?",
        "What privacy risks exist with smart home devices?",
        "How do we regulate autonomous weapon systems?",
        "What happens when AI hiring tools discriminate?",
        "Are AI medical diagnoses safe and reliable?",
        "How do recommendation algorithms create echo chambers?",
        "What are the cybersecurity risks of AI systems?",
        "How do AI systems impact workforce displacement?",
        "What transparency requirements should AI have?",
        "How do we protect children from AI-driven content?",
        "How do neural networks process natural language?",
        "What makes AI systems robust against adversarial attacks?",
        "How do we measure AI model performance?",
        "What are the computational requirements for large language models?",
        "How do transformer architectures work?",
        "What is the training process for deep learning models?",
        "How do we optimize AI algorithms for efficiency?",
        "What are the limitations of current AI architectures?",
        "How do AI systems handle uncertainty and ambiguity?",
        "What benchmarks exist for evaluating AI capabilities?",
        "What's the best recipe for chocolate chip cookies?",
        "How do I fix my car engine?",
        "Tell me about the weather today",
        "What's the capital of France?",
        "How do I learn to play guitar?",
    ]
    
    print("🚀 Full Conversation Response Test - Complete User Responses")
    print("=" * 80)
    
    try:
        from src.core.services.chat_service import ChatService
        from src.core.models.gemini import GeminiModel
        from src.core.storage.vector_store import VectorStore
        from src.core.query.monitor import Monitor
        from src.config.settings import settings
        
        # Initialize components
        gemini_model = GeminiModel(api_key=settings.GEMINI_API_KEY, use_fallback=True)
        vector_store = VectorStore()
        query_monitor = Monitor(api_key=settings.GEMINI_API_KEY)
        
        # CRITICAL: Initialize the vector store from documents directory
        print("🔧 Initializing vector store from documents...")
        if not vector_store.initialize():
            print("❌ Failed to initialize vector store from documents!")
            return
        print("✅ Vector store initialized successfully")
        
        # Initialize the chat service (what users actually interact with)
        chat_service = ChatService(
            gemini_model=gemini_model,
            vector_store=vector_store,
            query_monitor=query_monitor
        )
        print("✅ Chat service initialized")
        print()
        
        full_responses = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"🔍 Query {i}/45: {query}")
            print("=" * 60)
            
            # Rate limiting
            if i > 1:
                import time
                time.sleep(4)  # 4 second delay to avoid quota issues
            
            try:
                # Get the full response that users would see
                full_response, documents = chat_service.process_query(query, conversation_id=f"test_{i}")
                
                print("📝 FULL USER RESPONSE:")
                print(full_response)
                print()
                print("=" * 60)
                print()
                
                # Store response
                full_responses.append({
                    "query": query,
                    "full_response": full_response,
                    "response_length": len(full_response),
                    "documents_found": len(documents),
                    "response_type": "success"
                })
                
            except Exception as e:
                error_msg = f"❌ Error processing query: {e}"
                print(error_msg)
                print("=" * 60)
                print()
                
                full_responses.append({
                    "query": query,
                    "full_response": error_msg,
                    "error": str(e),
                    "response_type": "error"
                })
        
        # Save all responses to JSON file
        with open('full_conversation_responses.json', 'w') as f:
            json.dump(full_responses, f, indent=2)
        
        # Analysis
        successful_responses = [r for r in full_responses if r['response_type'] == 'success']
        error_responses = [r for r in full_responses if r['response_type'] == 'error']
        
        if successful_responses:
            avg_length = sum(r['response_length'] for r in successful_responses) / len(successful_responses)
        else:
            avg_length = 0
        
        print("🎯 === CONVERSATION RESPONSE ANALYSIS === 🎯")
        print(f"📝 Total queries: {len(test_queries)}")
        print(f"✅ Successful responses: {len(successful_responses)}")
        print(f"❌ Error responses: {len(error_responses)}")
        print(f"📊 Average response length: {avg_length:.0f} characters")
        print()
        print("📁 All responses saved to: full_conversation_responses.json")
        print("🔍 You can examine the quality and completeness of user responses")
        
    except Exception as e:
        print(f"❌ Failed to initialize chat service: {e}")

if __name__ == "__main__":
    test_full_conversation_responses()