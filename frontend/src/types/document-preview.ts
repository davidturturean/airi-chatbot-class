/**
 * TypeScript interfaces for Interactive Reference Visualization System
 * Inspired by Airtable's rich preview capabilities
 */

export interface DocumentMetadata {
  domain?: string;
  subdomain?: string;
  risk_category?: string;
  entity?: string;
  intent?: string;
  timing?: string;
  description?: string;
  source_file?: string;
  row_number?: number;
  type?: string;
  file_type?: 'excel' | 'word' | 'pdf' | 'text' | 'image' | 'other';
  file_size?: number;
  last_modified?: string;
  sheet_count?: number;
  page_count?: number;
}

export interface DocumentPreview {
  rid: string;
  title: string;
  content: string;
  metadata: DocumentMetadata;
  highlights?: string[];
  created_at: string;
  preview_type: 'text' | 'excel' | 'word' | 'pdf' | 'image';
  thumbnail?: string;
}

export interface ExcelSheetData {
  sheet_name: string;
  columns: ExcelColumn[];
  rows: Record<string, any>[];
  total_rows: number;
  has_more: boolean;
}

export interface ExcelColumn {
  key: string;
  name: string;
  width?: number;
  resizable?: boolean;
  sortable?: boolean;
  filterable?: boolean;
}

export interface ExcelDocumentData {
  rid: string;
  title: string;
  sheets: ExcelSheetData[];
  active_sheet: string;
  metadata: DocumentMetadata;
}

export interface WordDocumentData {
  rid: string;
  title: string;
  html_content: string;
  toc?: TableOfContentsItem[];
  metadata: DocumentMetadata;
  word_count?: number;
  page_count?: number;
}

export interface TableOfContentsItem {
  id: string;
  title: string;
  level: number;
  children?: TableOfContentsItem[];
}

export interface CitationGalleryItem {
  rid: string;
  title: string;
  preview_type: 'text' | 'excel' | 'word' | 'pdf' | 'image';
  thumbnail?: string;
  metadata: DocumentMetadata;
  relevance_score?: number;
  created_at: string;
}

export interface CitationGalleryData {
  items: CitationGalleryItem[];
  total_count: number;
  filters: {
    domains: string[];
    file_types: string[];
    entities: string[];
    risk_categories: string[];
  };
}

export interface PanelState {
  isOpen: boolean;
  isPinned: boolean;
  currentRid: string | null;
  documentType: 'text' | 'excel' | 'word' | 'pdf' | 'image' | null;
  history: string[];
  historyIndex: number;
}

export interface HoverPreviewProps {
  rid: string;
  sessionId: string;
  children: React.ReactNode;
  delay?: number;
  onOpen?: () => void;
  onClose?: () => void;
}

export interface SlideoutPanelProps {
  isOpen: boolean;
  isPinned: boolean;
  rid: string | null;
  sessionId: string;
  onClose: () => void;
  onPin: () => void;
  onNavigate?: (rid: string) => void;
}

export interface ExcelViewerProps {
  data: ExcelDocumentData;
  onSheetChange?: (sheetName: string) => void;
  onCellSelect?: (row: number, column: string) => void;
  onExport?: (sheetName: string, filteredData: any[]) => void;
}

export interface WordViewerProps {
  data: WordDocumentData;
  onTocItemClick?: (itemId: string) => void;
  onSearch?: (query: string) => void;
}

export interface CitationGalleryProps {
  sessionId: string;
  items?: CitationGalleryItem[];
  onItemClick: (rid: string) => void;
  filters?: {
    domain?: string;
    file_type?: string;
    entity?: string;
    risk_category?: string;
  };
  groupBy?: 'domain' | 'file_type' | 'entity' | 'none';
}

// API Response Types
export interface PreviewApiResponse {
  success: boolean;
  data?: DocumentPreview;
  error?: string;
}

export interface ExcelApiResponse {
  success: boolean;
  data?: ExcelDocumentData;
  error?: string;
}

export interface WordApiResponse {
  success: boolean;
  data?: WordDocumentData;
  error?: string;
}

export interface GalleryApiResponse {
  success: boolean;
  data?: CitationGalleryData;
  error?: string;
}

// Cache Management
export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiry: number;
}

export interface DocumentCache {
  previews: Map<string, CacheEntry<DocumentPreview>>;
  excelData: Map<string, CacheEntry<ExcelDocumentData>>;
  wordData: Map<string, CacheEntry<WordDocumentData>>;
  gallery: Map<string, CacheEntry<CitationGalleryData>>;
}

// Performance Metrics
export interface PerformanceMetrics {
  preview_load_time: number;
  panel_open_time: number;
  excel_render_time: number;
  word_render_time: number;
  cache_hit_rate: number;
}
