# AI Risk Repository Chatbot: User Experience Testing Brief

## ⚠️ Access Information (NEW)

### Password-Protected Access
The chatbot is currently in **Stage 1: Internal Testing** with password protection.

**Access Credentials:**
- URL: `https://airisk.mit.edu/chat` 
- Password: `MITai2024test`
- Testing Period: September 11-18, 2024

### Important Updates
- Response times are now **3-5 seconds** (updated from 2-3s)
- All interactions are tracked via dashboard metrics
- PostHog analytics is recording user behavior (anonymized)
- Recording upload link: [Will be provided via email]
- Survey link: [Will be provided after testing]

---

## Background
The MIT AI Risk Repository project has developed an interactive chatbot interface to provide users with empirically-grounded, evidence-based information about AI risks. Our chatbot serves as a conversational gateway to the comprehensive MIT AI Risk Repository, which contains thousands of documented AI risks, their impacts, and potential mitigations.

### Current Capabilities
- Provides accurate, non-hallucinated responses based exclusively on AI Risk Repository data
- Covers comprehensive AI risk domains including safety, privacy, bias, governance, and socioeconomic impacts; we plan to include other AI Risk Initiative documents pertaining to AI risks in the future, such as compilations of AI risk mitigation strategies
- Includes clickable citations linking directly to source documents
- The above are achieved through retrieval-augmented generation (RAG) with field-aware hybrid search

We believe this chatbot represents a critical component of the AI Risk Repository's mission to make AI risk research accessible to policymakers, researchers, practitioners, as well as the general public. As we prepare for broader deployment, we need systematic user feedback to optimize the interface and user experience. This is where you come in - thank you!

## Testing Objectives
For this testing phase, we aim to:
1. **Evaluate User Experience:** Assess the clarity, usability, and intuitiveness of the current chatbot interface
2. **Identify Friction Points:** Document specific moments where users experience confusion, frustration, or uncertainty
3. **Validate Information Architecture:** Determine whether users understand the chatbot's purpose, scope, and capabilities in the first place
4. **Optimize Response Presentation:** Gather feedback on formatting, citation display, and content organization
5. **Assess User Expectations:** Understand what users expect(ed) from an AI risk chatbot in the first place and how our implementation aligns with those expectations

### Data Collection Transparency
Please note that the backend system logs all user inputs for analysis and improvement purposes. Your interactions will be used to enhance the chatbot's functionality and user experience. Personal information should not be included in your test queries.

**NEW: Metrics Being Collected:**
- Response latency (target: <3000ms median)
- Groundedness score (target: >95%)
- Citation accuracy
- Session duration and query patterns
- User satisfaction ratings

## Pre-Testing Setup

### Access the Chatbot
1. Navigate to `https://airisk.mit.edu/chat`
2. Enter password: `MITai2024test` when prompted
3. Ensure you have a stable internet connection
4. Use a desktop or laptop browser (Chrome, Firefox, or Safari recommended), not mobile for now please

### Recording Setup
1. Install Veed screen recording software or use your preferred screen recording tool
2. Begin recording **before** navigating to the password page
3. Include audio commentary describing your thoughts and reactions throughout the session
4. Upload recording to: [Google Drive link will be provided]

## Session Structure

### Phase 1: Initial Impressions (3-5 minutes)
Arrive at the chatbot interface (after entering password)
Spend 1-2 minutes exploring the interface before sending any messages
Verbally describe:
- Your first impression of the interface
- What you understand the chatbot's purpose to be
- Any confusion or uncertainty about how to proceed
- What additional information or guidance you would find helpful

### Phase 2: Natural Interaction (10-15 minutes)
Engage with the chatbot using queries relevant to your interests or work.

Please also consider testing these specific types of questions:

**Repository-Related Queries (recommended):**
- "What are the employment risks from AI automation?"
- "How does facial recognition bias affect marginalized communities?"
- "What privacy concerns arise from AI surveillance systems?"
- "What are the governance gaps in AI regulation?"

**General Knowledge Queries (unrelated to AI, AI risk, or the AI Risk Repository) And Edge Cases (to test boundaries):**
- "What's the capital of France?"
- "How do I bake cookies?"
- "Tell me about artificial flowers" (contains 'artificial' but not AI-related)
- "What machine should I buy for my gym?" (contains 'machine' but not AI-related)

During your interactions, please:
- Think aloud as you formulate questions
- Comment on response times and any periods of uncertainty
- React to the content, formatting, and presentation of responses
- Attempt to click on citations
- Describe how what you see differs from expectations

Stop recording when this is done. Please share the recording with us via the upload link provided.

### Phase 3: Focused Evaluation (15 minutes)
After natural interaction, please complete the survey: [Link will be provided via email]

## Known Limitations (NEW - Now Disclosed)
We're aware of these issues and actively working on improvements:
- Response times of 3-5 seconds (comprehensive search requires processing time)
- Basic interface lacking some user guidance
- Limited visual feedback during processing
- Citations may show as "AI Risk Repository" instead of specific document titles

### Performance Note
Current response times of 3-5 seconds reflect the system's comprehensive search and validation processes. We are implementing progress indicators and exploring optimization opportunities.

## Technical Architecture (For Context)
The chatbot employs advanced retrieval techniques including:
- Field-aware hybrid search combining vector similarity and keyword matching
- Multi-model fallback for enhanced reliability
- Semantic intent classification to optimize response relevance
- Real-time citation consistency validation
- **NEW:** Real-time metrics dashboard tracking all interactions
- **NEW:** PostHog analytics for user behavior analysis

## Metrics Dashboard (NEW)
Your testing session contributes to our deployment readiness assessment across 10 key metrics:
1. Groundedness (>95% target)
2. Hallucination Rate (<2% target)
3. Retrieval Accuracy (>90% target)
4. Response Latency (<3s median target)
5. User Satisfaction (>70% target)
6. And 5 additional operational metrics

View live metrics at: `http://localhost:8090/dashboard` (internal access only)

## Contact Information
**Project Team:**
- Peter Slattery (Project Lead): pslat@mit.edu
- Sasha Krigel (UI/UX): skrigel@mit.edu
- David Turturean (Backend): davidct@mit.edu

## Thank You!
Your participation directly impacts our ability to improve this tool for the AI safety community. Every piece of feedback matters.

---

*Document Version: 2.0 - Updated September 11, 2024*
*Stage: Internal Testing (Password Protected)*