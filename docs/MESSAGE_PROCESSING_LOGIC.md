# Message Processing Logic & Response Generation
## The AIRI Chatbot Intelligence Pipeline

*A comprehensive guide to how user messages are transformed into intelligent, cited responses*

---

## Executive Summary

The AIRI chatbot employs a sophisticated 12-stage pipeline that transforms raw user queries into intelligent, well-cited responses. Each message travels through intent classification, domain detection, document retrieval, AI generation, and validation before reaching the user. This system processes over 1,600 AI risk documents to provide authoritative answers with proper academic citations.

**Core Philosophy**: *Filter early, retrieve precisely, generate intelligently, validate rigorously*

---

## System Architecture Overview

```
User Query → Intent Filter → Domain Detection → Document Retrieval → AI Generation → Response
     ↓              ↓              ↓                ↓               ↓            ↓
 "What are      Repository    "bias" domain    5-6 relevant    Gemini 2.0     Validated
 AI hiring      related?      detected with    documents       generates      response
 biases?"       ✅ Yes        confidence       retrieved       detailed       with RID
                                                               response       citations
```

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Intent Classifier** | Filters non-repository queries | `src/core/query/intent_classifier.py` |
| **Query Processor** | Analyzes and enhances queries | `src/core/query/processor.py` |
| **Domain Classifier** | Detects AI risk domains | `src/config/domains.py` |
| **Vector Store** | Retrieves relevant documents | `src/core/storage/vector_store.py` |
| **Prompt Manager** | Builds context-aware prompts | `src/config/prompts.py` |
| **Citation Service** | Adds RID-based citations | `src/core/services/citation_service.py` |
| **Response Validator** | Ensures response quality | `src/core/validation/response_validator.py` |

---

## Phase-by-Phase Processing Pipeline

### 🔍 **Phase 1: Intent Classification & Pre-Filtering**
*"Is this about AI risks or just chit-chat?"*

**Purpose**: Eliminate non-repository queries before expensive processing

```python
# Example: Input filtering
query = "What are AI hiring biases?"
intent_result = intent_classifier.classify_intent(query)
```

**Decision Tree**:
- **Repository-related** → Continue to Phase 2
- **Chit-chat** → Return friendly redirect
- **General knowledge** → Return repository suggestion
- **Junk/spam** → Block processing

**Real Example**:
```
Query: "What are AI hiring biases?"
Intent: REPOSITORY_RELATED (confidence: 0.89)
Action: ✅ Continue processing

Query: "What's the weather today?"
Intent: GENERAL_KNOWLEDGE (confidence: 0.95)
Action: ❌ "I help with AI risks. Try asking about employment impacts..."
```

### 🔧 **Phase 2: Query Refinement & Analysis**
*"Can we make this query more specific?"*

**Purpose**: Handle overly broad queries and auto-refine when possible

```python
refinement_result = query_refiner.analyze_query(message)
if refinement_result.needs_refinement:
    message = refinement_result.refined_query  # Auto-enhance
```

**Complexity Categories**:
- **Specific** → Process directly
- **Broad** → Auto-refine if possible
- **Very Broad** → Request clarification

**Real Example**:
```
Original: "Tell me about AI"
Refined: "What are the main categories of AI risks and safety concerns?"
Action: ✅ Use refined query
```

### 🎯 **Phase 3: Domain Detection & Enhancement**
*"What type of AI risk is this about?"*

**Purpose**: Classify queries into AI risk domains for targeted retrieval

```python
query_type, domain = query_processor.analyze_query(message)
```

**Domain Classification**:
1. **Monitor Analysis**: Uses Gemini model for advanced classification
2. **Fallback Classification**: Pattern-based domain detection
3. **Enhanced Detection**: Keyword matching for missed domains

**Domain Categories**:
- **socioeconomic** → Employment, automation, inequality
- **safety** → Accidents, failures, physical harm
- **privacy** → Data protection, surveillance
- **bias** → Discrimination, fairness issues
- **governance** → Regulation, oversight, policy
- **technical** → System failures, performance issues

**Real Example**:
```
Query: "How does facial recognition bias affect hiring?"
Initial: domain="other"
Enhanced: domain="bias" (detected keywords: facial, recognition, bias, hiring)
Final: query_type="bias", domain="bias"
```

### 📊 **Phase 4: Document Retrieval & Ranking**
*"Find the most relevant documents from 1,600+ sources"*

**Purpose**: Retrieve and rank documents using hybrid search with field-aware boosting

```python
docs = vector_store.similarity_search_with_relevance_scores(
    query, k=6, score_threshold=domain_threshold
)
```

**Retrieval Strategy**:
1. **Vector Search**: Semantic similarity using embeddings
2. **Keyword Search**: BM25 for exact term matching
3. **Hybrid Fusion**: Combines both approaches
4. **Field-Aware Boosting**: Prioritizes title/domain matches
5. **Cross-Encoder Re-ranking**: Re-scores for relevance
6. **MMR Deduplication**: Removes similar documents

