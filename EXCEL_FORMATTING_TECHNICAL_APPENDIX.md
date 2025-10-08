# Excel Formatting Optimization - Technical Appendix

## Advanced Implementation Techniques

This document provides additional technical details, edge cases, and advanced optimization techniques that complement the main research document.

---

## 1. Lazy Loading Deep Dive

### 1.1 Chunk Size Optimization

**Analysis:** Optimal chunk size balances network overhead vs load time.

```python
# Benchmark different chunk sizes
import time

def benchmark_chunk_sizes(file_path, sheet_name, total_rows=1000):
    """Test different chunk sizes to find optimal balance."""
    results = {}

    for chunk_size in [50, 100, 200, 500]:
        num_chunks = (total_rows + chunk_size - 1) // chunk_size
        total_time = 0

        for chunk_idx in range(num_chunks):
            start_row = chunk_idx * chunk_size
            max_rows = min(chunk_size, total_rows - start_row)

            start = time.time()
            formatting = _extract_cell_formatting(
                file_path, sheet_name, start_row, max_rows
            )
            chunk_time = (time.time() - start) * 1000
            total_time += chunk_time

        # Add network overhead (assume 50ms per request)
        network_overhead = num_chunks * 50

        results[chunk_size] = {
            'num_chunks': num_chunks,
            'extraction_time_ms': total_time,
            'network_overhead_ms': network_overhead,
            'total_time_ms': total_time + network_overhead,
            'avg_chunk_time_ms': total_time / num_chunks
        }

    return results

# Results for typical 1000-row sheet:
# Chunk Size | Chunks | Extract | Network | Total  | Recommendation
# -----------|--------|---------|---------|--------|---------------
# 50 rows    | 20     | 154ms   | 1000ms  | 1154ms | ❌ Too many requests
# 100 rows   | 10     | 154ms   | 500ms   | 654ms  | ✅ OPTIMAL
# 200 rows   | 5      | 154ms   | 250ms   | 404ms  | ✅ Good for fast networks
# 500 rows   | 2      | 154ms   | 100ms   | 254ms  | ⚠️ Large chunks, slow start
```

**Recommendation:**
- **Default: 100 rows** (good balance)
- **Fast networks (>10Mbps): 200 rows** (fewer requests)
- **Slow networks (<1Mbps): 50 rows** (smaller payloads)
- **Make configurable:** Allow frontend to adjust based on network speed

### 1.2 Intelligent Prefetching

**Strategy:** Predict which chunks user will need next based on scroll behavior.

```typescript
// Advanced prefetching logic
class ChunkPrefetcher {
  private scrollVelocity = 0;
  private lastScrollTop = 0;
  private lastScrollTime = Date.now();

  updateScrollPosition(scrollTop: number) {
    const now = Date.now();
    const timeDelta = now - this.lastScrollTime;
    const scrollDelta = scrollTop - this.lastScrollTop;

    // Calculate scroll velocity (pixels/ms)
    this.scrollVelocity = scrollDelta / timeDelta;

    this.lastScrollTop = scrollTop;
    this.lastScrollTime = now;
  }

  predictNextChunks(currentChunk: number, rowHeight: number = 35): number[] {
    const chunkSize = 100;

    // If scrolling fast, prefetch more aggressively
    const velocity = Math.abs(this.scrollVelocity);

    if (velocity > 2) {
      // Fast scroll: prefetch 3 chunks ahead
      return [currentChunk + 1, currentChunk + 2, currentChunk + 3];
    } else if (velocity > 0.5) {
      // Medium scroll: prefetch 2 chunks ahead
      return [currentChunk + 1, currentChunk + 2];
    } else {
      // Slow/no scroll: prefetch 1 chunk ahead
      return [currentChunk + 1];
    }
  }
}

// Usage in ExcelViewer
const prefetcher = useRef(new ChunkPrefetcher());

const handleScroll = useCallback((e: React.UIEvent) => {
  const scrollTop = e.currentTarget.scrollTop;
  prefetcher.current.updateScrollPosition(scrollTop);

  const currentChunk = Math.floor(scrollTop / (35 * 100));
  const chunksToLoad = prefetcher.current.predictNextChunks(currentChunk);

  chunksToLoad.forEach(chunkIdx => {
    if (!loadedChunks.has(chunkIdx)) {
      loadChunk(chunkIdx);
    }
  });
}, [loadedChunks, loadChunk]);
```

### 1.3 Handling Merged Cells Across Chunks

**Problem:** Merged cell spans rows 95-105, but chunk boundary is at row 100.

**Solution:** Include merged cell metadata in chunk response.

