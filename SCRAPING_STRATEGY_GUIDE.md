# Web Scraping Strategy Guide

## Overview

The Enterprise RAG Chatbot supports multiple web scraping strategies to handle different types of websites. Understanding how these work will help you choose the right approach for your needs.

---

## Phase 2: Scraping Strategy & Configuration Explained

### What Phase 2 Does

Phase 2 controls **HOW** the content is extracted from web pages after Phase 1 handles compliance and access control.

### Available Scraping Strategies

#### 1. **Auto** (Recommended - Default)
- **Description**: Automatically selects the best strategy based on URL  patterns
- **How it works**:
  - Detects bot-protected sites (Wikipedia, LinkedIn) → Uses Hybrid with Playwright
  - Detects JavaScript-heavy sites (YouTube, Twitter) → Uses Playwright if enabled
  - Detects article sites (Medium, blogs, news) → Uses Trafilatura
  - Unknown sites → Uses Hybrid approach
- **Use when**: You want the system to intelligently choose the best method

#### 2. **Trafilatura**
- **Description**: Best for articles and blog posts
- **Strengths**:
  - Excellent content extraction from news articles
  - Removes boilerplate (navigation, ads, etc.) automatically
  - Fast and lightweight
- **Limitations**:
  - May fail on JavaScript-heavy sites
  - Can't handle dynamic content
- **Use when**: Scraping news articles, blogs, Medium posts

#### 3. **BeautifulSoup**
- **Description**: General purpose HTML parsing
- **Strengths**:
  - Works with any HTML
  - Good for structured data extraction
  - Customizable element removal
- **Limitations**:
  - Only processes static HTML (no JavaScript execution)
  - May include unwanted content without careful configuration
- **Use when**: Need general HTML parsing and CSS selector access

#### 4. **Playwright** ⚠️
- **Description**: For JavaScript-heavy sites (requires Playwright)
- **Strengths**:
  - **Executes JavaScript** - sees the page as a browser would
  - Bypasses bot detection (403 Forbidden errors)
  - Handles Single Page Applications (SPAs)
  - Can wait for specific elements to load
- **Limitations**:
  - **Much slower** (needs to launch browser)
  - **Higher resource usage** (CPU + memory)
  - Requires Playwright installation
- **Use when**:
  - Site returns 403 Forbidden errors
  - Content is loaded dynamically via JavaScript
  - Other strategies fail

#### 5. **Hybrid**
- **Description**: Tries multiple strategies in sequence (fallback chain)
- **How it works**:
  1. Tries Trafilatura first
  2. Falls back to BeautifulSoup if Trafilatura fails
  3. Falls back to Playwright as last resort
- **Use when**: Not sure which strategy will work, want maximum success rate

---

## Advanced Configuration Options

### Performance Settings

| Setting | Default | Description |
|---------|---------|-------------|
| **Timeout (seconds)** | 30 | How long to wait for page to load |
| **Max Retries** | 3 | Number of retry attempts on failure |
| **Min Content Length** | 100 | Minimum characters required for valid content |

### Content Options

| Option | What It Includes |
|--------|------------------|
| **Links** | Extracts all hyperlinks from the page |
| **Tables** | Includes table data |
| **Images** | Extracts image URLs |
| **Metadata** | Captures meta tags, titles, descriptions |

### Remove Elements

| Element | What It Removes |
|---------|----------------|
| **Navigation** | Nav menus, sidebars |
| **Footer** | Page footers |
| **Header** | Page headers |
| **Advertisements** | Ad containers |

### JavaScript Rendering (Playwright Only)

**Enable JavaScript Rendering** checkbox controls:
- Whether to use browser automation (Playwright)
- Only applies when strategy is set to "Playwright" or affects "Auto"/"Hybrid" fallback behavior

**Additional Options when enabled:**
- **Wait for selector**: CSS selector to wait for before extracting (e.g., `.article-content`)
- **Wait timeout**: Maximum time to wait for selector

---

## Does Enabling Playwright Break Basic Scraping?

### Short Answer: **NO** - It depends on the strategy selected

