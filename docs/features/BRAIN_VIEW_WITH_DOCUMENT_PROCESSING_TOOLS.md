# Brain View Implementation - Including Document Processing Tools

**Date**: 2025-12-06
**Issue**: Brain View needs to show Vision/OCR/Docling/Tesseract tools used during document processing

---

## Problem Analysis

### Two Tracking Systems

1. **`tools_used` array** (rag_service.py, in-memory):
   - Tracks RAG query execution steps (security_check, embedding_generation, vector_search, etc.)
   - Lives in memory during query execution
   - Returned in response metadata

2. **`tool_usage_stats` table** (tool_usage_tracker.py, database):
   - Tracks document processing tools (Docling, Tesseract OCR, Vision Service, etc.)
   - Persisted to database during document upload/processing
   - NOT currently included in query response

### What's Missing

When Brain View shows retrieved documents, it should also show:
- Which tools were used to process those documents (Docling, Tesseract, Vision, etc.)
- Performance metrics for those tools
- Success/failure status

---

## Solution: Hybrid Approach

### Phase 1: Query-Time Tools (Already Tracked)
**Location**: `rag_service.py` - `tools_used` array
**Includes**:
- Security Check
- Query Classification
- Embedding Generation
- Vector Search  
- Reranking
- LLM Generation

### Phase 2: Document Processing Tools (NEW - Need to Query)
**Location**: `tool_usage_stats` table
**Includes**:
- Docling (PDF parsing)
- Tesseract OCR (text extraction from images)
- Vision Service (image analysis with GPT-4 Vision/Claude)
- Hybrid Extraction Service (OCR + Vision combined)
- Multi-channel Processor (text + visual embeddings)

---

## Implementation Plan

### Backend Changes

#### File 1: `backend/app/services/rag_service.py`

**Location**: End of `query()` method, in debug_context assembly

```python
# At the end of query() method, before final return

# Get document IDs from retrieved sources
document_ids = [src.get('document_id') for src in result.get('sources', []) if src.get('document_id')]

# Query tool usage stats for these documents
document_processing_tools = []
if document_ids and db:
    try:
        from sqlalchemy import select, and_
        from app.models.database import ToolUsageStats  # Assuming this model exists
        
        # Query tools used for these documents
        query = select(ToolUsageStats).where(
            and_(
                ToolUsageStats.tool_category.in_([
                    'document_processing', 
                    'vision_service', 
                    'ocr_service'
                ]),
                ToolUsageStats.metadata['document_id'].astext.in_([str(doc_id) for doc_id in document_ids])
            )
        ).order_by(ToolUsageStats.created_at.desc())
        
        result_tools = await db.execute(query)
        tools = result_tools.scalars().all()
        
        # Format for Brain View
        for tool in tools:
            document_processing_tools.append({
                'tool_id': f"{tool.tool_name}_{tool.id}",
                'tool_name': tool.tool_name.replace('_', ' ').title(),
                'category': tool.tool_category,
                'operation': tool.operation,
                'status': 'success' if tool.success else 'failure',
                'latency_ms': round(tool.latency_ms, 1),
                'document_id': tool.metadata.get('document_id') if tool.metadata else None,
                'created_at': tool.created_at.isoformat() if tool.created_at else None,
                'quality_score': tool.quality_score,
                'error_message': tool.error_message
            })
            
    except Exception as e:
        logger.warning(f"Could not fetch document processing tools: {e}")

# Assemble debug context for Brain View
debug_context = {
    "routing_decision": {
        "strategy": result.get('metadata', {}).get('routing_strategy', 'unknown'),
        "reason": result.get('metadata', {}).get('routing_reason', 'N/A'),
        "strategy_weights": result.get('metadata', {}).get('strategy_weights', {}),
        "threshold_triggered": result.get('metadata', {}).get('routing_strategy', '') == 'conversation_only'
    },
    "conversation_history": {
        "messages_used": result.get('metadata', {}).get('conversation_messages_used', 0),
        "messages": []  # Frontend already has this from localStorage
    },
    "tools_executed": {
        "query_time_tools": tools_used,  # RAG query execution tools
        "document_processing_tools": document_processing_tools  # Tools used during document upload
    },
    "documents_retrieved": {
        "total_chunks": len(result.get('sources', [])),
        "chunks": [
            {
                "document_id": src.get('document_id', 'unknown'),
                "filename": src.get('filename', 'unknown'),
                "similarity_score": src.get('score', 0.0),
                "content_preview": src.get('content', '')[:200] + '...' if len(src.get('content', '')) > 200 else src.get('content', '')
            }
            for src in result.get('sources', [])
        ]
    },
    "performance_metrics": {
        "total_latency_ms": result.get('latency_ms', 0),
        "breakdown": {
            "security_check": tools_used[0]['latency_ms'] if len(tools_used) > 0 and tools_used[0]['tool_name'] == 'Security Check' else 0,
            "embedding_generation": next((t['latency_ms'] for t in tools_used if 'Embedding' in t['tool_name']), 0),
            "vector_search": next((t['latency_ms'] for t in tools_used if 'Search' in t['tool_name']), 0),
            "llm_generation": next((t['latency_ms'] for t in tools_used if 'LLM' in t['tool_name'] or 'Generate' in t['tool_name']), 0)
        },
        "model_used": result.get('model_used', 'unknown'),
        "tokens_used": result.get('tokens_used', 0)
    }
}

# Add debug_context to result
result['debug_context'] = debug_context
```

---

### Frontend Changes

#### File 1: `frontend/src/components/ChatInterfaceEnhanced.tsx`

**Modify the Tools & Actions Tab** to show TWO sections:

