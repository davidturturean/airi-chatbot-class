import React, { useEffect } from 'react';
import Highlighter from 'react-highlight-words';

interface SnippetMetadata {
  domain: string;
  subdomain?: string;
  risk_category?: string;
  entity?: string;
  intent?: string;
  timing?: string;
  description?: string;
  source_file?: string;
  row_number?: number;
  type?: string;
}

interface SnippetJSON {
  rid: string;
  title: string;
  content: string;
  metadata: SnippetMetadata;
  highlights?: string[];
  created_at: string;
}

interface SnippetModalProps {
  isOpen: boolean;
  onClose: () => void;
  rid: string | null;
  sessionId: string;
}

export const SnippetModal: React.FC<SnippetModalProps> = ({ 
  isOpen, 
  onClose, 
  rid,
  sessionId 
}) => {
  const [snippetData, setSnippetData] = React.useState<SnippetJSON | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  
  // Client-side cache for snippets to avoid refetching
  const [snippetCache, setSnippetCache] = React.useState<Record<string, SnippetJSON>>({});

  // Clear cache when session changes
  useEffect(() => {
    setSnippetCache({});
  }, [sessionId]);

  useEffect(() => {
    if (isOpen && rid) {
      fetchSnippet();
    }
  }, [isOpen, rid]);

  const fetchSnippet = async () => {
    if (!rid) return;
    
    // Check cache first
    const cacheKey = `${sessionId}-${rid}`;
    if (snippetCache[cacheKey]) {
      setSnippetData(snippetCache[cacheKey]);
      setError(null);
      return; // Use cached data, no loading needed
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/snippet/${rid}?session_id=${sessionId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch snippet');
      }
      
      const data = await response.json();
      setSnippetData(data);
      
      // Cache the successful fetch
      setSnippetCache(prev => ({
        ...prev,
        [cacheKey]: data
      }));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const renderMetadataBadge = (label: string, value: string | undefined) => {
    if (!value) return null;
    return (
      <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
        <span className="font-semibold">{label}:</span>
        <span className="ml-1">{value}</span>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Modal Content */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-gray-900">
                {loading ? 'Loading...' : (snippetData?.title || 'Document Snippet')}
              </h2>
              {snippetData && (
                <p className="mt-1 text-sm text-gray-500">
                  {snippetData.rid}
                </p>
              )}
            </div>
            <button
              onClick={onClose}
              className="ml-4 bg-white rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              aria-label="Close modal"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading && (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </div>
          )}
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              Error loading snippet: {error}
            </div>
          )}
          
          {snippetData && !loading && !error && (
            <>
              {/* Metadata badges */}
              <div className="flex flex-wrap gap-2 mb-6">
                {renderMetadataBadge('Domain', snippetData.metadata.domain)}
                {renderMetadataBadge('Category', snippetData.metadata.risk_category)}
                {renderMetadataBadge('Entity', snippetData.metadata.entity)}
                {renderMetadataBadge('Intent', snippetData.metadata.intent)}
                {renderMetadataBadge('Timing', snippetData.metadata.timing)}
              </div>
              
              {/* Description if available */}
              {snippetData.metadata.description && (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Description</h3>
                  <p className="text-sm text-gray-600">{snippetData.metadata.description}</p>
                </div>
              )}
              
              {/* Main content with highlighting */}
              <div className="prose prose-sm max-w-none">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Content</h3>
                <div className="bg-gray-50 p-4 rounded-lg text-sm">
                  {/* Check if content is JSON (for metadata results) */}
                  {snippetData.metadata?.type === 'metadata_query_result' ? (
                    <pre className="whitespace-pre-wrap font-mono text-xs">
                      {snippetData.content}
                    </pre>
                  ) : (
                    <div className="whitespace-pre-wrap">
                      {snippetData.highlights && snippetData.highlights.length > 0 ? (
                        <Highlighter
                          highlightClassName="bg-yellow-200"
                          searchWords={snippetData.highlights}
                          autoEscape={true}
                          textToHighlight={snippetData.content}
                        />
                      ) : (
                        snippetData.content
                      )}
                    </div>
                  )}
                </div>
              </div>
              
              {/* Footer metadata */}
              <div className="mt-6 pt-4 border-t border-gray-200 text-sm text-gray-500">
                {snippetData.metadata.source_file && (
                  <p>Source: {snippetData.metadata.source_file}</p>
                )}
                {snippetData.metadata.row_number && (
                  <p>Row: {snippetData.metadata.row_number}</p>
                )}
                <p>Retrieved: {new Date(snippetData.created_at).toLocaleString()}</p>
              </div>
            </>
          )}
        </div>
        
        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => {
                if (snippetData) {
                  navigator.clipboard.writeText(snippetData.content);
                  // You could add a toast notification here
                }
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              Copy Content
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};