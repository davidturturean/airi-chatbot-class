# Scripts Directory

This directory contains one-off utility scripts and data processing tools that are not part of the core application.

## Directory Structure

```
scripts/
├── preprint/           # Preprint extraction and indexing scripts
├── testing/            # Test generation and document creation scripts
├── data_migration/     # Data reingestion and migration tools
├── utilities/          # Debugging and utility scripts
├── check_deployment_gates.py    # Deployment readiness validation
├── generate_test_data.py        # Test data generation
├── monitor_metrics.py           # Metrics monitoring
├── quick_test.py                # Quick testing utility
├── rebuild_database.py          # Database rebuild script
├── run_comprehensive_tests.py   # Comprehensive test suite
├── setup.py                     # Setup script
└── test_metrics_db.py          # Metrics database testing
```

## Subdirectories

### preprint/
Scripts for extracting, processing, and indexing academic preprints:
- `extract_preprint.py` - Extract content from preprint PDFs
- `extract_preprint_simple.py` - Simplified extraction
- `chunk_and_index_preprint.py` - Chunk and index preprint content
- `index_preprint_to_chromadb.py` - Index to ChromaDB
- `load_preprint_to_vectordb.py` - Load to vector database
- `test_preprint_coverage.py` - Test preprint coverage
- `test_preprint_integration.py` - Test preprint integration

### testing/
Scripts for generating testing documents and data:
- `create_feedback_docx.py` - Generate feedback documents
- `create_performance_docs.py` - Generate performance testing docs
- `create_merged_testing_doc.py` - Merge testing documents
- `create_ui_performance_doc.py` - UI performance documentation
- `root_test_files/` - Legacy test files from root directory

### data_migration/
Scripts for data migration and reingestion:
- `reingest_all_documents.py` - Reingest all documents to vector DB
- `init_metadata.py` - Initialize metadata
- `test_reingest.py` - Test reingestion process

### utilities/
General debugging and utility scripts:
- `debug_retrieval.py` - Debug retrieval issues
- `test_import_safety.py` - Test import safety

## Usage

Most scripts are meant to be run from the project root:

```bash
# From project root
python scripts/preprint/extract_preprint.py

# Or with full path
python -m scripts.preprint.extract_preprint
```

## Note

These scripts are typically one-off or maintenance tools. The core application logic is in `src/`.
