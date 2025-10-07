/**
 * Enhanced Slideout Panel
 * Intelligently loads the appropriate viewer based on document type
 * Supports: text, Excel, Word, PDF, image
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { SlideoutPanel } from './SlideoutPanel';
import { ExcelViewer } from '../viewers/ExcelViewer';
import { WordViewer } from '../viewers/WordViewer';
import { previewCache } from '../../utils/preview-cache';
import type { ExcelDocumentData, WordDocumentData } from '../../types/document-preview';

interface EnhancedSlideoutPanelProps {
  isOpen: boolean;
  isPinned: boolean;
  rid: string | null;
  sessionId: string;
  onClose: () => void;
  onPin: () => void;
  onNavigate?: (rid: string) => void;
}

export const EnhancedSlideoutPanel: React.FC<EnhancedSlideoutPanelProps> = (props) => {
  const [documentType, setDocumentType] = useState<'text' | 'excel' | 'word' | 'pdf' | 'image' | null>(null);
  const [excelData, setExcelData] = useState<ExcelDocumentData | null>(null);
  const [wordData, setWordData] = useState<WordDocumentData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Determine document type when RID changes
  useEffect(() => {
    if (props.rid && props.isOpen) {
      determineDocumentType(props.rid);
    }
  }, [props.rid, props.isOpen]);

  // Clean up state when panel closes to prevent stale data on next open
  useEffect(() => {
    if (!props.isOpen) {
      // Panel is closing - clear all state for clean slate
      setDocumentType(null);
      setExcelData(null);
      setWordData(null);
      setLoading(false);
      setError(null);
    }
  }, [props.isOpen]);

  const determineDocumentType = async (rid: string) => {
    try {
      // Check preview cache first
      const preview = previewCache.getPreview(rid);
      if (preview) {
        setDocumentType(preview.preview_type);
        if (preview.preview_type === 'excel') {
          loadExcelData(rid);
        } else if (preview.preview_type === 'word') {
          loadWordData(rid);
        }
        return;
      }

      // Fetch document type
      const response = await fetch(`/api/document/${rid}/type?session_id=${props.sessionId}`);
      if (response.ok) {
        const data = await response.json();
        setDocumentType(data.type);

        if (data.type === 'excel') {
          loadExcelData(rid);
        } else if (data.type === 'word') {
          loadWordData(rid);
        }
      }
    } catch (err) {
      console.error('Error determining document type:', err);
      setDocumentType('text'); // Default to text
    }
  };

  const loadExcelData = async (rid: string) => {
    const startTime = performance.now();

    // Check cache first - data may have been prefetched by hover preview
    const cached = previewCache.getExcelData(rid);
    if (cached) {
      const cacheHitTime = performance.now() - startTime;
      console.log(`Excel data loaded from cache in ${cacheHitTime.toFixed(2)}ms (instant load)`);
      setExcelData(cached);
      return;
    }

    // Cache miss - need to fetch (will show loading spinner)
    console.log('Excel data not cached, fetching from server...');
    setLoading(true);
    setError(null);

    try {
      const fetchStart = performance.now();

      // Add timeout to prevent infinite waiting
      // Increased from 30s to 60s to handle large Excel files with multiple sheets
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout

      // Fetch WITH formatting enabled by default (user needs colors/bold for readability)
      // Backend now optimized: parallel processing + iter_rows + first 50 visible rows only
      // Expected performance: 2-3 seconds for 11-sheet files (down from 17+ seconds)
      const response = await fetch(`/api/document/${rid}/excel?session_id=${props.sessionId}&include_formatting=true`, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      const fetchTime = performance.now() - fetchStart;
      console.log(`Excel fetch completed in ${fetchTime.toFixed(2)}ms, status: ${response.status}`);

      if (!response.ok) {
        throw new Error(`Failed to load Excel data: ${response.status} ${response.statusText}`);
      }

      const parseStart = performance.now();
      const data = await response.json();
      const parseTime = performance.now() - parseStart;
      console.log(`Excel JSON parsing completed in ${parseTime.toFixed(2)}ms, data size: ${JSON.stringify(data).length} bytes`);

      // Enhance with source_location from preview cache if available
      const preview = previewCache.getPreview(rid);
      if (preview && preview.source_location) {
        data.source_location = preview.source_location;
      }

      setExcelData(data);
      previewCache.setExcelData(rid, data);

      const totalTime = performance.now() - startTime;
      console.log(`✅ Excel data loaded and ready to render in ${totalTime.toFixed(2)}ms`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      if (errorMessage.includes('aborted')) {
        console.error(`❌ Excel fetch timeout after 60 seconds for ${rid}`);
        setError('Excel file too large or server timeout. Please try a smaller file or contact support.');
      } else {
        console.error(`❌ Excel fetch error for ${rid}:`, errorMessage);
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadWordData = async (rid: string) => {
    const startTime = performance.now();

    // Check cache first - data may have been prefetched by hover preview
    const cached = previewCache.getWordData(rid);
    if (cached) {
      const cacheHitTime = performance.now() - startTime;
      console.log(`Word data loaded from cache in ${cacheHitTime.toFixed(2)}ms (instant load)`);
      setWordData(cached);
      return;
    }

    // Cache miss - need to fetch (will show loading spinner)
    console.log('Word data not cached, fetching from server...');
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/document/${rid}/word?session_id=${props.sessionId}`);
      if (!response.ok) {
        throw new Error('Failed to load Word data');
      }

      const data = await response.json();
      setWordData(data);
      previewCache.setWordData(rid, data);

      const totalTime = performance.now() - startTime;
      console.log(`Word data fetched in ${totalTime.toFixed(2)}ms`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };


  // Loading state
  if (loading) {
    return (
      <div className="enhanced-panel fixed inset-y-0 right-0 w-[600px] bg-white shadow-xl border-l border-gray-200 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-sm text-gray-600">
            Loading {documentType === 'excel' ? 'spreadsheet' : documentType === 'word' ? 'document' : 'content'}...
          </p>
        </motion.div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="enhanced-panel fixed inset-y-0 right-0 w-[600px] bg-white shadow-xl border-l border-gray-200 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center max-w-md px-6"
        >
          <div className="text-red-500 mb-4">
            <svg className="h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Failed to load {documentType || 'document'}
          </h3>
          <p className="text-sm text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => {
              setError(null);
              if (props.rid) {
                if (documentType === 'excel') {
                  loadExcelData(props.rid);
                } else if (documentType === 'word') {
                  loadWordData(props.rid);
                }
              }
            }}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
          >
            Try Again
          </button>
          <button
            onClick={props.onClose}
            className="ml-3 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
          >
            Close
          </button>
        </motion.div>
      </div>
    );
  }

  // Excel viewer
  if (documentType === 'excel' && excelData) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="enhanced-panel fixed inset-y-0 right-0 w-[800px] bg-white shadow-xl border-l border-gray-200"
      >
        <div className="h-full flex flex-col">
          {/* Header with close/pin buttons */}
          <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                <svg className="h-3 w-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
                </svg>
                Excel
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={props.onPin}
                className={`p-2 rounded-md transition-colors ${props.isPinned ? 'bg-indigo-100 text-indigo-700' : 'text-gray-500 hover:bg-gray-100'}`}
                title={props.isPinned ? 'Unpin panel' : 'Pin panel'}
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1zm-5 8.274l-.818 2.552c-.25.78.409 1.674 1.215 1.674.233 0 .462-.057.667-.165l.952-.382a1 1 0 01.894 1.788l-.952.382A3.989 3.989 0 015 17a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L8 6.323V5a1 1 0 011-1 1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1z" />
                </svg>
              </button>
              <button
                onClick={props.onClose}
                className="p-2 text-gray-500 hover:bg-gray-100 rounded-md transition-colors"
                title="Close panel"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Excel Viewer */}
          <div className="flex-1 overflow-hidden">
            <ExcelViewer
              data={excelData}
              sourceLocation={excelData.source_location}
              onSheetChange={(sheetName) => console.log('Sheet changed:', sheetName)}
              onCellSelect={(row, col) => console.log('Cell selected:', row, col)}
              onExport={(sheetName, rows) => console.log('Export:', sheetName, rows)}
            />
          </div>
        </div>
      </motion.div>
    );
  }

  // Word viewer
  if (documentType === 'word' && wordData) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="enhanced-panel fixed inset-y-0 right-0 w-[900px] bg-white shadow-xl border-l border-gray-200"
      >
        <div className="h-full flex flex-col">
          {/* Header with close/pin buttons */}
          <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                <svg className="h-3 w-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                </svg>
                Word
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={props.onPin}
                className={`p-2 rounded-md transition-colors ${props.isPinned ? 'bg-indigo-100 text-indigo-700' : 'text-gray-500 hover:bg-gray-100'}`}
                title={props.isPinned ? 'Unpin panel' : 'Pin panel'}
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1zm-5 8.274l-.818 2.552c-.25.78.409 1.674 1.215 1.674.233 0 .462-.057.667-.165l.952-.382a1 1 0 01.894 1.788l-.952.382A3.989 3.989 0 015 17a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L8 6.323V5a1 1 0 011-1 1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1z" />
                </svg>
              </button>
              <button
                onClick={props.onClose}
                className="p-2 text-gray-500 hover:bg-gray-100 rounded-md transition-colors"
                title="Close panel"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Word Viewer */}
          <div className="flex-1 overflow-hidden">
            <WordViewer
              data={wordData}
              onTocItemClick={(itemId) => console.log('TOC click:', itemId)}
              onSearch={(query) => console.log('Search:', query)}
            />
          </div>
        </div>
      </motion.div>
    );
  }

  // Default to regular SlideoutPanel for text content
  return <SlideoutPanel {...props} />;
};
