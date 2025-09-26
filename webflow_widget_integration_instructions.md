# 🚀 Webflow Widget Integration - Quick Start Guide

## ⏱️ Total Time: 5 minutes

### Step 1: Copy the Widget Code (1 min)
1. Open `webflow_widget_ready.html`
2. Select ALL the code (Cmd+A / Ctrl+A)
3. Copy it (Cmd+C / Ctrl+C)

### Step 2: Add to Webflow (2 min)
1. Log into Webflow
2. Open your project: **AI Risk Repository**
3. Go to: **Site Settings** → **Custom Code** → **Footer Code**
4. Paste the entire code
5. Click **Save Changes**

### Step 3: Publish (1 min)
1. Click **Publish** button
2. Select your domain
3. Confirm publish

### Step 4: Test (1 min)
1. Visit: https://ai-risk-repository-601932-8fac479478ab1.webflow.io
2. Look for purple chat button in bottom-right corner
3. Click to open chatbot
4. Verify it loads your Railway chatbot

## ✅ Success Checklist

- [ ] Purple chat button appears on main pages
- [ ] NO button on /chatbot page (prevents duplication)
- [ ] Click opens chatbot overlay
- [ ] X button closes overlay
- [ ] Expand button works for fullscreen
- [ ] Works on mobile (test on phone)

## 🎯 What You Get

**Two Ways to Access Chatbot:**
1. **Existing "Chatbot" Tab** → Full page experience at `/chatbot`
2. **New Floating Widget** → Quick access from ANY page

## 🔧 Common Issues & Fixes

### Widget Not Appearing?
- Check you pasted in **Footer Code** (not Header)
- Make sure you **Published** after adding code
- Clear browser cache (Cmd+Shift+R / Ctrl+Shift+R)

### Chatbot Not Loading?
- Verify Railway app is running
- Check browser console for errors (F12)
- Try incognito/private browser window

### Widget Appears on /chatbot Page?
- The code already handles this - should auto-hide
- If still showing, check line 278 in the code

## 🎨 Quick Customizations

### Change Button Position
Find line 18-19 and change:
```css
bottom: 20px;  /* Change to: top: 20px */
right: 20px;   /* Change to: left: 20px */
```

### Change Colors
Find line 27 and replace gradient:
```css
background: linear-gradient(135deg, #YOUR_COLOR 0%, #YOUR_COLOR2 100%);
```

### Change Widget Size
Find lines 73-74:
```css
width: 400px;  /* Make wider/narrower */
height: 600px; /* Make taller/shorter */
```

## 📊 Analytics Tracking

The widget automatically tracks:
- Widget opens/closes
- Fullscreen toggles
- Session duration
- Page where opened

View in PostHog dashboard after adding PostHog code to site.

## 🚦 Password Protection Compatibility

The widget works perfectly with password-protected pages:
1. User enters password to access site
2. Widget appears after authentication
3. No additional password needed for widget

## 📱 Mobile Experience

On phones/tablets:
- Smaller button (better for thumbs)
- Widget expands to nearly full screen
- Smooth animations maintained
- Touch-optimized interface

## 💡 Pro Tips

1. **First-Time Visitors**: Notification badge appears after 5 seconds
2. **Return Visitors**: No notification badge (uses sessionStorage)
3. **Direct Link**: Add `?openchat=true` to any URL to auto-open widget
4. **Keyboard Users**: Full accessibility with aria-labels

## ⚠️ Important Notes

- Widget automatically hides on `/chatbot` page
- Uses your Railway deployment URL (already configured)
- PostHog tracking ready (if PostHog added to site)
- Works with password protection
- Mobile responsive out of the box

## 🆘 Need Help?

Contact: davidct@mit.edu

---

**Ready to go! Just copy, paste, publish. The widget is pre-configured for your deployment.**