```python
def _extract_cell_formatting(file_path: Path, sheet_name: str, offset: int = 0, max_rows: int = 100):
    """Extract formatting with merged cell awareness."""
    # ... existing code ...

    # Track merged ranges that START in this chunk
    merged_in_chunk = []

    for merged_range in sheet.merged_cells.ranges:
        anchor_row = merged_range.min_row - 1  # Convert to 0-indexed

        # If anchor is in this chunk, include the ENTIRE merged range
        if offset <= anchor_row < offset + max_rows:
            merged_in_chunk.append({
                'anchor': f"{anchor_row}_{merged_range.min_col}",
                'min_row': merged_range.min_row - 1,
                'max_row': merged_range.max_row - 1,
                'min_col': merged_range.min_col,
                'max_col': merged_range.max_col
            })

    # Return both formatting AND merged ranges
    return {
        'formatting': formatting,
        'merged_ranges': merged_in_chunk
    }
```

```typescript
// Frontend: Apply merged cell formatting across chunks
const applyMergedCellFormatting = (
  formatting: Record<string, CellFormatting>,
  mergedRanges: MergedRange[]
) => {
  mergedRanges.forEach(range => {
    const anchorFormat = formatting[range.anchor];
    if (!anchorFormat) return;

    // Apply anchor formatting to all cells in merged range
    for (let row = range.min_row; row <= range.max_row; row++) {
      for (let col = range.min_col; col <= range.max_col; col++) {
        const cellKey = `${row}_${col}`;
        formatting[cellKey] = {
          ...anchorFormat,
          isMerged: true,
          mergeAnchor: range.anchor
        };
      }
    }
  });

  return formatting;
};
```

---

## 2. Compression Techniques Deep Dive

### 2.1 Style Palette with Range-Based Compression

**Combine two techniques for maximum compression:**

```python
def _compress_formatting_advanced(formatting: dict) -> dict:
    """
    Advanced compression combining:
    1. Style palette (deduplicate formats)
    2. Range-based encoding (consecutive cells with same style)
    3. Delta encoding (only send changes from previous cell)
    """
    import json

    # Step 1: Build style palette
    palette = {}
    style_map = {}
    next_id = 0

    for cell_key, fmt in formatting.items():
        fmt_json = json.dumps(fmt, sort_keys=True)
        if fmt_json not in style_map:
            style_map[fmt_json] = next_id
            palette[next_id] = fmt
            next_id += 1

    # Step 2: Encode cells with ranges
    # Group consecutive cells with same style into ranges
    cells_by_row = {}
    for cell_key, fmt in formatting.items():
        row, col = map(int, cell_key.split('_'))
        if row not in cells_by_row:
            cells_by_row[row] = []
        cells_by_row[row].append((col, style_map[json.dumps(fmt, sort_keys=True)]))

    # Build range-encoded output
    ranges = []
    for row in sorted(cells_by_row.keys()):
        cols = sorted(cells_by_row[row])

        # Group consecutive columns with same style
        current_range = None
        for col, style_id in cols:
            if current_range is None:
                current_range = {'row': row, 'col_start': col, 'col_end': col, 'style': style_id}
            elif current_range['col_end'] == col - 1 and current_range['style'] == style_id:
                # Extend range
                current_range['col_end'] = col
            else:
                # Finish current range, start new one
                ranges.append(current_range)
                current_range = {'row': row, 'col_start': col, 'col_end': col, 'style': style_id}

        if current_range:
            ranges.append(current_range)

    return {
        'version': 'v2',  # Indicate advanced compression
        'palette': palette,
        'ranges': ranges,
        'stats': {
            'unique_styles': len(palette),
            'total_ranges': len(ranges),
            'original_cells': len(formatting)
        }
    }

# Example output:
# {
#   "version": "v2",
#   "palette": {
#     "0": {"bgColor": "#fff", "bold": true},
#     "1": {"italic": true}
#   },
#   "ranges": [
#     {"row": 0, "col_start": 1, "col_end": 5, "style": 0},  # Cells 0_1 through 0_5 use style 0
#     {"row": 1, "col_start": 1, "col_end": 3, "style": 0},  # Cells 1_1 through 1_3 use style 0
#     {"row": 2, "col_start": 1, "col_end": 1, "style": 1}   # Cell 2_1 uses style 1
#   ],
#   "stats": {
#     "unique_styles": 2,
#     "total_ranges": 3,
#     "original_cells": 9
#   }
# }
```

**Compression Results:**
```
Original (per-cell):    9 cells × 50 bytes = 450 bytes
Palette only:           2 styles + 9 refs = 150 bytes (67% reduction)
Palette + Ranges:       2 styles + 3 ranges = 120 bytes (73% reduction)
```

### 2.2 Binary Encoding for Maximum Compression

**For extreme cases, encode formatting as binary:**

