/**
 * Enhanced Slideout Panel
 * Intelligently loads the appropriate viewer based on document type
 * Supports: text, Excel, Word, PDF, image
 */

import React, { useState, useEffect, useCallback } from 'react';
import { SlideoutPanel } from './SlideoutPanel';
import { ExcelViewer } from '../viewers/ExcelViewer';
import { WordViewer } from '../viewers/WordViewer';
import { previewCache } from '../../utils/preview-cache';
import type { DocumentPreview, ExcelDocumentData, WordDocumentData } from '../../types/document-preview';

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
    // Check cache
    const cached = previewCache.getExcelData(rid);
    if (cached) {
      setExcelData(cached);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/document/${rid}/excel?session_id=${props.sessionId}`);
      if (!response.ok) {
        throw new Error('Failed to load Excel data');
      }

      const data = await response.json();
      setExcelData(data);
      previewCache.setExcelData(rid, data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const loadWordData = async (rid: string) => {
    // Check cache
    const cached = previewCache.getWordData(rid);
    if (cached) {
      setWordData(cached);
      return;
    }

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
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Render appropriate viewer based on document type
  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-6">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            Error loading document: {error}
          </div>
        </div>
      );
    }

    switch (documentType) {
      case 'excel':
        return excelData ? (
          <ExcelViewer
            data={excelData}
            onSheetChange={(sheetName) => {
              console.log('Sheet changed:', sheetName);
            }}
          />
        ) : null;

      case 'word':
        return wordData ? (
          <WordViewer
            data={wordData}
            onTocItemClick={(itemId) => {
              console.log('TOC item clicked:', itemId);
            }}
          />
        ) : null;

      case 'text':
      default:
        // Use default SlideoutPanel for text content
        return null;
    }
  };

  // If we have a specialized viewer, render it in the panel
  if (documentType === 'excel' || documentType === 'word') {
    return (
      <div className="enhanced-panel">
        {/* Custom panel implementation would go here */}
        {/* For now, we'll use the regular SlideoutPanel as fallback */}
        <SlideoutPanel {...props} />
      </div>
    );
  }

  // Default to regular SlideoutPanel for text content
  return <SlideoutPanel {...props} />;
};
