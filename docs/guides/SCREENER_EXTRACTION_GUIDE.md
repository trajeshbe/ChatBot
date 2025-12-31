# Screener.in Data Extraction Guide

Complete guide for extracting financial data from screener.in company pages to Excel.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install playwright pandas beautifulsoup4 lxml openpyxl
playwright install chromium
```

### 2. Verify Setup

```bash
cd ../scripts/debugging
./test-screener-setup.sh
```

### 3. Extract Data

```bash
# Basic usage (auto-generates filename with timestamp)
./extract-screener.sh https://www.screener.in/company/BHARTIARTL/consolidated/

# Specify custom output filename
./extract-screener.sh https://www.screener.in/company/BHARTIARTL/consolidated/ bharti_airtel.xlsx
```

---

## 📊 What Gets Extracted

The tool extracts comprehensive financial data from screener.in and organizes it into multiple Excel sheets:

### Excel Workbook Structure

1. **Metadata Sheet**
   - Page title
   - URL
   - Extraction timestamp
   - Description

2. **Company Info Sheet**
   - Company name
   - Sector
   - Industry
   - Market cap
   - Stock price
   - 52-week high/low
   - Other company details

3. **Highlights Sheet**
   - Key financial ratios
   - Performance metrics
   - Valuation metrics
   - Quick overview numbers

4. **Financial Tables** (Multiple sheets)
   - Quarterly Results
   - Profit & Loss Statement
   - Balance Sheet
   - Cash Flow Statement
   - Ratios
   - Shareholding Pattern
   - Peer Comparison
   - And more...

---

## 💡 Usage Examples

### Example 1: Bharti Airtel
```bash
./extract-screener.sh https://www.screener.in/company/BHARTIARTL/consolidated/
```

Output:
- `screener_BHARTIARTL_20251116_143025.xlsx`
- `screener_BHARTIARTL_20251116_143025_debug.html`
- `screener_extraction.log`

### Example 2: TCS with Custom Filename
```bash
./extract-screener.sh https://www.screener.in/company/TCS/consolidated/ tcs_financials.xlsx
```

Output:
- `tcs_financials.xlsx`
- `tcs_financials_debug.html`
- `screener_extraction.log`

### Example 3: Multiple Companies (Batch Processing)
```bash
#!/bin/bash
# Extract data for multiple companies

companies=(
    "BHARTIARTL"
    "TCS"
    "RELIANCE"
    "INFY"
    "HDFCBANK"
)

for company in "${companies[@]}"; do
    echo "Extracting $company..."
    ./extract-screener.sh "https://www.screener.in/company/$company/consolidated/" "${company}_data.xlsx"
    sleep 2  # Polite delay between requests
done
```

---

## 🔍 Diagnostics and Troubleshooting

### Check Logs
```bash
# View extraction log
cat screener_extraction.log

# View last 50 lines
tail -50 screener_extraction.log

# View errors only
grep ERROR screener_extraction.log
```

### Debug HTML File
If extraction isn't working as expected:

1. Open the `*_debug.html` file in your browser
2. This shows the actual HTML content that was extracted
3. Use this to:
   - Verify the page loaded correctly
   - Check if JavaScript rendered properly
   - Identify missing elements
   - Understand page structure

### Common Issues

#### Issue: 403 Forbidden Error
```
Error: Failed to access URL after 3 attempts. The website may be blocking automated access.
```

**Solution:**
- The site may be blocking automation
- Try with a VPN or different IP
- Increase delay between requests
- Use the debug HTML to see if captcha appeared

#### Issue: Missing Tables
```
Warning: No tables found on page
```

**Solution:**
1. Check the debug HTML file
2. Verify the URL is correct
3. The page may have changed structure
4. Try with `headless=False` to see browser

#### Issue: Empty Excel File
```
Error: No data extracted
```

**Solution:**
1. Review `screener_extraction.log`
2. Check internet connection
3. Verify dependencies installed
4. Run `./test-screener-setup.sh`

#### Issue: Playwright Not Found
```
Error: Missing required package: playwright
```

**Solution:**
```bash
cd ../../backend
pip install playwright
playwright install chromium
```

---

## ⚙️ Advanced Usage

### Direct Python Script
```bash
# Use Python script directly for more control
python3 diagnose-screener-extraction.py <url> [output_file]

# Examples
python3 diagnose-screener-extraction.py https://www.screener.in/company/BHARTIARTL/consolidated/
python3 diagnose-screener-extraction.py https://www.screener.in/company/TCS/consolidated/ tcs.xlsx
```

### Customize Extraction
Edit `diagnose-screener-extraction.py` to customize:

```python
# Change browser settings (line 52)
self.browser = await playwright.chromium.launch(
    headless=False,  # Set to False to see browser
    slow_mo=100      # Slow down for debugging
)

# Adjust timeouts (line 125)
await self.page.wait_for_selector('table', timeout=30000)  # 30 seconds

