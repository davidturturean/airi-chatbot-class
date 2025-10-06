# Test Results Archive

This directory contains historical test results and performance benchmarks.

## Directory Structure

```
test_results/
├── taxonomy/          # Taxonomy-based testing results
├── performance/       # Performance benchmark results
├── integration/       # Integration test results
└── logs/             # Debug and execution logs
```

## Subdirectories

### taxonomy/
Results from taxonomy-based query testing:
- `taxonomy_test_results.json` - Initial taxonomy tests
- `taxonomy_test_results_comprehensive.json` - Comprehensive taxonomy coverage
- `taxonomy_test_summary.json` - Summary of taxonomy tests
- `taxonomy_queries_responses_*.json` - Timestamped query/response pairs
- `taxonomy_queries_responses_*.md` - Human-readable results

### performance/
Performance testing and benchmark results:
- `test_results_105_prompts_updated_*.json` - 105-prompt test suite results
- `extracted_prompts_responses.json` - Extracted prompt/response data
- `extracted_prompts_responses.md` - Human-readable prompt/response log

### integration/
Integration testing results:
- `preprint_integration_results.json` - Preprint integration test results

### logs/
Debug and execution logs:
- `debug_105_test_*.log` - Debug logs from 105-prompt tests
- `server.log` - Server execution log (may be actively written)

## Usage

These files are for historical reference and analysis. They are not used by the application at runtime.

### Analyzing Results

To analyze test results:
```python
import json

# Load taxonomy results
with open('test_results/taxonomy/taxonomy_test_results_comprehensive.json') as f:
    results = json.load(f)

# Analyze performance
with open('test_results/performance/test_results_105_prompts_updated_20250806_011643.json') as f:
    perf_data = json.load(f)
```

## Git Ignore

Large log files and timestamped results are gitignored to prevent repository bloat. The directory structure is preserved with this README.

## Generating New Results

When running tests that generate results:
1. Tests in `tests/` - Results go to `test_results/`
2. Scripts in `scripts/testing/` - Results go to `test_results/`
3. Use timestamped filenames for new results
4. Update this README if adding new result categories

## Retention Policy

- Keep latest comprehensive results for each test type
- Archive older results locally if needed
- Don't commit files larger than 10MB
- Logs older than 30 days can be removed
