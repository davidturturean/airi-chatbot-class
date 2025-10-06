#!/usr/bin/env python3
"""
Load the AI Risk Repository Preprint into the vector database.
"""

import sys
import os
sys.path.append('.')

from pathlib import Path
from langchain_community.document_loaders import Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_preprint_to_vectordb():
    """Load the preprint DOCX into ChromaDB."""
    
    print("LOADING PREPRINT INTO VECTOR DATABASE")
    print("=" * 60)
    
    # 1. Load the DOCX file
    docx_path = "data/info_files/AI_Risk_Repository_Preprint.docx"
    
    if not Path(docx_path).exists():
        print(f"Error: {docx_path} not found!")
        return False
    
    print(f"Loading: {docx_path}")
    
    # Use Docx2txtLoader to extract text
    loader = Docx2txtLoader(docx_path)
    documents = loader.load()
    
    print(f"Extracted {len(documents)} document(s)")
    print(f"Total characters: {sum(len(doc.page_content) for doc in documents)}")
    
    # 2. Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")
    
    # 3. Add metadata to each chunk
    for i, chunk in enumerate(chunks):
        chunk.metadata.update({
            'source': 'AI_Risk_Repository_Preprint',
            'type': 'preprint',
            'document_type': 'research_paper',
            'authors': 'Slattery et al.',
            'year': '2024',
            'chunk_id': i,
            'title': 'The AI Risk Repository: A Comprehensive Meta-Review, Database, and Taxonomy'
        })
    
    # 4. Initialize embeddings
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment!")
        return False
    
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=api_key
    )
    
    # 5. Load into ChromaDB
    persist_directory = "data/chroma_db"
    
    # Load existing database
    print(f"Loading existing ChromaDB from {persist_directory}")
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # Get current count
    existing_count = vectorstore._collection.count()
    print(f"Existing documents in ChromaDB: {existing_count}")
    
    # Add new documents
    print("Adding preprint chunks to database...")
    vectorstore.add_documents(chunks)
    
    # Verify addition
    new_count = vectorstore._collection.count()
    added = new_count - existing_count
    print(f"Successfully added {added} chunks")
    print(f"Total documents now: {new_count}")
    
    # 6. Test retrieval
    print("\nTesting retrieval...")
    test_queries = [
        "methodology systematic review",
        "Gabriel et al coverage",
        "limitations of the taxonomy",
        "How many documents were analyzed?"
    ]
    
    for query in test_queries:
        results = vectorstore.similarity_search(query, k=2)
        if results:
            print(f"\n✓ Query: '{query}'")
            print(f"  Found: {results[0].page_content[:100]}...")
        else:
            print(f"\n✗ Query: '{query}' - No results")
    
    print("\n" + "=" * 60)
    print("PREPRINT SUCCESSFULLY LOADED INTO VECTOR DATABASE!")
    return True

if __name__ == "__main__":
    success = load_preprint_to_vectordb()
    exit(0 if success else 1)