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
