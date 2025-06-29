#!/bin/bash

echo "🚀 AIRI Chatbot → Webflow Deployment Script"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
REPO_NAME="airi-chatbot-class"
GITHUB_USERNAME="davidturturean"  # Update this if different
WEBFLOW_BRANCH="gh-pages"

echo -e "${BLUE}📁 Setting up Webflow deployment...${NC}"

# Create webflow-dist directory
mkdir -p webflow-dist
cd webflow-dist

echo -e "${YELLOW}📋 Copying frontend assets...${NC}"

# Copy all frontend assets
cp -r ../frontend/* .

# Copy our enhanced webflow bundle
cp ../webflow-bundle.html index.html

echo -e "${YELLOW}🔧 Creating deployment bundle...${NC}"

# Create a simple bundle info file
cat > bundle-info.json << EOF
{
  "bundleName": "airi-chatbot-webflow",
  "version": "$(date +%Y%m%d-%H%M%S)",
  "apiBackend": "https://airi-chatbot-class-production.up.railway.app",
  "deployedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "githubUrl": "https://${GITHUB_USERNAME}.github.io/${REPO_NAME}/"
}
EOF

echo -e "${GREEN}✅ Webflow bundle created in webflow-dist/!${NC}"
echo ""
echo -e "${BLUE}📤 Next steps:${NC}"
echo "1. Commit these changes to git"
echo "2. Push to gh-pages branch for hosting"
echo "3. Use this URL in Webflow:"
echo -e "   ${YELLOW}https://${GITHUB_USERNAME}.github.io/${REPO_NAME}/${NC}"
echo ""
echo -e "${BLUE}🌐 Webflow Integration Code:${NC}"
echo "Add this to your Webflow page's custom code:"
echo ""
echo -e "${YELLOW}<script>"
echo "window.AIRI_CONFIG = {"
echo "  apiBaseUrl: 'https://airi-chatbot-class-production.up.railway.app',"
echo "  embeddedMode: true"
echo "};"
echo "</script>"
echo "<iframe"
echo "  src=\"https://${GITHUB_USERNAME}.github.io/${REPO_NAME}/\""
echo "  width=\"100%\""
echo "  height=\"600\""
echo "  frameborder=\"0\""
echo "  style=\"border: none; border-radius: 8px;\""
echo "></iframe>${NC}"

cd ..
echo ""
echo -e "${GREEN}🎉 Deployment bundle ready! Rock and roll! 🤘${NC}"