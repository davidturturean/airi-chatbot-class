"""
Vector store implementation with hybrid search capabilities.
"""
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.docstore.document import Document
from langchain_core.retrievers import BaseRetriever
from langchain_community.retrievers import BM25Retriever
from rank_bm25 import BM25Okapi
import numpy as np
from ..retrieval.multi_strategy_retriever import MultiStrategyRetriever

from .document_processor import DocumentProcessor
from ..retrieval.advanced_retrieval import advanced_retriever
from ..taxonomy.scqa_taxonomy import scqa_manager, SCQAComponent
from ..metadata.fact_extractor import FactExtractor
from ...config.logging import get_logger
from ...config.settings import settings
from ...config.domains import domain_classifier

logger = get_logger(__name__)

class FieldAwareHybridRetriever(BaseRetriever):
    """Combines vector similarity and field-aware keyword search with metadata boosting."""
    
    # Declare fields for Pydantic validation
    vector_retriever: BaseRetriever
    keyword_retriever: BaseRetriever
    documents: List[Document]
    vector_weight: float
    keyword_weight: float
    rerank_top_k: int
    
    # BM25 indices (not declared as Pydantic fields since they're created dynamically)
    bm25_high_priority: Any = None
    bm25_medium_priority: Any = None
    bm25_all_fields: Any = None
    
    class Config:
        """Pydantic config to allow arbitrary types."""
        arbitrary_types_allowed = True
    
    def __init__(
        self,
        vector_retriever: BaseRetriever,
        keyword_retriever: BaseRetriever,
        documents: List[Document],
        vector_weight: float = None,
        rerank_top_k: int = None,
        **kwargs
    ):
        # Calculate weights
        calculated_vector_weight = max(0.0, min(1.0, vector_weight or settings.VECTOR_WEIGHT))
        calculated_keyword_weight = 1.0 - calculated_vector_weight
        calculated_rerank_top_k = rerank_top_k or settings.HYBRID_RERANK_TOP_K
        
        # Initialize with Pydantic
        super().__init__(
            vector_retriever=vector_retriever,
            keyword_retriever=keyword_retriever,
            documents=documents,
            vector_weight=calculated_vector_weight,
            keyword_weight=calculated_keyword_weight,
            rerank_top_k=calculated_rerank_top_k,
            **kwargs
        )
        
        # Create field-aware BM25 indices
        self._create_field_aware_indices()
        
    def _create_field_aware_indices(self):
        """Create BM25 indices for different metadata fields."""
        try:
            # Extract content for different priority fields
            high_priority_corpus = []
            medium_priority_corpus = []
            all_fields_corpus = []
            
            for doc in self.documents:
                # High priority fields (titles, domains, categories)
                high_priority_text = doc.metadata.get('search_high_priority', '')
                high_priority_corpus.append(high_priority_text.split() if high_priority_text else [])
                
                # Medium priority fields (subdomains, specific domains)
                medium_priority_text = doc.metadata.get('search_medium_priority', '')
                medium_priority_corpus.append(medium_priority_text.split() if medium_priority_text else [])
                
                # All searchable fields combined
                all_fields_text = doc.metadata.get('search_all_fields', '')
                all_fields_corpus.append(all_fields_text.split() if all_fields_text else [])
            
            # Create BM25 indices
            self.bm25_high_priority = BM25Okapi(high_priority_corpus) if any(high_priority_corpus) else None
            self.bm25_medium_priority = BM25Okapi(medium_priority_corpus) if any(medium_priority_corpus) else None
            self.bm25_all_fields = BM25Okapi(all_fields_corpus) if any(all_fields_corpus) else None
            
            logger.info(f"Created field-aware BM25 indices for {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"Error creating field-aware indices: {str(e)}")
            self.bm25_high_priority = None
            self.bm25_medium_priority = None
            self.bm25_all_fields = None
    
    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        """Get relevant documents using field-aware hybrid search."""
        # Get docs from vector retriever (use invoke to avoid deprecation)
        try:
            vector_docs = self.vector_retriever.invoke(query)
        except:
            # Fallback to deprecated method if invoke not available
            vector_docs = self.vector_retriever.get_relevant_documents(query)
        
        # Get field-aware keyword matches
        field_aware_docs = self._get_field_aware_matches(query)
        
        # Get standard keyword docs as fallback
        try:
            standard_keyword_docs = self.keyword_retriever.invoke(query)
        except:
            # Fallback to deprecated method if invoke not available
            standard_keyword_docs = self.keyword_retriever.get_relevant_documents(query)
        
        # Track unique docs and scores
        unique_docs = {}
        
        # Add vector docs with position-based scoring
        for i, doc in enumerate(vector_docs):
            doc_id = self._get_doc_id(doc)
            score = self.vector_weight * (1.0 - (i / max(1, len(vector_docs))))
            unique_docs[doc_id] = {"doc": doc, "score": score, "sources": ["vector"]}
        
        # Add field-aware keyword docs with boosted scores
        for doc, field_score in field_aware_docs:
            doc_id = self._get_doc_id(doc)
            # Field-aware scores are higher priority
            boosted_score = self.keyword_weight * field_score * settings.METADATA_BOOST_FACTOR
            
            if doc_id in unique_docs:
                unique_docs[doc_id]["score"] += boosted_score
                unique_docs[doc_id]["sources"].append("field_aware")
            else:
                unique_docs[doc_id] = {"doc": doc, "score": boosted_score, "sources": ["field_aware"]}
        
        # Add standard keyword docs with lower weight
        for i, doc in enumerate(standard_keyword_docs):
            doc_id = self._get_doc_id(doc)
            score = self.keyword_weight * (1.0 - (i / max(1, len(standard_keyword_docs)))) * 0.8  # 20% penalty
            
            if doc_id in unique_docs:
                unique_docs[doc_id]["score"] += score
                unique_docs[doc_id]["sources"].append("standard_keyword")
            else:
                unique_docs[doc_id] = {"doc": doc, "score": score, "sources": ["standard_keyword"]}
        
        # Sort by score and return top results
        sorted_docs = sorted(unique_docs.values(), key=lambda x: x["score"], reverse=True)
        return [item["doc"] for item in sorted_docs[:self.rerank_top_k]]
    
    def _get_field_aware_matches(self, query: str) -> List[Tuple[Document, float]]:
        """Get documents that match in specific metadata fields with boosted scores."""
        if not any([self.bm25_high_priority, self.bm25_medium_priority, self.bm25_all_fields]):
            return []
        
        query_tokens = query.lower().split()
        field_matches = []
        
        try:
            # Search in high priority fields (configurable boost)
            if self.bm25_high_priority:
                scores = self.bm25_high_priority.get_scores(query_tokens)
                for i, score in enumerate(scores):
                    if score > 0 and i < len(self.documents):
                        field_matches.append((self.documents[i], score * settings.HIGH_PRIORITY_FIELD_BOOST))
            
            # Search in medium priority fields (configurable boost)
            if self.bm25_medium_priority:
                scores = self.bm25_medium_priority.get_scores(query_tokens)
                for i, score in enumerate(scores):
                    if score > 0 and i < len(self.documents):
                        field_matches.append((self.documents[i], score * settings.MEDIUM_PRIORITY_FIELD_BOOST))
            
            # Search in all fields (1x boost)
            if self.bm25_all_fields:
                scores = self.bm25_all_fields.get_scores(query_tokens)
                for i, score in enumerate(scores):
                    if score > 0 and i < len(self.documents):
                        field_matches.append((self.documents[i], score))
            
            # Remove duplicates, keeping highest score
            unique_matches = {}
            for doc, score in field_matches:
                doc_id = self._get_doc_id(doc)
                if doc_id not in unique_matches or score > unique_matches[doc_id][1]:
                    unique_matches[doc_id] = (doc, score)
            
            # Sort by score and return top matches
            sorted_matches = sorted(unique_matches.values(), key=lambda x: x[1], reverse=True)
            return sorted_matches[:self.rerank_top_k]
            
        except Exception as e:
            logger.error(f"Error in field-aware matching: {str(e)}")
            return []
    
    def _get_doc_id(self, doc: Document) -> str:
        """Generate unique ID for document."""
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "")
        row = doc.metadata.get("row", "")
        content_hash = hash(doc.page_content[:100]) % 10000
        return f"{source}_{page}_{row}_{content_hash}"

