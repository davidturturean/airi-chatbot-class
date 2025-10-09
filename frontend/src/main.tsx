/**
 * Suppress "custom element already defined" errors from external scripts
 *
 * When the chatbot is embedded in Webflow via iframe, both the parent page
 * and the iframe may load the same web components (e.g., TinyMCE's mce-autosize-textarea).
 * This causes harmless "already defined" errors in the console.
 *
 * The first registration wins, subsequent attempts fail silently.
 * This is expected behavior and does not affect functionality.
 */
const originalError = console.error;
console.error = function(...args: any[]) {
  const message = args[0]?.toString() || '';

  // Ignore custom element redefinition errors from external scripts (Webflow/TinyMCE)
  if (message.includes('custom element') && message.includes('already been defined')) {
    console.warn(
      '⚠️  Webflow Integration: External custom element already defined (expected behavior)',
      '\n   This is harmless - the chatbot iframe shares web components with the parent page.',
      '\n   The first registration wins. Functionality is not affected.',
      '\n   Details:', ...args
    );
    return;
  }

  // Ignore specific TinyMCE component redefinition (common in Webflow)
  if (message.includes('mce-autosize-textarea')) {
    console.warn(
      '⚠️  Webflow Integration: TinyMCE component already defined by external script',
      '\n   This is expected when embedded in Webflow pages.',
      '\n   Details:', ...args
    );
    return;
  }

  // Pass through all other errors unchanged
  originalError.apply(console, args);
};

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import posthog from 'posthog-js'
import './index.css'
import App from './App.tsx'

// Initialize PostHog
if (typeof window !== 'undefined') {
  posthog.init(
    import.meta.env.VITE_POSTHOG_API_KEY || 'phc_PROJECT_API_KEY',
    {
      api_host: import.meta.env.VITE_POSTHOG_HOST || 'https://us.posthog.com',
      loaded: () => {
        if (import.meta.env.MODE === 'development') {
          console.log('PostHog loaded successfully')
        }
      }
    }
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
