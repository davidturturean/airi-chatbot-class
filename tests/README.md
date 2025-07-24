# AIRI Chatbot Tests

This directory contains all tests for the AIRI chatbot system.

## Directory Structure

- **`unit/`** - Unit tests for individual components
  - `services/` - Tests for service classes
  - `models/` - Tests for model classes
  - `utils/` - Tests for utility functions

- **`integration/`** - Integration tests
  - Tests that verify multiple components work together

- **`e2e/`** - End-to-end tests
  - `105_prompts/` - Full pipeline test with 105 diverse queries
  - `synthesis_tests/` - Tests for synthesis capabilities

- **`fixtures/`** - Test data and fixtures

- **`results/`** - Test outputs (ignored by git)
  - `extracted/` - Extracted Q&A pairs from test runs

- **`debug/`** - Debugging scripts (ignored by git)

## Running Tests

### Run the 105 Prompts Test
```bash
cd tests/e2e/105_prompts
python run_105_prompts_test.py
```

### Run Integration Tests
```bash
cd tests/integration
python test_105_prompts_full_pipeline.py
```

## Test Results

Test results are saved in the `results/` directory with timestamps. These are not tracked by git.