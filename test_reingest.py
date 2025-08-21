#!/usr/bin/env python3
"""Re-ingest documents with fact extraction."""

from pathlib import Path
from src.core.storage.vector_store import VectorStore
from src.config.settings import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

print("Re-initializing vector store with fact extraction...")

# Initialize vector store
vector_store = VectorStore()
success = vector_store.initialize()
print(f"Vector store initialization: {'Success' if success else 'Failed'}")

if not success:
    print("Failed to initialize vector store!")
    exit(1)

# Check if vector store is properly initialized
if vector_store.vector_store is None:
    print("ERROR: vector_store.vector_store is None after initialization!")
    exit(1)

print(f"Vector store initialized: {vector_store.vector_store is not None}")

# Check current documents
try:
    all_docs = vector_store.vector_store._collection.get()
    if all_docs and 'ids' in all_docs:
        print(f"Current documents in vector store: {len(all_docs['ids'])}")
        
        # Check for documents with extracted facts
        docs_with_facts = 0
        preprint_docs = 0
        preprint_with_facts = 0
        
        for metadata in all_docs['metadatas']:
            if metadata.get('has_extracted_facts'):
                docs_with_facts += 1
            if 'Preprint' in metadata.get('source', ''):
                preprint_docs += 1
                if metadata.get('has_extracted_facts'):
                    preprint_with_facts += 1
        
        print(f"Documents with extracted facts: {docs_with_facts}")
        print(f"Preprint documents: {preprint_docs}")
        print(f"Preprint documents with facts: {preprint_with_facts}")
        
        # If no facts extracted, we need to reingest
        if docs_with_facts == 0:
            print("\nNo documents have extracted facts. Need to reingest with fact extraction.")
            print("This requires modifying the ingestion process...")
            
except Exception as e:
    print(f"Error checking documents: {e}")

print("\nDone!")