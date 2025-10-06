# Codebase Cleanup and Organization Agent

## Mission
Clean up and reorganize the AIRI Chatbot codebase to make it maintainable, comprehensible for new developers, and adaptable to future changes (especially RAG method modifications). The codebase currently has 79+ loose files in the root directory, making it difficult to navigate and understand project structure.

## Context
This is a production AI chatbot deployed on Railway and embedded in Webflow. The project has evolved rapidly with many experimental files, test results, documentation versions, and Webflow integration scripts scattered throughout. A new developer or future maintainer would struggle to understand what's active vs. deprecated, what's documentation vs. code, and where to make changes for common tasks like swapping RAG implementations.

## Core Principles
1. **Do not break anything** - Run tests after each major change
2. **Preserve git history** - Use `git mv` for file moves
3. **Document everything** - Update README and create migration guides
4. **Backward compatibility** - Maintain all import paths initially, then deprecate gradually
5. **Test continuously** - Verify builds and deploys still work

## Phase 1: Analysis and Planning

### Task 1.1: Audit Current State
Create a comprehensive inventory:

```bash
# Generate file categorization report
./scripts/audit_codebase.py > docs/codebase_audit.md
```

Categorize all root-level files into:
- **Active Production Code** (main.py, requirements.txt, etc.)
- **Configuration** (.env.example, Dockerfile, railway.json, etc.)
- **Documentation** (*.md files)
- **Test Results** (test_results_*.json, debug_*.log, taxonomy_*.json)
- **Webflow Integration** (webflow_*.html, *_widget_*.html)
- **Experimental/One-off Scripts** (extract_preprint.py, chunk_and_index_preprint.py, etc.)
- **Generated Documents** (*.docx files)
- **Temporary/Lock Files** (~$*.docx, server.log)

### Task 1.2: Identify Core Architecture
Map the actual architecture vs. documented architecture:
- Where is RAG implementation? (src/core/storage/)
- Where is query processing? (src/core/query/)
- Where are retrievers defined? (find all retriever classes)
- What are the key integration points?

**Output**: `docs/architecture_map.md` - Visual map of current architecture

### Task 1.3: Create Migration Plan
Document the proposed new structure with rationale:

```
airi-chatbot-class/
├── src/                          # Core application (unchanged)
├── frontend/                     # Frontend app (unchanged)
├── tests/                        # All tests (unchanged)
├── scripts/                      # One-off utility scripts
│   ├── preprint/                # Preprint extraction/indexing
│   ├── testing/                 # Test generation scripts
│   └── data_migration/          # Data reingestion tools
├── docs/                         # Consolidated documentation
│   ├── architecture/            # Architecture diagrams, maps
│   ├── deployment/              # Deployment guides
│   ├── webflow/                 # Webflow integration docs
│   ├── testing/                 # Testing plans and briefs
│   └── archive/                 # Deprecated/historical docs
├── webflow/                      # Webflow integration code
│   ├── widget/                  # Widget HTML/JS versions
│   ├── chatbot_page/            # Chatbot page scripts
│   └── analytics/               # PostHog integration
├── test_results/                 # Historical test outputs
│   ├── taxonomy/                # Taxonomy test results
│   ├── performance/             # Performance benchmarks
│   └── integration/             # Integration test results
├── data/                         # Data directory (mostly unchanged)
├── GoogleDocs/                   # Generated Google Docs exports
├── .archive/                     # Deprecated code/experiments
│   ├── old_scripts/
│   └── experimental/
├── main.py                       # Main entry point
├── requirements.txt              # Python dependencies
├── README.md                     # Main documentation
├── Dockerfile                    # Container config
└── railway.json                  # Railway config
```

**Output**: `docs/migration_plan.md`

## Phase 2: Documentation Consolidation

### Task 2.1: Consolidate Markdown Documentation
Move and organize all `.md` files:

```bash
# Testing documentation
git mv CHATBOT_TESTING_BRIEF.md docs/testing/testing_brief_original.md
git mv CHATBOT_TESTING_BRIEF_UPDATED.md docs/testing/testing_brief.md
git mv session_transfer_test_plan.md docs/testing/session_transfer.md
git mv pre_testing_checklist.md docs/testing/pre_testing_checklist.md

# Deployment documentation
git mv DEPLOYMENT.md docs/deployment/deployment_guide.md
git mv deployment_decision_matrix.md docs/deployment/decision_matrix.md
git mv deployment_gates_reference.md docs/deployment/gates_reference.md
git mv executive_summary_deployment.md docs/deployment/executive_summary.md
git mv running_lean_application.md docs/deployment/running_lean.md

# Webflow documentation
git mv webflow_widget_integration_instructions.md docs/webflow/widget_integration.md
git mv chatbot_session_integration.md docs/webflow/session_integration.md
git mv webflow_posthog_setup.md docs/webflow/analytics_setup.md

# Architecture and performance
git mv PERFORMANCE_IMPROVEMENT_PLAN_UPDATED.md docs/architecture/performance_plan.md
git mv synthesis_improvements_summary.md docs/architecture/synthesis_improvements.md
git mv SNIPPET_SYSTEM_DOCUMENTATION.md docs/architecture/snippet_system.md

# User testing
git mv supervisor_briefing.md docs/testing/supervisor_briefing.md
git mv google_form_instructions.md docs/testing/google_form_setup.md
```

