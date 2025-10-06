#!/usr/bin/env python3
"""
Index the preprint chunks into ChromaDB vector store.
"""

import json
from pathlib import Path
import chromadb
from chromadb.config import Settings
import sys
sys.path.append(str(Path(__file__).parent))

from src.config.settings import settings
from src.core.storage.vector_store import VectorStore

def main():
    # Load chunks
    chunks_path = Path('/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/data/preprint_chunks.json')
    
    if not chunks_path.exists():
        print(f"Error: Chunks not found at {chunks_path}")
        print("Please run chunk_and_index_preprint.py first")
        return
    
    print(f"Loading chunks from: {chunks_path}")
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"Loaded {len(chunks)} chunks")
    
    # Initialize vector store
    print("\nInitializing vector store...")
    vector_store = VectorStore(
        embedding_provider=settings.EMBEDDING_PROVIDER,
        api_key=settings.GEMINI_API_KEY,
        repository_path=settings.get_repository_path(),
        persist_directory=str(settings.CHROMA_DB_DIR),
        use_hybrid_search=settings.USE_HYBRID_SEARCH
    )
    
    # Initialize if needed
    if not vector_store.initialize():
        print("Failed to initialize vector store")
        return
    
    print("Vector store initialized")
    
    # Prepare documents for indexing
    print("\nPreparing documents for indexing...")
    documents = []
    metadatas = []
    ids = []
    
    for chunk in chunks:
        # Create document text
        doc_text = chunk['content']
        
        # Add section context to improve retrieval
        if chunk['metadata']['section'] != 'Unknown':
            doc_text = f"Section: {chunk['metadata']['section']}\n\n{doc_text}"
        
        documents.append(doc_text)
        
        # Prepare metadata
        metadata = {
            'source': chunk['metadata']['source'],
            'section': chunk['metadata']['section'],
            'content_type': chunk['metadata'].get('content_type', 'general'),
            'type': 'preprint',
            'chunk_id': chunk['metadata']['chunk_id'],
            'rid': chunk['id']
        }
        metadatas.append(metadata)
        
        # Use chunk ID
        ids.append(chunk['id'])
    
    print(f"Prepared {len(documents)} documents for indexing")
    
    # Add to vector store
    print("\nIndexing documents into ChromaDB...")
    try:
        # Use the existing vector store's collection
        if hasattr(vector_store, 'collection') and vector_store.collection:
            collection = vector_store.collection
            print(f"Using existing collection: {collection.name}")
        else:
            # Fallback to creating client
            client = chromadb.PersistentClient(path=str(settings.CHROMA_DB_DIR))
            # Try to get or create collection
            try:
                collection = client.get_collection(name="ai_risk_repository")
                print(f"Retrieved existing collection: {collection.name}")
            except:
                collection = client.create_collection(
                    name="ai_risk_repository",
                    metadata={"description": "AI Risk Repository with Preprint Content"}
                )
                print(f"Created new collection: {collection.name}")
        
        # Add documents in batches
        batch_size = 10
        for i in range(0, len(documents), batch_size):
            batch_end = min(i + batch_size, len(documents))
            
            print(f"Indexing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}...")
            
            collection.add(
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end],
                ids=ids[i:batch_end]
            )
        
        print(f"\nSuccessfully indexed {len(documents)} preprint chunks")
        
        # Verify by querying
        print("\nVerifying indexing with test queries...")
        
        test_queries = [
            "PRISMA methodology",
            "limitations of the taxonomy",
            "Weidinger comparison",
            "screening criteria",
            "future work"
        ]
        
        for query in test_queries:
            results = collection.query(
                query_texts=[query],
                n_results=1
            )
            
            if results['documents'][0]:
                print(f"✓ Query '{query}' found relevant content")
                print(f"  Section: {results['metadatas'][0][0].get('section', 'Unknown')}")
            else:
                print(f"✗ Query '{query}' returned no results")
        
    except Exception as e:
        print(f"Error indexing documents: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✅ Preprint indexing complete!")
    print(f"Added {len(chunks)} chunks covering methodology, limitations, comparative analysis, etc.")

if __name__ == "__main__":
    main()