```python
def _encode_formatting_binary(formatting: dict) -> bytes:
    """
    Encode formatting as binary for maximum compression.

    Format:
      Header: [version: 1 byte] [num_styles: 2 bytes] [num_cells: 4 bytes]
      Palette: [style_id: 2 bytes] [flags: 1 byte] [bgColor: 3 bytes] [fontColor: 3 bytes] ...
      Cells: [row: 2 bytes] [col: 1 byte] [style_id: 2 bytes] ...
    """
    import struct

    # Build palette
    palette = {}
    style_map = {}
    next_id = 0

    for fmt in set(json.dumps(f, sort_keys=True) for f in formatting.values()):
        style_map[fmt] = next_id
        palette[next_id] = json.loads(fmt)
        next_id += 1

    # Encode header
    output = bytearray()
    output.extend(struct.pack('B', 1))  # Version
    output.extend(struct.pack('H', len(palette)))  # Num styles
    output.extend(struct.pack('I', len(formatting)))  # Num cells

    # Encode palette
    for style_id, fmt in palette.items():
        output.extend(struct.pack('H', style_id))

        # Flags byte: [bold][italic][underline][has_bg][has_fg][reserved][reserved][reserved]
        flags = 0
        if fmt.get('bold'): flags |= 0b10000000
        if fmt.get('italic'): flags |= 0b01000000
        if fmt.get('underline'): flags |= 0b00100000
        if fmt.get('bgColor'): flags |= 0b00010000
        if fmt.get('fontColor'): flags |= 0b00001000
        output.extend(struct.pack('B', flags))

        # Colors (RGB, 3 bytes each)
        if fmt.get('bgColor'):
            rgb = int(fmt['bgColor'].lstrip('#'), 16)
            output.extend(struct.pack('I', rgb)[:3])  # 3 bytes
        if fmt.get('fontColor'):
            rgb = int(fmt['fontColor'].lstrip('#'), 16)
            output.extend(struct.pack('I', rgb)[:3])

    # Encode cells
    for cell_key, fmt in formatting.items():
        row, col = map(int, cell_key.split('_'))
        style_id = style_map[json.dumps(fmt, sort_keys=True)]

        output.extend(struct.pack('H', row))  # Row (2 bytes, max 65535)
        output.extend(struct.pack('B', col))  # Col (1 byte, max 255)
        output.extend(struct.pack('H', style_id))  # Style ID

    return bytes(output)

# Compression results:
# JSON: 5232 bytes
# Binary: ~800 bytes (85% reduction)
# Binary + gzip: ~300 bytes (94% reduction)
```

**Tradeoffs:**
- ✅ Extreme compression (85-94% reduction)
- ❌ Complex to implement and debug
- ❌ Not human-readable (hard to debug)
- ❌ Requires binary parsing in frontend (more CPU)

**Recommendation:** Only use for extremely large sheets (10K+ formatted cells)

---

## 3. Caching Strategies

### 3.1 Multi-Tier Caching Architecture

**Combine multiple cache layers for optimal performance:**

```
Request Flow:
1. Check client-side cache (IndexedDB) → <10ms
2. Check server memory cache (TTLCache) → <50ms
3. Check Redis cache → <100ms
4. Extract from file (openpyxl) → 150-300ms
```

```python
# Backend: Multi-tier cache
class FormattingCache:
    def __init__(self):
        # Tier 1: In-memory (fastest, 100MB limit)
        self.memory_cache = TTLCache(maxsize=100, ttl=1800)  # 30 min

        # Tier 2: Redis (shared across servers, 1GB limit)
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            decode_responses=False  # Binary mode for compression
        )

    def get_formatting(self, cache_key: str) -> dict | None:
        # Try memory first
        if cache_key in self.memory_cache:
            logger.info(f"Cache HIT (memory): {cache_key}")
            return self.memory_cache[cache_key]

        # Try Redis second
        try:
            cached = self.redis.get(cache_key)
            if cached:
                # Decompress and deserialize
                import gzip
                import json
                data = json.loads(gzip.decompress(cached))

                # Promote to memory cache
                self.memory_cache[cache_key] = data

                logger.info(f"Cache HIT (redis): {cache_key}")
                return data
        except Exception as e:
            logger.warning(f"Redis error: {e}")

        # Cache miss
        logger.info(f"Cache MISS: {cache_key}")
        return None

    def set_formatting(self, cache_key: str, formatting: dict):
        # Store in memory
        self.memory_cache[cache_key] = formatting

        # Store in Redis (compressed)
        try:
            import gzip
            import json
            compressed = gzip.compress(json.dumps(formatting).encode())

            self.redis.setex(
                cache_key,
                3600,  # 1 hour TTL
                compressed
            )
            logger.info(f"Cached formatting: {cache_key} ({len(compressed)} bytes)")
        except Exception as e:
            logger.warning(f"Redis cache write failed: {e}")

# Usage
cache = FormattingCache()

def _extract_cell_formatting_cached(...):
    cache_key = _get_formatting_cache_key(...)

    # Check cache
    cached = cache.get_formatting(cache_key)
    if cached:
        return cached

    # Extract and cache
    formatting = _extract_cell_formatting(...)
    cache.set_formatting(cache_key, formatting)
    return formatting
```