```typescript
{/* Tab 3: Tools & Actions - ENHANCED */}
<div className="mb-4">
  <h3 className="font-semibold text-sm mb-2 text-purple-700">🔧 Tools Executed</h3>
  <div className="bg-gray-50 p-3 rounded text-xs">
    
    {/* Section 1: Query-Time Tools */}
    <div className="mb-3">
      <div className="font-semibold text-xs mb-2 text-purple-600">⚡ Query Execution Tools</div>
      {brainViewData.tools_executed.query_time_tools && brainViewData.tools_executed.query_time_tools.length > 0 ? (
        brainViewData.tools_executed.query_time_tools.map((tool: any) => (
          <div key={tool.tool_id} className="mb-2 p-2 bg-white rounded border border-purple-200">
            <div className="flex justify-between items-center">
              <span className="font-medium">
                {tool.status === 'success' ? '✅' : '❌'} {tool.tool_name}
              </span>
              <span className="text-gray-500 font-mono">{tool.latency_ms.toFixed(1)}ms</span>
            </div>
            <div className="text-xs text-gray-500">Order: {tool.order}</div>
          </div>
        ))
      ) : (
        <div className="text-gray-500">No query tools executed</div>
      )}
    </div>

    {/* Section 2: Document Processing Tools (NEW) */}
    <div className="mb-3">
      <div className="font-semibold text-xs mb-2 text-blue-600">📄 Document Processing Tools</div>
      {brainViewData.tools_executed.document_processing_tools && brainViewData.tools_executed.document_processing_tools.length > 0 ? (
        <>
          <div className="text-xs text-gray-600 mb-2">
            Tools used during document upload/processing:
          </div>
          {brainViewData.tools_executed.document_processing_tools.map((tool: any) => (
            <div key={tool.tool_id} className="mb-2 p-2 bg-blue-50 rounded border border-blue-200">
              <div className="flex justify-between items-center">
                <span className="font-medium">
                  {tool.status === 'success' ? '✅' : '❌'} {tool.tool_name}
                </span>
                <span className="text-gray-500 font-mono">{tool.latency_ms.toFixed(1)}ms</span>
              </div>
              <div className="text-xs text-gray-600 mt-1">
                <div>Category: {tool.category.replace('_', ' ')}</div>
                <div>Operation: {tool.operation}</div>
                {tool.quality_score && (
                  <div className="flex items-center gap-2 mt-1">
                    <span>Quality:</span>
                    <div className="w-16 bg-gray-200 rounded-full h-1.5">
                      <div
                        className="bg-blue-500 h-1.5 rounded-full"
                        style={{ width: `${tool.quality_score * 100}%` }}
                      />
                    </div>
                    <span className="font-mono">{(tool.quality_score * 100).toFixed(0)}%</span>
                  </div>
                )}
                {tool.error_message && (
                  <div className="text-red-600 text-xs mt-1">Error: {tool.error_message}</div>
                )}
              </div>
            </div>
          ))}
        </>
      ) : (
        <div className="text-gray-500">No document processing tools used</div>
      )}
    </div>

  </div>
</div>
```

---

## Benefits

### For Users
- **Complete Visibility**: See BOTH query-time AND document-time tools
- **Tool Attribution**: Understand which tools contributed to answer quality
- **Performance Analysis**: Compare tool latencies (e.g., Docling vs PyPDF2)
- **Debugging**: Identify which OCR/Vision tools were used on diagrams/images

### For Developers
- **Tool Usage Patterns**: See which tools are actually being used
- **Quality Metrics**: Track which tools produce better results
- **Cost Attribution**: Understand Vision API costs per document
- **Performance Optimization**: Identify slow tools that need optimization

---

## Example Brain View Output

```
🔧 Tools Executed

⚡ Query Execution Tools
  ✅ Security Check (12.3ms) - Order: 1
  ✅ Embedding Generation (45.2ms) - Order: 2
  ✅ Vector Search (23.7ms) - Order: 3
  ✅ LLM Generation (892.1ms) - Order: 4

📄 Document Processing Tools
  ✅ Docling (1234.5ms)
     Category: document_processing
     Operation: parse_pdf
     Quality: ████████░░ 85%

  ✅ Vision Service (2341.2ms)
     Category: vision_service
     Operation: analyze_diagram
     Quality: ███████████ 92%

  ✅ Tesseract OCR (543.1ms)
     Category: ocr_service
     Operation: extract_text_from_image
     Quality: ██████░░░░ 67%
```

---

## Database Schema Assumption

Assuming `tool_usage_stats` table exists with:
```sql
CREATE TABLE tool_usage_stats (
    id UUID PRIMARY KEY,
    tool_category VARCHAR(50),  -- 'document_processing', 'vision_service', 'ocr_service'
    tool_name VARCHAR(100),     -- 'docling', 'tesseract', 'vision_service'
    operation VARCHAR(100),     -- 'parse_pdf', 'extract_text', 'analyze_image'
    session_id VARCHAR(255),
    user_id UUID,
    latency_ms FLOAT,
    success BOOLEAN,
    error_message TEXT,
    quality_score FLOAT,
    metadata JSONB,             -- Contains document_id reference
    created_at TIMESTAMP
);
```

---

## Implementation Timeline

1. **Backend** (15 minutes): Add document processing tools query
2. **Frontend** (10 minutes): Update Tools tab to show both sections
3. **Testing** (10 minutes): Upload document with vision, verify tools shown

**Total**: ~35 minutes

---

## Next Steps

1. Verify `tool_usage_stats` table schema matches assumptions
2. Implement backend query for document processing tools
3. Update frontend Tools tab UI
4. Test with documents that use Vision/OCR/Docling
5. Document the feature

---

**Status**: Ready to implement after schema verification