### Task 2.2: Create Master Documentation Index
Create `docs/README.md` that categorizes and links to all documentation:

```markdown
# AIRI Chatbot Documentation

## Quick Start
- [Main README](../README.md) - Installation and basic usage
- [Deployment Guide](deployment/deployment_guide.md) - How to deploy

## For Developers
- [Architecture Overview](architecture/architecture_map.md)
- [RAG System](architecture/rag_system.md) - How to modify retrieval
- [API Reference](api/endpoints.md)

## For Deployers
- [Deployment Decision Matrix](deployment/decision_matrix.md)
- [Railway Deployment](deployment/railway.md)
- [Webflow Integration](webflow/integration_overview.md)

## For Testers
- [Testing Brief](testing/testing_brief.md)
- [Test Plans](testing/README.md)

## Archive
- Historical documents and deprecated guides
```

## Phase 3: Code Organization

### Task 3.1: Organize Scripts
Move all one-off scripts to appropriate subdirectories:

```bash
# Create scripts directory structure
mkdir -p scripts/{preprint,testing,data_migration,utilities}

# Preprint-related scripts
git mv extract_preprint.py scripts/preprint/
git mv extract_preprint_simple.py scripts/preprint/
git mv chunk_and_index_preprint.py scripts/preprint/
git mv index_preprint_to_chromadb.py scripts/preprint/
git mv load_preprint_to_vectordb.py scripts/preprint/
git mv test_preprint_coverage.py scripts/preprint/
git mv test_preprint_integration.py scripts/preprint/

# Data migration scripts
git mv reingest_all_documents.py scripts/data_migration/
git mv init_metadata.py scripts/data_migration/
git mv test_reingest.py scripts/data_migration/

# Testing generation scripts
git mv create_feedback_docx.py scripts/testing/
git mv create_performance_docs.py scripts/testing/
git mv create_merged_testing_doc.py scripts/testing/
git mv create_ui_performance_doc.py scripts/testing/

# Debugging utilities
git mv debug_retrieval.py scripts/utilities/
git mv test_import_safety.py scripts/utilities/
```

Add README to each scripts subdirectory explaining purpose.

### Task 3.2: Organize Webflow Integration Code
Consolidate all Webflow-related files:

```bash
mkdir -p webflow/{widget/versions,chatbot_page,analytics}

# Widget versions (archive old ones)
git mv webflow_widget_COMPLETE.html webflow/widget/widget.html
git mv webflow_widget_ready.html webflow/widget/versions/v1_ready.html
git mv webflow_widget_branded.html webflow/widget/versions/v2_branded.html
git mv webflow_widget_resizable.html webflow/widget/versions/v3_resizable.html
git mv webflow_widget_final.html webflow/widget/versions/v4_final.html
git mv webflow_widget_session.html webflow/widget/versions/v5_session.html
git mv widget_implementation.html webflow/widget/versions/v0_implementation.html

# Chatbot page code
git mv conversation_transfer_receiver.js webflow/chatbot_page/
# Move docs/webflow_chatbot_page_* files here too

# Analytics
git mv webflow_posthog_integration.html webflow/analytics/
```

Create `webflow/README.md` explaining the integration architecture.

### Task 3.3: Organize Test Results
Move all test result files to dedicated directory:

```bash
mkdir -p test_results/{taxonomy,performance,integration}

# Taxonomy test results
git mv taxonomy_test_results.json test_results/taxonomy/
git mv taxonomy_test_results_comprehensive.json test_results/taxonomy/
git mv taxonomy_test_summary.json test_results/taxonomy/
git mv taxonomy_queries_responses_*.{json,md} test_results/taxonomy/

# Performance/integration results
git mv test_results_105_prompts_updated_*.json test_results/performance/
git mv extracted_prompts_responses.{json,md} test_results/performance/
git mv preprint_integration_results.json test_results/integration/

# Debug logs
git mv debug_105_test_*.log test_results/performance/logs/
git mv server.log test_results/logs/ || true  # May be actively written
```

