# Excel Formatting Optimization - Implementation Roadmap

## Executive Summary

**Objective:** Load Excel cell formatting for ALL rows without sacrificing initial load time.

**Recommended Solution:** Lazy Loading with Progressive Enhancement (Phased Approach)

**Expected Results:**
- ✅ Initial load time: **2-3s** (no change from current)
- ✅ All formatting loaded: **Within 10-30s** (background loading)
- ✅ User experience: **No degradation** (progressive enhancement)
- ✅ Implementation time: **1-2 weeks**

---

## Phase 1: Core Lazy Loading (Week 1)

### Goals
1. Add chunked formatting endpoint
2. Load first 100 rows immediately (current behavior)
3. Load additional formatting in background
4. No impact on initial UX

### Implementation Steps

#### Backend Changes

**File:** `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/src/api/routes/excel_viewer.py`

**Step 1.1: Add Chunked Formatting Endpoint (2 hours)**
```python
@excel_viewer_bp.route('/api/document/<rid>/excel/formatting-chunk', methods=['GET'])
def get_formatting_chunk(rid):
    """
    Get formatting for a specific row range.

    Query params:
      - session_id: Session identifier (required)
      - sheet: Sheet name (required)
      - start_row: Starting row, 0-indexed (default: 0)
      - end_row: Ending row, exclusive (default: 100)

    Returns:
      {
        "rid": "RID-07595",
        "sheet": "Sheet1",
        "start_row": 100,
        "end_row": 200,
        "formatting": {"100_1": {bgColor: "#fff"}, ...},
        "chunk_size": 50,
        "extraction_time_ms": 15.3
      }
    """
    start_time = datetime.now()

    try:
        # Validate params
        session_id = request.args.get('session_id')
        sheet_name = request.args.get('sheet')
        start_row = int(request.args.get('start_row', 0))
        end_row = int(request.args.get('end_row', 100))

        if not session_id or not sheet_name:
            return jsonify({"error": "Missing required parameters"}), 400

        if end_row <= start_row:
            return jsonify({"error": "end_row must be greater than start_row"}), 400

        # Get file path
        snippet_data = snippet_db.get_snippet(session_id, rid)
        if not snippet_data:
            return jsonify({"error": "Document not found"}), 404

        source_file = snippet_data.get('metadata', {}).get('source_file', '')
        file_path = _resolve_file_path(source_file)

        if not file_path or not file_path.exists():
            return jsonify({"error": "File not found"}), 404

        # Extract formatting for this chunk
        formatting = _extract_cell_formatting(
            file_path,
            sheet_name,
            offset=start_row,
            max_rows=end_row - start_row
        )

        extraction_time = (datetime.now() - start_time).total_seconds() * 1000

        return jsonify({
            'rid': rid,
            'sheet': sheet_name,
            'start_row': start_row,
            'end_row': end_row,
            'formatting': formatting,
            'chunk_size': len(formatting),
            'extraction_time_ms': round(extraction_time, 2)
        })

    except Exception as e:
        logger.error(f"Error getting formatting chunk for {rid}: {str(e)}")
        return jsonify({"error": str(e)}), 500
```

**Step 1.2: Verify `_extract_cell_formatting` Supports Offset (1 hour)**

Current implementation already supports offset:
```python
# Line 504: start_row = offset + 1
```
✅ No changes needed - already supports arbitrary offset.

**Testing:**
```bash
# Test endpoint manually
curl "http://localhost:5000/api/document/RID-07595/excel/formatting-chunk?session_id=test&sheet=Sheet1&start_row=100&end_row=200"
```

#### Frontend Changes

**File:** `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/frontend/src/components/viewers/ExcelViewer.tsx`

