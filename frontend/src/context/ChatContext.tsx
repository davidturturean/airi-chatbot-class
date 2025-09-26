// context/ChatContext.tsx
import { createContext, useContext, useState, useRef, useEffect } from "react";
import { message } from "../interfaces/interfaces";
import { v4 as uuidv4 } from "uuid";
import { useSidebar } from "./SidebarContext";
import { trackQuery, trackResponse, trackError } from "../utils/analytics";

const WELCOME: message = {
  content: "Hi! I'm your AI assistant to help you navigate the AI Risk repository. How can I help you today?",
  role: 'assistant',
  id: uuidv4(),
};

const API_URL = '';

// Helper to get or create session ID
const getSessionId = (): string => {
  // First check URL parameters for session from widget
  const urlParams = new URLSearchParams(window.location.search);
  const urlSession = urlParams.get('session');
  
  if (urlSession) {
    // Session passed from widget, use it
    console.log('Using session from URL:', urlSession);
    localStorage.setItem('airi_session_id', urlSession);
    return urlSession;
  }
  
  // Otherwise check localStorage
  let sessionId = localStorage.getItem('airi_session_id');
  if (!sessionId) {
    sessionId = uuidv4();
    localStorage.setItem('airi_session_id', sessionId);
  }
  return sessionId;
};

interface LanguageInfo {
  code: string;
  native_name: string;
  english_name: string;
  category: string;
}

interface ChatContextType {
  previousMessages: message[];
  currentMessage: message | null;
  isLoading: boolean;
  handleSubmit: (text?: string) => Promise<void>;
  setPreviousMessages: React.Dispatch<React.SetStateAction<message[]>>;
  setCurrentMessage: React.Dispatch<React.SetStateAction<message | null>>;
  sessionId: string;
  clearSession: () => Promise<void>;
  sessionLanguage: LanguageInfo | null;
  setSessionLanguage: (language: LanguageInfo) => void;
}

const ChatContext = createContext<ChatContextType | null>(null);

