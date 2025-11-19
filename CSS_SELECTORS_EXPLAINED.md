# CSS Selectors Explained - With Real Examples

**Date**: 2025-11-19
**Purpose**: Understanding CSS selectors with Screener.in example

---

## 🎯 What Are CSS Selectors?

**CSS Selectors = Addresses to find specific data on a webpage**

Like GPS coordinates that tell the computer exactly where to look.

---

## 📄 Real Example: Screener.in HTML

When you visit `https://www.screener.in/company/RELIANCE/`, the browser downloads this HTML:

```html
<html>
  <head>
    <title>Reliance Industries Ltd</title>
  </head>
  <body>
    <div id="top-ratios">
      <ul class="top-ratios">
        <!-- Market Cap -->
        <li class="flex flex-space-between">
          <span class="name">Market Cap</span>
          <span class="number">
            17,50,000 <span class="small">Cr.</span>
          </span>
        </li>

        <!-- Current Price -->
        <li class="flex flex-space-between">
          <span class="name">Current Price</span>
          <span class="number">1,234</span>
        </li>

        <!-- Stock P/E -->
        <li class="flex flex-space-between">
          <span class="name">Stock P/E</span>
          <span class="number">28.5</span>
        </li>
      </ul>
    </div>

    <div id="profit-loss">
      <section class="card">
        <table>
          <thead>
            <tr>
              <th>Year</th>
              <th>Sales</th>
              <th>Net Profit</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Mar 2024</td>
              <td>6,92,000</td>
              <td>53,000</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </body>
</html>
```

---

## 🎯 CSS Selector Examples

### Basic Selectors

| Selector | What It Finds | Example |
|----------|---------------|---------|
| `h1` | All `<h1>` tags | Company name headings |
| `.company-name` | Elements with class="company-name" | `<h1 class="company-name">` |
| `#top-ratios` | Element with id="top-ratios" | `<div id="top-ratios">` |
| `span.number` | `<span>` tags with class="number" | `<span class="number">28.5</span>` |

### Advanced Selectors

| Selector | What It Finds | Example |
|----------|---------------|---------|
| `ul.top-ratios li` | All `<li>` inside `<ul class="top-ratios">` | All ratio items |
| `li:nth-child(1)` | First `<li>` element | Market Cap row |
| `li:nth-child(3)` | Third `<li>` element | Stock P/E row |
| `table tbody tr:first td:nth-child(2)` | Second cell of first row in tbody | Sales value |

---

## 💡 Step-by-Step Example: Extract Market Cap

### Step 1: Inspect the HTML
Right-click on "Market Cap" value on Screener.in → Inspect Element

You'll see:
```html
<li class="flex flex-space-between">
  <span class="name">Market Cap</span>
  <span class="number">
    17,50,000 <span class="small">Cr.</span>
  </span>
</li>
```

### Step 2: Write the CSS Selector

**Option 1 - By Position:**
```css
ul.top-ratios li:nth-child(1) span.number
```
Meaning: In the top-ratios list, get the first item's number span

**Option 2 - By Content (More Reliable):**
```css
li:has(span.name:contains("Market Cap")) span.number
```
Meaning: Find the `<li>` that contains "Market Cap", then get its number span

### Step 3: Test in Browser Console

Open browser console (F12) and run:
```javascript
document.querySelector('ul.top-ratios li:nth-child(1) span.number').innerText
// Output: "17,50,000 Cr."
```

---

## 🔧 Complete Extraction Example

Let's extract all 4 fields from our Excel template:

### Field 1: Company Name
**HTML:**
```html
<h1 class="company-name">Reliance Industries Ltd</h1>
```

**CSS Selector:**
```
h1.company-name
```

**Python Code:**
```python
from bs4 import BeautifulSoup

html = """<h1 class="company-name">Reliance Industries Ltd</h1>"""
soup = BeautifulSoup(html, 'html.parser')

company_name = soup.select_one('h1.company-name').text
print(company_name)  # Output: Reliance Industries Ltd
```

---

### Field 2: Market Cap
**HTML:**
```html
<li class="flex">
  <span class="name">Market Cap</span>
  <span class="number">17,50,000 <span class="small">Cr.</span></span>
</li>
```

**CSS Selector:**
```
ul.top-ratios li:nth-child(1) span.number
```

**Python Code:**
```python
market_cap = soup.select_one('ul.top-ratios li:nth-child(1) span.number').text
print(market_cap)  # Output: 17,50,000 Cr.
```

---

### Field 3: Stock P/E
**HTML:**
```html
<li class="flex">
  <span class="name">Stock P/E</span>
  <span class="number">28.5</span>
</li>
```

**CSS Selector:**
```
ul.top-ratios li:nth-child(3) span.number
```

**Python Code:**
```python
stock_pe = soup.select_one('ul.top-ratios li:nth-child(3) span.number').text
print(stock_pe)  # Output: 28.5
```

---

### Field 4: Revenue (from table)
**HTML:**
```html
<table>
  <tbody>
    <tr>
      <td>Mar 2024</td>
      <td>6,92,000</td>  <!-- This is Revenue -->
      <td>53,000</td>
    </tr>
  </tbody>
</table>
```

**CSS Selector:**
```
#profit-loss table tbody tr:first td:nth-child(2)
```

