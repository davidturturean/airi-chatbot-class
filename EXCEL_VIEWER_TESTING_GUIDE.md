# Excel Viewer Evolution: Testing Guide

## Quick Start Testing

### Prerequisites
```bash
# Ensure dependencies are installed
pip install openpyxl pandas flask

cd frontend
npm install
```

### Start the Application
```bash
# Terminal 1: Backend
python -m src.api.app

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Access the Application
Open browser to: `http://localhost:3000`

---

## Test Scenarios

### Scenario 1: Citation Navigation to Exact Cell

**Test:** Verify that clicking an Excel citation navigates to the exact row with context

**Steps:**
1. Ask chatbot: "What are AI risks in healthcare?"
2. Look for citations like: `[MIT AI Repository, AI Risk Database v3, Row 47]`
3. Click the citation link
4. **Expected Results:**
   - ✅ Slideout panel opens on the right
   - ✅ Excel viewer shows correct sheet (e.g., "AI Risk Database v3")
   - ✅ Scrolled to row 47 with 5-10 rows visible above it
   - ✅ Row 47 highlighted in GOLD for 3 seconds
   - ✅ Gold highlight fades, but row remains visible
   - ✅ You can see context rows (46, 48, 49, etc.)

**How to Verify Sheet Selection:**
- Look at sheet tabs at bottom of Excel viewer
- The correct sheet should have blue underline and indigo text
- NOT showing "Sheet1" unless that's the actual source

**How to Verify Scroll Position:**
- Row number column on left should show target row in middle of viewport
- Should see rows BEFORE target (context)
- Should NOT be scrolled to top (row 1)

**Screenshot Test:**
- Take screenshot showing:
  - Citation text in chat
  - Excel viewer with highlighted row
  - Sheet tab selection
  - Row numbers visible

---

### Scenario 2: Cell Formatting Preservation

**Test:** Verify that Excel cell colors, bold, fonts are preserved

**Steps:**
1. Open an Excel file that has:
   - Red background cells (high risk)
   - Green background cells (low risk)
   - Bold headers
   - Different font sizes

2. Click citation to that file
3. **Expected Results:**
   - ✅ Red cells display with red background
   - ✅ Green cells display with green background
   - ✅ Bold text displays as bold
   - ✅ Font sizes match original
   - ✅ Font colors preserved

**Example File to Test:**
- `The_AI_Risk_Repository_V3_26_03_2025.xlsx`
- Should have various colored cells indicating risk levels

**How to Verify:**
1. Open the Excel file in Microsoft Excel/LibreOffice
2. Note which cells have colors/formatting
3. Compare with web viewer
4. Should look identical (or very close)

**If Formatting Missing:**
- Check browser console for errors
- Verify openpyxl is installed: `pip list | grep openpyxl`
- Check backend logs for "Extracted formatting for X cells"
- Verify API response includes `formatting` object

---

### Scenario 3: Zoom Controls

**Test:** Verify zoom in/out functionality

**Steps:**
1. Open any Excel citation
2. Look for zoom controls in toolbar (top right):
   ```
   [−] 100% [+] [↻]
   ```

3. **Test Zoom Out:**
   - Click `[−]` button
   - Verify zoom changes to 75%
   - Verify grid shrinks visually
   - Verify you can see MORE rows/columns at once
   - Verify button is disabled at 75%

4. **Test Zoom In:**
   - Click `[+]` button twice
   - Verify zoom changes to 125%, then 150%
   - Verify grid grows visually
   - Verify text is easier to read
   - Verify button is disabled at 150%

5. **Test Reset:**
   - Click `[↻]` reset button
   - Verify zoom returns to 100%
   - Verify grid returns to normal size

**Expected Results:**
- ✅ Zoom range: 75% to 150%
- ✅ Increments: 25% steps
- ✅ Smooth scaling (CSS transform)
- ✅ No re-render lag
- ✅ Buttons disabled at limits
- ✅ Reset always works

