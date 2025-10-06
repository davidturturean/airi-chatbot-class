# AIRI Chatbot Snippet System Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Document Storage & Structure](#1-document-storage--structure)
4. [Backend Processing Flow](#2-backend-processing-flow)
5. [API Response Streaming](#3-api-response-streaming)
6. [Frontend Reception](#4-frontend-reception)
7. [Related Documents Display](#5-related-documents-display)
8. [Snippet API & Retrieval](#6-snippet-api--retrieval)
9. [Snippet Rendering](#7-snippet-rendering)
10. [Chat Message Citation Links](#8-chat-message-citation-links)
11. [Error Handling](#error-handling)
12. [Testing Strategies](#testing-strategies)
13. [Performance Considerations](#performance-considerations)
14. [Security Implications](#security-implications)
15. [Future Enhancements](#future-enhancements)
16. [Troubleshooting Guide](#troubleshooting-guide)

## Overview

The snippet system in the AIRI chatbot is a complete document retrieval and rendering pipeline that enables users to access source documents referenced in AI responses. The system:

1. Stores document snippets as text files in `data/doc_snippets/`
2. References them using RID (Repository ID) format: `RID-#####`
3. Generates clickable links in chat responses
4. Displays them in the "Related Documents" tab
5. Renders them in a dedicated snippet viewer page

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Excel Data    │────▶│ Text Snippets   │────▶│  Vector Store   │
│ (.xlsx source)  │     │ (RID-#####.txt) │     │  (ChromaDB)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Chat Service   │────▶│Citation Service │────▶│   Enhanced      │
│ (process_query) │     │ (add citations) │     │   Response      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   API Stream    │────▶│    Frontend     │────▶│ Related Docs    │
│  (SSE format)   │     │   Reception     │     │    Display      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Snippet API    │◀────│  User Click     │◀────│ Document Link   │
│ (/api/snippet) │      │   Handler       │     │   Button        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │ Snippet Viewer  │
                                                 │     Page        │
                                                 └─────────────────┘
```

## 1. Document Storage & Structure

### Storage Location
- **Directory**: `/data/doc_snippets/`
- **File Format**: `RID-#####.txt` (e.g., `RID-00073.txt`, `RID-01234.txt`)
- **Content**: Plain text extracted from Excel file
- **Source File**: `The_AI_Risk_Repository_V3_26_03_2025.xlsx`

### File Naming Convention
- RID = Repository ID
- Always 5 digits with leading zeros
- Example: `RID-00001.txt`, `RID-02345.txt`

## 2. Backend Processing Flow

### 2.1 Query Processing
**File**: `/src/core/services/chat_service.py`
**Lines**: 44-241
```python
def process_query(self, message: str, conversation_id: str) -> Tuple[str, List[Any]]:
    # ... intent classification and routing ...
    
    # Line 200-201: Retrieve documents
    docs = self._retrieve_documents(message, query_type, domain)
    
    # Line 216: Enhance response with citations
    enhanced_response = self.citation_service.enhance_response_with_citations(response, docs)
    
    # Line 236: Return response and documents
    return validated_response, docs
```

### 2.2 Citation Enhancement
**File**: `/src/core/services/citation_service.py`
**Lines**: 26-61
```python
def enhance_response_with_citations(self, response: str, docs: List[Document]) -> str:
    # Line 41-49: Build RID citation mapping
    for doc in docs:
        rid = doc.metadata.get('rid', None)
        if rid:
            citation = self._format_rid_citation(doc)  # Creates [RID-#####](/snippet/RID-#####)
            self.rid_citation_map[rid] = citation
            self._save_rid_snippet(doc, rid)  # Saves to file system
    
    # Line 52: Replace RID placeholders in text
    enhanced_response = self._replace_rid_citations(response, docs)
```

**Lines**: 63-101 - RID replacement logic
```python
def _replace_rid_citations(self, response: str, docs: List[Document]) -> str:
    # Line 79: Pattern to match RID-##### 
    rid_pattern = r'(?:\()?RID-(\d{5})(?:\))?'
    
    def replace_rid(match):
        rid = f"RID-{match.group(1)}"
        # Line 100: Convert to clickable link
        return f"[{rid}](/snippet/{rid})"
```

## 3. API Response Streaming

### 3.1 Stream Endpoint
**File**: `/src/api/routes/chat.py`
**Lines**: 52-168
```python
@chat_bp.route('/api/v1/stream', methods=['POST'])
def stream_message():
    def generate():
        # Line 88: Process query and get docs
        response_text, docs = chat_service.process_query(message, conversation_id)
        
        # Lines 104-145: Format documents for Related Documents
        related_docs = []
        
        if is_metadata_query:
            # Lines 106-125: Handle metadata results
            for i, result in enumerate(docs[:10]):
                title = f"Risk {result['risk_id']}" if 'risk_id' in result else "Metadata Result"
                url = f"metadata://result/{i}"
                related_docs.append({"title": title, "url": url})
        
        elif docs and hasattr(docs[0], 'metadata'):
            # Lines 136-144: Handle regular documents
            for doc in docs:
                url = doc.metadata.get("url", "#")
                if os.path.exists(url):
                    url = f"local-file://{url}"
                related_docs.append({
                    "title": doc.metadata.get("title", "Unknown Title"), 
                    "url": url
                })
        
        # Line 148: Send related documents
        yield json.dumps({"related_documents": related_docs}) + '\n'
```

### 3.2 Streaming Format
The API sends Server-Sent Events (SSE) with two types of messages:
1. **Text chunks**: `"piece of response text"`
2. **Document metadata**: `{"related_documents": [...]}`

## 4. Frontend Reception

### 4.1 Streaming Response Handler
**File**: `/frontend/src/pages/fullchat/fullchat.tsx`
**Lines**: 52-147
```typescript
async function handleSubmit(text?: string) {
    // Line 64-68: Make streaming request
    const stream = await fetch(`${API_URL}api/v1/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText }),
    });
    
    // Lines 78-123: Process streaming data
    while (!done) {
        // ... read stream chunks ...
        
        // Line 91: Parse JSON from stream
        const parsed = JSON.parse(line);
        
        // Lines 112-114: Capture related documents
        if (parsed.related_documents) {
            setRelatedDocuments(parsed.related_documents);
        } else {
            // Lines 115-117: Accumulate text response
            accumulatedText += parsed;
            setCurrentMessage({ content: accumulatedText, role: 'assistant', id: uuidv4() });
        }
    }
}
```

### 4.2 Related Documents Click Handler
**File**: `/frontend/src/pages/fullchat/fullchat.tsx`
**Lines**: 25-44
```typescript
const handleFileClick = async (url: string) => {
    if (url.startsWith('metadata://')) {
        // Line 30: Handle metadata results
        alert('This is a metadata query result. Details view coming soon!');
    } else if (url.startsWith('http://') || url.startsWith('https://')) {
        // Line 33: Open external URLs in new tab
        window.open(url, '_blank', 'noopener,noreferrer');
    } else if (url.startsWith('local-file://')) {
        // Lines 35-38: Extract snippet ID from local file path
        const path = url.replace('local-file://', '');
        const snippetId = path.split('/').pop();
        window.open(`/snippet/${snippetId}`, '_blank', 'noopener,noreferrer');
    } else {
        // Lines 41-42: Default - assume it's a snippet ID
        const snippetId = url.split('/').pop();
        window.open(`/snippet/${snippetId}`, '_blank', 'noopener,noreferrer');
    }
};
```

## 5. Related Documents Display

**File**: `/frontend/src/pages/fullchat/fullchat.tsx`
**Lines**: 203-218
```jsx
<div className="bg-white border rounded-xl p-4 shadow-sm">
    <h3 className="text-md font-semibold mb-2">Related Documents</h3>
    <ul className="text-sm text-gray-600 space-y-2">
        {relatedDocuments.length > 0 ? (
            relatedDocuments.map((doc, index) => (
                <li key={index}>
                    <button onClick={() => handleFileClick(doc.url)} className="text-blue-600 underline">
                        {doc.title}
                    </button>
                </li>
            ))
        ) : (
            <li>No documents yet. Submit a request to populate this area.</li>
        )}
    </ul>
</div>
```

## 6. Snippet API & Retrieval

### 6.1 Snippet API Endpoint
**File**: `/src/api/routes/snippets.py`
**Lines**: 22-50
```python
@snippets_bp.route('/api/snippet/<doc_id>', methods=['GET'])
def get_snippet(doc_id):
    # Line 30-31: Handle file requests (redirect)
    if '.' in doc_id:
        return redirect(url_for('file_content.get_file_content', path=doc_id))
    
    # Lines 34-38: Handle RID format
    if doc_id.startswith('RID-') and len(doc_id) == 9:
        snippet = chat_service.citation_service.get_snippet_by_rid(doc_id, include_metadata=True)
    else:
        # Legacy format support
        snippet = chat_service.citation_service.get_snippet_content(doc_id, include_metadata=True)
    
    # Line 45: Return JSON response
    return jsonify(snippet)
```

### 6.2 Raw Snippet Endpoint
**File**: `/src/api/routes/snippets.py`
**Lines**: 51-71
```python
@snippets_bp.route('/api/snippet/<rid>/raw', methods=['GET'])
def get_snippet_raw(rid):
    """Get raw snippet content for RID (plain text)."""
    # Returns plain text instead of JSON
    return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
```

### 6.3 Snippet Page Component
**File**: `/frontend/src/pages/snippet/snippet.tsx`
**Lines**: 5-43
```typescript
export function SnippetPage() {
    const { fileName } = useParams<{ fileName: string }>();
    
    useEffect(() => {
        const fetchSnippet = async () => {
            // Line 13: Fetch snippet from API
            const response = await fetch(`/api/snippet/${fileName}`);
            const data = await response.json();
            setSnippet(data);
        };
        
        if (fileName) {
            fetchSnippet();
        }
    }, [fileName]);
    
    // Lines 37-42: Render snippet
    return (
        <div>
            <h1>{fileName}</h1>
            <SnippetRenderer snippet={snippet} />
        </div>
    );
}
```

## 7. Snippet Rendering

**File**: `/frontend/src/components/snippet-renderer.tsx`
**Lines**: 13-59
```typescript
export const SnippetRenderer: React.FC<SnippetRendererProps> = ({ snippet }) => {
    const { content, file_type, search_terms } = snippet;
    
    switch (file_type) {
        case 'text':
            // Lines 18-27: Plain text with highlighting
            return (
                <pre>
                    <Highlighter
                        highlightClassName="bg-yellow-200"
                        searchWords={search_terms}
                        autoEscape={true}
                        textToHighlight={content}
                    />
                </pre>
            );
        
        case 'markdown':
            // Lines 29-46: Markdown rendering
            return (
                <ReactMarkdown
                    components={{
                        p: ({ node, ...props }) => (
                            <p>
                                <Highlighter
                                    highlightClassName="bg-yellow-200"
                                    searchWords={search_terms}
                                    autoEscape={true}
                                    textToHighlight={props.children?.toString() || ''}
                                />
                            </p>
                        ),
                    }}
                >
                    {content}
                </ReactMarkdown>
            );
        
        default:
            // Lines 48-57: Default fallback
            return <pre>...</pre>;
    }
};
```

## 8. Chat Message Citation Links

**File**: `/frontend/src/pages/chat/chat.tsx`
**Lines**: 50-63
```jsx
<ReactMarkdown
    components={{
        a: ({ node, ...props }) => {
            const href = props.href || '';
            // Lines 54-57: Transform API snippet links to frontend routes
            if (href.startsWith('/api/snippet/')) {
                const fileName = href.substring('/api/snippet/'.length);
                return <a {...props} href={`/snippet/${fileName}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline" />;
            }
            // Line 58: Regular external links
            return <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline" />;
        },
    }}
>
    {msg.content}
</ReactMarkdown>
```

## Error Handling

### Backend Error Handling

1. **Missing Snippets** (`snippets.py:40-44`):
   ```python
   if not snippet or "not found" in str(snippet).lower():
       return jsonify({"error": "Snippet not found"}), 404
   ```

2. **Citation Service Errors** (`citation_service.py`):
   - Logs warnings for missing RIDs
   - Falls back to creating links anyway
   - Handles file system errors gracefully

3. **Stream Errors** (`chat.py:150-152`):
   ```python
   except Exception as e:
       logger.error(f"Error in streaming generator: {str(e)}")
       yield json.dumps(f"An error occurred: {str(e)}") + '\n'
   ```

### Frontend Error Handling

1. **Snippet Loading Errors** (`snippet.tsx:20-21`):
   ```typescript
   } catch (error) {
       setError((error as Error).message);
   }
   ```

2. **Stream Processing Errors** (`fullchat.tsx:119-121`):
   ```typescript
   } catch (err) {
       console.error('Error parsing line:', line, err);
   }
   ```

3. **Missing Documents** (`fullchat.tsx:214-216`):
   ```jsx
   ) : (
       <li>No documents yet. Submit a request to populate this area.</li>
   )}
   ```

## Testing Strategies

### Unit Tests

1. **Citation Service Tests**:
   - Test RID pattern matching
   - Test citation link generation
   - Test snippet saving functionality
   - Test edge cases (malformed RIDs, missing metadata)

2. **API Endpoint Tests**:
   - Test snippet retrieval by RID
   - Test 404 handling for missing snippets
   - Test different URL formats
   - Test streaming response format

3. **Frontend Component Tests**:
   - Test snippet renderer with different file types
   - Test related documents display
   - Test click handlers for different URL types
   - Test error states

### Integration Tests

1. **End-to-End Flow**:
   - Submit query → Receive response with citations → Click citation → View snippet
   - Test with different document types
   - Test with metadata queries
   - Test with external links

2. **Performance Tests**:
   - Test streaming with large responses
   - Test multiple concurrent snippet requests
   - Test with many related documents

## Performance Considerations

### Backend Optimizations

1. **Caching**:
   - Consider caching frequently accessed snippets
   - Implement Redis cache for snippet content
   - Cache citation mappings per session

2. **Batch Processing**:
   - Process multiple RID replacements in single pass
   - Batch snippet file writes
   - Optimize document retrieval queries

3. **Streaming Efficiency**:
   - Chunk size optimization (currently 5 words)
   - Compression for large responses
   - Connection pooling for database queries

### Frontend Optimizations

1. **Lazy Loading**:
   - Load snippets only when clicked
   - Implement virtual scrolling for long document lists
   - Prefetch snippets on hover

2. **State Management**:
   - Memoize related documents list
   - Cache snippet content in browser
   - Implement proper cleanup for streaming connections

3. **Rendering Performance**:
   - Use React.memo for snippet components
   - Debounce search term highlighting
   - Virtualize long snippet content

## Security Implications

### Backend Security

1. **Path Traversal Prevention**:
   - Validate RID format strictly
   - Sanitize file paths
   - Use safe path joining methods

2. **Content Sanitization**:
   - Escape HTML in snippet content
   - Validate JSON responses
   - Implement rate limiting on snippet API

3. **Access Control**:
   - Consider authentication for snippet access
   - Log snippet access for auditing
   - Implement CORS properly

### Frontend Security

1. **XSS Prevention**:
   - Use ReactMarkdown's safe rendering
   - Sanitize user-provided search terms
   - Validate URLs before opening

2. **CSRF Protection**:
   - Use proper headers for API requests
   - Validate origin for streaming connections
   - Implement token-based authentication

## Future Enhancements

### Feature Enhancements

1. **Rich File Format Support**:
   ```typescript
   // Add to snippet-renderer.tsx
   case 'pdf':
       return <PDFViewer url={content_url} />;
   case 'excel':
       return <ExcelPreview data={parsed_content} />;
   case 'docx':
       return <WordDocViewer content={content} />;
   ```

2. **Advanced Snippet Features**:
   - Full-text search within snippets
   - Snippet annotations and comments
   - Version history for snippets
   - Snippet collections/bookmarks

3. **UI/UX Improvements**:
   - Inline snippet preview on hover
   - Snippet comparison view
   - Export snippets to different formats
   - Mobile-responsive snippet viewer

### Technical Enhancements

1. **Real-time Updates**:
   - WebSocket support for live updates
   - Push notifications for new related documents
   - Collaborative snippet viewing

2. **Analytics Integration**:
   - Track most viewed snippets
   - User interaction heatmaps
   - Search query analysis
   - Performance metrics dashboard

3. **API Enhancements**:
   - GraphQL endpoint for flexible queries
   - Batch snippet retrieval
   - Snippet metadata API
   - Full-text search API

## Troubleshooting Guide

### Common Issues

1. **Snippets Not Loading**:
   - Check if snippet file exists in `/data/doc_snippets/`
   - Verify RID format (must be RID-#####)
   - Check API endpoint accessibility
   - Review browser console for errors

2. **Related Documents Not Appearing**:
   - Verify streaming response includes `related_documents`
   - Check state update in `fullchat.tsx`
   - Ensure documents have proper metadata
   - Check for JavaScript errors

3. **Citation Links Not Working**:
   - Verify citation pattern matching in backend
   - Check ReactMarkdown link transformation
   - Ensure proper URL routing
   - Test with different link formats

### Debug Commands

```bash
# Check if snippet file exists
ls data/doc_snippets/RID-00073.txt

# Test snippet API directly
curl http://localhost:5000/api/snippet/RID-00073

# Check streaming response
curl -N http://localhost:5000/api/v1/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "test query"}'

# Monitor citation service logs
tail -f logs/citation_service.log
```

### Log Locations

- Backend logs: Check console output or configured log files
- Frontend logs: Browser developer console
- API logs: Network tab in browser developer tools
- Citation logs: Look for "CitationService" entries

## Summary of Key Integration Points

1. **Citation Generation**: `citation_service.py:26-61` creates `[RID-#####](/snippet/RID-#####)` links
2. **Document Metadata**: `chat.py:104-148` formats document list with titles and URLs
3. **Frontend State**: `fullchat.tsx:112-114` captures `related_documents` from stream
4. **URL Routing**: `fullchat.tsx:25-44` handles different URL types (local, external, metadata)
5. **Snippet API**: `snippets.py:22-50` serves snippet content as JSON
6. **Rendering**: `snippet-renderer.tsx:13-59` displays content based on file type

This architecture ensures that every document reference is trackable, clickable, and properly rendered regardless of its source or format.

---

*Document Version: 1.0*  
*Last Updated: January 2025*  
*Author: AIRI Chatbot Development Team*