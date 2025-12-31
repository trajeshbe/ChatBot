# Extraction Returning Empty Data - Root Cause Analysis

## 🎯 PROBLEM SUMMARY

**Ultra-Smart Extraction API returns "—" for all fields despite:**
- ✅ OpenAI API working (RAG chat confirms this)
- ✅ Text extraction working (2,555 characters extracted)
- ✅ Playwright integration working
- ✅ Fields being parsed correctly

## 🔍 INVESTIGATION FINDINGS

### 1. The Wrong Extractor is Being Used

**Discovery**: The logs show `llm_extractor.py` is being used, NOT `ultra_smart_extractor.py`!

```
07:10:19.424 | WARNING | app.services.webscraper.extractors.llm_extractor - ⚠ LLM extraction returned 0 non-empty values
```

**Evidence**:
- `ultra_smart_extractor.py` has debug logging we added (lines 478-505)
- We added logs like "🔍 LLM EXTRACTION DEBUG INFO"
- These logs are **NOT appearing** in the backend logs
- Instead, we see logs from `llm_extractor.py`

**Conclusion**: The `/api/v1/extract/ultra-smart` endpoint is NOT using `ultra_smart_extractor.py` as expected!

### 2. LLM Service Logs Are Missing

**Expected**: When `llm_service.generate()` is called, it logs:
```
logger.info("="*60)
logger.info("🤖 LLM GENERATION REQUEST")
logger.info(f"📝 Prompt length: {len(prompt)} chars")
logger.info(f"💬 Messages: {len(messages) if messages else 0}")
logger.info(f"🎯 Max tokens: {max_tokens}")
logger.info(f"🌡️  Temperature: {temperature}")
logger.info("="*60)
```

**Actual**: These logs are **NOT appearing** at all!

**Conclusion**: Either:
1. `llm_service.generate()` is not being called
2. A different LLM service method is being called
3. The extractor is using a completely different code path

### 3. llm_extractor.py IS Getting Responses

**Evidence from code** (`llm_extractor.py` lines 600-669):
- Line 608: "🔍 Parsing LLM response as JSON..."
- Line 620: `mapped_data = result.get('mapped_data', {})`
- Line 643: Warning logged (we see this in logs!)

**This means**:
- LLM WAS called successfully
- LLM DID return a JSON response
- The response was parsed successfully
- But ALL values in `mapped_data` were "—"

## 🚨 ROOT CAUSE

### The LLM is WORKING but returning "—" for everything!

**Why would the LLM return "—" for all fields?**

1. **Prompt doesn't match content structure**
   - The LLM prompt might be asking for data that doesn't exist in the extracted text
   - Or the prompt format is confusing the LLM

2. **Content quality issue**
   - The extracted 2,555 characters might not actually contain "Sharp Objects" or "£47.82"
   - Playwright's `inner_text()` might be extracting the wrong elements

3. **Response format mismatch**
   - The LLM might be returning data in a different format than expected
   - The JSON parsing might be incorrectly interpreting the response

## 🔬 COMPARISON: Chat vs. Extraction

### Working RAG Chat (llm_service.py)

```python
# RAG uses llm_service.generate()
messages = [{"role": "user", "content": prompt}]
result = await self._call_openai(messages, max_tokens, temperature)
# Result: {"content": "Yes, I'm here to help you..."}
```

**Logs show**:
- Query: "you there?"
- Answer: "Yes, I'm here to help you. How may I assist you today?"
- Model: gpt-4-turbo
- ✅ WORKING PERFECTLY

### Broken Extraction (llm_extractor.py)

```python
# Extraction uses ???
# We don't see llm_service.generate() logs!
# Instead we see llm_extractor logs
# Result: {"mapped_data": {"Book Title": "—", "Price": "—"}}
```

**Logs show**:
- URL: books.toscrape.com/catalogue/sharp-objects_997/index.html
- Text extracted: 2,555 characters
- Fields requested: ["Book Title", "Price"]
- Result: ALL "—" (default "not found" value)
- ❌ BROKEN

## 📋 DEBUGGING STEPS NEEDED

### Step 1: Check Which Extractor the API Route Uses

```bash
# Find the ultra-smart extraction route
grep -r "ultra-smart" backend/app/api/routes/
```