**Performance Check:**
- Zoom should be INSTANT (<100ms)
- No loading spinner
- No grid flicker

---

### Scenario 4: Context-Aware Search

**Test:** Verify search highlights matches WITHOUT hiding other rows

**Steps:**
1. Open Excel viewer (any file)
2. Type in search box: "healthcare"
3. **Expected Results (CRITICAL):**
   - ✅ Shows match count: "12 matches found" (or similar)
   - ✅ Matched cells highlighted in YELLOW
   - ✅ Scrolls to first match
   - ✅ Shows 5-10 rows BEFORE first match (context)
   - ✅ **ALL 500 ROWS STILL VISIBLE** (NOT filtered out)
   - ✅ Can scroll up/down to see non-matching rows
   - ✅ Can see patterns in surrounding data

4. **Test Different Search:**
   - Clear search: ""
   - Verify yellow highlights disappear
   - Type: "risk"
   - Verify new matches highlighted
   - Verify count updates

**CRITICAL: What NOT to See:**
- ❌ Rows disappearing/filtering out
- ❌ Only 1-2 rows visible
- ❌ "Showing 12 of 500 rows" message
- ❌ Context destroyed

**Before vs After:**
```
BROKEN (old way):
Search "healthcare" → 12 rows shown, 488 hidden → NO CONTEXT

CORRECT (new way):
Search "healthcare" → 12 matches highlighted in yellow, all 500 rows visible → FULL CONTEXT
```

**How to Verify:**
1. Search for something rare (1-2 matches)
2. Scroll up from first match
3. Should see MANY rows without yellow highlights
4. This proves filtering is NOT happening

---

### Scenario 5: Column Resizing

**Test:** Verify columns can be resized by dragging

**Steps:**
1. Open Excel viewer
2. Hover over column border between headers
3. Cursor should change to resize cursor `<->`
4. Click and drag left/right
5. **Expected Results:**
   - ✅ Column width changes as you drag
   - ✅ Smooth resizing
   - ✅ Other columns adjust
   - ✅ Content reflows to fit

**Note:** This already worked before, just verify no regression

---

### Scenario 6: Sorting and Filtering

**Test:** Verify existing sort/filter features still work

**Steps:**
1. Open Excel viewer
2. Click column header (e.g., "Domain")
3. Verify sort icon appears
4. **Expected Results:**
   - ✅ Rows sort alphabetically (A-Z)
   - ✅ Click again: reverse sort (Z-A)
   - ✅ Click third time: remove sort
   - ✅ Formatting preserved during sort
   - ✅ Highlighted rows maintain highlight

**Note:** Existing features, verify no regression

---

### Scenario 7: Export to CSV

**Test:** Verify export functionality works

**Steps:**
1. Open Excel viewer
2. Click "Export" button (top right)
3. **Expected Results:**
   - ✅ CSV file downloads
   - ✅ Filename: `[title]_[sheet].csv`
   - ✅ Open CSV in Excel/text editor
   - ✅ All data present
   - ✅ Proper escaping (commas, quotes)

**Note:** Existing feature, verify no regression

---

### Scenario 8: Sheet Tab Switching

**Test:** Verify switching between sheets works

**Steps:**
1. Open Excel file with multiple sheets
2. Look for sheet tabs below toolbar
3. Click different sheet tab
4. **Expected Results:**
   - ✅ Grid updates to show new sheet data
   - ✅ Active tab highlighted (blue underline)
   - ✅ Row count updates
   - ✅ Search/filters reset
   - ✅ Zoom maintained

---

### Scenario 9: Performance Testing

**Test:** Verify performance targets are met

**Tools:**
- Browser DevTools → Network tab
- Browser DevTools → Performance tab

**Metrics:**
1. **Preview Load Time:** <200ms
   - Time from citation click to preview data loaded
   - Check Network tab → `/api/document/{rid}/preview`

2. **Panel Open Time:** <300ms
   - Time from preview load to panel visible
   - Should feel instant

3. **Excel Render Time:** <500ms
   - Time from panel open to grid rendered
   - Check Network tab → `/api/document/{rid}/excel`

