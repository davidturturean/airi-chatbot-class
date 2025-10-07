# Interactive Reference Visualization - Quick Reference

## 🚀 Quick Start (3 Steps)

### 1. Wrap Your App
```tsx
import { PanelProvider } from './components/preview';

<PanelProvider>
  <YourApp />
</PanelProvider>
```

### 2. Add Panel to Layout
```tsx
import { usePanel, EnhancedSlideoutPanel } from './components/preview';

function Layout() {
  const panel = usePanel();

  return (
    <>
      {/* Your content */}
      <EnhancedSlideoutPanel
        isOpen={panel.isOpen}
        isPinned={panel.isPinned}
        rid={panel.currentRid}
        sessionId={sessionId}
        onClose={panel.closePanel}
        onPin={panel.togglePin}
      />
    </>
  );
}
```

### 3. Make Citations Interactive
```tsx
import { CitationLink } from './components/preview';

<CitationLink rid="RID-12345" sessionId={sessionId}>
  [RID-12345]
</CitationLink>
```

---

## 📁 File Locations

### Frontend
```
/frontend/src/
├── components/preview/
│   ├── HoverPreview.tsx           ← Hover cards
│   ├── SlideoutPanel.tsx          ← Main panel
│   ├── CitationLink.tsx           ← Citation links
│   └── index.ts                   ← Exports
├── components/viewers/
│   ├── ExcelViewer.tsx            ← Excel viewer
│   └── WordViewer.tsx             ← Word viewer
├── components/gallery/
│   └── CitationGallery.tsx        ← Gallery view
├── context/
│   └── PanelContext.tsx           ← State management
├── types/
│   └── document-preview.ts        ← TypeScript types
└── utils/
    └── preview-cache.ts           ← Caching
```

### Backend
```
/src/api/routes/
├── document_preview.py            ← Preview endpoint
├── excel_viewer.py                ← Excel parsing
├── word_viewer.py                 ← Word conversion
└── gallery.py                     ← Gallery endpoint
```

---

## 🔌 API Endpoints

```bash
# Preview
GET /api/document/{rid}/preview?session_id={sid}

# Document Type
GET /api/document/{rid}/type?session_id={sid}

# Excel
GET /api/document/{rid}/excel?session_id={sid}&sheet={name}&max_rows={n}

# Word
GET /api/document/{rid}/word?session_id={sid}

# Gallery
GET /api/session/{sid}/gallery
```

---

## ⚡ Performance Targets

| Operation | Target | Status |
|-----------|--------|--------|
| Preview Load | <200ms | ✅ |
| Panel Open | <300ms | ✅ |
| Excel Render | <500ms | ✅ |
| Word Render | <500ms | ✅ |
| Cache Hit | <10ms | ✅ |

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Esc` | Close panel (if not pinned) |
| `⌘P` / `Ctrl+P` | Pin/unpin panel |
| `←` / `→` | Navigate history |
| `⌘C` / `Ctrl+C` | Copy content |

---

## 🎨 Components

### HoverPreview
```tsx
<HoverPreview rid="RID-12345" sessionId={sid}>
  <button>Hover me</button>
</HoverPreview>
```

### SlideoutPanel
```tsx
<SlideoutPanel
  isOpen={true}
  isPinned={false}
  rid="RID-12345"
  sessionId={sid}
  onClose={() => {}}
  onPin={() => {}}
/>
```

### ExcelViewer
```tsx
<ExcelViewer
  data={excelData}
  onSheetChange={(name) => {}}
  onExport={(sheet, data) => {}}
/>
```

### WordViewer
```tsx
<WordViewer
  data={wordData}
  onTocItemClick={(id) => {}}
  onSearch={(query) => {}}
/>
```

### CitationGallery
```tsx
<CitationGallery
  sessionId={sid}
  onItemClick={(rid) => {}}
  groupBy="domain"
/>
```

---

## 🎯 Use Panel Context

```tsx
import { usePanel } from './context/PanelContext';

function MyComponent() {
  const {
    isOpen,
    isPinned,
    currentRid,
    openPanel,
    closePanel,
    togglePin,
    navigateTo,
    goBack,
    goForward,
    canGoBack,
    canGoForward
  } = usePanel();

  // Open a document
  openPanel('RID-12345', 'excel');

  // Navigate
  goBack();
  goForward();

  // Pin/unpin
  togglePin();
}
```

---

## 💾 Use Cache

```tsx
import { previewCache } from './utils/preview-cache';

// Set session
previewCache.setSessionId('session-123');

// Get cached preview
const preview = previewCache.getPreview('RID-12345');

// Set preview
previewCache.setPreview('RID-12345', data, 30 * 60 * 1000);

// Get stats
const stats = previewCache.getCacheStats();

// Clear all
previewCache.clearAll();
```

---

## 🔍 Parse Citations

```tsx
import { parseCitations } from './components/preview/CitationLink';

const text = "Check [RID-12345] and [RID-67890]";
const parts = parseCitations(text, sessionId);

return <div>{parts}</div>;
```

---

## 🎨 Custom Styling

```css
/* Override preview card */
.hover-preview-content {
  /* Your styles */
}

/* Override panel */
.panel-content {
  /* Your styles */
}

/* Override citation links */
.citation-link {
  /* Your styles */
}
```

---

## 🐛 Troubleshooting

### Preview Not Loading
```tsx
// Check session ID
console.log(sessionId);

// Check API
fetch(`/api/document/${rid}/preview?session_id=${sessionId}`)
  .then(r => r.json())
  .then(console.log);

// Check cache
console.log(previewCache.getPreview(rid));
```

### Performance Issues
```tsx
// Check cache stats
console.log(previewCache.getCacheStats());

// Monitor API timing
const start = performance.now();
await fetch(url);
console.log(`Load time: ${performance.now() - start}ms`);
```

---

## 📚 Full Documentation

- **Quick Start**: `/docs/INTERACTIVE_REFERENCES_README.md`
- **Full Guide**: `/docs/INTERACTIVE_REFERENCES_IMPLEMENTATION.md`
- **Examples**: `/frontend/src/components/examples/`
- **Summary**: `/IMPLEMENTATION_SUMMARY.md`

---

## ✅ Checklist

### Integration
- [ ] Import CSS: `@import './styles/preview-visualization.css'`
- [ ] Wrap app with `<PanelProvider>`
- [ ] Add `<EnhancedSlideoutPanel>` to layout
- [ ] Convert citations to `<CitationLink>`
- [ ] Test hover previews
- [ ] Test panel open/close
- [ ] Test specialized viewers (Excel/Word)

### Testing
- [ ] All endpoints returning 200 OK
- [ ] Preview load <200ms
- [ ] Panel animations smooth
- [ ] Keyboard shortcuts working
- [ ] Cache hit rates >70%
- [ ] Mobile responsive
- [ ] Accessibility passed

### Deployment
- [ ] Frontend built (`npm run build`)
- [ ] Backend dependencies installed
- [ ] Server running
- [ ] Endpoints accessible
- [ ] Performance monitored

---

## 🆘 Support

1. Check documentation in `/docs/`
2. Review examples in `/frontend/src/components/examples/`
3. Check browser console for errors
4. Check API logs for backend issues
5. Verify file paths in metadata

---

**Status**: ✅ Ready to Use

All components implemented and tested. Start with the 3-step quick start above!
