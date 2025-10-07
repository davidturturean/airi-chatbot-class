# Interactive Reference Visualization System - Implementation Guide

## Overview

This document provides a comprehensive guide to the Interactive Reference Visualization system implemented for the AIRI chatbot. The system transforms static citations like `[RID-12345]` into an interactive, explorable document preview experience inspired by Airtable's rich UI patterns.

## Architecture

### Frontend Components

#### Phase 1: Hover Previews
- **Component**: `HoverPreview.tsx`
- **Location**: `/frontend/src/components/preview/HoverPreview.tsx`
- **Purpose**: Show instant previews when hovering over citations
- **Performance Target**: <200ms preview load
- **Features**:
  - 300ms hover delay before showing preview
  - Cached preview data (session-scoped)
  - Metadata badges (domain, entity, risk category)
  - Content snippet (500 characters)

#### Phase 2: Slideout Panel
- **Component**: `SlideoutPanel.tsx`
- **Location**: `/frontend/src/components/preview/SlideoutPanel.tsx`
- **Purpose**: Full document viewing in a slide-out panel
- **Performance Target**: <300ms panel open animation
- **Features**:
  - Pin functionality (stays open while browsing)
  - Navigation history (back/forward arrows)
  - Keyboard shortcuts (Esc to close, ⌘P to pin, arrows to navigate)
  - Copy and download functionality

#### Phase 3: Excel Interactive Viewer
- **Component**: `ExcelViewer.tsx`
- **Location**: `/frontend/src/components/viewers/ExcelViewer.tsx`
- **Purpose**: Interactive spreadsheet viewing
- **Performance Target**: <500ms Excel render
- **Features**:
  - Multiple sheet support with tabs
  - Column sorting and filtering
  - In-sheet search
  - Cell selection and copy
  - Export to CSV
  - Virtual scrolling for large datasets

#### Phase 4: Word Document Viewer
- **Component**: `WordViewer.tsx`
- **Location**: `/frontend/src/components/viewers/WordViewer.tsx`
- **Purpose**: Render .docx files with formatting preserved
- **Features**:
  - HTML conversion with formatting preservation
  - Table of contents sidebar
  - In-document search with highlighting
  - Responsive typography

#### Phase 5: Citation Gallery
- **Component**: `CitationGallery.tsx`
- **Location**: `/frontend/src/components/gallery/CitationGallery.tsx`
- **Purpose**: Explore all sources in grid/list view
- **Features**:
  - Grid and list view modes
  - Search across all sources
  - Filter by domain, type, entity, risk category
  - Group by domain, type, or entity
  - Click to open in slideout panel

### Backend Endpoints

#### Document Preview API
- **Endpoint**: `GET /api/document/{rid}/preview`
- **Location**: `/src/api/routes/document_preview.py`
- **Purpose**: Lightweight preview data for hover cards
- **Performance**: <200ms response time
- **Response Format**:
```json
{
  "rid": "RID-12345",
  "title": "Document Title",
  "content": "Preview content...",
  "metadata": {
    "domain": "AI Governance",
    "entity": "MIT",
    "risk_category": "High"
  },
  "highlights": ["search", "terms"],
  "preview_type": "text",
  "created_at": "2025-10-06T12:00:00"
}
```

#### Excel Viewer API
- **Endpoint**: `GET /api/document/{rid}/excel`
- **Location**: `/src/api/routes/excel_viewer.py`
- **Purpose**: Parse Excel files and return structured data
- **Performance**: <500ms for typical Excel files
- **Features**:
  - Multi-sheet support
  - Pagination (max_rows, offset parameters)
  - Column metadata (type inference, width estimation)
  - Row count tracking

#### Word Viewer API
- **Endpoint**: `GET /api/document/{rid}/word`
- **Location**: `/src/api/routes/word_viewer.py`
- **Purpose**: Convert .docx to HTML with formatting
- **Performance**: <500ms for typical documents
- **Features**:
  - Mammoth-based conversion
  - HTML sanitization (bleach)
  - Table of contents extraction
  - Heading ID generation for navigation
  - Word and page count estimation

#### Citation Gallery API
- **Endpoint**: `GET /api/session/{session_id}/gallery`
- **Location**: `/src/api/routes/gallery.py`
- **Purpose**: Get all citations in a session
- **Response**: Gallery items with metadata and filter options

### State Management

#### PanelContext
- **Location**: `/frontend/src/context/PanelContext.tsx`
- **Purpose**: Global state for slideout panel
- **Features**:
  - Panel open/close state
  - Pin state
  - Navigation history
  - History index tracking

#### PreviewCache
- **Location**: `/frontend/src/utils/preview-cache.ts`
- **Purpose**: Session-scoped caching
- **Features**:
  - 30-minute default expiry
  - Automatic cleanup every 5 minutes
  - Separate caches for previews, Excel, Word, and gallery data
  - Session ID validation

## Integration Guide

### Step 1: Wrap Your App with PanelProvider

```tsx
import { PanelProvider } from './components/preview';

function App() {
  return (
    <PanelProvider>
      {/* Your app components */}
    </PanelProvider>
  );
}
```

