# Webflow PostHog Setup Instructions

## What is PostHog?
PostHog is a product analytics platform that tracks user interactions with your chatbot. It's like Google Analytics but specifically designed for understanding product usage and user behavior.

## Why Add PostHog Tracking?
- **Automatic Metrics**: Track every query, response time, and user action
- **Real Data**: See what users actually do, not just what they say
- **Performance Monitoring**: Identify slow queries and errors
- **Deployment Decisions**: Get data to support go/no-go decisions
- **User Journey**: Understand how people use the chatbot

## Step-by-Step Installation

### Step 1: Access Webflow Site Settings
1. Log into your Webflow account
2. Select your AI Risk Repository site
3. Click the gear icon (⚙️) for **Site Settings**

### Step 2: Navigate to Custom Code
1. In the left sidebar, find **Custom Code**
2. You'll see two text areas:
   - **Head Code** (this is where we'll add PostHog)
   - **Footer Code** (already has the widget)

### Step 3: Add PostHog Tracking Script
1. Copy ALL the code from `webflow_posthog_integration.html`
2. Paste it into the **Head Code** section
3. The code should start with `<!-- PostHog Integration for Webflow -->`

### Step 4: Verify Configuration
Check that these values are correct in the pasted code:
```javascript
const RAILWAY_URL = 'https://airi-chatbot-class-production.up.railway.app';
const ENABLE_DEBUG = true; // Keep true during testing
posthog.init('phx_pa5zpKS0q1DTprlpwAaInqlYFIqY2u8iWCKL2C4m2FF5S7M', ...
```

### Step 5: Update Iframe ID (if needed)
If your chatbot iframe has a different ID than `chatbot-iframe`:
1. Find this line in the code: `const CHATBOT_IFRAME_ID = 'chatbot-iframe';`
2. Replace `'chatbot-iframe'` with your actual iframe ID
3. Check the widget code in Footer Code to find the correct ID

### Step 6: Publish Changes
1. Click **Save Changes** at the bottom
2. Click **Publish** (top right)
3. Select your domain
4. Click **Publish to Selected Domains**

## Testing the Integration

### Step 1: Open Browser Console
1. Visit your published Webflow site
2. Open Developer Tools (F12 or right-click → Inspect)
3. Go to the **Console** tab

### Step 2: Check for PostHog Messages
You should see messages like:
```
[Chatbot Analytics] PostHog loaded successfully
[Chatbot Analytics] Chatbot opened
[Chatbot Analytics] Query submitted {session_id: "...", ...}
```

### Step 3: Test Events
1. Open the chatbot
2. Type a test query
3. Click a citation
4. Watch the console for tracking messages

### Step 4: Verify in PostHog Dashboard
1. Go to [https://us.posthog.com](https://us.posthog.com)
2. Log in with your PostHog account
3. Navigate to **Events** tab
4. You should see events appearing in real-time:
   - `chatbot_page_viewed`
   - `chatbot_opened`
   - `query_submitted`
   - `response_received`
   - etc.

## Events Being Tracked

### Page Events
- `chatbot_page_viewed` - When someone visits the page with chatbot

### User Actions
- `chatbot_opened` - Widget or page opened
- `query_submitted` - User sends a question
- `response_received` - Chatbot responds
- `citation_clicked` - User clicks on a source
- `feedback_given` - Thumbs up/down
- `session_ended` - User leaves or closes

### Error Events
- `error_occurred` - Any error happens
- `query_timeout` - Response takes too long

## Troubleshooting

### PostHog Not Loading
**Problem**: No PostHog messages in console
**Solution**: 
1. Check that code is in Head Code section
2. Verify you published the site
3. Clear browser cache and reload

### Events Not Appearing
**Problem**: Console shows events but PostHog dashboard is empty
**Solution**:
1. Check API key is correct: `phx_pa5zpKS0q1DTprlpwAaInqlYFIqY2u8iWCKL2C4m2FF5S7M`
2. Make sure you're looking at the right project in PostHog
3. Check date range in PostHog dashboard

### Cross-Origin Errors
**Problem**: Console shows "Blocked a frame with origin..."
**Solution**:
1. This is expected for iframe security
2. Events will still track correctly
3. Can be ignored during testing

### No Debug Messages
**Problem**: No `[Chatbot Analytics]` messages
**Solution**:
1. Check `ENABLE_DEBUG = true` in the code
2. Make sure console logging isn't filtered
3. Try incognito/private browsing mode

## Debugging Mode

To see detailed tracking information:
1. Keep `ENABLE_DEBUG = true` during testing
2. Open browser console before using chatbot
3. All events will log to console
4. Set to `false` for production

## Security Notes

During testing, the origin check is commented out:
```javascript
// if (!ALLOWED_ORIGINS.includes(event.origin)) {
```

For production, uncomment these lines for security.

## Data You'll Collect

### User Behavior
- How many queries per session
- Time between queries
- Most common query types
- Citation engagement rate

### Performance
- Response times (latency)
- Error rates
- Timeout frequency
- Success rates by query type

### Engagement
- Session duration
- Return user rate
- Feedback scores
- Task completion rates

## Next Steps After Installation

1. **Test with Team**: Have 2-3 team members test
2. **Check Data Quality**: Verify events in PostHog
3. **Create Dashboard**: Set up PostHog dashboard for testing
4. **Monitor During Testing**: Watch real-time during user tests
5. **Export Data**: After testing, export for analysis

## PostHog Dashboard Access

**URL**: [https://us.posthog.com](https://us.posthog.com)
**Project**: AI Risk Repository Chatbot
**API Key**: `phx_pa5zpKS0q1DTprlpwAaInqlYFIqY2u8iWCKL2C4m2FF5S7M`

Need dashboard access? Contact davidct@mit.edu

## Quick Checklist

- [ ] Code added to Webflow Head Code
- [ ] Site published
- [ ] Console shows PostHog loaded
- [ ] Test query tracked
- [ ] Events appear in PostHog dashboard
- [ ] Debug mode enabled for testing
- [ ] Team notified of tracking

## Support

**Technical Issues**: davidct@mit.edu
**PostHog Documentation**: [https://posthog.com/docs](https://posthog.com/docs)
**Integration Code**: See `webflow_posthog_integration.html`

---

*Remember: PostHog tracking helps us understand how people actually use the chatbot, which is essential for making it better!*