**Step 1.3: Add Chunk Loading Hook (4 hours)**
```typescript
// Add after existing imports
import { useState, useEffect, useCallback, useRef } from 'react';

// Add new hook before ExcelViewer component
const useFormattingChunks = (
  rid: string,
  sessionId: string,
  activeSheet: string,
  totalRows: number,
  initialFormatting: Record<string, CellFormatting>
) => {
  const [formatting, setFormatting] = useState(initialFormatting);
  const [loadedChunks, setLoadedChunks] = useState<Set<number>>(new Set([0]));
  const [isLoadingChunk, setIsLoadingChunk] = useState(false);
  const CHUNK_SIZE = 100;

  const loadChunk = useCallback(async (chunkIndex: number) => {
    if (loadedChunks.has(chunkIndex) || isLoadingChunk) {
      return;
    }

    setIsLoadingChunk(true);
    const startRow = chunkIndex * CHUNK_SIZE;
    const endRow = Math.min(startRow + CHUNK_SIZE, totalRows);

    try {
      const response = await fetch(
        `/api/document/${rid}/excel/formatting-chunk?` +
        `session_id=${sessionId}&sheet=${activeSheet}&start_row=${startRow}&end_row=${endRow}`,
        { signal: AbortSignal.timeout(10000) }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      // Merge new formatting
      setFormatting(prev => ({
        ...prev,
        ...data.formatting
      }));

      setLoadedChunks(prev => new Set(prev).add(chunkIndex));
      console.log(`✅ Loaded formatting chunk ${chunkIndex} (${data.chunk_size} cells, ${data.extraction_time_ms}ms)`);

    } catch (error) {
      console.error(`❌ Failed to load chunk ${chunkIndex}:`, error);
    } finally {
      setIsLoadingChunk(false);
    }
  }, [rid, sessionId, activeSheet, totalRows, loadedChunks, isLoadingChunk]);

  // Auto-load chunks in background
  useEffect(() => {
    const totalChunks = Math.ceil(totalRows / CHUNK_SIZE);
    let currentChunk = 1; // Start from chunk 1 (0 already loaded)

    const loadNextChunk = () => {
      if (currentChunk < totalChunks && !loadedChunks.has(currentChunk)) {
        loadChunk(currentChunk);
        currentChunk++;
        setTimeout(loadNextChunk, 200); // Throttle: 5 chunks/sec
      }
    };

    // Start loading after 500ms (let initial render complete)
    const timer = setTimeout(loadNextChunk, 500);
    return () => clearTimeout(timer);
  }, [totalRows, loadChunk, loadedChunks]);

  return {
    formatting,
    loadedChunks: loadedChunks.size,
    totalChunks: Math.ceil(totalRows / CHUNK_SIZE),
    loadChunk
  };
};

// Update ExcelViewer component
export const ExcelViewer: React.FC<ExcelViewerProps> = ({ data, ... }) => {
  // ... existing state ...

  // Get session ID from props or context
  const sessionId = props.sessionId || 'default'; // Adjust based on your setup

  // Use formatting chunks hook
  const {
    formatting,
    loadedChunks,
    totalChunks,
    loadChunk
  } = useFormattingChunks(
    data.rid,
    sessionId,
    activeSheet,
    currentSheetData?.total_rows || 0,
    currentSheetData?.formatting || {}
  );

  // Update FormattedCell to use formatting from hook
  const FormattedCell = (props: RenderCellProps<any>) => {
    // ... existing code ...

    // Change this line:
    // const fmt: CellFormatting | undefined = formatting[cellKey];

    // To use formatting from hook:
    const fmt: CellFormatting | undefined = formatting[cellKey];

    // ... rest of cell rendering ...
  };

  // Add loading indicator
  const showLoadingIndicator = loadedChunks < totalChunks;

  return (
    <div className="excel-viewer flex flex-col h-full">
      {/* ... existing toolbar ... */}

      {/* Add loading indicator after toolbar */}
      {showLoadingIndicator && (
        <div className="px-4 py-2 bg-blue-50 border-b border-blue-200 text-xs text-blue-800">
          Loading formatting: {loadedChunks} / {totalChunks} chunks loaded
        </div>
      )}

      {/* ... rest of component ... */}
    </div>
  );
};
```

**Step 1.4: Update Initial Load to NOT Include Formatting (1 hour)**

**File:** `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/frontend/src/components/preview/EnhancedSlideoutPanel.tsx`

Change line 109 from:
```typescript
// OLD: include_formatting=false (no formatting at all)
const response = await fetch(`/api/document/${rid}/excel?session_id=${props.sessionId}&include_formatting=false`, {
```