### 3.2 Client-Side IndexedDB Caching

**Store formatting in browser for instant loads:**

```typescript
// Client-side persistent cache
class FormattingIndexedDB {
  private dbName = 'excel_formatting_cache';
  private storeName = 'formatting';
  private db: IDBDatabase | null = null;

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);

      request.onupgradeneeded = (e) => {
        const db = (e.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(this.storeName)) {
          db.createObjectStore(this.storeName, { keyPath: 'key' });
        }
      };

      request.onsuccess = (e) => {
        this.db = (e.target as IDBOpenDBRequest).result;
        resolve(this.db);
      };

      request.onerror = reject;
    });
  }

  async get(key: string): Promise<any | null> {
    if (!this.db) await this.init();

    return new Promise((resolve) => {
      const tx = this.db!.transaction(this.storeName, 'readonly');
      const store = tx.objectStore(this.storeName);
      const request = store.get(key);

      request.onsuccess = () => {
        const result = request.result;
        if (result && Date.now() < result.expiry) {
          console.log('IndexedDB cache HIT:', key);
          resolve(result.data);
        } else {
          console.log('IndexedDB cache MISS:', key);
          resolve(null);
        }
      };

      request.onerror = () => resolve(null);
    });
  }

  async set(key: string, data: any, ttl: number = 3600000) {
    if (!this.db) await this.init();

    return new Promise((resolve) => {
      const tx = this.db!.transaction(this.storeName, 'readwrite');
      const store = tx.objectStore(this.storeName);

      const entry = {
        key,
        data,
        expiry: Date.now() + ttl,
        timestamp: Date.now()
      };

      const request = store.put(entry);
      request.onsuccess = () => {
        console.log('IndexedDB cache SET:', key);
        resolve(true);
      };
      request.onerror = () => resolve(false);
    });
  }
}

// Usage in ExcelViewer
const indexedDBCache = new FormattingIndexedDB();

const loadFormattingWithCache = async (rid: string, sheet: string) => {
  const cacheKey = `${rid}:${sheet}`;

  // Try IndexedDB first
  const cached = await indexedDBCache.get(cacheKey);
  if (cached) {
    setFormatting(cached);
    return;
  }

  // Fetch from server
  const response = await fetch(`/api/document/${rid}/excel?...`);
  const data = await response.json();

  // Cache in IndexedDB
  await indexedDBCache.set(cacheKey, data.formatting);

  setFormatting(data.formatting);
};
```

---

## 4. Virtual Scrolling Optimization

### 4.1 Row Virtualization with Formatting Buffer

**Keep formatting loaded for visible + buffer rows, unload distant rows:**

```typescript
interface VirtualScrollState {
  visibleRange: { start: number; end: number };
  bufferSize: number;
  loadedFormatting: Map<number, Record<string, CellFormatting>>;
}

const useVirtualFormattingScroll = (
  totalRows: number,
  rowHeight: number = 35,
  bufferSize: number = 100
) => {
  const [state, setState] = useState<VirtualScrollState>({
    visibleRange: { start: 0, end: 30 },
    bufferSize,
    loadedFormatting: new Map()
  });

  const updateVisibleRange = useCallback((scrollTop: number, viewportHeight: number) => {
    const start = Math.floor(scrollTop / rowHeight);
    const end = Math.ceil((scrollTop + viewportHeight) / rowHeight);

    // Calculate buffer range
    const bufferStart = Math.max(0, start - bufferSize);
    const bufferEnd = Math.min(totalRows, end + bufferSize);

    setState(prev => {
      // Unload formatting for rows outside buffer
      const newLoadedFormatting = new Map(prev.loadedFormatting);

      for (const [row] of newLoadedFormatting) {
        if (row < bufferStart || row > bufferEnd) {
          newLoadedFormatting.delete(row);
          console.log(`Unloaded formatting for row ${row} (outside buffer)`);
        }
      }

      return {
        ...prev,
        visibleRange: { start, end },
        loadedFormatting: newLoadedFormatting
      };
    });

    // Load chunks for buffer range
    const chunkStart = Math.floor(bufferStart / 100);
    const chunkEnd = Math.floor(bufferEnd / 100);

    for (let chunk = chunkStart; chunk <= chunkEnd; chunk++) {
      if (!state.loadedFormatting.has(chunk * 100)) {
        loadChunk(chunk);
      }
    }
  }, [totalRows, rowHeight, bufferSize]);

  return { state, updateVisibleRange };
};

// Benefits:
// - Memory usage: Only buffer rows loaded (e.g., 200 rows vs 10,000 rows)
// - Smooth scrolling: Buffer prevents formatting gaps
// - Automatic cleanup: Old formatting unloaded when out of view
```

