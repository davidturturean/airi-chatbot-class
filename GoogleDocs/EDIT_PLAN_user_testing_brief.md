# Edit Plan: User Testing Brief

## Critical Issues Found:
1. **URL points to Railway instead of Webflow** (line 67-68)
2. **No mention of widget** - users won't know to test it
3. **No widget vs full page instructions**
4. **Missing time commitment information**
5. **Google Form URL is present but should be verified**
6. **Recording scope unclear** - should they record form completion?
7. **No success criteria for Phase 1**

---

## Edits to Make:

### EDIT 1: Fix "Pre-Testing Setup" section (lines 63-83)
**FIND:**
```markdown
Access the Chatbot:

- Navigate to [[this
  URL]{.underline}](https://airi-chatbot-class-production.up.railway.app/chat)

- Ensure you have a stable internet connection

- Use a desktop or laptop browser (Chrome, Firefox, or Safari
  recommended), not mobile for now please
```

**REPLACE WITH:**
```markdown
**Time Commitment:** ~40-45 minutes total
- Pre-testing setup: 5 minutes
- Phase 1 (Initial Impressions): 3-5 minutes
- Phase 2 (Widget + Full Page Testing): 15-20 minutes
- Phase 3 (Form Completion): 15 minutes

Access the Chatbot:

- Navigate to [[https://ai-risk-repository-601932-8fac479478ab1.webflow.io]{.underline}](https://ai-risk-repository-601932-8fac479478ab1.webflow.io)

- You'll see a **floating chat button** in the bottom-right corner - this is the widget version

- Ensure you have a stable internet connection

- Use a desktop or laptop browser (Chrome, Firefox, or Safari recommended), not mobile for now please
```

**REASON:** Adds time commitment, fixes URL to Webflow main page, mentions widget explicitly

---

### EDIT 2: Update Phase 1 (lines 91-106)
**FIND:**
```markdown
## Phase 1: Initial Impressions (3-5 minutes)

1.  Arrive at the chatbot interface

2.  Spend 1-2 minutes exploring the interface before sending any
    messages

3.  Verbally describe:

    - Your first impression of the interface

    - What you understand the chatbot\'s purpose to be

    - Any confusion or uncertainty about how to proceed

    - What additional information or guidance you would find helpful
```

**REPLACE WITH:**
```markdown
## Phase 1: Initial Impressions (3-5 minutes)

1.  Arrive at the main page (https://ai-risk-repository-601932-8fac479478ab1.webflow.io)

2.  **WITHOUT clicking anything yet**, verbally describe:

    - Do you notice a chatbot? Where is it?
    - What do you think it does based on visual cues?
    - Would you click it? Why or why not?

3.  **THEN** click the floating chat button to open the widget

4.  Spend 1-2 minutes exploring the widget interface before sending any messages

5.  Verbally describe:

    - Your first impression of the widget interface

    - What you understand the chatbot's purpose to be

    - Any confusion or uncertainty about how to proceed

    - What additional information or guidance you would find helpful
```

**REASON:** Adds widget discoverability testing, structures observation before interaction

---

### EDIT 3: Completely rewrite Phase 2 (lines 110-155)
**FIND:**
```markdown
## Phase 2: Natural Interaction (10-15 minutes)

Engage with the chatbot using queries relevant to your interests or
work.

Please also consider testing these specific types of questions:

*Repository-Related Queries (recommended):*

- \"What are the employment risks from AI automation?\"

- \"How does facial recognition bias affect marginalized communities?\"

- \"What privacy concerns arise from AI surveillance systems?\"

- \"What are the governance gaps in AI regulation?\"

*General Knowledge Queries (unrelated to AI, AI risk, or the AI Risk
Repository) And Edge Cases (to test boundaries):*

- \"What\'s the capital of France?\"

- \"How do I bake cookies?\"

<!-- -->

- \"Tell me about artificial flowers\" (contains \'artificial\' but not
  AI-related)

- \"What machine should I buy for my gym?\" (contains \'machine\' but
  not AI-related)

During your interactions, please:

- Think aloud as you formulate questions

- Comment on response times and any periods of uncertainty

- React to the content, formatting, and presentation of responses

- Attempt to click on citations

- Describe how what you see differs from expectations

Stop recording when this is done. Please share the recording with us in
the short form linked below in Phase 3.
```