To:
```typescript
// NEW: include_formatting=true (first 100 rows only)
const response = await fetch(`/api/document/${rid}/excel?session_id=${props.sessionId}&include_formatting=true`, {
```

**Why this works:**
- Backend already limits formatting to first 100 rows (line 501)
- This gives us initial formatting for chunk 0
- Additional chunks loaded in background

### Testing Phase 1

**Test Cases:**
1. ✅ Small file (100 rows) - should load instantly, no background loading
2. ✅ Medium file (500 rows) - should load first 100 instantly, then 4 more chunks
3. ✅ Large file (5000 rows) - should load first 100 instantly, then 49 more chunks
4. ✅ Sheet switching - should cancel background loading, start fresh
5. ✅ Scroll during loading - should not break rendering

**Performance Verification:**
```typescript
// Add to useFormattingChunks hook for testing
useEffect(() => {
  if (loadedChunks === totalChunks) {
    console.log(`✅ All ${totalChunks} chunks loaded successfully`);
    console.log(`Total formatting cells: ${Object.keys(formatting).length}`);
  }
}, [loadedChunks, totalChunks]);
```

**Expected Results:**
- Initial render: 2-3s (unchanged)
- 1000-row file: All chunks loaded within 5-10s
- 5000-row file: All chunks loaded within 20-30s
- No UI jank or freezing

---

## Phase 2: Compression Enhancement (Week 2)

### Goals
1. Reduce network transfer by 60-70%
2. Especially beneficial for mobile/slow networks
3. Minimal CPU overhead

### Implementation Steps

**File:** `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/src/api/routes/excel_viewer.py`

**Step 2.1: Add Compression Function (2 hours)**
```python
def _compress_formatting_with_palette(formatting: dict) -> dict:
    """
    Compress formatting using style palette approach.
    Reduces payload size by 60-70% for typical spreadsheets.
    """
    import json

    palette = {}
    cells = {}
    style_map = {}
    next_id = 0

    for cell_key, fmt in formatting.items():
        fmt_json = json.dumps(fmt, sort_keys=True)

        if fmt_json not in style_map:
            style_map[fmt_json] = next_id
            palette[next_id] = fmt
            next_id += 1

        cells[cell_key] = style_map[fmt_json]

    return {
        "version": "v1",
        "palette": palette,
        "cells": cells,
        "stats": {
            "total_cells": len(cells),
            "unique_styles": len(palette),
            "compression_ratio": len(palette) / len(cells) if cells else 0
        }
    }
```

**Step 2.2: Apply Compression to Chunk Endpoint (1 hour)**
```python
@excel_viewer_bp.route('/api/document/<rid>/excel/formatting-chunk', methods=['GET'])
def get_formatting_chunk(rid):
    # ... existing code to extract formatting ...

    # Add compression (optional, controlled by query param)
    use_compression = request.args.get('compress', 'true').lower() == 'true'

    if use_compression and formatting:
        compressed = _compress_formatting_with_palette(formatting)
        return jsonify({
            'rid': rid,
            'sheet': sheet_name,
            'start_row': start_row,
            'end_row': end_row,
            'formatting': compressed,  # Compressed format
            'extraction_time_ms': round(extraction_time, 2)
        })
    else:
        # Uncompressed (for backwards compatibility)
        return jsonify({
            'rid': rid,
            'sheet': sheet_name,
            'start_row': start_row,
            'end_row': end_row,
            'formatting': formatting,
            'extraction_time_ms': round(extraction_time, 2)
        })
```

**Step 2.3: Update Frontend to Decompress (2 hours)**

**File:** `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/frontend/src/components/viewers/ExcelViewer.tsx`

