// context/ChatContext.tsx
import { createContext, useContext, useState, useRef } from "react";
import { message } from "../interfaces/interfaces";
import { v4 as uuidv4 } from "uuid";
import { useSidebar } from "./SidebarContext";

const WELCOME: message = {
  content: "Hi! I'm your AI assistant to help you navigate the AI Risk repository. How can I help you today?",
  role: 'assistant',
  id: uuidv4(),
};

const API_URL = '';

// Helper to get or create session ID
const getSessionId = (): string => {
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

    const loadingMessage: message = { content: 'Loading...', role: 'assistant', id: 'loading' };
    setCurrentMessage(loadingMessage);

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

      if (!stream.body) throw new Error('Failed!!');

      const reader = stream.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let buffer = '';
      let accumulatedText = '';

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

              const isStatusMessage =
                typeof parsed === "string" &&
                (
                  parsed.startsWith("Processing") ||
                  parsed.startsWith("Analyzing") ||
                  parsed.startsWith("Searching") ||
                  parsed.startsWith("Generating") ||
                  parsed.startsWith("Found") ||
                  parsed.startsWith("Retrieving") ||
                  parsed.startsWith("Using") ||
                  parsed.startsWith("No specific documents") ||
                  parsed.startsWith("Using general knowledge")
                );

              if (isStatusMessage) {
                // Optionally show this briefly in the UI via some loading bar/spinner
                const currMess: message = { content: parsed, role: 'assistant', id: uuidv4() };
                setCurrentMessage(currMess);
                continue;
              }
              
              if (parsed.related_documents) {
                setRelatedDocuments(parsed.related_documents);
              } else if (parsed.language) {
                // Update session language when received from backend
                setSessionLanguage(parsed.language);
              } else {
                accumulatedText += parsed;
                const currMess: message = { content: accumulatedText, role: 'assistant', id: uuidv4() };
                setCurrentMessage(currMess);
              }
            } catch (err) {
              console.error('Error parsing line:', line, err);
            }
          }
        }
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
      const errorMessage: message = {
        content: 'Error talking to server.',
        role: 'assistant',
        id: uuidv4(),
      };
      setPreviousMessages((prev) => [...prev, errorMessage]);
      setCurrentMessage(null);
    } finally {
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