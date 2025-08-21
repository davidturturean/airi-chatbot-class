#!/usr/bin/env python3
"""Debug script to check vector store retrieval."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.storage.vector_store import VectorStore
from src.config.settings import settings

def test_retrieval():
    """Test vector store retrieval for problematic queries."""
    
    # Initialize vector store
    print("Initializing vector store...")
    vector_store = VectorStore(
        repository_path=str(settings.INFO_FILES_DIR),
        persist_directory=str(settings.CHROMA_DB_DIR),
        use_hybrid_search=True
    )
    
    # Load existing store
    if not vector_store.load_existing_store():
        print("Failed to load vector store")
        return
    
    print("Vector store loaded successfully")
    
    # Test queries
    test_queries = [
        "What are the limitations of this research?",
        "limitations scope boundary challenges",
        "Weidinger framework comparison",
        "Gabriel et al framework",
        "PRISMA methodology"  # Control - this should work
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        # Get relevant documents
        docs = vector_store.get_relevant_documents(query, k=5)
        
        if docs:
            print(f"Found {len(docs)} documents:")
            for i, doc in enumerate(docs[:3]):  # Show first 3
                source = doc.metadata.get('source', 'Unknown')
                rid = doc.metadata.get('rid', 'Unknown')
                content_preview = doc.page_content[:200]
                print(f"\n{i+1}. Source: {source}")
                print(f"   RID: {rid}")
                print(f"   Content: {content_preview}...")
        else:
            print("No documents found!")
    
    # Check if RID-PREP documents are in the store
    print(f"\n{'='*60}")
    print("Checking for RID-PREP documents in store...")
    print(f"{'='*60}")
    
    # Try to retrieve a specific preprint chunk
    preprint_test = vector_store.get_relevant_documents("AI Risk Database Coded With Causal Taxonomy", k=3)
    if preprint_test:
        print(f"Found {len(preprint_test)} preprint documents")
        for doc in preprint_test:
            rid = doc.metadata.get('rid', 'Unknown')
            print(f"  - {rid}")
    else:
        print("No preprint documents found!")

if __name__ == "__main__":
    test_retrieval()