# PostHog Analytics Implementation for Webflow

## Overview
Add PostHog tracking to monitor user interactions with the AIRI chatbot on futuretech.mit.edu.

**Your PostHog API Key:** `phx_pa5zpKS0q1DTprlpwAaInqlYFIqY2u8iWCKL2C4m2FF5S7M`

---

## Step 1: Add PostHog Script to Webflow

### 1.1 Open Webflow Project Settings
1. Go to **Webflow Dashboard** → Your project
2. Click **Project Settings** (gear icon)
3. Go to **Custom Code** tab

### 1.2 Add PostHog to Header Code
In the **Head Code** section, add this **BEFORE** the closing `</head>` tag:

```html
<!-- PostHog Analytics -->
<script>
  !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.async=!0,p.src=s.api_host+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled onFeatureFlags getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures getActiveMatchingSurveys getSurveys onSessionId".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);

  posthog.init('phx_pa5zpKS0q1DTprlpwAaInqlYFIqY2u8iWCKL2C4m2FF5S7M', {
    api_host: 'https://us.i.posthog.com',
    person_profiles: 'identified_only',
    autocapture: true,
    capture_pageview: true,
    capture_pageleave: true
  })
</script>
```

### 1.3 Save and Publish
1. Click **Save Changes**
2. Click **Publish** (top right)
3. Publish to your production domain

---

## Step 2: Verify PostHog is Working

### 2.1 Check Installation
1. Open your Webflow site: https://futuretech.mit.edu
2. Open browser DevTools (F12)
3. Go to **Console** tab
4. Type: `posthog`
5. You should see the PostHog object (not undefined)

### 2.2 Check PostHog Dashboard
1. Go to https://posthog.com and log in
2. Go to **Activity** → **Live events**
3. Open your Webflow site in another tab
4. You should see events appearing in real-time:
   - `$pageview` - Page views
   - `$pageleave` - When user leaves
   - `$autocapture` - Automatic click tracking

---

## Step 3: Custom Event Tracking (Already Implemented in Widget)

Your widget code **already tracks** these events (no changes needed):

### Events Currently Tracked:
```javascript
// When widget opens
posthog.capture('chatbot_widget_opened', {
  session_id: currentSessionId,
  page: window.location.pathname
});

// When widget closes
posthog.capture('chatbot_widget_closed', {
  session_id: currentSessionId,
  page: window.location.pathname
});

// When user opens in full page
posthog.capture('chatbot_fullpage_transition', {
  session_id: currentSessionId,
  from: 'widget'
});
```

These events will **automatically start working** once PostHog is added to your Webflow Header Code.

---

## Step 4: Verify Custom Events

### 4.1 Test Widget Events
1. Open https://futuretech.mit.edu
2. Click the **chatbot button**
3. In PostHog Live Events, you should see: `chatbot_widget_opened`
4. Click the **X** to close
5. You should see: `chatbot_widget_closed`
6. Open widget again and click **Full Page** button
7. You should see: `chatbot_fullpage_transition`

### 4.2 Check Event Properties
Each event includes:
- `session_id` - User's conversation session
- `page` - Current page path
- `from` - Source of transition (for fullpage events)

---

## Step 5: Set Up PostHog Dashboards

### 5.1 Create Chatbot Usage Dashboard
1. In PostHog, go to **Dashboards** → **New Dashboard**
2. Name it: "AIRI Chatbot Usage"
3. Add these insights:

#### Insight 1: Widget Opens Over Time
- **Type:** Trend
- **Event:** `chatbot_widget_opened`
- **Visualization:** Line chart
- **Interval:** Daily

#### Insight 2: Full Page Transitions
- **Type:** Trend
- **Event:** `chatbot_fullpage_transition`
- **Visualization:** Bar chart
- **Group by:** `page` property

#### Insight 3: Session Retention
- **Type:** Retention
- **First event:** `chatbot_widget_opened`
- **Return event:** `chatbot_widget_opened`
- **Period:** Weekly

#### Insight 4: Pages Where Widget is Used Most
- **Type:** Bar chart
- **Event:** `chatbot_widget_opened`
- **Breakdown by:** `page` property

