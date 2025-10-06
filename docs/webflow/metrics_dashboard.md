# Metrics Dashboard Access & Interpretation Guide

## Dashboard Access

### Current Development URL
```
http://localhost:8090/dashboard
```

### Production URL (After Deployment)
```
https://[your-railway-app].railway.app/dashboard
```

## Dashboard Overview

The metrics dashboard provides real-time visibility into the chatbot's performance across 10 deployment gates based on Running Lean methodology. All data shown is **100% real** - no mock or simulated data.

![Dashboard Overview](dashboard_screenshot_empty.png)
*Note: Dashboard will initially show "No data available" until testing begins*

## Main Sections

### 1. Deployment Gates Status (Top Section)

Shows all 10 gates with current status:

| Gate | What It Measures | Target | How It's Calculated |
|------|------------------|--------|---------------------|
| **Groundedness** | Response accuracy | ≥95% | % of responses with valid citations |
| **Hallucination Rate** | Made-up information | ≤2% | Inverse of groundedness |
| **Retrieval Hit Rate** | Finding relevant docs | ≥90% | % queries with good document matches |
| **Median Latency** | Typical response time | ≤3s | Middle value of all response times |
| **P95 Latency** | Worst-case response time | ≤7s | 95% of responses faster than this |
| **Containment Rate** | Self-service success | ≥60% | % queries resolved without escalation |
| **Satisfaction Score** | User happiness | ≥70% | Average of user feedback ratings |
| **Cost per Query** | Economic viability | ≤$0.30 | Total API costs / number of queries |
| **Safety Violations** | Harmful outputs | 0 | Count of flagged responses |
| **Data Freshness** | Update recency | ≤24h | Hours since last data update |

**Visual Indicators:**
- 🟢 Green border = Passing
- 🔴 Red border = Failing  
- ℹ️ Info icon = Click for explanation

**Interactivity:**
- **Click any gate** to see detailed breakdown
- Shows specific queries contributing to that metric
- Displays calculation methodology

### 2. Performance Metrics (Left Card)

**Median Latency**
- The "typical" response time
- Should be under 3000ms (3 seconds)
- Updates in real-time as queries are processed

**P95 Latency**
- The slowest 5% of responses
- Important for user experience consistency
- Target: under 7000ms (7 seconds)

### 3. Success Metrics (Middle Card)

**Success Rate**
- Percentage of queries completed without errors
- Calculated as: (1 - error_rate) × 100
- Should be above 95%

**Containment Rate**  
- Percentage of users who got their answer without needing human help
- Key metric for ROI demonstration
- Based on user feedback when available

### 4. Cost Metrics (Right Card)

**Cost per Query**
- Average cost including all API calls
- Critical for budget planning
- Should decrease as system optimizes

**Total Queries (24h)**
- Volume indicator
- Helps project scaling needs
- Resets daily

### 5. Charts Section

**Latency Trend (Left Chart)**
- Blue line: Median latency over time
- Purple line: P95 latency over time  
- Shows last 24 hours by default
- Helps identify performance patterns

**Query Volume (Right Chart)**
- Bar chart showing queries per hour
- Identifies peak usage times
- Useful for capacity planning

### 6. Recent Sessions (Bottom Left)

Shows last 20 user sessions:
- Session ID (anonymized)
- Number of queries in session
- Average latency for that session
- Timestamp

### 7. System Status (Bottom Right)

Replaces traditional alerts with actionable status:
- **No Data**: "Submit queries to see metrics"
- **Operational**: Shows gates passing ratio
- **Issues**: Specific problems identified

## How to Use During Testing

### Phase 1: Initial Testing (Empty State)

When you first access the dashboard:
1. You'll see "No data available" messages
2. Gates will show 0/10 passing
3. This is normal - metrics populate as testing begins

### Phase 2: Active Testing

As testers use the system:
1. Metrics update in real-time (30-second refresh)
2. Gates will start showing pass/fail status
3. Charts will build historical patterns
4. Click gates to see specific problem queries

### Phase 3: Analysis

After testing sessions:
1. Review which gates are failing and why
2. Click through to see specific examples
3. Export data for deeper analysis
4. Share screenshots in status reports

## Drill-Down Capability

Click any metric for details:

**Example: Clicking "Groundedness"**
```
Groundedness Details
━━━━━━━━━━━━━━━━━
Description: Percentage of response content backed by citations

Total Queries: 42
Passing (≥80% grounded): 38
Percentage: 90.5%

Recent Queries:
┌─────────────────────────────────────┐
│ Query: "What are AI risks?"         │
│ Groundedness: 95%                   │
│ Citations: 5                        │
│ Time: 2024-09-11 14:23:01          │
└─────────────────────────────────────┘
[More queries...]
```

## Monitoring Best Practices

### Daily Checks
1. Overall gates status (X/10 passing)
2. Any gates that dropped below threshold
3. Error rate trends
4. Cost tracking vs budget

### Weekly Review
1. User satisfaction trends
2. Most common failure patterns
3. Performance optimization opportunities
4. Capacity planning needs

### Before Go/No-Go Decisions
1. Screenshot current dashboard state
2. Export detailed metrics
3. Document any anomalies
4. Prepare trend analysis

## Common Issues & Solutions

**"No data available"**
- Normal before testing starts
- Run test queries to populate
- Check API connection if persists

**Gate showing red but seems fine**
- Click for details to understand calculation
- May need threshold adjustment
- Could indicate edge cases

**Latency spikes**
- Check time of day patterns
- May indicate API rate limiting
- Review query complexity

**Cost higher than expected**
- Click cost metric for breakdown
- Check for unusually long responses
- Review token usage patterns

## Access Permissions

| Role | Access Level | Features |
|------|--------------|----------|
| **Admin** | Full | View all, drill-down, export |
| **Tester** | Read | View metrics, drill-down |
| **Stakeholder** | Summary | High-level view only |

## Export Capabilities

Data can be exported for reporting:
1. Click "Export" button (when implemented)
2. Choose format: CSV, JSON, PDF
3. Select date range
4. Include in status reports

## Integration with Other Tools

**PostHog Analytics**
- User behavior tracking
- Conversion funnels
- A/B test results
- Complements dashboard metrics

**Railway Logs**
- Backend performance details
- Error stack traces
- API call debugging

**Webflow Analytics**  
- Page views and traffic sources
- User demographics
- Engagement metrics

## Support

**Dashboard not loading?**
- Check Flask server is running
- Verify `/dashboard` route exists
- Clear browser cache

**Metrics questions?**
- Technical: davidct@mit.edu
- Interpretation: pslat@mit.edu
- UI/UX: skrigel@mit.edu