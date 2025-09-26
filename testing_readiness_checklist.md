# Testing Readiness Checklist

## Pre-Testing Setup (Complete Before First Tester)

### Technical Infrastructure
- [ ] Flask API server running and accessible
- [ ] Webflow chatbot page live
- [ ] Password protection enabled on Webflow
- [ ] Dashboard accessible at `/dashboard`
- [ ] PostHog tracking code added to Webflow
- [ ] All API endpoints tested and working
- [ ] Database ready to collect metrics
- [ ] Citation links verified working

### Access & Credentials  
- [ ] Password set: `MITai2024test`
- [ ] Password protection tested in incognito mode
- [ ] Test user list finalized (6-10 people)
- [ ] Access instructions document ready
- [ ] Login credentials sent to testers

### Testing Materials
- [ ] Testing guide reviewed and finalized
- [ ] Recording setup instructions tested
- [ ] Survey questions loaded into Google Form
- [ ] Survey link generated and tested
- [ ] Upload location for recordings prepared
- [ ] All documents in `user_testing_kit/` folder

### Communication
- [ ] Testing schedule confirmed with all participants
- [ ] Calendar invites sent with all details
- [ ] Reminder emails scheduled
- [ ] Support contact (davidct@mit.edu) available
- [ ] Slack channel or communication method ready

### Analytics & Monitoring
- [ ] PostHog events verified firing correctly
- [ ] Dashboard showing "No data" state properly
- [ ] Metrics collection tested with sample query
- [ ] Error logging enabled and tested
- [ ] Performance monitoring active

## Day of Testing

### Morning Checks (Before First Session)
- [ ] API server health check passing
- [ ] Webflow site loading correctly
- [ ] Password protection working
- [ ] Dashboard accessible
- [ ] Support person available
- [ ] Backup contact designated

### Per Testing Session
- [ ] Tester has received credentials
- [ ] Tester confirmed recording capability
- [ ] Support available during session
- [ ] Monitor dashboard for errors
- [ ] Note any critical issues immediately

### End of Day
- [ ] All recordings received or upload confirmed
- [ ] Survey responses collected
- [ ] Critical issues documented
- [ ] Metrics dashboard checked
- [ ] Team debriefed on any problems

## Post-Testing

### Data Collection (Within 24 Hours)
- [ ] All recordings downloaded and backed up
- [ ] Survey responses exported
- [ ] Metrics data verified in database
- [ ] PostHog analytics reviewed
- [ ] Issues log compiled

### Analysis (Within 48 Hours)
- [ ] Recordings reviewed for key insights
- [ ] Survey responses analyzed
- [ ] Metrics dashboard screenshots taken
- [ ] Common themes identified
- [ ] Priority improvements listed

### Reporting (Within 72 Hours)
- [ ] Testing summary report created
- [ ] Go/No-Go recommendation prepared
- [ ] Key metrics documented
- [ ] Next steps defined
- [ ] Stakeholders informed

## Emergency Procedures

### If System Goes Down
1. [ ] Notify testers immediately
2. [ ] Provide alternative testing time
3. [ ] Document what caused outage
4. [ ] Fix and test before next session
5. [ ] Extend testing period if needed

### If Password Protection Fails
1. [ ] Temporarily disable page
2. [ ] Fix password protection
3. [ ] Generate new password if compromised
4. [ ] Notify only scheduled testers
5. [ ] Re-enable with new credentials

### If Major Bug Discovered
1. [ ] Document exact steps to reproduce
2. [ ] Determine if testing can continue
3. [ ] Notify upcoming testers if delayed
4. [ ] Hot-fix if possible
5. [ ] Note in testing results

## Quality Checks

### Before Marking "Ready"
- [ ] Tested full user journey yourself
- [ ] Another team member verified access
- [ ] All 4 specific test tasks completable
- [ ] Response time under 10 seconds
- [ ] Citations clickable and working

### Acceptable Issues (Don't Block Testing)
- Minor UI inconsistencies
- Occasional slow responses (>5s but <15s)
- Non-critical error messages
- Styling issues
- Feature requests

### Unacceptable Issues (Must Fix First)
- Complete failures/timeouts
- Password protection not working
- No responses to queries
- Security vulnerabilities
- Data not being collected

## Sign-off

### Testing Readiness Confirmed By:

**Technical Infrastructure**
- Name: ________________
- Date: ________________
- Signature: ________________

**Testing Materials**
- Name: ________________
- Date: ________________
- Signature: ________________

**Analytics & Monitoring**
- Name: ________________
- Date: ________________  
- Signature: ________________

## Quick Reference

### Key URLs
- Chatbot: `https://airisk.mit.edu/chat`
- Dashboard: `http://localhost:8090/dashboard`
- PostHog: `https://app.posthog.com`

### Key Contacts
- Technical: davidct@mit.edu
- UX: skrigel@mit.edu
- Project: pslat@mit.edu

### Key Credentials
- Password: `MITai2024test`
- PostHog API: `phx_pa5zpKS0q1DTprlpwAaInqlYFIqY2u8iWCKL2C4m2FF5S7M`

### Testing Window
- Dates: [To be scheduled]
- Duration: 1 week
- Sessions: 6-10 testers
- Session length: 45 minutes each

---

**Last Updated:** September 11, 2024
**Next Review:** Before testing begins