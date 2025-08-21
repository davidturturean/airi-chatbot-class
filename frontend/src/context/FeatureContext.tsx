import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface FeatureMetadata {
  label: string;
  description: string;
  category: string;
  requiresRestart: boolean;
  value: boolean;
  default: boolean;
}

interface FeatureConfig {
  flags: Record<string, FeatureMetadata>;
  categories: Record<string, string>;
}

interface FeatureContextType {
  features: Record<string, boolean>;
  featureConfig: FeatureConfig | null;
  loading: boolean;
  error: string | null;
  updateFeature: (flagName: string, value: boolean) => Promise<void>;
  updateMultipleFeatures: (updates: Record<string, boolean>) => Promise<void>;
  resetToDefaults: () => Promise<void>;
  refreshFeatures: () => Promise<void>;
  isSidebarEnabled: boolean;
}

const FeatureContext = createContext<FeatureContextType | undefined>(undefined);

export const useFeatures = () => {
  const context = useContext(FeatureContext);
  if (!context) {
    throw new Error('useFeatures must be used within a FeatureProvider');
  }
  return context;
};

interface FeatureProviderProps {
  children: ReactNode;
}

export const FeatureProvider: React.FC<FeatureProviderProps> = ({ children }) => {
  const [features, setFeatures] = useState<Record<string, boolean>>({});
  const [featureConfig, setFeatureConfig] = useState<FeatureConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSidebarEnabled, setIsSidebarEnabled] = useState(false);

  // Fetch features from backend
  const fetchFeatures = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch current feature values
      const response = await fetch('/api/features');
      if (!response.ok) {
        throw new Error('Failed to fetch features');
      }
      
      const data = await response.json();
      if (data.success) {
        setFeatures(data.features);
        setIsSidebarEnabled(data.isSidebarEnabled);
      } else {
        throw new Error(data.error || 'Failed to fetch features');
      }
      
      // Fetch feature configuration
      const configResponse = await fetch('/api/features/config');
      if (configResponse.ok) {
        const configData = await configResponse.json();
        if (configData.success) {
          setFeatureConfig(configData.config);
        }
      }
    } catch (err) {
      console.error('Error fetching features:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch features');
      
      // Fall back to local defaults if backend is unavailable
      setFeatures({
        SHOW_RELATED_DOCUMENTS: false,
        SHOW_PERSONALIZED_QUESTIONS: false,
        SHOW_GENERAL_TOPICS: false,
        SHOW_SESSION_WINDOW: true,
        SHOW_LANGUAGE_SELECTOR: true,
        SHOW_FEATURE_TOGGLE_PANEL: true,
      });
    } finally {
      setLoading(false);
    }
  };

  // Update a single feature
  const updateFeature = async (flagName: string, value: boolean) => {
    try {
      const response = await fetch(`/api/features/${flagName}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ value }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update feature');
      }
      
      const data = await response.json();
      if (data.success) {
        setFeatures(prev => ({ ...prev, [flagName]: value }));
        setIsSidebarEnabled(data.isSidebarEnabled);
      } else {
        throw new Error(data.error || 'Failed to update feature');
      }
    } catch (err) {
      console.error('Error updating feature:', err);
      throw err;
    }
  };

  // Update multiple features
  const updateMultipleFeatures = async (updates: Record<string, boolean>) => {
    try {
      const response = await fetch('/api/features', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ features: updates }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update features');
      }
      
      const data = await response.json();
      if (data.success) {
        setFeatures(data.features);
        setIsSidebarEnabled(data.isSidebarEnabled);
      } else {
        throw new Error(data.error || 'Failed to update features');
      }
    } catch (err) {
      console.error('Error updating features:', err);
      throw err;
    }
  };

  // Reset to defaults
  const resetToDefaults = async () => {
    try {
      const response = await fetch('/api/features/reset', {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to reset features');
      }
      
      const data = await response.json();
      if (data.success) {
        setFeatures(data.features);
        await fetchFeatures(); // Refresh config too
      } else {
        throw new Error(data.error || 'Failed to reset features');
      }
    } catch (err) {
      console.error('Error resetting features:', err);
      throw err;
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchFeatures();
  }, []);

  return (
    <FeatureContext.Provider
      value={{
        features,
        featureConfig,
        loading,
        error,
        updateFeature,
        updateMultipleFeatures,
        resetToDefaults,
        refreshFeatures: fetchFeatures,
        isSidebarEnabled,
      }}
    >
      {children}
    </FeatureContext.Provider>
  );
};