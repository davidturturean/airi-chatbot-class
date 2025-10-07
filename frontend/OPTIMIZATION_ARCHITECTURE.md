# Excel Optimization Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AIRI CHATBOT UI                              │
│                                                                       │
│  ┌──────────────────┐                  ┌────────────────────┐      │
│  │  Chat Message    │                  │  Citation Badge    │      │
│  │                  │                  │    [RID-12345]     │      │
│  │ "According to    │                  │                    │      │
│  │  [RID-12345]..." │                  │  Hover me!         │      │
│  └──────────────────┘                  └────────┬───────────┘      │
│                                                  │                   │
│                                            HOVER EVENT               │
│                                                  ▼                   │
│                                    ┌─────────────────────────┐      │
│                                    │   HoverPreview.tsx      │      │
│                                    ├─────────────────────────┤      │
│                                    │ 1. Fetch preview        │      │
│                                    │ 2. Detect type: EXCEL   │      │
│                                    │ 3. Trigger prefetch()   │      │
│                                    └───────────┬─────────────┘      │
│                                                │                     │
│                                                │ (Background)        │
│                                                ▼                     │
│                                    ┌─────────────────────────┐      │
│                                    │  preview-cache.ts       │      │
│                                    ├─────────────────────────┤      │
│                                    │ prefetchExcelData(rid)  │      │
│                                    │                         │      │
│                                    │ • Check cache           │      │
│                                    │ • Track in-flight       │      │
│                                    │ • Fetch async           │      │
│                                    │ • Store result          │      │
│                                    └───────────┬─────────────┘      │
│                                                │                     │
└────────────────────────────────────────────────┼─────────────────────┘
                                                  │
                                                  │ HTTP GET
                                                  │ /api/document/RID-12345/excel
                                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND (Python/Flask)                       │
│                                                                       │
│                        ┌─────────────────────────┐                  │
│                        │  excel_viewer.py        │                  │
│                        ├─────────────────────────┤                  │
│                        │ get_excel_data(rid)     │                  │
│                        │                         │                  │
│                        │ 1. Generate cache_key   │                  │
│                        │    session:rid:mtime... │                  │
│                        │                         │                  │
│                        │ 2. Check excel_cache    │                  │
│                        │    TTLCache(100, 3600s) │                  │
│                        └───────────┬─────────────┘                  │
│                                    │                                 │
│                    ┌───────────────┴──────────────┐                 │
│                    │                               │                 │
│              CACHE HIT                       CACHE MISS              │
│                    │                               │                 │
│                    ▼                               ▼                 │
│         ┌──────────────────┐         ┌────────────────────────┐    │
│         │ Return cached    │         │ Parse Excel File       │    │
│         │ data (50ms)      │         │ pandas + openpyxl      │    │
│         │                  │         │                        │    │
│         │ Log: "Cache HIT" │         │ • Read sheets          │    │
│         └──────────────────┘         │ • Extract data         │    │
│                                      │ • Format cells         │    │
│                                      │ • Type inference       │    │
│                                      │                        │    │
│                                      │ (500-2000ms)           │    │
│                                      │                        │    │
│                                      │ Store in excel_cache   │    │
│                                      │ Log: "Cache MISS"      │    │
│                                      └────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ JSON Response
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React/TypeScript)                  │
│                                                                       │
│                        ┌─────────────────────────┐                  │
│                        │  preview-cache.ts       │                  │
│                        ├─────────────────────────┤                  │
│                        │ • Receives data         │                  │
│                        │ • Stores in cache       │                  │
│                        │ • Logs completion time  │                  │
│                        └─────────────────────────┘                  │
│                                                                       │
│                                                                       │
│                        [User clicks citation]                        │
│                                    │                                 │
│                                    ▼                                 │
│                      ┌─────────────────────────────┐                │
│                      │ EnhancedSlideoutPanel.tsx   │                │
│                      ├─────────────────────────────┤                │
│                      │ loadExcelData(rid)          │                │
│                      │                             │                │
│                      │ 1. Check cache FIRST        │                │
│                      │    cache.getExcelData(rid)  │                │
│                      └───────────┬─────────────────┘                │
│                                  │                                   │
│                  ┌───────────────┴───────────────┐                  │
│                  │                               │                  │
│            CACHE HIT                        CACHE MISS               │
│                  │                               │                  │
│                  ▼                               ▼                  │
│       ┌──────────────────┐         ┌────────────────────────┐     │
│       │ Instant Load!    │         │ Show loading spinner   │     │
│       │ (10-50ms)        │         │ Fetch from backend     │     │
│       │                  │         │ Wait for response      │     │
│       │ setExcelData()   │         │ (500-2000ms)           │     │
│       │ NO SPINNER       │         │                        │     │
│       │                  │         │ Then setExcelData()    │     │
│       └────────┬─────────┘         └────────────┬───────────┘     │
│                │                                 │                  │
│                └─────────────┬───────────────────┘                  │
│                              ▼                                       │
│                    ┌─────────────────────┐                          │
│                    │   ExcelViewer.tsx   │                          │
│                    ├─────────────────────┤                          │
│                    │ • Render data grid  │                          │
│                    │ • Apply formatting  │                          │
│                    │ • Enable sorting    │                          │
│                    │ • Enable filtering  │                          │
│                    └─────────────────────┘                          │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Timeline

