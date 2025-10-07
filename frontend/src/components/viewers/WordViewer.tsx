/**
 * Phase 4: Word Document Viewer
 * Renders .docx files with formatting preserved
 * Includes table of contents and in-document search
 */

import React, { useState, useEffect, useMemo } from 'react';
import DOMPurify from 'dompurify';
import * as ScrollArea from '@radix-ui/react-scroll-area';
import { Search, List, ChevronDown, ChevronRight } from 'lucide-react';
import type { WordViewerProps, TableOfContentsItem } from '../../types/document-preview';

export const WordViewer: React.FC<WordViewerProps> = ({
  data,
  onTocItemClick,
  onSearch
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showToc, setShowToc] = useState(true);
  const [expandedTocItems, setExpandedTocItems] = useState<Set<string>>(new Set());

  // Sanitize HTML content
  const sanitizedHtml = useMemo(() => {
    return DOMPurify.sanitize(data.html_content, {
      ALLOWED_TAGS: [
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li',
        'strong', 'b', 'em', 'i', 'u', 's',
        'a', 'br', 'hr',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'img', 'span', 'div',
        'blockquote', 'pre', 'code'
      ],
      ALLOWED_ATTR: [
        'href', 'src', 'alt', 'title',
        'class', 'style', 'id',
        'colspan', 'rowspan'
      ],
      ALLOW_DATA_ATTR: false
    });
  }, [data.html_content]);

  // Highlight search results
  const highlightedHtml = useMemo(() => {
    if (!searchQuery || searchQuery.length < 2) {
      return sanitizedHtml;
    }

    const regex = new RegExp(`(${searchQuery})`, 'gi');
    return sanitizedHtml.replace(regex, '<mark class="bg-yellow-200">$1</mark>');
  }, [sanitizedHtml, searchQuery]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    onSearch?.(query);

    // Scroll to first match
    if (query && query.length >= 2) {
      setTimeout(() => {
        const firstMark = document.querySelector('.word-content mark');
        if (firstMark) {
          firstMark.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 100);
    }
  };

  const handleTocClick = (itemId: string) => {
    onTocItemClick?.(itemId);

    // Scroll to heading
    const element = document.getElementById(itemId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const toggleTocItem = (itemId: string) => {
    setExpandedTocItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  };

  return (
    <div className="word-viewer flex h-full">
      {/* Table of Contents Sidebar */}
      {data.toc && data.toc.length > 0 && showToc && (
        <div className="flex-shrink-0 w-64 border-r border-gray-200 bg-gray-50">
          <div className="px-4 py-3 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-900">Contents</h3>
              <button
                onClick={() => setShowToc(false)}
                className="text-gray-400 hover:text-gray-600"
                aria-label="Hide table of contents"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
            </div>
          </div>

          <ScrollArea.Root className="h-[calc(100%-60px)]">
            <ScrollArea.Viewport className="h-full px-4 py-2">
              <nav className="space-y-1">
                {data.toc.map(item => (
                  <TocItem
                    key={item.id}
                    item={item}
                    expanded={expandedTocItems.has(item.id)}
                    onClick={handleTocClick}
                    onToggle={toggleTocItem}
                  />
                ))}
              </nav>
            </ScrollArea.Viewport>
            <ScrollArea.Scrollbar orientation="vertical" className="w-2.5 bg-gray-100">
              <ScrollArea.Thumb className="bg-gray-400 rounded-full" />
            </ScrollArea.Scrollbar>
          </ScrollArea.Root>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="flex-shrink-0 px-4 py-3 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              {!showToc && data.toc && data.toc.length > 0 && (
                <button
                  onClick={() => setShowToc(true)}
                  className="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
                >
                  <List className="h-3.5 w-3.5 mr-1" />
                  TOC
                </button>
              )}
              <h3 className="text-sm font-semibold text-gray-900">{data.title}</h3>
            </div>
            <div className="flex items-center space-x-4 text-xs text-gray-500">
              {data.word_count && <span>{data.word_count.toLocaleString()} words</span>}
              {data.page_count && <span>{data.page_count} pages</span>}
            </div>
          </div>

          {/* Search bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search in document..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Document Content */}
        <ScrollArea.Root className="flex-1">
          <ScrollArea.Viewport className="h-full">
            <div className="px-8 py-6 max-w-4xl mx-auto">
              <div
                className="word-content prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{ __html: highlightedHtml }}
                style={{
                  fontFamily: 'Georgia, serif',
                  lineHeight: '1.8'
                }}
              />
            </div>
          </ScrollArea.Viewport>
          <ScrollArea.Scrollbar orientation="vertical" className="w-2.5 bg-gray-100">
            <ScrollArea.Thumb className="bg-gray-400 rounded-full" />
          </ScrollArea.Scrollbar>
        </ScrollArea.Root>
      </div>
    </div>
  );
};

// Table of Contents Item Component
interface TocItemProps {
  item: TableOfContentsItem;
  expanded: boolean;
  onClick: (id: string) => void;
  onToggle: (id: string) => void;
}

const TocItem: React.FC<TocItemProps> = ({ item, expanded, onClick, onToggle }) => {
  const hasChildren = item.children && item.children.length > 0;
  const indent = item.level * 12;

  return (
    <div>
      <button
        onClick={() => onClick(item.id)}
        className="w-full flex items-start text-left px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded group"
        style={{ paddingLeft: `${indent}px` }}
      >
        {hasChildren && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggle(item.id);
            }}
            className="mr-1 mt-0.5 text-gray-400 hover:text-gray-600"
          >
            {expanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </button>
        )}
        <span className="flex-1 truncate">{item.title}</span>
      </button>

      {hasChildren && expanded && (
        <div className="mt-0.5">
          {item.children!.map(child => (
            <TocItem
              key={child.id}
              item={child}
              expanded={expanded}
              onClick={onClick}
              onToggle={onToggle}
            />
          ))}
        </div>
      )}
    </div>
  );
};
