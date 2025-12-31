# Scraping Configuration & Compliance Guide

> **Last Updated**: 2025-11-23
> **Purpose**: Comprehensive guide for configuring responsible and compliant web scraping

---

## Table of Contents

1. [Overview](#overview)
2. [Admin Console Features](#admin-console-features)
3. [Database Schema](#database-schema)
4. [Configuration Options](#configuration-options)
5. [Best Practices](#best-practices)
6. [API Reference](#api-reference)
7. [Examples](#examples)

---

## Overview

The Scraping Configuration & Compliance system provides:

- ✅ **Domain-level control** over what can be scraped
- ✅ **Robots.txt compliance** enforcement
- ✅ **Rate limiting** per domain
- ✅ **API integration** for sites with official APIs
- ✅ **Terms of Service tracking**
- ✅ **Permission management** from site owners
- ✅ **Comprehensive audit logging**

---

## Admin Console Features

### **1. Domain Whitelist/Blacklist**

Configure which domains are allowed to be scraped:

```
Domain: moneycontrol.com
Allow Scraping: ❌ No
Status: 🔴 Blocked
Reason: Strict anti-scraping policy (Akamai Bot Manager)
Alternative: Use MoneyControl API (if available)
```

### **2. Robots.txt Compliance**

Automatic checking and enforcement:

- Auto-fetches `/robots.txt` for each domain
- Parses User-agent rules
- Enforces `Disallow` directives
- Respects `Crawl-delay` settings
- Tracks last check timestamp

### **3. Rate Limiting Configuration**

Per-domain rate limits:

```
Domain: example.com
Requests per minute: 10
Delay between requests: 2.0 seconds
Max concurrent requests: 1
```

### **4. API Integration**

For sites with official APIs:

```
Domain: newsapi.org
Use API: ✅ Yes
API Endpoint: https://newsapi.org/v2/everything
API Key: [Encrypted]
API Documentation: https://newsapi.org/docs
Preferred Method: API
```

### **5. Terms of Service Tracker**

Document ToS compliance:

```
Domain: example.com
Terms Checked: ✅ Yes
Terms URL: https://example.com/terms
Checked At: 2025-11-23 10:00:00
Notes: "Allows non-commercial scraping with attribution"
```

### **6. Permission Registry**

Track permissions from site owners:

```
Domain: example.com
Permission Granted: ✅ Yes
Contact: webmaster@example.com
Granted At: 2025-11-15
Expires At: 2026-11-15
Permission Document: /permissions/example-com-2025.pdf
```

---

## Database Schema

### **scraping_configs**

Main configuration table:

| Column | Type | Description |
|--------|------|-------------|
| `domain` | VARCHAR(255) | Domain name (e.g., "example.com") |
| `allow_scraping` | BOOLEAN | Whether scraping is allowed |
| `robots_txt_compliant` | BOOLEAN | Enforce robots.txt |
| `rate_limit_requests_per_minute` | INTEGER | Max requests per minute |
| `rate_limit_delay_seconds` | FLOAT | Delay between requests |
| `use_api` | BOOLEAN | Use official API instead |
| `api_endpoint` | VARCHAR(512) | API base URL |
| `api_key_encrypted` | TEXT | Encrypted API key |
| `terms_checked` | BOOLEAN | ToS reviewed |
| `permission_granted` | BOOLEAN | Explicit permission |
| `preferred_method` | VARCHAR(50) | 'api', 'playwright', 'requests', 'auto' |
| `status` | VARCHAR(50) | 'active', 'blocked', 'suspended' |

### **scraping_audit_log**

Track all scraping attempts:

| Column | Type | Description |
|--------|------|-------------|
| `domain` | VARCHAR(255) | Domain scraped |
| `url` | VARCHAR(1024) | Full URL |
| `method` | VARCHAR(50) | Method used ('api', 'playwright') |
| `status_code` | INTEGER | HTTP status code |
| `success` | BOOLEAN | Whether successful |
| `robots_txt_allowed` | BOOLEAN | Compliant with robots.txt |
| `rate_limit_respected` | BOOLEAN | Rate limit honored |

### **domain_statistics**

Aggregate stats per domain:

| Column | Type | Description |
|--------|------|-------------|
| `domain` | VARCHAR(255) | Domain name |
| `total_requests` | INTEGER | Total scraping attempts |
| `successful_requests` | INTEGER | Successful scrapes |
| `failed_requests` | INTEGER | Failed scrapes |
| `rate_limit_violations` | INTEGER | Rate limit breaches |
| `robots_txt_violations` | INTEGER | Robots.txt violations |

---

## Configuration Options

### **Compliance Settings**

```python
{
    "allow_scraping": True,  # Master switch
    "robots_txt_compliant": True,  # Enforce robots.txt
    "robots_txt_url": "https://example.com/robots.txt",
    "robots_txt_checked_at": "2025-11-23T10:00:00Z"
}
```

### **Rate Limiting**

```python
{
    "rate_limit_enabled": True,
    "rate_limit_requests_per_minute": 10,  # Max 10 requests/min
    "rate_limit_delay_seconds": 2.0,  # 2 second delay
    "max_concurrent_requests": 1  # Sequential only
}
```

### **API Configuration**

```python
{
    "use_api": True,
    "api_endpoint": "https://api.example.com/v1",
    "api_key_encrypted": "<encrypted_key>",
    "api_documentation_url": "https://api.example.com/docs",
    "preferred_method": "api"
}
```

### **Permission Tracking**

```python
{
    "permission_granted": True,
    "permission_contact": "webmaster@example.com",
    "permission_granted_at": "2025-11-15T00:00:00Z",
    "permission_expires_at": "2026-11-15T00:00:00Z",
    "permission_document_url": "/permissions/example-2025.pdf"
}
```

---

## Best Practices

### **1. Check Robots.txt First** ✅

Before scraping any domain:

```bash
curl https://example.com/robots.txt
```

Look for:
- `User-agent: *` (applies to all bots)
- `Disallow: /` (blocks all scraping)
- `Crawl-delay: 5` (5 second delay required)

### **2. Review Terms of Service** ✅

Check the website's ToS:

- ❌ Explicit "No scraping" clauses
- ✅ "Non-commercial use" permissions
- ✅ "With attribution" requirements
- ❌ "Must use API" requirements

### **3. Use Official APIs When Available** ✅

Many sites offer APIs:

| Site | API Available | Documentation |
|------|---------------|---------------|
| NewsAPI | ✅ Yes | https://newsapi.org/docs |
| Twitter | ✅ Yes | https://developer.twitter.com |
| Reddit | ✅ Yes | https://www.reddit.com/dev/api |
| Amazon | ✅ Yes | Product Advertising API |
| Google | ✅ Yes | Custom Search JSON API |

### **4. Respect Rate Limits** ✅

Recommended limits:

- **Small sites**: 1 request every 5-10 seconds
- **Medium sites**: 1 request every 2-5 seconds
- **Large sites**: 10-20 requests per minute
- **APIs**: Follow documented rate limits

### **5. Request Permission** ✅

For commercial use or bulk scraping:

**Email Template:**

```
Subject: Permission Request for Data Access

Dear [Site Owner],

I am writing to request permission to programmatically access content
from [domain] for [purpose].

Purpose: [e.g., "Academic research on..."]
Frequency: [e.g., "10 requests per hour"]
Data Usage: [e.g., "Non-commercial, internal analysis only"]
Attribution: [e.g., "Will cite your site in all publications"]

Would it be possible to grant permission for this access? I am happy
to provide more details or discuss alternative arrangements.

Best regards,
[Your Name]
```

### **6. Identify Your Bot** ✅

Use a custom User-Agent:

```
User-Agent: YourBotName/1.0 (+https://yoursite.com/bot-info)
```

Create a `/bot-info` page explaining:
- What your bot does
- How often it scrapes
- Contact information
- How to opt-out

---

## API Reference

### **Create Domain Configuration**

```bash
POST /api/v1/admin/scraping-configs
Content-Type: application/json

{
  "domain": "example.com",
  "allow_scraping": true,
  "robots_txt_compliant": true,
  "rate_limit_requests_per_minute": 10,
  "rate_limit_delay_seconds": 2.0,
  "notes": "Allowed for non-commercial use"
}
```

### **Update Domain Configuration**

```bash
PUT /api/v1/admin/scraping-configs/{domain}
Content-Type: application/json

{
  "allow_scraping": false,
  "status": "blocked",
  "block_reason": "Received cease & desist notice"
}
```

### **Get Domain Configuration**

```bash
GET /api/v1/admin/scraping-configs/{domain}
```

### **Check if Domain Allows Scraping**

```bash
GET /api/v1/admin/scraping-configs/{domain}/check
```

Response:
```json
{
  "allowed": false,
  "reason": "Domain is blocked",
  "status": "blocked",
  "alternative": "Use official API at https://api.example.com"
}
```

### **Get Scraping Audit Logs**

```bash
GET /api/v1/admin/scraping-audit-logs?domain=example.com&limit=100
```

### **Get Domain Statistics**

```bash
GET /api/v1/admin/domain-statistics/{domain}
```

Response:
```json
{
  "domain": "example.com",
  "total_requests": 150,
  "successful_requests": 140,
  "failed_requests": 10,
  "rate_limit_violations": 0,
  "robots_txt_violations": 0,
  "avg_response_time_ms": 250.5
}
```

---

## Examples

### **Example 1: Allow Simple Site**

```python
# Configure books.toscrape.com (test site)
config = {
    "domain": "books.toscrape.com",
    "allow_scraping": True,
    "robots_txt_compliant": True,
    "rate_limit_requests_per_minute": 30,
    "rate_limit_delay_seconds": 1.0,
    "notes": "Test site designed for scraping practice"
}
```

### **Example 2: Block Protected Site**

```python
# Block moneycontrol.com (Akamai protection)
config = {
    "domain": "moneycontrol.com",
    "allow_scraping": False,
    "status": "blocked",
    "block_reason": "Enterprise-grade bot protection (Akamai)",
    "notes": "Investigate if they offer an official API"
}
```

### **Example 3: Use API Instead**

```python
# Configure NewsAPI
config = {
    "domain": "newsapi.org",
    "allow_scraping": True,
    "use_api": True,
    "api_endpoint": "https://newsapi.org/v2/everything",
    "api_key_encrypted": encrypt("your_api_key_here"),
    "api_documentation_url": "https://newsapi.org/docs",
    "preferred_method": "api",
    "rate_limit_requests_per_minute": 100,  # API limit
    "notes": "Official API - preferred over scraping"
}
```

### **Example 4: Tracked Permission**

```python
# Site with explicit permission
config = {
    "domain": "university-research.edu",
    "allow_scraping": True,
    "permission_granted": True,
    "permission_contact": "data-officer@university.edu",
    "permission_granted_at": "2025-11-01T00:00:00Z",
    "permission_expires_at": "2026-11-01T00:00:00Z",
    "permission_document_url": "/permissions/university-2025.pdf",
    "rate_limit_requests_per_minute": 60,
    "notes": "Permission granted for academic research project"
}
```

---

## Default Configurations

The migration includes default configs for common sites:

### **Allowed (Test Sites)**

- ✅ `books.toscrape.com` - Scraping practice site
- ✅ `example.com` - IANA example domain
- ✅ `httpbin.org` - HTTP testing service

### **Blocked (Strict Policies)**

- ❌ `amazon.com` - Use Product Advertising API
- ❌ `google.com` - Use Custom Search JSON API
- ❌ `facebook.com` - Use Graph API
- ❌ `twitter.com` - Use Twitter API v2
- ❌ `linkedin.com` - Use LinkedIn Marketing API

---

## Migration

Apply the migration:

```bash
cd backend
psql -U postgres -d ragchatbot -f migrations/004_add_scraping_configs.sql
```

Or using the setup script:

```bash
./scripts/setup/apply-migrations.sh
```

---

## Next Steps

1. **Implement Backend Service** - `scraping_config_service.py`
2. **Add Admin API Routes** - `/api/v1/admin/scraping-configs/*`
3. **Create Frontend Component** - `ScrapingConfigTab.tsx`
4. **Integrate with Compliance Engine** - Check configs before scraping
5. **Add Audit Logging** - Log all scraping attempts

---

## Related Documentation

- [Admin Guide](./ADMIN_GUIDE.md)
- [Web Scraper Guide](./WEB_SCRAPER_ENHANCED_GUIDE.md)
- [Ultra-Smart Extraction Guide](./SMART_EXTRACTION_GUIDE.md)

---

**Questions or Issues?**

See `docs/README.md` for additional documentation or contact the development team.

---

**Last Updated**: 2025-11-23