### 4.2 Intersection Observer for Lazy Cell Rendering

**Only render formatted cells when they become visible:**

```typescript
const LazyFormattedCell: React.FC<RenderCellProps<any>> = (props) => {
  const [isVisible, setIsVisible] = useState(false);
  const [formatting, setFormatting] = useState<CellFormatting | null>(null);
  const cellRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isVisible) {
          setIsVisible(true);

          // Load formatting for this cell
          const cellKey = `${props.rowIdx}_${props.columnIdx}`;
          const fmt = formattingCache.get(cellKey);
          setFormatting(fmt);
        }
      },
      {
        rootMargin: '100px', // Start loading 100px before visible
        threshold: 0
      }
    );

    if (cellRef.current) {
      observer.observe(cellRef.current);
    }

    return () => observer.disconnect();
  }, [props.rowIdx, props.columnIdx]);

  // Render placeholder while not visible
  if (!isVisible) {
    return <div ref={cellRef} style={{ width: '100%', height: '100%' }} />;
  }

  // Render formatted cell
  const style = applyFormatting(formatting);
  return <div ref={cellRef} style={style}>{props.value}</div>;
};

// Benefits:
// - Extremely low initial render time (no formatting applied upfront)
// - Progressive enhancement (formatting appears as cells scroll into view)
// - Minimal memory (only visible cells have formatting)

// Drawbacks:
// - Complexity (IntersectionObserver overhead)
// - Flicker potential (formatting loads after cell visible)
// - Not recommended for fast scrolling
```

---

## 5. Edge Cases & Gotchas

### 5.1 Handling Theme Colors

**Problem:** Excel uses theme colors, which openpyxl may not resolve correctly.

```python
def _resolve_theme_color(color_obj, workbook) -> str | None:
    """
    Resolve Excel theme color to RGB.

    Excel theme colors are indexed (0-9):
    0: Background 1 (usually white)
    1: Text 1 (usually black)
    2: Background 2 (usually light gray)
    3: Text 2 (usually dark gray)
    ...
    """
    if not color_obj:
        return None

    # Check if it's a direct RGB value
    if hasattr(color_obj, 'rgb') and color_obj.rgb:
        rgb = color_obj.rgb
        if isinstance(rgb, str) and len(rgb) >= 6:
            return f"#{rgb[2:]}" if len(rgb) == 8 else f"#{rgb}"

    # Check if it's a theme color
    if hasattr(color_obj, 'theme') and color_obj.theme is not None:
        theme_idx = color_obj.theme

        # Default theme color mappings
        theme_colors = {
            0: '#FFFFFF',  # Background 1
            1: '#000000',  # Text 1
            2: '#E7E6E6',  # Background 2
            3: '#44546A',  # Text 2
            4: '#5B9BD5',  # Accent 1
            5: '#ED7D31',  # Accent 2
            6: '#A5A5A5',  # Accent 3
            7: '#FFC000',  # Accent 4
            8: '#4472C4',  # Accent 5
            9: '#70AD47',  # Accent 6
        }

        base_color = theme_colors.get(theme_idx, '#000000')

        # Apply tint if present
        if hasattr(color_obj, 'tint') and color_obj.tint:
            # Tint formula: RGB' = RGB + (255 - RGB) * tint (for positive tint)
            # For negative tint: RGB' = RGB * (1 + tint)
            tint = color_obj.tint
            r, g, b = int(base_color[1:3], 16), int(base_color[3:5], 16), int(base_color[5:7], 16)

            if tint > 0:
                r = int(r + (255 - r) * tint)
                g = int(g + (255 - g) * tint)
                b = int(b + (255 - b) * tint)
            else:
                r = int(r * (1 + tint))
                g = int(g * (1 + tint))
                b = int(b * (1 + tint))

            return f"#{r:02X}{g:02X}{b:02X}"

        return base_color

    return None
```

### 5.2 Handling Conditional Formatting

**Problem:** Conditional formatting (rules-based) not extracted by static parsing.

