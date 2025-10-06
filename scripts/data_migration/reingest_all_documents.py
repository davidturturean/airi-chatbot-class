#!/usr/bin/env python3
"""
Re-ingest all documents including the preprint into a fresh vector store.
This ensures all documents are properly indexed for retrieval.
"""

import sys
import os
import shutil
from pathlib import Path

sys.path.append('.')

from src.core.storage.vector_store import VectorStore
from src.config.logging import get_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)

def reingest_all_documents():
    """Re-ingest all documents from scratch."""
    
    print("="*60)
    print("RE-INGESTING ALL DOCUMENTS INTO VECTOR STORE")
    print("="*60)
    
    # Backup existing ChromaDB
    chroma_dir = Path("data/chroma_db")
    backup_dir = Path("data/chroma_db_backup")
    
    if chroma_dir.exists():
        print(f"Backing up existing ChromaDB to {backup_dir}")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(chroma_dir, backup_dir)
        print("Backup complete")
        
        # Remove existing ChromaDB
        print("Removing existing ChromaDB...")
        shutil.rmtree(chroma_dir)
        print("Removed")
    
    # Initialize fresh vector store
    print("\nInitializing fresh vector store...")
    vector_store = VectorStore()
    
    # This will trigger ingest_documents since no existing store exists
    success = vector_store.initialize()
    
    if success:
        print("✅ Vector store initialized successfully")
        
        # Test retrieval
        print("\nTesting retrieval...")
        test_queries = [
            "777 documents analyzed",
            "Slattery et al authors",
            "PRISMA methodology systematic review"
        ]
        
        for query in test_queries:
            docs = vector_store.get_relevant_documents(query, k=2)
            if docs:
                content_preview = docs[0].page_content[:100]
                # Check for preprint indicators
                has_preprint = any(term in content_preview.lower() 
                                  for term in ['777', 'slattery', 'prisma', 'systematic'])
                status = "✅" if has_preprint else "❌"
                print(f"{status} Query: '{query}' - Found: {content_preview[:50]}...")
            else:
                print(f"❌ Query: '{query}' - No results")
        
        print("\n" + "="*60)
        print("RE-INGESTION COMPLETE")
        return True
    else:
        print("❌ Failed to initialize vector store")
        # Restore backup
        if backup_dir.exists():
            print("Restoring backup...")
            shutil.copytree(backup_dir, chroma_dir)
            print("Backup restored")
        return False

if __name__ == "__main__":
    success = reingest_all_documents()
    sys.exit(0 if success else 1)