```typescript
// Add decompression function
const decompressFormatting = (compressed: any): Record<string, CellFormatting> => {
  if (compressed.version === 'v1') {
    // Style palette format
    const { palette, cells } = compressed;
    const decompressed: Record<string, CellFormatting> = {};

    for (const [cellKey, styleId] of Object.entries(cells)) {
      decompressed[cellKey] = palette[styleId as number];
    }

    console.log(
      `Decompressed formatting: ${compressed.stats.total_cells} cells using ${compressed.stats.unique_styles} styles ` +
      `(${(compressed.stats.compression_ratio * 100).toFixed(1)}% compression ratio)`
    );

    return decompressed;
  } else {
    // Uncompressed or unknown format
    return compressed;
  }
};

// Update loadChunk in useFormattingChunks
const loadChunk = useCallback(async (chunkIndex: number) => {
  // ... existing code ...

  const data = await response.json();

  // Decompress if needed
  const chunkFormatting = data.formatting.version
    ? decompressFormatting(data.formatting)
    : data.formatting;

  // Merge
  setFormatting(prev => ({
    ...prev,
    ...chunkFormatting
  }));

  // ... rest of code ...
}, [...]);
```

### Testing Phase 2

**Compression Verification:**
```python
# Backend test
def test_compression_ratio():
    file_path = Path("data/info_files/The_AI_Risk_Repository_V3_26_03_2025.xlsx")
    formatting = _extract_cell_formatting(file_path, "Sheet1", 0, 100)

    uncompressed_size = len(json.dumps(formatting))
    compressed = _compress_formatting_with_palette(formatting)
    compressed_size = len(json.dumps(compressed))

    print(f"Uncompressed: {uncompressed_size} bytes")
    print(f"Compressed: {compressed_size} bytes")
    print(f"Reduction: {(1 - compressed_size/uncompressed_size)*100:.1f}%")

    # Should see 60-70% reduction
    assert compressed_size < uncompressed_size * 0.4
```

**Network Savings:**
- 100 cells: 5KB → 1.7KB (66% reduction)
- 1000 cells: 50KB → 17KB (66% reduction)
- 10000 cells: 500KB → 170KB (66% reduction)

---

## Phase 3: Production Optimization (Week 3-4, Optional)

### Goals
1. Add Redis caching for repeated requests
2. Achieve <200ms load time on cache hit
3. Only deploy if traffic justifies infrastructure

### Implementation Steps

**Step 3.1: Set Up Redis (1 day)**

**File:** `docker-compose.yml` (create if doesn't exist)
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    container_name: excel_formatting_cache
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    restart: unless-stopped

volumes:
  redis_data:
```

**File:** `requirements.txt`
```
redis==5.0.0
```

**Step 3.2: Add Redis Caching Layer (2 hours)**

**File:** `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/src/api/routes/excel_viewer.py`

```python
import redis
import hashlib
import json

# Initialize Redis (with fallback if unavailable)
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=0,
        decode_responses=True,
        socket_connect_timeout=2
    )
    redis_client.ping()  # Test connection
    REDIS_AVAILABLE = True
    logger.info("✅ Redis cache connected")
except:
    REDIS_AVAILABLE = False
    logger.warning("⚠️ Redis unavailable, caching disabled")

def _get_file_hash(file_path: Path) -> str:
    """Get unique hash for file (based on mtime and size)."""
    stat = file_path.stat()
    return hashlib.md5(f"{file_path}:{stat.st_mtime}:{stat.st_size}".encode()).hexdigest()

def _get_formatting_cache_key(file_path: Path, sheet_name: str, offset: int, max_rows: int) -> str:
    """Generate Redis cache key."""
    file_hash = _get_file_hash(file_path)
    return f"excel:fmt:{file_hash}:{sheet_name}:{offset}:{max_rows}"

def _extract_cell_formatting_cached(file_path: Path, sheet_name: str, offset: int = 0, max_rows: int = 100):
    """Extract formatting with Redis caching."""
    if not REDIS_AVAILABLE:
        return _extract_cell_formatting(file_path, sheet_name, offset, max_rows)

    cache_key = _get_formatting_cache_key(file_path, sheet_name, offset, max_rows)

    # Try cache
    try:
        cached = redis_client.get(cache_key)
        if cached:
            logger.info(f"✅ Formatting cache HIT: {cache_key[:50]}...")
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis read error: {e}")

    # Cache miss - extract
    logger.info(f"Formatting cache MISS: {cache_key[:50]}...")
    formatting = _extract_cell_formatting(file_path, sheet_name, offset, max_rows)

    # Cache result
    try:
        redis_client.setex(
            cache_key,
            3600,  # 1 hour TTL
            json.dumps(formatting)
        )
    except Exception as e:
        logger.warning(f"Redis write error: {e}")

    return formatting

