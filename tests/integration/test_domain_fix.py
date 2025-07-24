#!/usr/bin/env python3
"""
Test script to verify the domain classification bug fix.
Tests that medical queries are properly routed to safety domain.
"""
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.query.processor import QueryProcessor
from src.core.query.monitor import Monitor
from src.core.services.chat_service import ChatService
from src.config.settings import settings

def test_domain_classification():
    """Test that medical queries get proper domain classification."""
    
    print("🧪 Testing Domain Classification Fix")
    print("=" * 50)
    
    # Initialize components
    query_monitor = Monitor(settings.GEMINI_API_KEY)
    query_processor = QueryProcessor(query_monitor=query_monitor)
    
    # Test query
    medical_query = "What are the risks of AI chatbots misdiagnosing medical conditions?"
    
    print(f"📝 Query: {medical_query}")
    print()
    
    # Step 1: Test query analysis
    print("1️⃣ Testing query analysis...")
    query_type, domain = query_processor.analyze_query(medical_query)
    print(f"   Query Type: {query_type}")
    print(f"   Domain: {domain}")
    print()
    
    # Step 2: Test prompt generation with fixed domain passthrough
    print("2️⃣ Testing prompt generation...")
    
    # Mock some context to simulate retrieved documents
    mock_context = """
    SECTION 1:
    Title: Safety Assessment of Chinese Large Language Models
    Domain: 3. Misinformation
    Sub-domain: 3.1 > False or misleading information
    Risk Category: Typical safety scenarios
    Risk Subcategory: Mental Health
    Description: "The model generates a risky response about mental health, such as content that encourages suicide or causes panic or anxiety."
    """
    
    # Test the fixed generate_prompt method with domain parameter
    try:
        prompt = query_processor.generate_prompt(
            message=medical_query,
            query_type=query_type, 
            domain=domain,  # 🔧 This is the fix - domain is now passed correctly
            context=mock_context,
            session_id="test",
            docs=None
        )
        
        print("   ✅ Prompt generation successful!")
        print(f"   📊 Domain passed to prompt: {domain}")
        
        # Check if prompt contains safety-specific content
        if "SAFETY FOCUS" in prompt:
            print("   ✅ Safety domain template used correctly!")
        elif "Based on the AI Risk Repository" in prompt and domain == 'general':
            print("   ❌ General template used (bug still present)")
        else:
            print("   ⚠️  Unexpected prompt template")
            
        print("\n📋 Prompt Preview (first 200 chars):")
        print(prompt[:200] + "...")
        print()
        
    except Exception as e:
        print(f"   ❌ Error in prompt generation: {e}")
        return False
    
    # Step 3: Test the overall flow
    print("3️⃣ Testing overall classification flow...")
    
    if domain == "safety":
        print("   ✅ Medical query correctly classified as SAFETY domain")
        print("   ✅ Domain classification bug is FIXED!")
        return True
    else:
        print(f"   ❌ Medical query incorrectly classified as {domain} domain")
        print("   ❌ Bug still present")
        return False

def test_other_domains():
    """Test that other domain classifications still work."""
    
    print("\n🔍 Testing Other Domain Classifications")
    print("=" * 50)
    
    test_cases = [
        ("Will AI take my job?", "socioeconomic"),
        ("How do I prevent bias in hiring algorithms?", "bias"),
        ("What privacy risks exist with AI?", "privacy"),
        ("How should AI be regulated?", "governance"),
    ]
    
    query_monitor = Monitor(settings.GEMINI_API_KEY)
    query_processor = QueryProcessor(query_monitor=query_monitor)
    
    all_passed = True
    
    for query, expected_domain in test_cases:
        query_type, domain = query_processor.analyze_query(query)
        
        print(f"📝 Query: {query}")
        print(f"   Expected: {expected_domain}")
        print(f"   Got: {domain}")
        
        if domain == expected_domain:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")
            all_passed = False
        print()
    
    return all_passed

if __name__ == "__main__":
    print("🚀 Starting Domain Classification Fix Test")
    print("=" * 60)
    
    # Test the main fix
    medical_test_passed = test_domain_classification()
    
    # Test that we didn't break other domains
    other_domains_passed = test_other_domains()
    
    print("🏁 FINAL RESULTS")
    print("=" * 50)
    
    if medical_test_passed:
        print("✅ Medical Query Fix: WORKING")
    else:
        print("❌ Medical Query Fix: FAILED")
    
    if other_domains_passed:
        print("✅ Other Domains: WORKING")
    else:
        print("❌ Other Domains: BROKEN")
    
    if medical_test_passed and other_domains_passed:
        print("\n🎉 ALL TESTS PASSED! Domain classification bug is FIXED!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the output above.")
        sys.exit(1)