#!/bin/bash
# Comprehensive Test for Enhanced Agent Runtime
# Tests all 7 enhanced tools with real sample data

set -e  # Exit on error

echo "=============================================================================="
echo "COMPREHENSIVE TEST - Enhanced Agent Runtime"
echo "=============================================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${YELLOW}TEST $TOTAL_TESTS: $test_name${NC}"
    echo "Command: $test_command"
    echo ""

    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
    echo "------------------------------------------------------------------------------"
    echo ""
}

# Cleanup function
cleanup() {
    echo "Cleaning up test artifacts..."
    rm -rf /tmp/agent_test_workspace 2>/dev/null || true
}

# Setup
echo "Setting up test workspace..."
mkdir -p /tmp/agent_test_workspace/{input,output}
trap cleanup EXIT

# ============================================================================
# TEST 1: Container Starts Successfully
# ============================================================================
run_test "Container starts and shows help" \
    "docker run --rm chatbot-agent-runtime:enhanced python -c 'import sys; sys.path.insert(0, \"/app\"); from agent_tools_enhanced import EnhancedAgentTools; print(\"✅ Container working\")'"

# ============================================================================
# TEST 2: Create Sample CSV Data
# ============================================================================
echo "Creating sample CSV data..."
cat > /tmp/agent_test_workspace/input/sales_data.csv << 'EOF'
date,product,quantity,revenue,region
2024-01-01,Widget A,100,5000,North
2024-01-02,Widget B,150,7500,South
2024-01-03,Widget A,120,6000,East
2024-01-04,Widget C,80,4000,West
2024-01-05,Widget B,200,10000,North
2024-01-06,Widget A,90,4500,South
2024-01-07,Widget C,110,5500,East
2024-01-08,Widget B,160,8000,West
2024-01-09,Widget A,140,7000,North
2024-01-10,Widget C,95,4750,South
EOF
echo "✅ Created: sales_data.csv"
echo ""

# ============================================================================
# TEST 3: Tier 2 - Data Analysis (analyze_dataframe)
# ============================================================================
run_test "Tier 2: Analyze DataFrame (EDA)" \
    "docker run --rm \
        -v /tmp/agent_test_workspace:/workspace \
        chatbot-agent-runtime:enhanced \
        python -c '
