import { Link, useNavigate } from 'react-router-dom';

export const Header = () => {
  const navigate = useNavigate();

  // Check if we're inside an iframe
  const isInIframe = window.self !== window.top;

  // Detect if we're embedded in Webflow (check parent domain)
  const isInWebflow = isInIframe && (
    window.location.search.includes('from=webflow') ||
    window.location.search.includes('source=widget')
  );

  const handleNavigation = (path: string, webflowPath: string) => {
    if (isInWebflow) {
      // Navigate parent window to Webflow page
      try {
        window.top!.location.href = `https://ai-risk-repository-601932-8fac479478ab1.webflow.io${webflowPath}`;
      } catch (e) {
        // Fallback if cross-origin prevents access
        window.open(`https://ai-risk-repository-601932-8fac479478ab1.webflow.io${webflowPath}`, '_blank');
      }
    } else {
      // Normal React Router navigation
      navigate(path);
    }
  };

  return (
    <header className="flex items-center justify-between h-16 px-4 bg-white border-b border-gray-200">
      <div className="text-lg font-medium text-gray-800">AIRI Assistant</div>
      <nav className="space-x-4 text-sm text-gray-600">
        {isInWebflow ? (
          <>
            <button
              onClick={() => handleNavigation('/', '/')}
              className="hover:text-black transition-colors cursor-pointer bg-transparent border-none text-gray-600"
            >
              Home
            </button>
            <button
              onClick={() => handleNavigation('/chat', '/chatbot')}
              className="hover:text-black transition-colors cursor-pointer bg-transparent border-none text-gray-600"
            >
              Chat
            </button>
          </>
        ) : (
          <>
            <Link
              to="/"
              className="hover:text-black transition-colors"
            >
              Home
            </Link>
            <Link
              to="/chat"
              className="hover:text-black transition-colors"
            >
              Chat
            </Link>
          </>
        )}
      </nav>
    </header>
  );
};