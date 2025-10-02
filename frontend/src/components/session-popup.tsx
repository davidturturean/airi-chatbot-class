import { useState } from 'react';
import { InfoTooltip } from './info-tooltip';

interface SessionPopupProps {
  sessionId: string;
  onClearSession: () => void;
  inSidebar?: boolean;
}

export const SessionPopup = ({ sessionId, onClearSession, inSidebar = false }: SessionPopupProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showCopied, setShowCopied] = useState(false);

  const copySessionId = () => {
    navigator.clipboard.writeText(sessionId);
    setShowCopied(true);
    setTimeout(() => setShowCopied(false), 2000);
  };

  // Different styling for sidebar vs floating
  const containerClass = inSidebar
    ? "bg-white border rounded-xl shadow-sm transition-all"
    : "fixed bottom-6 right-6 bg-white border rounded-xl shadow-lg z-10 transition-all";

  return (
    <div className={containerClass}>
      {/* Collapsed view - just a small button */}
      {!isExpanded ? (
        <button
          onClick={() => setIsExpanded(true)}
          className="px-3 py-2 text-xs text-gray-600 hover:bg-gray-50 rounded-xl flex items-center gap-1.5 transition"
          title="Show session info"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-xs">Session</span>
        </button>
      ) : (
        /* Expanded view - full session details */
        <div className="p-4 min-w-[280px]">
          {/* Header with collapse button */}
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-md font-semibold">Session</h3>
            <button
              onClick={() => setIsExpanded(false)}
              className="p-1 hover:bg-gray-100 rounded transition"
              title="Minimize"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>

          {/* Full Session ID with copy button */}
          <div className="mb-3">
            <p className="text-xs text-gray-500 mb-1">Session ID:</p>
            <div className="flex items-center gap-2 bg-gray-50 p-2 rounded-lg">
              <code className="text-xs font-mono text-gray-700 flex-1 break-all">
                {sessionId}
              </code>
              <button
                onClick={copySessionId}
                className="p-1 hover:bg-gray-200 rounded transition flex-shrink-0"
                title="Copy session ID"
              >
                {showCopied ? (
                  <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* Clear Session Button */}
          <div className="flex items-center gap-2">
            <button
              onClick={onClearSession}
              className="text-sm text-red-600 hover:text-red-800 hover:bg-red-50 px-3 py-1 rounded transition"
            >
              Clear Session Data
            </button>
            <InfoTooltip content="This will clear your current conversation history and start a fresh session. Your previous messages will be permanently deleted." />
          </div>
        </div>
      )}
    </div>
  );
};