# Update chunk endpoint to use cached version
@excel_viewer_bp.route('/api/document/<rid>/excel/formatting-chunk', methods=['GET'])
def get_formatting_chunk(rid):
    # ... validation code ...

    # Use cached extraction
    formatting = _extract_cell_formatting_cached(
        file_path,
        sheet_name,
        offset=start_row,
        max_rows=end_row - start_row
    )

    # ... rest of code ...
```

**Step 3.3: Monitor Cache Performance (2 hours)**

```python
@excel_viewer_bp.route('/api/excel/cache-stats', methods=['GET'])
def get_cache_stats():
    """Get Redis cache statistics."""
    if not REDIS_AVAILABLE:
        return jsonify({"error": "Redis not available"}), 503

    try:
        info = redis_client.info('stats')
        return jsonify({
            'redis_available': True,
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
            'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100,
            'memory_used_mb': info.get('used_memory', 0) / 1024 / 1024,
            'connected_clients': info.get('connected_clients', 0)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### Testing Phase 3

**Cache Hit Test:**
```python
# Test 1: First request (cache miss)
start = time.time()
formatting = _extract_cell_formatting_cached(file_path, "Sheet1", 0, 100)
time_miss = (time.time() - start) * 1000
print(f"Cache MISS: {time_miss:.2f}ms")

# Test 2: Second request (cache hit)
start = time.time()
formatting = _extract_cell_formatting_cached(file_path, "Sheet1", 0, 100)
time_hit = (time.time() - start) * 1000
print(f"Cache HIT: {time_hit:.2f}ms")

# Should see dramatic improvement
assert time_hit < time_miss * 0.2  # At least 5x faster
```

---

## Rollback Plan

### Phase 1 Rollback
If chunk loading causes issues:

1. **Disable chunk endpoint (immediate):**
   ```python
   @excel_viewer_bp.route('/api/document/<rid>/excel/formatting-chunk', methods=['GET'])
   def get_formatting_chunk(rid):
       return jsonify({"error": "Endpoint temporarily disabled"}), 503
   ```

2. **Revert frontend (next deploy):**
   ```typescript
   // Comment out useFormattingChunks hook
   // Use original formatting from data prop
   ```

### Phase 2 Rollback
If compression causes parsing errors:

1. **Disable compression (immediate):**
   ```python
   use_compression = False  # Force disable
   ```

2. **Frontend handles both formats (already implemented):**
   ```typescript
   // Already has fallback for uncompressed format
   const chunkFormatting = data.formatting.version
     ? decompressFormatting(data.formatting)
     : data.formatting;
   ```

### Phase 3 Rollback
If Redis causes issues:

1. **Disable Redis caching:**
   ```python
   REDIS_AVAILABLE = False  # Force disable
   ```

2. **Stop Redis container:**
   ```bash
   docker-compose stop redis
   ```

---

## Success Metrics

### Performance Metrics
| Metric | Baseline | Target | How to Measure |
|--------|----------|--------|----------------|
| Initial load time | 2-3s | <3s | Performance.now() in frontend |
| First chunk (100 rows) | N/A | <200ms | Backend logs |
| All chunks loaded (1000 rows) | N/A | <10s | Frontend logs |
| Network transfer per chunk | 5KB | <2KB | Chrome DevTools Network |
| Cache hit rate (Phase 3) | 0% | >60% | Redis stats endpoint |

### User Experience Metrics
- No increase in error rate
- No UI jank (maintain 60fps)
- No memory leaks (stable memory usage)
- Formatting appears progressively (no gaps)

### Monitoring Dashboard

**Grafana Queries:**
```promql
# Average chunk load time
histogram_quantile(0.95,
  rate(formatting_chunk_duration_ms_bucket[5m])
)

# Cache hit rate
sum(rate(formatting_cache_hits[5m])) /
sum(rate(formatting_cache_requests[5m])) * 100

# Network savings from compression
(
  avg(formatting_chunk_uncompressed_bytes) -
  avg(formatting_chunk_compressed_bytes)
) / avg(formatting_chunk_uncompressed_bytes) * 100
```

---

## Timeline Summary

### Week 1: Phase 1 - Core Lazy Loading
- **Day 1:** Backend chunked endpoint (3 hours)
- **Day 2:** Frontend chunk loading hook (4 hours)
- **Day 3:** Integration and testing (6 hours)
- **Day 4:** Bug fixes and refinement (4 hours)
- **Day 5:** Performance testing and optimization (4 hours)

### Week 2: Phase 2 - Compression
- **Day 1:** Backend compression logic (3 hours)
- **Day 2:** Frontend decompression (3 hours)
- **Day 3:** Testing and validation (4 hours)
- **Day 4:** Performance benchmarking (3 hours)
- **Day 5:** Documentation and rollout (3 hours)

### Week 3-4: Phase 3 - Production (Optional)
- **Week 3:** Redis setup and integration
- **Week 4:** Monitoring, optimization, and tuning

---

## Final Checklist

### Pre-Implementation
- [ ] Review this roadmap with team
- [ ] Get approval for Phase 1 implementation
- [ ] Set up performance monitoring
- [ ] Create test Excel files (100, 1000, 5000 rows)
- [ ] Set up local development environment

### Phase 1 Implementation
- [ ] Add chunked formatting endpoint
- [ ] Implement frontend chunk loading
- [ ] Add loading indicator UI
- [ ] Test with small/medium/large files
- [ ] Verify no performance regression
- [ ] Update API documentation

### Phase 2 Implementation (If Needed)
- [ ] Implement compression function
- [ ] Add frontend decompression
- [ ] Benchmark network savings
- [ ] Test on slow networks (throttled)
- [ ] Verify CPU overhead acceptable

### Phase 3 Implementation (If Needed)
- [ ] Set up Redis infrastructure
- [ ] Implement caching layer
- [ ] Add cache monitoring
- [ ] Load test with Redis
- [ ] Document Redis configuration

### Post-Implementation
- [ ] Monitor error rates (should be <1%)
- [ ] Monitor performance metrics
- [ ] Collect user feedback
- [ ] Document any issues
- [ ] Plan next optimizations

---

## Related Documents

1. **Main Research:** `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/EXCEL_FORMATTING_OPTIMIZATION_RESEARCH.md`
   - Comprehensive analysis of all approaches
   - Detailed implementation code examples
   - Performance benchmarks and comparisons

2. **Technical Appendix:** `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/EXCEL_FORMATTING_TECHNICAL_APPENDIX.md`
   - Advanced optimization techniques
   - Edge cases and gotchas
   - Alternative approaches (WebWorkers, binary encoding)

3. **Current Performance Report:** `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/EXCEL_PERFORMANCE_OPTIMIZATION.md`
   - Baseline performance metrics
   - Previous optimization efforts

---

## Quick Start (TL;DR)

**Want to start implementing today? Follow these steps:**

1. **Backend (30 minutes):**
   ```python
   # Add to excel_viewer.py
   @excel_viewer_bp.route('/api/document/<rid>/excel/formatting-chunk', methods=['GET'])
   def get_formatting_chunk(rid):
       # Copy implementation from roadmap above
       pass
   ```

2. **Frontend (1 hour):**
   ```typescript
   // Add to ExcelViewer.tsx
   const useFormattingChunks = (...) => {
       // Copy implementation from roadmap above
   };
   ```

3. **Test:**
   ```bash
   # Backend
   curl "http://localhost:5000/api/document/RID-07595/excel/formatting-chunk?session_id=test&sheet=Sheet1&start_row=100&end_row=200"

   # Frontend
   # Open Excel viewer, check console for chunk loading logs
   ```

4. **Monitor:**
   ```typescript
   console.log('Loaded chunks:', loadedChunks, '/', totalChunks);
   ```

**Expected result:** First 100 rows load instantly, rest load in background within 10-30s.

---

**Document Date:** 2025-10-07
**Author:** Senior Performance Engineer (AI Assistant)
**Status:** Implementation Roadmap - Ready to Execute
**Estimated Implementation Time:** 1-2 weeks (Phase 1 + 2), 3-4 weeks (all phases)
