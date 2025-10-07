# Excel Loading Performance Optimization - Testing Guide

## Implementation Summary

We've implemented a comprehensive two-phase optimization strategy to dramatically improve Excel spreadsheet loading performance:

### Phase A: Backend Caching (Server-Side)
- **Added `cachetools` dependency** for session-scoped TTL caching
- **Implemented TTLCache in `excel_viewer.py`**:
  - Cache key format: `{session_id}:{rid}:{file_mtime}:{sheet}:{max_rows}:{offset}`
  - TTL: 1 hour (3600 seconds)
  - Max size: 100 entries
  - Cache invalidation on file modification (via mtime)
  - Cache statistics tracking (hits, misses, hit rate)

### Phase B: Frontend Prefetching (Client-Side)
- **Added prefetch methods to `preview-cache.ts`**:
  - `prefetchExcelData(rid)` - Background Excel data fetching
  - `prefetchWordData(rid)` - Background Word data fetching
  - In-flight request tracking to prevent duplicate fetches
  - Detailed console logging for performance monitoring

- **Enhanced `HoverPreview.tsx`**:
  - Detects Excel/Word document types in hover preview
  - Triggers background prefetch automatically (non-blocking)
  - By the time user clicks, data is already cached

- **Optimized `EnhancedSlideoutPanel.tsx`**:
  - Checks cache FIRST before fetching
  - Only shows loading spinner on cache miss
  - Performance timing logs for cache hits/misses

## Performance Targets

| Scenario | Before | Target | Expected After |
|----------|--------|--------|----------------|
| **First Load** | Variable (500ms+) | <500ms | 500ms (unchanged) |
| **Cached Load (Same Session)** | Variable (500ms+) | <100ms | 50-100ms |
| **Pre-fetched Load (After Hover)** | Variable (500ms+) | <50ms | 10-50ms (instant) |

## Testing Instructions

### Prerequisites

1. **Install dependencies**:
   ```bash
   cd /Users/davidturturean/Documents/Codingprojects/airi-chatbot-class
   pip install -r requirements.txt
   ```

2. **Start the application**:
   ```bash
   # Start backend (adjust command as needed)
   python app.py

   # Start frontend (adjust command as needed)
   npm start
   ```

3. **Open browser DevTools**:
   - Open Chrome/Firefox DevTools (F12)
   - Navigate to **Console** tab (for logs)
   - Navigate to **Network** tab (for timing)

### Test 1: Baseline Performance (Before Optimization)

**Purpose**: Establish baseline metrics for comparison

**Steps**:
1. Clear all caches:
   - DevTools → Network → Right-click → Clear browser cache
   - Console → `previewCache.clearAll()`
2. Start a new chat session
3. Ask a question that returns Excel citations
4. Click an Excel citation `[RID-xxxxx]`
5. **Record timing from Network tab**:
   - Find request to `/api/document/{rid}/excel`
   - Note the **Time** column (e.g., "850ms")
6. **Record from Console**:
   - Look for "Excel parsing exceeded target" or "Excel parsed successfully"
   - Note the exact time (e.g., "Excel parsed successfully: 824.56ms")

**Expected Baseline**: 500ms - 2000ms depending on file size

### Test 2: Backend Cache Performance

**Purpose**: Verify backend TTL cache is working

**Steps**:
1. Clear browser cache (not server cache)
2. Click the same Excel citation again (within same session)
3. **Check Console for**:
   - "Excel cache HIT for {rid} (XX.XXms) - Hit rate: XX.X%"
4. **Check Network tab**:
   - Request should complete in <100ms
5. Click different Excel citations from the same file
6. **Verify cache hits** continue for same file

**Expected Result**:
- First click: "Excel cache MISS" + full parse time (500ms+)
- Second click: "Excel cache HIT" + <100ms
- Hit rate should increase with each subsequent request

### Test 3: Hover Prefetch Performance

**Purpose**: Verify hover-triggered background prefetch

