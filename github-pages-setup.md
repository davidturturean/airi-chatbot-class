# 🚀 GitHub Pages Setup for Webflow Integration

## Step 1: Create GitHub Pages Branch
```bash
# Create orphan branch for GitHub Pages
git checkout --orphan gh-pages

# Remove all files from this branch
git rm -rf .

# Copy our webflow bundle
cp -r webflow-dist/* .

# Add deployment info
echo "# AIRI Chatbot - Webflow Integration Bundle" > README.md
echo "This branch hosts the embedded bundle for Webflow integration" >> README.md
echo "" >> README.md
echo "🌐 Live URL: https://davidturturean.github.io/airi-chatbot-class/" >> README.md
echo "📅 Last Updated: $(date)" >> README.md

# Stage and commit
git add .
git commit -m "🚀 Initial Webflow integration bundle"

# Push to GitHub
git push origin gh-pages
```

## Step 2: Enable GitHub Pages
1. Go to your repo on GitHub.com
2. Settings → Pages
3. Source: Deploy from branch
4. Branch: gh-pages
5. Folder: / (root)
6. Save

## Step 3: Get Your Embed URL
Your app will be available at:
**https://davidturturean.github.io/airi-chatbot-class/**

## Step 4: Test the Hosted Version
Visit the URL and verify:
- ✅ App loads correctly
- ✅ API calls work (check browser console)
- ✅ Chat functionality works
- ✅ No CORS errors

## Step 5: Webflow Integration Code
Add this to your Webflow page:

### Option A: Iframe Embed (Recommended)
```html
<iframe 
  src="https://davidturturean.github.io/airi-chatbot-class/"
  width="100%" 
  height="600" 
  frameborder="0"
  style="border: none; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
</iframe>
```

### Option B: Direct Script Include
```html
<div id="airi-chatbot-root"></div>
<script>
window.AIRI_CONFIG = {
  apiBaseUrl: 'https://airi-chatbot-class-production.up.railway.app',
  embeddedMode: true
};
</script>
<script src="https://davidturturean.github.io/airi-chatbot-class/api-patch.js"></script>
<link rel="stylesheet" href="https://davidturturean.github.io/airi-chatbot-class/assets/index-D8R_wQYv.css">
<script type="module" src="https://davidturturean.github.io/airi-chatbot-class/assets/index-RDKkp_mY.js"></script>
```

## 🎯 Success Metrics
- [ ] GitHub Pages URL loads the app
- [ ] Chat functionality works in embedded mode
- [ ] Railway backend API calls succeed
- [ ] No console errors
- [ ] Mobile responsive
- [ ] Ready for Webflow integration!