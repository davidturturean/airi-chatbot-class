# Chatbot Session Integration Guide

## Overview
This guide explains how to integrate session-based conversation persistence into your chatbot, enabling seamless transitions between widget and full-page views.

## Backend Changes Needed

### 1. Update Chat Service to Use Sessions

In `src/core/services/chat_service.py`, add session support:

```python
async def process_query_with_session(self, query: str, session_id: str = None) -> Dict[str, Any]:
    """Process query with session tracking."""
    
    # Get session history if exists
    if session_id:
        history = await self.get_session_history(session_id)
    else:
        history = []
    
    # Process query with context
    response = await self.process_query(query, context=history)
    
    # Save to session
    if session_id:
        await self.save_to_session(session_id, query, response)
    
    return response
```

### 2. Update Chat Route to Handle Sessions

In `src/api/routes/chat.py`, read session from URL:

```python
@chat_bp.route('/api/chat', methods=['POST'])
async def chat():
    data = request.json
    query = data.get('query')
    session_id = data.get('session_id') or request.args.get('session')
    
    # If session_id provided, use session-aware processing
    if session_id:
        # Save query to session
        requests.post(f"{API_BASE}/api/session/{session_id}/messages", json={
            "message": query,
            "role": "user"
        })
        
        response = await chat_service.process_query(query)
        
        # Save response to session
        requests.post(f"{API_BASE}/api/session/{session_id}/messages", json={
            "message": response['answer'],
            "role": "assistant",
            "metadata": {"citations": response.get('citations', [])}
        })
    else:
        response = await chat_service.process_query(query)
    
    return jsonify(response)
```

### 3. Frontend Changes for Full Page

In your chatbot frontend (the page at `/chat`), add:

```javascript
// On page load, check for session parameter
window.addEventListener('DOMContentLoaded', async function() {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session');
    
    if (sessionId) {
        // Load previous conversation
        try {
            const response = await fetch(`/api/session/${sessionId}/messages`);
            const data = await response.json();
            
            if (data.success && data.messages) {
                // Display previous messages
                data.messages.forEach(msg => {
                    displayMessage(msg.content, msg.role);
                });
                
                // Store session ID for future messages
                window.currentSessionId = sessionId;
                
                // Show notification
                showNotification('Conversation continued from widget');
            }
        } catch (error) {
            console.error('Failed to load session:', error);
        }
    }
});

// When sending messages, include session ID
async function sendMessage(query) {
    const payload = {
        query: query,
        session_id: window.currentSessionId
    };
    
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    
    // ... handle response
}
```

## Testing the Integration

### 1. Test Session Creation
```bash
curl -X POST https://your-app.railway.app/api/session/create
```

### 2. Test Message Storage
```bash
curl -X POST https://your-app.railway.app/api/session/session_123/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "What is AI risk?", "role": "user"}'
```

### 3. Test Message Retrieval
```bash
curl https://your-app.railway.app/api/session/session_123/messages
```

## Widget Installation

1. **Replace widget code** in Webflow with `webflow_widget_session.html`
2. **Update URLs** in the CONFIG section:
   ```javascript
   CHATBOT_BASE_URL: 'https://your-app.railway.app',
   API_BASE_URL: 'https://your-app.railway.app',
   ```

## Full Page Setup

On your `/chatbot` page, add this script:

```html
<script>
// Session continuation script
(function() {
  const urlParams = new URLSearchParams(window.location.search);
  const sessionId = urlParams.get('session');
  
  if (sessionId) {
    // Add session to all API calls
    window.CHATBOT_SESSION_ID = sessionId;
    
    // Load conversation on iframe load
    const chatFrame = document.querySelector('iframe');
    if (chatFrame) {
      chatFrame.addEventListener('load', function() {
        chatFrame.contentWindow.postMessage({
          type: 'load_session',
          session_id: sessionId
        }, '*');
      });
    }
  }
})();
</script>
```

## Benefits of This Approach

1. **No Cross-Domain Issues**: Session ID in URL bypasses iframe restrictions
2. **Persistent History**: Conversations survive page refreshes
3. **Multi-Device**: Access same conversation from different devices
4. **Analytics Ready**: Full conversation tracking in backend
5. **Scalable**: Can add Redis/database for production

## Production Considerations

### 1. Use Redis for Session Storage
Replace in-memory storage with Redis:

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def save_to_session(session_id, message):
    key = f"session:{session_id}"
    messages = json.loads(redis_client.get(key) or "[]")
    messages.append(message)
    redis_client.setex(key, 86400, json.dumps(messages))  # 24hr expiry
```

### 2. Add Authentication
Protect sessions with user authentication:

```python
@session_bp.route('/api/session/<session_id>/messages')
@require_auth  # Add authentication decorator
def get_session_messages(session_id):
    # Verify user owns this session
    # ... rest of code
```

### 3. Rate Limiting
Add rate limiting to prevent abuse:

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: session_id)

@limiter.limit("100 per hour")
@session_bp.route('/api/session/<session_id>/messages', methods=['POST'])
```

## Troubleshooting

### Session Not Loading
1. Check browser console for errors
2. Verify session ID in URL
3. Check backend logs for API calls
4. Ensure CORS allows your domain

### Messages Not Saving
1. Verify API endpoint is accessible
2. Check request payload format
3. Monitor backend session storage
4. Check for rate limiting

### Widget Not Creating Session
1. Check browser localStorage
2. Verify API endpoint URL
3. Check CORS configuration
4. Monitor network requests

## Summary

This session-based approach provides seamless conversation continuity without the complexity of cross-domain iframe communication. The backend maintains the source of truth for all conversations, making it reliable and scalable.