4. **Formatting Load Time:** <150ms
   - Part of Excel render time
   - Check backend logs for "Extracted formatting"

**How to Test:**
1. Open DevTools → Network
2. Clear network log
3. Click Excel citation
4. Check timing of requests:
   - `/preview`: Should be <200ms
   - `/excel`: Should be <500ms
5. Grid should render immediately after data loads

**Red Flags:**
- ❌ >1 second to open panel
- ❌ Loading spinner for more than 500ms
- ❌ Blank screen after clicking citation

---

### Scenario 10: Error Handling

**Test:** Verify graceful degradation when things fail

**Steps:**
1. **Test Missing File:**
   - Create citation to non-existent file
   - Click citation
   - **Expected:** Error message, "Try Again" button

2. **Test Corrupted File:**
   - (Requires test file with broken formatting)
   - **Expected:** Grid loads without formatting (graceful degradation)

3. **Test Network Error:**
   - Disconnect WiFi
   - Click citation
   - **Expected:** Error message, "Try Again" button works when WiFi returns

4. **Test No Source Location:**
   - Old citation without source_location
   - **Expected:** Grid opens to top (row 1), no navigation error

---

## Automated Testing

### Backend Unit Tests

```python
# Test source location extraction
def test_extract_excel_source_location():
    metadata = {
        'url': 'test.xlsx',
        'sheet': 'Sheet1',
        'row': 42
    }
    location = citation_service._extract_excel_source_location(metadata)
    assert location == {'sheet': 'Sheet1', 'row': 42}

# Test cell formatting extraction
def test_extract_cell_formatting():
    formatting = _extract_cell_formatting(test_file, 'Sheet1', 0, 100)
    assert isinstance(formatting, dict)
    assert len(formatting) > 0
```

### Frontend Unit Tests

```typescript
// Test zoom controls
test('zoom increases by 25%', () => {
  const { getByTitle } = render(<ExcelViewer ... />);
  const zoomIn = getByTitle('Zoom in');

  fireEvent.click(zoomIn);
  expect(screen.getByText('125%')).toBeInTheDocument();
});

// Test search highlighting
test('search highlights matches', () => {
  const { getByPlaceholderText } = render(<ExcelViewer ... />);
  const search = getByPlaceholderText(/search/i);

  fireEvent.change(search, { target: { value: 'test' } });
  expect(screen.getByText(/matches found/i)).toBeInTheDocument();
});
```

---

## Regression Testing Checklist

Before deploying, verify ALL existing features still work:

- [ ] Hover preview cards appear on citation hover
- [ ] Slideout panel opens on citation click
- [ ] Word viewer works for .docx files
- [ ] PDF viewer works for .pdf files
- [ ] Text viewer works for plain text
- [ ] Gallery view shows all citations
- [ ] Navigation history (back/forward) works
- [ ] Pin panel feature works
- [ ] Session persistence works
- [ ] Mobile responsive (panel adapts to small screens)

---

## Browser Compatibility Testing

**Test in:**
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

