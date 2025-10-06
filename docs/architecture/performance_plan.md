# AI Risk Repository Chatbot: User Feedback & Performance Improvement Plan

**PostHog API Key:** `phx_pa5zpKS0q1DTprlpwAaInqlYFIqY2u8iWCKL2C4m2FF5S7M`  
**Dashboard URL:** `http://localhost:8090/dashboard`  
**Last Updated:** September 11, 2024  
**Current Stage:** Internal Testing (Password Protected)

## 🚀 IMPLEMENTATION STATUS (NEW SECTION)

### ✅ Completed Technical Infrastructure
- **Metrics Dashboard:** Fully operational with real-time data (NO mock data)
- **10 Deployment Gates:** Implemented based on Running Lean methodology
- **Database Persistence:** All metrics stored in SQLite
- **API Endpoints:** `/api/metrics/hourly` and `/api/metrics/details/<metric>`
- **PostHog Analytics:** Configured and ready for deployment
- **Citation System:** Fixed "preprint_raw.txt" issue
- **Test Data Generator:** `scripts/generate_test_data.py` ready

### 🟨 In Progress
- **Password Protection:** Being enabled on Webflow today
- **Google Form:** Survey questions ready, form creation pending
- **User Scheduling:** 6-10 testers being identified

### ❌ Not Started
- **Pop-up Widget:** Alternative interface option
- **Tooltips:** UI enhancements
- **Mobile Optimization:** Responsive design improvements

---

## Current State & Challenge

### What We Have
- Chatbot embedded in airisk.mit.edu
- Direct navigation from main site "Chatbot" tab to /chat interface (no separate homepage for the chatbot)
- Citation system linking to source documents
- **UPDATED:** Response times now 3-5 seconds (was 2-3 seconds)
- **NEW:** Real-time metrics dashboard tracking all interactions
- **NEW:** 10 deployment gates with specific thresholds

### The Challenge
The "curse of knowledge", of understanding the system's capabilities and limitations. We need fresh perspectives to understand:
- What new users expect vs. what they experience
- Whether the current interface supports user goals effectively
- What barriers prevent successful task completion
- Which queries cause performance bottlenecks
- How system accuracy varies by query type

## Deployment Gates & Metrics (NEW SECTION)

### The 10 Gates We Track

| Gate # | Metric | Current | Target | Stage 1→2 | Stage 2→3 | Status |
|--------|--------|---------|--------|-----------|-----------|---------|
| 1 | Groundedness | TBD | ≥95% | ≥90% | ≥95% | 🔄 Awaiting data |
| 2 | Hallucination Rate | TBD | ≤2% | ≤5% | ≤2% | 🔄 Awaiting data |
| 3 | Retrieval Hit Rate | TBD | ≥90% | ≥85% | ≥90% | 🔄 Awaiting data |
| 4 | Median Latency | ~3500ms | ≤3000ms | ≤5000ms | ≤3000ms | 🟨 Close |
| 5 | P95 Latency | ~7000ms | ≤7000ms | ≤10000ms | ≤7000ms | ✅ Meeting |
| 6 | Containment Rate | TBD | ≥60% | ≥50% | ≥60% | 🔄 Awaiting data |
| 7 | Satisfaction Score | TBD | ≥70% | ≥70% | ≥80% | 🔄 Awaiting data |
| 8 | Cost per Query | ~$0.25 | ≤$0.30 | ≤$0.40 | ≤$0.30 | ✅ Meeting |
| 9 | Safety Violations | 0 | 0 | 0 | 0 | ✅ Meeting |
| 10 | Data Freshness | <24h | ≤24h | ≤24h | ≤24h | ✅ Meeting |

**Stage Progression Requirements:**
- **Stage 1 → Stage 2 (Internal → Canary):** 6/10 gates passing
- **Stage 2 → Stage 3 (Canary → Production):** 8/10 gates passing

## Key Questions to Answer Internally

### 1. Onboarding & First Impressions
- Do users understand what the chatbot can/cannot do from first impression?
- Are example queries or guided options needed?
- Does initial query response time affect user engagement?

### 2. Interface Design Decisions (not mutually exclusive)
- **Current:** Full-page embedded chat via iframe
- **Alternative A:** Floating chat widget that expands
- **Idea:** Implement Alternative A as well, with option to expand to full-page

### 3. User Intent & Success
- What are users actually trying to accomplish?
- Can they complete their intended tasks?
- What queries fail most often?
- What is the accuracy rate for different query categories?
- How many retries occur due to unsatisfactory responses?

### 4. Trust & Understanding
- Do users trust the responses?
- Do users understand the citations and use them?
- Are citations accurate and do links work properly?
- What percentage of responses contain verifiable facts?

### 5. Deployment Threshold
What performance level justifies deployment?
**ANSWER:** See deployment gates table above

## Feedback Methodology

### Phase 1: User Research (Week of Sept 11-18)
**Structured User Testing Sessions**
- Target: 6-10 people (45 minutes each)
- Plus automated testing on 100+ queries

