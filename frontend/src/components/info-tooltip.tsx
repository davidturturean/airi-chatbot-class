import React from 'react';

interface InfoTooltipProps {
  content: string;
  className?: string;
}

export const InfoTooltip: React.FC<InfoTooltipProps> = ({ content, className = "" }) => {
  return (
    <div className={`relative group inline-block ${className}`}>
      {/* Question mark icon */}
      <svg 
        className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-help transition-colors" 
        fill="none" 
        viewBox="0 0 24 24" 
        stroke="currentColor"
        strokeWidth={2}
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" 
        />
      </svg>
      
      {/* Tooltip */}
      <div className="absolute hidden group-hover:block z-50 w-64 p-3 mt-1 text-xs bg-gray-900 text-white rounded-lg shadow-lg left-0">
        <div className="relative">
          {content}
          {/* Arrow pointing up */}
          <div className="absolute -top-5 left-2 w-0 h-0 border-l-4 border-l-transparent border-r-4 border-r-transparent border-b-4 border-b-gray-900"></div>
        </div>
      </div>
    </div>
  );
};