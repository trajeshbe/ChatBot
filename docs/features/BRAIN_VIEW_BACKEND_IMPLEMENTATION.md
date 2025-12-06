# Brain View Backend Implementation

**File**: `backend/app/services/rag_service.py`
**Location**: Add code between line 678 and line 683 (before `return result`)

---

## Code to Add

Insert this code block right after the conversation message saving (after line 677) and before the caching step (line 679):

```python
            # 🧠 Step 8.5: Assemble Brain View debug context
            # Query document processing tools used for retrieved documents
            document_processing_tools = []
            if sources and db:
                try:
                    # Get document IDs from sources
                    document_ids = [src.get('id') for src in sources if src.get('id')]
                    
                    if document_ids:
                        # Query tool_usage_stats for document processing tools
                        tool_query = sql_text("""
                            SELECT 
                                tool_category,
                                tool_name,
                                operation,
                                latency_ms,
                                success,
                                quality_score,
                                error_message,
                                metadata,
                                created_at
                            FROM tool_usage_stats
                            WHERE tool_category IN ('document_processing', 'vision_service', 'ocr_service')
                              AND (metadata->>'document_id')::text = ANY(:doc_ids)
                            ORDER BY created_at DESC
                            LIMIT 50
                        """)
                        
                        tool_result = await db.execute(
                            tool_query, 
                            {'doc_ids': [str(doc_id) for doc_id in document_ids]}
                        )
                        
                        for row in tool_result:
                            metadata_json = row.metadata if hasattr(row, 'metadata') and row.metadata else {}
                            document_processing_tools.append({
                                'tool_id': f"{row.tool_name}_{hash(str(row.created_at))}",
                                'tool_name': row.tool_name.replace('_', ' ').title() if row.tool_name else 'Unknown',
                                'category': row.tool_category,
                                'operation': row.operation,
                                'status': 'success' if row.success else 'failure',
                                'latency_ms': round(row.latency_ms, 1) if row.latency_ms else 0,
                                'document_id': metadata_json.get('document_id') if isinstance(metadata_json, dict) else None,
                                'created_at': row.created_at.isoformat() if hasattr(row.created_at, 'isoformat') else str(row.created_at),
                                'quality_score': row.quality_score,
                                'error_message': row.error_message
                            })
                        
                        logger.debug(f"🧠 Brain View: Found {len(document_processing_tools)} document processing tools")
                        
                except Exception as e:
                    logger.warning(f"Could not fetch document processing tools for Brain View: {e}")
            
            # Assemble complete debug context for Brain View
            result['debug_context'] = {
                "routing_decision": {
                    "strategy": classification.get('query_type', 'unknown') if classification else 'unknown',
                    "reason": f"Query classified as {classification.get('query_type')} with {classification.get('confidence', 0):.0%} confidence" if classification else 'N/A',
                    "strategy_weights": result.get('rag_settings', {}).get('weights', {}),
                    "classification_confidence": classification.get('confidence', 0) if classification else 0
                },
                "conversation_history": {
                    "messages_used": 0,  # Frontend manages conversation history
                    "note": "Conversation history managed by frontend (sent with each request)"
                },
                "tools_executed": {
                    "query_time_tools": tools_used,  # Query execution tools (already tracked)
                    "document_processing_tools": document_processing_tools  # Tools used during document upload
                },
                "documents_retrieved": {
                    "total_chunks": len(sources),
                    "chunks": [
                        {
                            "document_id": src.get('id', 'unknown'),
                            "filename": src.get('filename', 'unknown'),
                            "similarity_score": src.get('relevance', 0.0),
                            "memory_type": src.get('memory_type', 'unknown'),
                            "content_preview": src.get('excerpt', '')[:200] + '...' if len(src.get('excerpt', '')) > 200 else src.get('excerpt', '')
                        }
                        for src in sources[:10]  # Limit to top 10 for performance
                    ]
                },
                "performance_metrics": {
                    "total_latency_ms": result.get('latency_ms', 0),
                    "breakdown": {
                        "security_check": tools_used[0]['latency_ms'] if len(tools_used) > 0 and 'Security' in tools_used[0].get('tool_name', '') else 0,
                        "embedding_generation": next((t['latency_ms'] for t in tools_used if 'Embedding' in t.get('tool_name', '')), 0),
                        "vector_search": next((t['latency_ms'] for t in tools_used if 'Search' in t.get('tool_name', '')), 0),
                        "llm_generation": next((t['latency_ms'] for t in tools_used if 'LLM' in t.get('tool_name', '') or 'Generate' in t.get('tool_name', '')), 0)
                    },
                    "model_used": result.get('model_name', result.get('model', 'unknown')),
                    "tokens_used": result.get('tokens_used', 0)
                }
            }
```

---

## Location Breakdown

**Current code structure (lines 678-683):**
```python
            )                                                    # Line 677

            # Step 9: Cache the result                          # Line 679
            if use_cache and settings.USE_SEMANTIC_CACHE:       # Line 680
                await self._cache_result(...)                   # Line 681

            return result                                        # Line 683
```

**After adding debug_context (new structure):**
```python
            )                                                    # Line 677

            # 🧠 Step 8.5: Assemble Brain View debug context    # Line 678 (NEW)
            # ... (60 lines of debug_context code)               # Lines 678-738 (NEW)

            # Step 9: Cache the result                          # Line 739 (shifted)
            if use_cache and settings.USE_SEMANTIC_CACHE:       # Line 740 (shifted)
                await self._cache_result(...)                   # Line 741 (shifted)

            return result                                        # Line 743 (shifted)
```

---

## What This Adds

1. **Document Processing Tools Query**: Queries `tool_usage_stats` table for Vision/OCR/Docling tools used on retrieved documents
2. **Complete Debug Context**: Assembles all Brain View data including:
   - Routing decisions
   - Conversation history (managed by frontend)
   - Query-time tools + Document processing tools
   - Retrieved documents with scores
   - Performance metrics breakdown

3. **Added to Response**: `result['debug_context']` will be included in the query response

---

## Testing

After implementation, test with:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=test query" \
  -F "session_id=test123" \
  -F "model=gpt-4o-mini" | jq '.debug_context'
```

Should return debug_context with all 5 sections.

---

**Status**: Ready to implement