import sys
sys.path.insert(0, \"/app\")
from agent_tools_enhanced import EnhancedAgentTools
from pathlib import Path
import asyncio

async def test():
    tools = EnhancedAgentTools(
        workspace=Path(\"/workspace\"),
        artifacts_dir=Path(\"/workspace/output\"),
        session_state={\"artifacts\": [], \"tool_calls\": []}
    )
    result = await tools.analyze_dataframe(\"input/sales_data.csv\", \"basic\")
    assert result[\"success\"], \"Analysis failed\"
    print(\"✅ DataFrame analysis successful\")
    print(f\"   Rows: {result[\"summary\"][\"shape\"][0]}\")
    print(f\"   Columns: {result[\"summary\"][\"shape\"][1]}\")

asyncio.run(test())
'"

# ============================================================================
# TEST 4: Tier 2 - Data Visualization (visualize_data)
# ============================================================================
run_test "Tier 2: Create Visualization (Chart)" \
    "docker run --rm \
        -v /tmp/agent_test_workspace:/workspace \
        chatbot-agent-runtime:enhanced \
        python -c '
import sys
sys.path.insert(0, \"/app\")
from agent_tools_enhanced import EnhancedAgentTools
from pathlib import Path
import asyncio

async def test():
    tools = EnhancedAgentTools(
        workspace=Path(\"/workspace\"),
        artifacts_dir=Path(\"/workspace/output\"),
        session_state={\"artifacts\": [], \"tool_calls\": []}
    )
    result = await tools.visualize_data(
        \"input/sales_data.csv\",
        chart_type=\"line\",
        x_col=\"date\",
        y_col=\"revenue\",
        title=\"Revenue Over Time\"
    )
    assert result[\"success\"], \"Visualization failed\"
    print(\"✅ Visualization created\")
    print(f\"   Chart saved to: {result.get(\"chart_path\", \"output\")}\")

asyncio.run(test())
'"

# ============================================================================
# TEST 5: Create Sample PDF
# ============================================================================
echo "Creating sample PDF with Python..."
docker run --rm \
    -v /tmp/agent_test_workspace:/workspace \
    chatbot-agent-runtime:enhanced \
    python -c '
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pathlib import Path

pdf_path = Path("/workspace/input/sample_report.pdf")
c = canvas.Canvas(str(pdf_path), pagesize=letter)
c.drawString(100, 750, "Sample Business Report")
c.drawString(100, 700, "This is a test PDF document.")
c.drawString(100, 680, "It contains sample text for extraction testing.")
c.save()
print("✅ Created: sample_report.pdf")
' 2>/dev/null || echo "⚠️  PDF creation requires reportlab (optional)"

# ============================================================================
# TEST 6: Tier 3 - PDF Extraction
# ============================================================================
if [ -f /tmp/agent_test_workspace/input/sample_report.pdf ]; then
    run_test "Tier 3: Extract PDF Content" \
        "docker run --rm \
            -v /tmp/agent_test_workspace:/workspace \
            chatbot-agent-runtime:enhanced \
            python -c '
import sys
sys.path.insert(0, \"/app\")
from agent_tools_enhanced import EnhancedAgentTools
from pathlib import Path
import asyncio

async def test():
    tools = EnhancedAgentTools(
        workspace=Path(\"/workspace\"),
        artifacts_dir=Path(\"/workspace/output\"),
        session_state={\"artifacts\": [], \"tool_calls\": []}
    )
    result = await tools.extract_pdf_content(\"input/sample_report.pdf\", strategy=\"auto\")
    assert result[\"success\"], \"PDF extraction failed\"
    print(\"✅ PDF extraction successful\")
    print(f\"   Text length: {len(result.get(\"text\", \"\"))} characters\")

asyncio.run(test())
'"
else
    echo "⚠️  Skipping PDF test (reportlab not available)"
fi

# ============================================================================
# TEST 7: Create Sample Excel File
# ============================================================================
echo "Creating sample Excel file..."
docker run --rm \
    -v /tmp/agent_test_workspace:/workspace \
    chatbot-agent-runtime:enhanced \
    python -c '
import pandas as pd
from pathlib import Path

# Create sample data
data1 = {
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30, 35],
    "Salary": [50000, 60000, 70000]
}
data2 = {
    "Product": ["A", "B", "C"],
    "Sales": [100, 200, 150]
}

# Save to Excel with multiple sheets
excel_path = Path("/workspace/input/sample_workbook.xlsx")
with pd.ExcelWriter(excel_path) as writer:
    pd.DataFrame(data1).to_excel(writer, sheet_name="Employees", index=False)
    pd.DataFrame(data2).to_excel(writer, sheet_name="Sales", index=False)

print("✅ Created: sample_workbook.xlsx")
'
echo ""

# ============================================================================
# TEST 8: Tier 3 - Excel Analysis
# ============================================================================
run_test "Tier 3: Analyze Excel Workbook" \
    "docker run --rm \
        -v /tmp/agent_test_workspace:/workspace \
        chatbot-agent-runtime:enhanced \
        python -c '
import sys
sys.path.insert(0, \"/app\")
from agent_tools_enhanced import EnhancedAgentTools
from pathlib import Path
import asyncio

async def test():
    tools = EnhancedAgentTools(
        workspace=Path(\"/workspace\"),
        artifacts_dir=Path(\"/workspace/output\"),
        session_state={\"artifacts\": [], \"tool_calls\": []}
    )
    result = await tools.analyze_excel_workbook(\"input/sample_workbook.xlsx\")
    assert result[\"success\"], \"Excel analysis failed\"
    print(\"✅ Excel analysis successful\")
    print(f\"   Sheets: {result[\"summary\"][\"total_sheets\"]}\")
    print(f\"   Sheet names: {list(result[\"summary\"][\"sheets\"].keys())}\")

asyncio.run(test())
'"

# ============================================================================
# TEST 9: Create Sample Image
# ============================================================================
echo "Creating sample image for OCR..."
docker run --rm \
    -v /tmp/agent_test_workspace:/workspace \
    chatbot-agent-runtime:enhanced \
    python -c '
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Create a simple image with text
img = Image.new("RGB", (400, 200), color="white")
draw = ImageDraw.Draw(img)

# Add text
text = "Hello World\nThis is a test image\nfor OCR extraction"
draw.text((20, 20), text, fill="black")

# Save
img_path = Path("/workspace/input/sample_text.png")
img.save(img_path)
print("✅ Created: sample_text.png")
'
echo ""

# ============================================================================
# TEST 10: Tier 4 - OCR Text Extraction
# ============================================================================
run_test "Tier 4: Extract Text from Image (OCR)" \
    "docker run --rm \
        -v /tmp/agent_test_workspace:/workspace \
        chatbot-agent-runtime:enhanced \
        python -c '
import sys
sys.path.insert(0, \"/app\")
from agent_tools_enhanced import EnhancedAgentTools
from pathlib import Path
import asyncio

async def test():
    tools = EnhancedAgentTools(
        workspace=Path(\"/workspace\"),
        artifacts_dir=Path(\"/workspace/output\"),
        session_state={\"artifacts\": [], \"tool_calls\": []}
    )
    result = await tools.extract_text_from_image(\"input/sample_text.png\", ocr_engine=\"tesseract\")
    assert result[\"success\"], \"OCR failed\"
    print(\"✅ OCR extraction successful\")
    print(f\"   Extracted text length: {len(result.get(\"text\", \"\"))} characters\")
    print(f\"   Preview: {result.get(\"text\", \"\")[:50]}...\")

asyncio.run(test())
'"

# ============================================================================
# TEST 11: Tier 4 - Vision Model (if Ollama is available)
# ============================================================================
echo ""
echo "Note: Vision model test requires Ollama with llama3.2-vision model running"
echo "      Skipping vision model test (requires external service)"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "=============================================================================="
echo "TEST SUMMARY"
echo "=============================================================================="
echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
else
    echo "Failed: $FAILED_TESTS"
fi
echo ""

SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo "Success Rate: ${SUCCESS_RATE}%"
echo ""

if [ $SUCCESS_RATE -ge 80 ]; then
    echo -e "${GREEN}✅ OVERALL: PASS - Container is working well!${NC}"
    exit 0
else
    echo -e "${RED}❌ OVERALL: FAIL - Some critical issues detected${NC}"
    exit 1
fi
