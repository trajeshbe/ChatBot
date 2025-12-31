# Enhanced Web Scraper Guide

> **Version**: 2.0
> **Last Updated**: 2025-11-16
> **Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Configuration](#configuration)
5. [Scraping Strategies](#scraping-strategies)
6. [API Usage](#api-usage)
7. [Frontend Usage](#frontend-usage)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)
10. [Examples](#examples)

---

## Overview

The Enhanced Web Scraper provides a flexible, plugin-based architecture for extracting content from web pages with multiple scraping strategies, comprehensive configuration options, and AI-powered content filtering.

### What's New in v2.0

- **Plugin Architecture**: Multiple scraping strategies (Trafilatura, BeautifulSoup, Playwright, Hybrid, Auto)
- **Feature Flags**: Granular control over scraping capabilities
- **Smart Scraping**: AI-powered content filtering based on user prompts
- **Advanced Configuration**: Fine-tune extraction, filtering, and performance
- **Bulk Scraping**: Process multiple URLs efficiently with concurrency control
- **Enhanced UI**: Collapsible advanced settings with strategy selection

---

## Features

### Core Features

✅ **Multiple Scraping Strategies**
- Auto-detection of best strategy
- Article-optimized extraction (Trafilatura)
- General HTML parsing (BeautifulSoup)
- JavaScript rendering (Playwright)
- Hybrid fallback approach

✅ **Feature Flags**
- Enable/disable web scraping
- Optional Playwright for JavaScript sites
- AI-powered smart scraping

✅ **Comprehensive Configuration**
- Timeout and retry settings
- Content extraction options
- Element filtering (nav, header, footer)
- Quality thresholds
- Rate limiting

✅ **Smart Scraping (AI-Powered)**
- LLM-based content filtering
- Extract only relevant information
- Guided by user prompts

✅ **Bulk Operations**
- Process up to 50 URLs per request
- Automatic concurrency control
- Rate limiting and politeness

---

## Architecture

### Plugin-Based Design

```
┌─────────────────────────────────────────┐
│     Enhanced Scraper Service            │
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐  │
│  │  Scraper Strategy Factory         │  │
│  └───────────────┬───────────────────┘  │
│                  │                       │
│       ┌──────────┴──────────┐           │
│       │                     │           │
│  ┌────▼────┐         ┌─────▼─────┐     │
│  │  Auto   │         │  Hybrid   │     │
│  │Strategy │         │ Strategy  │     │
│  └────┬────┘         └─────┬─────┘     │
│       │                    │            │
│  ┌────▼────────────────────▼─────┐     │
│  │  Base Scraper Strategies:    │     │
│  │  - Trafilatura               │     │
│  │  - BeautifulSoup             │     │
│  │  - Playwright                │     │
│  └──────────────────────────────┘     │
└─────────────────────────────────────────┘
```

### Component Overview

| Component | Purpose | Location |
|-----------|---------|----------|
| **Scraper Strategies** | Plugin implementations | `backend/app/services/scraper_strategies.py` |
| **Enhanced Service** | Main scraping orchestration | `backend/app/services/scraper_service_enhanced.py` |
| **API Routes** | REST endpoints | `backend/app/api/routes/scraper_routes.py` |
| **Schemas** | Request/response models | `backend/app/schemas/scraper_schemas.py` |
| **Frontend Component** | Enhanced UI | `frontend/src/components/WebScraperEnhanced.tsx` |

---

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Feature Flags
ENABLE_WEB_SCRAPING=true              # Enable web scraping feature
ENABLE_PLAYWRIGHT_SCRAPING=false      # Enable JavaScript rendering (requires Playwright)
ENABLE_SMART_SCRAPING=true            # Enable AI-powered content filtering

# Scraping Strategy
SCRAPER_DEFAULT_STRATEGY=auto         # auto, trafilatura, beautifulsoup, playwright, hybrid
SCRAPER_TIMEOUT=30.0                  # Request timeout in seconds
SCRAPER_MAX_RETRIES=3                 # Maximum retry attempts
SCRAPER_FOLLOW_REDIRECTS=true         # Follow HTTP redirects
SCRAPER_USER_AGENT="Mozilla/5.0 ..."  # Custom user agent

# Content Extraction
SCRAPER_INCLUDE_LINKS=true            # Include links in content
SCRAPER_INCLUDE_TABLES=true           # Include tables
SCRAPER_INCLUDE_IMAGES=false          # Include image references
SCRAPER_INCLUDE_METADATA=true         # Include page metadata

# Content Filtering
SCRAPER_REMOVE_NAV=true               # Remove navigation elements
SCRAPER_REMOVE_FOOTER=true            # Remove footer elements
SCRAPER_REMOVE_HEADER=true            # Remove header elements
SCRAPER_REMOVE_ADS=true               # Remove advertisement elements

# JavaScript Rendering (Playwright)
SCRAPER_ENABLE_JAVASCRIPT=false       # Enable JS rendering
SCRAPER_WAIT_TIMEOUT=10.0             # Wait timeout for JS rendering

# Rate Limiting
SCRAPER_RESPECT_ROBOTS_TXT=true       # Respect robots.txt (future)
SCRAPER_DELAY_BETWEEN_REQUESTS=1.0    # Delay between requests (seconds)
SCRAPER_MAX_CONCURRENT_REQUESTS=5     # Max concurrent requests

# Content Quality
SCRAPER_MIN_CONTENT_LENGTH=100        # Minimum content length (characters)
SCRAPER_MAX_CONTENT_LENGTH=1000000    # Maximum content length (1MB)

# Smart Scraping
SMART_SCRAPE_MODEL=gpt-3.5-turbo      # Model for content filtering
SMART_SCRAPE_MAX_TOKENS=2000          # Max tokens for filtered content
```

---

## Scraping Strategies

### 1. Auto Strategy (Default)

**Best for**: Unknown or mixed content types

**How it works**:
- Analyzes URL patterns
- Selects optimal strategy automatically
- Falls back to hybrid if uncertain

**URL Patterns**:
```python
# JavaScript-heavy sites → Playwright (if enabled)
- youtube.com, twitter.com, facebook.com

# Articles/blogs → Trafilatura
- medium.com, blog.*, *blog*, *article*, *news*

# Unknown → Hybrid
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/scraper/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://blog.example.com/article",
    "strategy": "auto"
  }'
```

### 2. Trafilatura Strategy

**Best for**: Articles, blog posts, news sites

**Strengths**:
- Excellent article extraction
- Removes boilerplate content
- Preserves structure

**Weaknesses**:
- Not suitable for structured data
- May miss non-article content

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/scraper/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://medium.com/article",
    "strategy": "trafilatura"
  }'
```

### 3. BeautifulSoup Strategy

**Best for**: General HTML parsing, structured content

**Strengths**:
- Works on any HTML
- Flexible filtering
- Fast and reliable

**Weaknesses**:
- May include unwanted content
- Requires configuration for best results

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/scraper/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/page",
    "strategy": "beautifulsoup",
    "config": {
      "remove_nav": true,
      "remove_footer": true
    }
  }'
```

### 4. Playwright Strategy

**Best for**: JavaScript-heavy sites, SPAs

**Requirements**:
- Playwright installed: `pip install playwright`
- Browser binaries: `playwright install chromium`
- `ENABLE_PLAYWRIGHT_SCRAPING=true`

**Strengths**:
- Executes JavaScript
- Waits for dynamic content
- Screenshots possible

**Weaknesses**:
- Slower (launches browser)
- Higher resource usage
- Requires additional setup

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/scraper/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://react-app.example.com",
    "strategy": "playwright",
    "config": {
      "enable_javascript": true,
      "wait_for_selector": ".main-content"
    }
  }'
```

### 5. Hybrid Strategy

**Best for**: Unreliable or diverse content

**How it works**:
1. Try Trafilatura first
2. If insufficient content, try BeautifulSoup
3. If JS enabled, try Playwright last
4. Return first successful result

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/scraper/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://complex-site.com",
    "strategy": "hybrid"
  }'
```

---

## API Usage

### Get Scraper Capabilities

**Endpoint**: `GET /api/v1/scraper/capabilities`

**Response**:
```json
{
  "web_scraping_enabled": true,
  "playwright_enabled": false,
  "smart_scraping_enabled": true,
  "available_strategies": ["auto", "trafilatura", "beautifulsoup", "hybrid"],
  "default_strategy": "auto",
  "max_concurrent_requests": 5,
  "configuration": {
    "timeout": 30.0,
    "max_retries": 3,
    "min_content_length": 100,
    "javascript_enabled": false
  }
}
```

### Scrape Single URL

**Endpoint**: `POST /api/v1/scraper/scrape`

**Request**:
```json
{
  "url": "https://example.com/article",
  "scrape_prompt": "Extract information about AI",
  "strategy": "auto",
  "config": {
    "timeout": 60,
    "include_tables": true,
    "remove_nav": true
  },
  "session_id": "session_123"
}
```

**Response**:
```json
{
  "success": true,
  "job_id": "job_abc123",
  "document_id": "doc_def456",
  "title": "Article About AI",
  "content_length": 5000,
  "url": "https://example.com/article",
  "strategy_used": "auto(trafilatura)",
  "metadata": {
    "description": "Article description",
    "keywords": "AI, machine learning"
  }
}
```

### Scrape Multiple URLs (Bulk)

**Endpoint**: `POST /api/v1/scraper/scrape/bulk`

**Request**:
```json
{
  "urls": [
    "https://example.com/article1",
    "https://example.com/article2"
  ],
  "scrape_prompt": "Extract product information",
  "strategy": "auto",
  "session_id": "session_123"
}
```

**Response**:
```json
{
  "results": [
    {
      "success": true,
      "document_id": "doc_1",
      "url": "https://example.com/article1",
      "content_length": 3000
    },
    {
      "success": false,
      "url": "https://example.com/article2",
      "error": "Connection timeout"
    }
  ],
  "total": 2,
  "successful": 1,
  "failed": 1
}
```

### Get Scrape Job Status

**Endpoint**: `GET /api/v1/scraper/jobs/{job_id}`

**Response**:
```json
{
  "job_id": "job_abc123",
  "url": "https://example.com/article",
  "status": "completed",
  "document_id": "doc_def456",
  "created_at": "2025-11-16T12:00:00Z",
  "completed_at": "2025-11-16T12:00:05Z"
}
```

---

## Frontend Usage

### Using Enhanced Web Scraper Component

```tsx
import WebScraperEnhanced from '@/components/WebScraperEnhanced'

function App() {
  return <WebScraperEnhanced />
}
```

### Features

1. **Multiple URL Input**: Add multiple URLs with + button
2. **Strategy Selection**: Choose scraping strategy from dropdown
3. **Advanced Settings**: Collapsible panel with all options
4. **Smart Prompts**: AI-guided content extraction
5. **Bulk Processing**: Efficient concurrent scraping
6. **Job Tracking**: Real-time status updates

---

## Advanced Features

### Smart Scraping (AI-Powered)

When `ENABLE_SMART_SCRAPING=true` and a `scrape_prompt` is provided:

1. Content is scraped normally
2. LLM filters content based on prompt
3. Only relevant portions are kept
4. Reduces noise and improves quality

**Example**:
```json
{
  "url": "https://long-article.com",
  "scrape_prompt": "Extract only information about pricing and features",
  "strategy": "auto"
}
```

**How it works**:
```python
# System prompt
"Extract and return only the most relevant portions of the content
based on the user's specific information need."

# User prompt
"User is looking for: {scrape_prompt}

Raw content: {scraped_content}

Extract only the relevant portions:"
```

### Custom Configuration

Override any default setting per request:

```json
{
  "url": "https://example.com",
  "config": {
    "strategy": "beautifulsoup",
    "timeout": 120,
    "max_retries": 5,
    "include_links": false,
    "include_tables": true,
    "include_images": true,
    "remove_nav": true,
    "remove_header": true,
    "remove_footer": true,
    "enable_javascript": false,
    "min_content_length": 500,
    "max_content_length": 50000
  }
}
```

### Rate Limiting

Protect scraped sites with built-in rate limiting:

```python
# Settings
SCRAPER_DELAY_BETWEEN_REQUESTS = 1.0  # 1 second delay
SCRAPER_MAX_CONCURRENT_REQUESTS = 5   # Max 5 concurrent

# Automatic in bulk scraping
results = await enhanced_scraper_service.scrape_multiple_urls(urls)
```

---

## Troubleshooting

### Web Scraping Disabled

**Error**: `Web scraping is disabled`

**Solution**:
```bash
# Set in .env
ENABLE_WEB_SCRAPING=true
```

### Playwright Not Available

**Error**: `Playwright not installed`

**Solution**:
```bash
# Install Playwright
pip install playwright
playwright install chromium

# Enable in .env
ENABLE_PLAYWRIGHT_SCRAPING=true
```

### Insufficient Content Extracted

**Error**: `Insufficient content extracted`

**Solutions**:
1. Lower `min_content_length` threshold
2. Try different strategy (hybrid or beautifulsoup)
3. Enable JavaScript rendering for dynamic sites
4. Check if site blocks scrapers (user agent)

### Connection Timeout

**Error**: `Connection timeout`

**Solutions**:
1. Increase `timeout` setting
2. Increase `max_retries`
3. Check internet connectivity
4. Verify URL is accessible

### All Strategies Failed

**Error**: `All strategies failed`

**Solutions**:
1. Check if site requires authentication
2. Verify site doesn't block bots
3. Try with JavaScript enabled
4. Inspect site structure manually

---

## Examples

### Example 1: Basic Article Scraping

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/v1/scraper/scrape",
    json={
        "url": "https://blog.example.com/ai-article",
        "strategy": "auto"
    }
)

result = response.json()
print(f"Scraped: {result['title']}")
print(f"Content length: {result['content_length']}")
```

### Example 2: Smart Scraping with Prompt

```python
response = httpx.post(
    "http://localhost:8000/api/v1/scraper/scrape",
    json={
        "url": "https://product-page.com",
        "scrape_prompt": "Extract pricing, features, and customer reviews",
        "strategy": "auto"
    }
)
```

### Example 3: Bulk Scraping with Custom Config

```python
response = httpx.post(
    "http://localhost:8000/api/v1/scraper/scrape/bulk",
    json={
        "urls": [
            "https://news.com/article1",
            "https://news.com/article2",
            "https://news.com/article3"
        ],
        "strategy": "trafilatura",
        "config": {
            "timeout": 60,
            "include_tables": true,
            "remove_nav": true
        },
        "session_id": "my_session"
    }
)

results = response.json()
print(f"Successful: {results['successful']}/{results['total']}")
```

### Example 4: JavaScript Site Scraping

```python
response = httpx.post(
    "http://localhost:8000/api/v1/scraper/scrape",
    json={
        "url": "https://react-app.com",
        "strategy": "playwright",
        "config": {
            "enable_javascript": true,
            "wait_for_selector": ".content-loaded",
            "wait_timeout": 15
        }
    }
)
```

---

## Best Practices

### 1. Choose the Right Strategy

- **Articles/Blogs**: Use `trafilatura` or `auto`
- **General Pages**: Use `beautifulsoup`
- **JavaScript Sites**: Use `playwright` (with JS enabled)
- **Unknown/Mixed**: Use `hybrid` or `auto`

### 2. Optimize Performance

- Use bulk scraping for multiple URLs
- Set reasonable timeouts
- Don't enable JavaScript unless needed
- Use rate limiting for large batches

### 3. Respect Websites

- Add delays between requests
- Use descriptive user agent
- Respect robots.txt (future feature)
- Don't scrape excessively

### 4. Use Smart Scraping

- Provide clear, specific prompts
- Use for filtering, not primary extraction
- Fallback to raw content if LLM fails

### 5. Handle Errors Gracefully

- Always check `success` field
- Log failed jobs for retry
- Use hybrid strategy for unreliable sites

---

## Migration from Basic Scraper

### Old Endpoint (Still Supported)

```python
# POST /api/v1/scrape
FormData:
  url: "https://example.com"
  scrape_prompt: "optional prompt"
```

### New Enhanced Endpoint

```python
# POST /api/v1/scraper/scrape
JSON:
  {
    "url": "https://example.com",
    "scrape_prompt": "optional prompt",
    "strategy": "auto",
    "config": {...}
  }
```

### Migration Steps

1. Update API endpoint path
2. Change from FormData to JSON
3. Add strategy selection (optional)
4. Configure advanced options (optional)
5. Update response handling (same structure)

---

## FAQ

**Q: Which strategy should I use?**
A: Start with `auto`. It intelligently selects the best strategy for each URL.

**Q: How do I scrape JavaScript-heavy sites?**
A: Enable Playwright and use `strategy: "playwright"` with `enable_javascript: true`.

**Q: Can I scrape authenticated pages?**
A: Not yet. This feature is planned for a future release.

**Q: What's the maximum number of URLs in bulk scraping?**
A: 50 URLs per request to prevent abuse and ensure responsiveness.

**Q: How does smart scraping work?**
A: An LLM filters the scraped content based on your prompt, keeping only relevant information.

**Q: Is web scraping legal?**
A: It depends on the website's terms of service and your jurisdiction. Always check before scraping.

---

## Support

For issues or questions:

1. Check this guide
2. Review [Troubleshooting](#troubleshooting)
3. Check server logs: `docker-compose logs backend`
4. Open an issue on GitHub

---

**End of Enhanced Web Scraper Guide**
