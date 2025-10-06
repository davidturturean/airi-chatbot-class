# PostHog Analytics Integration Plan

## API Key
```
phx_pa5zpKS0q1DTprlpwAaInqlYFIqY2u8iWCKL2C4m2FF5S7M
```

## Integration Overview

PostHog provides product analytics specifically designed for understanding user behavior. This complements our metrics dashboard by tracking user interactions, conversion funnels, and feature usage patterns.

## Implementation Status

### Already Configured
✅ PostHog API key integrated in codebase
✅ Basic event tracking structure in place
✅ User session tracking enabled
✅ Ready to deploy to production

### Pending Activation
- Enable on Webflow embedded page
- Set up custom events for testing phase
- Configure dashboards and reports
- Create team access

## Events to Track During Testing Phase

### Core User Events

```javascript
// Page Load
posthog.capture('chatbot_loaded', {
    stage: 'internal_testing',
    password_protected: true,
    user_type: 'tester',
    load_time_ms: loadTime
});

// Query Submitted
posthog.capture('query_submitted', {
    query_length: query.length,
    query_type: classifyQuery(query),
    session_query_count: queryCount,
    time_to_first_query: timeToFirst
});

// Response Received
posthog.capture('response_received', {
    latency_ms: responseTime,
    response_length: response.length,
    citation_count: citationCount,
    error: false
});

// Citation Clicked
posthog.capture('citation_clicked', {
    citation_position: position,
    citation_rid: rid,
    time_since_response: timeSince
});

// Feedback Provided
posthog.capture('feedback_submitted', {
    feedback_type: 'thumbs', // or 'detailed'
    feedback_value: value,
    query_index: index
});

// Session End
posthog.capture('session_ended', {
    total_queries: totalQueries,
    session_duration_ms: duration,
    citations_clicked: citationsClicked,
    feedback_provided: feedbackCount
});
```

### Error Events

```javascript
// Timeout
posthog.capture('query_timeout', {
    timeout_after_ms: timeoutDuration,
    query_type: queryType
});

// Error
posthog.capture('query_error', {
    error_type: errorType,
    error_message: message,
    recovery_action: action
});

// Fallback
posthog.capture('fallback_triggered', {
    fallback_reason: reason,
    original_intent: intent
});
```

## User Journey Mapping

### Testing Phase Journey

```
1. Password Entry → 2. First Impression → 3. First Query → 4. Response Review → 5. Citation Check → 6. Additional Queries → 7. Feedback → 8. Exit
```

### Key Metrics to Track

| Metric | PostHog Event | Why It Matters |
|--------|--------------|----------------|
| **Time to First Query** | Time between load and first query | Indicates interface clarity |
| **Query Refinement Rate** | Sequential similar queries | Shows if first answers satisfy |
| **Citation Click Rate** | Clicks / Citations shown | Validates citation value |
| **Feedback Rate** | Feedback / Total queries | Engagement indicator |
| **Drop-off Points** | Last event before exit | Identifies friction |
| **Session Duration** | End time - Start time | Overall engagement |

## Conversion Funnels

### Primary Testing Funnel
```
Step 1: Page Load (100%)
  ↓
Step 2: First Query (Target: >90%)
  ↓
Step 3: Second Query (Target: >70%)
  ↓
Step 4: Citation Click (Target: >50%)
  ↓
Step 5: Feedback Provided (Target: >30%)
```

### Quality Funnel
```
Query Submitted (100%)
  ↓
Response Received (Target: >95%)
  ↓
Response Satisfactory (Target: >70%)
  ↓
No Follow-up Needed (Target: >60%)
```

## Dashboard Setup in PostHog

### 1. Testing Overview Dashboard

**Widgets to Create:**
- Total unique testers
- Total queries submitted
- Average queries per session
- Citation click rate
- Feedback submission rate
- Error rate

### 2. User Behavior Dashboard

**Widgets to Create:**
- User paths visualization
- Drop-off analysis
- Query type distribution
- Time to first query histogram
- Session duration distribution

### 3. Performance Dashboard

**Widgets to Create:**
- Response time trends
- Error rate over time
- Timeout frequency
- API cost per session

## A/B Testing Capabilities

### Potential Tests During Canary Phase

