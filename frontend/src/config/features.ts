/**
 * Feature flags for controlling UI components visibility
 * These are now synchronized with backend feature flags
 * This file provides a compatibility layer for existing code
 */

// Default feature flags (used as fallback when backend is unavailable)
export const DEFAULT_FEATURE_FLAGS = {
  // Sidebar Features
  SHOW_RELATED_DOCUMENTS: false,       // Shows related documents from search results
  SHOW_PERSONALIZED_QUESTIONS: false,  // Shows personalized question generator
  SHOW_GENERAL_TOPICS: false,          // Shows general topic exploration buttons
  
  // Core Features
  SHOW_SESSION_WINDOW: true,           // Shows session ID and clear button
  SHOW_LANGUAGE_SELECTOR: true,        // Shows language dropdown
  SHOW_FEATURE_TOGGLE_PANEL: true,     // Shows feature toggle panel
  
  // Language Features
  ENABLE_LANGUAGE_DETECTION: true,     // Auto-detect query language
  ENABLE_MULTILINGUAL_RESPONSES: true, // Respond in detected language
  
  // Advanced Features
  ENABLE_WEB_SEARCH: false,           // Enable web search capabilities
  ENABLE_ADVANCED_ANALYTICS: false,    // Enable usage analytics
  
  // Debug Features
  SHOW_DEBUG_INFO: false,              // Show debug information in UI
  ENABLE_VERBOSE_LOGGING: false,       // Enable verbose API logging
} as const;

// This will be populated from backend
export let FEATURE_FLAGS = { ...DEFAULT_FEATURE_FLAGS };

// Function to update feature flags from backend
export const updateFeatureFlags = (flags: Record<string, boolean>) => {
  FEATURE_FLAGS = { ...DEFAULT_FEATURE_FLAGS, ...flags };
};

// Helper function to check if any sidebar feature is enabled
export const isSidebarEnabled = (): boolean => {
  return (
    FEATURE_FLAGS.SHOW_RELATED_DOCUMENTS ||
    FEATURE_FLAGS.SHOW_PERSONALIZED_QUESTIONS ||
    FEATURE_FLAGS.SHOW_GENERAL_TOPICS
  );
};

// Type-safe feature flag keys
export type FeatureFlagKey = keyof typeof DEFAULT_FEATURE_FLAGS;