# Change retry logic (line 109)
max_retries = 5  # Increase retries
```

---

## 📝 Output File Details

### Excel Formatting
- **Header Row**: Bold white text on blue background
- **Column Widths**: Auto-adjusted to content (max 50 characters)
- **Alignment**: Headers centered, data left-aligned
- **Sheet Names**: Sanitized and truncated to 31 characters

### File Naming
Auto-generated filenames follow this pattern:
```
screener_<COMPANY_CODE>_<YYYYMMDD>_<HHMMSS>.xlsx
```

Example:
```
screener_BHARTIARTL_20251116_143025.xlsx
```

### Log File Format
```
2025-11-16 14:30:25 - INFO - Starting scrape job for URL: https://...
2025-11-16 14:30:26 - INFO - Fetching URL (attempt 1/3): https://...
2025-11-16 14:30:30 - INFO - Fetched 125,456 bytes from URL
2025-11-16 14:30:30 - INFO - Found 8 tables
2025-11-16 14:30:31 - INFO - Successfully exported to screener_BHARTIARTL_20251116_143025.xlsx
```

---

## 🔒 Best Practices

### Rate Limiting
- Add delays between requests (2-5 seconds recommended)
- Don't overwhelm the server with rapid requests
- Use batch scripts with sleep delays

### Data Validation
- Always check the extracted Excel file
- Compare with source website to verify accuracy
- Review debug HTML if data looks incomplete

### File Organization
```bash
# Create organized directory structure
mkdir -p extracted_data/{bharti,tcs,reliance}

# Extract to organized folders
./extract-screener.sh https://www.screener.in/company/BHARTIARTL/consolidated/ \
    extracted_data/bharti/bharti_$(date +%Y%m%d).xlsx
```

### Automation
```bash
# Create cron job for daily extraction
# crontab -e
0 9 * * * cd /path/to/ChatBot/scripts/debugging && ./extract-screener.sh https://www.screener.in/company/BHARTIARTL/consolidated/ /path/to/output/bharti_$(date +\%Y\%m\%d).xlsx
```

---

## 🛠️ Integration with RAG System

You can use extracted Excel files with the RAG chatbot:

### 1. Upload to RAG System
```bash
# Upload Excel file via API
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@screener_BHARTIARTL_20251116_143025.xlsx"
```

### 2. Query Financial Data
```bash
# Query via API
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Bharti Airtel's revenue for Q3 2024?",
    "model": "gpt-4"
  }'
```

### 3. Use in Frontend
1. Open the chatbot frontend: http://localhost:3001
2. Upload the Excel file
3. Ask questions about the financial data

---

## 📊 Data Analysis Examples

Once you have the Excel file, you can:

### Python Analysis
```python
import pandas as pd

# Load Excel file
excel_file = 'screener_BHARTIARTL_20251116_143025.xlsx'

# Read company info
company_info = pd.read_excel(excel_file, sheet_name='Company Info')
print(company_info)

# Read financials
quarterly_results = pd.read_excel(excel_file, sheet_name='Quarterly Results')
print(quarterly_results)

# Calculate metrics
revenue_growth = quarterly_results['Revenue'].pct_change() * 100
print(f"Revenue growth: {revenue_growth.iloc[-1]:.2f}%")
```

### Excel Analysis
1. Open Excel file
2. Use pivot tables for analysis
3. Create charts and visualizations
4. Compare multiple companies

---

## 📚 Related Documentation

- **Main README**: [../README.md](../README.md)
- **Scripts README**: [../scripts/README.md](../scripts/README.md)
- **Debugging README**: [../scripts/debugging/README.md](../scripts/debugging/README.md)
- **CLAUDE.md**: [../CLAUDE.md](../CLAUDE.md)

---

## ❓ FAQ

### Q: Can I extract data from other pages on screener.in?
**A:** Yes! The tool works with any screener.in company page. Just change the URL.

### Q: Does this work with other financial websites?
**A:** Not by default. The script is customized for screener.in's structure. You can modify the Python script to support other sites.

### Q: How often should I extract data?
**A:** Financial data updates daily/quarterly. Extracting once per day or week is usually sufficient.

### Q: Can I extract historical data?
**A:** The tool extracts what's currently visible on the page. For historical data, you'd need to navigate to specific historical views or use screener.in's API (if available).

### Q: Is this legal?
**A:** Web scraping has legal gray areas. Always:
- Check the website's Terms of Service
- Respect robots.txt
- Use reasonable rate limiting
- For commercial use, consider official APIs or data providers

### Q: What if the page structure changes?
**A:** You'll need to update the parsing logic in `diagnose-screener-extraction.py`. The debug HTML file helps identify what changed.

---

## 🎯 Next Steps

1. ✅ Install dependencies
2. ✅ Run test setup script
3. ✅ Extract your first company
4. ✅ Review Excel output
5. ✅ Upload to RAG system
6. ✅ Query financial data

---

**Last Updated**: 2025-11-16
**Version**: 1.0.0
