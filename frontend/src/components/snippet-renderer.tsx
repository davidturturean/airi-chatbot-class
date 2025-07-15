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

  const renderTextBasedContent = () => (
    <pre>
      <Highlighter
        highlightClassName="bg-yellow-200"
        searchWords={search_terms}
        autoEscape={true}
        textToHighlight={content}
      />
    </pre>
  );

  const renderDownloadLink = () => {
    const blob = new Blob([content], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    return (
      <div>
        <p>This file type cannot be displayed. You can download it instead.</p>
        <a href={url} download={`snippet.${file_type}`}>
          Download snippet
        </a>
      </div>
    );
  };

  switch (file_type) {
    case 'txt':
    case 'text':
      return renderTextBasedContent();
    case 'md':
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
    case 'xlsx':
    case 'docx':
      return renderDownloadLink();
    default:
      return renderTextBasedContent();
  }
};
