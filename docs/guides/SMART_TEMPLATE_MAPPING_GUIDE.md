# Smart Template Mapping Guide

## Overview

The **Smart Template Mapping** feature uses AI (LLM) to intelligently map raw scraped web data to your custom Excel template columns. This solves the common problem where you have:

1. **Scraped data** from a website (raw HTML or text)
2. **Your custom template** with specific column headers you want to populate

Instead of manually writing selectors or regex patterns for each field, the LLM analyzes your scraped data and automatically maps it to your template columns.

## Key Features

### 🎯 No Hallucination
- **Never makes up values** that don't exist in the scraped data
- Only extracts values that are actually present
- Explicitly marks missing fields

### 📊 Transparent Data Completeness
- Shows which fields were successfully extracted
- Lists which fields require additional research
- Marks missing fields as `— (requires additional research)`

### 🔄 Flexible Template Support
- Works with any custom template columns
- Supports example values to guide extraction
- Handles numeric, text, percentage, and other data types

### 🚀 Easy to Use
- No need to write complex selectors
- Just provide scraped data and template columns
- LLM handles the intelligent mapping

## Problem Solved

### Before: Null Values Despite Correct Columns

```python
# Old approach might return:
{
    "Market Cap": None,
    "Stock P/E": None,
    "ROE": None,
    # ... all columns present but values are NULL
}
```

**Why?** The old prompts didn't clearly instruct the LLM on:
- How to map scraped data to template columns
- Not to hallucinate missing values
- How to handle fields not present in the data

### After: Smart Mapping with Clear Results

```python
# New approach returns:
{
    "mapped_data": {
        "Market Cap": "17,88,392 Cr",
        "Stock P/E": "25.3",
        "ROE": "8.92 %",
        "Revenue Growth": "— (requires additional research)"
    },
    "missing_fields": ["Revenue Growth"],
    "extraction_complete": False
}
```

## Usage

### Basic Usage

```python
from app.services.llm_service import llm_service
from app.services.webscraper.extractors.llm_extractor import LLMExtractor

# Initialize
await llm_service.initialize()
extractor = LLMExtractor(llm_service=llm_service)

# Define your template columns
template_columns = [
    "Company Name",
    "Market Cap",
    "Current Price",
    "Stock P/E",
    "Book Value",
    "Revenue Growth"  # May not be in scraped data
]

# Your scraped data (HTML or text)
scraped_data = """
<html>
    <h1>Reliance Industries Ltd.</h1>
    <div>Market Cap: ₹ 17,88,392 Cr.</div>
    <div>Current Price: ₹ 2,645</div>
    <div>Stock P/E: 25.3</div>
    <div>Book Value: ₹ 1,289</div>
</html>
"""

# Map to template
result = await extractor.map_to_custom_template(
    scraped_data=scraped_data,
    template_columns=template_columns,
    llm_provider="openai"  # Recommended for best accuracy
)

# Access results
mapped_data = result['mapped_data']
missing_fields = result['missing_fields']

print(f"Successfully extracted: {len(mapped_data) - len(missing_fields)} fields")
print(f"Require research: {missing_fields}")
```

### With Template Examples

If your Excel template has example values, you can provide them to guide the LLM:

```python
template_examples = {
    "Market Cap": "1234",
    "Stock P/E": "25.3",
    "Revenue Growth": "15%"
}

result = await extractor.map_to_custom_template(
    scraped_data=scraped_data,
    template_columns=template_columns,
    template_examples=template_examples,
    llm_provider="openai"
)
```

## How It Works

### The Improved Prompt

The new implementation uses a carefully crafted prompt that:

```
YOU are a professional data transformation assistant.

Your tasks:
1. Extract all numeric and text values from the scraped data
2. Map every scraped value to the correct column in the template
3. If a field does not exist in the scraped data, mark it as "— (requires additional research)"
4. Never fill values you do not see in the input
5. Provide a list of fields that need external sources

CRITICAL RULES:
- Extract ONLY values that exist in the scraped data
- NEVER hallucinate or make up values
- If a field does not exist, mark as "— (requires additional research)"
```

### Response Format

The LLM returns a structured JSON response:

```json
{
  "mapped_data": {
    "Company Name": "Reliance Industries Ltd.",
    "Market Cap": "17,88,392 Cr",
    "Current Price": "2,645",
    "Stock P/E": "25.3",
    "Revenue Growth": "— (requires additional research)"
  },
  "missing_fields": ["Revenue Growth"]
}
```

