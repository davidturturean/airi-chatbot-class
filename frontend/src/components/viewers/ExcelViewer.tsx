/**
 * Phase 3: Excel Interactive Viewer
 * Interactive spreadsheet viewer with sorting, filtering, and cell selection
 * Performance target: <500ms Excel render time
 */

import React, { useState, useMemo } from 'react';
import DataGrid, { Column, SortColumn } from 'react-data-grid';
import * as Tabs from '@radix-ui/react-tabs';
import { Search, Download } from 'lucide-react';
import type { ExcelViewerProps } from '../../types/document-preview';
import 'react-data-grid/lib/styles.css';

export const ExcelViewer: React.FC<ExcelViewerProps> = ({
  data,
  onSheetChange,
  onCellSelect,
  onExport
}) => {
  const [activeSheet, setActiveSheet] = useState(data.active_sheet || data.sheets[0]?.sheet_name);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortColumns, setSortColumns] = useState<readonly SortColumn[]>([]);
  const [filters, setFilters] = useState<Record<string, string>>({});

  const currentSheetData = useMemo(() => {
    return data.sheets.find(sheet => sheet.sheet_name === activeSheet);
  }, [data.sheets, activeSheet]);

  // Convert sheet data to DataGrid format
  const columns: readonly Column<any>[] = useMemo(() => {
    if (!currentSheetData) return [];

    return currentSheetData.columns.map(col => ({
      key: col.key,
      name: col.name,
      width: col.width || 150,
      resizable: col.resizable !== false,
      sortable: col.sortable !== false,
      filterable: col.filterable !== false
    }));
  }, [currentSheetData]);

  // Filter and sort rows
  const processedRows = useMemo(() => {
    if (!currentSheetData) return [];

    let rows = [...currentSheetData.rows];

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      rows = rows.filter(row =>
        Object.values(row).some(value =>
          String(value).toLowerCase().includes(query)
        )
      );
    }

    // Apply column filters
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
  }, [currentSheetData, searchQuery, filters, sortColumns]);

  const handleSheetChange = (sheetName: string) => {
    setActiveSheet(sheetName);
    onSheetChange?.(sheetName);
    // Reset filters and search when changing sheets
    setSearchQuery('');
    setFilters({});
    setSortColumns([]);
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

  return (
    <div className="excel-viewer flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900">{data.title}</h3>
          <button
            onClick={handleExport}
            className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Export
          </button>
        </div>

        {/* Search bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search in sheet..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>

        {/* Stats */}
        <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
          <span>{processedRows.length} rows</span>
          <span>{columns.length} columns</span>
          {searchQuery && <span className="text-indigo-600 font-medium">Filtered</span>}
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

      {/* Data grid */}
      <div className="flex-1 overflow-hidden">
        {currentSheetData && (
          <DataGrid
            columns={columns}
            rows={processedRows}
            defaultColumnOptions={{
              sortable: true,
              resizable: true
            }}
            sortColumns={sortColumns}
            onSortColumnsChange={setSortColumns}
            onCellClick={handleCellClick}
            className="rdg-light h-full"
            style={{ height: '100%' }}
            rowKeyGetter={(row) => row.__row_id__ !== undefined ? row.__row_id__ : row.id || JSON.stringify(row)}
          />
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