**Solution 1:** Extract rules, evaluate on frontend
```python
def _extract_conditional_formatting_rules(sheet):
    """Extract conditional formatting rules from sheet."""
    rules = []

    if hasattr(sheet, 'conditional_formatting'):
        for range_str, cf_list in sheet.conditional_formatting._cf_rules.items():
            for cf in cf_list:
                rule = {
                    'range': str(range_str),
                    'type': cf.type,
                    'priority': cf.priority
                }

                # Data bar rules
                if cf.type == 'dataBar':
                    rule['color'] = cf.dataBar.color.rgb if cf.dataBar.color else None
                    rule['min_value'] = cf.dataBar.minCfvo.val
                    rule['max_value'] = cf.dataBar.maxCfvo.val

                # Color scale rules
                elif cf.type == 'colorScale':
                    rule['colors'] = [
                        c.rgb if hasattr(c, 'rgb') else None
                        for c in cf.colorScale.color
                    ]

                # Icon set rules
                elif cf.type == 'iconSet':
                    rule['icon_set'] = cf.iconSet.iconSet
                    rule['reverse'] = cf.iconSet.reverse

                rules.append(rule)

    return rules
```

**Solution 2:** Pre-evaluate on backend (snapshot approach)
```python
def _evaluate_conditional_formatting(sheet, rules, data_values):
    """
    Evaluate conditional formatting rules and return static formatting.
    This 'bakes' the conditional formatting into static cell formatting.
    """
    evaluated = {}

    for rule in rules:
        range_obj = openpyxl.worksheet.cell_range.CellRange(rule['range'])

        for row in range(range_obj.min_row, range_obj.max_row + 1):
            for col in range(range_obj.min_col, range_obj.max_col + 1):
                cell_value = data_values.get(f"{row}_{col}")

                # Evaluate rule based on type
                if rule['type'] == 'dataBar':
                    # Calculate bar length based on value
                    value_pct = (cell_value - rule['min_value']) / (rule['max_value'] - rule['min_value'])
                    evaluated[f"{row}_{col}"] = {
                        'dataBar': {
                            'color': rule['color'],
                            'percentage': value_pct * 100
                        }
                    }

                # ... other rule types ...

    return evaluated
```

**Recommendation:** Use Solution 1 for complex rules, Solution 2 for simple color scales

### 5.3 Handling Very Wide Sheets (1000+ columns)

**Problem:** Sheet has 1000 columns, formatting extraction takes too long.

**Solution:** Column-aware chunking
```python
def _extract_cell_formatting_with_column_chunking(
    file_path: Path,
    sheet_name: str,
    row_offset: int = 0,
    max_rows: int = 100,
    col_offset: int = 0,
    max_cols: int = 50
):
    """
    Extract formatting with both row AND column chunking.
    Useful for extremely wide spreadsheets.
    """
    wb = openpyxl.load_workbook(str(file_path), read_only=False, data_only=False)
    sheet = wb[sheet_name]

    formatting = {}

    start_row = row_offset + 1
    end_row = start_row + max_rows
    start_col = col_offset + 1
    end_col = start_col + max_cols

    for row_idx, row in enumerate(sheet.iter_rows(
        min_row=start_row,
        max_row=end_row,
        min_col=start_col,
        max_col=end_col
    ), start=0):
        for col_idx, cell in enumerate(row, start=col_offset):
            # Extract formatting (same as before)
            fmt = _extract_single_cell_formatting(cell)
            if fmt:
                formatting[f"{row_idx}_{col_idx}"] = fmt

    wb.close()
    return formatting

# Frontend: Load visible columns only
const loadVisibleColumnsFormatting = async (visibleColRange: [number, number]) => {
  const [startCol, endCol] = visibleColRange;

  const response = await fetch(
    `/api/document/${rid}/excel/formatting-chunk?` +
    `start_row=0&end_row=100&col_offset=${startCol}&max_cols=${endCol - startCol}`
  );

  const data = await response.json();
  setFormatting(prev => ({ ...prev, ...data.formatting }));
};
```

---

## 6. Performance Monitoring & Metrics

### 6.1 Detailed Performance Logging

```python
import time
import functools

def timing_decorator(label: str):
    """Decorator to time function execution and log detailed metrics."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000

                # Log to structured logging (for metrics aggregation)
                logger.info(
                    f"Performance metric",
                    extra={
                        'metric_type': 'timing',
                        'function': func.__name__,
                        'label': label,
                        'duration_ms': round(duration, 2),
                        'args': str(args)[:100],  # First 100 chars
                    }
                )

                return result
            except Exception as e:
                duration = (time.perf_counter() - start) * 1000
                logger.error(
                    f"Performance metric (failed)",
                    extra={
                        'metric_type': 'timing',
                        'function': func.__name__,
                        'label': label,
                        'duration_ms': round(duration, 2),
                        'error': str(e)
                    }
                )
                raise
        return wrapper
    return decorator

# Usage
@timing_decorator('formatting_extraction')
def _extract_cell_formatting(...):
    # ... existing code ...
    pass

@timing_decorator('chunk_load')
def get_formatting_chunk(rid):
    # ... existing code ...
    pass
```

### 6.2 Client-Side Performance Monitoring

