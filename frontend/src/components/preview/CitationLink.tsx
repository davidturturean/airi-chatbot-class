/**
 * Citation Link Component
 * Integrates HoverPreview with existing citation system
 * Wraps [RID-12345] citations to make them interactive
 */

import React from 'react';
import { HoverPreview } from './HoverPreview';
import { usePanel } from '../../context/PanelContext';

interface CitationLinkProps {
  rid: string;
  sessionId: string;
  children?: React.ReactNode;
}

export const CitationLink: React.FC<CitationLinkProps> = ({
  rid,
  sessionId,
  children
}) => {
  const { openPanel } = usePanel();

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    openPanel(rid);
  };

  return (
    <HoverPreview rid={rid} sessionId={sessionId}>
      <a
        href={`#${rid}`}
        onClick={handleClick}
        className="citation-link inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700 hover:bg-indigo-100 hover:text-indigo-900 transition-colors cursor-pointer"
        data-rid={rid}
      >
        {children || rid}
      </a>
    </HoverPreview>
  );
};

/**
 * Parse markdown-style citations and convert them to interactive links
 * Converts: [RID-12345] -> <CitationLink rid="RID-12345" />
 */
export function parseCitations(text: string, sessionId: string): React.ReactNode[] {
  const citationRegex = /\[(RID-\d{5}|META-\d{5})\]/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;

  while ((match = citationRegex.exec(text)) !== null) {
    // Add text before citation
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    // Add citation link
    const rid = match[1];
    parts.push(
      <CitationLink key={`${rid}-${match.index}`} rid={rid} sessionId={sessionId}>
        {match[0]}
      </CitationLink>
    );

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
}
