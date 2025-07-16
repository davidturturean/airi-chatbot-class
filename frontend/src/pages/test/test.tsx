import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function TestPage() {
  const markdown = `[This is a link](https://www.google.com)`;

  return (
    <div>
      <h1>Test Page</h1>
      <ReactMarkdown
        components={{
          a: ({ node, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline" />,
        }}
        remarkPlugins={[remarkGfm]}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