## Configuration

### LLM Provider Selection

Different providers have different strengths:

```python
# OpenAI (Recommended for accuracy)
result = await extractor.map_to_custom_template(
    scraped_data=data,
    template_columns=columns,
    llm_provider="openai"  # Best accuracy, requires API key
)

# Anthropic Claude (Great for complex data)
result = await extractor.map_to_custom_template(
    scraped_data=data,
    template_columns=columns,
    llm_provider="anthropic"  # Excellent reasoning
)

# Ollama (Local, no API key needed)
result = await extractor.map_to_custom_template(
    scraped_data=data,
    template_columns=columns,
    llm_provider="ollama"  # Free, runs locally
)
```

### Temperature Setting

The method uses `temperature=0.0` for maximum consistency:
- No randomness in responses
- Same input → same output (deterministic)
- Best for data extraction tasks

## Error Handling

### When Mapping Fails

```python
result = await extractor.map_to_custom_template(
    scraped_data=data,
    template_columns=columns
)

if result is None:
    # Mapping failed - check:
    # 1. LLM service is initialized
    # 2. API keys are configured
    # 3. Scraped data is not empty
    print("Mapping failed - check logs")
else:
    # Success
    mapped_data = result['mapped_data']
```

### Partial Extraction

Even if some fields are missing, the method still succeeds:

```python
if not result['extraction_complete']:
    print(f"Warning: {len(result['missing_fields'])} fields need research")
    for field in result['missing_fields']:
        print(f"  - {field}")
```

## Best Practices

### 1. Use Descriptive Column Names

❌ **Bad:**
```python
template_columns = ["Col1", "Col2", "Col3"]
```

✅ **Good:**
```python
template_columns = [
    "Company Name",
    "Market Capitalization",
    "Price-to-Earnings Ratio"
]
```

### 2. Provide Example Values When Possible

```python
template_examples = {
    "Market Capitalization": "1,234 Cr",
    "Price-to-Earnings Ratio": "25.3"
}
```

This helps the LLM understand:
- Expected data format
- Units (Cr, %, $, etc.)
- Precision (decimals, etc.)

### 3. Clean Scraped Data First

```python
# Remove excessive whitespace
cleaned_data = ' '.join(scraped_data.split())

# Or use BeautifulSoup to get clean text
from bs4 import BeautifulSoup
soup = BeautifulSoup(scraped_html, 'html.parser')
cleaned_data = soup.get_text()

result = await extractor.map_to_custom_template(
    scraped_data=cleaned_data,
    template_columns=columns
)
```

### 4. Handle Large Scraped Data

The method automatically truncates data to 8000 characters:

```python
# This is handled internally
if len(scraped_data) > 8000:
    truncated_data = scraped_data[:8000] + "... [truncated]"
```

If important data is being truncated, consider:
- Scraping specific sections only
- Pre-processing to remove unnecessary HTML
- Extracting relevant sections first

## Integration Examples

### With Web Scraper

```python
from app.services.scraper_service import scraper_service

# Scrape the page
scrape_result = await scraper_service.scrape_url("https://example.com/company")
scraped_html = scrape_result.get('html', '')

# Map to template
result = await extractor.map_to_custom_template(
    scraped_data=scraped_html,
    template_columns=my_template_columns,
    template_examples=my_template_examples
)

# Export to DataFrame
import pandas as pd
df = pd.DataFrame([result['mapped_data']])
df.to_excel('output.xlsx', index=False)
```

### With Multiple Pages

```python
import pandas as pd

urls = [
    "https://example.com/company1",
    "https://example.com/company2",
    "https://example.com/company3"
]

all_data = []

for url in urls:
    # Scrape
    scrape_result = await scraper_service.scrape_url(url)

    # Map to template
    result = await extractor.map_to_custom_template(
        scraped_data=scrape_result['html'],
        template_columns=template_columns
    )

    all_data.append(result['mapped_data'])

# Create DataFrame
df = pd.DataFrame(all_data)
df.to_excel('all_companies.xlsx', index=False)
```

## Comparison with Other Approaches

### vs. CSS Selectors

| Feature | Smart Mapping | CSS Selectors |
|---------|--------------|---------------|
| Flexibility | ✓ Works with any structure | ✗ Requires specific HTML |
| Setup Time | Fast (no selector writing) | Slow (write each selector) |
| Maintenance | Low (adapts to changes) | High (breaks with changes) |
| Accuracy | High (understands context) | Perfect (when working) |
| Cost | LLM API calls | Free |

