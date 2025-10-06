# AIRI Chatbot

A sophisticated chatbot for the MIT AI Risk Repository with advanced RAG capabilities, modular architecture, and clickable citations.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/skrigel/airi-chatbot-class.git
cd airi-chatbot-class

# Create and activate virtual environment (IMPORTANT!)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set your API key (required)
export GEMINI_API_KEY="your-api-key-here"

# Run the chatbot
python3 main.py
```

The chatbot will automatically find an available port (usually 8000, 8080, or 8090) and display the URL.

## Project Structure

```
airi-chatbot-class/
├── src/                    # Core application code
│   ├── api/               # Web API layer (Flask routes)
│   ├── core/              # Business logic
│   │   ├── models/       # AI model implementations (Gemini)
│   │   ├── storage/      # Vector store and databases
│   │   ├── retrieval/    # Multi-strategy retrieval
│   │   ├── query/        # Query processing and intent
│   │   ├── services/     # Orchestration services
│   │   ├── taxonomy/     # Taxonomy handling
│   │   └── metadata/     # Metadata extraction
│   └── config/            # Configuration and settings
├── frontend/              # React TypeScript frontend
├── tests/                 # Test suites
├── docs/                  # Comprehensive documentation
│   ├── architecture/     # Technical architecture docs
│   ├── deployment/       # Deployment guides
│   ├── testing/          # Testing plans and briefs
│   └── webflow/          # Webflow integration
├── scripts/               # Utility scripts
│   ├── preprint/         # Preprint processing
│   ├── testing/          # Test generation
│   ├── data_migration/   # Data reingestion
│   └── utilities/        # Debug and utilities
├── webflow/               # Webflow integration code
│   ├── widget/           # Chatbot widget
│   └── analytics/        # PostHog integration
├── test_results/          # Test results archive
├── data/                  # Data files and vector DB
├── GoogleDocs/            # Generated documents
├── main.py                # Application entry point
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container configuration
└── railway.json           # Railway deployment config
```

## Key Features

- **Advanced RAG System**: Hybrid retrieval combining vector search and keyword matching
- **Multi-Strategy Retrieval**: Handles numbers, names, and exact matches intelligently
- **Intent Classification**: Routes queries to specialized handlers
- **Taxonomy Integration**: Structured responses from AI Risk Repository preprint
- **Clickable Citations**: Each response includes links to source documents
- **Field-Aware Retrieval**: Metadata boosting for domain-specific queries
- **Multi-Language Support**: Responses in multiple languages
- **Session Management**: Persistent conversations across page navigation
- **Webflow Integration**: Embeddable widget with analytics

## Documentation

### For New Developers
- **[Documentation Hub](docs/README.md)** - Complete documentation index
- **[RAG System Guide](docs/architecture/rag_system.md)** - How the retrieval system works
- **[Modifying RAG](docs/architecture/modifying_rag.md)** - Step-by-step modification guide
- **[Message Processing](docs/architecture/MESSAGE_PROCESSING_LOGIC.md)** - How queries are processed

### For Deployers
- **[Deployment Guide](docs/deployment/deployment_guide.md)** - Complete deployment instructions
- **[Decision Matrix](docs/deployment/decision_matrix.md)** - Choosing deployment options
- **[Running Lean](docs/deployment/running_lean.md)** - Resource optimization

### For Testers
- **[Testing Brief](docs/testing/testing_brief.md)** - Comprehensive testing guide
- **[Pre-Testing Checklist](docs/testing/pre_testing_checklist.md)** - What to verify first

### For Webflow Integration
- **[Widget Integration](docs/webflow/widget_integration.md)** - How to embed the chatbot
- **[Analytics Setup](docs/webflow/analytics_setup.md)** - PostHog configuration

## System Architecture

The system uses a sophisticated RAG (Retrieval-Augmented Generation) architecture:

```
User Query
    ↓
Intent Classification → Route to handler
    ↓
Query Processing → Enhance query
    ↓
Multi-Strategy Retrieval
    ├── Vector Search (semantic)
    ├── BM25 Search (keyword)
    └── Field-Aware (metadata)
    ↓
Hybrid Fusion → Re-rank results
    ↓
LLM Generation → Synthesize response
    ↓
Citations → Add source links
    ↓
Response to User
```

### Core Components

1. **Vector Store** (`src/core/storage/`)
   - ChromaDB for vector storage
   - Google Embeddings (text-embedding-004)
   - Hybrid search with BM25 keyword matching

2. **Multi-Strategy Retrieval** (`src/core/retrieval/`)
   - Handles edge cases (numbers, names, exact matches)
   - Multiple retrieval strategies with confidence scoring
   - Result merging and deduplication

3. **Query Processing** (`src/core/query/`)
   - Intent classification and routing
   - Query enhancement and expansion
   - Domain and taxonomy detection

4. **Chat Service** (`src/core/services/`)
   - Orchestrates conversation flow
   - Manages citations and snippets
   - Multi-language support

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Required
GEMINI_API_KEY=your-api-key-here

# Optional - Application
PORT=8090
DEBUG=false

# Optional - Vector Store
CHROMA_DB_PATH=./data/chroma_db
EMBEDDING_MODEL=models/text-embedding-004

# Optional - Retrieval
USE_HYBRID_SEARCH=true
USE_FIELD_AWARE_HYBRID=true
VECTOR_WEIGHT=0.7              # 0-1, balance vector vs keyword
HYBRID_RERANK_TOP_K=10         # Results to re-rank
TOP_K_DOCS=5                   # Documents for context

# Optional - Generation
LLM_MODEL=gemini-1.5-flash-latest
TEMPERATURE=0.3
```

