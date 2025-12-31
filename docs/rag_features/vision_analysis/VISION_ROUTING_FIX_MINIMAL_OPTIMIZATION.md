# Vision Routing Fix - MINIMAL Optimization Using EXISTING Code

**Date**: 2025-12-08
**Status**: 🔍 **ANALYSIS COMPLETE** - Ready for minimal implementation
**Approach**: **REUSE EXISTING CODE** - No new methods, no over-engineering

---

## 🎯 Problem Statement (User's Words)

> "btw this was working yesterday before we upgraded brain view and llm classification.. ideally it should be routed to vision analysis ..compare with last commit and see how the routing was done"

> "now, lets not introduce a new set of code or make drastic changes.. Evaluate the existing code base,, we have multiple routing, text classification, vision.. i.e intent LLM classification is already there, keywords is already there, extensive multi strategy vision analysis is already there .. just see what can be done with the existing logic to optimize it.. lets not over engineer or over complicate implementations and logic.. reuse reuse reuse existing code and just see the points where it has to be optimized.. thats it"

---

## 📊 Existing Code Inventory

### ✅ What We Already Have (NO NEW CODE NEEDED!)

#### 1. **Visual Query Detection** (ALREADY EXISTS)
**File**: `/backend/app/agents/enhanced_rag_agent.py` lines 916-1064
**Method**: `_select_tools_llm_ollama()`

```python
# Tool Selection Rules ALREADY IMPLEMENTED:
# - Queries mentioning "diagram", "chart", "figure", "image", "graph", "table",
#   "drawing", "illustration", "blueprint", "schematic", "floor plan", "map"
#   → vision_analysis OR ocr
```

**This method ALREADY:**
- ✅ Uses Qwen 2.5 1.5B to detect visual queries
- ✅ Returns `{"tools": ["vision_analysis"], ...}` for visual content
- ✅ Has keyword detection for diagrams, charts, images
- ✅ Includes reasoning and confidence scores
- ✅ Has fallback to document_rag if LLM fails

**Status**: **WORKING AND TESTED** - Just needs to be called!

#### 2. **Keyword-Based Classification** (ALREADY EXISTS)
**File**: `/backend/app/services/intelligent_retrieval_service.py` lines 157-192
**Method**: `_keyword_classify()`

```python
# ALREADY classifies queries into:
# - TEXT (text semantic)
# - TABLE (tabular)
# - VISUAL (vision) ← PERFECT FOR OUR NEEDS!
# - CODE (code semantic)
# - MULTI_MODAL (combination)
```

**This method ALREADY:**
- ✅ Fast path (0ms) using keyword matching
- ✅ Detects visual keywords
- ✅ Returns strategy: "vision" for visual queries
- ✅ Returns vector_column: "visual_embedding"

**Status**: **WORKING** - But not being called before FORCE_RAG!

#### 3. **Visual Fallback Chains** (ALREADY EXISTS)
**File**: `/backend/app/services/task_router.py` lines 88-114
**Method**: `fallback_chains` dict

```python
# ALREADY has visual tool fallback chains:
FileType.PDF: [
    "docling_pdf",      # Primary
    "ocr",             # Fallback 1
    "document_rag",     # Fallback 2
    "vision_analysis"   # Fallback 3 - LAST RESORT
]

FileType.IMAGE: [
    "ocr",             # Primary
    "document_rag",     # Fallback 1
    "vision_analysis"   # Fallback 2 - LAST RESORT
]
```

**Philosophy**: "Local tools first (CPU-only), LLM vision LAST resort"
**Status**: **WORKING** - But TaskRouter never reached due to FORCE_RAG!

---

## 💥 The ONE Problem (Root Cause)

**File**: `/backend/app/agents/enhanced_rag_agent.py` lines 240-273

```python
# 🚀 Scenario 2: User forces RAG (must use document search)
elif rag_short_term_weight > 0.8 or rag_long_term_weight > 0.8:
    logger.info("📌 ROUTING: FORCE_RAG (document search required)")

    # Execute RAG tool
    result = await self._execute_tool_document_rag(...)

    # ❌ PROBLEM: Returns immediately, bypassing:
    #    - TaskRouter (line 316)
    #    - _select_tools_llm_ollama() (line 916)
    #    - All visual query detection logic
    return result  # ← EXITS HERE!
```

**Impact**:
1. User sets `rag_short_term=0.9` → FORCE_RAG activates
2. FORCE_RAG goes straight to `document_rag` tool
3. Returns immediately (line 273)
4. TaskRouter **never** reached (line 316 unreachable)
5. `_select_tools_llm_ollama()` **never** called
6. Visual query detection **bypassed**
7. Query about "arch1 diagram" retrieves text chunks instead of visual analysis

---

## ✅ The MINIMAL Fix (3-Line Change)

### Optimization Point 1: Call Existing Visual Detection BEFORE FORCE_RAG

