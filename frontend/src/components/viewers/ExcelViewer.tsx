/**
 * Phase 3: Excel Interactive Viewer - ENHANCED
 * Interactive spreadsheet viewer with:
 * - Smart navigation to cited cells
 * - Cell formatting preservation
 * - Zoom controls
 * - Context-aware search (scroll + highlight, not filter)
 * Performance target: <500ms Excel render time
 */

import React, { useState, useMemo, useEffect, useRef } from 'react';
import DataGrid, { Column, SortColumn, RenderCellProps } from 'react-data-grid';
import * as Tabs from '@radix-ui/react-tabs';
import { Search, Download, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import type { ExcelViewerProps, CellFormatting } from '../../types/document-preview';
import 'react-data-grid/lib/styles.css';

export const ExcelViewer: React.FC<ExcelViewerProps> = ({
  data,
  onSheetChange,
  onCellSelect,
  onExport,
  sourceLocation
}) => {
  const [activeSheet, setActiveSheet] = useState(data.active_sheet || data.sheets[0]?.sheet_name);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortColumns, setSortColumns] = useState<readonly SortColumn[]>([]);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [zoom, setZoom] = useState(100);
  const [highlightedCell, setHighlightedCell] = useState<string | null>(null);
  const [searchMatches, setSearchMatches] = useState<Set<string>>(new Set());
  const [hasAutoNavigated, setHasAutoNavigated] = useState(false);

  const gridRef = useRef<any>(null);

  const currentSheetData = useMemo(() => {
    return data.sheets.find(sheet => sheet.sheet_name === activeSheet);
  }, [data.sheets, activeSheet]);

  // Navigation to source location when component mounts or sourceLocation changes
  useEffect(() => {
    if (sourceLocation && currentSheetData && !hasAutoNavigated) {
      // Auto-select correct sheet if different
      if (sourceLocation.sheet !== activeSheet) {
        setActiveSheet(sourceLocation.sheet);
        return; // Will trigger again when activeSheet changes
      }

      // Mark that we've completed auto-navigation
      setHasAutoNavigated(true);

      // Scroll to the row and highlight the cell
      const targetRow = sourceLocation.row;

      // Highlight the ROW for 5 seconds (more visible, longer duration)
      const cellKey = `${targetRow}_citation`;
      setHighlightedCell(cellKey);
      console.log(`🎯 Highlighting row ${targetRow} with gold background for 5 seconds`);

      setTimeout(() => {
        setHighlightedCell(null);
        console.log('✓ Gold highlight removed');
      }, 5000);  // Increased from 3 to 5 seconds

      // Scroll to row (DataGrid uses 0-indexed row positions)
      // We want to show context, so scroll to a bit before the target
      const scrollToIdx = Math.max(0, targetRow - 5);

      // Use DataGrid's scrollToRow if available
      setTimeout(() => {
        if (gridRef.current && gridRef.current.scrollToCell) {
          gridRef.current.scrollToCell({ rowIdx: scrollToIdx, colIdx: 0 });
        }
      }, 100);
    }
  }, [sourceLocation, activeSheet, currentSheetData, hasAutoNavigated]);

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

    const formatting = currentSheetData.formatting || {};

    // Debug: Log formatting summary on sheet change (not per-cell)
    if (Object.keys(formatting).length > 0) {
      console.log(`[ExcelViewer] ✅ Loaded ${Object.keys(formatting).length} formatted cells for sheet "${currentSheetData.sheet_name}"`);
    } else {
      console.log(`[ExcelViewer] No cell formatting found for sheet "${currentSheetData.sheet_name}"`);
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
        padding: '0 8px',
      };

      // Apply cell formatting from Excel FIRST (so citation highlight can override)
      if (fmt) {
        if (fmt.bgColor) style.backgroundColor = fmt.bgColor;
        if (fmt.fontColor) style.color = fmt.fontColor;
        if (fmt.bold) style.fontWeight = 'bold';
        if (fmt.italic) style.fontStyle = 'italic';
        if (fmt.underline) style.textDecoration = 'underline';
        if (fmt.fontSize) style.fontSize = `${fmt.fontSize}px`;
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

      return <div style={style} className={cellClassName}>{value !== null && value !== undefined ? String(value) : ''}</div>;
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
  }, [currentSheetData, highlightedCell, searchMatches]);

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

  // Track render completion (moved here after processedRows is defined)
  useEffect(() => {
    if (currentSheetData && processedRows.length > 0) {
      // Simple completion log - render tracking removed to avoid complexity
      console.log(`✅ Excel viewer displaying ${processedRows.length} rows, ${columns.length} columns`);
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
    // Don't re-trigger auto-navigation when user manually changes sheets
    // hasAutoNavigated remains true to prevent re-highlighting
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
                className="p-1.5 hover:bg-gray-100 border-l border-gray-300"
                title="Reset zoom"
              >
                <RotateCcw className="h-3.5 w-3.5 text-gray-600" />
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

        /* Remove cell borders to allow color-coded cells to visually merge */
        /* This is critical for databases where adjacent cells with same color form visual blocks */
        .rdg-cell {
          border-right: none !important;
          border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important;
        }

        /* Remove white borders from formatted cells */
        .excel-viewer .rdg {
          --rdg-border-color: transparent !important;
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