### Data Setup

Place your MIT AI Risk Repository files in `data/info_files/`:
- Excel files (`.xlsx`, `.xls`)
- Text files (`.txt`, `.md`)
- The system automatically processes and indexes all files on startup

## Common Tasks

### Modifying RAG Behavior

See detailed guide: [docs/architecture/modifying_rag.md](docs/architecture/modifying_rag.md)

**Quick adjustments:**
```bash
# Adjust vector vs keyword balance (in .env)
VECTOR_WEIGHT=0.8    # More semantic, less keyword
VECTOR_WEIGHT=0.5    # Balanced
VECTOR_WEIGHT=0.3    # More keyword, less semantic

# Get more context documents
TOP_K_DOCS=7

# Re-rank more candidates
HYBRID_RERANK_TOP_K=15
```

### Running Tests

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Legacy test files
python scripts/testing/root_test_files/test_comprehensive_taxonomy.py

# Test specific functionality
python scripts/utilities/debug_retrieval.py
```

### Reingesting Documents

If you update documents in `data/info_files/`:

```bash
# Delete existing ChromaDB
rm -rf data/chroma_db

# Restart the application to reingest
python main.py
```

Or use the migration script:
```bash
python scripts/data_migration/reingest_all_documents.py
```

## API Endpoints

The system provides RESTful API endpoints:

- `POST /api/v1/stream` - Streaming chat responses (SSE)
- `POST /api/v1/sendMessage` - Non-streaming chat
- `GET /api/health` - System health check
- `GET /snippet/{id}` - View source document citations
- `POST /api/v1/feedback` - Submit user feedback

See [API documentation](docs/api/) for details.

## Deployment

### Railway (Recommended)

The application is configured for Railway deployment:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway up
```

See [Deployment Guide](docs/deployment/deployment_guide.md) for detailed instructions.

### Docker

Build and run with Docker:

```bash
# Build image
docker build -t airi-chatbot .

# Run container
docker run -p 8090:8080 \
  -e GEMINI_API_KEY=your-api-key \
  -v $(pwd)/data:/app/data \
  airi-chatbot
```

### Local Development

```bash
# Backend
python main.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Troubleshooting

### Common Issues

**Port Conflicts**
- App automatically finds available ports (8000, 8080, 8090)
- Override with `PORT=8090` environment variable

**Missing API Key**
- Set `GEMINI_API_KEY` in `.env` file or environment

**No Citations/Poor Retrieval**
- Ensure documents are in `data/info_files/`
- Check `VECTOR_WEIGHT` setting
- Review retrieval configuration in `.env`

**Frontend Build Fails**
- Ensure Node.js 18+ is installed
- Delete `frontend/node_modules` and reinstall

### Debug Mode

Enable debug logging:
```bash
DEBUG=true python main.py
```

Use debug utilities:
```bash
# Debug retrieval
python scripts/utilities/debug_retrieval.py

# Test import safety
python scripts/utilities/test_import_safety.py
```

## Example Queries

Try these queries to test the system:

**Taxonomy Queries:**
- "What are the main types of AI risks?"
- "What is the SCQA framework?"
- "Show me the AI risk taxonomy"

**Employment Queries:**
- "How will AI affect my job as an accountant?"
- "What are the risks of AI automation in the workplace?"

**Domain-Specific:**
- "What are the risks of AI in healthcare?"
- "What might happen if self-driving cars get compromised?"

**Specific Facts:**
- "How many AI incidents are recorded?"
- "What is incident #777?"

## Scripts and Utilities

Located in `scripts/`:

**Preprint Processing** (`scripts/preprint/`)
- Extract and index academic preprints
- Test preprint coverage

**Testing** (`scripts/testing/`)
- Generate testing documents
- Create test data
- Comprehensive test suites

**Data Migration** (`scripts/data_migration/`)
- Reingest all documents
- Initialize metadata
- Test reingestion

**Utilities** (`scripts/utilities/`)
- Debug retrieval issues
- Test import safety

## Contributing

1. Create a feature branch
2. Make changes with tests
3. Update documentation
4. Submit pull request

See [docs/MAINTENANCE.md](docs/MAINTENANCE.md) for file organization guidelines.

## Performance

### Optimization Tips

- Adjust `VECTOR_WEIGHT` based on query types
- Tune `TOP_K_DOCS` for speed vs. context trade-off
- Use `HYBRID_RERANK_TOP_K` for quality vs. speed
- Consider caching for frequently asked questions

See [Performance Plan](docs/architecture/performance_plan.md) for detailed optimization strategies.

## License

See the [LICENSE](LICENSE) file for details.

## Support

- **Documentation:** [docs/README.md](docs/README.md)
- **RAG System:** [docs/architecture/rag_system.md](docs/architecture/rag_system.md)
- **Deployment:** [docs/deployment/deployment_guide.md](docs/deployment/deployment_guide.md)
- **Issues:** GitHub Issues

---

Built with LangChain, ChromaDB, Google Gemini, and React.