**Known Issues:**
- IE11: NOT SUPPORTED (react-data-grid doesn't support it)
- Mobile: Responsive but not optimized for touch (future work)

---

## Production Deployment Checklist

Before going live:

**Backend:**
- [ ] openpyxl installed on production server
- [ ] Excel files accessible from API server
- [ ] Logging configured (check for "Extracted formatting" logs)
- [ ] Error tracking configured (Sentry, etc.)

**Frontend:**
- [ ] lucide-react icons installed
- [ ] Build optimized: `npm run build`
- [ ] Source maps uploaded (for debugging)
- [ ] CDN configured (if using)

**Database:**
- [ ] Existing snippets migrated (or graceful fallback for old format)
- [ ] Snippet database backed up
- [ ] Index on source_location field (if stored separately)

**Monitoring:**
- [ ] Performance metrics tracked (preview load, Excel render)
- [ ] Error rate monitored (<2% target)
- [ ] User feedback collection configured
- [ ] A/B test setup (if rolling out gradually)

---

## Troubleshooting Guide

### Issue: Formatting Not Showing

**Symptoms:** Cells are all white, no colors
**Possible Causes:**
1. openpyxl not installed
2. Excel file has no formatting
3. Formatting extraction failed

**Debug Steps:**
```bash
# Check openpyxl installed
pip list | grep openpyxl

# Check backend logs
grep "Extracted formatting" logs/app.log

# Check API response
curl http://localhost:5000/api/document/RID-00073/excel?session_id=test | jq '.sheets[0].formatting'
```

**Solution:**
- Install openpyxl: `pip install openpyxl`
- Restart Flask server
- Clear browser cache

---

### Issue: Navigation Not Working

**Symptoms:** Citation opens Excel but doesn't scroll to row
**Possible Causes:**
1. source_location not in API response
2. Sheet name mismatch
3. DataGrid ref not set

**Debug Steps:**
```javascript
// In browser console
console.log(excelData.source_location);
// Should show: {sheet: "...", row: 47}

// Check if sheet exists
console.log(excelData.sheets.map(s => s.sheet_name));
// Should include source_location.sheet
```

**Solution:**
- Verify preview API returns source_location
- Check sheet name matches exactly (case-sensitive)
- Ensure gridRef is properly set in ExcelViewer

---

### Issue: Search Filtering Rows

**Symptoms:** Rows disappear when searching
**Possible Causes:**
1. Old code still active
2. Filter logic applied to search

**Debug Steps:**
```typescript
// In processedRows useMemo
console.log('Search query:', searchQuery);
console.log('Rows before filter:', rows.length);
console.log('Rows after filter:', filteredRows.length);
```

**Solution:**
- Ensure processedRows does NOT filter by searchQuery
- Search should only update searchMatches Set
- Highlighting happens in FormattedCell renderer

---

### Issue: Zoom Not Smooth

**Symptoms:** Lag when zooming, grid flickers
**Possible Causes:**
1. CSS transform not applied correctly
2. Re-rendering on zoom change

**Debug Steps:**
```typescript
// Check if transform is applied
console.log(document.querySelector('.excel-viewer div[style*="transform"]'));
```

**Solution:**
- Ensure zoom uses CSS transform, not re-render
- Memoize columns and rows (useMemo)
- Avoid unnecessary state updates

---

## Success Metrics

After deploying, track these metrics:

**Week 1:**
- Navigation success rate: >95%
- Formatting display rate: >90%
- Error rate: <5%

**Week 2:**
- Navigation success rate: >98%
- User satisfaction (survey): >4/5
- Error rate: <2%

**Month 1:**
- Citation click-through rate: +20%
- Time to find data: -50%
- User retention: +10%

---

## Feedback Collection

**User Survey Questions:**
1. "How easy was it to find the cited data?" (1-5 scale)
2. "Did the cell colors help you understand the data?" (Yes/No)
3. "Did you use the zoom feature?" (Yes/No/Didn't notice)
4. "Was the search helpful?" (Yes/No/Didn't use)
5. "Any suggestions for improvement?" (Open text)

**Analytics Events to Track:**
- `excel_citation_clicked`
- `excel_navigation_success`
- `excel_zoom_used`
- `excel_search_used`
- `excel_export_used`

---

## Next Steps After Testing

1. **Fix Critical Bugs:** Any issues that break core functionality
2. **Address Performance:** If any metric exceeds target (>500ms)
3. **Collect User Feedback:** Deploy to small group, get feedback
4. **Iterate:** Improve based on data
5. **Full Rollout:** Deploy to all users
6. **Monitor:** Track metrics for 1 month
7. **Plan Enhancements:** Implement wish-list features

---

## Contact for Testing Support

**Implementation:** EXCEL_VIEWER_EVOLUTION_REPORT.md
**Code:** See modified files in report
**Issues:** Check browser console, backend logs
**Questions:** Review this testing guide

Happy Testing! 🚀