### Task 3.4: Archive or Remove Deprecated Files
Move clearly deprecated/temporary files:

```bash
mkdir -p .archive/{temp,old_docs,old_tests}

# Temporary Word doc locks
git rm ~$*.docx 2>/dev/null || mv ~$*.docx .archive/temp/ 2>/dev/null

# Old HTML files (if superseded)
git mv CHATBOT_TESTING_BRIEF.html .archive/old_docs/
git mv webflow-bundle.html .archive/old_docs/ # If not used

# Consolidated .gitignore additions
echo "
# Archive directory
.archive/

# Test results (keep in repo but don't track new ones)
test_results/**/*.log
test_results/**/*_$(date +%Y%m%d_*).*

# Temp files
~$*
*.log
" >> .gitignore
```

## Phase 4: RAG System Documentation

### Task 4.1: Document Current RAG Architecture
Create comprehensive RAG documentation in `docs/architecture/rag_system.md`:

**Required sections:**
1. **Overview** - High-level architecture diagram
2. **Components**:
   - Vector Store (ChromaDB usage, collection management)
   - Embedding Service (Google Embeddings)
   - Retrievers (FieldAwareHybridRetriever, etc.)
   - Query Processing Pipeline
   - Response Synthesis
3. **Data Flow** - Query → Retrieval → Synthesis → Response
4. **Key Files and Their Roles**:
   - `src/core/storage/vector_store.py` - Vector database interface
   - `src/core/query/retriever.py` - Retrieval strategies
   - `src/core/services/chat_service.py` - Orchestration
5. **Configuration Points** - Where to change parameters

### Task 4.2: Create RAG Modification Guide
Create `docs/architecture/modifying_rag.md`:

**Guide for common modifications:**

```markdown
# How to Modify the RAG System

## Switching Retrieval Methods

### Current Implementation
- **Hybrid Retrieval**: Combines semantic + keyword search
- **Field-Aware**: Considers taxonomy structure
- **Re-ranking**: Not currently implemented

### To Switch Retrievers

1. **Create New Retriever Class**:
   ```python
   # src/core/query/retriever.py
   class YourNewRetriever(BaseRetriever):
       def retrieve(self, query, top_k=10):
           # Your implementation
   ```

2. **Register in Chat Service**:
   ```python
   # src/core/services/chat_service.py
   # Line ~XX: Change retriever initialization
   ```

3. **Update Configuration**:
   ```python
   # src/config/settings.py
   RETRIEVER_TYPE = "your_new_retriever"
   ```

4. **Test Changes**:
   ```bash
   python -m pytest tests/unit/test_retriever.py
   python scripts/testing/test_retrieval_quality.py
   ```

### Example: Adding BM25 Retrieval

[Step-by-step example with code snippets]

### Example: Switching to Pinecone

[Step-by-step example for changing vector stores]
```

## Phase 5: Update Configuration and Build

### Task 5.1: Update Import Paths
Create `scripts/utilities/update_imports.py` to:
1. Find all imports of moved files
2. Update to new paths
3. Add deprecation warnings to old locations

### Task 5.2: Update Build Configuration
Update all build/deploy configs:
- `Dockerfile` - Ensure COPY commands include new paths
- `railway.json` - Update build commands if needed
- `.gitignore` - Add new directories appropriately
- Frontend build (vite.config.ts) - Verify no broken paths

### Task 5.3: Update README
Rewrite main README.md to reflect new structure:

```markdown
# AIRI Chatbot

AI Risk Repository chatbot with advanced RAG capabilities.

## Quick Start
[Keep existing quick start]

## Project Structure

```
├── src/              # Core application code
├── frontend/         # React TypeScript frontend
├── tests/            # Test suites
├── scripts/          # Utility scripts
├── docs/             # Documentation
├── webflow/          # Webflow integration
└── data/             # Data files and vector DB
```

See [Documentation Index](docs/README.md) for detailed guides.

## Common Tasks

### Modifying RAG Behavior
See [Modifying RAG Guide](docs/architecture/modifying_rag.md)

### Deploying
See [Deployment Guide](docs/deployment/deployment_guide.md)

### Running Tests
```bash
pytest tests/
```

[Rest of README]
```

## Phase 6: Testing and Validation

### Task 6.1: Pre-deployment Testing
Before committing any changes:

```bash
# Run full test suite
pytest tests/ -v

# Test import paths
python -c "from src.core.services.chat_service import ChatService; print('✓ Imports work')"

# Test build
docker build -t airi-test .

# Verify frontend builds
cd frontend && npm run build

# Check for broken imports
grep -r "from scripts\." src/ tests/  # Should be empty after migration
```

