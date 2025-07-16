import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { SnippetRenderer } from '../../components/snippet-renderer';

export function SnippetPage() {
  const { fileName } = useParams<{ fileName: string }>();
  const [snippet, setSnippet] = useState<{ content: string; file_type: string; search_terms: string[] } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSnippet = async () => {
      try {
        const response = await fetch(`/api/snippet/${fileName}`);
        if (!response.ok) {
          throw new Error('Snippet not found');
        }
        const data = await response.json();
        setSnippet(data);
      } catch (error) {
        setError((error as Error).message);
      }
    };

    if (fileName) {
      fetchSnippet();
    }
  }, [fileName]);

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!snippet) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>{fileName}</h1>
      <SnippetRenderer snippet={snippet} />
    </div>
  );
}
