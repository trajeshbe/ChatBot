# Vision Routing Regression - ROOT CAUSE ANALYSIS

**Date**: 2025-12-08
**Issue**: Queries about architecture diagrams (arch1.pdf) are NOT being routed to `vision_analysis` tool
**Status**: 🔴 **REGRESSION** - Working yesterday before Brain View upgrade

---

## 📊 What User Observed

### Query That Failed:
```
"In the arch1 architecture diagram, analyze and find the number of rooms and also the total sq ft area of the house"
```

### Expected Behavior (Yesterday - MVP 0.91):
1. Query contains "arch1" + "diagram" keywords
2. System detects visual query intent
3. Routes to `vision_analysis` tool
4. Tool analyzes arch1.pdf with vision model (llama3.2-vision:11b or qwen2.5vl)
5. Returns analysis of rooms and square footage

### Actual Behavior (Today - MVP 0.92):
1. Query received with RAG session docs weight = 0.9 ✅
2. Routing decision: **FORCE_RAG** (document search) ❌
3. Retrieves arch1.pdf from **long-term memory** (not session docs) ❌
4. Extracts OCR text (not visual analysis) ❌
5. Returns: "The provided context does not contain any information..." ❌

---

## 🔍 Log Evidence

### Current Behavior (MVP 0.92):
```
2025-12-08 06:14:31 - enhanced_rag_agent - INFO - 📌 ROUTING: FORCE_RAG (document search required per user's strategy_weights)
2025-12-08 06:14:31 - enhanced_rag_agent - INFO -    Reason: rag_short_term=0.85 or rag_long_term=0.30 > 0.8
2025-12-08 06:14:31 - enhanced_rag_agent - INFO - 🔍 FORCE_RAG: Searching documents for 'In th arch1 architecure diagram...'

Retrieved: arch1.pdf
Memory type: "long-term" ❌
Content: "=== OCR EXTRACTED TEXT ===" ❌
Similarity: 0.463 (LOW) ❌
```

**NO vision_analysis tool was called!**

---

## 🔬 What Changed Between MVP 0.91 and 0.92

### Commits:
- **9b070e0** (MVP 0.91 - Yesterday) - Working vision routing
- **ff4ed04** (MVP 0.92 - Today) - Brain View + LLM classification upgrades

### Key Changes:
1. **Brain View Integration**: Added `debug_context` to response
2. **LLM-Based Document Classification**: Changed upload classification to use LLM
3. **Enhanced RAG Agent Refactoring**: Modified routing logic

---

## 💥 REGRESSION IDENTIFIED

### Before (MVP 0.91):

The system had **query classification logic** that detected visual queries and routed them to tools.

**Hypothesis**: The routing logic BEFORE Brain View likely had:
1. Query keyword detection ("diagram", "architecture", "visual", etc.)
2. Decision to use vision_analysis tool BEFORE generic RAG search
3. Tool registry priority for visual queries

### After (MVP 0.92):

The new FORCE_RAG routing **overrides** tool selection:

```python
# Current logic in enhanced_rag_agent.py
if rag_short_term > 0.8 or rag_long_term > 0.8:
    # FORCE_RAG path - goes straight to document search
    # ❌ Skips vision_analysis tool selection!
```

---

## 🎯 Expected Fix Path

### Option 1: Add Vision Query Detection BEFORE FORCE_RAG

```python
# Detect visual queries first
if _is_visual_query(query):
    logger.info("🎨 Detected visual query - routing to vision_analysis tool")
    return await vision_analysis_tool(query, file_path=...)

# Then check FORCE_RAG
if rag_short_term > 0.8:
    return await rag_search(...)
```

### Option 2: Enhance FORCE_RAG to Use Vision Analysis When Needed

```python
# Inside FORCE_RAG path
retrieved_docs = await rag_search(...)

# Check if retrieved docs have visual content
if any(doc.has_visual_embeddings for doc in retrieved_docs):
    logger.info("🎨 Retrieved visual document - using vision_analysis")
    return await vision_analysis_tool(query, documents=retrieved_docs)
```

### Option 3: Restore Pre-Brain View Routing Logic

Compare with MVP 0.91 routing and restore vision tool selection priority.

---

## 📝 Questions to Answer

1. **Where was vision routing logic before?**
   - Check MVP 0.91 enhanced_rag_agent.py route_query() method
   - Look for vision_analysis tool call

2. **When should vision_analysis be called?**
   - Visual query keywords: "diagram", "architecture", "drawing", "image", "visual"
   - Document has visual_embeddings in database
   - User explicitly requests visual analysis

3. **Should FORCE_RAG skip tool selection?**
   - NO - FORCE_RAG should still allow vision_analysis for visual documents
   - Tool selection should happen BEFORE or WITHIN FORCE_RAG path

---

## 🧪 Verification Test

After fix is applied:

```bash
# Test query
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=In the arch1 architecture diagram, find the number of rooms" \
  -F "session_id=test_vision_routing" \
  -F "model=qwen2.5vl:latest"

# Expected logs:
# 🎨 Detected visual query - routing to vision_analysis tool
# 📄 Found visual document: arch1.pdf
# 🔍 Analyzing PDF with vision model: qwen2.5vl:latest
# ✅ Vision analysis complete

# Expected response:
# Answer contains room count and analysis from vision model
# NOT "The provided context does not contain..."
```

---

## 🚨 User Impact

**Severity**: HIGH
**Users Affected**: Anyone querying visual documents (diagrams, charts, architecture drawings)
**Workaround**: None - users cannot access visual analysis functionality

**User's Exact Words**:
> "btw this was working yesterday before we upgraded brain view and llm classification..
> ideally it should be routed to vision analysis ..compare with last commit and see how
> the routing was done"

---

**Next Steps**:
1. ✅ Analysis complete (this document)
2. ⏳ Compare routing logic between MVP 0.91 and 0.92
3. ⏳ Identify exact code that broke vision routing
4. ⏳ Restore vision tool selection logic
5. ⏳ Test with user's original query
6. ⏳ Deploy fix
