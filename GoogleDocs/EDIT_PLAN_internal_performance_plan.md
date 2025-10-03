# Edit Plan: Internal Performance Plan

## Critical Issues Found:
1. **SECURITY**: PostHog API key exposed in line 1
2. **OUTDATED**: "Alternative A: Floating chat widget that expands → Idea: implement" (line 57-62) - **WIDGET ALREADY EXISTS**
3. **OUTDATED**: "averaging 2-3 second response times" (line 26) conflicts with "5-10 seconds" in brief
4. **MISSING**: Widget testing objectives in feedback methodology
5. **MISSING**: Session transfer metrics to track
6. **HIGHLIGHTED TEXT**: Multiple `.mark` formatting that should be preserved

---

## Edits to Make:

### EDIT 1: Remove/Redact PostHog API key (line 1)
**FIND:**
```markdown
*PostHog API key: phx_pa5zpKS0q1DTprlpwAaInqlYFIqY2u8iWCKL2C4m2FF5S7M*
```

**REPLACE WITH:**
```markdown
*PostHog Analytics: See project dashboard at [https://app.posthog.com/](https://app.posthog.com/)*

*Note: Project API key is already configured in frontend code (`frontend/src/utils/analytics.ts`)*
```

**REASON:** Don't expose API keys unnecessarily in docs. Reference location instead.

---

### EDIT 2: Update "What We Have" section (lines 17-26)
**FIND:**
```markdown
## **What We Have**

• Chatbot embedded in airisk.mit.edu

• Direct navigation from main site \"Chatbot\" tab to /chat interface
(no separate homepage for the chatbot)

• Citation system linking to source documents

• Diverse query processing [averaging 2-3 second response times]{.mark}
```

**REPLACE WITH:**
```markdown
## **What We Have**

• **Floating chat widget** on all airisk.mit.edu pages with burgundy branding

• **Full-page chat interface** accessible via /chatbot URL

• **Session transfer system** enabling conversation continuity between widget ↔ full page

• **Session persistence** via backend API (`/api/session/{id}/messages` endpoints)

• **Citation system** with clickable RID links to source documents

• **Real-time status indicators** during query processing (🔄 Initializing, 🧠 Classifying, 🔍 Searching, ✨ Generating)

• **PostHog analytics integration** tracking queries, responses, citations, errors, and session metrics

• [Response times: 2-10 seconds typical, 15-30 seconds on first query (embedding initialization)]{.mark}
```

**REASON:** Widget exists! Update to reflect current implementation accurately.

---

### EDIT 3: Replace "Interface Design Decisions" section (lines 55-62)
**FIND:**
```markdown
## **2. Interface Design Decisions (not mutually exclusive)**

Current: Full-page embedded chat via iframe

Alternative A: Floating chat widget that expands

→ Idea: implement Alternative A as well, with option to expand to
full-page, and see how the testing for that goes
```

**REPLACE WITH:**
```markdown
## **2. Interface Design & User Preference**

**Current Implementation:**

• Floating widget (popup) on main site pages
• Full-page interface at /chatbot
• Session transfer between both interfaces

**Questions to Answer:**

• Which interface do users prefer for quick questions vs. in-depth research?
• Is the widget discoverable enough on the main page?
• Does session transfer work reliably from user perspective?
• Do users understand they can switch between interfaces?
• What percentage of users try both vs. stick to one?
```

**REASON:** Widget already implemented - focus on testing preferences, not implementation decisions

---

### EDIT 4: Add widget metrics to "What we will measure" (after line 138)
**INSERT AFTER:**
```markdown
• [Error rates and timeout frequencies]{.mark}
```

**ADD:**
```markdown

**Widget & Session Transfer Metrics:**

• [Widget button click rate (how many visitors engage)]{.mark}
• [Widget → Full Page transition rate]{.mark}
• [Session transfer success rate (messages preserved correctly)]{.mark}
• [Session ID copy attempts and success]{.mark}
• [Average time spent in widget vs. full page]{.mark}
• [Query count comparison: widget-only vs. full-page-only vs. mixed users]{.mark}
```

**REASON:** Need to track widget-specific metrics based on what was built

---

### EDIT 5: Update survey questions to include widget testing (after line 161)
**INSERT AFTER:**
```markdown
7\. [Did you encounter any errors or timeouts? (Yes/No +
details)]{.mark}
```

**ADD:**
```markdown

8\. Did you try both the widget and full page versions? (Yes, both / Only widget / Only full page)

9\. If you tried both, which did you prefer? (Widget / Full page / No preference) [Why?]{.mark}

10\. Was the floating chat button easy to find on the main page? (Yes, immediately / Yes, after looking / No, missed it)

11\. Did the conversation transfer correctly when switching to full page? (Yes, perfectly / Mostly / No, messages were lost / Didn't try)
```

**REASON:** Google Form has these questions - internal doc should match

---

### EDIT 6: Update "Performance metrics for each task" (lines 108-114)
**FIND:**
```markdown
[Performance metrics for each task:]{.mark}

[• Response time (target \<2s)]{.mark}

[• Factual accuracy (target \>95%)]{.mark}

[• Citation validity (100% working links)]{.mark}
```

**REPLACE WITH:**
```markdown
[Performance metrics for each task:]{.mark}

[• Response time (target: \<5s typical, \<15s max excluding first-time init)]{.mark}

[• Factual accuracy (target \>95%)]{.mark}

[• Citation validity (target: 100% working links)]{.mark}

[• Status indicator appearance (target: 100% of queries show progress)]{.mark}
```

**REASON:** <2s target is unrealistic. 2-10s is current performance. Add status indicator metric.

---

### EDIT 7: Add PostHog event reference (after line 165)
**INSERT AFTER:**
```markdown
\+ [Automated performance metrics dashboard with real-time monitoring,
through Railway]{.mark}
```

**ADD:**
```markdown

**PostHog Events Being Tracked:**

• `chatbot_opened` - Initial widget/page load
• `query_submitted` - User sends message
• `response_received` - Bot responds (includes latency_ms, citations_count, response_length)
• `citation_clicked` - User clicks RID link
• `error_occurred` - Any errors during query processing
• `session_ended` - Session summary with total queries and duration
• `session_transferred` - Widget → Full Page transition *(to be added)*

See `frontend/src/utils/analytics.ts` for implementation details.
```

**REASON:** Documents what's already being tracked, identifies what needs to be added

---

## Summary of Changes:
1. ✅ Removed PostHog API key, replaced with dashboard reference
2. ✅ Updated "What We Have" to reflect widget, session transfer, status indicators
3. ✅ Replaced "Alternative A" with current implementation testing questions
4. ✅ Added widget & session transfer metrics section
5. ✅ Added widget-specific survey questions
6. ✅ Updated response time targets to realistic values
7. ✅ Added PostHog events reference

## Formatting Notes:
- **PRESERVE ALL `{.mark}` highlighting** - this is intentional emphasis
- Preserve bold: `**text**`
- Preserve italics: `*text*`
- Preserve escape characters: `\` before special chars
- Preserve numbered list format: `1\.` etc.
