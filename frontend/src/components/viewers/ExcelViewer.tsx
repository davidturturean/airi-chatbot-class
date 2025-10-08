/**
 * Phase 3: Excel Interactive Viewer - ENHANCED
 * Interactive spreadsheet viewer with:
 * - Smart navigation to cited cells
 * - Cell formatting preservation
 * - Zoom controls
 * - Context-aware search (scroll + highlight, not filter)
 * Performance target: <500ms Excel render time
 */

import React, { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import DataGrid, { Column, SortColumn, RenderCellProps } from 'react-data-grid';
import * as Tabs from '@radix-ui/react-tabs';
import { Search, Download, ZoomIn, ZoomOut } from 'lucide-react';
import type { ExcelViewerProps, CellFormatting } from '../../types/document-preview';
import 'react-data-grid/lib/styles.css';

/**
 * Hook for loading Excel formatting chunks in the background.
 * Implements progressive enhancement: first 100 rows load immediately,
 * additional formatting loads in background without blocking UI.
 */
const useFormattingChunks = (
  rid: string,
  sessionId: string,
  activeSheet: string,
  totalRows: number,
  initialFormatting: Record<string, CellFormatting>
) => {
  const [formatting, setFormatting] = useState(initialFormatting);
  const [loadedChunks, setLoadedChunks] = useState<Set<number>>(new Set([0])); // Chunk 0 already loaded
  const [isLoadingChunk, setIsLoadingChunk] = useState(false);
  const CHUNK_SIZE = 100;

  // Reset when sheet changes
  useEffect(() => {
    setFormatting(initialFormatting);
    setLoadedChunks(new Set([0]));
  }, [activeSheet, initialFormatting]);

  const loadChunk = useCallback(async (chunkIndex: number) => {
    if (loadedChunks.has(chunkIndex) || isLoadingChunk) {
      return; // Already loaded or loading
    }

    setIsLoadingChunk(true);
    const startRow = chunkIndex * CHUNK_SIZE;
    const endRow = Math.min(startRow + CHUNK_SIZE, totalRows);

    try {
      const response = await fetch(
        `/api/document/${rid}/excel/formatting-chunk?` +
        `session_id=${sessionId}&sheet=${encodeURIComponent(activeSheet)}&start_row=${startRow}&end_row=${endRow}`,
        { signal: AbortSignal.timeout(10000) } // 10s timeout
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      // Debug: Log what's in the incoming chunk
      console.log(
        `📦 Chunk ${chunkIndex} received: ${Object.keys(data.formatting || {}).length} formatting keys`
      );

      // Merge new formatting into existing formatting
      setFormatting(prev => {
        const prevCount = Object.keys(prev).length;
        const newFormatting = { ...prev, ...data.formatting };
        const afterCount = Object.keys(newFormatting).length;

        console.log(
          `🔀 Merging chunk ${chunkIndex}: ` +
          `${prevCount} existing + ${Object.keys(data.formatting || {}).length} new = ${afterCount} total`
        );

        return newFormatting;
      });

      setLoadedChunks(prev => new Set(prev).add(chunkIndex));
      console.log(
        `✅ Loaded formatting chunk ${chunkIndex} (rows ${startRow}-${endRow}): ` +
        `${data.chunk_size} cells in ${data.extraction_time_ms}ms`
      );

    } catch (error) {
      console.error(`❌ Failed to load chunk ${chunkIndex}:`, error);
    } finally {
      setIsLoadingChunk(false);
    }
  }, [rid, sessionId, activeSheet, totalRows, loadedChunks, isLoadingChunk]);

  // Auto-load chunks in background
  useEffect(() => {
    if (totalRows <= CHUNK_SIZE) {
      // Small file, all formatting already loaded
      return;
    }

    const totalChunks = Math.ceil(totalRows / CHUNK_SIZE);
    let currentChunk = 1; // Start from chunk 1 (0 already loaded with initial data)

    const loadNextChunk = () => {
      if (currentChunk < totalChunks && !loadedChunks.has(currentChunk)) {
        loadChunk(currentChunk);
        currentChunk++;
        setTimeout(loadNextChunk, 200); // Throttle: 5 chunks/sec
      }
    };

    // Start loading after 500ms (let initial render complete)
    const timer = setTimeout(loadNextChunk, 500);
    return () => clearTimeout(timer);
  }, [totalRows, loadChunk, loadedChunks, CHUNK_SIZE]);

  return {
    formatting,
    loadedChunks: loadedChunks.size,
    totalChunks: Math.ceil(totalRows / CHUNK_SIZE),
    loadChunk
  };
};

export const ExcelViewer: React.FC<ExcelViewerProps> = ({
  data,
  sessionId,
  onSheetChange,
  onCellSelect,
  onExport,
  sourceLocation,
  navigationTrigger
}) => {
  const [activeSheet, setActiveSheet] = useState(data.active_sheet || data.sheets[0]?.sheet_name);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortColumns, setSortColumns] = useState<readonly SortColumn[]>([]);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [zoom, setZoom] = useState(100);
  const [highlightedCell, setHighlightedCell] = useState<string | null>(null);
  const [searchMatches, setSearchMatches] = useState<Set<string>>(new Set());

  const gridRef = useRef<any>(null);

  // Track the last navigation trigger value to detect actual navigation requests
  const lastNavigationTriggerRef = useRef<number | undefined>(navigationTrigger);

  const currentSheetData = useMemo(() => {
    return data.sheets.find(sheet => sheet.sheet_name === activeSheet);
  }, [data.sheets, activeSheet]);

  // Use formatting chunks hook for progressive loading
  const {
    formatting,
    loadedChunks,
    totalChunks
  } = useFormattingChunks(
    data.rid,
    sessionId,
    activeSheet,
    currentSheetData?.total_rows || 0,
    currentSheetData?.formatting || {}
  );

  // Debug: Log initial formatting data
  useEffect(() => {
    if (currentSheetData) {
      const initialFormatting = currentSheetData.formatting || {};
      const initialFormattingCount = Object.keys(initialFormatting).length;
      console.log(
        `[ExcelViewer] Initial data for sheet "${currentSheetData.sheet_name}": ` +
        `${initialFormattingCount} formatting keys, ${currentSheetData.rows.length} rows`
      );
      if (initialFormattingCount > 0) {
        const firstKey = Object.keys(initialFormatting)[0];
        console.log(`[ExcelViewer] Sample formatting key: ${firstKey} = `, initialFormatting[firstKey]);
      }
    }
  }, [currentSheetData]);

  // Navigation to source location - triggers ONLY when navigationTrigger changes
  // This allows re-navigation when user clicks citation, but NOT when manually changing sheets
  useEffect(() => {
    // Only navigate if navigationTrigger has actually changed (user clicked citation)
    if (navigationTrigger === lastNavigationTriggerRef.current) {
      return; // No new navigation request
    }

    console.log(`[ExcelViewer] Navigation trigger changed: ${lastNavigationTriggerRef.current} -> ${navigationTrigger}`);

    // Update the ref to the new trigger value
    lastNavigationTriggerRef.current = navigationTrigger;

    if (!sourceLocation) {
      console.log(`[ExcelViewer] ⚠️ No source location provided for navigation`);
      return;
    }

    if (!currentSheetData) {
      console.log(`[ExcelViewer] ⚠️ No current sheet data available for navigation`);
      return;
    }

    console.log(`[ExcelViewer] Navigating to:`, sourceLocation);
    console.log(`[ExcelViewer] Current sheet: "${activeSheet}"`);

    // Auto-select correct sheet if different
    if (sourceLocation.sheet !== activeSheet) {
      console.log(`[ExcelViewer] Switching to sheet "${sourceLocation.sheet}"`);
      setActiveSheet(sourceLocation.sheet);
      return; // Will trigger again when activeSheet changes
    }

    // Scroll to the row and highlight the cell
    const targetRow = sourceLocation.row;

    // Highlight the ROW for 5 seconds
    const cellKey = `${targetRow}_citation`;
    setHighlightedCell(cellKey);
    console.log(`[ExcelViewer] 🎯 Highlighting row ${targetRow} in sheet "${sourceLocation.sheet}" (gold highlight for 5 seconds)`);

    setTimeout(() => {
      setHighlightedCell(null);
    }, 5000);

    // Scroll to row (DataGrid uses 0-indexed row positions)
    // We want to show context, so scroll to a bit before the target
    const scrollToIdx = Math.max(0, targetRow - 5);

    // Use DataGrid's scrollToRow if available
    setTimeout(() => {
      if (gridRef.current && gridRef.current.scrollToCell) {
        console.log(`[ExcelViewer] Scrolling to row index ${scrollToIdx}`);
        gridRef.current.scrollToCell({ rowIdx: scrollToIdx, colIdx: 0 });
      } else {
        console.log(`[ExcelViewer] ⚠️ DataGrid scrollToCell not available`);
      }
    }, 100);
  }, [navigationTrigger, sourceLocation, activeSheet, currentSheetData]);

  // Search functionality - finds matches but doesn't filter
  useEffect(() => {
    if (!searchQuery || !currentSheetData) {
      setSearchMatches(new Set());
      return;
    }

    const query = searchQuery.toLowerCase();
    const matches = new Set<string>();

    currentSheetData.rows.forEach((row, rowIdx) => {
      Object.entries(row).forEach(([colKey, value]) => {
        if (String(value).toLowerCase().includes(query)) {
          matches.add(`${rowIdx}_${colKey}`);
        }
      });
    });

    setSearchMatches(matches);

    // Scroll to first match
    if (matches.size > 0) {
      const firstMatch = Array.from(matches)[0];
      const rowIdx = parseInt(firstMatch.split('_')[0]);
      const scrollToIdx = Math.max(0, rowIdx - 5);

      setTimeout(() => {
        if (gridRef.current && gridRef.current.scrollToCell) {
          gridRef.current.scrollToCell({ rowIdx: scrollToIdx, colIdx: 0 });
        }
      }, 100);
    }
  }, [searchQuery, currentSheetData]);

  // Convert sheet data to DataGrid format with custom cell renderer
  const columns: readonly Column<any>[] = useMemo(() => {
    if (!currentSheetData) return [];

    // Debug: Log formatting summary on sheet change (not per-cell)
    if (Object.keys(formatting).length > 0) {
      console.log(`[ExcelViewer] ✅ ${Object.keys(formatting).length} formatted cells for sheet "${currentSheetData.sheet_name}"`);
      // Log a sample of formatting keys to verify format
      const sampleKeys = Object.keys(formatting).slice(0, 3);
      console.log(`[ExcelViewer] Sample formatting keys:`, sampleKeys);
    } else {
      console.log(`[ExcelViewer] ⚠️ No formatted cells in sheet "${currentSheetData.sheet_name}" (this is normal for sheets with no colors/bold/borders)`);
    }

    // Custom cell renderer that applies formatting
    const FormattedCell = (props: RenderCellProps<any>) => {
      const { row, column, rowIdx } = props;
      const value = row[column.key];

      // Determine cell key for formatting lookup
      // Backend formatting uses 1-indexed Excel column numbers
      // Frontend columns array includes __row_id__ as first column
      // So we need to find the Excel column index by excluding __row_id__ from the count
      const dataColumns = currentSheetData.columns.filter(c => c.key !== '__row_id__');
      const excelColIdx = dataColumns.findIndex(c => c.key === column.key) + 1; // +1 for 1-indexed Excel columns

      // Backend key format: "dataGridRowIdx_excelColIdx"
      // rowIdx from DataGrid is already 0-indexed and matches what backend generates (row_idx - offset)
      const cellKey = `${rowIdx}_${excelColIdx}`;
      const fmt: CellFormatting | undefined = formatting[cellKey];

      // Check if this cell should be highlighted (citation target or search match)
      const isCitationHighlight = highlightedCell === `${rowIdx}_citation`;
      const isSearchMatch = searchMatches.has(`${rowIdx}_${column.key}`);

      // Debug logging for citation highlighting ONLY (rare, important event)
      if (isCitationHighlight && column.key !== '__row_id__') {
        console.log(`🟡 Rendering gold highlight for row ${rowIdx}, column ${column.key}`);
      }

      const style: React.CSSProperties = {
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        padding: '2px 8px',  // Minimal padding to match CSS
        margin: 0,
        border: 'none',
        boxSizing: 'border-box',
        overflow: 'visible',  // Allow text to overflow into adjacent cells
        textOverflow: 'clip',  // Don't truncate with ellipsis
      };

      // Apply cell formatting from Excel FIRST (so citation highlight can override)
      if (fmt) {
        if (fmt.bgColor) style.backgroundColor = fmt.bgColor;
        if (fmt.fontColor) style.color = fmt.fontColor;
        if (fmt.bold) style.fontWeight = 'bold';
        if (fmt.italic) style.fontStyle = 'italic';
        if (fmt.underline) style.textDecoration = 'underline';
        if (fmt.fontSize) style.fontSize = `${fmt.fontSize}px`;

        // Apply text wrapping
        if (fmt.wrapText) {
          style.whiteSpace = 'pre-wrap';
          style.wordWrap = 'break-word';
          style.overflowWrap = 'break-word';
        }

        // Apply actual Excel borders
        if (fmt.borders) {
          // Map Excel border styles to CSS
          const getBorderStyle = (borderInfo: any) => {
            const width = borderInfo.style === 'thick' ? '2px' :
                         borderInfo.style === 'medium' ? '1.5px' : '1px';
            const color = borderInfo.color || '#000000';
            const lineStyle = borderInfo.style === 'dashed' ? 'dashed' :
                             borderInfo.style === 'dotted' ? 'dotted' : 'solid';
            return `${width} ${lineStyle} ${color}`;
          };

          if (fmt.borders.top) {
            style.borderTop = getBorderStyle(fmt.borders.top);
          }
          if (fmt.borders.bottom) {
            style.borderBottom = getBorderStyle(fmt.borders.bottom);
          }
          if (fmt.borders.left) {
            style.borderLeft = getBorderStyle(fmt.borders.left);
          }
          if (fmt.borders.right) {
            style.borderRight = getBorderStyle(fmt.borders.right);
          }
        }
      }

      // Apply highlight for citation target (OVERRIDES cell formatting background)
      // This makes the entire row GOLD for maximum visibility
      // Using !important doesn't work in inline styles, so we add a className
      let cellClassName = '';
      if (isCitationHighlight) {
        cellClassName = 'citation-highlighted-cell';
        // Still apply inline styles as fallback
        style.backgroundColor = '#FFD700';
        style.border = '2px solid #FFA500';
        style.fontWeight = 'bold';
        style.boxShadow = '0 0 10px rgba(255, 215, 0, 0.5)';
      }

      // Apply highlight for search matches (yellow background)
      if (isSearchMatch && !isCitationHighlight) {
        style.backgroundColor = '#ffeb3b';
      }

      // Render cell content
      let content: React.ReactNode = value !== null && value !== undefined ? String(value) : '';

      // If cell has hyperlink, render as clickable link
      if (fmt?.hyperlink) {
        console.log(`[ExcelViewer] Rendering hyperlink in cell ${rowIdx},${column.key}: ${fmt.hyperlink}`);
        content = (
          <a
            href={fmt.hyperlink}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: style.color || '#0066cc',
              textDecoration: 'underline',
              cursor: 'pointer',
              position: 'relative',
              zIndex: 10,
            }}
            onClick={(e) => {
              e.stopPropagation();
              console.log(`[ExcelViewer] Hyperlink clicked: ${fmt.hyperlink}`);
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = '#003d7a';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = style.color || '#0066cc';
            }}
          >
            {content}
          </a>
        );
      }

      // If this is a merged cell (not anchor), show empty content
      // The anchor cell will display the content spanning visually
      if (fmt?.isMerged && fmt?.mergeAnchor) {
        content = '';
      }

      // Add pointer cursor to parent div if cell has hyperlink
      if (fmt?.hyperlink) {
        style.cursor = 'pointer';
        style.position = 'relative';
      }

      return <div style={style} className={cellClassName}>{content}</div>;
    };

    return currentSheetData.columns.map(col => ({
      key: col.key,
      name: col.name,
      width: col.width || 150,
      resizable: col.resizable !== false,
      sortable: col.sortable !== false,
      filterable: col.filterable !== false,
      renderCell: col.key === '__row_id__' ? undefined : FormattedCell
    }));
  }, [currentSheetData, highlightedCell, searchMatches, formatting]);

  // Filter and sort rows (but NOT by search - search only highlights)
  const processedRows = useMemo(() => {
    if (!currentSheetData) return [];

    let rows = [...currentSheetData.rows];

    // Apply column filters only (NOT search filter)
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        rows = rows.filter(row =>
          String(row[key]).toLowerCase().includes(value.toLowerCase())
        );
      }
    });

    // Apply sorting
    if (sortColumns.length > 0) {
      rows.sort((a, b) => {
        for (const sort of sortColumns) {
          const aValue = a[sort.columnKey];
          const bValue = b[sort.columnKey];

          if (aValue === bValue) continue;

          const compareResult = aValue > bValue ? 1 : -1;
          return sort.direction === 'ASC' ? compareResult : -compareResult;
        }
        return 0;
      });
    }

    return rows;
  }, [currentSheetData, filters, sortColumns]);

  // Row height function - returns custom height for each row or default
  const getRowHeight = useCallback((row: any) => {
    if (!currentSheetData?.row_heights) {
      return 35; // Default row height
    }

    const rowIdx = row.__row_id__;
    const height = currentSheetData.row_heights[rowIdx];

    if (height) {
      // Apply min/max constraints
      const MIN_HEIGHT = 20;
      const MAX_HEIGHT = 500;
      return Math.max(MIN_HEIGHT, Math.min(MAX_HEIGHT, height));
    }

    return 35; // Default height if no custom height
  }, [currentSheetData]);

  // Track render completion (moved here after processedRows is defined)
  useEffect(() => {
    if (currentSheetData && processedRows.length > 0) {
      // Simple completion log - render tracking removed to avoid complexity
      console.log(`✅ Excel viewer displaying ${processedRows.length} rows, ${columns.length} columns`);

      // Log row height info
      const rowHeights = currentSheetData.row_heights || {};
      const customHeightCount = Object.keys(rowHeights).length;
      if (customHeightCount > 0) {
        console.log(`📐 ${customHeightCount} rows have custom heights`);
        // Log sample heights
        const sampleHeights = Object.entries(rowHeights).slice(0, 5);
        sampleHeights.forEach(([rowIdx, height]) => {
          console.log(`   Row ${rowIdx}: ${height}px`);
        });
      }
    }
  }, [processedRows.length, columns.length, currentSheetData]);

  const handleSheetChange = (sheetName: string) => {
    setActiveSheet(sheetName);
    onSheetChange?.(sheetName);
    // Reset filters and search when changing sheets
    setSearchQuery('');
    setFilters({});
    setSortColumns([]);
    setHighlightedCell(null);
    setSearchMatches(new Set());
    // Note: lastSourceRef is NOT reset - allows re-navigation if user clicks citation again
  };

  const handleExport = () => {
    if (currentSheetData) {
      onExport?.(activeSheet, processedRows);

      // Default export implementation
      const csvContent = convertToCSV(processedRows, columns);
      downloadCSV(csvContent, `${data.title}_${activeSheet}.csv`);
    }
  };

  const handleCellClick = (args: any) => {
    onCellSelect?.(args.row, args.column);
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 25, 300));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 25, 10));
  };

  const handleZoomReset = () => {
    setZoom(100);
  };

  // Show loading indicator when chunks are still loading
  const showLoadingIndicator = loadedChunks < totalChunks;

  return (
    <div className="excel-viewer flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900">{data.title}</h3>
          <div className="flex items-center space-x-2">
            {/* Zoom controls */}
            <div className="flex items-center space-x-1 border border-gray-300 rounded-md bg-white">
              <button
                onClick={handleZoomOut}
                disabled={zoom <= 10}
                className="p-1.5 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Zoom out"
              >
                <ZoomOut className="h-3.5 w-3.5 text-gray-600" />
              </button>
              <span className="px-2 text-xs font-medium text-gray-700 min-w-[3rem] text-center">
                {zoom}%
              </span>
              <button
                onClick={handleZoomIn}
                disabled={zoom >= 300}
                className="p-1.5 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Zoom in"
              >
                <ZoomIn className="h-3.5 w-3.5 text-gray-600" />
              </button>
              <button
                onClick={handleZoomReset}
                className="px-2 py-1.5 hover:bg-gray-100 border-l border-gray-300 text-xs font-medium text-gray-600"
                title="Reset zoom to 100%"
              >
                100%
              </button>
            </div>

            {/* Export button */}
            <button
              onClick={handleExport}
              className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <Download className="h-3.5 w-3.5 mr-1.5" />
              Export
            </button>
          </div>
        </div>

        {/* Search bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search current sheet..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>

        {/* Stats */}
        <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
          <span>{processedRows.length} rows</span>
          <span>{columns.length} columns</span>
          {searchQuery && searchMatches.size > 0 && (
            <span className="text-indigo-600 font-medium">
              {searchMatches.size} matches found
            </span>
          )}
        </div>
      </div>

      {/* Loading indicator for background formatting chunks */}
      {showLoadingIndicator && (
        <div className="px-4 py-2 bg-blue-50 border-b border-blue-200 text-xs text-blue-800 flex items-center space-x-2">
          <svg className="animate-spin h-3 w-3 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>Loading formatting: {loadedChunks} / {totalChunks} chunks loaded</span>
        </div>
      )}

      {/* Sheet tabs */}
      {data.sheets.length > 1 && (
        <Tabs.Root value={activeSheet} onValueChange={handleSheetChange}>
          <Tabs.List className="flex-shrink-0 flex items-center space-x-1 px-4 border-b border-gray-200 bg-white overflow-x-auto">
            {data.sheets.map(sheet => (
              <Tabs.Trigger
                key={sheet.sheet_name}
                value={sheet.sheet_name}
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 border-b-2 border-transparent data-[state=active]:border-indigo-600 data-[state=active]:text-indigo-600 whitespace-nowrap"
              >
                {sheet.sheet_name}
                <span className="ml-2 text-xs text-gray-400">
                  ({sheet.total_rows})
                </span>
              </Tabs.Trigger>
            ))}
          </Tabs.List>
        </Tabs.Root>
      )}

      {/* Data grid with zoom */}
      <div className="flex-1 overflow-hidden">
        {currentSheetData && (
          <div style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top left', width: `${10000 / zoom}%`, height: `${10000 / zoom}%` }}>
            <DataGrid
              ref={gridRef}
              columns={columns}
              rows={processedRows}
              defaultColumnOptions={{
                sortable: true,
                resizable: true
              }}
              sortColumns={sortColumns}
              onSortColumnsChange={setSortColumns}
              onCellClick={handleCellClick}
              className="rdg-light"
              style={{ height: '100%', minHeight: '600px' }}
              rowKeyGetter={(row) => row.__row_id__ !== undefined ? row.__row_id__ : row.id || JSON.stringify(row)}
              rowHeight={getRowHeight}
            />
          </div>
        )}

        {!currentSheetData && (
          <div className="flex items-center justify-center h-full text-gray-500">
            No data available
          </div>
        )}
      </div>

      {/* Footer info */}
      {currentSheetData && currentSheetData.has_more && (
        <div className="flex-shrink-0 px-4 py-2 border-t border-gray-200 bg-yellow-50 text-xs text-yellow-800">
          Showing {processedRows.length} of {currentSheetData.total_rows} rows.
          Some rows may be hidden for performance.
        </div>
      )}

      {/* Add pulse animation and citation highlight styles */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }

        /* Use Excel's actual border formatting - no default borders */
        /* This ensures cells render EXACTLY as they appear in Excel/Google Drive */

        .excel-viewer .rdg {
          --rdg-border-color: transparent;
          --rdg-row-hover-background-color: transparent;
          border: 1px solid #d0d0d0;
        }

        /* Remove all default cell borders - Excel borders applied via inline styles */
        .excel-viewer .rdg-cell {
          border: none !important;
          padding: 0 !important;
          outline: none !important;
          box-shadow: none !important;
        }

        /* Remove all padding/margin that creates gaps */
        /* Borders are applied directly to the content div from Excel data */
        .excel-viewer .rdg-cell > div {
          margin: 0 !important;
          padding: 2px 8px !important;
          outline: none !important;
          box-sizing: border-box !important;
          width: 100% !important;
          height: 100% !important;
        }

        /* Row styling */
        .excel-viewer .rdg-row {
          border: none !important;
        }

        /* Header row */
        .excel-viewer .rdg-header-row {
          border-bottom: 2px solid #d0d0d0 !important;
          background-color: #f8f9fa !important;
        }

        .excel-viewer .rdg-header-row .rdg-cell {
          font-weight: 600 !important;
        }

        /* Citation highlight - MUST use !important to override DataGrid CSS */
        .citation-highlighted-cell {
          background-color: #FFD700 !important;
          border: 2px solid #FFA500 !important;
          font-weight: bold !important;
          box-shadow: 0 0 10px rgba(255, 215, 0, 0.5) !important;
          animation: pulse 1.5s ease-in-out 3 !important;
          z-index: 100 !important;
          position: relative !important;
        }
      `}</style>
    </div>
  );
};

// Helper functions
function convertToCSV(rows: any[], columns: readonly Column<any>[]): string {
  const headers = columns.map(col => col.name).join(',');
  const data = rows.map(row =>
    columns.map(col => {
      const value = row[col.key];
      // Escape commas and quotes
      const escaped = String(value).replace(/"/g, '""');
      return `"${escaped}"`;
    }).join(',')
  );

  return [headers, ...data].join('\n');
}

function downloadCSV(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