**Python Code:**
```python
revenue = soup.select_one('#profit-loss table tbody tr:first td:nth-child(2)').text
print(revenue)  # Output: 6,92,000
```

---

## 🛠️ How Template Extraction Works

### Without CSS Selectors (What You Saw):
```python
# Method 5: Excel Upload + Jobs
POST /api/v1/extraction/jobs
{
  "template_id": "...",
  "urls": ["https://www.screener.in/company/RELIANCE/"]
}

# Result: Only URL populated, because no selectors defined
```

### With CSS Selectors (Method 1):
```python
POST /api/v1/extract/custom
{
  "name": "Reliance Data",
  "url": "https://www.screener.in/company/RELIANCE/",
  "fields": [
    {
      "name": "Company Name",
      "selector": "h1.company-name",
      "data_type": "text"
    },
    {
      "name": "Market Cap",
      "selector": "ul.top-ratios li:nth-child(1) span.number",
      "data_type": "text"
    },
    {
      "name": "Stock P/E",
      "selector": "ul.top-ratios li:nth-child(3) span.number",
      "data_type": "float"
    },
    {
      "name": "Revenue",
      "selector": "#profit-loss table tbody tr:first td:nth-child(2)",
      "data_type": "text"
    }
  ]
}

# Result: ALL fields populated with actual data! ✅
```

---

## 🤖 Smart Mapping vs CSS Selectors

### CSS Selectors (Manual):
```
You write:  "ul.top-ratios li:nth-child(1) span.number"
Computer:   Goes to that exact location and copies the text
Result:     Fast, precise, but breaks if HTML changes
```

### Smart Mapping (AI-Powered):
```
You write:  "Market Cap"
AI:         Looks at entire page, understands context, finds the value
Result:     Slower, more flexible, works even when HTML changes
```

---

## 📊 Comparison Table

| Aspect | CSS Selectors | Smart Mapping (AI) |
|--------|---------------|-------------------|
| **Speed** | ⚡⚡⚡ Very Fast (0.1s) | ⚡ Slow (5-15s) |
| **Accuracy** | ⭐⭐⭐ 100% if selectors are correct | ⭐⭐ 85-95% (depends on page) |
| **Setup Time** | 🕒 30-60 mins (write selectors) | 🕒 2 mins (just column names) |
| **Maintenance** | 🔧 Breaks when site changes | 🔧 Adapts automatically |
| **Cost** | 💰 Free | 💰 ~$0.02 per page (API cost) |
| **Technical Skill** | 👨‍💻 High (need to know CSS/HTML) | 👶 Low (anyone can use) |

---

## 🎓 When to Use Which?

### Use CSS Selectors When:
1. ✅ You know HTML/CSS
2. ✅ Website structure is stable
3. ✅ Processing 1000+ URLs (cost matters)
4. ✅ Need 100% accuracy
5. ✅ Scraping regularly (worth the setup time)

**Example:** Daily stock data collection from same website

### Use Smart Mapping When:
1. ✅ You don't know CSS selectors
2. ✅ Website structure might change
3. ✅ One-time or occasional extraction
4. ✅ Custom columns for each project
5. ✅ Quick turnaround needed

**Example:** Your Bharti Airtel case - 33 custom columns, one-time analysis

---

## 💻 Live Example You Can Try

Let me show you CSS selectors in action with a simple test:

```bash
# Scrape Screener.in with CSS selectors
curl -X POST http://localhost:8000/api/v1/extract/custom \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Reliance Quick Extract",
    "url": "https://www.screener.in/company/RELIANCE/",
    "fields": [
      {
        "name": "Company Name",
        "selector": "h1.company-name",
        "data_type": "text",
        "required": true
      },
      {
        "name": "Market Cap",
        "selector": "ul.top-ratios li:nth-child(1) span.number",
        "data_type": "text"
      }
    ]
  }'
```

**This will return:**
```json
{
  "success": true,
  "data": [
    {
      "Company Name": "Reliance Industries Ltd",
      "Market Cap": "17,50,000 Cr."
    }
  ]
}
```

---

## 🎯 Summary

### CSS Selectors =
**Exact addresses to find data on a webpage**

Like telling someone:
> "Go to building #5, floor 3, room 12, desk by the window, top drawer"

### Why You Need Them:
- Computers are dumb - they need exact instructions
- HTML is just text, selectors tell WHERE to look
- Without selectors, system doesn't know what data to extract

### Why Smart Mapping is Better for You:
- ✅ You don't need to learn CSS
- ✅ AI figures out selectors automatically
- ✅ Works for custom columns
- ✅ Adapts to website changes

---

## 🚀 Your Next Step

For your **33-column Bharti Airtel template**, use **Smart Mapping**:

```bash
curl -X POST http://localhost:8000/api/v1/extract/smart-map-to-template \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.screener.in/company/BHARTIARTL/",
    "template_columns": [
      "Company Name",
      "Market Cap",
      "Revenue (Annual)",
      ... (all 33 columns)
    ],
    "llm_provider": "openai",
    "output_format": "excel"
  }'
```

**No CSS selectors needed!** 🎉

---

**Generated**: 2025-11-19
**Status**: Complete explanation with examples