### Detailed Explanation:

#### Scenario 1: Strategy = "Auto" or "Hybrid"
```
enable_javascript = FALSE
URL: https://en.wikipedia.org/wiki/Tuticorin_Airport
```
**What happens:**
1. Auto detects Wikipedia → Uses Hybrid strategy
2. Hybrid tries Trafilatura first → **Likely fails with 403 Forbidden**
3. Hybrid tries BeautifulSoup → **Likely fails with 403 Forbidden**
4. Hybrid tries Playwright as fallback → **✅ SUCCEEDS**

```
enable_javascript = TRUE
URL: https://en.wikipedia.org/wiki/Tuticorin_Airport
```
**What happens:**
1. Auto detects Wikipedia → Uses Hybrid strategy
2. Same as above, Playwright still used as fallback and succeeds

**Result**: `enable_javascript` checkbox doesn't affect Wikipedia scraping much because Hybrid/Auto always includes Playwright as fallback for bot-protected sites.

#### Scenario 2: Strategy = "Trafilatura" or "BeautifulSoup"
```
enable_javascript = FALSE
Strategy: "Trafilatura"
URL: https://en.wikipedia.org/wiki/Tuticorin_Airport
```
**What happens:**
- Uses only Trafilatura
- **❌ FAILS** with 403 Forbidden (Wikipedia blocks simple HTTP clients)

#### Scenario 3: Strategy = "Playwright"
```
enable_javascript = TRUE
Strategy: "Playwright"
URL: https://en.wikipedia.org/wiki/Tuticorin_Airport
```
**What happens:**
- Uses browser automation
- **✅ SUCCEEDS** (bypasses bot detection)

### Wikipedia-Specific Behavior

Wikipedia is on the **bot-protected sites list** (see `scraper_strategies.py:504`):
```python
bot_protected_sites = ['wikipedia.org', 'wikimedia.org', 'linkedin.com']
```

When using "Auto" strategy, Wikipedia automatically gets assigned "Hybrid" which includes Playwright as a fallback, so it will always work eventually.

---

## Proposed Solution: Two Scrape Buttons

### Current UX Issue
Users must configure Phase 2 settings even for simple scraping, which is confusing.

### Recommended Implementation

#### **Button 1: Quick Scrape** (Phase 1 Only)
- **Location**: End of Phase 1 section
- **Label**: "Quick Scrape" or "Scrape Now (Basic)"
- **Behavior**:
  - Uses Phase 1 settings (compliance, LLM, auth)
  - Automatically uses "Auto" strategy
  - Skips Phase 2 configuration
  - Best for: Simple, one-click scraping

#### **Button 2: Advanced Scrape** (Phase 1 + Phase 2)
- **Location**: End of Phase 2 section (current position)
- **Label**: "Start Enterprise Scraping" (keep current)
- **Behavior**:
  - Uses both Phase 1 AND Phase 2 settings
  - Respects custom strategy selection
  - Respects advanced configuration
  - Best for: Fine-tuned control

### Mockup Structure

```
┌─────────────────────────────────────────┐
│ Phase 1: Compliance & Smart Scraping    │
│ [Compliance Level: Balanced]            │
│ [Enable LLM: ✓] [Provider: Ollama]     │
│ [Scraping Instructions: ...]           │
│                                         │
│ [Quick Scrape] ← NEW BUTTON             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Phase 2: Scraping Strategy (Optional)   │
│ [Strategy: Auto]                        │
│ [Show Advanced: ✓]                      │
│   • Timeout: 30s                        │
│   • Enable JavaScript: □                 │
│                                         │
│ [Start Enterprise Scraping] ← EXISTING  │
└─────────────────────────────────────────┘
```

---

## Best Practices

### For Simple Sites (Blogs, News, Static Pages)
- **Strategy**: Auto or Trafilatura
- **JavaScript**: Disabled
- **Why**: Faster, less resource-intensive

### For Bot-Protected Sites (Wikipedia, LinkedIn)
- **Strategy**: Auto or Hybrid
- **JavaScript**: Enabled or Disabled (Hybrid includes Playwright fallback)
- **Why**: Auto-detection handles it, or Hybrid ensures Playwright fallback

