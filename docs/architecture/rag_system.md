# AIRI Chatbot RAG System Architecture

This document provides a comprehensive overview of the Retrieval-Augmented Generation (RAG) system used in the AIRI Chatbot.

## Table of Contents
1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [Key Files and Their Roles](#key-files-and-their-roles)
5. [Configuration Points](#configuration-points)
6. [How It Works](#how-it-works)

## System Overview

The AIRI Chatbot uses a sophisticated multi-strategy RAG system that combines:
- **Vector semantic search** (ChromaDB with Google Embeddings)
- **Keyword search** (BM25 algorithm)
- **Field-aware retrieval** (metadata boosting)
- **Intent classification** (routing queries to appropriate handlers)
- **Taxonomy-based responses** (structured preprint content)

### High-Level Architecture

```
User Query
    ↓
Intent Classification → Route to appropriate handler
    ↓
Query Processing → Enhance and analyze query
    ↓
Multi-Strategy Retrieval
    ├── Vector Search (semantic similarity)
    ├── BM25 Search (keyword matching)
    └── Field-Aware Search (metadata boosting)
    ↓
Hybrid Fusion → Combine and re-rank results
    ↓
Context Assembly → Prepare retrieved documents
    ↓
LLM Generation (Gemini) → Synthesize response
    ↓
Citation Service → Add clickable citations
    ↓
Response to User
```

## Core Components

### 1. Vector Store (`src/core/storage/vector_store.py`)

**Purpose:** Stores document embeddings and handles semantic retrieval.

**Technology:**
- ChromaDB for vector storage
- Google Generative AI Embeddings (text-embedding-004)
- RecursiveCharacterTextSplitter for chunking

**Key Features:**
- Hybrid search combining vector and keyword approaches
- Field-aware BM25 indices for metadata
- Document processing and ingestion
- Metadata enhancement (taxonomy, domains, categories)

**Main Class:** `VectorStore`
- Manages ChromaDB collection
- Handles document loading from `data/info_files/`
- Creates embeddings for documents
- Provides retrieval interface

**Retriever:** `FieldAwareHybridRetriever`
- Combines vector similarity and BM25 keyword search
- Uses metadata fields for boosting relevant results
- Configurable weights for vector vs keyword search
- Re-ranks results based on metadata priority

### 2. Multi-Strategy Retriever (`src/core/retrieval/multi_strategy_retriever.py`)

**Purpose:** Handles edge cases and specific query types.

**Strategies:**
- **Exact matching** - For numbers, names, specific terms
- **Regex search** - For formatted content (phone numbers, IDs, etc.)
- **Semantic search** - For conceptual queries
- **BM25 keyword** - For keyword-based queries

**Key Features:**
- Query analysis to determine appropriate strategy
- Clean document processing (removes punctuation issues)
- Confidence scoring for each strategy
- Result merging from multiple strategies

### 3. Query Processor (`src/core/query/processor.py`)

**Purpose:** Analyzes and enhances queries before retrieval.

**Capabilities:**
- Query expansion and refinement
- Intent detection
- Employment query handling
- Domain classification
- Technical term extraction

### 4. Intent Classifier (`src/core/query/intent_classifier.py`)

**Purpose:** Routes queries to appropriate handlers.

**Intent Categories:**
- `TAXONOMY_QUERY` - Questions about AI risk taxonomy → Uses preprint
- `EMPLOYMENT_QUERY` - Job/career questions → Uses employment handler
- `GENERAL_QUERY` - Standard questions → Uses RAG retrieval
- `GREETING` - Conversational → Direct response

### 5. Taxonomy Handler (`src/core/taxonomy/taxonomy_handler.py`)

**Purpose:** Handles taxonomy-specific queries using structured preprint data.

**Features:**
- SCQA taxonomy structure (Scenario, Complication, Question, Answer)
- Pre-indexed taxonomy concepts
- Structured responses with proper formatting
- Preprint citation handling

### 6. Chat Service (`src/core/services/chat_service.py`)

**Purpose:** Orchestrates the entire conversation flow.

**Responsibilities:**
- Intent-based routing
- Query processing coordination
- Retrieval execution
- Response generation via Gemini
- Citation management
- Conversation history
- Multi-language support

### 7. Gemini Model (`src/core/models/gemini.py`)

**Purpose:** LLM for response generation and synthesis.

**Features:**
- Google Gemini 1.5 Flash
- Streaming response support
- Context-aware generation
- System prompts for AI Risk Repository expertise

## Data Flow

### Standard Query Flow

1. **User Input** → Message received via API endpoint
2. **Intent Classification** → Determine query type
3. **Query Processing** → Enhance and analyze query
4. **Document Retrieval:**
   - Vector search finds semantically similar documents
   - BM25 search finds keyword matches
   - Field-aware search boosts results with matching metadata
   - Multi-strategy retriever handles edge cases
5. **Result Fusion:**
   - Combine results from different strategies
   - Remove duplicates
   - Re-rank based on relevance and metadata
6. **Context Preparation:**
   - Select top-k documents
   - Format as context for LLM
7. **Response Generation:**
   - Gemini synthesizes response from context
   - Maintains conversational tone
   - Stays grounded in retrieved documents
8. **Citation Addition:**
   - Extract source metadata
   - Create clickable citation links
   - Generate snippet IDs
9. **Response Delivery** → Stream to user

### Taxonomy Query Flow

1. **Intent = TAXONOMY_QUERY** → Route to TaxonomyHandler
2. **Taxonomy Lookup** → Find relevant taxonomy sections
3. **Structured Response** → Format with SCQA structure
4. **Preprint Citation** → Add preprint as source
5. **Response Delivery** → Stream to user

## Key Files and Their Roles

### Core RAG Implementation

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `src/core/storage/vector_store.py` | Vector database interface | `VectorStore`, `FieldAwareHybridRetriever` |
| `src/core/retrieval/multi_strategy_retriever.py` | Multi-strategy retrieval | `MultiStrategyRetriever` |
| `src/core/retrieval/advanced_retrieval.py` | Advanced retrieval logic | `advanced_retriever()` |
| `src/core/query/processor.py` | Query enhancement | `QueryProcessor` |
| `src/core/query/intent_classifier.py` | Intent routing | `IntentClassifier`, `IntentCategory` |
| `src/core/services/chat_service.py` | Main orchestration | `ChatService` |
| `src/core/models/gemini.py` | LLM interface | `GeminiModel` |
| `src/core/services/citation_service.py` | Citation management | `CitationService` |

### Supporting Components

| File | Purpose |
|------|---------|
| `src/core/storage/document_processor.py` | Document loading and chunking |
| `src/core/taxonomy/taxonomy_handler.py` | Taxonomy query handling |
| `src/core/taxonomy/scqa_taxonomy.py` | SCQA taxonomy structure |
| `src/core/metadata/metadata_loader.py` | Metadata extraction |
| `src/core/query/technical_handler.py` | Technical query processing |
| `src/config/settings.py` | Configuration parameters |

## Configuration Points

### Environment Variables (`.env`)

```bash
# Required
GEMINI_API_KEY=your-api-key

# Optional - Vector Store
CHROMA_DB_PATH=./data/chroma_db
EMBEDDING_MODEL=models/text-embedding-004

# Optional - Retrieval
USE_HYBRID_SEARCH=true
USE_FIELD_AWARE_HYBRID=true
VECTOR_WEIGHT=0.7              # 0.0-1.0, balance vector vs keyword
HYBRID_RERANK_TOP_K=10         # How many results to re-rank
```

### Settings (`src/config/settings.py`)

```python
# Retrieval Configuration
VECTOR_WEIGHT = 0.7            # Vector search weight (0-1)
HYBRID_RERANK_TOP_K = 10       # Results to re-rank
TOP_K_DOCS = 5                 # Documents to use for context

# Chunk Configuration
CHUNK_SIZE = 1000              # Characters per chunk
CHUNK_OVERLAP = 200            # Overlap between chunks

# Search Configuration
USE_HYBRID_SEARCH = True       # Enable hybrid search
USE_FIELD_AWARE_HYBRID = True  # Enable field-aware boosting
```

## How It Works

### Document Ingestion

When the application starts:
1. Scans `data/info_files/` for documents (.txt, .xlsx, .md)
2. Loads and chunks documents (1000 chars, 200 overlap)
3. Extracts metadata (taxonomy, domains, categories)
4. Generates embeddings using Google Embeddings
5. Stores in ChromaDB collection
6. Creates BM25 indices for keyword search
7. Builds field-aware indices for metadata

### Query Processing

When a query arrives:
1. **Intent Classification:**
   - Patterns/keywords determine intent category
   - Confidence score influences routing

2. **Query Enhancement:**
   - Expand employment queries with synonyms
   - Extract technical terms
   - Identify domain context

3. **Retrieval Execution:**
   - **Vector Search:** Embed query → Find similar embeddings
   - **BM25 Search:** Tokenize query → Score documents by term frequency
   - **Field-Aware Search:** Boost documents with matching metadata
   - **Multi-Strategy:** Apply specialized strategies for numbers/names

4. **Result Fusion:**
   - Combine results from all strategies
   - Apply weights (default: 70% vector, 30% keyword)
   - Remove duplicates
   - Re-rank by metadata priority

5. **Response Generation:**
   - Select top-k documents (default: 5)
   - Format as context
   - Prompt Gemini with context and query
   - Stream response

6. **Citation Addition:**
   - Extract source metadata from retrieved docs
   - Create snippet IDs
   - Add clickable links to response

### Metadata Boosting

Field-aware retrieval gives priority to matches in:
- **High Priority:** Title, Domain, Category
- **Medium Priority:** Subdomain, Specific domains
- **All Fields:** Combined searchable content

This ensures queries like "healthcare AI risks" prioritize documents with "Healthcare" in their domain metadata.

## Modifying the System

See [Modifying RAG Guide](modifying_rag.md) for:
- Switching retrieval methods
- Changing vector stores
- Adjusting weights and parameters
- Adding new retrieval strategies
- Testing modifications

## Performance Considerations

### Optimization Points

1. **Embedding Generation:** Cached after first load
2. **BM25 Indices:** Built once at startup
3. **Result Caching:** Consider Redis for frequently asked queries
4. **Chunk Size:** Balance context vs. precision
5. **Top-K Selection:** More docs = better context but slower generation

### Trade-offs

- **Higher Vector Weight (0.8+):** Better for conceptual questions, worse for specific terms
- **Higher Keyword Weight (0.3+):** Better for exact matches, worse for synonyms
- **More Chunks:** Better coverage, but slower retrieval
- **Larger Chunks:** Better context, but less precise matching

## Troubleshooting

### Poor Retrieval Quality
- Check `VECTOR_WEIGHT` - adjust based on query type
- Verify documents are properly indexed
- Review metadata quality
- Test with different chunk sizes

### Slow Response Time
- Reduce `HYBRID_RERANK_TOP_K`
- Decrease `TOP_K_DOCS`
- Consider result caching
- Check database size

### Missing Citations
- Ensure documents have proper metadata
- Verify snippet database is populated
- Check citation service configuration

## Related Documentation

- [Message Processing Logic](MESSAGE_PROCESSING_LOGIC.md)
- [Modifying RAG System](modifying_rag.md)
- [Performance Plan](performance_plan.md)
- [Snippet System](snippet_system.md)
