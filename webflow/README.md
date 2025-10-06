# Webflow Integration

This directory contains all code and resources for integrating the AIRI Chatbot with Webflow.

## Directory Structure

```
webflow/
├── widget/                          # Chatbot widget implementations
│   ├── widget.html                 # Current production widget
│   └── versions/                   # Historical widget versions
├── analytics/                       # Analytics integration code
│   └── posthog_integration.html   # PostHog analytics setup
└── conversation_transfer_receiver.js  # Session transfer handler
```

## Components

### Widget (widget/)
The chatbot widget that embeds in Webflow pages.

**Current Version:** `widget.html`
- Full-featured chatbot widget
- Session management
- Responsive design
- PostHog analytics integration

**Version History:** (in `versions/`)
- `v0_implementation.html` - Initial implementation
- `v1_ready.html` - Ready for deployment
- `v2_branded.html` - Branded version
- `v3_resizable.html` - Added resizable functionality
- `v4_final.html` - Final pre-session version
- `v5_session.html` - Session management added

### Analytics (analytics/)
PostHog analytics integration for tracking user interactions.

- `posthog_integration.html` - PostHog setup code for Webflow

### Session Transfer
- `conversation_transfer_receiver.js` - Handles session transfer between widget and full chatbot page

## Documentation

See `docs/webflow/` for comprehensive integration guides:
- [Widget Integration Guide](../docs/webflow/widget_integration.md)
- [Session Integration](../docs/webflow/session_integration.md)
- [Analytics Setup](../docs/webflow/analytics_setup.md)
- [Chatbot Page Files](../docs/webflow/chatbot_page/)

## Integration Steps

1. **Widget Integration:**
   - Copy contents of `widget/widget.html`
   - Add to Webflow page custom code (before </body>)
   - Configure API endpoint URL

2. **Analytics Setup:**
   - Copy contents of `analytics/posthog_integration.html`
   - Add to Webflow site-wide footer code
   - Set PostHog project token

3. **Session Transfer:**
   - Include `conversation_transfer_receiver.js` on chatbot page
   - Ensure proper API endpoint configuration

## Configuration

Update these values in the widget code:
```javascript
const API_BASE_URL = 'https://your-api-endpoint.com';
const POSTHOG_TOKEN = 'your-posthog-token';
```

## Testing

Test the integration:
1. Widget appears and opens correctly
2. Messages send and receive responses
3. Session persists across page navigation
4. Analytics events fire correctly

## Support

For integration issues, see:
- [Webflow Integration Guide](../docs/webflow/widget_integration.md)
- [Troubleshooting Guide](../docs/webflow/widget_integration.md#troubleshooting)
