/**
 * Panel State Management Context
 * Global state for slideout panel with history tracking
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import type { PanelState } from '../types/document-preview';

interface PanelContextValue extends PanelState {
  openPanel: (rid: string, documentType?: 'text' | 'excel' | 'word' | 'pdf' | 'image') => void;
  closePanel: () => void;
  togglePin: () => void;
  navigateTo: (rid: string) => void;
  goBack: () => void;
  goForward: () => void;
  canGoBack: boolean;
  canGoForward: boolean;
  navigationCounter: number;  // Increments on every openPanel call to trigger re-navigation
}

const PanelContext = createContext<PanelContextValue | undefined>(undefined);

interface PanelProviderProps {
  children: ReactNode;
}

export const PanelProvider: React.FC<PanelProviderProps> = ({ children }) => {
  const [state, setState] = useState<PanelState>({
    isOpen: false,
    isPinned: false,
    currentRid: null,
    documentType: null,
    history: [],
    historyIndex: -1
  });

  // Navigation counter to force re-navigation even when clicking the same RID
  const [navigationCounter, setNavigationCounter] = useState(0);

  const openPanel = useCallback((rid: string, documentType: 'text' | 'excel' | 'word' | 'pdf' | 'image' = 'text') => {
    setState(prev => {
      // Add to history if it's different from current
      const newHistory = prev.currentRid !== rid
        ? [...prev.history.slice(0, prev.historyIndex + 1), rid]
        : prev.history;

      const newIndex = prev.currentRid !== rid
        ? newHistory.length - 1
        : prev.historyIndex;

      return {
        ...prev,
        isOpen: true,
        currentRid: rid,
        documentType,
        history: newHistory,
        historyIndex: newIndex
      };
    });

    // Increment navigation counter to trigger re-navigation in Excel viewer
    // This allows scrolling back to source even when clicking same RID
    setNavigationCounter(prev => prev + 1);
  }, []);

  const closePanel = useCallback(() => {
    setState(prev => ({
      ...prev,
      isOpen: false,
      // Keep currentRid and history for reopening
    }));
  }, []);

  const togglePin = useCallback(() => {
    setState(prev => ({
      ...prev,
      isPinned: !prev.isPinned
    }));
  }, []);

  const navigateTo = useCallback((rid: string) => {
    setState(prev => {
      const newHistory = [...prev.history.slice(0, prev.historyIndex + 1), rid];
      return {
        ...prev,
        currentRid: rid,
        history: newHistory,
        historyIndex: newHistory.length - 1
      };
    });
  }, []);

  const goBack = useCallback(() => {
    setState(prev => {
      if (prev.historyIndex <= 0) return prev;

      const newIndex = prev.historyIndex - 1;
      return {
        ...prev,
        currentRid: prev.history[newIndex],
        historyIndex: newIndex
      };
    });
  }, []);

  const goForward = useCallback(() => {
    setState(prev => {
      if (prev.historyIndex >= prev.history.length - 1) return prev;

      const newIndex = prev.historyIndex + 1;
      return {
        ...prev,
        currentRid: prev.history[newIndex],
        historyIndex: newIndex
      };
    });
  }, []);

  const value: PanelContextValue = {
    ...state,
    openPanel,
    closePanel,
    togglePin,
    navigateTo,
    goBack,
    goForward,
    canGoBack: state.historyIndex > 0,
    canGoForward: state.historyIndex < state.history.length - 1,
    navigationCounter
  };

  return (
    <PanelContext.Provider value={value}>
      {children}
    </PanelContext.Provider>
  );
};

export const usePanel = () => {
  const context = useContext(PanelContext);
  if (!context) {
    throw new Error('usePanel must be used within a PanelProvider');
  }
  return context;
};
