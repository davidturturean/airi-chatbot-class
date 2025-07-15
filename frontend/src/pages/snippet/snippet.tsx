import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { API_URL } from '../../constants';

interface Snippet {
  content: string;
  file_type: string;
}

export function SnippetViewer() {
  const { snippetId } = useParams<{ snippetId: string }>();
  const [snippet, setSnippet] = useState<Snippet | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSnippet = async () => {
      try {
        const response = await fetch(`${API_URL}/api/snippet/${snippetId}`);
        if (response.ok) {
          const data = await response.json();
          setSnippet(data);
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

  if (!snippet) {
    return <div>Loading...</div>;
  }

  const urlParams = new URLSearchParams(window.location.search);
  const searchTerms = urlParams.get('q')?.split(' ') || [];

  return (
    <div>
      <h1>Snippet Viewer</h1>
      <SnippetRenderer snippet={{...snippet, search_terms: searchTerms}} />
    </div>
  );
}