### For JavaScript-Heavy Sites (SPAs, React apps)
- **Strategy**: Playwright
- **JavaScript**: Enabled
- **Wait for selector**: Specify if needed (e.g., `.main-content`)
- **Why**: Only way to get dynamically loaded content

### For Unknown Sites
- **Strategy**: Hybrid or Auto
- **JavaScript**: Enabled
- **Why**: Maximizes success rate by trying multiple approaches

---

## Examples

### Example 1: Wikipedia Airport Page

**URL**: `https://en.wikipedia.org/wiki/Tuticorin_Airport`

**Recommended Settings:**
- **Strategy**: Auto (or Hybrid)
- **Compliance**: Balanced
- **JavaScript**: Can be disabled (Hybrid fallback handles it)

**Expected Flow:**
1. Auto detects Wikipedia → selects Hybrid
2. Trafilatura tries → Gets 403 Forbidden
3. BeautifulSoup tries → Gets 403 Forbidden
4. Playwright tries → ✅ **SUCCESS** (bypasses bot detection)

### Example 2: Medium Blog Post

**URL**: `https://medium.com/@author/article`

**Recommended Settings:**
- **Strategy**: Auto (or Trafilatura)
- **Compliance**: Balanced
- **JavaScript**: Disabled

**Expected Flow:**
1. Auto detects "medium.com" → selects Trafilatura
2. Trafilatura extracts clean article text → ✅ **SUCCESS**

### Example 3: Dynamic Product Page

**URL**: `https://shop.example.com/product/123`

**Recommended Settings:**
- **Strategy**: Playwright
- **JavaScript**: Enabled
- **Wait for selector**: `.product-details`
- **Wait timeout**: 10s

**Expected Flow:**
1. Playwright launches browser
2. Waits for `.product-details` to appear
3. Extracts rendered content → ✅ **SUCCESS**

---

## Common Issues & Solutions

### Issue: "Scraping failed with 403 Forbidden"
**Cause**: Website blocking simple HTTP requests
**Solution**: Use "Hybrid" or "Playwright" strategy

### Issue: "Insufficient content extracted"
**Cause**: Content is loaded via JavaScript
**Solution**: Enable JavaScript and use Playwright

### Issue: "Timeout error"
**Cause**: Page takes too long to load
**Solution**: Increase timeout in advanced settings

### Issue: "Too much boilerplate content"
**Cause**: Navigation, ads not being removed
**Solution**: Enable "Remove Elements" options in advanced settings

---

## Performance Comparison

| Strategy | Speed | Resource Usage | Success Rate |
|----------|-------|----------------|--------------|
| Trafilatura | ⚡⚡⚡ Fast | 💾 Low | 🎯 High (articles) |
| BeautifulSoup | ⚡⚡ Medium | 💾 Low | 🎯 Medium |
| Playwright | ⚡ Slow | 💾💾💾 High | 🎯🎯 Very High |
| Hybrid | ⚡⚡ Medium* | 💾💾 Medium* | 🎯🎯🎯 Highest |
| Auto | ⚡⚡ Medium* | 💾💾 Medium* | 🎯🎯 High |

*Depends on which strategy succeeds

---

## Summary

1. **Phase 2 doesn't "break" basic scraping** - it enhances it with more options
2. **"Enable JavaScript" checkbox** only affects Playwright strategy usage
3. **"Auto" and "Hybrid" strategies** already include smart fallbacks, including Playwright
4. **Wikipedia works fine** with default "Auto" strategy because it's detected as bot-protected
5. **Two scrape buttons** would improve UX:
   - Quick Scrape: One-click with smart defaults
   - Enterprise Scrape: Full control over strategy

---

## Next Steps

Would you like me to:
1. ✅ **Implement two scrape buttons** (Quick vs Enterprise)?
2. ✅ **Add strategy recommendations** based on URL in the UI?
3. ✅ **Create preset configurations** for common site types?

This would make the scraper more user-friendly while maintaining the power of advanced configurations!
