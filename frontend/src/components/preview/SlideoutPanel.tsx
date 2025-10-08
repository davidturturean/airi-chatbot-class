/**
 * Phase 2: Slideout Panel Component
 * Airtable-inspired slide-out panel for detailed document viewing
 * Performance target: <300ms panel open animation
 * Features: Pin, navigation history, keyboard shortcuts
 */

import React, { useState, useEffect, useRef } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import * as ScrollArea from '@radix-ui/react-scroll-area';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Lock, Unlock, ChevronLeft, ChevronRight, Download, Copy } from 'lucide-react';
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
  const [previewData, setPreviewData] = useState<DocumentPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [showPinToast, setShowPinToast] = useState(false);
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
      setPreviewData(cached);
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

      setPreviewData(data);
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

      // ESC to unpin first if pinned, then close if unpinned
      if (e.key === 'Escape') {
        if (isPinned) {
          // First ESC press: unpin the panel
          onPin(); // Toggle to unpin
          setShowPinToast(true);
          setTimeout(() => setShowPinToast(false), 2000);
        } else {
          // Second ESC press (or first if already unpinned): close the panel
          onClose();
        }
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
      if ((e.metaKey || e.ctrlKey) && e.key === 'c' && previewData) {
        navigator.clipboard.writeText(previewData.content);
      }
    };

    window.document.addEventListener('keydown', handleKeyDown);
    return () => window.document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isPinned, historyIndex, history, previewData, onClose, onPin, onNavigate]);

  const handleCopyContent = () => {
    if (previewData) {
      const cleanedContent = parseDocumentContent(previewData.content);
      navigator.clipboard.writeText(cleanedContent);
      // Show a brief success indication
      setShowPinToast(true);
      setTimeout(() => setShowPinToast(false), 2000);
    }
  };

  const handlePinClick = () => {
    onPin();
    setShowPinToast(true);
    setTimeout(() => setShowPinToast(false), 2000);
  };

  const handleDownload = () => {
    if (!previewData) return;

    // Parse and clean content for download
    const cleanedContent = parseDocumentContent(previewData.content);

    // Create a well-formatted document with metadata
    const downloadContent = `${previewData.title}
${previewData.rid}

${previewData.metadata.domain ? `Domain: ${previewData.metadata.domain}\n` : ''}${previewData.metadata.subdomain ? `Sub-domain: ${previewData.metadata.subdomain}\n` : ''}${previewData.metadata.risk_category ? `Risk Category: ${previewData.metadata.risk_category}\n` : ''}${previewData.metadata.entity ? `Entity: ${previewData.metadata.entity}\n` : ''}${previewData.metadata.timing ? `Timing: ${previewData.metadata.timing}\n` : ''}${previewData.metadata.intent ? `Intent: ${previewData.metadata.intent}\n` : ''}
${previewData.metadata.description ? `Description:\n${previewData.metadata.description}\n\n` : ''}
Content:
${cleanedContent}

${previewData.metadata.source_file ? `\nSource: ${previewData.metadata.source_file}` : ''}
`;

    const blob = new Blob([downloadContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = window.document.createElement('a');
    a.href = url;
    a.download = `${previewData.rid}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Helper function to parse document content and remove metadata lines
  const parseDocumentContent = (content: string): string => {
    if (!content) return '';

    const lines = content.split('\n');
    const contentLines: string[] = [];
    let inContentSection = false;

    for (const line of lines) {
      const trimmed = line.trim();

      // Skip metadata lines
      if (
        trimmed.startsWith('Repository ID:') ||
        trimmed.startsWith('Source:') ||
        trimmed.startsWith('Domain:') ||
        trimmed.startsWith('Sub-domain:') ||
        trimmed.startsWith('Risk Category:') ||
        trimmed.startsWith('Risk Subcategory:') ||
        trimmed.startsWith('Entity:') ||
        trimmed.startsWith('Intent:') ||
        trimmed.startsWith('Timing:') ||
        trimmed.startsWith('Description:') ||
        trimmed.startsWith('Title:')
      ) {
        continue;
      }

      // Mark when we hit the content section
      if (trimmed === 'Content:') {
        inContentSection = true;
        continue;
      }

      // Add content lines
      if (inContentSection || contentLines.length > 0 || trimmed) {
        contentLines.push(line);
      }
    }

    return contentLines.join('\n').trim();
  };

  // Handle close action - unpins if pinned, then closes
  const handleClose = () => {
    if (isPinned) {
      onPin(); // Unpin first
    }
    onClose(); // Then close
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <Dialog.Root open={isOpen} modal={false}>
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
                        {loading ? 'Loading...' : (previewData?.title || 'Document')}
                      </Dialog.Title>
                      {previewData && (
                        <Dialog.Description className="mt-1 text-sm text-gray-500">
                          {previewData.rid}
                        </Dialog.Description>
                      )}
                    </div>

                    <div className="ml-4 flex items-center space-x-2">
                      {/* History navigation buttons */}
                      {history.length > 1 && (
                        <>
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
                            aria-label="Previous in history"
                            title={`Previous document in history (${historyIndex}/${history.length - 1})`}
                          >
                            <ChevronLeft className="h-5 w-5" />
                          </button>

                          <span className="text-xs text-gray-400 font-medium min-w-[3ch] text-center">
                            {historyIndex + 1}/{history.length}
                          </span>

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
                            aria-label="Next in history"
                            title={`Next document in history (${historyIndex + 2}/${history.length})`}
                          >
                            <ChevronRight className="h-5 w-5" />
                          </button>
                        </>
                      )}

                      {/* Pin button */}
                      <button
                        onClick={handlePinClick}
                        className={`p-2 rounded-md transition-all ${
                          isPinned
                            ? 'text-indigo-600 bg-indigo-100 hover:bg-indigo-200 ring-2 ring-indigo-200'
                            : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                        }`}
                        aria-label={isPinned ? 'Unpin panel' : 'Pin panel'}
                        title={isPinned ? 'Pinned - Panel stays open (⌘P to unpin)' : 'Pin to keep panel open (⌘P)'}
                      >
                        {isPinned ? (
                          <Lock className="h-5 w-5" />
                        ) : (
                          <Unlock className="h-5 w-5" />
                        )}
                      </button>

                      {/* Close button */}
                      <Dialog.Close asChild>
                        <button
                          onClick={handleClose}
                          className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100 transition-colors"
                          aria-label="Close panel"
                          title={isPinned ? 'Close and unpin' : 'Close (Esc)'}
                        >
                          <X className="h-5 w-5" />
                        </button>
                      </Dialog.Close>
                    </div>
                  </div>

                  {/* Metadata tags */}
                  {previewData && (previewData.metadata.domain || previewData.metadata.entity || previewData.metadata.risk_category) && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {previewData.metadata.domain && (
                        <span
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700 cursor-help"
                          title="AI Risk Domain - The primary category of AI risk"
                        >
                          Domain: {previewData.metadata.domain}
                        </span>
                      )}
                      {previewData.metadata.subdomain && (
                        <span
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-50 text-purple-600 cursor-help"
                          title="Specific sub-category within the risk domain"
                        >
                          {previewData.metadata.subdomain}
                        </span>
                      )}
                      {previewData.metadata.entity && (
                        <span
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 cursor-help"
                          title="Entity affected by this risk (Human, AI, or both)"
                        >
                          Entity: {previewData.metadata.entity}
                        </span>
                      )}
                      {previewData.metadata.risk_category && (
                        <span
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-700 cursor-help"
                          title="Broader risk category classification"
                        >
                          {previewData.metadata.risk_category}
                        </span>
                      )}
                      {previewData.metadata.timing && (
                        <span
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700 cursor-help"
                          title="When this risk occurs (Pre-deployment or Post-deployment)"
                        >
                          {previewData.metadata.timing}
                        </span>
                      )}
                      {previewData.metadata.intent && (
                        <span
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700 cursor-help"
                          title="Whether the risk is intentional or unintentional"
                        >
                          {previewData.metadata.intent}
                        </span>
                      )}
                      <span
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700 cursor-help"
                        title="Document type"
                      >
                        {previewData.preview_type}
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

                      {previewData && !loading && !error && (
                        <>
                          {/* Description */}
                          {previewData.metadata.description && (
                            <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
                              <h3 className="text-sm font-semibold text-blue-900 mb-2">Description</h3>
                              <p className="text-sm text-blue-800">{previewData.metadata.description}</p>
                            </div>
                          )}

                          {/* Main content */}
                          <div className="prose prose-sm max-w-none">
                            <div className="bg-white p-4 rounded-lg border border-gray-200">
                              <div className="whitespace-pre-wrap font-sans text-sm text-gray-700 leading-relaxed">
                                {parseDocumentContent(previewData.content)}
                              </div>
                            </div>
                          </div>

                          {/* Expandable metadata section */}
                          <details className="mt-4 group">
                            <summary className="cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors flex items-center gap-2">
                              <svg className="w-4 h-4 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                              View Full Metadata
                            </summary>
                            <div className="mt-3 p-4 bg-gray-50 rounded-lg border border-gray-200 text-sm text-gray-600 space-y-2">
                              {previewData.metadata.domain && (
                                <p><span className="font-medium">Domain:</span> {previewData.metadata.domain}</p>
                              )}
                              {previewData.metadata.subdomain && (
                                <p><span className="font-medium">Sub-domain:</span> {previewData.metadata.subdomain}</p>
                              )}
                              {previewData.metadata.risk_category && (
                                <p><span className="font-medium">Risk Category:</span> {previewData.metadata.risk_category}</p>
                              )}
                              {previewData.metadata.entity && (
                                <p><span className="font-medium">Entity:</span> {previewData.metadata.entity}</p>
                              )}
                              {previewData.metadata.intent && (
                                <p><span className="font-medium">Intent:</span> {previewData.metadata.intent}</p>
                              )}
                              {previewData.metadata.timing && (
                                <p><span className="font-medium">Timing:</span> {previewData.metadata.timing}</p>
                              )}
                              {previewData.metadata.source_file && (
                                <p><span className="font-medium">Source File:</span> {previewData.metadata.source_file}</p>
                              )}
                              {previewData.metadata.row_number && (
                                <p><span className="font-medium">Row Number:</span> {previewData.metadata.row_number}</p>
                              )}
                              <p><span className="font-medium">Retrieved:</span> {new Date(previewData.created_at).toLocaleString()}</p>
                            </div>
                          </details>
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
                      to pin {isPinned && '• '}
                      {isPinned && (
                        <>
                          <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-200 rounded">
                            ESC
                          </kbd>{' '}
                          to unpin
                        </>
                      )}
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

                {/* Toast notification */}
                <AnimatePresence>
                  {showPinToast && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 20 }}
                      className="absolute bottom-20 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-medium z-50"
                    >
                      {isPinned ? 'Panel pinned' : 'Panel unpinned'}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
      )}
    </AnimatePresence>
  );
};