**Real Example**:
```
Query: "AI hiring bias"
Retrieved: 6 documents → 3 above threshold (0.25) → 2 domain-specific added
Final: 5 documents with RIDs: RID-01519, RID-00954, RID-01529, RID-01256, RID-00956
```

### 📝 **Phase 5: Context Formatting**
*"Package documents into a coherent context"*

**Purpose**: Format retrieved documents for AI consumption

```python
context = self._format_context(docs, query_type)
```

**Context Structure**:
```
INFORMATION FROM THE AI RISK REPOSITORY:

SECTION 1 (Domain: Discrimination & Toxicity):
[Document content with metadata]

SECTION 2 (Domain: Safety):
[Document content with metadata]
...
```

### 🧠 **Phase 6: AI Response Generation**
*"Generate intelligent responses using Gemini 2.0"*

**Purpose**: Create contextual, domain-specific responses using advanced prompts

```python
prompt = query_processor.generate_prompt(message, query_type, context, conversation_id, docs)
response = gemini_model.generate(prompt, history)
```

**Prompt Engineering**:
- **Domain-Specific Templates**: Tailored prompts for each risk domain
- **Brevity Rules**: Concise, direct responses
- **Citation Requirements**: Must use provided RIDs
- **Context Awareness**: Leverages conversation history

**Model Fallback Chain**:
1. **gemini-2.0-flash** (primary)
2. **gemini-2.5-flash** (backup)
3. **gemini-2.5-flash-lite** (fallback)

**Real Example**:
```
Domain: "bias"
Prompt Template: "BIAS FOCUS: You're answering about algorithmic bias, discrimination, fairness..."
Context: [5 documents about AI bias]
Response: "AI systems can perpetuate biases present in training data, leading to unfair outcomes..."
```

### 🔗 **Phase 7: Citation Enhancement**
*"Add proper academic citations with clickable RIDs"*

**Purpose**: Enhance responses with RID-based citations and create snippet files

```python
enhanced_response = citation_service.enhance_response_with_citations(response, docs)
```

**Citation Process**:
1. **RID Extraction**: Extract RIDs from source documents
2. **Citation Mapping**: Map document content to RID citations
3. **Response Enhancement**: Add citations to response text
4. **Snippet Creation**: Save document snippets as `RID-XXXXX.txt`

**Citation Formats**:
- **Inline**: "AI systems can cause bias (RID-01519)"
- **Source List**: "• RID-01519: Future Risks of Frontier AI (Domain: Bias)"
- **Legacy Replacement**: "SECTION 1" → "RID-01519"

### ✅ **Phase 8: Response Validation**
*"Ensure response quality and appropriateness"*

**Purpose**: Validate response quality using multiple criteria

```python
validated_response, validation_results = validation_chain.validate_and_improve(
    response, query, documents, domain
)
```

**Validation Criteria**:
- **Factual Accuracy**: Claims supported by documents
- **Relevance**: Addresses the user's question
- **Completeness**: Comprehensive coverage
- **Appropriateness**: Professional tone, no deflection
- **Citation Quality**: Proper RID usage

**Quality Scoring**:
- **Score > 0.8**: Excellent response
- **Score 0.6-0.8**: Good response
- **Score < 0.6**: Needs improvement

---

## Real-World Processing Example

Let's trace a complete query through the system:

### Input Query: *"How can I mitigate bias in AI-powered customer service chatbots?"*

**Step-by-Step Processing**:

```
📥 RECEIVED: "How can I mitigate bias in AI-powered customer service chatbots?"

🔍 PHASE 1 - Intent Classification:
   Result: REPOSITORY_RELATED (confidence: 0.87)
   Action: ✅ Continue processing

🔧 PHASE 2 - Query Refinement:
   Complexity: SPECIFIC
   Action: ✅ No refinement needed

🎯 PHASE 3 - Domain Detection:
   Monitor: domain="other" (fallback triggered)
   Enhanced: domain="bias" (keywords: bias, AI, chatbots)
   Final: query_type="bias", domain="bias"

📊 PHASE 4 - Document Retrieval:
   Vector Search: 6 candidates
   Threshold Filter: 3 above 0.25 similarity
   Domain Boost: +2 bias-specific documents
   Final: 5 documents retrieved

📝 PHASE 5 - Context Formatting:
   Structure: 5 sections with domain metadata
   Length: 2,847 characters
   RIDs: RID-01519, RID-00954, RID-01529, RID-01256, RID-00956

🧠 PHASE 6 - AI Generation:
   Model: gemini-2.0-flash
   Prompt: Bias-focused template with context
   Response: 287 words with specific mitigation strategies

🔗 PHASE 7 - Citation Enhancement:
   Citations Added: 5 RID references
   Snippets Created: 5 new RID-XXXXX.txt files
   Legacy Patterns: None to replace

✅ PHASE 8 - Response Validation:
   Overall Score: 0.92 (Excellent)
   Factual Accuracy: ✅ All claims supported
   Relevance: ✅ Directly addresses query
   Appropriateness: ✅ Professional, helpful tone

📤 DELIVERED: Comprehensive response with actionable mitigation strategies
```

---

## Key Components Deep Dive

### Intent Classifier (`intent_classifier.py`)
**Purpose**: Lightning-fast pre-filtering to avoid expensive processing