**Test 1: Interface Variations**
- A: Current full-page embed
- B: Floating widget option
- Metric: Engagement rate

**Test 2: Onboarding**
- A: No examples
- B: 3 example queries shown
- Metric: Time to first query

**Test 3: Response Format**
- A: Current format
- B: Structured with sections
- Metric: Satisfaction score

## Access & Permissions

### Team Access Setup

| Role | PostHog Access | Features |
|------|---------------|----------|
| **Admin** (David) | Full access | All features, billing |
| **Project Lead** (Peter) | Editor | View all, create dashboards |
| **UX Lead** (Sasha) | Viewer | View dashboards, reports |
| **Testers** | No direct access | Data collected automatically |

### How to Access PostHog

1. **URL:** https://app.posthog.com
2. **Login:** Via email invitation
3. **Project:** AI Risk Repository Chatbot
4. **Default View:** Testing Overview Dashboard

## Implementation Code

### Webflow Custom Code Section

Add to page header:
```html
<script>
  !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.async=!0,p.src=s.api_host+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled onFeatureFlags getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures getActiveMatchingSurveys getSurveys".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
  
  posthog.init('phx_pa5zpKS0q1DTprlpwAaInqlYFIqY2u8iWCKL2C4m2FF5S7M',{
    api_host:'https://app.posthog.com',
    capture_pageview: true,
    capture_pageleave: true,
    autocapture: true,
    session_recording: {
      enabled: false // Enable if you want session recordings
    }
  });
  
  // Identify testing phase
  posthog.capture('pageview', {
    deployment_stage: 'internal_testing',
    page_type: 'chatbot'
  });
</script>
```

### Chatbot Integration Points

```javascript
// When chatbot initializes
function initChatbot() {
    const startTime = Date.now();
    
    // Track initialization
    posthog.capture('chatbot_initialized', {
        stage: window.DEPLOYMENT_STAGE || 'testing',
        timestamp: new Date().toISOString()
    });
    
    // Track time to first interaction
    document.getElementById('queryInput').addEventListener('focus', function() {
        posthog.capture('first_interaction', {
            time_to_interact_ms: Date.now() - startTime
        });
    }, { once: true });
}

// When query submitted
function submitQuery(query) {
    posthog.capture('query_submitted', {
        query_length: query.length,
        word_count: query.split(' ').length,
        has_question_mark: query.includes('?')
    });
}

// When response received
function handleResponse(response, latency) {
    const citations = response.match(/RID-\d{5}/g) || [];
    
    posthog.capture('response_received', {
        latency_ms: latency,
        citation_count: citations.length,
        response_length: response.length,
        success: true
    });
}
```

## Reports to Generate

### Weekly Testing Report
- Total sessions
- Unique testers
- Average satisfaction
- Top failure points
- Most common queries
- Performance trends

### Go/No-Go Decision Report
- Funnel completion rates
- User satisfaction scores
- Error rates by type
- Feature usage statistics
- A/B test results (if any)

## Privacy & Compliance

### Data Collection Notice
"This chatbot uses PostHog analytics to improve user experience. We track interactions but not personal information."

### What We Track
- ✅ User interactions (clicks, queries)
- ✅ Performance metrics
- ✅ Error events
- ✅ Session flow

### What We DON'T Track
- ❌ Personal information
- ❌ Query content (only metadata)
- ❌ IP addresses (masked)
- ❌ Screen recordings (unless enabled)

## Success Metrics

### Testing Phase (Week 1)
- Setup completion: 100%
- Event capture rate: >95%
- Dashboard creation: Complete
- Team access: Configured

### Canary Phase (Weeks 2-3)
- A/B tests running: 2+
- Funnel tracking: Active
- Conversion rate: Baseline established
- User segments: Defined

### Production (Week 4+)
- Full analytics pipeline
- Automated reports
- Alert system active
- ROI tracking enabled

## Support & Documentation

**PostHog Documentation:** https://posthog.com/docs
**Support:** support@posthog.com
**Our Contact:** davidct@mit.edu

## Next Steps

1. **Today:** Add tracking code to Webflow
2. **Before Testing:** Verify events firing correctly
3. **During Testing:** Monitor dashboard daily
4. **After Testing:** Generate insights report
5. **Before Canary:** Set up A/B tests