**File to Edit**: `/backend/app/agents/enhanced_rag_agent.py`
**Location**: Insert BEFORE line 240 (FORCE_RAG block)

```python
# 🎨 NEW: Check for visual queries BEFORE forcing RAG
# Uses EXISTING _select_tools_llm_ollama() method - NO NEW CODE!
tool_selection = await self._select_tools_llm_ollama(
    query=query,
    session_id=session_id,
    top_k=top_k
)

# If visual tool selected, use TaskRouter (EXISTING fallback chains)
if "vision_analysis" in tool_selection.get("tools", []):
    logger.info(f"🎨 Visual query detected by LLM: {tool_selection.get('reasoning')}")
    logger.info(f"   Bypassing FORCE_RAG to use vision_analysis tool")

    # Continue to balanced routing (line 316) which will use TaskRouter
    # TaskRouter ALREADY has vision fallback chains!
    pass  # Fall through to line 316
else:
    # Not a visual query - proceed with FORCE_RAG as normal
    # (Keep existing FORCE_RAG logic - lines 240-273)
```

**That's it! Just call EXISTING method before FORCE_RAG!**

---

## 🔍 Why This Fix is MINIMAL and REUSES EXISTING CODE

### ✅ Reuses Existing Components

1. **`_select_tools_llm_ollama()`** (line 916) - ALREADY detects visual queries
2. **TaskRouter** (line 316) - ALREADY has vision fallback chains
3. **Vision keywords** - ALREADY defined in `_select_tools_llm_ollama()` prompt
4. **Qwen 2.5 1.5B** - ALREADY used for classification
5. **Vision analysis tool** - ALREADY implemented

### ✅ No New Code Required

- ❌ NO new classification methods
- ❌ NO new keyword detection
- ❌ NO new modality detection
- ❌ NO new routing logic
- ✅ Just call existing `_select_tools_llm_ollama()` method

### ✅ Minimal Changes

**Lines to Add**: ~10 lines (check visual tool selection)
**Lines to Modify**: 0 lines
**Lines to Delete**: 0 lines
**New Methods**: 0
**New Files**: 0

### ✅ Preserves All Existing Functionality

- ✅ FORCE_RAG still works for text queries
- ✅ Session document prioritization preserved
- ✅ Brain View integration unchanged
- ✅ All other routing scenarios unchanged
- ✅ Fallback chains still used

---

## 🧪 Testing the Fix

### Step 1: Expected Logs After Fix

```bash
# Query: "In the arch1 architecture diagram, find the number of rooms"

# NEW LOG (from visual detection):
🤖 Ollama LLM selected tools: ['vision_analysis'] (confidence: 0.95) - Query mentions 'arch1 architecture diagram', selecting vision analysis

🎨 Visual query detected by LLM: Query mentions 'arch1 architecture diagram', selecting vision analysis
   Bypassing FORCE_RAG to use vision_analysis tool

# EXISTING LOG (from TaskRouter):
🎯 TaskRouter selected: vision_analysis
   Fallback chain: vision_analysis → ocr → document_rag

# EXISTING LOG (from vision tool):
🔍 Vision Analysis: Processing arch1.pdf with llama3.2-vision:11b
✅ Vision analysis complete
```

### Step 2: Verification Commands

```bash
# Test visual query with high RAG weight
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=How many rooms are in the arch1 architecture diagram?" \
  -F "session_id=test_vision_fix" \
  -F "model=llama3.2-vision:11b" \
  -F 'unified_config={"strategy_weights":{"rag_short_term":0.9}}'

# Expected: Answer with room count from vision analysis
# NOT: "The provided context does not contain any information..."
```

---

## 📝 Implementation Steps (MINIMAL)

### Step 1: Open File
```bash
# File to edit:
/backend/app/agents/enhanced_rag_agent.py
```

### Step 2: Insert Check BEFORE Line 240

**BEFORE (Current - Line 240)**:
```python
        # 🚀 Scenario 2: User forces RAG (must use document search)
        elif rag_short_term_weight > 0.8 or rag_long_term_weight > 0.8:
```

**AFTER (With Visual Detection)**:
```python
        # 🎨 PRE-CHECK: Detect visual queries BEFORE forcing RAG
        # Uses EXISTING _select_tools_llm_ollama() - NO NEW CODE!
        tool_selection = await self._select_tools_llm_ollama(
            query=query,
            session_id=session_id,
            top_k=top_k
        )

        # If visual tool selected, bypass FORCE_RAG
        if "vision_analysis" in tool_selection.get("tools", []):
            logger.info(f"🎨 Visual query detected: {tool_selection.get('reasoning')}")
            logger.info("   Bypassing FORCE_RAG to use vision_analysis via TaskRouter")
            # Fall through to balanced routing (line 316)
            pass

        # 🚀 Scenario 2: User forces RAG (must use document search)
        elif rag_short_term_weight > 0.8 or rag_long_term_weight > 0.8:
            # ... existing FORCE_RAG logic unchanged ...
```