export const ChatProvider = ({ children }: { children: React.ReactNode }) => {
  const [previousMessages, setPreviousMessages] = useState<message[]>([WELCOME]);
  const { setRelatedDocuments } = useSidebar();
  const [currentMessage, setCurrentMessage] = useState<message | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const messageHandlerRef = useRef<((event: MessageEvent) => void) | null>(null);
  const [sessionId] = useState<string>(getSessionId());
  const [sessionLanguage, setSessionLanguage] = useState<LanguageInfo | null>(null);

  // Load existing messages if coming from widget with session
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const fromWidget = urlParams.get('from') === 'widget';
    const sessionFromUrl = urlParams.get('session');
    
    if (fromWidget && sessionFromUrl && !localStorage.getItem('airi_session_initialized')) {
      // Load messages from backend for this session
      loadSessionMessages(sessionFromUrl);
      // Mark as initialized to avoid duplicate loads
      localStorage.setItem('airi_session_initialized', 'true');
    }
  }, []);

  const loadSessionMessages = async (sessionId: string) => {
    try {
      const response = await fetch(`${API_URL}api/session/${sessionId}/messages`);
      if (response.ok) {
        const data = await response.json();
        if (data.messages && data.messages.length > 0) {
          // Convert backend messages to frontend format
          const messages: message[] = data.messages.map((msg: any) => ({
            content: msg.content,
            role: msg.role,
            id: msg.id || uuidv4()
          }));
          setPreviousMessages(messages);
          console.log(`Loaded ${messages.length} messages from session`);
        }
      }
    } catch (error) {
      console.error('Failed to load session messages:', error);
    }
  };

  const cleanupMessageHandler = () => {
    if (messageHandlerRef.current) {
      messageHandlerRef.current = null;
    }
  };

  const clearSession = async () => {
    try {
      await fetch(`${API_URL}api/session/${sessionId}/clear`, {
        method: 'DELETE',
      });
      
      // Clear local storage and reset
      localStorage.removeItem('airi_session_id');
      localStorage.removeItem('airi_session_initialized');
      window.location.reload();
    } catch (error) {
      console.error('Failed to clear session:', error);
    }
  };

  async function handleSubmit(text?: string) {
    if (isLoading) return;
    const messageText = text;
    if (!messageText || !messageText.trim()) return;

    const userMessage: message = { content: messageText, role: 'user', id: uuidv4() };
    setPreviousMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    
    // Track query submission
    trackQuery(messageText, sessionLanguage?.code);

    const loadingMessage: message = { content: '🔄 Initializing...', role: 'assistant', id: 'loading', isStatus: true };
    setCurrentMessage(loadingMessage);
    
    // Set up a timeout to show a message if processing takes too long
    const timeoutId = setTimeout(() => {
      if (isLoading) {
        const timeoutMsg: message = { 
          content: '⚠️ This is taking longer than expected. The embedding service may be initializing for the first time. Please wait...', 
          role: 'assistant', 
          id: 'timeout',
          isStatus: true 
        };
        setCurrentMessage(timeoutMsg);
      }
    }, 15000); // 15 seconds (increased since we now have 30s timeout)

    try {
      const stream = await fetch(`${API_URL}api/v1/stream`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Session-ID': sessionId 
        },
        body: JSON.stringify({ 
          message: messageText,
          session_id: sessionId,
          language_code: sessionLanguage?.code  // Pass selected language if set
        }),
      });

      if (!stream.ok) {
        throw new Error(`HTTP ${stream.status}: ${stream.statusText || 'Request failed'}`);
      }

      if (!stream.body) {
        throw new Error('No response body received from server');
      }

      const reader = stream.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let buffer = '';
      let accumulatedText = '';
      const queryStartTime = Date.now(); // Track actual query start time

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        buffer += decoder.decode(value, { stream: !done });

        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (line.trim()) {
            try {
              const parsed = JSON.parse(line);
              
              // TYPE 1: Status messages with explicit type field
              if (parsed && typeof parsed === 'object' && 'type' in parsed) {
                if (parsed.type === 'status' && parsed.status) {
                  // Enhanced status messages with specific icons
                  let statusIcon = '⏳';
                  let statusText = parsed.status;
                  
                  // Match specific stages for better UX
                  if (parsed.stage === 'init' || statusText.includes('Initializing')) {
                    statusIcon = '🔄';
                  } else if (parsed.stage === 'classification' || statusText.includes('Classifying')) {
                    statusIcon = '🧠';
                  } else if (parsed.stage === 'retrieval' || statusText.includes('Searching')) {
                    statusIcon = '🔍';
                  } else if (parsed.stage === 'generation' || statusText.includes('Generating')) {
                    statusIcon = '✨';
                  } else if (parsed.stage === 'analysis' || statusText.includes('Analyzing')) {
                    statusIcon = '📊';
                  }
                  
                  const fullStatusText = `${statusIcon} ${statusText}`;
                  const currMess: message = { 
                    content: fullStatusText, 
                    role: 'assistant', 
                    id: 'status-' + (parsed.stage || 'update'),
                    isStatus: true 
                  };
                  setCurrentMessage(currMess);
                  continue;
                }
                // Skip any other typed objects that aren't status
                continue;
              }
              
              // TYPE 2: String content (actual response text)
              if (typeof parsed === 'string') {
                // Check for legacy status messages
                const statusPrefixes = [
                  "Processing", "Analyzing", "Searching", "Generating",
                  "Found", "Retrieving", "Using", "No specific documents",
                  "Using general knowledge", "Classifying", "Initializing",
                  "Validating", "Enhancing"
                ];
                const isStatusMessage = statusPrefixes.some(prefix => parsed.startsWith(prefix));
                
                if (isStatusMessage) {
                  // Use appropriate icon for legacy status messages
                  let statusIcon = '⏳';
                  if (parsed.includes('Initializing')) statusIcon = '🔄';
                  else if (parsed.includes('Classifying')) statusIcon = '🧠';
                  else if (parsed.includes('Searching') || parsed.includes('Retrieving')) statusIcon = '🔍';
                  else if (parsed.includes('Generating')) statusIcon = '✨';
                  else if (parsed.includes('Analyzing')) statusIcon = '📊';
                  else if (parsed.includes('Processing')) statusIcon = '⚙️';
                  
                  const currMess: message = { 
                    content: `${statusIcon} ${parsed}`, 
                    role: 'assistant', 
                    id: uuidv4(),
                    isStatus: true 
                  };
                  setCurrentMessage(currMess);
                } else {
                  // This is actual message content
                  accumulatedText += parsed;
                  const currMess: message = { 
                    content: accumulatedText, 
                    role: 'assistant', 
                    id: uuidv4() 
                  };
                  setCurrentMessage(currMess);
                }
                continue;
              }
              
              // TYPE 3: Known object types
              if (parsed && typeof parsed === 'object') {
                // Related documents
                if ('related_documents' in parsed && Array.isArray(parsed.related_documents)) {
                  setRelatedDocuments(parsed.related_documents);
                  continue;
                }
                
                // Language info
                if ('language' in parsed && parsed.language) {
                  setSessionLanguage(parsed.language);
                  continue;
                }
                
                // Metrics data
                if ('metrics' in parsed) {
                  // Store metrics for later use but don't display
                  console.log('Received metrics:', parsed.metrics);
                  continue;
                }
                
                // Error messages
                if ('error' in parsed) {
                  console.error('Stream error:', parsed.error);
                  const errorMess: message = {
                    content: `Error: ${parsed.error}`,
                    role: 'assistant',
                    id: uuidv4(),
                    isStatus: false
                  };
                  setCurrentMessage(errorMess);
                  continue;
                }
                
                // Unknown object - log but don't display
                console.warn('Received unknown object type:', parsed);
                continue;
              }
              
              // TYPE 4: Fallback for anything else
              console.warn('Unexpected parsed type:', typeof parsed, parsed);
              
            } catch (err) {
              console.error('Error parsing line:', line, err);
            }
          }
        }
      }

      // Track successful response
      if (accumulatedText) {
        trackResponse({
          latency_ms: Date.now() - queryStartTime, // Accurate latency from query start
          citations_count: (accumulatedText.match(/RID-\d+/g) || []).length, // Count RID citations
          response_length: accumulatedText.length
        });
      }
      
      const botMessage: message = {
        content: accumulatedText,
        role: 'assistant',
        id: uuidv4(),
      };

      setPreviousMessages((prev) => [...prev, botMessage]);
      setCurrentMessage(null);
    } catch (error) {
      console.error('Error sending message:', error);
      // Track error
      trackError('stream_error', error instanceof Error ? error.message : 'Unknown error');
      
      const errorMessage: message = {
        content: 'Error talking to server.',
        role: 'assistant',
        id: uuidv4(),
      };
      setPreviousMessages((prev) => [...prev, errorMessage]);
      setCurrentMessage(null);
    } finally {
      clearTimeout(timeoutId);
      setIsLoading(false);
      cleanupMessageHandler();
    }
  }

  return (
    <ChatContext.Provider value={{
      previousMessages,
      currentMessage,
      isLoading,
      handleSubmit,
      setPreviousMessages,
      setCurrentMessage,
      sessionId,
      clearSession,
      sessionLanguage,
      setSessionLanguage,
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};