import React from 'react';
import ReactMarkdown from 'react-markdown';
import Highlighter from 'react-highlight-words';

interface SnippetRendererProps {
  snippet: {
    content: string;
    file_type: string;
    search_terms: string[];
  };
}

export const SnippetRenderer: React.FC<SnippetRendererProps> = ({ snippet }) => {
  const { content, file_type, search_terms } = snippet;

  switch (file_type) {
    case 'text':
      return (
        <pre>
          <Highlighter
            highlightClassName="bg-yellow-200"
            searchWords={search_terms}
            autoEscape={true}
            textToHighlight={content}
          />
        </pre>
      );
    case 'markdown':
      return (
        <ReactMarkdown
          components={{
            p: ({ node, ...props }) => (
              <p>
                <Highlighter
                  highlightClassName="bg-yellow-200"
                  searchWords={search_terms}
                  autoEscape={true}
                  textToHighlight={props.children ? props.children.toString() : ''}
                />
              </p>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      );
    default:
      return (
        <pre>
          <Highlighter
            highlightClassName="bg-yellow-200"
            searchWords={search_terms}
            autoEscape={true}
            textToHighlight={content}
          />
        </pre>
      );
  }
};
