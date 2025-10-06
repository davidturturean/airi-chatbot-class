# How to Modify the RAG System

This guide provides step-by-step instructions for common RAG system modifications.

## Table of Contents
1. [Switching Retrieval Methods](#switching-retrieval-methods)
2. [Changing Vector Stores](#changing-vector-stores)
3. [Adjusting Weights and Parameters](#adjusting-weights-and-parameters)
4. [Adding New Retrieval Strategies](#adding-new-retrieval-strategies)
5. [Modifying Response Generation](#modifying-response-generation)
6. [Testing Your Changes](#testing-your-changes)

## Switching Retrieval Methods

### Current Implementation

The system currently uses:
- **Hybrid Retrieval:** Combines semantic (vector) + keyword (BM25) search
- **Field-Aware Boosting:** Considers metadata fields (title, domain, category)
- **Multi-Strategy:** Handles specific cases (numbers, names, exact matches)

### Option 1: Switch to Pure Vector Search

**When to use:** Queries are mostly conceptual, exact keywords less important

**Steps:**

1. **Disable hybrid search** in `.env`:
   ```bash
   USE_HYBRID_SEARCH=false
   VECTOR_WEIGHT=1.0
   ```

2. **Update VectorStore initialization** in `src/core/storage/vector_store.py`:
   ```python
   # Line ~300-320 in VectorStore class
   def get_retriever(self):
       """Get the appropriate retriever."""
       if not settings.USE_HYBRID_SEARCH:
           # Use pure vector retriever
           return self.vector_store.as_retriever(
               search_kwargs={"k": settings.TOP_K_DOCS}
           )
       # ... existing hybrid code ...
   ```

3. **Test the change:**
   ```bash
   python scripts/testing/root_test_files/test_api_taxonomy.py
   ```

### Option 2: Switch to Pure BM25 (Keyword) Search

**When to use:** Queries use specific terminology, exact term matching critical

**Steps:**

1. **Configure for keyword-only** in `.env`:
   ```bash
   USE_HYBRID_SEARCH=false
   VECTOR_WEIGHT=0.0
   ```

2. **Update retriever** in `src/core/storage/vector_store.py`:
   ```python
   def get_retriever(self):
       """Get the appropriate retriever."""
       if settings.VECTOR_WEIGHT == 0.0:
           # Use pure BM25 retriever
           return BM25Retriever.from_documents(
               self.all_documents,
               k=settings.TOP_K_DOCS
           )
       # ... existing code ...
   ```

3. **Test keyword matching:**
   ```bash
   python scripts/utilities/debug_retrieval.py
   ```

### Option 3: Enable Re-ranking with Cross-Encoder

**When to use:** Want highest quality results, willing to trade speed

**Steps:**

1. **Install cross-encoder dependencies:**
   ```bash
   pip install sentence-transformers
   ```

2. **Update `requirements.txt`:**
   ```txt
   sentence-transformers==2.2.2
   ```

3. **Add re-ranker** to `src/core/retrieval/advanced_retrieval.py`:
   ```python
   from sentence_transformers import CrossEncoder

   class ReRanker:
       def __init__(self, model_name='cross-encoder/ms-marco-MiniLM-L-6-v2'):
           self.model = CrossEncoder(model_name)

       def rerank(self, query: str, documents: List[Document], top_k: int = 5):
           """Re-rank documents using cross-encoder."""
           # Prepare pairs
           pairs = [[query, doc.page_content] for doc in documents]

           # Score pairs
           scores = self.model.predict(pairs)

           # Sort by score
           doc_scores = list(zip(documents, scores))
           doc_scores.sort(key=lambda x: x[1], reverse=True)

           # Return top-k
           return [doc for doc, score in doc_scores[:top_k]]
   ```

4. **Integrate in retrieval pipeline** in `src/core/storage/vector_store.py`:
   ```python
   from ..retrieval.advanced_retrieval import ReRanker

   class VectorStore:
       def __init__(self):
           # ... existing init ...
           self.reranker = ReRanker() if settings.USE_RERANKING else None

       def query(self, query_text: str, top_k: int = 5):
           # Get initial results
           docs = self.retriever.get_relevant_documents(query_text)

           # Re-rank if enabled
           if self.reranker:
               docs = self.reranker.rerank(query_text, docs, top_k)

           return docs[:top_k]
   ```

5. **Add configuration** in `src/config/settings.py`:
   ```python
   USE_RERANKING = os.getenv('USE_RERANKING', 'false').lower() == 'true'
   ```

6. **Test re-ranking:**
   ```bash
   USE_RERANKING=true python scripts/testing/root_test_files/test_comprehensive_taxonomy.py
   ```

## Changing Vector Stores

### Current: ChromaDB

**Pros:** Easy to use, runs locally, good for development
**Cons:** Limited scale, no cloud persistence

### Switch to Pinecone

**When to use:** Need cloud hosting, larger scale, managed service

**Steps:**

1. **Install Pinecone:**
   ```bash
   pip install pinecone-client langchain-pinecone
   ```

2. **Get Pinecone API key:**
   - Sign up at https://www.pinecone.io/
   - Create an index with dimension=768 (Google Embeddings)
   - Copy API key and environment

3. **Add to `.env`:**
   ```bash
   PINECONE_API_KEY=your-api-key
   PINECONE_ENVIRONMENT=your-environment
   PINECONE_INDEX_NAME=airi-chatbot
   ```

4. **Create Pinecone wrapper** in `src/core/storage/pinecone_store.py`:
   ```python
   import pinecone
   from langchain_pinecone import Pinecone
   from langchain_google_genai import GoogleGenerativeAIEmbeddings
   from ...config.settings import settings
   from ...config.logging import get_logger

   logger = get_logger(__name__)

   class PineconeVectorStore:
       def __init__(self):
           # Initialize Pinecone
           pinecone.init(
               api_key=settings.PINECONE_API_KEY,
               environment=settings.PINECONE_ENVIRONMENT
           )

           # Get embeddings
           self.embeddings = GoogleGenerativeAIEmbeddings(
               model="models/text-embedding-004"
           )

           # Connect to index
           self.index_name = settings.PINECONE_INDEX_NAME
           self.vector_store = Pinecone(
               index=pinecone.Index(self.index_name),
               embedding=self.embeddings,
               text_key="text"
           )

       def add_documents(self, documents):
           """Add documents to Pinecone."""
           self.vector_store.add_documents(documents)
           logger.info(f"Added {len(documents)} documents to Pinecone")

       def query(self, query_text, top_k=5):
           """Query Pinecone for similar documents."""
           return self.vector_store.similarity_search(query_text, k=top_k)
   ```

5. **Update settings** in `src/config/settings.py`:
   ```python
   # Vector Store Selection
   VECTOR_STORE_TYPE = os.getenv('VECTOR_STORE_TYPE', 'chroma')  # 'chroma' or 'pinecone'
   PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
   PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT')
   PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'airi-chatbot')
   ```

6. **Update ChatService** to use selected store in `src/core/services/chat_service.py`:
   ```python
   from ...config.settings import settings

   # In initialization
   if settings.VECTOR_STORE_TYPE == 'pinecone':
       from ..storage.pinecone_store import PineconeVectorStore
       self.vector_store = PineconeVectorStore()
   else:
       from ..storage.vector_store import VectorStore
       self.vector_store = VectorStore()
   ```

7. **Migrate data to Pinecone:**
   ```bash
   VECTOR_STORE_TYPE=pinecone python scripts/data_migration/reingest_all_documents.py
   ```

### Switch to Weaviate

**When to use:** Need advanced filtering, graph capabilities, cloud or self-hosted

Follow similar pattern as Pinecone:
- Install `weaviate-client` and `langchain-weaviate`
- Create `weaviate_store.py` wrapper
- Update settings and initialization

## Adjusting Weights and Parameters

### Vector vs. Keyword Weight

**Location:** `.env` or `src/config/settings.py`

```bash
# In .env
VECTOR_WEIGHT=0.7  # 70% vector, 30% keyword
```

**Tuning guide:**
- `0.8-1.0` - Conceptual queries, synonym matching important
- `0.6-0.7` - Balanced (recommended default)
- `0.3-0.5` - Keyword queries, exact terms important
- `0.0-0.2` - Pure keyword matching

**Test different weights:**
```python
# In scripts/testing/test_weight_comparison.py
weights = [0.5, 0.6, 0.7, 0.8, 0.9]
for weight in weights:
    # Test queries with each weight
    # Compare results
```

### Top-K Documents

**How many documents to retrieve and use for context**

```python
# src/config/settings.py
TOP_K_DOCS = 5  # Default
```

**Tuning guide:**
- `3-5` - Fast, focused responses
- `5-7` - Balanced (default)
- `7-10` - Comprehensive, slower

**Trade-offs:**
- More docs = better context but slower LLM processing
- Fewer docs = faster but may miss relevant info

### Chunk Size and Overlap

**Location:** `src/config/settings.py`

```python
CHUNK_SIZE = 1000       # Characters per chunk
CHUNK_OVERLAP = 200     # Overlap between chunks
```

**Tuning guide:**

**Chunk Size:**
- `500-800` - Precise matching, more chunks
- `1000-1500` - Balanced (recommended)
- `1500-2000` - Better context, less precise

**Overlap:**
- `0-100` - Minimal redundancy
- `200-300` - Balanced (recommended)
- `300-500` - Prevents split concepts

**Re-chunk documents:**
```bash
python scripts/data_migration/reingest_all_documents.py
```

## Adding New Retrieval Strategies

### Example: Add Fuzzy Matching Strategy

**Use case:** Handle misspellings and typos

1. **Add fuzzy matching to multi-strategy retriever** in `src/core/retrieval/multi_strategy_retriever.py`:

   ```python
   from rapidfuzz import fuzz, process

   class MultiStrategyRetriever:
       def _fuzzy_search(self, query: str, threshold: int = 80) -> List[Document]:
           """Find documents with fuzzy string matching."""
           results = []

           # Search in document content
           for doc in self.all_documents:
               # Calculate fuzzy match score
               score = fuzz.partial_ratio(query.lower(), doc.page_content.lower())

               if score >= threshold:
                   results.append((doc, score))

           # Sort by score
           results.sort(key=lambda x: x[1], reverse=True)

           return [doc for doc, score in results[:10]]

       def retrieve(self, query: str, k: int = 5) -> List[Document]:
           """Retrieve with fuzzy matching strategy."""
           strategies = []

           # Existing strategies...

           # Add fuzzy strategy
           if len(query) > 5:  # Only for longer queries
               fuzzy_docs = self._fuzzy_search(query)
               if fuzzy_docs:
                   strategies.append(RetrievalStrategy(
                       name="fuzzy",
                       confidence=0.6,
                       documents=fuzzy_docs
                   ))

           # Merge strategies...
           return self._merge_strategies(strategies, k)
   ```

2. **Install dependency:**
   ```bash
   pip install rapidfuzz
   ```

3. **Test fuzzy matching:**
   ```python
   # Test with misspelled query
   query = "artifical inteligence risks"  # Misspelled
   docs = retriever.retrieve(query)
   ```

### Example: Add Date-Based Retrieval

**Use case:** Prioritize recent documents

1. **Add date scoring** in `src/core/retrieval/advanced_retrieval.py`:

   ```python
   from datetime import datetime

   def score_by_recency(documents: List[Document]) -> List[Document]:
       """Score documents by recency."""
       scored_docs = []

       for doc in documents:
           # Get date from metadata
           date_str = doc.metadata.get('date', '2020-01-01')
           doc_date = datetime.strptime(date_str, '%Y-%m-%d')

           # Calculate recency score (0-1)
           days_old = (datetime.now() - doc_date).days
           recency_score = 1 / (1 + days_old / 365)  # Decay over years

           # Boost score
           doc.metadata['recency_score'] = recency_score
           scored_docs.append(doc)

       # Sort by recency
       scored_docs.sort(key=lambda d: d.metadata.get('recency_score', 0), reverse=True)

       return scored_docs
   ```

2. **Integrate in retrieval**:
   ```python
   # In VectorStore.query()
   docs = self.retriever.get_relevant_documents(query_text)
   docs = score_by_recency(docs)
   return docs[:top_k]
   ```

## Modifying Response Generation

### Change LLM Model

**Current:** Gemini 1.5 Flash

**Switch to Gemini 1.5 Pro:**

1. **Update model name** in `src/core/models/gemini.py`:
   ```python
   MODEL_NAME = "gemini-1.5-pro-latest"  # More capable, slower
   ```

**Switch to different provider (OpenAI GPT-4):**

1. **Create new model wrapper** in `src/core/models/openai.py`:
   ```python
   import openai
   from .base import BaseModel

   class OpenAIModel(BaseModel):
       def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
           openai.api_key = api_key
           self.model = model

       def generate(self, prompt: str, context_docs: List[Document]) -> str:
           # Format context
           context = "\n\n".join([doc.page_content for doc in context_docs])

           # Call OpenAI
           response = openai.ChatCompletion.create(
               model=self.model,
               messages=[
                   {"role": "system", "content": "You are an AI Risk expert..."},
                   {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"}
               ]
           )

           return response.choices[0].message.content
   ```

2. **Update ChatService initialization**:
   ```python
   # In main.py or app initialization
   from src.core.models.openai import OpenAIModel

   model = OpenAIModel(api_key=os.getenv('OPENAI_API_KEY'))
   chat_service = ChatService(gemini_model=model)
   ```

### Customize System Prompt

**Location:** `src/core/models/gemini.py`

```python
def generate(self, user_message: str, retrieved_documents: List[Document]) -> str:
    """Generate response with custom system prompt."""

    system_prompt = """You are an AI Risk expert assistant.

    Your role:
    - Provide accurate information about AI risks
    - Use the provided context to answer questions
    - Cite sources when making claims
    - Admit when you don't know something

    Response style:
    - Clear and concise
    - Well-structured with headings
    - Include specific examples
    - Maintain professional but friendly tone
    """

    # ... rest of generation logic ...
```

## Testing Your Changes

### Unit Tests

**Test retrieval:**
```bash
python -m pytest tests/unit/test_vector_store.py -v
```

**Test specific retriever:**
```python
# tests/unit/test_retriever.py
def test_hybrid_retriever():
    retriever = FieldAwareHybridRetriever(...)
    docs = retriever.get_relevant_documents("AI healthcare risks")
    assert len(docs) > 0
    assert any('healthcare' in doc.metadata.get('domain', '') for doc in docs)
```

### Integration Tests

**Test end-to-end:**
```bash
python scripts/testing/root_test_files/test_comprehensive_taxonomy.py
```

**Test specific queries:**
```python
# scripts/testing/test_rag_modifications.py
from src.core.services.chat_service import ChatService

chat_service = ChatService()

test_queries = [
    "What are AI risks in healthcare?",
    "How many AI incidents are recorded?",
    "What is the SCQA framework?"
]

for query in test_queries:
    response, docs, _ = chat_service.process_query(query, "test-session")
    print(f"\nQuery: {query}")
    print(f"Response: {response[:200]}...")
    print(f"Documents retrieved: {len(docs)}")
```

### Performance Testing

**Measure retrieval speed:**
```python
import time

start = time.time()
docs = vector_store.query("test query", top_k=5)
elapsed = time.time() - start

print(f"Retrieval time: {elapsed:.3f}s")
```

**Compare configurations:**
```bash
# Test different weights
for weight in 0.5 0.6 0.7 0.8 0.9; do
    VECTOR_WEIGHT=$weight python scripts/testing/benchmark_retrieval.py
done
```

### Quality Testing

**Evaluate response quality:**
```python
# scripts/testing/evaluate_quality.py
from src.core.services.chat_service import ChatService

chat_service = ChatService()

# Load test questions with expected answers
test_cases = [
    {
        "query": "What are the main AI risk categories?",
        "expected_topics": ["safety", "security", "fairness", "privacy"]
    },
    # ... more cases ...
]

for case in test_cases:
    response, _, _ = chat_service.process_query(case["query"], "test")

    # Check if expected topics are covered
    topics_found = sum(1 for topic in case["expected_topics"]
                      if topic.lower() in response.lower())

    coverage = topics_found / len(case["expected_topics"])
    print(f"Coverage: {coverage:.1%}")
```

## Rollback Plan

If changes cause issues:

1. **Check git status:**
   ```bash
   git status
   git diff
   ```

2. **Revert specific files:**
   ```bash
   git checkout HEAD -- src/core/storage/vector_store.py
   ```

3. **Revert to tagged version:**
   ```bash
   git checkout pre-cleanup-20251006
   ```

4. **Restore configuration:**
   ```bash
   cp .env.backup .env
   ```

## Best Practices

1. **Always test locally first** before deploying
2. **Make one change at a time** to isolate issues
3. **Document configuration changes** in comments
4. **Keep backups** of working configurations
5. **Monitor performance** after changes
6. **Use feature flags** for experimental features
7. **Version your changes** with git tags

## Need Help?

- Check [RAG System Architecture](rag_system.md) for system overview
- Review [Performance Plan](performance_plan.md) for optimization tips
- See test files in `scripts/testing/root_test_files/` for examples
- Run `python scripts/utilities/debug_retrieval.py` to debug issues