class VectorStore:
    """Vector store for document embeddings and retrieval."""
    
    def __init__(self, 
                 embedding_provider: str = "google", 
                 api_key: Optional[str] = None,
                 repository_path: Optional[str] = None,
                 persist_directory: Optional[str] = None,
                 use_hybrid_search: bool = True):
        """
        Initialize the vector store.
        
        Args:
            embedding_provider: Provider for embeddings
            api_key: API key for the embedding provider
            repository_path: Path to the directory containing documents
            persist_directory: Directory to persist the vector store
            use_hybrid_search: Whether to use hybrid search
        """
        self.embedding_provider = embedding_provider
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.repository_path = repository_path or str(settings.INFO_FILES_DIR)
        self.persist_directory = persist_directory or str(settings.CHROMA_DB_DIR)
        self.use_hybrid_search = use_hybrid_search
        
        # Initialize embeddings
        self.embeddings = self._initialize_embeddings()
        
        # Cache for query results
        self.query_cache = {}
        self.cache_expiry = settings.QUERY_CACHE_EXPIRY
        
        # Text splitters
        self.default_text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.DEFAULT_CHUNK_SIZE,
            chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP,
            length_function=len,
        )
        
        self.risk_entry_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RISK_ENTRY_CHUNK_SIZE,
            chunk_overlap=settings.RISK_ENTRY_CHUNK_OVERLAP,
            length_function=len,
        )
        
        # Initialize components
        self.vector_store = None
        self.keyword_retriever = None
        self.hybrid_retriever = None
        self.multi_strategy_retriever = None  # New multi-strategy retriever
        self.structured_data = []
        self.all_documents = []
        
        # Document processor
        self.document_processor = DocumentProcessor()
        
        # Fact extractor for metadata enrichment
        self.fact_extractor = FactExtractor()
        
        # Ensure directories exist
        settings.ensure_directories()
    
    def initialize(self) -> bool:
        """
        Initialize vector store with robust error handling.
        
        This method handles both fresh setup and existing store loading
        with a unified approach that doesn't need fallbacks.
        """
        try:
            logger.info(f"Initializing vector store - repository: {self.repository_path}, persist: {self.persist_directory}")
            
            # Check if repository path exists
            if not self.repository_path or not os.path.exists(self.repository_path):
                logger.error(f"Repository path {self.repository_path} does not exist")
                return False
            
            logger.info(f"Repository path exists with {len(os.listdir(self.repository_path))} items")
            
            # Determine initialization path
            if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
                logger.info(f"Existing vector store found at {self.persist_directory} - loading")
                result = self.load_existing_store()
                logger.info(f"Load existing store result: {result}")
                return result
            else:
                logger.info(f"No existing vector store found at {self.persist_directory} - creating new one")
                result = self.ingest_documents()
                logger.info(f"Ingest documents result: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Error during vector store initialization: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _initialize_embeddings(self):
        """Initialize embeddings based on the provider."""
        if self.embedding_provider.lower() == "google":
            try:
                embeddings = GoogleGenerativeAIEmbeddings(
                    model=settings.EMBEDDING_MODEL_NAME,
                    google_api_key=self.api_key,
                    task_type="retrieval_query"
                )
                # Test the embeddings
                test_embedding = embeddings.embed_query("test query for embeddings")
                if test_embedding and len(test_embedding) > 0:
                    logger.info("Embeddings test successful")
                    return embeddings
                else:
                    logger.error("Embeddings test failed - returned empty embedding")
                    raise ValueError("Empty embedding result")
            except Exception as e:
                logger.error(f"Error initializing Google embeddings: {str(e)}")
                raise
        else:
            raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")
    
    def ingest_documents(self) -> bool:
        """Ingest documents from the repository path into the vector store."""
        if not self.repository_path or not os.path.exists(self.repository_path):
            logger.error(f"Repository path {self.repository_path} does not exist")
            return False
        
        try:
            logger.info(f"Loading documents from {self.repository_path}")
            
            self.all_documents = []
            base_path = Path(self.repository_path)
            
            files_processed = 0
            files_failed = 0
            
            # Process files in the repository
            for file_path in base_path.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    try:
                        docs = self._process_file(file_path)
                        if docs:
                            self.all_documents.extend(docs)
                            files_processed += 1
                            logger.info(f"Successfully processed {file_path.name}: {len(docs)} documents")
                        else:
                            logger.warning(f"No documents extracted from {file_path.name}")
                    except Exception as e:
                        logger.error(f"Error processing file {file_path.name}: {str(e)}")
                        files_failed += 1
            
            # ALSO process doc_snippets directory for preprint and other chunks
            snippets_path = Path(self.repository_path).parent / 'doc_snippets'
            if snippets_path.exists():
                logger.info(f"Processing doc_snippets directory at {snippets_path}")
                snippet_count = 0
                
                # Process RID-PREP files (preprint chunks)
                for snippet_file in snippets_path.glob('RID-PREP-*.txt'):
                    try:
                        docs = self._process_snippet_file(snippet_file)
                        if docs:
                            self.all_documents.extend(docs)
                            snippet_count += len(docs)
                    except Exception as e:
                        logger.error(f"Error processing snippet {snippet_file.name}: {str(e)}")
                
                logger.info(f"Processed {snippet_count} preprint snippets from doc_snippets")
            
            logger.info(f"Document processing summary: {files_processed} processed, {files_failed} with errors")
            logger.info(f"Loaded {len(self.all_documents)} total documents")
            
            if not self.all_documents:
                logger.error("No documents were loaded")
                return False
            
            # Split documents into chunks
            all_splits = []
            for doc in self.all_documents:
                if 'risk_entry' in doc.metadata.get('file_type', ''):
                    splits = self.risk_entry_splitter.split_documents([doc])
                else:
                    splits = self.default_text_splitter.split_documents([doc])
                all_splits.extend(splits)
            
            logger.info(f"Split into {len(all_splits)} chunks")
            
            # Create vector store
            if os.path.exists(self.persist_directory):
                # Load existing vector store
                try:
                    logger.info(f"Loading existing vector store from {self.persist_directory}")
                    self.vector_store = Chroma(
                        persist_directory=self.persist_directory,
                        embedding_function=self.embeddings
                    )
                    # Add new documents
                    self.vector_store.add_documents(all_splits)
                except Exception as e:
                    logger.warning(f"Error loading existing vector store: {str(e)}")
                    # Create new one
                    logger.info(f"Creating new vector store in {self.persist_directory}")
                    self.vector_store = Chroma.from_documents(
                        documents=all_splits,
                        embedding=self.embeddings,
                        persist_directory=self.persist_directory
                    )
            else:
                logger.info(f"Creating new vector store in {self.persist_directory}")
                self.vector_store = Chroma.from_documents(
                    documents=all_splits,
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory
                )
            
            logger.info("Vector store created and persisted successfully")
            
            # Ensure complete initialization
            success = self._ensure_complete_initialization()
            if not success:
                logger.error("Vector store created but initialization incomplete")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error during document ingestion: {str(e)}")
            return False
    
    def _ensure_complete_initialization(self) -> bool:
        """Ensure vector store is completely initialized with all components."""
        try:
            # Check if vector store exists
            if not self.vector_store:
                logger.error("Vector store not initialized")
                return False
            
            # Test vector store basic functionality
            try:
                test_results = self.vector_store.similarity_search("test query", k=1)
                logger.info(f"Vector store test successful - found {len(test_results)} results")
            except Exception as e:
                logger.error(f"Vector store test failed: {str(e)}")
                return False
            
            # Set up hybrid retriever if enabled and not already set up
            if self.use_hybrid_search and not self.hybrid_retriever:
                try:
                    # Get all documents from the vector store to rebuild BM25
                    # Use the Chroma collection's get() method to retrieve all documents
                    if hasattr(self.vector_store, '_collection'):
                        all_docs = self.vector_store._collection.get()
                    else:
                        # Fallback: try to get documents via similarity search with large k
                        logger.warning("Using fallback document retrieval method")
                        sample_docs = self.vector_store.similarity_search("", k=1000)
                        all_docs = {
                            'documents': [doc.page_content for doc in sample_docs],
                            'metadatas': [doc.metadata for doc in sample_docs]
                        }
                    
                    if not all_docs or not all_docs.get('documents'):
                        logger.warning("No documents found in vector store - disabling hybrid search")
                        self.use_hybrid_search = False
                        return True
                    
                    # Reconstruct Document objects for BM25
                    documents = []
                    for i, text in enumerate(all_docs['documents']):
                        if text:  # Skip empty documents
                            metadata = all_docs['metadatas'][i] if all_docs.get('metadatas') and i < len(all_docs['metadatas']) else {}
                            doc = Document(page_content=text, metadata=metadata or {})
                            documents.append(doc)
                    
                    logger.info(f"Building BM25 retriever with {len(documents)} documents")
                    self.keyword_retriever = BM25Retriever.from_documents(documents)
                    self.keyword_retriever.k = settings.BM25_TOP_K
                    
                    # Initialize multi-strategy retriever with all documents
                    try:
                        self.multi_strategy_retriever = MultiStrategyRetriever(
                            vector_store=self.vector_store,
                            all_documents=documents
                        )
                        logger.info("Multi-strategy retriever initialized successfully")
                    except Exception as e:
                        logger.error(f"Failed to initialize multi-strategy retriever: {str(e)}")
                        self.multi_strategy_retriever = None
                    
                    # Choose retriever type based on configuration
                    if settings.USE_FIELD_AWARE_HYBRID:
                        logger.info("Setting up field-aware hybrid retriever")
                        self.hybrid_retriever = FieldAwareHybridRetriever(
                            vector_retriever=self.vector_store.as_retriever(),
                            keyword_retriever=self.keyword_retriever,
                            documents=documents
                        )
                        logger.info("Field-aware hybrid retriever initialized successfully")
                    else:
                        logger.info("Setting up basic hybrid retriever")
                        # For basic hybrid, we'll use the keyword retriever directly
                        # and combine in get_relevant_documents method
                        self.hybrid_retriever = "basic"  # Flag for basic hybrid mode
                        logger.info("Basic hybrid retriever mode enabled")
                    
                except Exception as e:
                    logger.error(f"Error setting up hybrid retriever: {str(e)}")
                    logger.info("Falling back to vector-only search")
                    self.use_hybrid_search = False
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring complete initialization: {str(e)}")
            return False
    
    def load_existing_store(self) -> bool:
        """Load existing vector store and ensure complete initialization."""
        try:
            if not os.path.exists(self.persist_directory):
                logger.error(f"Vector store directory {self.persist_directory} does not exist")
                return False
            
            # Load existing vector store
            logger.info(f"Loading existing vector store from {self.persist_directory}")
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            
            # Check if preprint snippets are already in the store
            test_result = self.vector_store.similarity_search("PRISMA methodology systematic review", k=1)
            has_preprint = any("RID-PREP" in str(doc.metadata.get('rid', '')) for doc in test_result)
            
            if not has_preprint:
                # CRITICAL: Load and add snippet documents to the existing store
                snippets_path = Path(self.repository_path).parent / 'doc_snippets'
                if snippets_path.exists():
                    logger.info(f"Preprint snippets not found in store - loading from {snippets_path}")
                    snippet_docs = []
                    
                    # Process RID-PREP files (preprint chunks)
                    for snippet_file in snippets_path.glob('RID-PREP-*.txt'):
                        try:
                            docs = self._process_snippet_file(snippet_file)
                            if docs:
                                snippet_docs.extend(docs)
                        except Exception as e:
                            logger.error(f"Error processing snippet {snippet_file.name}: {str(e)}")
                    
                    if snippet_docs:
                        logger.info(f"Adding {len(snippet_docs)} snippet documents to existing vector store")
                        # Add documents to the existing store
                        self.vector_store.add_documents(snippet_docs)
                        logger.info("Snippet documents added successfully")
                    else:
                        logger.warning("No snippet documents found to add")
                else:
                    logger.warning(f"Snippets directory {snippets_path} does not exist")
            else:
                logger.info("Preprint snippets already present in vector store")
            
            # Ensure complete initialization
            success = self._ensure_complete_initialization()
            if success:
                logger.info("Vector store loaded and fully initialized")
            else:
                logger.error("Vector store loaded but initialization incomplete")
            
            return success
            
        except Exception as e:
            logger.error(f"Error loading existing vector store: {str(e)}")
            return False
    
    def _process_file(self, file_path: Path) -> List[Document]:
        """Process a single file."""
        file_extension = file_path.suffix.lower()
        
        if file_extension in ['.xlsx', '.xls']:
            return self.document_processor.process_excel_file(file_path)
        elif file_extension == '.txt':
            return self._process_text_file(file_path)
        elif file_extension == '.docx':
            return self._process_docx_file(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_extension}")
            return []
    
    def _process_snippet_file(self, file_path: Path) -> List[Document]:
        """Process snippet files from doc_snippets directory."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the snippet format
            lines = content.split('\n')
            metadata = {}
            actual_content = []
            in_content = False
            
            for line in lines:
                if line.startswith('Repository ID:'):
                    metadata['rid'] = line.split(':', 1)[1].strip()
                elif line.startswith('Source:'):
                    metadata['source'] = line.split(':', 1)[1].strip()
                elif line.startswith('Section:'):
                    metadata['section'] = line.split(':', 1)[1].strip()
                elif line.startswith('Content Type:'):
                    metadata['content_type'] = line.split(':', 1)[1].strip()
                elif line.startswith('Content:'):
                    in_content = True
                elif in_content:
                    actual_content.append(line)
            
            # Create document
            doc = Document(
                page_content='\n'.join(actual_content).strip(),
                metadata={
                    **metadata,
                    'file_type': 'snippet',
                    'file_name': file_path.name,
                    'type': 'preprint' if 'PREP' in file_path.name else 'snippet'
                }
            )
            
            return [doc]
            
        except Exception as e:
            logger.error(f"Error processing snippet file {file_path}: {str(e)}")
            return []
    
    def _process_text_file(self, file_path: Path) -> List[Document]:
        """Process text files with RID assignment."""
        try:
            loader = TextLoader(str(file_path), encoding='utf-8')
            documents = loader.load()
            
            # Add metadata and assign RIDs
            processed_docs = []
            for doc in documents:
                doc.metadata.update({
                    "file_type": "text",
                    "title": file_path.name
                })
                
                # Assign RID using DocumentProcessor
                self.document_processor._assign_rid(doc)
                processed_docs.append(doc)
            
            # Save RID registry after processing
            self.document_processor._save_rid_registry()
            
            return processed_docs
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {str(e)}")
            return []
    
    def _process_docx_file(self, file_path: Path) -> List[Document]:
        """Process DOCX files with RID assignment and proper chunking."""
        try:
            loader = Docx2txtLoader(str(file_path))
            documents = loader.load()
            
            # Split the document into chunks for better retrieval
            # Use a larger chunk size for research papers
            if "preprint" in str(file_path).lower():
                # For preprint, use specific chunking strategy
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1500,
                    chunk_overlap=200,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
            else:
                text_splitter = self.default_text_splitter
            
            # Split documents into chunks
            split_docs = text_splitter.split_documents(documents)
            
            # Add metadata and assign RIDs to each chunk
            processed_docs = []
            for i, doc in enumerate(split_docs):
                doc.metadata.update({
                    "file_type": "docx",
                    "document_type": "research_paper" if "preprint" in str(file_path).lower() else "document",
                    "title": file_path.stem,
                    "source": str(file_path),
                    "chunk_index": i,
                    "total_chunks": len(split_docs)
                })
                
                # Add special metadata for preprint
                if "preprint" in str(file_path).lower():
                    doc.metadata.update({
                        "type": "preprint",
                        "year": "2024"  # Keep year but remove hardcoded authors
                    })
                
                # Extract facts and enrich metadata (not hardcoded!)
                doc = self.fact_extractor.enrich_document(doc)
                
                # Assign RID using DocumentProcessor
                self.document_processor._assign_rid(doc)
                processed_docs.append(doc)
            
            # Save RID registry after processing
            self.document_processor._save_rid_registry()
            
            logger.info(f"Processed DOCX file {file_path.name}: {len(processed_docs)} chunks")
            return processed_docs
        except Exception as e:
            logger.error(f"Error processing DOCX file {file_path}: {str(e)}")
            return []
    
    def get_relevant_documents(self, query: str, k: int = 5, domain: str = None) -> List[Document]:
        """Get relevant documents for a query with relevance threshold filtering."""
        # Check cache
        cache_key = f"{query}_{k}_{domain}"
        if cache_key in self.query_cache:
            cached_time, cached_docs = self.query_cache[cache_key]
            if time.time() - cached_time < self.cache_expiry:
                return cached_docs
        
        try:
            # Use multi-strategy retriever if available (prioritize for factual queries)
            if self.multi_strategy_retriever:
                # Check if this is a factual query that needs special handling
                query_lower = query.lower()
                is_factual = any(term in query_lower for term in [
                    'how many', 'number', 'total', 'count',
                    'who', 'author', 'wrote', 'created',
                    'methodology', 'method', 'approach',
                    'when', 'where', 'what year'
                ])
                
                # Also check for numbers in query
                import re
                has_numbers = bool(re.search(r'\d+', query))
                
                if is_factual or has_numbers:
                    logger.info(f"Using multi-strategy retriever for factual query: {query}")
                    docs = self.multi_strategy_retriever.retrieve(query, k=k)
                    
                    # Cache and return
                    self.query_cache[cache_key] = (time.time(), docs)
                    return docs
            
            # Fall back to existing retrieval logic
        
            # Detect domain if not provided
            if not domain:
                domain = domain_classifier.classify_domain(query)
            
            # Get relevance threshold for this domain
            threshold = settings.DOMAIN_RELEVANCE_THRESHOLDS.get(domain, settings.MINIMUM_RELEVANCE_THRESHOLD)
            
            # Retrieve documents with scores
            if self.use_hybrid_search and self.hybrid_retriever:
                if isinstance(self.hybrid_retriever, FieldAwareHybridRetriever):
                    # Field-aware hybrid retrieval
                    docs_with_scores = self._get_docs_with_scores_field_aware_hybrid(query, k * 2)  # Get more to filter
                elif self.hybrid_retriever == "basic":
                    # Basic hybrid retrieval
                    docs_with_scores = self._get_docs_with_scores_basic_hybrid(query, k * 2)  # Get more to filter
                else:
                    # Fallback to vector
                    docs_with_scores = self._get_docs_with_scores_vector(query, k * 2)
            elif self.vector_store:
                docs_with_scores = self._get_docs_with_scores_vector(query, k * 2)
            else:
                logger.error("No retriever available")
                return []
            
            # Apply relevance threshold filtering
            filtered_docs = []
            filtered_scores = []
            for doc, score in docs_with_scores:
                if score >= threshold:
                    filtered_docs.append(doc)
                    filtered_scores.append(score)
                    if len(filtered_docs) >= settings.MAX_DOCS_ABOVE_THRESHOLD * 2:  # Get more for MMR
                        break
            
            # Dual-threshold system: ensure recall floor (at least 1 doc per top-2 domains)
            if not filtered_docs:
                logger.info(f"No documents above threshold {threshold:.3f}, applying recall floor...")
                # Expand search and lower threshold to ensure minimum documents
                expanded_docs_with_scores = self._expand_search_for_recall(query, k * 3, threshold)
                if expanded_docs_with_scores:
                    # Take at least 1 document even if below threshold
                    filtered_docs = [doc for doc, score in expanded_docs_with_scores[:2]]
                    filtered_scores = [score for doc, score in expanded_docs_with_scores[:2]]
                    logger.info(f"Recall floor applied: retrieved {len(filtered_docs)} documents with lower threshold")
                else:
                    logger.info(f"No documents found even with expanded search for query: {query[:50]}...")
                    return []
            
            # Apply advanced retrieval techniques (MMR deduplication + cross-encoder re-ranking)
            final_docs = advanced_retriever.retrieve_and_rerank(
                documents=filtered_docs,
                query=query,
                original_scores=filtered_scores,
                max_documents=min(settings.MAX_DOCS_ABOVE_THRESHOLD, len(filtered_docs))
            )
            
            # Log the core retrieval results first
            logger.info(f"Retrieved {len(final_docs)} documents above threshold {threshold:.3f}")
            
            # Add domain-specific documents if enhanced search is enabled
            if (domain != 'other' and domain_classifier.has_enhanced_search(domain)):
                domain_docs = self._get_domain_specific_docs(domain)
                final_docs.extend(domain_docs)
                logger.info(f"Added {len(domain_docs)} domain-specific documents for {domain}")
                logger.info(f"Total documents after domain enhancement: {len(final_docs)}")
            
            # Cache the results
            self.query_cache[cache_key] = (time.time(), final_docs)
            
            return final_docs[:k]  # Final limit
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []
    
    def _expand_search_for_recall(self, query: str, k: int, original_threshold: float) -> List[Tuple[Document, float]]:
        """Expand search with lower threshold to ensure minimum document recall."""
        try:
            # Lower the threshold by 50% for recall search
            recall_threshold = original_threshold * 0.5
            
            # Get more documents with expanded search
            if self.use_hybrid_search and self.hybrid_retriever:
                if isinstance(self.hybrid_retriever, FieldAwareHybridRetriever):
                    docs_with_scores = self._get_docs_with_scores_field_aware_hybrid(query, k)
                elif self.hybrid_retriever == "basic":
                    docs_with_scores = self._get_docs_with_scores_basic_hybrid(query, k)
                else:
                    docs_with_scores = self._get_docs_with_scores_vector(query, k)
            else:
                docs_with_scores = self._get_docs_with_scores_vector(query, k)
            
            # Filter with lower threshold
            recall_docs = []
            for doc, score in docs_with_scores:
                if score >= recall_threshold:
                    recall_docs.append((doc, score))
                    if len(recall_docs) >= 3:  # Limit recall expansion
                        break
            
            return recall_docs
            
        except Exception as e:
            logger.error(f"Error in expand search for recall: {str(e)}")
            return []
    
    def _get_docs_with_scores_vector(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """Get documents with similarity scores from vector search."""
        try:
            # Use similarity_search_with_score if available
            if hasattr(self.vector_store, 'similarity_search_with_score'):
                return self.vector_store.similarity_search_with_score(query, k=k)
            else:
                # Fallback: get docs without scores (assume high relevance)
                docs = self.vector_store.similarity_search(query, k=k)
                return [(doc, 0.8) for doc in docs]  # Assume decent relevance
        except Exception as e:
            logger.error(f"Error getting vector docs with scores: {str(e)}")
            return []
    
    def _get_docs_with_scores_field_aware_hybrid(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """Get documents with scores from field-aware hybrid search."""
        try:
            # For field-aware hybrid search, we'll approximate scores with metadata boosts
            try:
                docs = self.hybrid_retriever.invoke(query)[:k]
            except:
                # Fallback to deprecated method if invoke not available
                docs = self.hybrid_retriever.get_relevant_documents(query)[:k]
            # Assign decreasing scores based on rank with metadata boosting
            scored_docs = []
            for i, doc in enumerate(docs):
                base_score = max(0.9 - (i * 0.1), 0.1)  # Start at 0.9, decrease by 0.1 per rank
                
                # Apply metadata boosting using settings configuration
                boost_factor = 1.0
                
                # Boost for high-priority metadata matches
                if 'search_high_priority' in doc.metadata:
                    query_lower = query.lower()
                    high_priority_text = doc.metadata['search_high_priority'].lower()
                    if any(word in high_priority_text for word in query_lower.split()):
                        boost_factor += (settings.HIGH_PRIORITY_FIELD_BOOST - 1.0) / 10  # Scale down for scoring
                
                # Boost for domain-specific documents
                if 'domain' in doc.metadata and doc.metadata['domain'] != 'Unspecified':
                    boost_factor += settings.DOMAIN_SPECIFIC_BOOST
                
                # Boost for AI risk entries (primary content)
                if doc.metadata.get('file_type') == 'ai_risk_entry':
                    boost_factor += settings.AI_RISK_ENTRY_BOOST
                
                # Boost for domain summaries (comprehensive content)
                if doc.metadata.get('file_type') == 'ai_risk_domain_summary':
                    boost_factor += settings.DOMAIN_SUMMARY_BOOST
                
                final_score = min(base_score * boost_factor, 1.0)
                scored_docs.append((doc, final_score))
            
            return scored_docs
        except Exception as e:
            logger.error(f"Error getting field-aware hybrid docs with scores: {str(e)}")
            return []
    
    def _get_docs_with_scores_basic_hybrid(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """Get documents with scores from basic hybrid search (vector + keyword)."""
        try:
            # Get vector results
            vector_docs_with_scores = self._get_docs_with_scores_vector(query, k)
            
            # Get keyword results
            if self.keyword_retriever:
                keyword_docs = self.keyword_retriever.get_relevant_documents(query)[:k]
                keyword_docs_with_scores = [(doc, 0.7) for doc in keyword_docs]  # Assign decent scores
            else:
                keyword_docs_with_scores = []
            
            # Combine and deduplicate
            combined_docs = {}
            
            # Add vector docs with vector weight
            for doc, score in vector_docs_with_scores:
                doc_id = self._generate_doc_id(doc)
                combined_docs[doc_id] = (doc, score * settings.VECTOR_WEIGHT)
            
            # Add keyword docs with keyword weight (combining scores if duplicate)
            for doc, score in keyword_docs_with_scores:
                doc_id = self._generate_doc_id(doc)
                if doc_id in combined_docs:
                    existing_doc, existing_score = combined_docs[doc_id]
                    combined_docs[doc_id] = (existing_doc, existing_score + (score * settings.KEYWORD_WEIGHT))
                else:
                    combined_docs[doc_id] = (doc, score * settings.KEYWORD_WEIGHT)
            
            # Sort by combined score and return
            sorted_docs = sorted(combined_docs.values(), key=lambda x: x[1], reverse=True)
            return sorted_docs[:k]
            
        except Exception as e:
            logger.error(f"Error getting basic hybrid docs with scores: {str(e)}")
            return []
    
    def _generate_doc_id(self, doc: Document) -> str:
        """Generate unique ID for document deduplication."""
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "")
        row = doc.metadata.get("row", "")
        content_hash = hash(doc.page_content[:100]) % 10000
        return f"{source}_{page}_{row}_{content_hash}"
    
    def _get_domain_specific_docs(self, domain: str) -> List[Document]:
        """Get domain-specific documents using generic domain system."""
        if not self.vector_store:
            return []
        
        try:
            # Search for domain-related content using configured queries
            domain_queries = domain_classifier.get_domain_queries(domain)
            
            docs = []
            for query in domain_queries:
                search_docs = self.vector_store.similarity_search(query, k=2)
                docs.extend(search_docs)
            
            # Remove duplicates
            seen_content = set()
            unique_docs = []
            for doc in docs:
                content_hash = hash(doc.page_content[:100])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_docs.append(doc)
            
            # Get domain-specific document limit
            doc_limit = domain_classifier.get_document_limit(domain)
            return unique_docs[:doc_limit]
            
        except Exception as e:
            logger.error(f"Error getting {domain}-specific docs: {str(e)}")
            return []
    
    def _get_employment_specific_docs(self) -> List[Document]:
        """Legacy method - use _get_domain_specific_docs('socioeconomic') instead."""
        return self._get_domain_specific_docs('socioeconomic')
    
    def format_context_from_docs(self, docs: List[Document]) -> str:
        """Format documents into context string with evidence budget and direct quotes."""
        if not docs:
            return ""
        
        context = settings.CONTEXT_TEMPLATE_HEADER
        
        # Alternate document order by domain to prevent single-domain dominance
        domain_balanced_docs = self._balance_docs_by_domain(docs)
        
        for i, doc in enumerate(domain_balanced_docs, 1):
            # Add document metadata if available
            title = doc.metadata.get('title', f'Document {i}')
            domain = doc.metadata.get('domain', '')
            
            section_header = settings.CONTEXT_SECTION_TEMPLATE.format(section_number=i)
            if domain and domain != 'Unspecified':
                section_header += settings.CONTEXT_DOMAIN_TEMPLATE.format(domain=domain)
            
            # Apply evidence budget (1200 chars for synthesis) with direct quote insertion
            formatted_content = self._format_content_with_evidence_budget(doc.page_content, 1200)
            
            context += section_header + settings.CONTEXT_SECTION_SEPARATOR.format(content=formatted_content)
        
        return context
    
    def _balance_docs_by_domain(self, docs: List[Document]) -> List[Document]:
        """Balance document order by domain to prevent single-domain dominance."""
        # Group documents by domain
        domain_groups = {}
        for doc in docs:
            domain = doc.metadata.get('domain', 'other')
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(doc)
        
        # Interleave documents from different domains
        balanced_docs = []
        max_per_domain = max(len(group) for group in domain_groups.values())
        
        for i in range(max_per_domain):
            for domain, group in domain_groups.items():
                if i < len(group):
                    balanced_docs.append(group[i])
        
        return balanced_docs
    
    def _format_content_with_evidence_budget(self, content: str, max_chars: int) -> str:
        """Format content with evidence budget and include direct quotes."""
        if len(content) <= max_chars:
            return content
        
        # Truncate content but try to preserve complete sentences
        truncated = content[:max_chars]
        
        # Find the last complete sentence within budget
        import re
        sentences = re.split(r'(?<=[.!?])\s+', truncated)
        if len(sentences) > 1:
            # Remove the last incomplete sentence
            truncated = '. '.join(sentences[:-1]) + '.'
        
        # Try to extract a direct quote (≤140 chars) to add grounding
        quote = self._extract_direct_quote(content, 140)
        if quote and quote not in truncated:
            # Add the quote as highlighted text
            truncated += f'\n\n► "{quote}"'
        
        return truncated
    
    def _extract_direct_quote(self, content: str, max_chars: int) -> str:
        """Extract a meaningful direct quote from content."""
        import re
        
        # Look for text in quotes first
        quote_patterns = [
            r'"([^"]{20,})"',  # Text in double quotes
            r"'([^']{20,})'",  # Text in single quotes
        ]
        
        for pattern in quote_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) <= max_chars:
                    return match
        
        # If no quotes found, extract a meaningful sentence
        sentences = re.split(r'(?<=[.!?])\s+', content)
        for sentence in sentences:
            if 20 <= len(sentence) <= max_chars and ('risk' in sentence.lower() or 'AI' in sentence):
                return sentence
        
        return None
    
    def get_scqa_enhanced_documents(self, 
                                   query: str, 
                                   k: int = 5,
                                   preferred_component: Optional[SCQAComponent] = None) -> List[Document]:
        """Get documents with SCQA enhancement and optional component filtering."""
        
        # Get regular documents first
        docs = self.get_relevant_documents(query, k * 2)  # Get more for filtering
        
        if not docs:
            return []
        
        try:
            # Enhance all documents with SCQA if not already done
            enhanced_docs = []
            for doc in docs:
                if 'scqa_structure' not in doc.metadata:
                    enhanced_doc = scqa_manager.enhance_document_with_scqa(doc)
                    enhanced_docs.append(enhanced_doc)
                else:
                    enhanced_docs.append(doc)
            
            # Filter by SCQA component if requested
            if preferred_component:
                component_docs = scqa_manager.get_documents_by_scqa_component(
                    enhanced_docs, preferred_component, query
                )
                # If we get good matches, prioritize them
                if component_docs:
                    # Combine component matches with other docs
                    remaining_docs = [doc for doc in enhanced_docs if doc not in component_docs]
                    final_docs = component_docs + remaining_docs
                    return final_docs[:k]
            
            return enhanced_docs[:k]
            
        except Exception as e:
            logger.error(f"Error in SCQA enhancement: {str(e)}")
            return docs[:k]
    
    def get_taxonomy_statistics(self) -> Dict[str, Any]:
        """Get SCQA taxonomy statistics for all documents."""
        if not self.all_documents:
            return {}
        
        try:
            return scqa_manager.get_taxonomy_statistics(self.all_documents)
        except Exception as e:
            logger.error(f"Error getting taxonomy statistics: {str(e)}")
            return {}