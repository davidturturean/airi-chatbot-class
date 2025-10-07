/**
 * Phase 2: Slideout Panel Component
 * Airtable-inspired slide-out panel for detailed document viewing
 * Performance target: <300ms panel open animation
 * Features: Pin, navigation history, keyboard shortcuts
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import * as ScrollArea from '@radix-ui/react-scroll-area';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Pin, PinOff, ChevronLeft, ChevronRight, Download, Copy } from 'lucide-react';
import { previewCache } from '../../utils/preview-cache';
import type { DocumentPreview, SlideoutPanelProps } from '../../types/document-preview';

export const SlideoutPanel: React.FC<SlideoutPanelProps> = ({
  isOpen,
  isPinned,
  rid,
  sessionId,
  onClose,
  onPin,
  onNavigate
}) => {
  const [document, setDocument] = useState<DocumentPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const panelRef = useRef<HTMLDivElement>(null);

  // Set session ID in cache
  useEffect(() => {
    previewCache.setSessionId(sessionId);
  }, [sessionId]);

  // Fetch document data when RID changes
  useEffect(() => {
    if (rid && isOpen) {
      fetchDocument(rid);

      // Add to history if it's a new navigation
      if (history[historyIndex] !== rid) {
        const newHistory = history.slice(0, historyIndex + 1);
        newHistory.push(rid);
        setHistory(newHistory);
        setHistoryIndex(newHistory.length - 1);
      }
    }
  }, [rid, isOpen]);

  const fetchDocument = async (documentRid: string) => {
    if (!documentRid || !sessionId) return;

    // Check cache first
    const cached = previewCache.getPreview(documentRid);
    if (cached) {
      setDocument(cached);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    const startTime = performance.now();

    try {
      const response = await fetch(`/api/document/${documentRid}/preview?session_id=${sessionId}`);

      if (!response.ok) {
        throw new Error('Failed to fetch document');
      }

      const data = await response.json();

      const loadTime = performance.now() - startTime;
      if (loadTime > 300) {
        console.warn(`Panel load time exceeded target: ${loadTime.toFixed(2)}ms`);
      }

      setDocument(data);
      previewCache.setPreview(documentRid, data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      // ESC to close (if not pinned)
      if (e.key === 'Escape' && !isPinned) {
        onClose();
      }

      // Cmd/Ctrl + P to pin/unpin
      if ((e.metaKey || e.ctrlKey) && e.key === 'p') {
        e.preventDefault();
        onPin();
      }

      // Left arrow for previous in history
      if (e.key === 'ArrowLeft' && historyIndex > 0) {
        const prevRid = history[historyIndex - 1];
        setHistoryIndex(historyIndex - 1);
        if (onNavigate) {
          onNavigate(prevRid);
        }
      }

      // Right arrow for next in history
      if (e.key === 'ArrowRight' && historyIndex < history.length - 1) {
        const nextRid = history[historyIndex + 1];
        setHistoryIndex(historyIndex + 1);
        if (onNavigate) {
          onNavigate(nextRid);
        }
      }

      // Cmd/Ctrl + C to copy content
      if ((e.metaKey || e.ctrlKey) && e.key === 'c' && document) {
        navigator.clipboard.writeText(document.content);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isPinned, historyIndex, history, document, onClose, onPin, onNavigate]);

  const handleCopyContent = () => {
    if (document) {
      navigator.clipboard.writeText(document.content);
      // TODO: Add toast notification
    }
  };

  const handleDownload = () => {
    if (!document) return;

    const blob = new Blob([document.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = window.document.createElement('a');
    a.href = url;
    a.download = `${document.rid}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <Dialog.Root open={isOpen} onOpenChange={(open) => !open && !isPinned && onClose()}>
          <Dialog.Portal>
            {/* Backdrop */}
            <Dialog.Overlay asChild>
              <motion.div
                className="fixed inset-0 bg-black/30 z-40"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                onClick={() => !isPinned && onClose()}
              />
            </Dialog.Overlay>

            {/* Panel */}
            <Dialog.Content asChild>
              <motion.div
                ref={panelRef}
                className="fixed right-0 top-0 h-full w-full max-w-2xl bg-white shadow-2xl z-50 flex flex-col"
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '100%' }}
                transition={{
                  type: 'spring',
                  damping: 30,
                  stiffness: 300,
                  duration: 0.3
                }}
              >
                {/* Header */}
                <div className="flex-shrink-0 px-6 py-4 border-b border-gray-200 bg-white">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <Dialog.Title className="text-lg font-semibold text-gray-900 truncate">
                        {loading ? 'Loading...' : (document?.title || 'Document')}
                      </Dialog.Title>
                      {document && (
                        <Dialog.Description className="mt-1 text-sm text-gray-500">
                          {document.rid}
                        </Dialog.Description>
                      )}
                    </div>

                    <div className="ml-4 flex items-center space-x-2">
                      {/* Navigation buttons */}
                      <button
                        onClick={() => {
                          if (historyIndex > 0) {
                            const prevRid = history[historyIndex - 1];
                            setHistoryIndex(historyIndex - 1);
                            onNavigate?.(prevRid);
                          }
                        }}
                        disabled={historyIndex <= 0}
                        className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed rounded-md hover:bg-gray-100 transition-colors"
                        aria-label="Previous document"
                      >
                        <ChevronLeft className="h-5 w-5" />
                      </button>

                      <button
                        onClick={() => {
                          if (historyIndex < history.length - 1) {
                            const nextRid = history[historyIndex + 1];
                            setHistoryIndex(historyIndex + 1);
                            onNavigate?.(nextRid);
                          }
                        }}
                        disabled={historyIndex >= history.length - 1}
                        className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed rounded-md hover:bg-gray-100 transition-colors"
                        aria-label="Next document"
                      >
                        <ChevronRight className="h-5 w-5" />
                      </button>

                      {/* Pin button */}
                      <button
                        onClick={onPin}
                        className={`p-2 rounded-md transition-colors ${
                          isPinned
                            ? 'text-indigo-600 bg-indigo-50 hover:bg-indigo-100'
                            : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                        }`}
                        aria-label={isPinned ? 'Unpin panel' : 'Pin panel'}
                        title={isPinned ? 'Unpin (⌘P)' : 'Pin (⌘P)'}
                      >
                        {isPinned ? <Pin className="h-5 w-5" /> : <PinOff className="h-5 w-5" />}
                      </button>

                      {/* Close button */}
                      <Dialog.Close asChild>
                        <button
                          onClick={onClose}
                          className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100 transition-colors"
                          aria-label="Close panel"
                          title={isPinned ? 'Close' : 'Close (Esc)'}
                        >
                          <X className="h-5 w-5" />
                        </button>
                      </Dialog.Close>
                    </div>
                  </div>

                  {/* Metadata tags */}
                  {document && (document.metadata.domain || document.metadata.entity || document.metadata.risk_category) && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {document.metadata.domain && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                          {document.metadata.domain}
                        </span>
                      )}
                      {document.metadata.entity && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                          {document.metadata.entity}
                        </span>
                      )}
                      {document.metadata.risk_category && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-700">
                          {document.metadata.risk_category}
                        </span>
                      )}
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                        {document.preview_type}
                      </span>
                    </div>
                  )}
                </div>

                {/* Content area */}
                <div className="flex-1 overflow-hidden">
                  <ScrollArea.Root className="h-full">
                    <ScrollArea.Viewport className="h-full px-6 py-4">
                      {loading && (
                        <div className="flex items-center justify-center h-64">
                          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                        </div>
                      )}

                      {error && (
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
                          Error loading document: {error}
                        </div>
                      )}

                      {document && !loading && !error && (
                        <>
                          {/* Description */}
                          {document.metadata.description && (
                            <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
                              <h3 className="text-sm font-semibold text-blue-900 mb-2">Description</h3>
                              <p className="text-sm text-blue-800">{document.metadata.description}</p>
                            </div>
                          )}

                          {/* Main content */}
                          <div className="prose prose-sm max-w-none">
                            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                              <pre className="whitespace-pre-wrap font-sans text-sm text-gray-700">
                                {document.content}
                              </pre>
                            </div>
                          </div>

                          {/* Footer metadata */}
                          <div className="mt-6 pt-4 border-t border-gray-200 text-sm text-gray-500 space-y-1">
                            {document.metadata.source_file && (
                              <p>
                                <span className="font-medium">Source:</span> {document.metadata.source_file}
                              </p>
                            )}
                            {document.metadata.row_number && (
                              <p>
                                <span className="font-medium">Row:</span> {document.metadata.row_number}
                              </p>
                            )}
                            <p>
                              <span className="font-medium">Retrieved:</span>{' '}
                              {new Date(document.created_at).toLocaleString()}
                            </p>
                          </div>
                        </>
                      )}
                    </ScrollArea.Viewport>
                    <ScrollArea.Scrollbar orientation="vertical" className="w-2.5 bg-gray-100">
                      <ScrollArea.Thumb className="bg-gray-400 rounded-full" />
                    </ScrollArea.Scrollbar>
                  </ScrollArea.Root>
                </div>

                {/* Footer actions */}
                <div className="flex-shrink-0 px-6 py-4 border-t border-gray-200 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="text-xs text-gray-500">
                      <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-200 rounded">
                        ⌘P
                      </kbd>{' '}
                      to pin
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={handleCopyContent}
                        className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <Copy className="h-4 w-4 mr-2" />
                        Copy
                      </button>
                      <button
                        onClick={handleDownload}
                        className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
      )}
    </AnimatePresence>
  );
};