### Scenario 1: First Load (No Hover)

```
Time    Action                                          Duration
────────────────────────────────────────────────────────────────
0ms     User clicks citation [RID-12345]
        ↓
10ms    EnhancedSlideoutPanel opens
        ↓
20ms    Check frontend cache → MISS
        ↓
30ms    Fetch /api/document/RID-12345/excel
        ↓
50ms    Backend receives request
        ↓
60ms    Generate cache key
        ↓
70ms    Check backend cache → MISS
        ↓
80ms    Start Excel parsing with pandas
        ↓↓↓
650ms   Parsing complete
        ↓
660ms   Store in backend cache
        ↓
670ms   Return JSON response
        ↓
720ms   Frontend receives response
        ↓
730ms   Store in frontend cache
        ↓
740ms   Render ExcelViewer
        ↓
750ms   ✅ DONE (Total: 750ms)
```

---

### Scenario 2: Hover Then Click (OPTIMIZED!)

```
Time    Action                                          Duration
────────────────────────────────────────────────────────────────
0ms     User hovers citation [RID-12345]
        ↓
300ms   HoverPreview opens (300ms delay)
        ↓
350ms   Fetch preview → Detect EXCEL type
        ↓
360ms   Trigger prefetchExcelData(rid) (BACKGROUND)
        ├─────────────────────────────────┐
        │ (Background prefetch)           │
        ↓                                 │
370ms   HoverPreview displays             │
        ↓                                 │
        [User reading preview...]         │
        │                                 │
        │                              450ms Backend parsing...
        │                                 ↓
2000ms  User clicks citation           1000ms Prefetch complete ✓
        ↓                                 │
2010ms  EnhancedSlideoutPanel opens       │
        ↓                                 │
2020ms  Check frontend cache → HIT! ✓─────┘
        ↓
2030ms  setExcelData(cached)
        ↓
2040ms  Render ExcelViewer
        ↓
2050ms  ✅ DONE (Total: 50ms from click!)
              (Felt instant, no spinner shown)
```

---

### Scenario 3: Repeat Load (Same Session)

```
Time    Action                                          Duration
────────────────────────────────────────────────────────────────
0ms     User clicks citation [RID-12345] (second time)
        ↓
10ms    EnhancedSlideoutPanel opens
        ↓
20ms    Check frontend cache → MISS (cleared earlier)
        ↓
30ms    Fetch /api/document/RID-12345/excel
        ↓
50ms    Backend receives request
        ↓
60ms    Generate cache key
        ↓
70ms    Check backend cache → HIT! ✓
        ↓
75ms    Return cached JSON
        ↓
90ms    Frontend receives response
        ↓
100ms   Store in frontend cache
        ↓
110ms   Render ExcelViewer
        ↓
120ms   ✅ DONE (Total: 120ms)
              (10x faster than first load!)
```

---

## Cache Architecture

