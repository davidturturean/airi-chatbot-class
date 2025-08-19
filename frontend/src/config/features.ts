/**
 * Feature flags for controlling UI components visibility
 * These flags allow us to toggle features on/off without removing code
 * For MVP, non-essential sidebar features are disabled by default
 */

export const FEATURE_FLAGS = {
  // Sidebar Features - disabled for MVP
  SHOW_RELATED_DOCUMENTS: false,       // Shows related documents from search results
  SHOW_PERSONALIZED_QUESTIONS: false,  // Shows personalized question generator
  SHOW_GENERAL_TOPICS: false,          // Shows general topic exploration buttons
  
  // Core Features - always enabled
  SHOW_SESSION_WINDOW: true,           // Shows session ID and clear button
  
  // Future feature flags can be added here
  // SHOW_ADVANCED_SETTINGS: false,
  // SHOW_ANALYTICS: false,
  // etc.
} as const;

// Helper function to check if any sidebar feature is enabled
export const isSidebarEnabled = (): boolean => {
  return (
    FEATURE_FLAGS.SHOW_RELATED_DOCUMENTS ||
    FEATURE_FLAGS.SHOW_PERSONALIZED_QUESTIONS ||
    FEATURE_FLAGS.SHOW_GENERAL_TOPICS
  );
};

// Type-safe feature flag keys
export type FeatureFlagKey = keyof typeof FEATURE_FLAGS;