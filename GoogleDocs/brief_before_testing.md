# Background

The MIT AI Risk Repository project has developed an interactive chatbot
interface to provide users with empirically-grounded, evidence-based
information about AI risks. Our chatbot serves as a conversational
gateway to the comprehensive MIT AI Risk Repository, which contains
thousands of documented AI risks, their impacts, and potential
mitigations.

The current capabilities of our chatbot:

- Provides accurate, non-hallucinated responses based exclusively on AI
  Risk Repository data

- Covers comprehensive AI risk domains including safety, privacy, bias,
  governance, and socioeconomic impacts; we plan to include other AI
  Risk Initiative documents pertaining to AI risks in the future, such
  as compilations of AI risk mitigation strategies

- Includes clickable citations linking directly to source documents

- The above are achieved through retrieval-augmented generation (RAG)
  with field-aware hybrid search

We believe this chatbot represents a critical component of the AI Risk
Repository\'s mission to make AI risk research accessible to
policymakers, researchers, practitioners, as well as the general public.
As we prepare for broader deployment, we need systematic user feedback
to optimize the interface and user experience. This is where you come
in - thank you!

# 

# Testing Objectives

For this testing phase, we aim to:

1.  Evaluate User Experience: Assess the clarity, usability, and
    intuitiveness of the current chatbot interface

2.  Identify Friction Points: Document specific moments where users
    experience confusion, frustration, or uncertainty

3.  Validate Information Architecture: Determine whether users
    understand the chatbot\'s purpose, scope, and capabilities in the
    first place

4.  Optimize Response Presentation: Gather feedback on formatting,
    citation display, and content organization

5.  Assess User Expectations: Understand what users expect(ed) from an
    AI risk chatbot in the first place and how our implementation aligns
    with those expectations

Data Collection Transparency: Please note that the backend system logs
all user inputs for analysis and improvement purposes. Your interactions
will be used to enhance the chatbot\'s functionality and user
experience. Personal information should not be included in your test
queries.

## 

## Pre-Testing Setup

**Time Commitment:** ~40-45 minutes total

- Pre-testing setup: 5 minutes
- Phase 1 (Initial Impressions): 3-5 minutes
- Phase 2 (Widget + Full Page Testing): 15-20 minutes
- Phase 3 (Form Completion): 15 minutes

Access the Chatbot:

- Navigate to [[https://ai-risk-repository-601932-8fac479478ab1.webflow.io]{.underline}](https://ai-risk-repository-601932-8fac479478ab1.webflow.io)

- You\'ll see a **floating chat button** in the bottom-right corner - this is the widget version

- Ensure you have a stable internet connection

- Use a desktop or laptop browser (Chrome, Firefox, or Safari
  recommended), not mobile for now please

Recording Setup:

- Install [[Veed]{.underline}](http://veed.io) screen recording software
  or use your preferred screen recording tool

- Begin recording before starting your interaction with the chatbot

- Include audio commentary describing your thoughts and reactions
  throughout the session

### 

## 

# Session Structure

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

    - What you understand the chatbot\'s purpose to be

    - Any confusion or uncertainty about how to proceed

    - What additional information or guidance you would find helpful

## 

## Phase 2: Natural Interaction (15-20 minutes)

### Part A: Widget Testing (7-10 minutes)

1.  **Ask 2-3 questions from the "Repository-Related Queries" below** in the widget popup

2.  During your widget interactions, please:

    - Think aloud as you formulate questions
    - Comment on response times and any periods of uncertainty
    - React to the content, formatting, and presentation of responses
    - Attempt to click on citations
    - Describe how the compact widget view affects your experience

3.  **Test the Session feature:**

    - Click the "Session" button to view your session ID
    - Try copying the session ID using the copy button
    - Comment on whether this feature is useful or confusing

4.  **Click the "Open in Full Page" button** and observe what happens

### Part B: Full Page Testing (8-10 minutes)

5.  **Verify your conversation history transferred correctly**

    - Do you see all your previous messages from the widget?
    - Verbally confirm whether the transfer worked

6.  **Ask 3-4 more questions** from both "Repository-Related" and "Edge Case" queries below

7.  **Compare the two experiences:**

    - Which interface (widget vs full page) do you prefer and why?
    - How does the full page change your interaction with the chatbot?
    - Are citations easier to use in the full page view?

### Test Queries:

**Repository-Related Queries (recommended):**

- \"What are the employment risks from AI automation?\"
- \"How does facial recognition bias affect marginalized communities?\"
- \"What privacy concerns arise from AI surveillance systems?\"
- \"What are the governance gaps in AI regulation?\"

**General Knowledge Queries & Edge Cases (to test boundaries):**

- \"What\'s the capital of France?\"
- \"How do I bake cookies?\"
- \"Tell me about artificial flowers\" (contains \'artificial\' but not AI-related)
- \"What machine should I buy for my gym?\" (contains \'machine\' but not AI-related)

### Stop recording after completing both parts.

You\'ll share the recording with us via the form in Phase 3.

## Phase 3: Focused Evaluation (15 minutes)

**Stop screen recording now** (to avoid recording personal information).

After natural interaction, please:

1.  Review our [[known limitations document]{.underline}](?tab=t.qacza6rqo0g0)

2.  Complete this [[evaluation form]{.underline}](https://docs.google.com/forms/d/e/1FAIpQLSdcoCHp7TiHz6CeFQpgSx6PY2gcZ6i_XyPCvnCmKAwmRlTfGw/viewform?usp=dialog)

3.  Upload your screen recording using the form

# Contact Information

Project Team:

- Peter Slattery (Project Lead),
  [[pslat@mit.edu]{.underline}](mailto:pslat@mit.edu)

- Sasha Krigel (UI/UX),
  [[skrigel@mit.edu]{.underline}](mailto:skrigel@mit.edu)

- David Turturean (Backend),
  [[davidct@mit.edu]{.underline}](mailto:davidct@mit.edu)
