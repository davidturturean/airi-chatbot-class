# Deployment Gates Quick Reference Card

## The 10 Gates at a Glance

| # | Gate | What It Means | Target | Why It Matters |
|---|------|---------------|--------|----------------|
| 1 | **Groundedness** | Responses cite real sources | ≥95% | Trust & credibility |
| 2 | **Hallucination Rate** | Made-up information | ≤2% | Prevents misinformation |
| 3 | **Retrieval Hit Rate** | Finds relevant documents | ≥90% | Core functionality |
| 4 | **Median Latency** | Typical response time | ≤3s | User experience |
| 5 | **P95 Latency** | Slowest 5% of responses | ≤7s | Consistency |
| 6 | **Containment Rate** | Users get answer without help | ≥60% | Self-service success |
| 7 | **Satisfaction Score** | User happiness rating | ≥70% | User acceptance |
| 8 | **Cost per Query** | API and infrastructure costs | ≤$0.30 | Economic viability |
| 9 | **Safety Violations** | Harmful or inappropriate content | 0 | User protection |
| 10 | **Data Freshness** | Hours since content update | ≤24h | Current information |

## Understanding Each Gate

### 🎯 Gate 1: Groundedness (≥95%)
**What:** Percentage of response content that can be traced to source documents
**How measured:** Automated checking + manual sampling
**Example:** "AI poses privacy risks [RID-00234]" ✓ vs "AI will take over the world" ✗

### 🚫 Gate 2: Hallucination Rate (≤2%)
**What:** Inverse of groundedness - claims without valid sources
**How measured:** 100% - Groundedness score
**Example:** Making up statistics or events that don't exist in the repository

### 🔍 Gate 3: Retrieval Hit Rate (≥90%)
**What:** System finds relevant documents for user queries
**How measured:** % of queries where top-3 results contain answer
**Example:** Query about "privacy" returns privacy-related documents

### ⚡ Gate 4: Median Latency (≤3s)
**What:** The "middle" response time - half are faster, half are slower
**How measured:** Sort all response times, take middle value
**Example:** If times are [1s, 2s, 3s, 4s, 5s], median = 3s

### 📊 Gate 5: P95 Latency (≤7s)
**What:** 95% of responses are faster than this
**How measured:** Sort response times, take 95th percentile
**Example:** Only 1 in 20 responses can be slower than 7 seconds

### ✅ Gate 6: Containment Rate (≥60%)
**What:** Users find answer without needing human support
**How measured:** (Queries resolved / Total queries) × 100
**Example:** User asks question, gets answer, doesn't email support

### 😊 Gate 7: Satisfaction Score (≥70%)
**What:** User feedback rating (thumbs up/down or 1-10 scale)
**How measured:** Average of all feedback scores
**Example:** Post-query "Was this helpful?" responses

### 💰 Gate 8: Cost per Query (≤$0.30)
**What:** Total cost including API calls, compute, storage
**How measured:** Total costs / Number of queries
**Example:** Gemini API ($0.20) + Infrastructure ($0.05) = $0.25/query

### 🛡️ Gate 9: Safety Violations (0)
**What:** Harmful, biased, or inappropriate responses
**How measured:** Automated filters + user reports
**Example:** Personal attacks, dangerous advice, discriminatory content

### 🔄 Gate 10: Data Freshness (≤24h)
**What:** How recent is the information being served
**How measured:** Time since last content update
**Example:** New AI risks added to repository appear in chatbot within 24h

## Stage Requirements

### 🟡 Stage 1: Internal Testing
**Required:** 6/10 gates passing
**Focus:** Basic functionality and safety
**Critical gates:** Safety (9), Groundedness (1), Retrieval (3)

### 🟠 Stage 2: Canary Release  
**Required:** 8/10 gates passing
**Focus:** Performance and user satisfaction
**Critical gates:** All Stage 1 + Latency (4,5), Satisfaction (7)

### 🟢 Stage 3: Full Production
**Required:** 8-10/10 gates passing
**Focus:** Scale and economics
**Critical gates:** All Stage 2 + Cost (8), Containment (6)

## Quick Decision Guide

### ✅ GREEN LIGHT if:
- Required gates passing for stage
- No critical failures
- Positive trend over time
- Team consensus

### 🟨 YELLOW LIGHT if:
- 1-2 gates below threshold but improving
- Minor issues with clear fixes
- Need more data to decide

### 🔴 RED LIGHT if:
- Safety violations (Gate 9) > 0
- Groundedness (Gate 1) < 90%
- More than half gates failing
- Critical bug discovered

## How Gates Connect

```
User Trust
├── Groundedness (1)
├── Hallucination (2)
└── Safety (9)

Performance
├── Median Latency (4)
├── P95 Latency (5)
└── Retrieval Rate (3)

Business Value
├── Containment (6)
├── Satisfaction (7)
└── Cost (8)

Operations
└── Freshness (10)
```

## Common Issues & Solutions

| Gate Failing | Likely Cause | Quick Fix |
|--------------|--------------|-----------|
| Groundedness low | Prompt issues | Adjust prompts to emphasize citations |
| High latency | Complex queries | Optimize retrieval, add caching |
| Low satisfaction | Poor answers | Improve retrieval quality |
| High costs | Long responses | Limit response length |
| Low containment | Unclear scope | Better onboarding/examples |

## Monitoring Frequency

**During Testing:** Check daily
**During Canary:** Check 2x daily
**In Production:** Real-time alerts + daily review

## Dashboard Access

```
URL: http://localhost:8090/dashboard
Production: https://[your-app].railway.app/dashboard
```

Click any gate on dashboard for detailed breakdown!

---

**Remember:** Gates are guidelines, not absolute rules. Use judgment and context when making go/no-go decisions.

**Contact:** davidct@mit.edu for gate questions