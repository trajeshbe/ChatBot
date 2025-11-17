#!/bin/bash
# ==============================================================================
# Test Screener Extraction Setup
# ==============================================================================
# Verify all dependencies are installed for screener extraction
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🧪 Testing Screener Extraction Setup${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# Check Python
echo -e "${YELLOW}📌 Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo ""

# Check required packages
echo -e "${YELLOW}📌 Checking Python packages...${NC}"

PACKAGES=("playwright" "pandas" "bs4" "lxml" "openpyxl")
ALL_INSTALLED=true

for package in "${PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        VERSION=$(python3 -c "import $package; print(getattr($package, '__version__', 'unknown'))" 2>/dev/null)
        echo -e "${GREEN}✅ $package ($VERSION)${NC}"
    else
        echo -e "${RED}❌ $package - NOT INSTALLED${NC}"
        ALL_INSTALLED=false
    fi
done
echo ""

if [ "$ALL_INSTALLED" = false ]; then
    echo -e "${RED}❌ Some packages are missing${NC}"
    echo ""
    echo "Install with:"
    echo "  cd ../../backend"
    echo "  pip install playwright pandas beautifulsoup4 lxml openpyxl"
    echo "  playwright install chromium"
    exit 1
fi

# Check Playwright browsers
echo -e "${YELLOW}📌 Checking Playwright browsers...${NC}"
if python3 -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); browser.close(); p.stop()" 2>/dev/null; then
    echo -e "${GREEN}✅ Chromium browser installed${NC}"
else
    echo -e "${RED}❌ Chromium browser not installed${NC}"
    echo ""
    echo "Install with:"
    echo "  playwright install chromium"
    exit 1
fi
echo ""

# Check script permissions
echo -e "${YELLOW}📌 Checking script permissions...${NC}"
if [ -x "extract-screener.sh" ]; then
    echo -e "${GREEN}✅ extract-screener.sh is executable${NC}"
else
    echo -e "${YELLOW}⚠️  extract-screener.sh is not executable${NC}"
    chmod +x extract-screener.sh
    echo -e "${GREEN}✅ Made extract-screener.sh executable${NC}"
fi

if [ -x "diagnose-screener-extraction.py" ]; then
    echo -e "${GREEN}✅ diagnose-screener-extraction.py is executable${NC}"
else
    echo -e "${YELLOW}⚠️  diagnose-screener-extraction.py is not executable${NC}"
    chmod +x diagnose-screener-extraction.py
    echo -e "${GREEN}✅ Made diagnose-screener-extraction.py executable${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${GREEN}✅ All checks passed!${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo "You can now use the screener extraction tool:"
echo ""
echo "  ${YELLOW}./extract-screener.sh https://www.screener.in/company/BHARTIARTL/consolidated/${NC}"
echo ""
echo "Or directly:"
echo ""
echo "  ${YELLOW}python3 diagnose-screener-extraction.py https://www.screener.in/company/BHARTIARTL/consolidated/${NC}"
echo ""