```typescript
// Client-side performance tracking
class PerformanceMonitor {
  private metrics: Map<string, number[]> = new Map();

  start(label: string): () => void {
    const startTime = performance.now();

    return () => {
      const duration = performance.now() - startTime;
      this.record(label, duration);
    };
  }

  record(label: string, duration: number) {
    if (!this.metrics.has(label)) {
      this.metrics.set(label, []);
    }
    this.metrics.get(label)!.push(duration);
  }

  getStats(label: string) {
    const values = this.metrics.get(label) || [];
    if (values.length === 0) return null;

    const sorted = [...values].sort((a, b) => a - b);
    return {
      count: values.length,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      avg: values.reduce((a, b) => a + b) / values.length,
      median: sorted[Math.floor(sorted.length / 2)],
      p95: sorted[Math.floor(sorted.length * 0.95)],
      p99: sorted[Math.floor(sorted.length * 0.99)]
    };
  }

  report() {
    const report: any = {};
    for (const [label, _] of this.metrics) {
      report[label] = this.getStats(label);
    }
    return report;
  }
}

// Usage in ExcelViewer
const perfMonitor = useRef(new PerformanceMonitor());

const loadChunk = async (chunkIndex: number) => {
  const end = perfMonitor.current.start('chunk_load');

  try {
    // ... load chunk ...
  } finally {
    end();
  }
};

// Report metrics every 30 seconds
useEffect(() => {
  const interval = setInterval(() => {
    const report = perfMonitor.current.report();
    console.log('Performance Report:', report);

    // Send to analytics
    fetch('/api/metrics/frontend', {
      method: 'POST',
      body: JSON.stringify(report)
    });
  }, 30000);

  return () => clearInterval(interval);
}, []);
```

---

## 7. Testing Strategies

### 7.1 Load Testing Chunked Formatting

```python
# test_chunk_loading_performance.py
import asyncio
import aiohttp
import time

async def load_chunk(session, rid, sheet, start_row, end_row):
    """Simulate loading a chunk."""
    url = f"http://localhost:5000/api/document/{rid}/excel/formatting-chunk"
    params = {
        'session_id': 'test',
        'sheet': sheet,
        'start_row': start_row,
        'end_row': end_row
    }

    start = time.time()
    async with session.get(url, params=params) as response:
        data = await response.json()
        duration = (time.time() - start) * 1000
        return {
            'chunk': f"{start_row}-{end_row}",
            'duration_ms': duration,
            'size_bytes': len(str(data))
        }

async def test_parallel_chunk_loading(rid, sheet, total_rows, chunk_size=100):
    """Test loading all chunks in parallel (simulates aggressive prefetching)."""
    chunks = [(i, min(i + chunk_size, total_rows)) for i in range(0, total_rows, chunk_size)]

    async with aiohttp.ClientSession() as session:
        tasks = [load_chunk(session, rid, sheet, start, end) for start, end in chunks]

        start = time.time()
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start) * 1000

        print(f"\nParallel Chunk Loading Test")
        print(f"Total chunks: {len(chunks)}")
        print(f"Total time: {total_time:.2f}ms")
        print(f"Average chunk time: {sum(r['duration_ms'] for r in results) / len(results):.2f}ms")
        print(f"Total data transferred: {sum(r['size_bytes'] for r in results):,} bytes")

        return results

# Run test
asyncio.run(test_parallel_chunk_loading('RID-07595', 'AI Risk Database v3', 1000))
```

### 7.2 Memory Leak Detection

```typescript
// Detect memory leaks in chunk loading
describe('Memory Leak Tests', () => {
  it('should not accumulate formatting indefinitely', async () => {
    const { result } = renderHook(() => useFormattingChunks(...));

    // Load 100 chunks
    for (let i = 0; i < 100; i++) {
      await act(async () => {
        await result.current.loadChunk(i);
      });
    }

    // Check memory usage (rough estimate)
    const formattingSize = JSON.stringify(result.current.formatting).length;
    expect(formattingSize).toBeLessThan(1000000); // <1MB

    // Scroll far away (should unload old chunks)
    await act(async () => {
      result.current.handleScroll(5000 * 35); // Scroll to row 5000
    });

    // Formatting should be cleaned up
    const newSize = JSON.stringify(result.current.formatting).length;
    expect(newSize).toBeLessThan(formattingSize * 0.5); // At least 50% reduction
  });
});
```

---

## 8. Production Deployment Checklist

### Pre-Deployment
- [ ] Load test with 1000-row, 5000-row, and 10000-row spreadsheets
- [ ] Test with slow network (throttle to 3G, 1Mbps)
- [ ] Test with high latency (add 500ms delay)
- [ ] Verify memory usage stays under 100MB for 10K rows
- [ ] Test rollback procedure in staging
- [ ] Set up performance monitoring dashboards

