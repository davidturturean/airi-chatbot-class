import { Chat } from '../../components/chat';
import { Header } from '../../components/header';
import { useSidebar } from '@/context/SidebarContext';
import { useChat } from '@/context/ChatContext';

export function FullChat() {

  const { previousMessages, currentMessage, handleSubmit, isLoading } = useChat();
  const { domain, setDomain, relatedDocuments, suggestedUseCases, handleDomainSubmit } = useSidebar();

  const handleFileClick = async (url: string) => {
    const snippetId = url.split('/').pop();
    window.open(`/snippet/${snippetId}`, '_blank', 'noopener,noreferrer');
  };


  const defaultUseCases = ['Medical chatbot', 'Customer service agent', 'Model risk review'];

  return (
    <div className="min-h-screen bg-gray-50 text-black flex flex-col">
      <Header />

      <main className="flex-1 p-6 xl:p-10 grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left Section – Text + Chat + Example Inputs */}
        <div className="xl:col-span-2 space-y-6">
          {/* 0. Text Explainer */}
          <section className="space-y-2">
            <h2 className="text-2xl font-bold text-gray-800">AI Risk Assistant</h2>
            <p className="text-sm text-gray-600 leading-relaxed">
              This assistant helps you explore and assess AI risk factors, drawing from the AI Risk Index. You can
              ask about governance frameworks, benchmarks, mitigations, and more.
            </p>
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

          <div className="bg-white border rounded-xl p-4 shadow-sm">
            {/** TODO: attach a model to suggest use for use cases for different types of users */}
            <h3 className="text-md font-semibold mb-2">Example Use Cases</h3>
            <div className="flex flex-col sm:flex-row gap-2 items-start sm:items-end">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-600 mb-1">Enter your domain or field:</label>
                <input
                  type="text"
                  placeholder="e.g. education, finance, healthcare"
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

          <div className="bg-white border rounded-xl p-4 shadow-sm">
            <h3 className="text-md font-semibold mb-2">Request Types</h3>
            <span className="text-gray-500">Try asking about:</span>
            {['Risk Taxonomies', 'Benchmarks', 'Mitigations'].map((type) => (
              <button
                key={type}
                onClick={() => handleSubmit(type)}
                className="bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-full"
              >
                {type}
              </button>
            ))}
          </div>
        </aside>
      </main>
    </div>
  );
}