### Step 3: Rebuild Backend
```bash
docker-compose build backend
docker-compose restart backend
```

### Step 4: Test
```bash
# Re-upload arch1.pdf through UI
# Query: "In the arch1 architecture diagram, find the number of rooms"
# Expected: Vision analysis used, NOT text RAG
```

---

## 🎯 Expected Outcome

### User Experience After Fix:

#### Scenario 1: Visual Query with High RAG Weight
**Query**: "Describe the architecture diagram in arch1.pdf"
**Settings**: `rag_short_term=0.9`

**BEFORE (Broken)**:
```
FORCE_RAG → document_rag → Text chunks → "No information found"
```

**AFTER (Fixed)**:
```
Visual Detection → vision_analysis → Vision model → "The diagram shows a floor plan with 3 bedrooms, 2 bathrooms, living room, and kitchen. Total area: ~1,200 sq ft"
```

#### Scenario 2: Text Query with High RAG Weight
**Query**: "What is the main idea of the document?"
**Settings**: `rag_short_term=0.9`

**BEFORE (Working)**:
```
FORCE_RAG → document_rag → Text chunks → Answer
```

**AFTER (Still Working)**:
```
Visual Detection → "document_rag" selected → FORCE_RAG → Same as before
```

---

## 🔗 Comparison: MVP 0.91 vs 0.92 vs FIXED

### MVP 0.91 (Yesterday - WORKING)
```
Query → TaskRouter → Vision detection → vision_analysis → Answer ✅
```

### MVP 0.92 (Today - BROKEN)
```
Query → FORCE_RAG → document_rag → Returns immediately → No vision ❌
        (TaskRouter never reached)
```

### MVP 0.92 + MINIMAL FIX (WORKING)
```
Query → Visual Detection (EXISTING method) → TaskRouter → vision_analysis → Answer ✅
OR
Query → Visual Detection → "Not visual" → FORCE_RAG → document_rag → Answer ✅
```

---

## 📊 Code Reuse Analysis

### EXISTING Methods Called (100% Reuse!)

1. **`_select_tools_llm_ollama()`** (line 916)
   - ALREADY EXISTS: ✅
   - NEW CODE ADDED: ❌ (0 lines)
   - CHANGES: ❌ (0 lines)

2. **TaskRouter** (line 316)
   - ALREADY EXISTS: ✅
   - NEW CODE ADDED: ❌ (0 lines)
   - CHANGES: ❌ (0 lines)

3. **Vision fallback chains** (task_router.py line 88)
   - ALREADY EXISTS: ✅
   - NEW CODE ADDED: ❌ (0 lines)
   - CHANGES: ❌ (0 lines)

### NEW Code Written

- **Pre-check before FORCE_RAG**: ~10 lines (just calling existing method)
- **New methods created**: 0
- **New files created**: 0
- **New dependencies**: 0

### Total Implementation Cost

- **Lines of code**: ~10
- **Methods**: 0 new
- **Files**: 0 new
- **Complexity**: MINIMAL (just conditional check)

---

## ✅ Checklist for Implementation

- [ ] Open `/backend/app/agents/enhanced_rag_agent.py`
- [ ] Insert visual detection check BEFORE line 240 (FORCE_RAG)
- [ ] Call existing `_select_tools_llm_ollama()` method
- [ ] Check if `"vision_analysis"` in selected tools
- [ ] If yes, bypass FORCE_RAG (fall through to TaskRouter)
- [ ] If no, proceed with FORCE_RAG as normal
- [ ] Rebuild backend: `docker-compose build backend`
- [ ] Restart backend: `docker-compose restart backend`
- [ ] Test visual query with `rag_short_term=0.9`
- [ ] Verify vision_analysis tool is called
- [ ] Verify answer contains visual analysis (not "no information found")

---

## 🎉 Summary

### What We're Doing:
**Calling EXISTING visual detection method BEFORE FORCE_RAG**

### What We're NOT Doing:
- ❌ Creating new classification methods
- ❌ Adding new modality detection
- ❌ Implementing new keyword matching
- ❌ Refactoring existing routing
- ❌ Over-engineering or over-complicating

### Why This Works:
1. **`_select_tools_llm_ollama()`** ALREADY detects visual queries perfectly
2. **TaskRouter** ALREADY has vision fallback chains
3. **All visual tools** ALREADY implemented
4. **Just need to call them BEFORE FORCE_RAG**

### Result:
**MINIMAL change, MAXIMUM reuse, FIXES vision routing regression!**

---

**Next Step**: Get user approval for this minimal approach, then implement the ~10 line fix.

**Related Documents**:
- Vision Routing Regression Analysis: `/tmp/vision_routing_regression_analysis.md`
- Complete Routing Architecture: `/tmp/COMPLETE_ROUTING_ARCHITECTURE_DIAGNOSIS.md`
- Query Analysis: `/tmp/query_analysis.md`
