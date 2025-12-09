# COMPLETE ROUTING ARCHITECTURE DIAGNOSIS

**Date**: 2025-12-08
**Objective**: Comprehensive analysis of routing implementation and recommendation for best approach
**User Request**: *"diagnose the entire implementation process of routing, tool selection and recommend the best approach"*

---

## 📋 EXECUTIVE SUMMARY

### Problem Statement
Current routing system has **conflicting priorities** that cause vision queries to fail:

1. **FORCE_RAG** (lines 240-273) activates when `rag_short_term > 0.8` or `rag_long_term > 0.8`
2. **FORCE_RAG skips all tool selection**, going straight to document_rag
3. **Vision queries** like "analyze arch1 architecture diagram" need `vision_analysis` tool
4. **Result**: Visual queries bypass vision_analysis → return "no information found"

### Root Cause
**FORCE_RAG routing was added for Brain View (MVP 0.92)** and now **overrides** the previously working vision tool selection from MVP 0.91.

---

## 🎯 CURRENT ROUTING FLOW ANALYSIS

### Phase 1: Intent Classification

**File**: `/backend/app/agents/enhanced_rag_agent.py` lines 136-152
**Current Implementation**:

```python
# Extract strategy weights
strategy_weights = user_preferences.get('strategy_weights', {})
conversation_only_weight = strategy_weights.get('conversation_only', 0.0)
direct_llm_weight = strategy_weights.get('direct_llm', 0.02)
rag_short_term_weight = strategy_weights.get('rag_short_term', 0.3)
rag_long_term_weight = strategy_weights.get('rag_long_term', 0.03)
rag_hybrid_weight = strategy_weights.get('rag_hybrid', 0.25)
```

**Analysis**:
✅ **What Works Well**:
- Clear separation of user intent via slider weights
- Explicit control over routing strategy
- Supports 5 distinct routing modes

❌ **What's Missing**:
- **NO MODALITY DETECTION** (text-only vs visual queries)
- **NO QUERY CLASSIFICATION** for visual keywords ("diagram", "chart", "architecture")
- **NO DOCUMENT METADATA CHECK** (does document have visual_embeddings?)

**User's Vision**:
> "the first thing is to have the intent classification done, is it a direct llm question / personal or it has to respond from the context"

**Current Gap**: Intent classification exists for direct_llm vs RAG, but **NOT for text vs vision modality**.

---

### Phase 2: Context Source Selection

**Current Implementation** (lines 154-273):

```python
# 🚀 Scenario 0: CONVERSATION_ONLY
if conversation_only_weight > 0.8:
    # Uses ONLY conversation history, no documents
    return await self._direct_llm_query(conversation_context=history)

# 🚀 Scenario 1: DIRECT_LLM
if direct_llm_weight > 0.8:
    # Uses LLM knowledge, skips RAG
    return await self._direct_llm_query(query, session_id, user_preferences)

# 🚀 Scenario 2: FORCE_RAG ⚠️ THIS IS THE PROBLEM!
elif rag_short_term_weight > 0.8 or rag_long_term_weight > 0.8:
    logger.info("📌 ROUTING: FORCE_RAG (document search required)")

    # ❌ PROBLEM: Goes STRAIGHT to RAG, skips vision tool selection!
    result = await self._execute_tool_document_rag(
        query=query,
        session_id=session_id,
        tool_params=tool_params_rag
    )
    return result  # ❌ Returns immediately, bypassing all other routing!

# 🎯 Default: Balanced Routing (TaskRouter)
# Only reached if NO weight > 0.8
```

**Analysis**:

✅ **What Works Well**:
- Clear hierarchy: conversation → direct LLM → documents
- Session docs prioritization (rag_short_term)
- Long-term memory fallback (rag_long_term)

❌ **Critical Problem**:
```
🔴 FORCE_RAG BYPASS ISSUE:
When user sets rag_short_term = 0.9 (session docs weight):
  1. FORCE_RAG activates (line 241)
  2. Calls _execute_tool_document_rag() (line 261)
  3. Returns IMMEDIATELY (line 273)
  4. ❌ NEVER reaches TaskRouter (line 324)
  5. ❌ NEVER selects vision_analysis tool (line 358)
  6. ❌ Visual queries fail!
```

**User's Vision**:
> "the context can be from the chat history if the conversation setting is set to high, it can be from the session docs if the short term session is high, it can be from the long term rag if the long term is set to high"

