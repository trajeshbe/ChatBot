#!/bin/bash
# ==============================================================================
# Screener.in Data Extraction Script
# ==============================================================================
# Extract financial data from screener.in company pages and export to Excel
#
# Usage:
#   ./extract-screener.sh <url> [output_file]
#
# Examples:
#   ./extract-screener.sh https://www.screener.in/company/BHARTIARTL/consolidated/
#   ./extract-screener.sh https://www.screener.in/company/BHARTIARTL/consolidated/ bharti.xlsx
#   ./extract-screener.sh https://www.screener.in/company/TCS/consolidated/ tcs_data.xlsx
#
# Requirements:
#   - Python 3.11+
#   - pip install playwright pandas beautifulsoup4 lxml openpyxl
#   - playwright install chromium
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../../backend" && pwd)"

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🔍 Screener.in Data Extraction${NC}"
echo -e "${BLUE}=============================================================================${NC}"

# Check if URL is provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: URL is required${NC}"
    echo ""
    echo "Usage: $0 <url> [output_file]"
    echo ""
    echo "Examples:"
    echo "  $0 https://www.screener.in/company/BHARTIARTL/consolidated/"
    echo "  $0 https://www.screener.in/company/TCS/consolidated/ tcs_data.xlsx"
    exit 1
fi

URL="$1"
OUTPUT_FILE="${2:-}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Check if required packages are installed
echo -e "${YELLOW}📦 Checking dependencies...${NC}"

REQUIRED_PACKAGES=("playwright" "pandas" "beautifulsoup4" "openpyxl")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python3 -c "import $package" 2>/dev/null; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing required packages: ${MISSING_PACKAGES[*]}${NC}"
    echo ""
    echo "Install with:"
    echo "  cd $BACKEND_DIR"
    echo "  pip install playwright pandas beautifulsoup4 lxml openpyxl"
    echo "  playwright install chromium"
    exit 1
fi

echo -e "${GREEN}✅ All dependencies installed${NC}"

# Run extraction
echo -e "${BLUE}🚀 Starting extraction...${NC}"
echo ""

cd "$SCRIPT_DIR"

if [ -z "$OUTPUT_FILE" ]; then
    python3 diagnose-screener-extraction.py "$URL"
else
    python3 diagnose-screener-extraction.py "$URL" "$OUTPUT_FILE"
fi

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Extraction completed successfully!${NC}"
    echo ""
    echo "Output files created:"
    echo "  • Excel file: $(ls -t screener_*.xlsx 2>/dev/null | head -1 || echo "$OUTPUT_FILE")"
    echo "  • HTML debug: $(ls -t screener_*_debug.html 2>/dev/null | head -1)"
    echo "  • Log file: screener_extraction.log"
else
    echo ""
    echo -e "${RED}❌ Extraction failed. Check screener_extraction.log for details.${NC}"
fi

exit $EXIT_CODE
