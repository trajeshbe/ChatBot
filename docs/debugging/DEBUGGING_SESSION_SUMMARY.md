# LLM Extraction Debugging Session Summary

**Date**: 2025-11-19
**Issue**: Ultra-Smart extraction returning "—" or "---" instead of actual book data
**Test URL**: https://books.toscrape.com/catalogue/sharp-objects_997/index.html

---

## ✅ CONFIRMED FACTS

### 1. The Data IS in the Scraped Content
**Validated**: YES ✅

Test proved that BeautifulSoup extracts **2,252 characters** containing:
- "Sharp Objects" at position 0
- "£47.82" at position 89 and appears 3 times total

### 2. The Prompt Construction IS Correct
**Validated**: YES ✅

The full prompt sent to OpenAI includes:
```
Task: From the following scraped data, extract the following values:
- Book Title
- Price

Input Data:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sharp Objects | Books to Scrape - Sandbox
...
Sharp Objects
Sharp Objects
£47.82
...
Price (excl. tax)
£47.82
Price (incl. tax)
£47.82
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Length**: 2,252 chars of data + 355 char system prompt + 768 char user instructions = ~3,375 total chars

###3. OpenAI API IS Working
**Validated**: YES ✅

RAG chat works perfectly:
- Query: "you there?"
- Answer: "Yes, I'm here to help you. How may I assist you today?"
- Model: gpt-4-turbo

### 4. Improved Prompt Format Implemented
**Validated**: YES ✅

Changed from generic prompt to your clearer format:
```python
system_prompt = """You are an expert at parsing and extracting structured data from scraped web content, such as HTML or raw text dumps. Your goal is to accurately identify and pull out specific key-value pairs without hallucinating or adding extra information. Always base extractions solely on the provided content. Do not infer or guess; use verbatim text where possible."""
```

---

## ❓ UNKNOWN / UNRESOLVED

### 1. Debug Logs Not Appearing
**Problem**: Added comprehensive debug logging to `llm_extractor.py` lines 584-593 but logs never appear

**Possible Causes**:
- Module caching (Python not reloading the code)
- Different code path being used
- Logging level filtering

### 2. Extraction Returns Instantly
**Observation**: Recent extraction returned immediately (< 1 second)
**Previous**: Took 38 seconds (indicating OpenAI call)

**This suggests**:
- OpenAI is NOT being called
- Result is cached or defaulting immediately
- Different extractor is being used

### 3. No Extraction Logs AT ALL
**Problem**: Backend logs show ZERO extraction activity:
- No "LLM TEMPLATE MAPPING STARTED"
- No "Calling LLM service..."
- No scraping logs
- No LLM response logs

**Only logs**: Database setup and SQLAlchemy queries

---

## 🔍 ROOT CAUSE HYPOTHESIS

### Theory 1: Module Caching
Python is not reloading `llm_extractor.py` after edits because:
- The module is already imported
- Docker volume mounting doesn't trigger reload
- Uvicorn's auto-reload isn't working

**Evidence**:
- Debug logs don't appear despite being added
- Prompt improvements don't seem to affect results

**Solution**: Force rebuild

### Theory 2: Wrong Extractor Being Used
The `/api/v1/extract/ultra-smart` endpoint might not be using `llm_extractor.py` at all.

**Evidence**:
- No extraction logs appear
- Instant response (no OpenAI call)
- Different behavior than expected

**Solution**: Trace the actual code path

### Theory 3: Caching Layer
There's a caching mechanism returning cached "—" values.

**Evidence**:
- Instant response
- No LLM call logs
- Consistent empty results

**Solution**: Check for caching in ultra_smart_extractor.py or template_extraction_routes.py

---

## 📋 CHANGES MADE TO CODE

### File: `backend/app/services/webscraper/extractors/llm_extractor.py`

#### Change 1: Improved Prompt (Lines 492-532)
**Old**: Generic "professional assistant" prompt with scattered rules
**New**: Clear expert prompt with explicit task description

```python
system_prompt = """You are an expert at parsing and extracting structured data from scraped web content..."""

extraction_prompt = f"""Task: From the following scraped data, extract the following values:
{fields_list}

Input Data:
{truncated_data}

Output Format: Respond only with a clean JSON object, JUST COLUMN VALUE PAIRS.
```

#### Change 2: Debug Logging (Lines 534-560, 584-593)
Added logging to capture:
- Scraped content preview
- System prompt
- Extraction prompt
- RAW LLM response (full dict)
- LLM response content

---

## 🎯 NEXT STEPS TO RESOLVE

### Step 1: Force Module Reload
```bash
docker-compose down
docker-compose build backend --no-cache
docker-compose up -d
```

### Step 2: Trace Actual Code Path
Check if `ultra_smart_extractor.py` actually calls `llm_extractor.py`:
```bash
grep -n "llm_extractor\|LLMExtractor" backend/app/services/webscraper/extractors/ultra_smart_extractor.py
```

### Step 3: Add Print Statements
If logging doesn't work, add `print()` statements that write to stdout:
```python
print("🔥 LLM_EXTRACTOR CALLED!", flush=True)
```

### Step 4: Check for Caching
Look for cache checks in:
- `ultra_smart_extractor.py`
- `template_extraction_routes.py`
- Redis or other caching layers

---

## 📊 TEST RESULTS TIMELINE

| Time | Action | Result | Duration |
|------|--------|--------|----------|
| Earlier | Initial test | `{"Book Title": "—", "Price": "—"}` | 38 seconds |
| After prompt improvement | Test with new prompt | `{"Book Title": "---", "Price": "---"}` | 38 seconds |
| After debug logging | Test with logging | `{"Book Title": "---", "Price": "---"}` | < 1 second |

**Concern**: The instant response suggests OpenAI is not being called at all.

---

## 💡 KEY INSIGHTS

1. **The data IS available** - The scraped content contains exactly what we need
2. **The prompt structure IS correct** - We verified the full prompt with data
3. **OpenAI IS working** - RAG chat proves the API key works
4. **Something is bypassing the extraction** - No logs appear, instant response

**Conclusion**: The issue is NOT with:
- ❌ Data extraction
- ❌ Prompt quality
- ❌ OpenAI API

**The issue IS with**:
- ✅ Code execution path (module not loading OR wrong path being taken)
- ✅ Caching (results being returned without LLM call)
- ✅ Logging configuration (can't see what's happening)

---

## 🔧 RECOMMENDED FIX

1. **Rebuild backend** to ensure new code loads
2. **Add print() debugging** to see actual execution
3. **Check caching mechanisms** in the extraction pipeline
4. **Trace from API endpoint** to see which extractor is actually called

The prompt improvement was good, but we need to ensure it's actually being executed.