**REPLACE WITH:**
```markdown
## Phase 2: Natural Interaction (15-20 minutes)

### Part A: Widget Testing (7-10 minutes)

1. **Ask 2-3 questions from the "Repository-Related Queries" below** in the widget popup

2. During your widget interactions, please:
   - Think aloud as you formulate questions
   - Comment on response times and any periods of uncertainty
   - React to the content, formatting, and presentation of responses
   - Attempt to click on citations
   - Describe how the compact widget view affects your experience

3. **Test the Session feature:**
   - Click the "Session" button to view your session ID
   - Try copying the session ID using the copy button
   - Comment on whether this feature is useful or confusing

4. **Click the "Open in Full Page" button** and observe what happens

### Part B: Full Page Testing (8-10 minutes)

5. **Verify your conversation history transferred correctly**
   - Do you see all your previous messages from the widget?
   - Verbally confirm whether the transfer worked

6. **Ask 3-4 more questions** from both "Repository-Related" and "Edge Case" queries below

7. **Compare the two experiences:**
   - Which interface (widget vs full page) do you prefer and why?
   - How does the full page change your interaction with the chatbot?
   - Are citations easier to use in the full page view?

### Test Queries:

**Repository-Related Queries (recommended):**

- "What are the employment risks from AI automation?"
- "How does facial recognition bias affect marginalized communities?"
- "What privacy concerns arise from AI surveillance systems?"
- "What are the governance gaps in AI regulation?"

**General Knowledge Queries & Edge Cases (to test boundaries):**

- "What's the capital of France?"
- "How do I bake cookies?"
- "Tell me about artificial flowers" (contains 'artificial' but not AI-related)
- "What machine should I buy for my gym?" (contains 'machine' but not AI-related)

### Stop recording after completing both parts.

You'll share the recording with us via the form in Phase 3.
```

**REASON:** Splits into widget/full page testing, adds session transfer testing, adds comparison questions

---

### EDIT 4: Update Phase 3 recording instructions (line 157-161)
**FIND:**
```markdown
## Phase 3: Focused Evaluation (15 minutes)

After natural interaction, please review our [[known
limitations]{.underline}](?tab=t.qacza6rqo0g0) and complete this [[short
form]{.underline}](https://docs.google.com/forms/d/e/1FAIpQLSdcoCHp7TiHz6CeFQpgSx6PY2gcZ6i_XyPCvnCmKAwmRlTfGw/viewform?usp=dialog).
```

**REPLACE WITH:**
```markdown
## Phase 3: Focused Evaluation (15 minutes)

**Stop screen recording now** (to avoid recording personal information).

After natural interaction, please:

1. Review our [[known limitations document]{.underline}](?tab=t.qacza6rqo0g0)

2. Complete this [[evaluation form]{.underline}](https://docs.google.com/forms/d/e/1FAIpQLSdcoCHp7TiHz6CeFQpgSx6PY2gcZ6i_XyPCvnCmKAwmRlTfGw/viewform?usp=dialog)

3. Upload your screen recording using the form
```

**REASON:** Clarifies when to stop recording, breaks down steps explicitly

---

## Summary of Changes:
1. ✅ Added time commitment section
2. ✅ Fixed URL from Railway to Webflow main page
3. ✅ Added widget mention and discoverability testing
4. ✅ Split Phase 2 into widget/full page parts
5. ✅ Added session transfer testing (copy button, full page button)
6. ✅ Added success criteria to Phase 1 (widget discovery)
7. ✅ Clarified recording scope (stop before form)
8. ✅ Kept Google Form URL (already correct)

## Formatting Notes:
- Preserve all markdown underline syntax: `[[text]{.underline}](url)`
- Preserve bold italics: `*text*` and `**text**`
- Preserve numbered lists and bullet points
- Preserve escape characters: `\'` for apostrophes