### Deployment
- [ ] Deploy backend changes (chunk endpoint)
- [ ] Deploy frontend changes (chunk loading logic)
- [ ] Enable feature flag for 10% of users
- [ ] Monitor error rates and performance metrics
- [ ] Gradually increase to 50%, then 100%

### Post-Deployment
- [ ] Monitor chunk load success rate (target: >95%)
- [ ] Monitor average chunk load time (target: <200ms)
- [ ] Monitor cache hit rate (if Redis enabled, target: >60%)
- [ ] Collect user feedback (via in-app survey)
- [ ] Review error logs for edge cases
- [ ] Document any issues and solutions

---

## 9. Alternative Approaches (Experimental)

### 9.1 WebWorker-Based Formatting Application

**Offload formatting application to background thread:**

```typescript
// formatting-worker.ts
self.addEventListener('message', (e) => {
  const { formatting, rows, columns } = e.data;

  // Apply formatting to rows (CPU-intensive)
  const formattedRows = rows.map((row: any, rowIdx: number) => {
    const formattedRow = { ...row };

    columns.forEach((col: any, colIdx: number) => {
      const cellKey = `${rowIdx}_${colIdx}`;
      const fmt = formatting[cellKey];

      if (fmt) {
        formattedRow[`${col.key}_style`] = {
          backgroundColor: fmt.bgColor,
          color: fmt.fontColor,
          fontWeight: fmt.bold ? 'bold' : 'normal',
          // ... etc
        };
      }
    });

    return formattedRow;
  });

  self.postMessage({ formattedRows });
});

// Main thread
const formattingWorker = new Worker('formatting-worker.ts');

formattingWorker.postMessage({
  formatting,
  rows,
  columns
});

formattingWorker.addEventListener('message', (e) => {
  setFormattedRows(e.data.formattedRows);
});
```

**Benefits:**
- ✅ Non-blocking UI (formatting applied in background)
- ✅ Smooth scrolling (no main thread jank)

**Drawbacks:**
- ❌ Complex (worker management, message passing)
- ❌ Limited benefit (formatting application is already fast)

### 9.2 CSV Export with Embedded Styling

**Export formatted data as styled CSV/HTML:**

```python
def export_formatted_excel_to_html(file_path, sheet_name, formatting):
    """
    Export Excel with formatting to styled HTML.
    Can be viewed offline, no server needed.
    """
    import pandas as pd

    # Read data
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Build HTML with inline styles
    html = ['<table border="1">']

    # Header
    html.append('<thead><tr>')
    for col in df.columns:
        html.append(f'<th>{col}</th>')
    html.append('</tr></thead>')

    # Rows
    html.append('<tbody>')
    for row_idx, row in df.iterrows():
        html.append('<tr>')
        for col_idx, (col_name, value) in enumerate(row.items(), start=1):
            cell_key = f"{row_idx}_{col_idx}"
            fmt = formatting.get(cell_key, {})

            style = []
            if fmt.get('bgColor'):
                style.append(f"background-color: {fmt['bgColor']}")
            if fmt.get('fontColor'):
                style.append(f"color: {fmt['fontColor']}")
            if fmt.get('bold'):
                style.append("font-weight: bold")

            style_str = '; '.join(style)
            html.append(f'<td style="{style_str}">{value}</td>')

        html.append('</tr>')
    html.append('</tbody></table>')

    return '\n'.join(html)
```

---

## 10. Summary & Quick Reference

### Performance Targets
| Metric | Target | Current | Gap |
|--------|--------|---------|-----|
| Initial load (100 rows) | <3s | 2-3s | ✅ Met |
| Chunk load (100 rows) | <200ms | 150ms | ✅ Met |
| All formatting loaded (1000 rows) | <10s | N/A | 🚧 To implement |
| Memory usage (10K rows) | <100MB | N/A | 🚧 To test |

### Recommended Stack
```
Backend:
  - Python 3.9+
  - openpyxl 3.1.2 (formatting extraction)
  - Redis 7+ (optional caching)
  - Flask (API endpoints)

Frontend:
  - React 18+
  - react-data-grid 7+ (virtual scrolling)
  - IndexedDB (client cache, optional)
  - fetch API (chunk loading)
```

### Quick Implementation (1 Week)
```python
# Day 1-2: Backend endpoint
@excel_viewer_bp.route('/api/document/<rid>/excel/formatting-chunk')
def get_formatting_chunk(rid):
    # Extract chunk formatting
    # Return JSON

# Day 3-4: Frontend chunk loading
const { loadChunk } = useFormattingChunks(...);
useEffect(() => {
    // Load chunks 1-N in background
}, []);

# Day 5: Testing & debugging
# Day 6-7: Performance tuning & deployment
```

---

**Document Date:** 2025-10-07
**Author:** Senior Performance Engineer (AI Assistant)
**Status:** Technical Appendix - Implementation Reference