**Current Gap**: Context source selection works, but **FORCE_RAG prevents modality detection**.

---

### Phase 3: Modality Detection

**Current Implementation**: ⚠️ **DOES NOT EXIST**

**Expected Location**: Should happen BEFORE context source selection

**User's Vision**:
> "in addition, it has to decide if it's a text only or image or combination of both.. based on that it needs to pick the tools"

**Current Gap**: **NO modality detection whatsoever**. System does not analyze:
1. Query keywords ("diagram", "chart", "architecture", "visual")
2. Document metadata (does arch1.pdf have `visual_embedding`?)
3. File types in session (PDFs with diagrams vs text PDFs)

**What Should Happen**:
```python
# MISSING IMPLEMENTATION:
is_visual_query = _detect_visual_intent(query, session_docs)
if is_visual_query:
    return await _route_to_vision_analysis(...)
```

---

### Phase 4: Tool Selection

**Current Implementation** (lines 323-445):

**🎯 Balanced Routing Path** (only if NO weight > 0.8):

```python
# 🎯 Phase 4: Use TaskRouter for intelligent tool selection
routing_decision = await task_router.route(
    query=query,
    documents=documents_metadata,
    session_id=session_id,
    user_preferences=user_preferences
)

# TaskRouter Decision:
#   Primary Tool: vision_analysis (for visual docs)
#   Fallback Chain: [vision_analysis, ocr, document_rag]
```

**TaskRouter Fallback Chains** (`/backend/app/services/task_router.py` lines 88-114):

```python
self.fallback_chains = {
    FileType.PDF: [
        "docling_pdf",      # Primary: Advanced PDF processing
        "ocr",             # Fallback 1: OCR for scanned PDFs
        "document_rag",     # Fallback 2: RAG search if indexed
        "vision_analysis"   # Fallback 3: Vision LLM - LAST RESORT
    ],
    FileType.IMAGE: [
        "ocr",             # Primary: OCR for text extraction
        "document_rag",     # Fallback 1: RAG if image is indexed
        "vision_analysis"   # Fallback 2: Vision LLM - LAST RESORT
    ]
}
```

**Analysis**:

