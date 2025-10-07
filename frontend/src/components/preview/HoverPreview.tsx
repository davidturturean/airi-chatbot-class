/**
 * Phase 1: Hover Preview Component
 * Airtable-inspired hover card that shows document previews on citation hover
 * Performance target: <200ms preview load, 300ms hover delay
 */

import React, { useState, useEffect, useCallback } from 'react';
import * as HoverCard from '@radix-ui/react-hover-card';
import { previewCache } from '../../utils/preview-cache';
import type { DocumentPreview, HoverPreviewProps } from '../../types/document-preview';

export const HoverPreview: React.FC<HoverPreviewProps> = ({
  rid,
  sessionId,
  children,
  delay = 300,
  onOpen,
  onClose,
  onOpenFull
}) => {
  const [preview, setPreview] = useState<DocumentPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [, setIsOpen] = useState(false);

  // Set session ID in cache
  useEffect(() => {
    previewCache.setSessionId(sessionId);
  }, [sessionId]);

  const fetchPreview = useCallback(async () => {
    if (!rid || !sessionId) return;

    // Check cache first
    const cached = previewCache.getPreview(rid);
    if (cached) {
      setPreview(cached);
      setError(null);

      // Trigger background prefetch for Excel/Word documents
      // This happens AFTER showing the preview (non-blocking)
      triggerBackgroundPrefetch(cached);

      return;
    }

    setLoading(true);
    setError(null);

    const startTime = performance.now();

    try {
      const response = await fetch(`/api/document/${rid}/preview?session_id=${sessionId}`);

      if (!response.ok) {
        throw new Error('Failed to fetch preview');
      }

      const data = await response.json();

      const loadTime = performance.now() - startTime;
      if (loadTime > 200) {
        console.warn(`Preview load time exceeded target: ${loadTime.toFixed(2)}ms`);
      }

      setPreview(data);
      previewCache.setPreview(rid, data);

      // Trigger background prefetch for Excel/Word documents
      // This happens AFTER showing the preview (non-blocking)
      triggerBackgroundPrefetch(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [rid, sessionId]);

  /**
   * Trigger background prefetch for Excel/Word documents when hover preview loads.
   * This is non-blocking and doesn't affect the hover preview display.
   * By the time user clicks, data should already be loaded.
   */
  const triggerBackgroundPrefetch = (preview: DocumentPreview) => {
    if (!preview || !rid) return;

    // Only prefetch for document types that need heavy parsing
    if (preview.preview_type === 'excel') {
      console.log(`Hover preview detected Excel document, triggering background prefetch for ${rid}`);
      // Don't await - let it run in background
      previewCache.prefetchExcelData(rid).catch((err) => {
        console.warn('Excel prefetch failed (non-critical):', err);
      });
    } else if (preview.preview_type === 'word') {
      console.log(`Hover preview detected Word document, triggering background prefetch for ${rid}`);
      // Don't await - let it run in background
      previewCache.prefetchWordData(rid).catch((err) => {
        console.warn('Word prefetch failed (non-critical):', err);
      });
    }
  };

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open);

    if (open) {
      fetchPreview();
      onOpen?.();
    } else {
      onClose?.();
    }
  };

  return (
    <HoverCard.Root
      openDelay={delay}
      closeDelay={150}
      onOpenChange={handleOpenChange}
    >
      <HoverCard.Trigger asChild>
        {children}
      </HoverCard.Trigger>

      <HoverCard.Portal>
        <HoverCard.Content
          className="hover-preview-content"
          side="top"
          sideOffset={5}
          align="start"
          style={{
            width: '400px',
            maxWidth: '90vw',
            zIndex: 9999
          }}
        >
          <div className="bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden">
            {loading && (
              <div className="p-6 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              </div>
            )}

            {error && (
              <div className="p-6">
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                  Failed to load preview: {error}
                </div>
              </div>
            )}

            {preview && !loading && !error && (
              <>
                {/* Header */}
                <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-semibold text-gray-900 truncate">
                        {preview.title}
                      </h3>
                      <p className="text-xs text-gray-500 mt-0.5">{preview.rid}</p>
                    </div>
                    <div className="ml-3 flex-shrink-0">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        preview.preview_type === 'excel' ? 'bg-green-100 text-green-800' :
                        preview.preview_type === 'word' ? 'bg-blue-100 text-blue-800' :
                        preview.preview_type === 'pdf' ? 'bg-red-100 text-red-800' :
                        preview.preview_type === 'image' ? 'bg-purple-100 text-purple-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {preview.preview_type === 'excel' && (
                          <svg className="h-3 w-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
                          </svg>
                        )}
                        {preview.preview_type === 'word' && (
                          <svg className="h-3 w-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                          </svg>
                        )}
                        {preview.preview_type === 'pdf' && (
                          <svg className="h-3 w-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                          </svg>
                        )}
                        {preview.preview_type === 'image' && (
                          <svg className="h-3 w-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                          </svg>
                        )}
                        {preview.preview_type}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Metadata Tags */}
                {(preview.metadata.domain || preview.metadata.entity || preview.metadata.risk_category) && (
                  <div className="px-4 py-2 border-b border-gray-100 bg-white">
                    <div className="flex flex-wrap gap-1.5">
                      {preview.metadata.domain && (
                        <span
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700 cursor-help"
                          title="AI Risk Domain"
                        >
                          {preview.metadata.domain}
                        </span>
                      )}
                      {preview.metadata.entity && (
                        <span
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700 cursor-help"
                          title="Entity affected by this risk"
                        >
                          {preview.metadata.entity}
                        </span>
                      )}
                      {preview.metadata.risk_category && (
                        <span
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-700 cursor-help"
                          title="Risk category"
                        >
                          {preview.metadata.risk_category}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Content Preview */}
                <div className="px-4 py-3 max-h-48 overflow-y-auto">
                  <div className="text-sm text-gray-700 whitespace-pre-wrap line-clamp-6">
                    {preview.content.substring(0, 500)}
                    {preview.content.length > 500 && '...'}
                  </div>
                </div>

                {/* Footer Actions */}
                <div className="px-4 py-2 border-t border-gray-100 bg-gray-50">
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    {onOpenFull ? (
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          onOpenFull();
                        }}
                        className="text-indigo-600 hover:text-indigo-800 font-medium cursor-pointer hover:underline"
                      >
                        Click to open full view
                      </button>
                    ) : (
                      <span>Click to open full view</span>
                    )}
                    <span className="font-medium">⌘K to search</span>
                  </div>
                </div>
              </>
            )}
          </div>

          <HoverCard.Arrow className="fill-white" />
        </HoverCard.Content>
      </HoverCard.Portal>
    </HoverCard.Root>
  );
};
