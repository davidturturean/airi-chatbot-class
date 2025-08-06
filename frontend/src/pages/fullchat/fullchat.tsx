import { Chat } from '../../components/chat';
import { Header } from '../../components/header';
import { SnippetModal } from '../../components/snippet-modal';
import { InfoTooltip } from '../../components/info-tooltip';
import { LanguageSelector } from '../../components/language-selector';
import { useSidebar } from '@/context/SidebarContext';
import { useChat } from '@/context/ChatContext';
import { useState, useEffect } from 'react';

export function FullChat() {

  const { previousMessages, currentMessage, handleSubmit, isLoading, sessionId, clearSession, sessionLanguage, setSessionLanguage } = useChat();
  const { domain, setDomain, relatedDocuments, suggestedUseCases, handleDomainSubmit } = useSidebar();
  
  // Modal state for snippet display
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedRid, setSelectedRid] = useState<string | null>(null);

  const handleFileClick = async (url: string) => {
    // Extract RID or META ID from URL and open modal
    const ridMatch = url.match(/RID-\d{5}/);
    const metaMatch = url.match(/META-\d{5}/);
    
    if (ridMatch) {
      setSelectedRid(ridMatch[0]);
      setIsModalOpen(true);
    } else if (metaMatch) {
      setSelectedRid(metaMatch[0]);
      setIsModalOpen(true);
    } else if (url.startsWith('metadata://')) {
      // Handle legacy metadata URLs
      alert('This is a metadata query result. Please refresh the query to see the updated format.');
    } else {
      // Fallback to original behavior for other URLs
      const snippetId = url.split('/').pop();
      if (snippetId && (snippetId.startsWith('RID-') || snippetId.startsWith('META-'))) {
        setSelectedRid(snippetId);
        setIsModalOpen(true);
      } else {
        window.open(`/snippet/${snippetId}`, '_blank', 'noopener,noreferrer');
      }
    }
  };

  // Listen for snippet modal events from chat component
  useEffect(() => {
    const handleOpenSnippetModal = (event: CustomEvent) => {
      const { rid } = event.detail;
      if (rid) {
        setSelectedRid(rid);
        setIsModalOpen(true);
      }
    };

    window.addEventListener('openSnippetModal', handleOpenSnippetModal as EventListener);
    
    return () => {
      window.removeEventListener('openSnippetModal', handleOpenSnippetModal as EventListener);
    };
  }, []);


  const defaultUseCases = ['Medical chatbot', 'Customer service agent', 'Model risk review'];

  return (
    <div className="min-h-screen bg-gray-50 text-black flex flex-col">
      <Header />

      <main className="flex-1 p-6 xl:p-10 grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left Section – Text + Chat + Example Inputs */}
        <div className="xl:col-span-2 space-y-6">
          {/* 0. Text Explainer */}
          <section className="space-y-2">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-gray-800">AI Risk Assistant</h2>
                <p className="text-sm text-gray-600 leading-relaxed mt-2">
                  This assistant helps you explore and assess AI risk factors, drawing from the AI Risk Index. You can
                  ask about governance frameworks, benchmarks, mitigations, and more.
                </p>
              </div>
              <div className="ml-4">
                <LanguageSelector
                  sessionId={sessionId}
                  currentLanguage={sessionLanguage}
                  onLanguageChange={setSessionLanguage}
                />
              </div>
            </div>
              <div className="bg-white border rounded-xl p-4 shadow-sm">
                <p className="text-sm text-gray-600 leading-relaxed">
              We are currently collecting message histories to improve user experience. Please be advised that your conversations will be stored in our database.
            </p>
          </div>
          </section>

          {/* Chat Component */}
          <div className="bg-white rounded-xl shadow border p-4 h-[80vh] overflow-y-auto">
            <Chat previousMessages={previousMessages} currentMessage={currentMessage} handleSubmit={handleSubmit} isLoading={isLoading} />
          </div>
        </div>

        {/* 1. Right Panel – Related Docs, Frameworks, Benchmarks */}
        <aside className="space-y-6 hidden xl:block">
          <div className="bg-white border rounded-xl p-4 shadow-sm">
            <h3 className="text-md font-semibold mb-2">Related Documents</h3>
            <ul className="text-sm text-gray-600 space-y-2">
              {relatedDocuments.length > 0 ? (
                relatedDocuments.map((doc, index) => (
                  <li key={index}>
                    <button onClick={() => handleFileClick(doc.url)} className="text-blue-600 underline">
                      {doc.title}
                    </button>
                  </li>
                ))
              ) : (
                <li>No documents yet. Submit a request to populate this area.</li>
              )}
            </ul>
          </div>

          <div className="bg-white border-2 border-gray-200 rounded-xl p-5 shadow-sm">
            <h3 className="text-md font-semibold mb-1 flex items-center gap-2">
              Get Personalized Questions
              <InfoTooltip content="Based on what you tell us about your role or area of interest, we'll suggest specific AI risk questions you should consider. For example, educators might ask about AI in grading, while developers might focus on model safety." />
            </h3>
            <p className="text-xs text-gray-500 mb-3">
              Tell us your role, field, or interest area for personalized AI risk questions
            </p>
            <div className="flex flex-col sm:flex-row gap-2 items-start sm:items-end">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-600 mb-1">I'm interested to learn more about AI risks in:</label>
                <input
                  type="text"
                  placeholder="e.g., education, healthcare, research, policy, startup"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-red-400"
                />
              </div>
              <button
                onClick={handleDomainSubmit}
                className="bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-600 transition text-sm"
              >
                Generate Use Cases
              </button>
            </div>

            {/* Suggested Domains */}
            <div className="space-y-2">
              <h4 className="text-sm text-gray-600 font-semibold">Suggested Domains</h4>
              <div className="flex flex-wrap gap-2">
                {defaultUseCases.map((uc) => (
                  <button
                    key={uc}
                    onClick={() => {
                      setDomain(uc);
                      handleDomainSubmit();
                    }}
                    className="bg-red-100 text-red-700 text-sm px-3 py-1 rounded-full hover:bg-red-200 transition"
                  >
                    {uc}
                  </button>
                ))}
              </div>
            </div>

            {/* Suggested Use Cases */}
            {suggestedUseCases.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm text-gray-600 font-semibold">Suggested Use Cases</h4>
                <div className="flex flex-wrap gap-2">
                  {suggestedUseCases.map((uc, i) => (
                    <button
                      key={`suggested-${i}`}
                      onClick={() => handleSubmit(uc)}
                      className="bg-gray-100 text-gray-700 text-sm px-3 py-1 rounded-full hover:bg-gray-200 transition"
                    >
                      {uc}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
            <h3 className="text-md font-semibold mb-1 flex items-center gap-2">
              Or Explore General Topics
              <InfoTooltip content="Explore different types of AI risk information: Risk Taxonomies (how we categorize risks), Benchmarks (evaluation criteria), and Mitigations (strategies to reduce risks)." />
            </h3>
            <p className="text-xs text-gray-500 mb-2">Find out more about our repository's structure by category</p>
            <div className="flex flex-wrap gap-2">
              {['Risk Taxonomies', 'Benchmarks', 'Mitigations'].map((type) => (
                <button
                  key={type}
                  onClick={() => handleSubmit(type)}
                  className="bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-full text-sm transition"
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
          
          {/* Session management */}
          <div className="bg-white border rounded-xl p-4 shadow-sm">
            <h3 className="text-md font-semibold mb-2">Session</h3>
            <p className="text-xs text-gray-500 mb-2">ID: {sessionId.slice(0, 8)}...</p>
            <button
              onClick={clearSession}
              className="text-sm text-red-600 hover:text-red-800"
            >
              Clear Session Data
            </button>
          </div>
        </aside>
      </main>
      
      {/* Snippet Modal */}
      <SnippetModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedRid(null);
        }}
        rid={selectedRid}
        sessionId={sessionId}
      />
    </div>
  );
}