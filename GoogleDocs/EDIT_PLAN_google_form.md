# Edit Plan: Google Form Updates

## Based on:
- Existing `docs/google_form_additions.md` (14 questions to add)
- User Testing Brief updates (widget testing, session transfer)
- Need to add 2 more widget-specific questions

---

## Questions to ADD to Google Form

### SECTION 4: Widget vs Full Page Experience
*Already planned - from `docs/google_form_additions.md`*

**Q1.** Did you try both the widget (popup) and full page versions?
- Yes, tried both
- Only tried widget
- Only tried full page

**Q2.** If you tried the widget, how intuitive was it to use?
- 1 (Very confusing) - 2 - 3 - 4 - 5 (Very intuitive)

**Q3.** Did the conversation successfully transfer when you clicked "Open in Full Page"?
- Yes, perfectly - all messages appeared
- Mostly - minor issues
- No - conversation was lost
- N/A - didn't try this feature

**Q4.** Which version do you prefer for quick questions?
- Widget (popup)
- Full page
- No preference

**Q5.** Which version do you prefer for in-depth research?
- Widget (popup)
- Full page
- No preference

### NEW ADDITIONS (not in original plan):

**Q6. [NEW]** Did you notice the floating chat button on the main page?
- Yes, immediately
- Yes, after a few seconds
- Only after being told about it
- No, I didn't see it

**Q7. [NEW]** Did the session ID copy button work when you tried it?
- Yes, copied successfully
- No, showed an error/alert
- Partially worked (had to use manual method)
- Didn't try this feature

---

### SECTION 5: Technical Issues
*Already planned - from `docs/google_form_additions.md`*

**Q1.** Did you experience any technical problems? (Select all that apply)
- [ ] Page wouldn't load
- [ ] Chatbot didn't respond
- [ ] Slow response times
- [ ] Browser crashed/froze
- [ ] Citations didn't work
- [ ] Widget button missing
- [ ] Session transfer failed
- [ ] Other: ___________
- [ ] No issues

**Q2.** If you experienced issues, how often did they occur?
- Every time I tried to use it
- Frequently (more than half the time)
- Occasionally (less than half)
- Rarely (once or twice)
- Never had issues

**Q3.** On a scale of 1-5, how reliable was the chatbot?
- 1 (Very unreliable) - 2 - 3 - 4 - 5 (Very reliable)

---

### SECTION 6: Specific Use Cases
*Already planned - from `docs/google_form_additions.md`*

**Q1.** What specific question(s) did you ask the chatbot? (Open-ended)
- [Large text box]

**Q2.** For your main question, did you get the information you needed?
- Yes, completely
- Mostly
- Partially
- Not really
- Not at all

**Q3.** How many follow-up questions did you ask?
- None
- 1-2
- 3-5
- 6-10
- More than 10

---

## IMPORTANT: Background Section Repositioning

### DO NOT add Section 0 (Background) at the beginning

**REASON:** Asking about expertise level FIRST creates selection bias - experts may perform differently knowing they're identified as experts.

### INSTEAD: Add Background questions at the END (after all testing questions)

**New Section 7: Background** (move to end of form, BEFORE final improvements section)

**Q1.** What is your role?
- Graduate Student
- Postdoc
- Faculty
- Research Staff
- Undergraduate
- Other: ___________

**Q2.** How familiar are you with AI risk research?
- Very familiar (actively research in this area)
- Moderately familiar (have read papers/attended talks)
- Somewhat familiar (basic awareness)
- Not familiar

**Q3.** Have you used the AI Risk Repository database before?
- Yes, frequently
- Yes, a few times
- Once or twice
- Never

---

## Final Form Structure (32 Questions Total)

**Sections 1-3: Existing Questions (16 total)** - NO CHANGES
- Section 1: Response Quality (6 questions)
- Section 2: UI/UX (5 questions)
- Section 3: Overall Preference (5 questions)

**Section 4: Widget vs Full Page (7 questions)** - NEW
- Q1-Q5: From original plan
- Q6-Q7: Added for widget discoverability & session copy button

**Section 5: Technical Issues (3 questions)** - NEW
- From original plan, added "Session transfer failed" to Q1 checklist

**Section 6: Specific Use Cases (3 questions)** - NEW
- From original plan

**Section 7: Background (3 questions)** - NEW, MOVED TO END
- From original plan, repositioned to avoid bias

**Section 8: Improvements (3 questions)** - EXISTING, KEEP AT END
- What changes would improve experience
- Other chatbots to learn from
- Additional comments

**TOTAL: 32 questions** (16 existing + 16 new)

---

## Implementation Instructions

### Step 1: Open Google Form Editor
https://docs.google.com/forms/d/e/1FAIpQLSdcoCHp7TiHz6CeFQpgSx6PY2gcZ6i_XyPCvnCmKAwmRlTfGw/edit

### Step 2: Add New Sections
After your existing Section 3 (Overall Preference), add:

1. **Section 4: Widget vs Full Page Experience**
   - Add all 7 questions listed above
   - Set Q2, Q3, Q6, Q7 to appear conditionally based on Q1 answer (optional)

2. **Section 5: Technical Issues**
   - Add all 3 questions
   - Make Q1 a "Checkboxes" question type
   - Make Q2 conditional on Q1 (only show if issues selected)

3. **Section 6: Specific Use Cases**
   - Add all 3 questions
   - Q1 should be "Long answer" text type

4. **Section 7: Background**
   - Add all 3 questions
   - Place BEFORE final improvements section

### Step 3: Enable Progress Bar
- Go to Settings (gear icon)
- Enable "Show progress bar"

### Step 4: Optional Enhancements
- Add email collection field at end (optional, for follow-up interviews)
- Add "Upload your screen recording" file upload question in Section 6
- Set form to allow response editing (Settings → "Respondents can edit after submit")

---

## Notes
- All widget-related questions align with User Testing Brief Phase 2
- Session transfer question (Q3) matches what users are instructed to test
- Widget discoverability (Q6) tests Phase 1 success criteria
- Copy button question (Q7) addresses Opera browser issue we fixed