**Specific Test Tasks:**
1. Find information about AI privacy risks
2. Understand how the repository categorizes risks
3. Explore employment impacts of AI
4. Locate specific statistics about AI safety

**Performance Metrics for Each Task:**
- Response time (target <3s median)
- Factual accuracy (target >95%)
- Citation validity (100% working links)

**Non-specific Test Tasks:**
- 4-6 prompts at tester's discretion

### What We Will Measure

**Quantitative Metrics (Automated):**
- Task completion rates
- Time to first meaningful interaction
- Query-to-response latency
- Token usage per query type
- Error rates and timeout frequencies
- Citation click-through rates
- Session duration
- Query refinement patterns

**Qualitative Metrics (Survey):**
1. Did you find what you were looking for? (Yes/Partially/No)
2. What was confusing about the interface? (open text)
3. Can we better convey what the system knows?
4. What would make this tool more useful? (open text)
5. Recommendation likelihood (1-10 scale)
6. Was the response speed acceptable? (Yes/No/Sometimes)
7. Did you encounter any errors? (Yes/No + details)

### How We Will Measure

**Real-time Dashboard:** `http://localhost:8090/dashboard`
- Live metrics updates every 30 seconds
- Drill-down capability for each gate
- Export functionality for reports

**PostHog Analytics:**
- User journey tracking
- Conversion funnels
- Drop-off analysis
- A/B testing capability (future)

**Survey Collection:**
- Google Form (being created)
- Post-session completion
- Anonymous responses

### Secondary Considerations (Important Long-term)

1. Mobile/tablet iframe compatibility
2. Autocomplete impact on query formulation
3. Conversation history/export functionality
4. Session memory usage implications

### Additional Performance Testing

- Stress testing with edge cases
- Database query optimization
- Multi-model fallback performance
- Cache effectiveness

## Phase 2: Analysis and Implementation (Week of Sept 18-25)

### Immediate Actions Based on Testing
1. Fix critical bugs (same day)
2. Address performance bottlenecks
3. Improve unclear UI elements
4. Update documentation

### Priority Matrix for Changes

**High Priority (Do immediately):**
- Any safety/security issues
- Complete failures/timeouts
- Broken core functionality

**Medium Priority (Do this week):**
- Performance optimizations
- UI/UX improvements
- Documentation updates

**Low Priority (Consider for future):**
- Nice-to-have features
- Advanced functionality
- Aesthetic improvements

## Technical Implementation Details (NEW)

### Current Architecture
```
User → Webflow (password protected) → iframe → Flask API → 
    ↓
    ├── Gemini Model (query processing)
    ├── Vector Store (retrieval)
    ├── Metrics Database (SQLite)
    └── PostHog (analytics)
```

### Metrics Collection Pipeline
```python
# Every query triggers:
1. Intent classification
2. Retrieval + generation
3. Metrics calculation:
   - Latency measurement
   - Groundedness scoring
   - Cost calculation
   - Citation validation
4. Database persistence
5. Dashboard update
```

### Dashboard Access Levels
- **Admin:** Full access, all metrics, drill-down
- **Tester:** View-only dashboard
- **Public:** No dashboard access (future: public metrics page)

## Deployment Stages & Timeline

### Stage 1: Internal Testing (Current - Sept 11-18)
- Password-protected Webflow page
- 6-10 testers from FutureTech
- Dashboard monitoring
- Daily bug fixes

### Stage 2: Canary Release (Sept 18-Oct 2, if gates pass)
- 5-10% traffic split
- A/B testing capability
- Broader user base
- Performance optimization

### Stage 3: Full Production (Oct 2+, if gates pass)
- 100% traffic
- Public announcement
- Continuous monitoring
- Regular updates

## Success Criteria

### For Stage 1 → Stage 2 Progression
✅ 6/10 deployment gates passing  
✅ 70% user satisfaction  
✅ Zero critical bugs  
✅ Median latency < 5 seconds  
✅ All testers complete sessions

### For Stage 2 → Stage 3 Progression
✅ 8/10 deployment gates passing  
✅ 80% user satisfaction  
✅ 20% ticket deflection demonstrated  
✅ Cost per query < $0.30  
✅ Stable performance under load

## Risk Mitigation

### Technical Risks
- **Mitigation:** Kill switch to disable generation
- **Fallback:** Return to search-only mode
- **Monitoring:** Real-time alerts on failures

### User Experience Risks
- **Mitigation:** Clear beta/testing labels
- **Feedback:** Multiple channels for reporting
- **Support:** Dedicated email for issues

### Cost Risks
- **Mitigation:** Per-query cost tracking
- **Alerts:** Budget threshold warnings
- **Controls:** Rate limiting if needed

## Contact & Resources

**Dashboard:** `http://localhost:8090/dashboard`  
**Documentation:** See `/user_testing_kit/` folder  
**Support:** davidct@mit.edu  
**PostHog:** Login via app.posthog.com  
**Repository:** github.com/[your-repo]

---

*This is a living document. Updates tracked in version control.*
*Last significant update: Added implementation status and deployment gates*