# Webflow Password Protection Setup Guide

## Overview
This guide explains how to password-protect the AI Risk Repository Chatbot page on Webflow for Stage 1 (Internal Testing).

## Step-by-Step Instructions

### 1. Access Webflow Project Settings
1. Log in to Webflow account
2. Navigate to the AI Risk Repository project
3. Click on "Project Settings" in the left sidebar

### 2. Set Up Password Protection

#### Option A: Page-Level Protection (Recommended)
1. Navigate to the **Pages** panel
2. Find the chatbot page (`/chat` or `/chatbot`)
3. Click the gear icon (⚙️) next to the page name
4. Scroll to **Password Protection** section
5. Toggle "Password protect this page" to ON
6. Enter password: `MITai2024test`
7. Customize the password page message:
   ```
   AI Risk Repository Chatbot - Internal Testing
   
   This page is currently in testing phase with select users.
   Please enter the password provided by the research team.
   
   Contact: davidct@mit.edu for access
   ```
8. Click "Save Changes"

#### Option B: Site-Wide Protection (If Needed)
1. Go to **Project Settings** → **General** tab
2. Scroll to **Password Protection**
3. Enable "Password protect your site"
4. Set password: `MITai2024test`
5. Add allowed emails for team members (optional)

### 3. Create Custom Password Page (Optional)

1. In Pages panel, create new page: "Password"
2. Design a branded password entry page with:
   - MIT FutureTech logo
   - Brief explanation of testing phase
   - Password input field
   - Contact information
3. Set as password page in settings

### 4. Configure Analytics Tracking

Add tracking code to password-protected page:

```html
<!-- PostHog Tracking -->
<script>
  !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.async=!0,p.src=s.api_host+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled onFeatureFlags getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures getActiveMatchingSurveys getSurveys".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
  
  posthog.init('phx_pa5zpKS0q1DTprlpwAaInqlYFIqY2u8iWCKL2C4m2FF5S7M',{
    api_host:'https://app.posthog.com',
    capture_pageview: true,
    capture_pageleave: true
  });
  
  // Track password entry success
  posthog.capture('testing_access_granted', {
    page: 'chatbot',
    stage: 'internal_testing'
  });
</script>
```

### 5. Share Access Credentials

#### Create Access Document for Testers

**Email Template:**
```
Subject: AI Risk Repository Chatbot - Testing Access

Dear [Tester Name],

Thank you for participating in our internal testing phase for the AI Risk Repository Chatbot.

Access Information:
- URL: https://airisk.mit.edu/chat
- Password: MITai2024test
- Testing Period: [Date] to [Date]

Please refer to the attached testing guide for instructions.

Best regards,
MIT FutureTech Team
```

#### Track Who Has Access
Create a spreadsheet with:
- Tester name
- Email
- Organization
- Access granted date
- Testing session scheduled
- Feedback received (Y/N)

### 6. Test the Protection

1. Open incognito/private browser window
2. Navigate to the chatbot page
3. Verify password prompt appears
4. Test with correct password
5. Test with incorrect password
6. Verify analytics tracking works

### 7. Monitor Access

Check Webflow Analytics for:
- Number of password page views
- Successful entries
- Geographic distribution
- Time spent on protected page

### 8. Disable Protection After Testing

When moving to Stage 2 (Canary):
1. Return to page settings
2. Toggle password protection OFF
3. OR change to A/B testing setup for canary

## Security Considerations

- **Don't share password publicly** (social media, public docs)
- **Change password if compromised**
- **Use different passwords for each stage**
- **Consider IP allowlisting** for extra security (Enterprise plan)

## Alternative: Staging Domain

For maximum control, consider:
1. Create staging subdomain: `testing.airisk.mit.edu`
2. Deploy chatbot there with password
3. Keep main site unchanged
4. Move to main site after testing

## Troubleshooting

**Password not working:**
- Clear browser cache
- Check caps lock
- Verify no spaces before/after password

**Analytics not tracking:**
- Check PostHog API key is correct
- Verify script is in custom code section
- Test in PostHog dashboard

**Page still accessible without password:**
- Publish site after enabling protection
- Check if bypassing via direct iframe URL
- Verify protection is on correct page

## Support

- Technical issues: davidct@mit.edu
- Webflow access: pslat@mit.edu
- Testing coordination: skrigel@mit.edu