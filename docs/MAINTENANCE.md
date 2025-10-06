# Maintenance Guide

This guide helps maintain the organized codebase structure and provides guidelines for adding new features, files, and documentation.

## Table of Contents
1. [File Organization Rules](#file-organization-rules)
2. [Adding New Features](#adding-new-features)
3. [Adding Documentation](#adding-documentation)
4. [Managing Test Results](#managing-test-results)
5. [Before Deploying](#before-deploying)
6. [Keeping the Codebase Clean](#keeping-the-codebase-clean)

## File Organization Rules

### Core Principles

1. **Root directory** is for essential files only
2. **All documentation** goes in `docs/`
3. **One-off scripts** go in `scripts/`
4. **Test results** go in `test_results/`
5. **Webflow code** goes in `webflow/`
6. **Never commit** logs, temp files, or credentials

### Root Directory - Essential Files Only

Keep ONLY these types of files in root:

**Application Core:**
- `main.py` - Entry point
- `requirements.txt` - Dependencies
- `package.json` - Node dependencies

**Configuration:**
- `Dockerfile` - Container config
- `railway.json` - Deployment config
- `.env.example` - Example environment
- `.gitignore` - Git ignore rules
- `.dockerignore` - Docker ignore rules

**Documentation:**
- `README.md` - Main README only
- `LICENSE` - License file

**Utilities:**
- `run.sh`, `auto-sync.sh` - Startup scripts

### Where Files Should Go

| File Type | Location | Example |
|-----------|----------|---------|
| Documentation (.md) | `docs/{category}/` | `docs/testing/new_test_plan.md` |
| Scripts (.py) | `scripts/{category}/` | `scripts/utilities/new_debug_tool.py` |
| Test results (.json, .log) | `test_results/{category}/` | `test_results/performance/benchmark.json` |
| Webflow HTML/JS | `webflow/{type}/` | `webflow/widget/new_version.html` |
| Source code (.py) | `src/` | `src/core/services/new_service.py` |
| Tests (.py) | `tests/` | `tests/unit/test_new_feature.py` |
| Generated docs (.docx) | `GoogleDocs/` | `GoogleDocs/test_report.docx` |
| Temporary files | `.archive/temp/` or delete | `.archive/temp/old_file.py` |

## Adding New Features

### 1. New RAG Components

**Location:** `src/core/`

**Process:**
1. Determine component type:
   - Retriever → `src/core/retrieval/`
   - Storage → `src/core/storage/`
   - Query processing → `src/core/query/`
   - Service → `src/core/services/`

2. Create the file:
   ```bash
   # Example: New retriever
   touch src/core/retrieval/semantic_retriever.py
   ```

3. Add tests:
   ```bash
   touch tests/unit/test_semantic_retriever.py
   ```

4. Update documentation:
   ```bash
   # Update relevant architecture docs
   nano docs/architecture/rag_system.md
   ```

5. See [Modifying RAG Guide](architecture/modifying_rag.md) for details

### 2. New API Endpoints

**Location:** `src/api/routes/`

**Process:**
1. Create route file:
   ```bash
   touch src/api/routes/new_feature.py
   ```

2. Register in `src/api/app.py`:
   ```python
   from .routes.new_feature import new_feature_bp
   app.register_blueprint(new_feature_bp)
   ```

3. Document in `docs/api/`:
   ```bash
   nano docs/api/endpoints.md
   ```

4. Add integration tests:
   ```bash
   touch tests/integration/test_new_feature_api.py
   ```

### 3. New Scripts

**Location:** `scripts/{category}/`

**Categories:**
- `preprint/` - Preprint processing
- `testing/` - Test generation and utilities
- `data_migration/` - Data reingestion and migration
- `utilities/` - Debug and general utilities

**Process:**
1. Determine category
2. Create script:
   ```bash
   touch scripts/utilities/new_debug_tool.py
   ```

3. Add shebang and docstring:
   ```python
   #!/usr/bin/env python3
   """
   Description of what this script does.

   Usage:
       python scripts/utilities/new_debug_tool.py [args]
   """
   ```

4. Update `scripts/README.md` with description

### 4. New Tests

**Location:** `tests/{type}/`

**Types:**
- `unit/` - Unit tests
- `integration/` - Integration tests
- `e2e/` - End-to-end tests

**Process:**
1. Create test file:
   ```bash
   touch tests/unit/test_new_feature.py
   ```

2. Follow naming convention:
   - File: `test_{feature_name}.py`
   - Class: `Test{FeatureName}`
   - Methods: `test_{specific_behavior}`

3. Run tests:
   ```bash
   python -m pytest tests/unit/test_new_feature.py -v
   ```

4. Results go to `test_results/` (gitignored)

## Adding Documentation

### Documentation Structure

```
docs/
├── README.md                 # Documentation hub (update this!)
├── architecture/             # Technical docs
├── deployment/               # Deployment guides
├── testing/                  # Testing documentation
├── webflow/                  # Webflow integration
├── api/                      # API documentation
└── archive/                  # Deprecated docs
```

### Adding New Documentation

1. **Determine category:**
   - Technical/architecture → `docs/architecture/`
   - Deployment/operations → `docs/deployment/`
   - Testing/QA → `docs/testing/`
   - Webflow/integration → `docs/webflow/`
   - API reference → `docs/api/`

2. **Create the document:**
   ```bash
   touch docs/architecture/new_feature_design.md
   ```

3. **Add to docs index:**
   ```bash
   nano docs/README.md
   # Add link in appropriate section
   ```

4. **Follow format:**
   ```markdown
   # Title

   Brief summary of what this doc covers.

   ## Table of Contents
   ## Section 1
   ## Section 2

   ## Related Documentation
   - [Link to related doc](other_doc.md)
   ```

### Updating Existing Documentation

When you modify the system:

**Must update:**
- `docs/architecture/rag_system.md` - If RAG components change
- `docs/architecture/modifying_rag.md` - If modification process changes
- `README.md` - If public API or setup changes

**Should update:**
- Relevant architecture docs - If implementation changes
- API docs - If endpoints change
- Deployment docs - If deployment process changes

## Managing Test Results

### Automatic Archiving

Test results automatically go to `test_results/` when you run:

```bash
# These scripts output to test_results/
python scripts/testing/root_test_files/test_comprehensive_taxonomy.py
python scripts/preprint/test_preprint_coverage.py
```

### Manual Organization

When you generate results:

1. **Categorize by type:**
   - Taxonomy tests → `test_results/taxonomy/`
   - Performance tests → `test_results/performance/`
   - Integration tests → `test_results/integration/`
   - Logs → `test_results/logs/`

2. **Use timestamps:**
   ```bash
   # Good
   test_results_20251006_143022.json

   # Bad
   results.json
   ```

3. **Don't commit large files:**
   - Test results are gitignored
   - Keep only essential baseline results in git
   - Archive old results locally

### Cleaning Up Test Results

Periodically clean old results:

```bash
# Keep results from last 30 days
find test_results/ -name "*.json" -mtime +30 -delete
find test_results/ -name "*.log" -mtime +7 -delete
```

## Before Deploying

### Pre-Deployment Checklist

Run through this checklist before every deployment:

#### 1. Code Quality

```bash
# All imports work
python -c "from src.core.services.chat_service import ChatService; print('✓')"

# No syntax errors
python -m py_compile src/**/*.py

# Code formatted (optional)
black src/ tests/
```

#### 2. Tests Pass

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Critical functionality
python scripts/testing/root_test_files/test_comprehensive_taxonomy.py
```

#### 3. Configuration

```bash
# .env.example is up to date
diff .env .env.example (should show only secrets)

# Dockerfile builds
docker build -t airi-test .

# Frontend builds
cd frontend && npm run build
```

#### 4. Documentation

- [ ] README.md reflects current features
- [ ] Docs updated for new features
- [ ] API docs match actual endpoints
- [ ] Configuration docs show all env vars

#### 5. Deployment Config

```bash
# Railway config valid
cat railway.json

# All required env vars in Railway dashboard
# PORT, GEMINI_API_KEY, etc.
```

#### 6. Git Status Clean

```bash
# No uncommitted changes
git status

# All changes committed
git log -1

# Push to remote
git push origin main
```

### Deployment Steps

See [Deployment Guide](deployment/deployment_guide.md) for full process.

**Quick checklist:**
1. ✓ Tests passing
2. ✓ Config updated
3. ✓ Documentation current
4. ✓ Git committed and pushed
5. ✓ Railway deployment triggered
6. ✓ Health check passes
7. ✓ Test key endpoints

## Keeping the Codebase Clean

### Daily Practices

**DO:**
- ✓ Put files in correct directories
- ✓ Use descriptive names
- ✓ Update documentation when you change code
- ✓ Commit related changes together
- ✓ Write meaningful commit messages

**DON'T:**
- ✗ Leave files in root directory
- ✗ Commit logs or test results
- ✗ Commit temporary files
- ✗ Use vague names like `test.py` or `temp.py`
- ✗ Make huge commits with unrelated changes

### Weekly Maintenance

Run these tasks weekly:

```bash
# 1. Check for misplaced files
find . -maxdepth 1 -type f -name "*.py" | grep -v main.py
# Should only show main.py

# 2. Check for uncommitted files
git status --short
# Should be empty or only expected files

# 3. Clean up test results
find test_results/ -name "*.log" -mtime +7 -delete

# 4. Update dependencies if needed
pip list --outdated
```

### Monthly Maintenance

**Documentation Review:**
- [ ] README.md still accurate
- [ ] All links in docs work
- [ ] New features documented
- [ ] Deprecated docs moved to archive

**Codebase Review:**
- [ ] No deprecated code in main paths
- [ ] Test coverage adequate
- [ ] Performance acceptable
- [ ] No security issues

**Dependencies:**
- [ ] Update Python packages: `pip install --upgrade -r requirements.txt`
- [ ] Update Node packages: `cd frontend && npm update`
- [ ] Test after updates
- [ ] Commit updated lock files

### File Organization Guidelines

#### Quick Reference

**If you create:**
- `.md` file → `docs/{category}/`
- `.py` script → `scripts/{category}/`
- `.py` source → `src/{module}/`
- `.py` test → `tests/{type}/`
- `.json` result → `test_results/{category}/`
- `.html` webflow → `webflow/{type}/`
- `.log` file → `test_results/logs/` or delete
- `.docx` doc → `GoogleDocs/`

**Special cases:**
- `main.py` → Root (exception)
- `requirements.txt` → Root (exception)
- `README.md` → Root only for main README
- Config files → Root (`.env`, `Dockerfile`, etc.)

## Common Tasks

### Moving a Misplaced File

If you find a file in the wrong location:

```bash
# 1. Determine correct location
# Example: test_new_feature.py in root should be in tests/

# 2. Move with git mv (preserves history)
git mv test_new_feature.py tests/unit/test_new_feature.py

# 3. Commit
git add -A
git commit -m "Move test_new_feature.py to correct location"
```

### Archiving Deprecated Files

Don't delete deprecated files immediately:

```bash
# 1. Move to archive
mkdir -p .archive/deprecated_$(date +%Y%m%d)
git mv old_feature.py .archive/deprecated_20251006/

# 2. Document why
echo "Deprecated: Replaced by new_feature.py" > .archive/deprecated_20251006/README.md

# 3. Commit
git add -A
git commit -m "Archive deprecated old_feature.py"
```

### Updating After Pulling Changes

After `git pull`:

```bash
# 1. Check for new dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. Check for new docs
ls docs/

# 3. Reingestion if data structure changed
# (only if migration scripts exist)
python scripts/data_migration/reingest_all_documents.py
```

## Project Health Metrics

Use these commands to check project health:

```bash
# Root directory cleanliness (should be ~15-20 files)
ls -la | grep "^-" | wc -l

# Documentation coverage (should have README in each docs/ subdir)
find docs/ -maxdepth 2 -name "README.md"

# Test file count
find tests/ -name "test_*.py" | wc -l

# Source code organization
tree src/ -d -L 2

# Untracked files that shouldn't exist
git status --short | grep "^??"
```

## Getting Help

If unsure where something goes:

1. **Check this guide** - Does it fit a category here?
2. **Look at similar files** - Where are similar files located?
3. **Check docs/README.md** - Is there relevant documentation?
4. **Ask the team** - When in doubt, ask before moving

## Summary

**Golden Rules:**
1. Root is sacred - only essential files
2. Everything has a place - use the right directory
3. Document your changes - future you will thank you
4. Test before deploying - always
5. Keep it clean - don't let it get messy again

**When adding anything new:**
1. Choose the right location
2. Follow naming conventions
3. Update relevant documentation
4. Add tests if it's code
5. Commit with clear message

**Maintenance rhythm:**
- Daily: Follow organization rules
- Weekly: Check for misplaced files, clean old results
- Monthly: Review docs, update dependencies, check health

---

**This maintenance guide ensures the codebase stays organized and navigable for all developers.**

Last updated: October 2025
