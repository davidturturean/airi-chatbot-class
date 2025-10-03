# Edit Plan: Known Limitations Document

## Critical Issues Found:
1. **OUTDATED CLAIM**: "Response times of 5-10 seconds without user feedback during processing" (line 5)
   - **REALITY**: Status indicators ARE implemented (🔄 Initializing, 🧠 Classifying, 🔍 Searching, ✨ Generating)
2. **Missing**: Current features section (what DOES work)
3. **Missing**: Widget-specific limitations
4. **Missing**: Session transfer limitations
5. **Conflicting info**: Performance note mentions "exploring options" but they're already implemented

---

## Edits to Make:

### EDIT 1: Remove outdated "without user feedback" claim (line 5)
**FIND:**
```markdown
- Response times of 5-10 seconds without user feedback during processing
```

**REPLACE WITH:**
```markdown
- Initial embedding service startup can take 15-30 seconds on first query of the day
```

**REASON:** Status indicators exist, so "without feedback" is false. First-time startup IS a real limitation.

---

### EDIT 2: Update Performance Note (lines 14-17)
**FIND:**
```markdown
Performance note: Any current response times of longer-than-average 5-10
seconds reflect the system\'s comprehensive search and validation
processes that can at times be extensive.. We are exploring options for
progress indicators and interim feedback during processing.
```

**REPLACE WITH:**
```markdown
**Performance Note:**

Typical response times range from 2-10 seconds depending on query complexity. The system provides real-time status updates during processing:

- 🔄 Initializing the request
- 🧠 Classifying query intent
- 🔍 Searching the repository
- ✨ Generating response

First-time queries may experience 15-30 second delays while the embedding service initializes. Timeout warnings appear after 15 seconds for unusually long operations.
```

**REASON:** Accurately describes current implementation, mentions status indicators already built

---

### EDIT 3: Add new "Current Features" section BEFORE limitations (after line 1)
**INSERT AFTER LINE 1:**
```markdown

## Current Features (What Works Well)

The chatbot includes several implemented features:

✓ **Real-time status indicators** during query processing (Initializing → Classifying → Searching → Generating)

✓ **Streaming responses** (text appears as it's generated, not all at once)

✓ **Session persistence** across widget and full page views

✓ **Conversation transfer** between widget popup and full page interface

✓ **Citation system** with clickable links to source documents

✓ **PostHog analytics** tracking query performance and user interactions

---

## Known Limitations

```

**REASON:** Users should know what's working before reading limitations. Provides context.

---

### EDIT 4: Add widget/session limitations (after existing limitations)
**INSERT AFTER LINE 12 (after "Unclear link styling and interaction patterns"):**
```markdown

- Widget may be overlooked by users unfamiliar with floating chat buttons

- Session management requires manual copy/paste of session ID for sharing

- Citation links open in same tab (may disrupt conversation flow)

- No conversation export functionality yet

- Limited mobile optimization (desktop-first design)
```

**REASON:** These are real limitations based on current implementation

---

### EDIT 5: Update "Limited context" limitation (line 7-8)
**FIND:**
```markdown
- Limited context provided about the chatbot\'s purpose, scope, and
  capabilities
```

**REPLACE WITH:**
```markdown
- No onboarding or example queries shown to new users to explain chatbot capabilities
```

**REASON:** More specific and actionable

---

## Summary of Changes:
1. ✅ Removed "without user feedback" (status indicators exist)
2. ✅ Added "Current Features" section highlighting what works
3. ✅ Updated performance note with accurate timing and status indicator details
4. ✅ Added widget/session-specific limitations
5. ✅ Made "limited context" more specific

## Formatting Notes:
- Preserve escape characters: `\'` for apostrophes
- Preserve markdown bold: `**text**`
- Preserve bullet points formatting
- Add checkmarks using `✓` for features list
