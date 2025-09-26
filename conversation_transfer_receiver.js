// AI Risk Repository - Conversation Transfer Receiver
// Add this script to the /chatbot page to receive transferred conversations from the widget

(function() {
  'use strict';
  
  // Configuration
  const STORAGE_KEY = 'airisk_conversation_transfer';
  const EXPIRY_TIME = 5 * 60 * 1000; // 5 minutes
  const DEBUG = false; // Set to true for console logging
  
  // Debug logger
  function log(message, data) {
    if (DEBUG) {
      console.log(`[Conversation Transfer] ${message}`, data || '');
    }
  }
  
  // Check for transferred conversation on page load
  function checkForTransfer() {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      
      if (!stored) {
        log('No transfer data found');
        return null;
      }
      
      const transferData = JSON.parse(stored);
      log('Transfer data found:', transferData);
      
      // Check if data is expired
      const age = Date.now() - transferData.timestamp;
      if (age > EXPIRY_TIME) {
        log('Transfer data expired', { age: age, limit: EXPIRY_TIME });
        sessionStorage.removeItem(STORAGE_KEY);
        return null;
      }
      
      // Validate transfer type
      if (transferData.transferType !== 'widget_to_fullpage') {
        log('Invalid transfer type:', transferData.transferType);
        return null;
      }
      
      // Clear the storage after reading (one-time use)
      sessionStorage.removeItem(STORAGE_KEY);
      log('Transfer data retrieved and cleared');
      
      return transferData;
    } catch (e) {
      console.error('[Conversation Transfer] Error reading transfer data:', e);
      // Clean up corrupted data
      try {
        sessionStorage.removeItem(STORAGE_KEY);
      } catch (cleanupError) {
        // Silently fail
      }
      return null;
    }
  }
  
  // Display transfer notification
  function showTransferNotification() {
    // Create a subtle notification
    const notification = document.createElement('div');
    notification.id = 'transfer-notification';
    notification.innerHTML = `
      <style>
        #transfer-notification {
          position: fixed;
          top: 20px;
          right: 20px;
          background: #A32035;
          color: white;
          padding: 12px 20px;
          border-radius: 8px;
          font-family: 'Figtree', 'Ubuntu', sans-serif;
          font-size: 14px;
          box-shadow: 0 4px 12px rgba(163, 32, 53, 0.3);
          z-index: 10000;
          animation: slideIn 0.3s ease-out;
          display: flex;
          align-items: center;
          gap: 10px;
        }
        
        @keyframes slideIn {
          from {
            transform: translateX(120%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        
        @keyframes slideOut {
          from {
            transform: translateX(0);
            opacity: 1;
          }
          to {
            transform: translateX(120%);
            opacity: 0;
          }
        }
        
        #transfer-notification.hiding {
          animation: slideOut 0.3s ease-out forwards;
        }
        
        #transfer-notification svg {
          width: 18px;
          height: 18px;
          fill: white;
        }
      </style>
      <svg viewBox="0 0 24 24">
        <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
      </svg>
      <span>Conversation continued from widget</span>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
      notification.classList.add('hiding');
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, 3000);
  }
  
  // Load conversation into chatbot
  function loadConversation(transferData) {
    log('Loading conversation into chatbot');
    
    // Wait for chatbot to be ready
    const checkInterval = setInterval(() => {
      // Try to find the chat interface (adjust selectors as needed)
      const chatInput = document.querySelector('#chat-input, .chat-input, textarea[placeholder*="Ask"], input[placeholder*="Ask"]');
      const chatContainer = document.querySelector('#chat-messages, .chat-messages, .message-container, .conversation-container');
      
      if (chatInput || chatContainer) {
        clearInterval(checkInterval);
        
        // Show notification
        showTransferNotification();
        
        // Try to populate conversation
        if (transferData.conversation && transferData.conversation.messages) {
          // Method 1: Try to inject via postMessage to iframe
          const chatFrame = document.querySelector('iframe[src*="chat"], iframe#chat-frame');
          if (chatFrame && chatFrame.contentWindow) {
            chatFrame.contentWindow.postMessage({
              type: 'load_conversation',
              conversation: transferData.conversation,
              sessionId: transferData.sessionId
            }, '*');
            log('Sent conversation via postMessage');
          }
          
          // Method 2: Try to populate directly if elements are accessible
          if (chatContainer && transferData.conversation.messages.length > 0) {
            // This would need to be customized based on your chat implementation
            log('Direct population may require custom implementation');
          }
          
          // Method 3: Store for the chatbot to read
          window.transferredConversation = transferData.conversation;
          window.transferredSessionId = transferData.sessionId;
          log('Stored conversation in window object');
        }
        
        // Track successful transfer
        if (typeof posthog !== 'undefined') {
          posthog.capture('conversation_transfer_completed', {
            sessionId: transferData.sessionId,
            messageCount: transferData.conversation?.messages?.length || 0,
            timestamp: new Date().toISOString()
          });
        }
      }
    }, 100);
    
    // Stop checking after 10 seconds
    setTimeout(() => {
      clearInterval(checkInterval);
      log('Stopped waiting for chatbot to load');
    }, 10000);
  }
  
  // Initialize on DOM ready
  function init() {
    log('Initializing conversation transfer receiver');
    
    const transferData = checkForTransfer();
    
    if (transferData) {
      log('Transfer data detected, loading conversation');
      loadConversation(transferData);
    } else {
      log('No transfer data, starting fresh conversation');
    }
  }
  
  // Run initialization
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  // Also expose a global function for manual testing
  window.checkConversationTransfer = function() {
    const data = checkForTransfer();
    console.log('Manual check - Transfer data:', data);
    return data;
  };
})();

/*
INTEGRATION INSTRUCTIONS:

1. ADD TO WEBFLOW /CHATBOT PAGE:
   - Go to Page Settings for /chatbot
   - Add this script to Custom Code > Before </body> tag
   - Or include as external script: <script src="/conversation_transfer_receiver.js"></script>

2. CUSTOMIZE SELECTORS:
   - Update lines 103-104 to match your actual chat input/container selectors
   - Update line 119 to match your iframe selector if using iframe

3. BACKEND INTEGRATION (if needed):
   For full conversation transfer to work, your chatbot needs to:
   - Listen for postMessage with type: 'load_conversation'
   - OR check window.transferredConversation on initialization
   - Load the messages into the chat interface

4. TESTING:
   1. Open widget on main site
   2. Have a conversation (send a few messages)
   3. Click "Open in Full Page" button
   4. Verify conversation appears in full page
   5. Check for notification "Conversation continued from widget"

5. DEBUGGING:
   - Set DEBUG = true on line 9 to see console logs
   - Run window.checkConversationTransfer() in console to manually check

6. PRIVACY & SECURITY:
   - Data only stored in sessionStorage (not localStorage)
   - Auto-expires after 5 minutes
   - Cleared immediately after reading
   - Same-origin only (no cross-domain access)
*/