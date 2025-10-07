#!/bin/bash

# Interactive Reference Visualization System - Verification Script
# This script verifies that all components are properly installed and configured

echo "=========================================="
echo "Interactive Reference Visualization"
echo "System Verification"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0

# Function to check if file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $2 - FILE NOT FOUND: $1"
        ((FAILED++))
    fi
}

# Function to check if directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $2 - DIRECTORY NOT FOUND: $1"
        ((FAILED++))
    fi
}

echo "Checking Frontend Components..."
echo "================================"

# Frontend TypeScript/React files
check_file "frontend/src/types/document-preview.ts" "TypeScript interfaces"
check_file "frontend/src/utils/preview-cache.ts" "Preview cache utility"
check_file "frontend/src/components/preview/HoverPreview.tsx" "HoverPreview component"
check_file "frontend/src/components/preview/SlideoutPanel.tsx" "SlideoutPanel component"
check_file "frontend/src/components/preview/EnhancedSlideoutPanel.tsx" "EnhancedSlideoutPanel component"
check_file "frontend/src/components/preview/CitationLink.tsx" "CitationLink component"
check_file "frontend/src/components/preview/index.ts" "Preview exports"
check_file "frontend/src/components/viewers/ExcelViewer.tsx" "ExcelViewer component"
check_file "frontend/src/components/viewers/WordViewer.tsx" "WordViewer component"
check_file "frontend/src/components/gallery/CitationGallery.tsx" "CitationGallery component"
check_file "frontend/src/context/PanelContext.tsx" "PanelContext"
check_file "frontend/src/styles/preview-visualization.css" "Visualization CSS"
check_file "frontend/src/components/examples/InteractiveReferencesExample.tsx" "Example components"

echo ""
echo "Checking Backend Routes..."
echo "================================"

# Backend Python files
check_file "src/api/routes/document_preview.py" "Document preview route"
check_file "src/api/routes/excel_viewer.py" "Excel viewer route"
check_file "src/api/routes/word_viewer.py" "Word viewer route"
check_file "src/api/routes/gallery.py" "Gallery route"

echo ""
echo "Checking Dependencies..."
echo "================================"

# Check frontend dependencies
if [ -f "frontend/package.json" ]; then
    if grep -q "react-data-grid" frontend/package.json; then
        echo -e "${GREEN}✓${NC} react-data-grid installed"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} react-data-grid not found in package.json"
        ((FAILED++))
    fi

    if grep -q "mammoth" frontend/package.json; then
        echo -e "${GREEN}✓${NC} mammoth (frontend) installed"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} mammoth not found in package.json"
        ((FAILED++))
    fi

    if grep -q "@types/dompurify" frontend/package.json; then
        echo -e "${GREEN}✓${NC} @types/dompurify installed"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} @types/dompurify not found in package.json"
        ((FAILED++))
    fi
else
    echo -e "${RED}✗${NC} frontend/package.json not found"
    ((FAILED+=3))
fi

# Check backend dependencies
if [ -f "requirements.txt" ]; then
    if grep -q "mammoth" requirements.txt; then
        echo -e "${GREEN}✓${NC} mammoth (backend) in requirements.txt"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} mammoth not found in requirements.txt"
        ((FAILED++))
    fi

    if grep -q "bleach" requirements.txt; then
        echo -e "${GREEN}✓${NC} bleach in requirements.txt"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} bleach not found in requirements.txt"
        ((FAILED++))
    fi

    if grep -q "pandas" requirements.txt; then
        echo -e "${GREEN}✓${NC} pandas in requirements.txt"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} pandas not found in requirements.txt"
        ((FAILED++))
    fi

    if grep -q "openpyxl" requirements.txt; then
        echo -e "${GREEN}✓${NC} openpyxl in requirements.txt"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} openpyxl not found in requirements.txt"
        ((FAILED++))
    fi
else
    echo -e "${RED}✗${NC} requirements.txt not found"
    ((FAILED+=4))
fi

echo ""
echo "Checking Documentation..."
echo "================================"

check_file "docs/INTERACTIVE_REFERENCES_IMPLEMENTATION.md" "Implementation guide"
check_file "docs/INTERACTIVE_REFERENCES_README.md" "Quick start guide"
check_file "IMPLEMENTATION_SUMMARY.md" "Implementation summary"
check_file "QUICK_REFERENCE.md" "Quick reference"

echo ""
echo "Checking App Integration..."
echo "================================"

# Check if routes are registered in app.py
if [ -f "src/api/app.py" ]; then
    if grep -q "document_preview_bp" src/api/app.py; then
        echo -e "${GREEN}✓${NC} document_preview_bp registered"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} document_preview_bp not registered in app.py"
        ((FAILED++))
    fi

    if grep -q "excel_viewer_bp" src/api/app.py; then
        echo -e "${GREEN}✓${NC} excel_viewer_bp registered"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} excel_viewer_bp not registered in app.py"
        ((FAILED++))
    fi

    if grep -q "word_viewer_bp" src/api/app.py; then
        echo -e "${GREEN}✓${NC} word_viewer_bp registered"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} word_viewer_bp not registered in app.py"
        ((FAILED++))
    fi

    if grep -q "gallery_bp" src/api/app.py; then
        echo -e "${GREEN}✓${NC} gallery_bp registered"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} gallery_bp not registered in app.py"
        ((FAILED++))
    fi
else
    echo -e "${RED}✗${NC} src/api/app.py not found"
    ((FAILED+=4))
fi

echo ""
echo "=========================================="
echo "Verification Results"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Build frontend: cd frontend && npm run build"
    echo "2. Start backend: source .venv/bin/activate && python main.py"
    echo "3. Test endpoints (see QUICK_REFERENCE.md)"
    echo "4. Integrate into chat interface (see docs/)"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review the errors above.${NC}"
    exit 1
fi