### Task 6.2: Deployment Verification
Deploy to Railway staging (if available) or test locally:

```bash
# Build production
docker build -t airi-production .
docker run -p 8090:8090 airi-production

# Test key endpoints
curl http://localhost:8090/api/health
curl -X POST http://localhost:8090/api/v1/stream -d '{"message":"test"}'

# Test frontend
open http://localhost:8090
```

### Task 6.3: Documentation Validation
Verify all documentation links work:

```bash
# Check for broken internal links
find docs/ -name "*.md" -exec grep -H "\](.*\.md)" {} \; | while read line; do
  # Parse and verify links exist
done

# Verify code examples in docs are valid
# Extract code blocks and test syntax
```

## Phase 7: Cleanup and Optimization

### Task 7.1: Remove True Duplicates
Identify and remove actual duplicate files (not versions):

```bash
# Find duplicates by hash
find . -type f -exec md5 {} \; | sort | uniq -d

# Review and remove confirmed duplicates
```

### Task 7.2: Optimize .gitignore
Update `.gitignore` to prevent future clutter:

```gitignore
# Test results (keep structure, ignore new results)
test_results/**/*.json
test_results/**/*.log
!test_results/README.md

# Temporary files
*.log
~$*
*.tmp

# Build artifacts
*.pyc
__pycache__/
.venv/
node_modules/
dist/
build/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Archive
.archive/
```

### Task 7.3: Create Maintenance Guide
Create `docs/MAINTENANCE.md`:

```markdown
# Maintenance Guide

## Adding New Features

1. **New RAG Components**: See [Modifying RAG](architecture/modifying_rag.md)
2. **New API Endpoints**: Add to `src/api/routes/`, document in `docs/api/`
3. **New Tests**: Add to `tests/`, results go to `test_results/`

## File Organization Rules

- **Scripts**: One-off utilities go in `scripts/[category]/`
- **Documentation**: All docs in `docs/[category]/`
- **Test Results**: Archive in `test_results/[category]/`
- **Webflow Code**: Integration code in `webflow/`
- **Never commit**: Logs, temp files, credentials

## Before Deploying

- [ ] Run test suite: `pytest tests/`
- [ ] Update CHANGELOG.md
- [ ] Test build: `docker build -t test .`
- [ ] Verify imports work
- [ ] Check Railway deployment settings
```

## Deliverables

After completing all phases, you should have:

1. ✅ **Clean Root Directory** - Only essential files (main.py, requirements.txt, Dockerfile, README.md, etc.)
2. ✅ **Organized Documentation** - All docs in `docs/` with clear index
3. ✅ **Categorized Scripts** - All utilities in `scripts/` with READMEs
4. ✅ **Webflow Integration Hub** - All Webflow code in `webflow/`
5. ✅ **Test Results Archive** - Historical results in `test_results/`
6. ✅ **RAG Modification Guide** - Clear instructions for changing retrieval methods
7. ✅ **Updated README** - Reflects new structure
8. ✅ **All Tests Passing** - No broken imports or functionality
9. ✅ **Deployment Verified** - Successfully builds and deploys
10. ✅ **Migration Commit** - Single well-documented commit with all moves

## Success Criteria

1. **A new developer can**:
   - Understand project structure in < 5 minutes
   - Find relevant documentation in < 2 minutes
   - Modify RAG method following guide without asking questions

2. **Deployment still works**:
   - Railway build succeeds
   - All API endpoints functional
   - Frontend loads and works
   - No broken imports

3. **Codebase is maintainable**:
   - Clear separation of concerns
   - No duplicate or deprecated files in main directories
   - Easy to find and modify any component

## Important Notes

- **Make incremental commits** - Don't do everything in one commit
- **Test after each phase** - Verify nothing breaks
- **Use `git mv`** - Preserves file history
- **Update imports carefully** - Use search/replace with verification
- **Keep backups** - Tag current state before starting: `git tag pre-cleanup`
- **Document decisions** - Why files were moved/archived

## Execution Strategy

Execute phases sequentially:
1. Analysis (Phase 1) - No code changes
2. Documentation (Phase 2) - Low risk moves
3. Code organization (Phase 3) - Higher risk, test thoroughly
4. RAG docs (Phase 4) - No code changes
5. Configuration (Phase 5) - Test extensively
6. Testing (Phase 6) - Validation phase
7. Cleanup (Phase 7) - Final polish

After each phase, commit with descriptive message and verify build succeeds.
