/**
 * Interactive Reference Visualization Components
 * Export all preview, panel, and viewer components
 */

export { HoverPreview } from './HoverPreview';
export { SlideoutPanel } from './SlideoutPanel';
export { EnhancedSlideoutPanel } from './EnhancedSlideoutPanel';
export { CitationLink, parseCitations } from './CitationLink';

// Viewers
export { ExcelViewer } from '../viewers/ExcelViewer';
export { WordViewer } from '../viewers/WordViewer';

// Gallery
export { CitationGallery } from '../gallery/CitationGallery';

// Context
export { PanelProvider, usePanel } from '../../context/PanelContext';

// Utilities
export { previewCache } from '../../utils/preview-cache';

// Types
export type {
  DocumentPreview,
  ExcelDocumentData,
  WordDocumentData,
  CitationGalleryItem,
  HoverPreviewProps,
  SlideoutPanelProps,
  ExcelViewerProps,
  WordViewerProps,
  CitationGalleryProps
} from '../../types/document-preview';
