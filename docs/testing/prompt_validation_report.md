# LLM Extraction Prompt Validation & Examples

## Current Prompt Analysis

### ✅ Current System Prompt (Score: 7/10)
```
You are an expert data extraction assistant. Extract the requested information from the provided content.

CRITICAL RULES:
1. Extract ONLY values that exist in the content
2. NEVER hallucinate or make up values
3. If a field is not found, use "—"
4. Return VALID JSON ONLY (no markdown, no explanations)
5. Be thorough - search entire content carefully

Return format:
{
  "field1": "extracted_value",
  "field2": "extracted_value",
  "field3": "—"
}
```

**Strengths:**
- Clear rules about not hallucinating
- Specifies JSON-only output
- Provides fallback value ("—")

**Weaknesses:**
- No concrete examples
- No search strategy guidance
- Generic format example

---

## 🎯 IMPROVED PROMPT EXAMPLES

### Example 1: Enhanced System Prompt (Score: 9/10)
```
You are an expert data extraction assistant specializing in structured data extraction from web pages and documents.

EXTRACTION RULES:
1. Extract ONLY values that appear in the provided content
2. Search the entire content systematically - don't stop at first mention
3. For prices: Look for currency symbols (£, $, €) and numeric values
4. For titles: Look for prominent text, headings, or <h1> tags
5. If a field truly doesn't exist in the content, return "—"
6. Return ONLY valid JSON - no markdown fences, no explanations

IMPORTANT: Be thorough. A value might appear multiple times - extract the most prominent or first occurrence.

Output format (STRICT):
{
  "field_name_1": "extracted value or —",
  "field_name_2": "extracted value or —"
}

Example extraction:
Content: "Product: iPhone 15 Pro. Price: $999. Available in stores."
Fields: ["Product Name", "Price", "Shipping Cost"]
Output: {"Product Name": "iPhone 15 Pro", "Price": "$999", "Shipping Cost": "—"}
```

**Why it's better:**
- ✅ Provides specific search strategies for common fields
- ✅ Shows concrete example of extraction
- ✅ Emphasizes thoroughness with explanation
- ✅ Warns about multiple occurrences

---

### Example 2: Context-Aware User Prompt (Score: 9/10)
```
CONTENT TYPE: Web page HTML (converted to text)
SOURCE: https://books.toscrape.com/catalogue/sharp-objects_997/index.html

CONTENT TO ANALYZE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[2,694 characters of content here...]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXTRACTION TASK:
Extract the following fields from the content above:

1. **Book Title**
   - Look for: Main heading, product title, or book name
   - Typically in <h1> tags or prominent text

2. **Price**
   - Look for: Currency symbol (£, $, €) followed by numbers
   - Common patterns: "£47.82", "Price: £47.82", "£ 47.82"

USER INSTRUCTION: Extract book title and price

OUTPUT FORMAT (JSON only):
{
  "Book Title": "extracted title or —",
  "Price": "extracted price with currency symbol or —"
}
```

**Why it's better:**
- ✅ Provides context about content type and source
- ✅ Numbered fields with search hints for each
- ✅ Shows example patterns for each field type
- ✅ Explicit output format with actual field names

---

## 📊 COMPARISON: Current vs. Improved

| Aspect | Current Prompt | Improved Prompt |
|--------|---------------|-----------------|
| **Clarity** | Generic instructions | Field-specific guidance |
| **Examples** | Abstract format only | Concrete extraction example |
| **Search Strategy** | "Be thorough" | Specific patterns to look for |
| **Context** | Content only | Content type + source + hints |
| **Success Rate** | ~50% (guessing) | ~85-95% (estimated) |

---

## 🔍 DEBUGGING THE CURRENT ISSUE

### Given Information:
- ✅ Text extraction: WORKING (2,694 characters extracted)
- ✅ OpenAI API key: WORKING (RAG chat working)
- ✅ Field parsing: WORKING (["Book Title", "Price"])
- ❌ LLM extraction: RETURNING "—" for all fields

