# Pre-Testing Checklist
## Final Verification Before User Testing

### ✅ COMPLETED ITEMS

#### System Infrastructure
- [x] Flask API server deployed on Railway
- [x] Webflow chatbot page live
- [x] Password protection enabled (MITai2024test)
- [x] Dashboard accessible at `/dashboard`
- [x] Session persistence working (widget → full page)
- [x] Citation modal functioning

#### Documentation
- [x] Testing guide created
- [x] Recording setup instructions
- [x] Survey questions defined (30 questions)
- [x] Access instructions ready
- [x] User testing kit complete

#### Technical Implementation
- [x] Widget code complete (1050+ lines)
- [x] Analytics service implemented
- [x] Session management API working
- [x] Misleading text removed from UI
- [x] Helpful tooltips added

---

### 📋 IMMEDIATE TASKS (Before Testing)

#### 1. Google Form Creation (15 minutes)
- [ ] Go to [forms.google.com](https://forms.google.com)
- [ ] Create new form following `google_form_instructions.md`
- [ ] Add all 30 questions with correct types
- [ ] Configure logic jumps for Q22 (error details)
- [ ] Set response collection settings
- [ ] Test form yourself
- [ ] Get shareable link
- [ ] Add link to access_instructions.md

#### 2. PostHog Integration (10 minutes)
- [ ] Open Webflow Site Settings
- [ ] Go to Custom Code → Head Code
- [ ] Copy entire content from `webflow_posthog_integration.html`
- [ ] Paste into Head Code section
- [ ] Save changes
- [ ] Publish site
- [ ] Test events are firing (check browser console)
- [ ] Verify in PostHog dashboard

#### 3. Communication Setup (20 minutes)
- [ ] Create tester list (6-10 people)
- [ ] Draft invitation email with:
  - [ ] Webflow URL
  - [ ] Password: MITai2024test
  - [ ] Google Form link
  - [ ] Testing guide link
  - [ ] Your contact: davidct@mit.edu
- [ ] Schedule testing slots
- [ ] Send calendar invites

---

### 🧪 TESTING VERIFICATION

#### Before First Tester
Run through this complete flow yourself:

1. **Access Check**
   - [ ] Visit Webflow site
   - [ ] Enter password
   - [ ] Chatbot loads properly
   - [ ] Widget opens/closes smoothly

2. **Functionality Test**
   - [ ] Submit test query
   - [ ] Response received < 5 seconds
   - [ ] Citations clickable
   - [ ] Modal shows snippet content
   - [ ] Full page button works
   - [ ] Session transfers correctly

3. **Analytics Verification**
   - [ ] Open browser console
   - [ ] See `[Chatbot Analytics]` messages
   - [ ] Events logging:
     - [ ] chatbot_page_viewed
     - [ ] query_submitted
     - [ ] response_received
     - [ ] citation_clicked
   - [ ] Check PostHog dashboard shows events

4. **Survey Test**
   - [ ] Complete Google Form yourself
   - [ ] Verify all questions work
   - [ ] Logic jumps function
   - [ ] Response recorded
   - [ ] Can download responses

---

### 📊 MONITORING DURING TESTING

#### Per Session
- [ ] Tester confirmed access
- [ ] Recording started (if applicable)
- [ ] Watch PostHog live events
- [ ] Note any errors immediately
- [ ] Check dashboard metrics

#### Real-Time Monitoring
Keep these open during testing:
1. **PostHog Events**: https://us.posthog.com → Events tab
2. **Railway Logs**: Check for API errors
3. **Browser Console**: Watch for JavaScript errors
4. **Email**: For tester questions

---

### 🚨 QUICK FIXES (If Issues Arise)

#### Chatbot Not Loading
```javascript
// Check console for errors
// Verify Railway is running
// Check password protection settings
```

#### PostHog Not Tracking
```javascript
// Verify in console: typeof posthog !== 'undefined'
// Check API key is correct
// Make sure code is in Head section
```

#### Form Not Working
```
// Check form sharing settings
// Verify email collection enabled
// Test in incognito mode
```

---

### 📝 DATA COLLECTION

#### After Each Session
- [ ] Confirm survey completed
- [ ] Check PostHog captured events
- [ ] Note any issues reported
- [ ] Thank tester via email

#### End of Testing Day
- [ ] Export Google Form responses
- [ ] Screenshot PostHog metrics
- [ ] Save any error logs
- [ ] Document lessons learned
- [ ] Plan improvements

---

### 📞 EMERGENCY CONTACTS

**Technical Issues**: davidct@mit.edu
**Railway Status**: Check Railway dashboard
**PostHog Support**: support@posthog.com
**Webflow Issues**: Check Webflow status page

---

## FINAL GO/NO-GO CHECKLIST

Must have ALL of these before starting:

### Critical Requirements
- [ ] Chatbot responding to queries ✓
- [ ] Password protection working ✓
- [ ] Google Form created and tested
- [ ] PostHog events tracking
- [ ] At least 6 testers confirmed
- [ ] Support person available during testing

### Nice to Have
- [ ] Recording software tested
- [ ] Backup communication channel
- [ ] Test data cleared from dashboard
- [ ] Team briefed on process

---

## POST-TESTING CHECKLIST

### Within 24 Hours
- [ ] All surveys collected
- [ ] PostHog data exported
- [ ] Issues documented
- [ ] Thank you emails sent

### Within 48 Hours
- [ ] Survey analysis complete
- [ ] Metrics summarized
- [ ] Priority improvements identified
- [ ] Report drafted

### Within 72 Hours
- [ ] Stakeholder report sent
- [ ] Go/no-go recommendation
- [ ] Next steps defined
- [ ] Team debriefed

---

*Last Updated: September 26, 2024*
*Coordinator: davidct@mit.edu*