### Frontend Cache (preview-cache.ts)

```
┌─────────────────────────────────────────────────────────┐
│              PreviewCacheManager                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  SESSION STORAGE:                                        │
│  ┌────────────────────────────────────────────────┐    │
│  │ previews: Map<string, CacheEntry>              │    │
│  │   Key: "{sessionId}-{rid}"                     │    │
│  │   Value: DocumentPreview                       │    │
│  │   TTL: 30 minutes                              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ excelData: Map<string, CacheEntry>             │    │
│  │   Key: "{sessionId}-{rid}"                     │    │
│  │   Value: ExcelDocumentData                     │    │
│  │   TTL: 30 minutes                              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ wordData: Map<string, CacheEntry>              │    │
│  │   Key: "{sessionId}-{rid}"                     │    │
│  │   Value: WordDocumentData                      │    │
│  │   TTL: 30 minutes                              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  IN-FLIGHT TRACKING (prevents duplicate fetches):       │
│  ┌────────────────────────────────────────────────┐    │
│  │ inFlightExcelRequests: Map<string, Promise>    │    │
│  │ inFlightWordRequests: Map<string, Promise>     │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  METHODS:                                                │
│  • getExcelData(rid)                                     │
│  • setExcelData(rid, data)                               │
│  • prefetchExcelData(rid) → Promise                      │
│  • prefetchWordData(rid) → Promise                       │
│  • clearAll()                                            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Backend Cache (excel_viewer.py)

```
┌─────────────────────────────────────────────────────────┐
│              TTLCache (cachetools)                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  CONFIGURATION:                                          │
│  • maxsize: 100 entries                                  │
│  • ttl: 3600 seconds (1 hour)                            │
│  • eviction: LRU + TTL                                   │
│                                                          │
│  CACHE KEY FORMAT:                                       │
│  "{session_id}:{rid}:{file_mtime}:{sheet}:{rows}:..."   │
│                                                          │
│  Example:                                                │
│  "sess-abc123:RID-12345:1728345600.0:Sheet1:1000:0"     │
│                                                          │
│  INVALIDATION:                                           │
│  • Automatic: TTL expires (1 hour)                       │
│  • Automatic: LRU eviction (when full)                   │
│  • Automatic: File mtime change (modified file)          │
│                                                          │
│  STORAGE:                                                │
│  ┌────────────────────────────────────────────────┐    │
│  │ Key: cache_key (string)                        │    │
│  │ Value: {                                       │    │
│  │   "sheets": [...],                             │    │
│  │   "active_sheet": "Sheet1",                    │    │
│  │   "rid": "RID-12345",                          │    │
│  │   "title": "Q3 Report.xlsx",                   │    │
│  │   "metadata": {...}                            │    │
│  │ }                                              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  STATISTICS:                                             │
│  ┌────────────────────────────────────────────────┐    │
│  │ cache_stats = {                                │    │
│  │   "hits": 125,                                 │    │
│  │   "misses": 25,                                │    │
│  │   "total_requests": 150                        │    │
│  │ }                                              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Component Interaction Diagram

