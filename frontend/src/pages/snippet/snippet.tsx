import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
const API_URL = '';

import { SnippetRenderer } from '../../components/snippet-renderer';

export function SnippetViewer() {
  const { snippetId } = useParams<{ snippetId: string }>();
  const [snippetContent, setSnippetContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSnippet = async () => {
      try {
        const response = await fetch(`${API_URL}/api/file-content?path=${snippetId}`);
        if (response.ok) {
          const data = await response.text();
          setSnippetContent(data);
        } else {
          setError('Failed to fetch snippet');
        }
      } catch (error) {
        setError('Error fetching snippet');
      }
    };

    fetchSnippet();
  }, [snippetId]);

  if (error) {
    return <div>{error}</div>;
  }

  if (!snippetContent) {
    return <div>Loading...</div>;
  }

  const urlParams = new URLSearchParams(window.location.search);
  const searchTerms = urlParams.get('q')?.split(' ') || [];
  const fileType = snippetId?.split('.').pop() || 'txt';

  return (
    <div>
      <h1>Snippet Viewer</h1>
      <SnippetRenderer snippet={{content: snippetContent, file_type: fileType, search_terms: searchTerms}} />
    </div>
  );
}
