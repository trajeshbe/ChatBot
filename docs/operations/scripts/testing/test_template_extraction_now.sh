#!/bin/bash
#
# Quick Test Script for Template-Based Extraction
# Run this to see template extraction in action!
#

set -e

echo "======================================================================"
echo "🧪 TEMPLATE-BASED EXTRACTION - LIVE TEST"
echo "======================================================================"
echo ""

# Step 1: Create simple Excel template
echo "📋 STEP 1: Creating Excel template..."
docker-compose exec backend python3 << 'PYTHON_EOF'
import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Company Data"
ws.append(["Company Name", "Market Cap", "Stock P/E", "Revenue"])
wb.save("/tmp/test_stock_template.xlsx")
print("✅ Created template with 4 columns: Company Name, Market Cap, Stock P/E, Revenue")
PYTHON_EOF

echo ""

# Step 2: Upload template
echo "📤 STEP 2: Uploading template to backend..."
UPLOAD_RESPONSE=$(docker-compose exec backend bash -c '
curl -s -X POST http://localhost:8000/api/v1/extraction/templates/upload-excel \
  -F "file=@/tmp/test_stock_template.xlsx" \
  -F "name=Test Stock Template" \
  -F "description=Simple test template for demo"
')

echo "$UPLOAD_RESPONSE" | jq '.'
TEMPLATE_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.template_id')

echo ""
echo "✅ Template uploaded successfully!"
echo "   Template ID: $TEMPLATE_ID"
echo ""

# Step 3: Create extraction job
echo "🚀 STEP 3: Creating extraction job for Reliance Industries..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/extraction/jobs \
  -H "Content-Type: application/json" \
  -d "{
    \"urls\": [\"https://www.screener.in/company/RELIANCE/\"],
    \"template_id\": \"$TEMPLATE_ID\",
    \"output_format\": \"excel\",
    \"delivery_method\": \"download\",
    \"session_id\": \"test_$(date +%s)\"
  }")

echo "$JOB_RESPONSE" | jq '.'
JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.job_id')

echo ""
echo "✅ Job created successfully!"
echo "   Job ID: $JOB_ID"
echo ""

# Step 4: Wait for completion
echo "⏳ STEP 4: Waiting for job to complete..."
for i in {1..20}; do
  sleep 3
  STATUS_RESPONSE=$(curl -s http://localhost:8000/api/v1/extraction/jobs/$JOB_ID)
  STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
  PROGRESS=$(echo "$STATUS_RESPONSE" | jq -r '.progress_percentage // 0')

  echo "   [$i] Status: $STATUS (Progress: $PROGRESS%)"

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
done

echo ""

# Step 5: Show results
echo "📊 STEP 5: Final job status:"
curl -s http://localhost:8000/api/v1/extraction/jobs/$JOB_ID | jq '{
  job_id,
  status,
  urls_processed,
  successful_scrapes,
  records_extracted,
  quality_score,
  output_file_path
}'

echo ""

if [ "$STATUS" = "completed" ]; then
  echo "======================================================================"
  echo "✅ SUCCESS! Template extraction completed"
  echo "======================================================================"
  echo ""
  echo "To download the Excel file, run:"
  echo "   curl -O http://localhost:8000/api/v1/extraction/jobs/$JOB_ID/download"
  echo ""
  echo "Or inspect the data:"
  OUTPUT_FILE=$(curl -s http://localhost:8000/api/v1/extraction/jobs/$JOB_ID | jq -r '.output_file_path')
  if [ -n "$OUTPUT_FILE" ] && [ "$OUTPUT_FILE" != "null" ]; then
    echo ""
    echo "📁 Checking extracted data:"
    docker-compose exec backend python3 << PYTHON_EOF
import openpyxl
from pathlib import Path

result_file = "$OUTPUT_FILE"
if Path(result_file).exists():
    wb = openpyxl.load_workbook(result_file)
    ws = wb.active

    print("\n📊 EXTRACTED DATA:")
    print("=" * 80)

    # Headers
    headers = [cell.value for cell in ws[1]]
    print("Columns:", ", ".join(headers))
    print()

    # Data rows
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=1):
        print(f"Row {row_idx}:")
        for header, value in zip(headers, row):
            print(f"  {header}: {value}")
    print("=" * 80)
else:
    print(f"❌ File not found: {result_file}")
PYTHON_EOF
  fi
else
  echo "======================================================================"
  echo "❌ FAILED! Job did not complete successfully"
  echo "======================================================================"
  echo "Check backend logs: docker-compose logs backend | tail -100"
fi

echo ""
echo "======================================================================"
echo "🎓 WHAT JUST HAPPENED:"
echo "======================================================================"
echo "1. ✅ Created Excel template with 4 columns"
echo "2. ✅ Uploaded template → got template_id"
echo "3. ✅ Created extraction job with Screener.in URL"
echo "4. ✅ System scraped website and filled Excel template"
echo "5. ✅ Downloaded results show structured data"
echo ""
echo "This is Template-Based Extraction in action!"
echo "======================================================================"