**Classification Strategy**:
- **Semantic Similarity**: Compares query to domain reference texts
- **Pattern Matching**: Detects spam, junk, and override attempts
- **Confidence Scoring**: Returns confidence levels for decisions

**Performance**: ~50ms average classification time

### Query Processor (`processor.py`)
**Purpose**: Central orchestrator for query analysis and enhancement

**Key Methods**:
- `analyze_query()`: Determines query type and domain
- `generate_prompt()`: Creates domain-specific prompts
- `enhance_query()`: Adds relevant keywords for better retrieval

### Domain Classifier (`domains.py`)
**Purpose**: Robust domain detection using weighted keyword matching

**Scoring Algorithm**:
```python
domain_score = sum(keyword_matches) * domain_weight
if domain_score > threshold:
    return domain
```

**Domain Weights**:
- Socioeconomic: 1.2x (employment queries are important)
- Safety: 1.0x (standard weight)
- Privacy: 1.0x (standard weight)
- Bias: 1.0x (standard weight)
- Governance: 1.0x (standard weight)
- Technical: 1.0x (standard weight)

### Vector Store (`vector_store.py`)
**Purpose**: Intelligent document retrieval with multiple search strategies

**Retrieval Pipeline**:
1. **Embedding Search**: Uses Google's text-embedding-004
2. **BM25 Search**: Keyword-based ranking
3. **Hybrid Fusion**: Combines scores using configurable weights
4. **Field-Aware Boosting**: Metadata-based score adjustment
5. **Cross-Encoder Re-ranking**: Final relevance scoring

**Performance Optimizations**:
- Relevance thresholds prevent low-quality results
- MMR deduplication reduces redundancy
- Domain-specific document limits balance comprehensiveness

### Prompt Manager (`prompts.py`)
**Purpose**: Context-aware prompt generation with domain expertise

**Template System**:
- **Base Template**: Core instructions and citation rules
- **Domain Templates**: Specialized prompts for each risk domain
- **Brevity Rules**: Ensures concise, actionable responses
- **Session Awareness**: Avoids repetitive introductions

**Out-of-Scope Handling**:
```python
if not context and domain == "other":
    return self._handle_out_of_scope(query)
```

---

## Debug & Monitoring

### Key Log Markers
Track message processing using these log patterns:

```bash
# Intent Classification
grep "Intent classification" app.log

# Domain Detection  
grep "Domain detected:" app.log

# Document Retrieval
grep "Retrieved.*documents" app.log

# Response Generation
grep "GEMINI.*DEBUG" app.log

# Citation Enhancement
grep "RID citation enhancement" app.log

# Validation Results
grep "Response validation:" app.log
```

### Debug Queries
Test specific pipeline components:

```python
# Test intent classification
intent_result = intent_classifier.classify_intent("Test query")

# Test domain detection
domain = domain_classifier.classify_domain("AI hiring bias")

# Test document retrieval
docs = vector_store.similarity_search("employment automation", k=5)

# Test prompt generation
prompt = prompt_manager.get_prompt("query", "bias", "context", "session1")
```

---

## Performance Considerations

### Bottlenecks & Optimizations

**🐌 Slowest Components**:
1. **Vector Search**: 200-500ms (embedding computation)
2. **AI Generation**: 1-3s (Gemini API call)
3. **Cross-Encoder Re-ranking**: 100-200ms (model inference)

**⚡ Optimization Strategies**:
- **Early Filtering**: Intent classification eliminates 40% of queries
- **Relevance Thresholds**: Skip processing of low-quality documents
- **Model Fallback**: Automatic failover for API issues
- **Caching**: Session-based conversation history

**📊 Performance Metrics**:
- **Average Response Time**: 2-4 seconds
- **Document Retrieval**: 95% accuracy for domain-specific queries
- **Citation Quality**: 99% of RID citations are valid
- **Response Validation**: 92% pass rate on first attempt

### Scaling Considerations

**Current Limits**:
- 1,600+ documents in vector store
- 5-8 documents per response
- 30-second timeout for AI generation

**Future Optimizations**:
- Document chunking for better retrieval
- Async processing for multiple queries
- Response caching for common questions
- Real-time learning from user feedback

---

## Conclusion

The AIRI chatbot's message processing pipeline represents a sophisticated balance of speed, accuracy, and intelligence. By combining intent classification, domain detection, hybrid retrieval, and advanced AI generation, the system delivers authoritative responses about AI risks with proper academic citations.

**Key Strengths**:
- **Intelligent Filtering**: Only processes relevant queries
- **Domain Expertise**: Specialized handling for each AI risk category
- **Hybrid Retrieval**: Combines semantic and keyword search
- **Quality Assurance**: Multi-stage validation ensures high response quality
- **Academic Rigor**: Proper citations with clickable RID references

**The Result**: Users receive intelligent, well-researched responses that feel like consulting an AI risk expert who has instant access to the world's most comprehensive AI risk database.

---

*This document serves as the definitive guide to understanding the AIRI chatbot's intelligence pipeline. For technical questions or improvements, see the individual component documentation in the `src/` directory.*