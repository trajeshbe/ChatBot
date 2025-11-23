# Advanced Capabilities Usage Guide

**Features**: OCR, Translation, Form Automation
**Status**: ✅ IMPLEMENTED
**Date**: 2025-11-21

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [OCR Service](#ocr-service)
3. [Translation Service](#translation-service)
4. [Form Automation](#form-automation)
5. [Integration Examples](#integration-examples)
6. [API Usage](#api-usage)

---

## Overview

Three new advanced capabilities have been added to the scraping stack:

1. **OCR Service**: Hybrid Docling + Tesseract for text extraction from scanned documents
2. **Translation Service**: Multi-backend (LLM + Transformers) for multilingual content
3. **Form Automation**: Playwright-integrated for intelligent form handling

### Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     OCR SERVICE                             │
│  Hybrid Strategy: Docling (Primary) → Tesseract (Fallback) │
│  • PDFs with complex layouts → Docling                     │
│  • Scanned documents/images → Tesseract                    │
│  • Automatic method selection                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 TRANSLATION SERVICE                         │
│  Multi-Backend: LLM (High Quality) ↔ Transformers (Bulk)   │
│  • Text < 500 chars → LLM (GPT-4/Claude)                   │
│  • Text >= 500 chars → Transformers (Helsinki-NLP)         │
│  • Intelligent cost optimization                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 FORM AUTOMATION                             │
│  Playwright-Integrated: Zero new dependencies              │
│  • Smart field detection (name, id, label, fuzzy)         │
│  • Multi-step form navigation                              │
│  • CAPTCHA detection                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## OCR Service

### Basic Usage

```python
from app.services.ocr_service import OCRService

# Initialize
ocr_service = OCRService()

# Extract text from PDF
result = await ocr_service.extract_text(
    file_path="/path/to/document.pdf",
    method="auto"  # Auto-selects best method
)

print(result["text"])
print(f"Method used: {result['method_used']}")
print(f"Confidence: {result['confidence']:.2f}")
print(f"Pages: {result['pages']}")
```

### Method Selection

```python
# Force specific method
result = await ocr_service.extract_text(
    file_path="/path/to/scanned.pdf",
    method="tesseract",  # "docling", "tesseract", or "auto"
    language="eng"  # Tesseract language code
)

# Auto method (recommended)
result = await ocr_service.extract_text(
    file_path="/path/to/document.pdf",
    method="auto"  # Intelligently selects based on file type
)
```

### Supported File Types

- **PDFs**: .pdf (Docling primary, Tesseract fallback)
- **Images**: .jpg, .jpeg, .png, .tiff, .bmp, .gif (Tesseract)

### Response Format

```json
{
  "text": "Extracted text content...",
  "method_used": "docling",
  "confidence": 0.95,
  "pages": 3,
  "file_path": "/path/to/document.pdf",
  "file_type": "pdf",
  "metadata": {
    "has_tables": true,
    "has_images": true,
    "converter": "docling"
  }
}
```

### Use Cases

#### 1. Scanned Invoices

```python
# Extract from scanned invoice
result = await ocr_service.extract_text(
    file_path="scanned_invoice.pdf",
    method="auto"
)

# Use extracted text for data extraction
invoice_data = extract_invoice_details(result["text"])
```

#### 2. Historical Documents

```python
# Extract from old documents
result = await ocr_service.extract_text(
    file_path="historical_doc.tiff",
    method="tesseract",
    language="eng"
)
```

#### 3. Image with Text

```python
# Extract from screenshot
result = await ocr_service.extract_text(
    file_path="screenshot.png",
    method="tesseract"
)
```

### Error Handling

```python
try:
    result = await ocr_service.extract_text(
        file_path=file_path,
        method="auto"
    )
except ValueError as e:
    print(f"Invalid input: {e}")
except RuntimeError as e:
    print(f"All OCR methods failed: {e}")
```

### Service Status

```python
# Check service status
status = ocr_service.get_status()
print(status)

# Output:
# {
#     "service": "ocr",
#     "backends": {
#         "docling": {"available": True, "description": "..."},
#         "tesseract": {"available": True, "description": "..."}
#     },
#     "ready": True
# }
```

---

## Translation Service

### Basic Usage

```python
from app.services.translation_service import TranslationService
from app.services.llm_service import LLMService

# Initialize
llm_service = LLMService(db)
translation_service = TranslationService(llm_service=llm_service)

# Translate text
result = await translation_service.translate(
    text="Hello, how are you?",
    source_lang="en",
    target_lang="es",
    quality="auto"  # Auto-selects best backend
)

print(result["translated_text"])
# Output: "Hola, ¿cómo estás?"
```

### Backend Selection

```python
# High quality (uses LLM)
result = await translation_service.translate(
    text="Important customer-facing content",
    source_lang="en",
    target_lang="fr",
    quality="high"  # Forces LLM backend
)

# Standard quality (uses Transformers)
result = await translation_service.translate(
    text="Large bulk content for processing...",
    source_lang="en",
    target_lang="de",
    quality="standard"  # Forces Transformers backend
)

# Auto (intelligent routing)
result = await translation_service.translate(
    text="Some text",
    source_lang="en",
    target_lang="es",
    quality="auto"  # Routes based on length
)
```

### Intelligent Routing Logic

```python
# Short text → LLM (high accuracy)
short_text = "Product description: Premium quality leather wallet"
result = await translation_service.translate(
    text=short_text,  # < 500 chars
    source_lang="en",
    target_lang="ja",
    quality="auto"  # Will use LLM
)

# Long text → Transformers (cost-effective)
long_text = "..." * 200  # > 500 chars
result = await translation_service.translate(
    text=long_text,
    source_lang="en",
    target_lang="zh",
    quality="auto"  # Will use Transformers
)
```

### Supported Languages

```python
# Get supported languages
languages = translation_service.get_supported_languages()

# Output:
# [
#     {"code": "en", "name": "English"},
#     {"code": "es", "name": "Spanish"},
#     {"code": "fr", "name": "French"},
#     # ... 26 languages total
# ]
```

### Response Format

```json
{
  "translated_text": "Hola, ¿cómo estás?",
  "source_lang": "en",
  "target_lang": "es",
  "backend_used": "llm",
  "confidence": 0.92,
  "metadata": {
    "model": "gpt-4-turbo",
    "tokens_used": 45,
    "source_length": 18,
    "target_length": 18,
    "length_ratio": 1.0
  }
}
```

### Use Cases

#### 1. Product Descriptions (High Quality)

```python
# Translate product descriptions
product_desc = "Premium leather wallet with RFID protection"
result = await translation_service.translate(
    text=product_desc,
    source_lang="en",
    target_lang="es",
    quality="high"  # Use LLM for accuracy
)
```

#### 2. Bulk Content (Cost-Effective)

```python
# Translate large corpus
articles = [...]  # List of long articles

for article in articles:
    result = await translation_service.translate(
        text=article,
        source_lang="en",
        target_lang="fr",
        quality="standard"  # Use Transformers for cost
    )
```

#### 3. Multilingual Scraping

```python
# Extract and translate
extracted_content = "Content in Spanish..."
result = await translation_service.translate(
    text=extracted_content,
    source_lang="es",
    target_lang="en",
    quality="auto"
)
```

### Cost Optimization

```python
# LLM Backend Cost
- Small text (< 500 chars): ~$0.01 per 1K characters
- Best for: Product descriptions, marketing, user-facing content

# Transformers Backend Cost
- Any length: Free (offline model)
- Best for: Bulk translation, metadata, tags, internal content

# Auto Routing
- Automatically selects cost-optimal backend
- Balances quality and cost
```

### Error Handling

```python
try:
    result = await translation_service.translate(
        text=text,
        source_lang="en",
        target_lang="es"
    )
except ValueError as e:
    print(f"Invalid language or input: {e}")
except RuntimeError as e:
    print(f"All translation backends failed: {e}")
```

---

## Form Automation

### Basic Usage

```python
from app.services.webscraper.automation import FormHandler
from playwright.async_api import async_playwright

# Initialize Playwright and page
async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()

    # Navigate to form page
    await page.goto("https://example.com/contact-form")

    # Initialize form handler
    form_handler = FormHandler(page)

    # Fill and submit form
    result = await form_handler.fill_and_submit_form(
        form_data={
            "name": "John Doe",
            "email": "john@example.com",
            "message": "Hello, I'd like to inquire about..."
        },
        wait_after_submit=3000  # Wait 3 seconds after submit
    )

    print(f"Success: {result['success']}")
    print(f"Fields filled: {result['fields_filled']}/{len(form_data)}")
    print(f"Submit successful: {result['submit_successful']}")
    print(f"Response URL: {result['response_url']}")
```

### Field Matching Strategies

The form handler uses multiple strategies to find fields:

```python
# Strategy 1: Exact name match
form_data = {
    "username": "johndoe",  # Matches <input name="username">
    "email": "john@example.com"  # Matches <input name="email">
}

# Strategy 2: ID match
form_data = {
    "user_email": "john@example.com"  # Matches <input id="user_email">
}

# Strategy 3: Label text match
form_data = {
    "Full Name": "John Doe",  # Matches <label>Full Name</label> <input>
    "Email Address": "john@example.com"
}

# Strategy 4: Fuzzy match (placeholder, aria-label)
form_data = {
    "email": "john@example.com"  # Matches <input placeholder="Enter email">
}
```

### Advanced Options

```python
result = await form_handler.fill_and_submit_form(
    form_data={
        "name": "John",
        "email": "john@example.com"
    },

    # Submit options
    submit_button_selector="button.submit-btn",  # Custom submit button
    wait_after_submit=5000,  # Wait 5 seconds

    # Automation options
    auto_submit=True,  # Auto-submit after filling
    check_for_captcha=True,  # Check for CAPTCHA
    pause_for_captcha=True,  # Pause if CAPTCHA detected

    # Field options
    field_timeout=5000,  # Timeout per field (ms)
    min_fields_required=2,  # Minimum fields to fill before submitting

    # Navigation options
    navigation_timeout=30000  # Timeout for post-submit navigation
)
```

### Field Types Supported

```python
# Text inputs
form_data = {
    "username": "johndoe",
    "email": "john@example.com"
}

# Dropdown/select
form_data = {
    "country": "USA"  # Selects option with value "USA"
}

# Checkboxes
form_data = {
    "terms_agree": True,  # Checks checkbox
    "newsletter": False  # Unchecks checkbox
}

# Textareas
form_data = {
    "message": "Multi-line\ntext\ncontent"
}

# File uploads
form_data = {
    "resume": "/path/to/resume.pdf"  # Single file
    # or
    "photos": ["/path/to/photo1.jpg", "/path/to/photo2.jpg"]  # Multiple files
}
```

### CAPTCHA Detection

```python
# Check for CAPTCHA
form_handler = FormHandler(page)
has_captcha = await form_handler._detect_captcha()

if has_captcha:
    print("CAPTCHA detected - manual intervention required")
    await page.pause()  # Pauses for user to solve

# Automatic CAPTCHA detection
result = await form_handler.fill_and_submit_form(
    form_data=data,
    check_for_captcha=True,  # Enable CAPTCHA detection
    pause_for_captcha=True  # Pause if detected
)
```

### Form Inspection

```python
# Get all form fields
form_handler = FormHandler(page)
fields = await form_handler.get_form_fields()

# Output:
# [
#     {
#         "tag": "input",
#         "type": "text",
#         "name": "username",
#         "id": "user_name",
#         "placeholder": "Enter username",
#         "required": True,
#         "value": ""
#     },
#     # ... more fields
# ]

# Get form status
status = await form_handler.get_form_status()

# Output:
# {
#     "has_form": True,
#     "total_fields": 5,
#     "required_fields": 3,
#     "filled_fields": 0,
#     "is_valid": False
# }
```

### Response Format

```json
{
  "success": true,
  "fields_filled": 3,
  "fields_failed": ["phone"],
  "submit_successful": true,
  "response_url": "https://example.com/thank-you",
  "errors": [],
  "metadata": {
    "captcha_detected": false
  }
}
```

### Use Cases

#### 1. Contact Form Submission

```python
result = await form_handler.fill_and_submit_form({
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "message": "Inquiry about services"
})
```

#### 2. Multi-Step Form Navigation

```python
# Step 1: Personal info
result1 = await form_handler.fill_and_submit_form(
    form_data={
        "first_name": "John",
        "last_name": "Doe"
    },
    submit_button_selector="button:has-text('Next')"
)

# Wait for next page
await page.wait_for_load_state("networkidle")

# Step 2: Contact info
result2 = await form_handler.fill_and_submit_form(
    form_data={
        "email": "john@example.com",
        "phone": "+1234567890"
    },
    submit_button_selector="button:has-text('Submit')"
)
```

#### 3. Form with File Upload

```python
result = await form_handler.fill_and_submit_form({
    "applicant_name": "John Doe",
    "resume": "/path/to/resume.pdf",
    "cover_letter": "/path/to/cover.pdf"
})
```

#### 4. Login Form

```python
result = await form_handler.fill_and_submit_form(
    form_data={
        "username": "johndoe",
        "password": "secretpassword"
    },
    submit_button_selector='button[type="submit"]',
    wait_after_submit=2000
)

# Check if login successful
if result["submit_successful"]:
    print(f"Logged in! Redirected to: {result['response_url']}")
```

### Error Handling

```python
result = await form_handler.fill_and_submit_form(form_data=data)

if not result["success"]:
    print("Form submission failed!")
    print(f"Errors: {result['errors']}")
    print(f"Failed fields: {result['fields_failed']}")
else:
    print(f"Success! Response URL: {result['response_url']}")
```

---

## Integration Examples

### Combined Usage: Scrape → OCR → Translate

```python
from playwright.async_api import async_playwright
from app.services.ocr_service import OCRService
from app.services.translation_service import TranslationService

async def scrape_and_process():
    # 1. Scrape PDF document
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com/document.pdf")

        # Download PDF
        async with page.expect_download() as download_info:
            await page.click("a.download-link")
        download = await download_info.value
        pdf_path = await download.path()

    # 2. Extract text with OCR
    ocr_service = OCRService()
    ocr_result = await ocr_service.extract_text(
        file_path=pdf_path,
        method="auto"
    )

    # 3. Translate extracted text
    translation_service = TranslationService(llm_service)
    translation_result = await translation_service.translate(
        text=ocr_result["text"],
        source_lang="es",
        target_lang="en",
        quality="high"
    )

    print(f"Original: {ocr_result['text'][:100]}...")
    print(f"Translated: {translation_result['translated_text'][:100]}...")
```

### Form Automation in Scraping Workflow

```python
from playwright.async_api import async_playwright
from app.services.webscraper.automation import FormHandler

async def scrape_with_form():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate to login page
        await page.goto("https://example.com/login")

        # Login with form automation
        form_handler = FormHandler(page)
        login_result = await form_handler.fill_and_submit_form({
            "username": "scraper_user",
            "password": "secret"
        })

        if login_result["submit_successful"]:
            # Now scrape protected content
            await page.goto("https://example.com/protected-data")
            content = await page.content()

            # Process content
            # ...
```

---

## API Usage

### Status Endpoints

```bash
# Check OCR service status
curl http://localhost:8000/api/v1/ocr/status

# Response:
# {
#   "service": "ocr",
#   "backends": {
#     "docling": {"available": true, "description": "..."},
#     "tesseract": {"available": true, "description": "..."}
#   },
#   "ready": true
# }

# Check translation service status
curl http://localhost:8000/api/v1/translation/status

# Response:
# {
#   "service": "translation",
#   "backends": {
#     "llm": {"available": true, "cost": "~$0.01 per 1K chars"},
#     "transformers": {"available": true, "cost": "Free (offline)"}
#   },
#   "supported_languages": 26,
#   "routing_threshold": 500,
#   "ready": true
# }
```

### OCR API Endpoint

```bash
# Extract text from document
curl -X POST http://localhost:8000/api/v1/ocr/extract \
  -F "file=@/path/to/document.pdf" \
  -F "method=auto" \
  -F "language=eng"

# Response:
# {
#   "success": true,
#   "text": "Extracted text content...",
#   "method_used": "docling",
#   "confidence": 0.95,
#   "pages": 3,
#   "file_type": "pdf"
# }
```

### Translation API Endpoint

```bash
# Translate text
curl -X POST http://localhost:8000/api/v1/translation/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "source_lang": "en",
    "target_lang": "es",
    "quality": "auto"
  }'

# Response:
# {
#   "success": true,
#   "translated_text": "Hola, ¿cómo estás?",
#   "source_lang": "en",
#   "target_lang": "es",
#   "backend_used": "llm",
#   "confidence": 0.92
# }
```

---

## Summary

✅ **OCR Service**: Hybrid Docling + Tesseract with automatic fallback
✅ **Translation Service**: Multi-backend LLM + Transformers with intelligent routing
✅ **Form Automation**: Playwright-integrated with smart field detection

All three services are production-ready and integrate seamlessly with the existing scraping stack!

**Dependencies Added**: Only 4 minimal packages (pytesseract, Pillow, sacremoses, sentencepiece)
**Architecture**: Zero-compromise solutions optimized for the task at hand
**Performance**: Intelligent routing for cost and quality optimization
