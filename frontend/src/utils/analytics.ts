/**
 * Analytics integration for PostHog and metrics tracking
 */
import posthog from 'posthog-js';

class AnalyticsService {
  private sessionId: string;
  private queryCount: number = 0;
  private sessionStartTime: number;
  
  constructor() {
    this.sessionId = this.getOrCreateSessionId();
    this.sessionStartTime = Date.now();
    this.initializePostMessage();
  }
  
  private getOrCreateSessionId(): string {
    let sessionId = sessionStorage.getItem('chatbot_session_id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('chatbot_session_id', sessionId);
    }
    return sessionId;
  }
  
  private initializePostMessage() {
    // Send initial opened event via PostHog and parent window
    const openData = {
      session_id: this.sessionId,
      timestamp: new Date().toISOString()
    };
    
    // Track in PostHog
    posthog.capture('chatbot_opened', openData);
    
    // Also send to parent for iframe integration
    this.sendToParent('chatbot_opened', openData);
    
    // Listen for parent requests
    window.addEventListener('message', (event) => {
      if (event.data?.type === 'request_final_metrics') {
        this.sendSessionSummary();
      }
    });
    
    // Send summary on unload
    window.addEventListener('beforeunload', () => {
      this.sendSessionSummary();
    });
  }
  
  private sendToParent(eventType: string, data: any) {
    // Check if we're in an iframe
    if (window.parent !== window) {
      window.parent.postMessage({
        type: eventType,
        data: {
          ...data,
          timestamp: new Date().toISOString()
        }
      }, '*'); // In production, replace '*' with your Webflow domain
    }
    
    // Also log to console for debugging
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Analytics] ${eventType}`, data);
    }
  }
  
  public trackQuerySubmitted(query: string, language?: string) {
    this.queryCount++;
    const eventData = {
      session_id: this.sessionId,
      query_number: this.queryCount,
      query_length: query.length,
      language: language || 'en'
    };
    
    // Track in PostHog
    posthog.capture('query_submitted', eventData);
    
    // Also send to parent for iframe integration
    this.sendToParent('query_submitted', eventData);
  }
  
  public trackResponseReceived(metrics: {
    latency_ms: number;
    citations_count: number;
    response_length: number;
  }) {
    const eventData = {
      session_id: this.sessionId,
      query_number: this.queryCount,
      ...metrics
    };
    
    // Track in PostHog
    posthog.capture('response_received', eventData);
    
    // Also send to parent for iframe integration
    this.sendToParent('response_received', eventData);
  }
  
  public trackFeedback(
    feedbackType: 'thumbs_up' | 'thumbs_down',
    queryNumber?: number,
    additionalData?: {
      found_answer?: 'yes' | 'partial' | 'no';
      would_recommend?: number;
    }
  ) {
    const eventData = {
      session_id: this.sessionId,
      feedback_type: feedbackType,
      query_number: queryNumber || this.queryCount,
      ...additionalData
    };
    
    // Track in PostHog
    posthog.capture('feedback_given', eventData);
    
    // Also send to parent for iframe integration
    this.sendToParent('feedback_given', eventData);
  }
  
  public trackCitationClicked(citationId: string, citationType: string) {
    const eventData = {
      session_id: this.sessionId,
      citation_id: citationId,
      citation_type: citationType,
      query_number: this.queryCount
    };
    
    // Track in PostHog
    posthog.capture('citation_clicked', eventData);
    
    // Also send to parent for iframe integration
    this.sendToParent('citation_clicked', eventData);
  }
  
  public trackError(errorType: string, errorMessage: string) {
    const eventData = {
      session_id: this.sessionId,
      error_type: errorType,
      error_message: errorMessage,
      query_number: this.queryCount
    };
    
    // Track in PostHog
    posthog.capture('error_occurred', eventData);
    
    // Also send to parent for iframe integration
    this.sendToParent('error_occurred', eventData);
  }
  
  private sendSessionSummary() {
    const sessionDuration = Date.now() - this.sessionStartTime;
    const eventData = {
      session_id: this.sessionId,
      total_queries: this.queryCount,
      session_duration_ms: sessionDuration,
      total_cost: 0 // This would come from backend metrics
    };
    
    // Track in PostHog
    posthog.capture('session_ended', eventData);
    
    // Also send to parent for iframe integration
    this.sendToParent('session_ended', eventData);
  }
  
  public getSessionId(): string {
    return this.sessionId;
  }
  
  public getQueryCount(): number {
    return this.queryCount;
  }
}

// Create singleton instance
export const analytics = new AnalyticsService();

// Export helper functions for easy use
export const trackQuery = (query: string, language?: string) => 
  analytics.trackQuerySubmitted(query, language);

export const trackResponse = (metrics: {
  latency_ms: number;
  citations_count: number;
  response_length: number;
}) => analytics.trackResponseReceived(metrics);

export const trackFeedback = (
  type: 'thumbs_up' | 'thumbs_down',
  queryNumber?: number,
  additionalData?: any
) => analytics.trackFeedback(type, queryNumber, additionalData);

export const trackCitation = (id: string, type: string = 'RID') => 
  analytics.trackCitationClicked(id, type);

export const trackError = (type: string, message: string) => 
  analytics.trackError(type, message);

export const getSessionId = () => analytics.getSessionId();
export const getQueryCount = () => analytics.getQueryCount();