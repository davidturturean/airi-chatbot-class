// context/SidebarContext.tsx
import { createContext, useContext, useState } from "react";

interface RelatedDoc {
  title: string;
  url: string;
}

interface SidebarContextProps {
  domain: string;
  setDomain: (domain: string) => void;
  relatedDocuments: RelatedDoc[];
  setRelatedDocuments: (docs: RelatedDoc[]) => void;
  suggestedUseCases: string[];
  handleDomainSubmit: () => Promise<void>;
}

const SidebarContext = createContext<SidebarContextProps | null>(null);

const API_URL = "";

export const SidebarProvider = ({ children }: { children: React.ReactNode }) => {
  const [domain, setDomain] = useState("");
  const [relatedDocuments, setRelatedDocuments] = useState<RelatedDoc[]>([]);
  const [suggestedUseCases, setSuggestedUseCases] = useState<string[]>([]);

  const handleDomainSubmit = async () => {
    if (!domain.trim()) return;

    try {
      const response = await fetch(`${API_URL}api/v1/use_cases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain }),
      });

      if (!response.ok) throw new Error("Failed to fetch use cases");

      const data = await response.json();
      setSuggestedUseCases(data.use_cases || []);
    } catch (error) {
      console.error("Error fetching use cases:", error);
      setSuggestedUseCases(["Error fetching use cases. Please try again."]);
    }
  };

  return (
    <SidebarContext.Provider
      value={{
        domain,
        setDomain,
        relatedDocuments,
        setRelatedDocuments,
        suggestedUseCases,
        handleDomainSubmit,
      }}
    >
      {children}
    </SidebarContext.Provider>
  );
};

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
};