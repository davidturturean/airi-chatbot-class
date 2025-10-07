/**
 * Phase 5: Citation Gallery Component
 * Airtable-inspired gallery view for exploring all sources
 * Features: Grid layout, filtering, grouping, metadata tags
 */

import React, { useState, useMemo, useEffect } from 'react';
import * as ScrollArea from '@radix-ui/react-scroll-area';
import { Search, Grid, List as ListIcon, FileText, FileSpreadsheet, FileImage, File } from 'lucide-react';
import type { CitationGalleryProps, CitationGalleryItem } from '../../types/document-preview';

type ViewMode = 'grid' | 'list';
type GroupBy = 'domain' | 'file_type' | 'entity' | 'none';

export const CitationGallery: React.FC<CitationGalleryProps> = ({
  sessionId,
  items = [],
  onItemClick,
  filters: initialFilters = {},
  groupBy: initialGroupBy = 'none'
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [groupBy, setGroupBy] = useState<GroupBy>(initialGroupBy);
  const [activeFilters, setActiveFilters] = useState(initialFilters);
  const [galleryItems, setGalleryItems] = useState<CitationGalleryItem[]>(items);

  // Fetch gallery items if not provided
  useEffect(() => {
    if (items.length === 0) {
      fetchGalleryItems();
    }
  }, [sessionId]);

  const fetchGalleryItems = async () => {
    try {
      const response = await fetch(`/api/session/${sessionId}/gallery`);
      if (response.ok) {
        const data = await response.json();
        setGalleryItems(data.items || []);
      }
    } catch (error) {
      console.error('Failed to fetch gallery items:', error);
    }
  };

  // Filter and search items
  const filteredItems = useMemo(() => {
    return galleryItems.filter(item => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesSearch =
          item.title.toLowerCase().includes(query) ||
          item.rid.toLowerCase().includes(query) ||
          item.metadata.domain?.toLowerCase().includes(query) ||
          item.metadata.entity?.toLowerCase().includes(query);

        if (!matchesSearch) return false;
      }

      // Active filters
      if (activeFilters.domain && item.metadata.domain !== activeFilters.domain) {
        return false;
      }
      if (activeFilters.file_type && item.preview_type !== activeFilters.file_type) {
        return false;
      }
      if (activeFilters.entity && item.metadata.entity !== activeFilters.entity) {
        return false;
      }
      if (activeFilters.risk_category && item.metadata.risk_category !== activeFilters.risk_category) {
        return false;
      }

      return true;
    });
  }, [galleryItems, searchQuery, activeFilters]);

  // Group items
  const groupedItems = useMemo(() => {
    if (groupBy === 'none') {
      return { 'All Documents': filteredItems };
    }

    const groups: Record<string, CitationGalleryItem[]> = {};

    filteredItems.forEach(item => {
      let groupKey = 'Other';

      if (groupBy === 'domain') {
        groupKey = item.metadata.domain || 'Uncategorized';
      } else if (groupBy === 'file_type') {
        groupKey = item.preview_type || 'unknown';
      } else if (groupBy === 'entity') {
        groupKey = item.metadata.entity || 'Uncategorized';
      }

      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(item);
    });

    return groups;
  }, [filteredItems, groupBy]);

  // Get unique filter values
  const _filterOptions = useMemo(() => {
    return {
      domains: [...new Set(galleryItems.map(i => i.metadata.domain).filter(Boolean))],
      fileTypes: [...new Set(galleryItems.map(i => i.preview_type))],
      entities: [...new Set(galleryItems.map(i => i.metadata.entity).filter(Boolean))],
      riskCategories: [...new Set(galleryItems.map(i => i.metadata.risk_category).filter(Boolean))]
    };
  }, [galleryItems]);

  const handleFilterChange = (filterType: string, value: string) => {
    setActiveFilters(prev => ({
      ...prev,
      [filterType]: prev[filterType as keyof typeof prev] === value ? undefined : value
    }));
  };

  const clearFilters = () => {
    setActiveFilters({});
    setSearchQuery('');
  };

  return (
    <div className="citation-gallery flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">All Sources</h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-indigo-100 text-indigo-600' : 'text-gray-400 hover:text-gray-600'}`}
              aria-label="Grid view"
            >
              <Grid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${viewMode === 'list' ? 'bg-indigo-100 text-indigo-600' : 'text-gray-400 hover:text-gray-600'}`}
              aria-label="List view"
            >
              <ListIcon className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search sources..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Filters and Group By */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value as GroupBy)}
              className="text-xs border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="none">No grouping</option>
              <option value="domain">Group by Domain</option>
              <option value="file_type">Group by Type</option>
              <option value="entity">Group by Entity</option>
            </select>

            {Object.values(activeFilters).some(v => v) && (
              <button
                onClick={clearFilters}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
              >
                Clear filters
              </button>
            )}
          </div>

          <div className="text-xs text-gray-500">
            {filteredItems.length} of {galleryItems.length} sources
          </div>
        </div>

        {/* Active Filters */}
        {Object.entries(activeFilters).some(([_, v]) => v) && (
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(activeFilters).map(([key, value]) =>
              value ? (
                <span
                  key={key}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700"
                >
                  {value}
                  <button
                    onClick={() => handleFilterChange(key, value)}
                    className="ml-1 text-indigo-600 hover:text-indigo-800"
                  >
                    ×
                  </button>
                </span>
              ) : null
            )}
          </div>
        )}
      </div>

      {/* Gallery Content */}
      <ScrollArea.Root className="flex-1">
        <ScrollArea.Viewport className="h-full px-6 py-4">
          {Object.entries(groupedItems).map(([groupName, items]) => (
            <div key={groupName} className="mb-8 last:mb-0">
              {groupBy !== 'none' && (
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  {groupName}
                  <span className="ml-2 text-xs font-normal text-gray-500">
                    ({items.length})
                  </span>
                </h3>
              )}

              <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-2'}>
                {items.map(item => (
                  viewMode === 'grid' ? (
                    <GalleryCard key={item.rid} item={item} onClick={() => onItemClick(item.rid)} />
                  ) : (
                    <GalleryListItem key={item.rid} item={item} onClick={() => onItemClick(item.rid)} />
                  )
                ))}
              </div>
            </div>
          ))}

          {filteredItems.length === 0 && (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <FileText className="h-12 w-12 mb-3" />
              <p className="text-sm">No sources found</p>
            </div>
          )}
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar orientation="vertical" className="w-2.5 bg-gray-100">
          <ScrollArea.Thumb className="bg-gray-400 rounded-full" />
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>
    </div>
  );
};

// Gallery Card Component (Grid View)
interface GalleryCardProps {
  item: CitationGalleryItem;
  onClick: () => void;
}

const GalleryCard: React.FC<GalleryCardProps> = ({ item, onClick }) => {
  const Icon = getFileTypeIcon(item.preview_type);

  return (
    <button
      onClick={onClick}
      className="group bg-white rounded-lg border border-gray-200 p-4 hover:border-indigo-300 hover:shadow-md transition-all text-left"
    >
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <Icon className="h-8 w-8 text-gray-400 group-hover:text-indigo-600" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-gray-900 truncate group-hover:text-indigo-600">
            {item.title}
          </h4>
          <p className="text-xs text-gray-500 mt-1">{item.rid}</p>

          {/* Metadata tags */}
          <div className="mt-2 flex flex-wrap gap-1">
            {item.metadata.domain && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700">
                {item.metadata.domain}
              </span>
            )}
            {item.metadata.entity && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
                {item.metadata.entity}
              </span>
            )}
          </div>
        </div>
      </div>
    </button>
  );
};

// Gallery List Item Component (List View)
const GalleryListItem: React.FC<GalleryCardProps> = ({ item, onClick }) => {
  const Icon = getFileTypeIcon(item.preview_type);

  return (
    <button
      onClick={onClick}
      className="group w-full bg-white rounded-lg border border-gray-200 px-4 py-3 hover:border-indigo-300 hover:shadow-sm transition-all flex items-center space-x-4"
    >
      <Icon className="h-5 w-5 text-gray-400 group-hover:text-indigo-600 flex-shrink-0" />

      <div className="flex-1 min-w-0 text-left">
        <h4 className="text-sm font-medium text-gray-900 truncate group-hover:text-indigo-600">
          {item.title}
        </h4>
        <p className="text-xs text-gray-500">{item.rid}</p>
      </div>

      <div className="flex items-center space-x-2 flex-shrink-0">
        {item.metadata.domain && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700">
            {item.metadata.domain}
          </span>
        )}
        {item.metadata.entity && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
            {item.metadata.entity}
          </span>
        )}
      </div>
    </button>
  );
};

// Helper function to get icon for file type
function getFileTypeIcon(fileType: string) {
  switch (fileType) {
    case 'excel':
      return FileSpreadsheet;
    case 'word':
      return FileText;
    case 'image':
      return FileImage;
    default:
      return File;
  }
}