### vs. Template Extractor

| Feature | Smart Mapping | Template Extractor |
|---------|--------------|-------------------|
| Requires Template | ✓ Yes | ✓ Yes |
| Selector Writing | ✗ No | ✓ Yes |
| Handles Variations | ✓ Yes | ✗ No |
| Speed | Slower (LLM call) | Faster (direct extract) |
| Accuracy | Context-aware | Selector-dependent |

## Troubleshooting

### Issue: All Fields Return "— (requires additional research)"

**Possible Causes:**
1. Scraped data is too long and important data is truncated
2. LLM doesn't understand the data format
3. Column names don't match data labels

**Solutions:**
```python
# 1. Check data length
print(f"Data length: {len(scraped_data)}")

# 2. Provide examples
template_examples = {"Market Cap": "1234 Cr"}

# 3. Use clearer column names
# Instead of "MC", use "Market Capitalization"
```

### Issue: Incorrect Value Extraction

**Possible Causes:**
1. Multiple similar values in data
2. Ambiguous column names
3. LLM choosing wrong value

**Solutions:**
```python
# Be more specific in column names
template_columns = [
    "Current Market Cap",  # Instead of just "Market Cap"
    "Latest Price",        # Instead of just "Price"
]

# Provide examples to guide extraction
template_examples = {
    "Current Market Cap": "17,88,392 Cr",
    "Latest Price": "2,645"
}
```

### Issue: LLM Service Not Available

**Error:**
```
LLM service not initialized
```

**Solution:**
```python
# Make sure to initialize
await llm_service.initialize()

# Check .env file has API keys
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

## API Reference

### `map_to_custom_template()`

```python
async def map_to_custom_template(
    self,
    scraped_data: str,
    template_columns: List[str],
    template_examples: Optional[Dict[str, Any]] = None,
    llm_provider: str = "openai"
) -> Optional[Dict[str, Any]]
```

**Parameters:**
- `scraped_data` (str): Raw scraped content (HTML or text)
- `template_columns` (List[str]): List of column headers from your template
- `template_examples` (Dict[str, Any], optional): Example values for columns
- `llm_provider` (str): LLM provider to use ("openai", "anthropic", or "ollama")

**Returns:**
Dictionary with:
- `mapped_data`: Dict mapping columns to extracted values
- `missing_fields`: List of fields that need additional research
- `extraction_complete`: Boolean indicating if all fields were found

**Returns None if:**
- LLM service not initialized
- LLM call failed
- Response parsing failed

## Testing

Run the test script to verify functionality:

```bash
cd backend
python test_smart_template_mapping.py
```

Expected output:
```
MAPPING RESULTS
================================================================================

Mapped Data:
  ✓ Company Name              : Reliance Industries Ltd.
  ✓ Market Cap                : 17,88,392 Cr
  ✓ Current Price             : 2,645
  ✓ Stock P/E                 : 25.3
  ✗ Revenue Growth            : — (requires additional research)

Extraction Status:
  - Complete: False
  - Fields requiring research: 1
```

## Future Enhancements

Planned improvements:
1. **Confidence Scores**: Return confidence for each extracted value
2. **Multiple Value Detection**: Handle cases where multiple values match
3. **Unit Normalization**: Automatically convert units (Cr → Crores, % → decimal)
4. **Caching**: Cache LLM responses for identical inputs
5. **Batch Processing**: Process multiple pages in one LLM call

## Support

If you encounter issues:

1. **Check Logs**: Enable debug logging
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Test with Simple Data**: Start with minimal scraped data

3. **Verify LLM Configuration**: Ensure API keys are set

4. **Review Template**: Make sure column names are clear and descriptive

## Conclusion

The Smart Template Mapping feature provides an intelligent, flexible way to map scraped web data to your custom templates without writing complex selectors or regex patterns. By leveraging LLM capabilities with carefully crafted prompts, it delivers accurate results while being transparent about data completeness.

**Key Takeaways:**
- ✓ No hallucination of missing values
- ✓ Clear marking of fields requiring research
- ✓ Works with any template structure
- ✓ No selector writing required
- ✓ Handles variations in web page structure

---

**Last Updated:** 2025-11-17
**Version:** 1.0
**Author:** ChatBot Development Team