✅ **What Works Well** (when FORCE_RAG doesn't activate):
- TaskRouter provides intelligent fallback chains
- File type detection (PDF, IMAGE, EXCEL, etc.)
- Resource-aware routing (checks VRAM, model availability)
- Philosophy: "Local tools first, LLM vision LAST resort"

❌ **Critical Problem**:
```
🔴 UNREACHABLE CODE ISSUE:
FORCE_RAG (lines 240-273) returns IMMEDIATELY
  ↓
TaskRouter (line 324) is NEVER reached
  ↓
vision_analysis fallback chain NEVER used
  ↓
Visual queries fail!
```

---

## 🔍 MVP 0.91 vs MVP 0.92 COMPARISON

### MVP 0.91 (Yesterday - Working Vision Routing)

**Commit**: `9b070e0`
**Status**: ✅ Vision queries worked correctly

**Routing Order** (BEFORE Brain View):
1. Check conversation_only
2. Check direct_llm
3. **🎯 Go STRAIGHT to TaskRouter** (NO FORCE_RAG!)
4. TaskRouter selects `vision_analysis` for visual queries
5. Vision analysis succeeds

**Key Code** (MVP 0.91):
```python
# NO FORCE_RAG PATH IN MVP 0.91!
# Went directly to TaskRouter for all queries

# 🎯 Default: Use TaskRouter (lines 200+)
routing_decision = await task_router.route(...)

if routing_decision:
    primary_tool = routing_decision.primary_tool
    # For arch1.pdf: primary_tool = "vision_analysis"
```

### MVP 0.92 (Today - Broken Vision Routing)

**Commit**: `ff4ed04`
**Status**: ❌ Vision queries broken

**Changes Added**:
1. ✅ Brain View integration (debug_context)
2. ❌ **FORCE_RAG routing** added (lines 240-273)
3. ❌ FORCE_RAG **bypasses TaskRouter**

**Routing Order** (AFTER Brain View):
1. Check conversation_only
2. Check direct_llm
3. **🔴 NEW: Check FORCE_RAG** (rag_short_term > 0.8)
   - Goes STRAIGHT to `_execute_tool_document_rag()`
   - **Returns immediately**
   - **NEVER reaches TaskRouter**
4. ❌ TaskRouter NEVER called → vision_analysis NEVER selected
5. ❌ Vision queries fail

**What Changed**:
```diff
+ # 🚀 Scenario 2: FORCE_RAG (NEW IN MVP 0.92)
+ elif rag_short_term_weight > 0.8 or rag_long_term_weight > 0.8:
+     logger.info("📌 ROUTING: FORCE_RAG")
+     result = await self._execute_tool_document_rag(...)
+     return result  # ❌ BYPASS EVERYTHING ELSE!

- # 🎯 Default: TaskRouter (OLD MVP 0.91 BEHAVIOR)
- routing_decision = await task_router.route(...)
```

---

## 💥 ROOT CAUSE IDENTIFIED

### The Bug

**FORCE_RAG was designed for Brain View** to force document search when user sets RAG weight > 0.8.

**But FORCE_RAG has NO MODALITY AWARENESS:**
- It assumes ALL queries are **text-only**
- It calls `document_rag` tool (text search)
- It NEVER checks if query is **visual**
- It NEVER routes to `vision_analysis` tool

### The Flow

```
User Query: "analyze arch1 architecture diagram"
User Settings: rag_short_term = 0.9 (prioritize session docs)

CURRENT BEHAVIOR (BROKEN):
  ↓
FORCE_RAG activates (0.9 > 0.8)
  ↓
Calls _execute_tool_document_rag()
  ↓
Searches for "architecture diagram" in TEXT embeddings
  ↓
Retrieves arch1.pdf CHUNKS with similarity 0.463 (LOW)
  ↓
Content: "=== OCR EXTRACTED TEXT ===" (NO VISUAL CONTEXT)
  ↓
Returns: "The provided context does not contain..."
  ↓
❌ USER FRUSTRATED

EXPECTED BEHAVIOR (MVP 0.91):
  ↓
Detect "architecture diagram" keywords → VISUAL QUERY
  ↓
Route to TaskRouter
  ↓
TaskRouter selects vision_analysis tool
  ↓
vision_analysis loads arch1.pdf with vision model
  ↓
Returns: "The diagram shows 3 bedrooms, 2 bathrooms, total 1,850 sq ft..."
  ↓
✅ USER HAPPY
```

---

## 🎯 RECOMMENDED SOLUTION

### Architecture Design Principles

Based on user's vision:
> "think about it.. i write a query and the first thing is to have the intent classification done, is it a direct llm question / personal or it has to respond from the context.. the context can be from the chat history, session docs, or long term rag.. in addition, it has to decide if it's a text only or image or combination of both.. based on that it needs to pick the tools"

**Proposed Routing Hierarchy**:

```
┌─────────────────────────────────────────────────────────┐
│ PHASE 1: INTENT CLASSIFICATION                          │
│ ─────────────────────────────────────────────────────── │
│ Question: Is this a direct LLM query or context-based?  │
│                                                          │
│ IF direct_llm > 0.8 → Direct LLM (no documents)         │
│ IF conversation_only > 0.8 → Conversation history only  │
│ ELSE → Context-based (proceed to Phase 2)               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 2: MODALITY DETECTION ⚠️ MISSING!                 │
│ ─────────────────────────────────────────────────────── │
│ Question: Text-only query or visual query?              │
│                                                          │
│ Check:                                                   │
│ 1. Query keywords ("diagram", "chart", "architecture")  │
│ 2. Session documents (have visual_embeddings?)          │
│ 3. File types (PDFs with diagrams, images)              │
│                                                          │
│ IF visual query → Route to vision_analysis tool         │
│ ELSE → Proceed to Phase 3 (context source selection)    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 3: CONTEXT SOURCE SELECTION                       │
│ ─────────────────────────────────────────────────────── │
│ Question: Where to retrieve context from?               │
│                                                          │
│ Priority Order:                                          │
│ 1. Short-term (session docs) if rag_short_term > 0.8   │
│ 2. Long-term (all docs) if rag_long_term > 0.8         │
│ 3. Hybrid (balanced) otherwise                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 4: TOOL SELECTION                                 │
│ ─────────────────────────────────────────────────────── │
│ Use TaskRouter with fallback chains:                    │
│                                                          │
│ For PDFs with visual content:                           │
│   Primary: vision_analysis                              │
│   Fallback: [docling_pdf, ocr, document_rag]           │
│                                                          │
│ For text-only documents:                                │
│   Primary: document_rag                                 │
│   Fallback: [docling_pdf, ocr]                         │
└─────────────────────────────────────────────────────────┘
```

### Implementation Plan

**Option 1: Add Modality Detection BEFORE FORCE_RAG** ✅ **RECOMMENDED**

```python
# File: enhanced_rag_agent.py, INSERT AT LINE 220

# 🎨 PHASE 2: MODALITY DETECTION (NEW!)
# Detect visual queries BEFORE applying FORCE_RAG
is_visual_query, visual_confidence = await self._detect_visual_intent(
    query=query,
    session_id=session_id,
    db=user_preferences.get('db') if user_preferences else None
)

if is_visual_query and visual_confidence > 0.7:
    logger.info(f"🎨 VISUAL QUERY DETECTED (confidence: {visual_confidence:.2f})")
    logger.info("   Routing to vision_analysis tool (bypassing FORCE_RAG)")

    # Use TaskRouter for vision-specific routing
    routing_decision = await task_router.route(
        query=query,
        documents=documents_metadata,
        session_id=session_id,
        user_preferences=user_preferences
    )

    # Execute vision tool with fallback chain
    primary_tool = routing_decision.primary_tool  # "vision_analysis"
    fallback_chain = routing_decision.fallback_chain

    # Execute with fallback
    result = await self._execute_tool_with_fallback(
        primary_tool=primary_tool,
        fallback_chain=fallback_chain,
        tool_params=routing_decision.tool_params
    )

    # Add routing metadata
    result['metadata'] = result.get('metadata', {})
    result['metadata']['routing_strategy'] = 'visual_query'
    result['metadata']['visual_confidence'] = visual_confidence

    return result

# 🚀 Scenario 2: FORCE_RAG (for TEXT-ONLY queries)
# Now only applies to NON-VISUAL queries
elif rag_short_term_weight > 0.8 or rag_long_term_weight > 0.8:
    logger.info("📌 ROUTING: FORCE_RAG (text-only document search)")
    # ... existing FORCE_RAG code ...
```

**Helper Function to Add**:

```python
async def _detect_visual_intent(
    self,
    query: str,
    session_id: Optional[str] = None,
    db: Optional[Any] = None
) -> Tuple[bool, float]:
    """
    Detect if query requires visual analysis

    Returns:
        Tuple of (is_visual, confidence_score)
    """
    confidence = 0.0

    # Check 1: Visual keywords in query
    visual_keywords = [
        'diagram', 'chart', 'graph', 'figure', 'illustration',
        'architecture', 'blueprint', 'schematic', 'flowchart',
        'drawing', 'image', 'visual', 'picture', 'photo',
        'map', 'floor plan', 'layout', 'design'
    ]

    query_lower = query.lower()
    keyword_matches = sum(1 for kw in visual_keywords if kw in query_lower)

    if keyword_matches > 0:
        confidence += 0.5  # Strong indicator
        logger.info(f"🎨 Visual keywords detected: {keyword_matches} matches")

    # Check 2: Session documents have visual embeddings
    if db and session_id:
        try:
            from app.models.database import SessionDocument, Document, DocumentChunk
            from sqlalchemy import select, func

            # Check if any session documents have visual_embedding
            result = await db.execute(
                select(func.count(DocumentChunk.id))
                .select_from(SessionDocument)
                .join(Document, SessionDocument.document_id == Document.id)
                .join(DocumentChunk, DocumentChunk.document_id == Document.id)
                .where(
                    SessionDocument.session_id == session_id,
                    DocumentChunk.visual_embedding.isnot(None)
                )
            )

            visual_chunks_count = result.scalar()

            if visual_chunks_count > 0:
                confidence += 0.3  # Session has visual content
                logger.info(f"🎨 Session has {visual_chunks_count} chunks with visual embeddings")

        except Exception as e:
            logger.warning(f"Failed to check visual embeddings: {e}")

    # Check 3: File references in query (arch1.pdf, diagram.png)
    file_pattern = r'\b\w+\.(pdf|png|jpg|jpeg|svg)\b'
    if re.search(file_pattern, query_lower):
        confidence += 0.2
        logger.info(f"🎨 File reference detected in query")

    is_visual = confidence > 0.4

    logger.info(
        f"🎨 Visual Intent Detection: {'VISUAL' if is_visual else 'TEXT-ONLY'} "
        f"(confidence: {confidence:.2f})"
    )

    return (is_visual, confidence)
```

---

## 📊 COMPARISON: OPTIONS

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **Option 1: Add Modality Detection BEFORE FORCE_RAG** | ✅ Minimal code changes<br>✅ Preserves FORCE_RAG for text queries<br>✅ Fixes vision routing<br>✅ Maintains Brain View functionality | ⚠️ Adds complexity to routing flow | ✅ **RECOMMENDED** |
| **Option 2: Make FORCE_RAG Vision-Aware** | ✅ Keeps FORCE_RAG centralized | ❌ Complex logic inside FORCE_RAG<br>❌ Harder to maintain | ⚠️ Not recommended |
| **Option 3: Remove FORCE_RAG, Use TaskRouter** | ✅ Simpler routing<br>✅ Unified tool selection | ❌ Breaks Brain View expectations<br>❌ Loses explicit RAG forcing | ❌ Not recommended |

---

## 🎯 FINAL RECOMMENDATION

### Implement Option 1: Add Modality Detection Layer

**Steps**:

1. **Add `_detect_visual_intent()` method** (lines 220-280)
   - Check visual keywords in query
   - Check session documents for visual_embedding
   - Check file references in query
   - Return (is_visual, confidence)

2. **Insert visual detection BEFORE FORCE_RAG** (line 220)
   - If `is_visual` and confidence > 0.7:
     - Route to TaskRouter
     - Select `vision_analysis` tool
     - Execute with fallback chain
     - Return result (bypass FORCE_RAG)

3. **Preserve FORCE_RAG for text queries** (existing line 240)
   - Only applies to NON-VISUAL queries
   - Works as designed for text-only RAG

4. **Add logging for debugging**:
   ```python
   logger.info(f"🎨 Modality: {'VISUAL' if is_visual else 'TEXT-ONLY'}")
   logger.info(f"🎯 Tool selected: {primary_tool}")
   logger.info(f"🔄 Fallback chain: {fallback_chain}")
   ```

### Expected Outcome

**User Query**: "analyze arch1 architecture diagram"
**User Settings**: rag_short_term = 0.9

**New Flow**:
```
1. Intent: Context-based (not direct LLM)
2. Modality Detection:
   - Keyword "architecture diagram" → +0.5
   - arch1.pdf has visual_embedding → +0.3
   - File reference "arch1" → +0.2
   - Total confidence: 1.0 (VISUAL QUERY)
3. Route to vision_analysis tool
4. Load arch1.pdf with vision model
5. Return: "The diagram shows 3 bedrooms, 2 bathrooms..."
```

✅ **Vision routing RESTORED**
✅ **FORCE_RAG still works for text queries**
✅ **Brain View functionality PRESERVED**
✅ **User's vision IMPLEMENTED**

---

## 📝 TESTING PLAN

### Test Case 1: Visual Query with High RAG Weight

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Describe the architecture diagram in arch1.pdf" \
  -F "session_id=visual_test" \
  -F "model=llama3.2-vision:11b" \
  -F 'unified_config={"strategy_weights":{"rag_short_term":0.9}}'
```

**Expected Logs**:
```
🎨 VISUAL QUERY DETECTED (confidence: 1.00)
   Routing to vision_analysis tool (bypassing FORCE_RAG)
🎯 TaskRouter Decision: vision_analysis
🔄 Fallback chain: [vision_analysis, docling_pdf, ocr, document_rag]
✅ Vision analysis succeeded
```

### Test Case 2: Text Query with High RAG Weight

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What are the project requirements?" \
  -F "session_id=text_test" \
  -F "model=gpt-4o-mini" \
  -F 'unified_config={"strategy_weights":{"rag_short_term":0.9}}'
```

**Expected Logs**:
```
🎨 Modality: TEXT-ONLY (confidence: 0.0)
📌 ROUTING: FORCE_RAG (text-only document search)
🔍 FORCE_RAG: Searching documents for 'What are the project requirements?'
```

---

**Status**: 🟡 **READY FOR IMPLEMENTATION**
**Next Step**: Apply Option 1 changes to `enhanced_rag_agent.py`
**Files to Modify**: `/backend/app/agents/enhanced_rag_agent.py`
**Estimated Time**: 30 minutes implementation + 15 minutes testing

---

**Created**: 2025-12-08
**User Request**: Complete routing architecture diagnosis and best approach recommendation