```
┌───────────────┐
│  User Action  │
└───────┬───────┘
        │
        │ HOVER
        ▼
┌──────────────────────────────────────────────────┐
│         HoverPreview.tsx                         │
├──────────────────────────────────────────────────┤
│                                                  │
│  1. fetchPreview()                               │
│     └─> GET /api/document/{rid}/preview          │
│                                                  │
│  2. triggerBackgroundPrefetch()                  │
│     └─> if (type === 'excel'):                   │
│         previewCache.prefetchExcelData(rid)      │
│                                                  │
└──────────────────┬───────────────────────────────┘
                   │
                   │ (Non-blocking)
                   ▼
        ┌──────────────────────┐
        │  preview-cache.ts    │
        ├──────────────────────┤
        │                      │
        │  prefetchExcelData() │
        │  • Check cache       │
        │  • Check in-flight   │
        │  • Fetch if needed   │
        │  • Store result      │
        │                      │
        └──────────┬───────────┘
                   │
                   │ GET /api/document/{rid}/excel
                   ▼
        ┌──────────────────────┐
        │  excel_viewer.py     │
        ├──────────────────────┤
        │                      │
        │  get_excel_data()    │
        │  • Check cache       │
        │  • Parse if needed   │
        │  • Update stats      │
        │  • Return data       │
        │                      │
        └──────────────────────┘
                   │
                   │ (Data stored in caches)
                   │
        ┌──────────▼────────────────┐
        │                           │
        │  [User clicks citation]   │
        │                           │
        └──────────┬────────────────┘
                   │
                   │ CLICK
                   ▼
┌──────────────────────────────────────────────────┐
│      EnhancedSlideoutPanel.tsx                   │
├──────────────────────────────────────────────────┤
│                                                  │
│  1. determineDocumentType()                      │
│     └─> Check previewCache                       │
│                                                  │
│  2. loadExcelData()                              │
│     └─> Check previewCache.getExcelData()        │
│         ├─> HIT: setExcelData() (instant)        │
│         └─> MISS: fetch from backend             │
│                                                  │
└──────────────────┬───────────────────────────────┘
                   │
                   │ (Data ready)
                   ▼
        ┌──────────────────────┐
        │  ExcelViewer.tsx     │
        ├──────────────────────┤
        │                      │
        │  • Render DataGrid   │
        │  • Apply formatting  │
        │  • Enable sorting    │
        │  • Enable filtering  │
        │                      │
        └──────────────────────┘
```

---

## Performance Metrics Flow

```
┌─────────────────────────────────────────────────────────┐
│                   PERFORMANCE TRACKING                   │
└─────────────────────────────────────────────────────────┘

Frontend (Console Logs):
  ┌────────────────────────────────────────────────┐
  │ HoverPreview.tsx:                              │
  │ • "Excel prefetch completed in XXXms"          │
  │                                                │
  │ EnhancedSlideoutPanel.tsx:                     │
  │ • "Excel data loaded from cache in Xms"        │
  │ • "Excel data fetched in XXXms"                │
  └────────────────────────────────────────────────┘

Backend (Logger):
  ┌────────────────────────────────────────────────┐
  │ excel_viewer.py:                               │
  │ • "Excel cache HIT for {rid} (XXms)"           │
  │ • "Excel cache MISS for {rid}"                 │
  │ • "Excel parsed successfully: XXXms"           │
  │ • "Excel parsing exceeded target: XXXms"       │
  └────────────────────────────────────────────────┘

Metrics API (/api/excel/cache-stats):
  ┌────────────────────────────────────────────────┐
  │ {                                              │
  │   "hits": 125,                                 │
  │   "misses": 25,                                │
  │   "total_requests": 150,                       │
  │   "hit_rate_percent": 83.3,                    │
  │   "cache_size": 15,                            │
  │   "cache_max_size": 100,                       │
  │   "cache_ttl_seconds": 3600                    │
  │ }                                              │
  └────────────────────────────────────────────────┘
```

---

## Security & Isolation Model

```
┌─────────────────────────────────────────────────────────┐
│                   SESSION ISOLATION                      │
└─────────────────────────────────────────────────────────┘

Session A (User 1):
  ┌────────────────────────────────────────────────┐
  │ Frontend Cache:                                │
  │   Key: "sessA-RID-12345"                       │
  │   Data: [User A's Excel data]                  │
  └────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────┐
  │ Backend Cache:                                 │
  │   Key: "sessA:RID-12345:mtime:..."             │
  │   Data: [User A's Excel data]                  │
  └────────────────────────────────────────────────┘

Session B (User 2):
  ┌────────────────────────────────────────────────┐
  │ Frontend Cache:                                │
  │   Key: "sessB-RID-12345"                       │
  │   Data: [User B's Excel data]                  │
  └────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────┐
  │ Backend Cache:                                 │
  │   Key: "sessB:RID-12345:mtime:..."             │
  │   Data: [User B's Excel data]                  │
  └────────────────────────────────────────────────┘

✅ ISOLATION GUARANTEED:
   • Different cache keys per session
   • No cross-session data leakage
   • Session changes clear frontend cache
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-07
**Status**: Ready for Implementation