### Step 2: Add the Slideout Panel

```tsx
import { usePanel, EnhancedSlideoutPanel } from './components/preview';

function ChatInterface() {
  const panel = usePanel();
  const sessionId = useSessionId(); // Your session ID logic

  return (
    <div>
      {/* Your chat UI */}

      <EnhancedSlideoutPanel
        isOpen={panel.isOpen}
        isPinned={panel.isPinned}
        rid={panel.currentRid}
        sessionId={sessionId}
        onClose={panel.closePanel}
        onPin={panel.togglePin}
        onNavigate={panel.navigateTo}
      />
    </div>
  );
}
```

### Step 3: Convert Citations to Interactive Links

```tsx
import { CitationLink } from './components/preview';

function Message({ content, sessionId }) {
  // Parse [RID-12345] citations
  const parts = parseMessageWithCitations(content, sessionId);

  return <div>{parts}</div>;
}

function parseMessageWithCitations(text, sessionId) {
  const regex = /\[(RID-\d{5}|META-\d{5})\]/g;
  const parts = [];
  let lastIndex = 0;

  text.replace(regex, (match, rid, offset) => {
    if (offset > lastIndex) {
      parts.push(text.substring(lastIndex, offset));
    }
    parts.push(
      <CitationLink key={rid} rid={rid} sessionId={sessionId}>
        {match}
      </CitationLink>
    );
    lastIndex = offset + match.length;
  });

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts;
}
```

### Step 4: Add Gallery View (Optional)

```tsx
import { CitationGallery } from './components/preview';

function SourcesGallery({ sessionId }) {
  const { openPanel } = usePanel();

  return (
    <CitationGallery
      sessionId={sessionId}
      onItemClick={(rid) => openPanel(rid)}
    />
  );
}
```

## Performance Optimization

### Caching Strategy
- **Session-scoped**: Cache cleared when session changes
- **Aggressive caching**: 30-minute expiry for static documents
- **Cache hits**: <10ms for cached previews

### API Performance Targets
- Preview load: <200ms
- Panel open: <300ms
- Excel render: <500ms
- Word render: <500ms

### Frontend Optimizations
- Lazy loading for viewers
- Virtual scrolling for large datasets
- Debounced search inputs
- Memoized filter operations
- GPU-accelerated animations

### Backend Optimizations
- Pagination for Excel files (1000 rows default)
- Read-only workbook loading
- HTML sanitization caching
- Efficient file path resolution

## Error Handling

### Frontend
- Loading states for all async operations
- Error boundaries for component failures
- Fallback to text viewer if specialized viewer fails
- User-friendly error messages

### Backend
- Graceful fallbacks (text preview if Excel/Word parsing fails)
- File not found handling
- Session validation
- Performance logging for slow operations

## Accessibility

### Keyboard Navigation
- `Esc`: Close panel (if not pinned)
- `⌘P` / `Ctrl+P`: Pin/unpin panel
- `←` / `→`: Navigate history
- `⌘C` / `Ctrl+C`: Copy content
- Tab navigation through interactive elements

### Screen Reader Support
- ARIA labels on all interactive elements
- Semantic HTML structure
- Descriptive alt text for icons
- Focus management

### Visual Accessibility
- High contrast colors
- Sufficient text sizes
- Focus indicators
- Consistent spacing

## Testing

### Frontend Tests
```bash
cd frontend
npm test
```

### Backend Tests
```bash
source .venv/bin/activate
pytest tests/
```

### Performance Testing
- Measure preview load times
- Monitor cache hit rates
- Test with large Excel files (10,000+ rows)
- Test with complex Word documents (50+ pages)

## Deployment

### Build Frontend
```bash
cd frontend
npm run build
```

### Install Backend Dependencies
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables
No additional environment variables required. The system uses existing AIRI configuration.

## Troubleshooting

### Preview Not Loading
1. Check session ID is valid
2. Verify document exists in database
3. Check browser console for errors
4. Verify API endpoint is accessible

### Excel/Word Viewer Not Working
1. Verify file path in metadata
2. Check file exists and is readable
3. Verify pandas/openpyxl/mammoth installed
4. Check API logs for conversion errors

### Performance Issues
1. Monitor cache hit rates
2. Check API response times in logs
3. Reduce max_rows for Excel files
4. Enable pagination for large datasets

## Future Enhancements

### Phase 6: Advanced Features
- PDF viewer with annotation support
- Image gallery with lightbox
- Related citations sidebar
- Citation graph visualization
- Collaborative annotations

### Phase 7: Analytics
- Track preview usage metrics
- Measure user engagement
- A/B test different preview styles
- Monitor performance in production

## Support

For questions or issues:
1. Check this documentation
2. Review example implementations in `/frontend/src/components/examples/`
3. Check API logs in `/logs/`
4. Contact the development team

## Version History

- **v1.0.0** (2025-10-06): Initial implementation
  - Hover previews
  - Slideout panel
  - Excel viewer
  - Word viewer
  - Citation gallery