**Steps**:
1. Clear all caches: `previewCache.clearAll()`
2. Start new chat session with Excel citations
3. **Hover** over an Excel citation for 500ms (DON'T CLICK YET)
4. **Watch Console for**:
   - "Hover preview detected Excel document, triggering background prefetch for {rid}"
   - "Starting Excel prefetch for {rid}..."
   - "Excel prefetch completed for {rid} in XXXms"
5. **Wait 2 seconds** for prefetch to complete
6. **Now click** the citation
7. **Check Console for**:
   - "Excel data loaded from cache in X.XXms (instant load)"

**Expected Result**:
- Hover triggers background prefetch
- Prefetch completes in background (500ms - 2000ms)
- Click loads instantly from cache (<50ms)
- NO loading spinner shown (data already cached)

### Test 4: Cache Statistics

**Purpose**: Monitor cache performance metrics

**Steps**:
1. Clear caches and start new session
2. Click 5 different Excel citations (mix of different files)
3. Click each citation a second time (should hit cache)
4. Open new browser tab and visit:
   ```
   http://localhost:5000/api/excel/cache-stats
   ```
5. **Verify response**:
   ```json
   {
     "hits": 5,
     "misses": 5,
     "total_requests": 10,
     "hit_rate_percent": 50.0,
     "cache_size": 5,
     "cache_max_size": 100,
     "cache_ttl_seconds": 3600
   }
   ```

**Expected Result**:
- Hit rate should be ~50% (first click = miss, second = hit)
- Cache size should equal number of unique documents
- Total requests should equal all clicks

### Test 5: Cache Invalidation on File Change

**Purpose**: Verify cache invalidates when file is modified

**Steps**:
1. Click an Excel citation, note the data
2. **Modify the source Excel file** (change any cell)
3. Click the same citation again
4. **Check Console for**:
   - "Excel cache MISS" (not HIT)
   - New parse time logged
5. **Verify** updated data is shown in viewer

**Expected Result**:
- Cache miss on second click (file mtime changed)
- Fresh data loaded from modified file

### Test 6: Session Isolation

**Purpose**: Verify caches are session-scoped

**Steps**:
1. Session A: Click Excel citation (cache miss)
2. Session A: Click same citation again (cache HIT)
3. **Start new session** (new chat or incognito window)
4. Session B: Click same citation
5. **Check Console**:
   - Should see "Excel cache MISS" (different session)

**Expected Result**:
- Caches are isolated per session
- Different sessions don't share cached data

### Test 7: Performance Under Load

**Purpose**: Verify performance with multiple Excel documents

**Steps**:
1. Clear all caches
2. Ask question that returns 10+ Excel citations
3. **Hover over each citation** (trigger prefetch)
4. **Wait 5 seconds** for all prefetches to complete
5. **Click each citation** in sequence
6. **Monitor Console for**:
   - How many load from cache vs fetch
   - Average load time for cached items

**Expected Result**:
- Most citations load from cache (<50ms)
- No performance degradation with multiple prefetches
- In-flight request tracking prevents duplicate fetches

### Test 8: Error Handling

**Purpose**: Verify graceful failure on prefetch errors

**Steps**:
1. Hover over Excel citation with **invalid/missing file**
2. **Check Console for**:
   - "Excel prefetch failed (non-critical): ..."
3. **Click the citation**
4. **Verify**:
   - Error is shown in slideout panel
   - Hover preview wasn't affected by prefetch failure

**Expected Result**:
- Prefetch errors are logged but don't break UI
- User still sees error message when clicking
- Hover preview shows successfully regardless

## Performance Benchmarks

Record your results in this table:

| Test Scenario | Time (ms) | Notes |
|---------------|-----------|-------|
| Baseline (first load) | ________ | Before optimization |
| Backend cache hit | ________ | Same session, repeat click |
| Hover prefetch → click | ________ | After 2s hover wait |
| Cache stats hit rate | ________ | After 10 mixed requests |

## Success Criteria

- [ ] **First load**: <500ms (same as baseline)
- [ ] **Cached load**: <100ms (10x improvement)
- [ ] **Pre-fetched load**: <50ms (feels instant, no spinner)
- [ ] **Cache hit rate**: >50% after 20 mixed requests
- [ ] **Console logs**: Show cache HIT/MISS clearly
- [ ] **No errors**: Prefetch failures don't break UI
- [ ] **Session isolation**: Different sessions have separate caches
- [ ] **File invalidation**: Modified files trigger cache miss

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'cachetools'"
**Solution**:
```bash
pip install cachetools>=5.3.0
```

### Issue: Cache never hits (always MISS)
**Check**:
1. Session ID is consistent across requests
2. File path and mtime are stable
3. Check logs for cache key generation errors

### Issue: Prefetch doesn't trigger on hover
**Check**:
1. Hover delay is at least 300ms (default)
2. Console shows "Hover preview detected Excel document"
3. Preview type is correctly set to 'excel'

### Issue: Data loads but spinner still shows
**Check**:
1. `loadExcelData()` checks cache BEFORE setting loading state
2. Console shows "loaded from cache" message
3. React state is updating correctly

## Console Log Reference

### Expected Log Sequence (Hover → Click):

```
1. [HoverPreview] Hover preview detected Excel document, triggering background prefetch for RID-12345
2. [PreviewCache] Starting Excel prefetch for RID-12345...
3. [Backend] Excel cache MISS for RID-12345 - Parsing file...
4. [Backend] Excel parsed successfully: 650.23ms for RID-12345
5. [PreviewCache] Excel prefetch completed for RID-12345 in 652.45ms
---
6. [User clicks citation]
---
7. [EnhancedSlideoutPanel] Excel data loaded from cache in 2.15ms (instant load)
8. [Backend] Excel cache HIT for RID-12345 (45.67ms) - Hit rate: 75.0%
```

### Expected Log Sequence (Direct Click, No Hover):

```
1. [User clicks citation]
2. [EnhancedSlideoutPanel] Excel data not cached, fetching from server...
3. [Backend] Excel cache MISS for RID-12345 - Parsing file...
4. [Backend] Excel parsed successfully: 650.23ms for RID-12345
5. [EnhancedSlideoutPanel] Excel data fetched in 652.45ms
```

## Monitoring Dashboard

Visit `http://localhost:5000/api/excel/cache-stats` to see:

```json
{
  "hits": 125,              // Requests served from cache
  "misses": 25,             // Requests that parsed file
  "total_requests": 150,    // Total Excel requests
  "hit_rate_percent": 83.3, // Cache efficiency
  "cache_size": 15,         // Current cached documents
  "cache_max_size": 100,    // Max cache capacity
  "cache_ttl_seconds": 3600 // Cache expiry time
}
```

**Healthy metrics**:
- Hit rate: 60-90% (after warmup period)
- Cache size: <100 (below limit)
- Misses should decrease over time as cache warms up

## Reporting Results

After completing all tests, report:

1. **Baseline performance**: First load time before optimization
2. **Cache hit performance**: Repeat load time after optimization
3. **Prefetch performance**: Load time after hover prefetch
4. **Cache hit rate**: Percentage from `/api/excel/cache-stats`
5. **Issues encountered**: Any errors or unexpected behavior
6. **Browser/environment**: Chrome version, OS, network conditions

Example report:
```
✅ Excel Optimization Testing - PASSED

Baseline (first load): 850ms
Cached load: 52ms (16x improvement)
Pre-fetched load: 15ms (57x improvement, instant)
Cache hit rate: 78.5% (after 40 requests)

Environment: Chrome 120, macOS 14.2, localhost
Issues: None
```

## Next Steps

After successful testing:

1. **Monitor production metrics**: Track cache hit rates in real usage
2. **Tune cache size**: Adjust `maxsize=100` if needed based on usage patterns
3. **Tune TTL**: Adjust `ttl=3600` (1 hour) if documents update more/less frequently
4. **Add cache warming**: Pre-load common documents on session start
5. **Add compression**: Consider gzip compression for cached responses
6. **Add metrics dashboard**: Build UI to visualize cache statistics

## Files Modified

**Backend**:
- `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/requirements.txt` - Added cachetools
- `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/src/api/routes/excel_viewer.py` - TTL cache implementation

**Frontend**:
- `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/frontend/src/utils/preview-cache.ts` - Prefetch methods
- `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/frontend/src/components/preview/HoverPreview.tsx` - Prefetch trigger
- `/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/frontend/src/components/preview/EnhancedSlideoutPanel.tsx` - Cache-first loading

---

**Document Version**: 1.0
**Last Updated**: 2025-10-07
**Status**: Ready for Testing
