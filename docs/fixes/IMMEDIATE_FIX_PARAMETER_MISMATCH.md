# IMMEDIATE FIX: Parameter Mismatch in Tool Wrappers

**Date**: 2025-12-05
**Priority**: CRITICAL - BLOCKS ALL TOOL EXECUTION
**Status**: READY TO IMPLEMENT

---

## Problem

Current logs show:
```
❌ docling_pdf failed: got an unexpected keyword argument 'query'
❌ ocr failed: got an unexpected keyword argument 'query'
✅ document_rag succeeded
```

**Root Cause**: TaskRouter passes `query` parameter, but `docling_pdf` and `ocr` tools expect different parameter names.

---

## The Issue in Detail

### What TaskRouter Passes
```python
# enhanced_rag_agent.py calls tools with:
await tool_registry._wrap_docling_pdf(
    query="How many rooms?",           # ← THIS IS THE PROBLEM
    session_id="session-123",
    db=db,
    # ... 50+ other parameters
)
```

### What Tools Expect
```python
#  _wrap_docling_pdf signature (CURRENT - BROKEN):
async def _wrap_docling_pdf(
    self,
    file_path: str,          # Expects file_path, not query!
    session_id: str,
    db: AsyncSession
):
```

**Mismatch**: Tool expects `file_path`, but receives `query`.

---

## Solution

Make all tool wrappers accept `**kwargs` (flexible parameters) and extract what they need:

```python
async def _wrap_docling_pdf(self, **kwargs) -> Dict[str, Any]:
    """
    Extract content from PDFs using Docling

    Flexible parameter handling - accepts any combination of:
    - query/question: User's question
    - file_path: Direct path to PDF
    - session_id + db: To find PDF in session
    """

    # Extract parameters flexibly
    query = kwargs.get('query') or kwargs.get('question', '')
    session_id = kwargs.get('session_id')
    db = kwargs.get('db')
    file_path = kwargs.get('file_path')

    # If no direct file_path, find PDF in session
    if not file_path and session_id and db:
        from app.models.database import SessionDocument, Document
        from sqlalchemy import select

        result = await db.execute(
            select(Document)
            .join(SessionDocument, SessionDocument.document_id == Document.id)
            .where(SessionDocument.session_id == session_id)
            .where(Document.file_type == 'pdf')
        )
        pdf_doc = result.scalar_one_or_none()

        if pdf_doc:
            file_path = pdf_doc.file_path

    if not file_path:
        return {
            "success": False,
            "error": "No PDF file specified or found in session"
        }

    # Now proceed with docling extraction
    try:
        from app.services.document_service import DocumentService

        doc_service = DocumentService(db)
        result = await doc_service.process_with_docling(file_path)

        # Extract answer using query if provided
        if query and result.get("chunks"):
            # Use LLM to answer based on extracted content
            context = "\n\n".join(chunk["content"] for chunk in result["chunks"])

            from app.services.llm_service import llm_service
            answer = await llm_service.generate_completion(
                messages=[
                    {"role": "system", "content": "Answer based on the provided document content."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
                ],
                model=kwargs.get('model_id', 'gpt-4o-mini')
            )

            return {
                "success": True,
                "text": answer,
                "answer": answer,
                "chunks": result.get("chunks"),
                "source": "docling_pdf"
            }
        else:
            return {
                "success": True,
                "text": result.get("text", ""),
                "chunks": result.get("chunks", []),
                "source": "docling_pdf"
            }

    except Exception as e:
        logger.error(f"Docling PDF extraction failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
```

---

## Files to Modify

### 1. `_wrap_docling_pdf` (Line ~1050-1100)

**Current signature**:
```python
async def _wrap_docling_pdf(self, file_path: str, session_id: str, db: AsyncSession):
```

**New signature**:
```python
async def _wrap_docling_pdf(self, **kwargs) -> Dict[str, Any]:
```

### 2. `_wrap_ocr` (Line ~1100-1150)

**Current signature**:
```python
async def _wrap_ocr(self, file_path: str, session_id: str, db: AsyncSession):
```

**New signature**:
```python
async def _wrap_ocr(self, **kwargs) -> Dict[str, Any]:
```

### 3. `_wrap_document_rag` (Already flexible - WORKS)

This tool already works because it accepts `**kwargs`:
```python
async def _wrap_document_rag(self, **kwargs) -> Dict[str, Any]:
    query = kwargs.get('query')
    # ... works fine
```

---

## Implementation Priority

### Phase 1: IMMEDIATE (15 minutes)
Fix `_wrap_docling_pdf` and `_wrap_ocr` to accept `**kwargs`

### Phase 2: Verification (5 minutes)
Test that tools no longer throw parameter errors

### Phase 3: Enhancement (later)
Add intelligent query classification and routing (see INTELLIGENT_QUERY_ROUTING_IMPLEMENTATION_PLAN.md)

---

## Testing

After fix, this should work:
```bash
# Upload PDF
# Query: "How many rooms in the ground floor?"

Expected logs:
✅ docling_pdf succeeded (no parameter error)
✅ ocr succeeded (no parameter error)
✅ document_rag succeeded
```

---

**Status**: Ready to implement
**Estimated Time**: 20 minutes
**Impact**: CRITICAL - unblocks all tool execution

