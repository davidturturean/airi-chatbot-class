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
const API_URL=''
const ChatContext = createContext<any>(null);

export const ChatProvider = ({ children }: { children: React.ReactNode }) => {
  const [previousMessages, setPreviousMessages] = useState<message[]>([WELCOME]);
  const { setRelatedDocuments } = useSidebar(); // <-- use the setter
  const [currentMessage, setCurrentMessage] = useState<message | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const messageHandlerRef = useRef<((event: MessageEvent) => void) | null>(null);

  const cleanupMessageHandler = () => {
    if (messageHandlerRef.current) {
      messageHandlerRef.current = null;
    }
  };

  async function handleSubmit(text?: string) {
    if (isLoading) return;
    const messageText = text;
    if (!messageText || !messageText.trim()) return;

    const userMessage: message = { content: messageText, role: 'user', id: uuidv4() };
    setPreviousMessages((prev) => [...prev, userMessage]);

    const loadingMessage: message = { content: 'Loading...', role: 'assistant', id: 'loading' };
    setCurrentMessage(loadingMessage);

    try {
      const stream = await fetch(`${API_URL}api/v1/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText }),
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
                  parsed.startsWith("No specific documents") ||
                  parsed.startsWith("Using general knowledge")
                );

              if (isStatusMessage) {
                // Optionally show this briefly in the UI via some loading bar/spinner
                  const currMess: message = { content: parsed, role: 'assistant', id: uuidv4() };
                  setCurrentMessage(currMess);
                  continue
               }
               if (parsed.related_documents) {
                     setRelatedDocuments(parsed.related_documents);
                }
                else {
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
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => useContext(ChatContext);
