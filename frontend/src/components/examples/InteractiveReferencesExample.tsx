/**
 * Interactive References Example
 * Demonstrates how to integrate the Interactive Reference Visualization system
 * into the AIRI chatbot
 */

import React, { useState } from 'react';
import { PanelProvider, usePanel } from '../../context/PanelContext';
import { EnhancedSlideoutPanel } from '../preview/EnhancedSlideoutPanel';
import { CitationLink } from '../preview/CitationLink';
import { CitationGallery } from '../gallery/CitationGallery';

/**
 * Example: Chat Message with Interactive Citations
 * This shows how to render AI responses with clickable citations
 */
export function ChatMessageWithCitations() {
  const sessionId = 'example-session-123'; // Replace with actual session ID

  // Example AI response with citations
  const aiResponse = `
    Based on the AI risk framework, you should focus on three key areas:

    1. Governance and Oversight [RID-00001]
       - Establish clear accountability structures
       - Define roles and responsibilities

    2. Technical Safety Measures [RID-00002]
       - Implement robust testing protocols
       - Monitor model behavior continuously

    3. Ethical Considerations [RID-00003]
       - Assess potential biases
       - Ensure fairness and transparency

    For more details on regulatory requirements, see [RID-00004] and [RID-00005].
  `;

  return (
    <PanelProvider>
      <div className="chat-message">
        <div className="message-content">
          {parseMessageWithCitations(aiResponse, sessionId)}
        </div>

        {/* The slideout panel */}
        <InteractivePanelManager sessionId={sessionId} />
      </div>
    </PanelProvider>
  );
}

/**
 * Example: Panel Manager Component
 * This component manages the slideout panel state
 */
function InteractivePanelManager({ sessionId }: { sessionId: string }) {
  const panel = usePanel();

  return (
    <EnhancedSlideoutPanel
      isOpen={panel.isOpen}
      isPinned={panel.isPinned}
      rid={panel.currentRid}
      sessionId={sessionId}
      onClose={panel.closePanel}
      onPin={panel.togglePin}
      onNavigate={panel.navigateTo}
    />
  );
}

/**
 * Example: Gallery View Button
 * This shows how to add a "View All Sources" button to responses
 */
export function ViewAllSourcesButton() {
  const [showGallery, setShowGallery] = useState(false);
  const sessionId = 'example-session-123'; // Replace with actual session ID
  const { openPanel } = usePanel();

  if (!showGallery) {
    return (
      <button
        onClick={() => setShowGallery(true)}
        className="inline-flex items-center px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 rounded-md hover:bg-indigo-100 transition-colors"
      >
        <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        View All Sources
      </button>
    );
  }

  return (
    <div className="gallery-modal fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-[80vh] flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Citation Gallery</h2>
          <button
            onClick={() => setShowGallery(false)}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-hidden">
          <CitationGallery
            sessionId={sessionId}
            onItemClick={(rid) => {
              openPanel(rid);
              setShowGallery(false);
            }}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * Helper function to parse message text and convert citations to interactive links
 */
function parseMessageWithCitations(text: string, sessionId: string): React.ReactNode[] {
  const citationRegex = /\[(RID-\d{5}|META-\d{5})\]/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;
  let keyIndex = 0;

  while ((match = citationRegex.exec(text)) !== null) {
    // Add text before citation
    if (match.index > lastIndex) {
      const textPart = text.substring(lastIndex, match.index);
      parts.push(
        <span key={`text-${keyIndex++}`}>{textPart}</span>
      );
    }

    // Add citation link
    const rid = match[1];
    parts.push(
      <CitationLink key={`citation-${rid}-${keyIndex++}`} rid={rid} sessionId={sessionId}>
        {match[0]}
      </CitationLink>
    );

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(
      <span key={`text-${keyIndex++}`}>{text.substring(lastIndex)}</span>
    );
  }

  return parts.length > 0 ? parts : [text];
}

/**
 * Complete Integration Example
 * This shows how to integrate all components into your chat interface
 */
export function AIRIChatWithInteractiveReferences() {
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const [messages] = useState([
    {
      role: 'assistant',
      content: 'Based on your question about AI governance, I found relevant information in our knowledge base [RID-00001] and [RID-00002].'
    }
  ]);

  return (
    <PanelProvider>
      <div className="chat-container flex flex-col h-screen">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          {messages.map((msg, idx) => (
            <div key={idx} className="mb-4">
              <div className="prose prose-sm max-w-none">
                {parseMessageWithCitations(msg.content, sessionId)}
              </div>
            </div>
          ))}

          {/* View All Sources Button */}
          <div className="mt-6">
            <ViewAllSourcesButton />
          </div>
        </div>

        {/* Chat Input */}
        <div className="border-t border-gray-200 p-4">
          <input
            type="text"
            placeholder="Ask a question..."
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Interactive Panel */}
        <InteractivePanelManager sessionId={sessionId} />
      </div>
    </PanelProvider>
  );
}