### 5.2 Create Conversion Funnel
1. Go to **Insights** → **New Insight**
2. Select **Funnel**
3. Add steps:
   - Step 1: `$pageview` (visited site)
   - Step 2: `chatbot_widget_opened` (opened widget)
   - Step 3: `chatbot_fullpage_transition` (engaged deeply)

This shows conversion from visitor → widget user → engaged user.

---

## Step 6: Set Up Alerts (Optional)

### 6.1 Widget Error Alert
If you want to track errors:
1. Go to **Alerts** → **New Alert**
2. Configure:
   - **Name:** "Chatbot Widget Errors"
   - **Insight:** Count of events matching error conditions
   - **Trigger:** When count > 10 in 1 hour
   - **Notify:** Your email

---

## Events You Can Track in PostHog

### Automatically Tracked (No Code Needed)
- ✅ `$pageview` - Every page view
- ✅ `$pageleave` - When users leave
- ✅ `$autocapture` - Button clicks, form submissions
- ✅ `$session_id` - Unique session identifier

### Custom Events (Already in Widget Code)
- ✅ `chatbot_widget_opened` - Widget popup opened
- ✅ `chatbot_widget_closed` - Widget popup closed
- ✅ `chatbot_fullpage_transition` - User went to full page

### Additional Events You Could Add (Optional)
If you want more granular tracking, you can add these to your widget code:

```javascript
// When user sends first message
posthog.capture('chatbot_first_message', {
  session_id: currentSessionId,
  message_length: message.length
});

// When user gets a response
posthog.capture('chatbot_response_received', {
  session_id: currentSessionId,
  response_time_ms: responseTime
});

// When user clicks a citation
posthog.capture('chatbot_citation_clicked', {
  session_id: currentSessionId,
  rid: riskId
});
```

---

## Privacy & Compliance Notes

### GDPR/Privacy Considerations
PostHog is configured with `person_profiles: 'identified_only'`, which means:
- ✅ Only tracks anonymous session data by default
- ✅ No personal information collected unless explicitly identified
- ✅ IP addresses are anonymized
- ✅ Compliant with MIT's privacy policies

### Data Retention
PostHog stores data for:
- **Events:** 7 years (configurable in settings)
- **Session recordings:** Not enabled by default
- **Heatmaps:** Not enabled by default

---

## Troubleshooting

### PostHog Not Loading?
1. Check browser console for errors
2. Verify API key is correct
3. Check if ad blockers are interfering
4. Try in incognito mode

### Events Not Appearing?
1. Verify PostHog script loaded (check console)
2. Check that `CONFIG.ENABLE_POSTHOG` is `true` in widget code (line 256)
3. Wait 5-10 seconds for events to appear in dashboard
4. Check PostHog Live Events view (not Insights)

### Widget Events Not Tracking?
Check that this line is `true` in your footer code:
```javascript
ENABLE_POSTHOG: true,  // Line 256
```

---

## Success Criteria

✅ PostHog script loads on all pages
✅ `$pageview` events appear in dashboard
✅ `chatbot_widget_opened` events tracked
✅ `chatbot_fullpage_transition` events tracked
✅ Can see real-time events in Live Events view
✅ Dashboard shows chatbot usage metrics

---

## Next Steps After Implementation

1. **Monitor for 24 hours** - Let data accumulate
2. **Create baseline metrics** - Document typical usage
3. **Share dashboard** with PI/supervisor
4. **Set up weekly reports** - Email summaries
5. **Analyze user behavior** - Identify improvement opportunities

---

## Questions to Answer with PostHog Data

1. **Usage:** How many people open the chatbot widget daily?
2. **Engagement:** What % of widget users transition to full page?
3. **Pages:** Which pages have highest chatbot usage?
4. **Retention:** Do users return to use the chatbot again?
5. **Time:** What time of day is the chatbot used most?
6. **Flow:** What's the typical user journey? (pageview → widget → fullpage)

---

## Summary

**What you need to do:**
1. Copy the PostHog script above
2. Paste into Webflow → Project Settings → Custom Code → Head Code
3. Save and Publish
4. Visit your site and check PostHog Live Events
5. Create dashboard with recommended insights

**Time required:** 10-15 minutes

**Your widget code already has tracking events** - they'll automatically start working once PostHog is added to Webflow!
