# 📋 MANUAL UI TESTING GUIDE
## Comprehensive Test of All Extraction Features

### Prerequisites
1. Open browser: http://localhost:3001
2. Have OpenAI API key configured in .env

---

## TEST 1: Smart Extractor - Basic Extraction
**Goal**: Extract books from Mystery category

### Steps:
1. Click **"Data Extraction Hub"** tab (or navigate to extraction section)
2. Click **"Smart Extractor"** sub-tab
3. Fill in fields:
   - **URL**: `https://books.toscrape.com/catalogue/category/books/mystery_3/index.html`
   - **Instructions**: `Extract all mystery books with title, price, and availability`
4. Click **"Extract Data"** button
5. Wait for extraction (20-40 seconds)

### Expected Results:
- ✅ Table appears with ~32 mystery books
- ✅ Columns: title, price, availability
- ✅ All rows have data (no empty cells)

---

## TEST 2: Template Saving
**Goal**: Save extraction as reusable template

### Steps (continue from Test 1):
1. After extraction completes, look for **"Save as Template"** button
2. Click **"Save as Template"**
3. Modal/dialog appears
4. Fill in:
   - **Template Name**: `mystery_books_test`
   - **Display Name**: `Mystery Books Test`
5. Click **"Save"** button
6. Wait for success message

### Expected Results:
- ✅ Success message appears
- ✅ Template saved to database
- ✅ Template available for reuse

---

## TEST 3: CSS Selector Mode (with Template)
**Goal**: Use CSS selectors for fast extraction

### Steps:
1. Navigate to **"Template Extractor"** tab
2. Select **"CSS Selector"** mode/method
3. Fill in:
   - **URL**: `https://books.toscrape.com/catalogue/category/books/mystery_3/index.html`
   - **Template**: Select saved template from dropdown (if available)
   - OR manually define CSS selectors:
     - `title`: `h3 a` or `article h3 a`
     - `price`: `.price_color`
     - `availability`: `.availability`
4. Click **"Extract"** button

### Expected Results:
- ✅ Fast extraction (<5 seconds)
- ✅ Same data as Smart Extractor
- ✅ No LLM API calls needed

---

## TEST 4: Smart Template Mapper
**Goal**: Auto-map template to new URL

### Steps:
1. Navigate to **"Smart Template Mapper"** tab
2. Fill in:
   - **URL**: `https://books.toscrape.com/catalogue/category/books/thriller_37/index.html`
   - **Template**: Select saved template
3. Click **"Map & Extract"** button

### Expected Results:
- ✅ AI maps template fields to new page structure
- ✅ Extracts thriller books successfully
- ✅ Maintains same column structure

---

## TEST 5: AI-Powered Navigation
**Goal**: Navigate and extract from nested pages

### Steps:
1. Back to **"Smart Extractor"** tab
2. Fill in:
   - **URL**: `https://books.toscrape.com/`
   - **Instructions**: `Navigate to the Fantasy category and extract all fantasy books with title and price`
3. Click **"Extract Data"** button
4. Wait (may take 30-60 seconds for navigation)

### Expected Results:
- ✅ System automatically finds Fantasy link
- ✅ Clicks through to Fantasy category page
- ✅ Extracts ~19 fantasy books
- ✅ Shows navigation path in metadata

---

## TEST 6: Document Extraction (Bonus)
**Goal**: Extract from uploaded file

### Steps:
1. Create a test CSV or upload sample document
2. Navigate to Smart Extractor
3. Select **"Document"** source type (if available)
4. Upload file
5. Add extraction instructions
6. Click "Extract"

### Expected Results:
- ✅ File uploaded successfully
- ✅ Content extracted into table format
- ✅ Structured output

---

## VERIFICATION CHECKLIST

After completing all tests:

- [ ] Smart Extraction works (Test 1)
- [ ] Template saving works (Test 2)
- [ ] CSS Selector extraction works (Test 3)
- [ ] Template Mapper works (Test 4)
- [ ] AI Navigation works (Test 5)
- [ ] No JavaScript errors in browser console (F12 → Console tab)
- [ ] Backend logs show no errors
- [ ] All extracted data is accurate

---

## 🐛 TROUBLESHOOTING

### If extraction fails:
1. Check browser console (F12) for errors
2. Check backend logs: `docker-compose logs backend | tail -50`
3. Verify OpenAI API key is set
4. Try with simpler instructions

### If template saving fails:
1. Check network tab for API response
2. Verify backend `/api/v1/extract/save-template` endpoint
3. Check database connection

### If nothing appears:
1. Hard refresh browser (Ctrl+Shift+R)
2. Clear browser cache
3. Check if frontend is running: `docker-compose ps frontend`
4. Check frontend logs: `docker-compose logs frontend | tail -20`

---

## 📸 SCREENSHOT LOCATIONS

If you want to save evidence of tests:
- Test 1 results: Take screenshot of results table
- Test 2: Screenshot of save template dialog
- Test 5: Screenshot showing navigation path