**Expected**: Should route to `ultra_smart_extractor.py`
**Likely Reality**: Routing to `llm_extractor.py` instead

### Step 2: Check Actual Content Being Extracted

```bash
# Add logging to see the 2,555 characters
docker-compose logs backend | grep -A 50 "📄 Content preview"
```

**Questions**:
- Does the content actually contain "Sharp Objects"?
- Does it contain "£47.82"?
- Or is it just navigation/boilerplate text?

### Step 3: Find Where llm_extractor Calls LLM

```bash
# Search for where llm_extractor calls LLM service
grep -n "llm_service.generate\|self.llm_service" backend/app/services/webscraper/extractors/llm_extractor.py
```

**Goal**: Find the actual LLM call and check:
- What prompt is being sent?
- What response is being received?
- Why are we not seeing llm_service logs?

### Step 4: Compare Prompts

**RAG Chat Prompt** (working):
```
System: You are a helpful assistant
User: you there?
```

**Extraction Prompt** (broken):
```
System: ??? (unknown)
User: ??? (unknown)
Content: [2,555 chars from webpage]
Fields: Book Title, Price
```

We need to see the ACTUAL prompt being sent!

## 💡 LIKELY SOLUTIONS

### Solution 1: llm_extractor Using Wrong LLM Method

**Hypothesis**: `llm_extractor.py` is not calling `llm_service.generate()` correctly

**Fix**:
1. Find the LLM call in `llm_extractor.py`
2. Ensure it's using `await self.llm_service.generate()` with correct parameters
3. Add debug logging to show prompt and response

### Solution 2: Prompt Quality Issue

**Hypothesis**: The prompt sent to the LLM doesn't match the content

**Fix**:
1. Log the actual prompt being sent
2. Log the first 1000 chars of content
3. Compare with working RAG prompt structure
4. Update prompt to be more specific (like the improved prompts in `/tmp/prompt_validation_report.md`)

### Solution 3: Content Quality Issue

**Hypothesis**: The 2,555 characters don't contain the actual book data

**Fix**:
1. Log the extracted content to a file
2. Verify it contains "Sharp Objects" and "£47.82"
3. If not, fix the Playwright extraction selector
4. Might need to target specific elements instead of using `inner_text()`

### Solution 4: Response Parsing Issue

**Hypothesis**: LLM is returning correct data but parsing fails

**Fix**:
1. Log the raw LLM response before JSON parsing
2. Check if response format matches expected structure
3. Update `_parse_json_response()` if needed

## 🎯 IMMEDIATE ACTION PLAN

1. **Find the API route** that handles `/api/v1/extract/ultra-smart`
   ```bash
   grep -r "ultra-smart" backend/app/api/routes/ -A 10
   ```

2. **Trace which extractor it uses**
   - Should use `UltraSmartExtractor`
   - But logs show `LLMExtractor` is being used

3. **Add logging to llm_extractor** to capture:
   - Prompt being sent to LLM
   - Content preview (first 1000 chars)
   - Raw LLM response
   - Parsed JSON structure

4. **Compare with ultra_smart_extractor** behavior
   - Why isn't our debug logging appearing?
   - Is the route even calling ultra_smart_extractor?

## 📊 SUMMARY

| Component | Status | Evidence |
|-----------|--------|----------|
| OpenAI API | ✅ WORKING | RAG chat returns answers |
| Text Extraction | ✅ WORKING | 2,555 chars extracted |
| Field Parsing | ✅ WORKING | ["Book Title", "Price"] detected |
| LLM Extraction | ❌ BROKEN | Returns "—" for all fields |
| ultra_smart_extractor | ❓ UNKNOWN | Debug logs not appearing |
| llm_extractor | ✅ RUNNING | Warning logs appearing |
| Actual Prompt | ❓ UNKNOWN | Not logged yet |
| Actual LLM Response | ❓ UNKNOWN | Not logged yet |

**KEY INSIGHT**: The issue is NOT that OpenAI isn't working. The issue is that the LLM IS working but returning empty data ("—") because either:
1. The prompt is bad
2. The content doesn't contain the data
3. The response parsing is broken

**NEXT STEP**: Find and read the actual API route to understand which extractor is being used and why our debug logs aren't appearing.
