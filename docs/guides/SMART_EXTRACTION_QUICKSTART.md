# Smart Extraction Quick Start Guide 🚀

**Auto-discover data from ANY website without CSS selectors!**

---

## ✨ What is Smart Extraction?

Smart Extraction uses AI (LLM) to automatically:
- Analyze any web page
- Discover what data is available
- Extract it intelligently
- **No CSS selectors needed!**

---

## 🎯 How to Use (3 Simple Steps)

### Step 1: Go to Smart Extraction

1. Visit http://localhost:3001
2. Click the **"Smart Extraction"** button (with ✨ sparkles icon)

### Step 2: Enter URL + Instructions

**URL:** Paste any website URL
```
https://www.screener.in/company/TCS/consolidated/
```

**Instructions:** Describe what you want to extract
```
Extract company name, market cap, current price, PE ratio, and ROE
```

### Step 3: Generate & Extract

1. Click **"Auto-Generate Template"**
   - AI analyzes the page (takes 10-15 seconds)
   - Shows you what fields it found

2. Click **"Extract Data"**
   - Scrapes the data
   - Downloads as Excel/CSV/JSON

**That's it!** ✅

---

## 📝 Example Instructions

### E-commerce Product
```
Extract product name, price, brand, description, stock status, and customer rating
```

### News Article
```
Get article title, author, publication date, category, and article text
```

### Job Listing
```
Extract job title, company, location, salary range, and job description
```

### Financial Data
```
Get stock symbol, current price, day high/low, volume, market cap, and PE ratio
```

### Real Estate
```
Extract property address, price, bedrooms, bathrooms, square footage, and description
```

---

## ⚙️ Advanced Options

Click **"Show Advanced Options"** for:

- **LLM Provider:**
  - Ollama (local, free, works offline)
  - OpenAI (requires API key, more accurate)
  - Anthropic (requires API key, best for complex pages)

- **Max Fields:** Limit number of fields to extract (default: 15)

- **Output Format:**
  - Excel (.xlsx) - Best for most use cases
  - CSV (.csv) - Simple tabular data
  - JSON (.json) - For developers

---

## 🆚 When to Use Each Mode

| Mode | Use When | Speed | Requires |
|------|----------|-------|----------|
| **Smart Extraction** | First time on a site, any website | Slow (15-30s) | Just the URL |
| **Template Mapper** | You have Excel column names | Slow (15-30s) | Column list |
| **CSS Selector** | Regular scraping, known site | Fast (2-3s) | Preset template |

---

## 💡 Pro Tips

### Tip 1: Be Specific in Instructions
❌ Bad: "Extract data from this page"
✅ Good: "Extract product name, price, and availability status"

### Tip 2: Test with One Page First
- Start with a single URL
- Verify the extraction works
- Then batch process multiple URLs

### Tip 3: Save Successful Templates
After Smart Extraction works:
1. Note which fields it extracted
2. Create a CSS selector preset (see ADDING_NEW_PRESET_TEMPLATES.md)
3. Use preset for faster future extractions

### Tip 4: Choose the Right LLM
- **Ollama (qwen2.5:1.5b)** - Fast, good for simple pages
- **OpenAI (gpt-4)** - More reliable, better for complex pages
- **Anthropic (claude-3)** - Best for messy HTML, great accuracy

---

## 🐛 Troubleshooting

### "Template generation failed"
**Cause:** LLM couldn't understand the page structure
**Fix:**
- Try a different LLM provider
- Make instructions more specific
- Check if the page loads properly in browser

### "No data extracted"
**Cause:** Selectors didn't match page elements
**Fix:**
- Verify URL is accessible
- Check if page requires login
- Try with a different page from same site

### "Extraction timeout"
**Cause:** Page takes too long to load
**Fix:**
- Check your internet connection
- Try a simpler page
- Increase timeout in backend settings

---

## 📊 Example: Extract from Screener.in

1. **URL:**
   ```
   https://www.screener.in/company/TCS/consolidated/
   ```

2. **Instructions:**
   ```
   Extract company name, market cap, current price, stock PE, book value, ROE, and ROCE
   ```

3. **Expected Result:**
   ```
   Company Name: Tata Consultancy Services Ltd
   Market Cap: ₹13,45,678 Cr
   Current Price: ₹3,654
   Stock P/E: 28.5
   Book Value: ₹256
   ROE: 45.2%
   ROCE: 52.8%
   ```

---

## 🔄 Comparison: Smart vs. CSS Selector

### Same Screener.in extraction:

**Smart Extraction:**
```
Time: 15-30 seconds
Setup: Copy URL + Write instructions
Flexibility: Can change fields anytime
Best for: One-off or exploratory scraping
```

**CSS Selector (Preset):**
```
Time: 2-3 seconds
Setup: Use existing "Screener.in" preset
Flexibility: Fixed fields only
Best for: Regular, repeated scraping
```

**Recommendation:**
- First time? → Use Smart Extraction
- Regular scraping? → Create CSS preset

---

## 🚀 Next Steps

1. **Try it now:**
   - Go to http://localhost:3001
   - Click "Smart Extraction"
   - Paste a URL and test it!

2. **Read the full guide:**
   - `AUTO_TEMPLATE_GENERATION_GUIDE.md` - Auto-generate CSS templates
   - `ADDING_NEW_PRESET_TEMPLATES.md` - Create manual presets

3. **Check out Template Mapper:**
   - Similar to Smart Extraction
   - But you provide the column names
   - Great when you have an Excel template

---

**Happy Extracting!** ✨

Need help? Check the logs:
```bash
docker-compose logs -f backend
```