### Possible Root Causes:

#### 1. **Prompt Too Generic** (Likelihood: 40%)
The current prompt doesn't give enough hints about WHERE to find data in HTML-derived text.

**Test:** Try the improved prompt above

#### 2. **Content Format Issue** (Likelihood: 30%)
The `inner_text()` from Playwright might be stripping important context or formatting that helps the LLM locate fields.

**Example:**
```
BAD (no structure):
Books to Scrape Sharp Objects £47.82 In stock...

GOOD (preserves structure):
Books to Scrape
---
Sharp Objects
Price: £47.82
Availability: In stock
```

**Test:** Check what the actual 2,694 characters look like

#### 3. **LLM Response Parsing Failure** (Likelihood: 20%)
The LLM might be returning valid data, but the JSON parsing is failing and defaulting to "—".

**Test:** Check the raw LLM response before parsing

#### 4. **Content Truncation** (Likelihood: 10%)
The prompt truncates content at 20,000 chars, but maybe the important data is getting cut off or the LLM is overwhelmed.

**Test:** Try with smaller, focused content

---

## 🧪 RECOMMENDED TESTS

### Test 1: Check Actual LLM Input
```bash
# Enable debug logging and capture the actual content being sent
docker-compose logs backend | grep -A 50 "📄 Content preview"
```

### Test 2: Check Raw LLM Response
```bash
# See what OpenAI actually returns before JSON parsing
docker-compose logs backend | grep -A 10 "🤖 LLM Response"
```

### Test 3: Test with Direct OpenAI Call
```python
# Bypass the extraction pipeline and call OpenAI directly
import openai

content = """
Sharp Objects
£47.82
In stock (22 available)
"""

response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "Extract book title and price. Return JSON only."},
        {"role": "user", "content": f"Content: {content}\n\nExtract: Book Title, Price\n\nReturn JSON."}
    ],
    temperature=0
)

print(response.choices[0].message.content)
# Expected: {"Book Title": "Sharp Objects", "Price": "£47.82"}
```

### Test 4: Compare Content Quality
```bash
# Check if the 2,694 characters actually contain the data
curl -X POST http://localhost:8000/api/v1/extract/ultra-smart \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://books.toscrape.com/catalogue/sharp-objects_997/index.html",
    "user_instructions": "Just return the first 1000 characters of content you see",
    "source_type": "url",
    "llm_provider": "openai"
  }' | jq -r '.table[0]'
```

---

## 🎯 RECOMMENDED IMPROVEMENTS

### Short-term (Fix current issue):
1. **Check raw LLM response** - Is OpenAI returning "—" or is parsing failing?
2. **Verify content quality** - Does the extracted text actually contain "Sharp Objects" and "£47.82"?
3. **Add debug output** - Print first 500 chars of content to verify

### Medium-term (Improve reliability):
1. **Enhance prompts** - Use the improved prompts above
2. **Add HTML structure preservation** - Keep some HTML tags or use structured extraction
3. **Add retry logic** - If extraction returns all "—", retry with more specific prompts

### Long-term (Production-ready):
1. **Multi-strategy extraction** - Try regex → CSS selectors → LLM (fallback chain)
2. **Validation layer** - Verify extracted data makes sense (e.g., price has currency symbol)
3. **Confidence scores** - LLM returns confidence for each field
4. **Field-specific models** - Use specialized prompts for different field types

---

## 📝 VERDICT

**Current Prompt Quality: 7/10** - Good foundation but too generic

**Recommended Action:**
1. ✅ **First:** Debug why it's failing (check actual LLM response in logs)
2. ✅ **Then:** Implement improved prompts (see Example 1 & 2 above)
3. ✅ **Finally:** Add validation and fallback strategies

The fact that OpenAI RAG Chat is working confirms the issue is NOT the API key, but rather:
- Either the prompt needs improvement
- Or the content format is problematic
- Or the response parsing is failing

Next step: Check the debug logs to see what OpenAI actually returns.
