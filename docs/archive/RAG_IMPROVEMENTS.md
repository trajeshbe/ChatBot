# RAG Pipeline Improvements - November 2025

## Overview
This document outlines the improvements made to the RAG (Retrieval-Augmented Generation) pipeline to enhance response quality and source attribution accuracy.

## Problems Identified

Based on analysis of query outputs, the following issues were identified:

1. **Irrelevant Document Retrieval**
   - Documents with low relevance (e.g., Thoothukudi Wikipedia) appearing in unrelated queries
   - Cascading fallback too aggressive (70% → 55% → 30%), allowing low-quality matches

2. **Source Over-Attribution**
   - All retrieved chunks shown as sources, even if not used in the answer
   - No quality threshold for displaying sources
   - Example: "Tom Clark" query retrieved Thoothukudi doc despite answer saying "no information found"

3. **Inconsistent RAG Quality**
   - RAG scores varying widely (44% to 87%)
   - No post-processing to filter low-quality sources

4. **Context Quality**
   - All chunks above minimum threshold passed to LLM, including marginal matches
   - No distinction between high-quality and acceptable sources

## Solutions Implemented

### 1. Configuration Updates (`backend/app/core/config.py`)

**Changes:**
- Increased `SIMILARITY_THRESHOLD`: 0.70 → **0.75** (75% for higher quality)
- Increased `MIN_SIMILARITY_THRESHOLD`: 0.55 → **0.60** (60% minimum)
- Added `HIGH_QUALITY_SOURCE_THRESHOLD`: **0.75** (only show sources above 75% confidence)
- Added `SOURCE_DISPLAY_THRESHOLD`: **0.70** (minimum to display a source)
- Increased `NO_RELEVANT_DOCS_THRESHOLD`: 0.65 → **0.70** (stricter document relevance check)

**Impact:**
- Higher quality baseline for all retrievals
- Stricter filtering prevents irrelevant documents
- Clear thresholds for source quality tiers

### 2. RAG Service Enhancements (`backend/app/services/rag_service.py`)

#### a. High-Quality Source Filtering

**Added Method: `_filter_high_quality_sources()`**
```python
def _filter_high_quality_sources(self, sources: List[Dict]) -> List[Dict]:
    """
    Filter sources to only include high-quality matches.
    High-quality sources are those with relevance scores above the threshold.
    """
    high_quality = [
        source for source in sources
        if source['relevance'] >= settings.HIGH_QUALITY_SOURCE_THRESHOLD
    ]
    return sorted(high_quality, key=lambda x: x['relevance'], reverse=True)
```

**Impact:**
- Only sources ≥75% confidence are shown as "high quality"
- Reduces false source attribution
- Improves user trust in source citations

#### b. Tiered Source Display Logic

**Updated: Source filtering in `query()` method**
- Tier 1: Show high-quality sources (≥75%) if available
- Tier 2: Show sources above display threshold (≥70%) if no high-quality sources
- Tier 3: Show top 2 sources as last resort

**Impact:**
- Prioritizes best sources
- Gracefully degrades when no high-quality sources available
- Always provides some context when documents exist

#### c. Context Quality Filtering

**Updated: LLM context preparation**
```python
# Further filter to only use high-quality chunks for LLM context
context_threshold = settings.SOURCE_DISPLAY_THRESHOLD
high_quality_chunks = [
    chunk for chunk in filtered_chunks
    if chunk.get('similarity', 0) >= context_threshold
]
chunks_for_context = high_quality_chunks if high_quality_chunks else filtered_chunks
```

**Impact:**
- LLM only sees chunks ≥70% relevance
- Reduces noise in LLM context
- Improves answer accuracy

### 3. Document Service Improvements (`backend/app/services/document_service.py`)

#### a. Conservative Cascading Fallback

**Before:**
```python
# Tried 3 levels: [threshold, threshold-0.1, MIN_THRESHOLD]
# Example: [0.70, 0.60, 0.30]
```

**After:**
```python
# Only 1 fallback level: [threshold, MIN_THRESHOLD]
# Example: [0.75, 0.60]
```

**Impact:**
- Prevents low-quality matches (eliminated 30% fallback)
- More conservative retrieval
- Better precision, acceptable recall trade-off

#### b. Enhanced Chunk Diversification

**Updated: `_diversify_chunks()` method**
- Added quality filtering: Only include chunks ≥ SOURCE_DISPLAY_THRESHOLD (70%)
- Sort by similarity descending
- Better logging of diversification results

**Impact:**
- No low-quality chunks in diversified results
- Best sources appear first
- Variety across documents maintained

### 4. LLM Prompt Improvements (`backend/app/services/llm_service.py`)

#### Updated `generate_with_context()` Prompt

**Before:**
```
System: "You are a helpful AI assistant with access to relevant documents..."
Context: "Source 1 (unknown):\n{content}"
```

**After:**
```
System: "You are a helpful AI assistant...
IMPORTANT RULES:
1. Use ONLY information from the provided sources
2. Always cite your sources using [Source N] notation
3. Do not make up information
4. Focus on the most relevant sources (higher relevance scores)
5. Be concise and accurate"

Context: "Source 1 - filename.pdf (Relevance: 85%):\n{content}"
```

**Impact:**
- Clearer instructions to LLM to only use provided sources
- Relevance scores help LLM prioritize sources
- Better source citation behavior
- Reduced hallucination risk

## Expected Improvements

### Quality Metrics

| Metric | Before | After (Expected) |
|--------|--------|------------------|
| Average RAG Score | 60-70% | 75-85% |
| Source Precision | ~60% | ~85% |
| Irrelevant Retrievals | Common | Rare |
| High-Quality Sources | ~50% | ~80% |

### Query-Specific Improvements

1. **"Tell me about yourself"**
   - Before: Retrieved Thoothukudi doc (44% RAG score)
   - After: Skips RAG entirely, no irrelevant sources

2. **"Tom Clark"** (not in documents)
   - Before: Retrieved Thoothukudi doc (70% RAG score)
   - After: No sources shown (or only if highly relevant)

3. **"TCS September results"**
   - Before: Retrieved Thoothukudi + TCS docs (57% RAG score)
   - After: Only TCS press release if relevant, higher quality threshold

4. **"Summarize TCS Press Release"**
   - Before: Retrieved Thoothukudi + TCS docs (73% RAG score)
   - After: Only TCS press release (high quality), better score

## Testing Recommendations

### Test Cases

1. **Generic AI Questions**
   - "Who are you?", "What can you do?", "Tell me about yourself"
   - Expected: No document retrieval, no sources shown

2. **Non-existent Topics**
   - "Tell me about [random person not in docs]"
   - Expected: "No information found", no irrelevant sources

3. **Document-Specific Queries**
   - "Summarize [specific document]"
   - Expected: High RAG score (>75%), only relevant sources

4. **Ambiguous Queries**
   - "What are the key findings?"
   - Expected: Best available sources, clear quality indicators

### Validation Metrics

Monitor these metrics post-deployment:

1. **Source Quality Distribution**
   - % of sources with score >75%
   - % of sources with score 70-75%
   - % of sources with score <70%

2. **RAG Score Improvements**
   - Average RAG score across all queries
   - % of queries with RAG score >75%

3. **User Feedback**
   - Source relevance rating
   - Answer accuracy rating

## Rollback Plan

If issues arise, revert by:

1. **Config rollback:**
   ```python
   SIMILARITY_THRESHOLD = 0.70
   MIN_SIMILARITY_THRESHOLD = 0.55
   NO_RELEVANT_DOCS_THRESHOLD = 0.65
   ```

2. **Remove source filtering:**
   - Comment out `_filter_high_quality_sources()` calls
   - Use all filtered_chunks for sources

3. **Restore cascading fallback:**
   - Re-add intermediate fallback level (threshold - 0.1)

## Monitoring

Key log messages to watch:

- `✨ Showing N high-quality sources (>=75%)`
- `📊 Showing N sources above display threshold (>=70%)`
- `⚠️ Showing top N sources (below quality thresholds)`
- `🔄 Cascading fallback enabled: will try thresholds [...]`
- `📝 Using N chunks for LLM context (filtered from M)`

## Future Enhancements

1. **Semantic Re-ranking**
   - Use cross-encoder for better relevance scoring
   - Re-rank after initial retrieval

2. **Source Attribution Verification**
   - Parse LLM response for [Source N] citations
   - Only show sources actually cited in answer

3. **Query Expansion**
   - Generate related queries for better recall
   - Combine results from multiple query variations

4. **Adaptive Thresholds**
   - Adjust thresholds based on query type
   - Learn optimal thresholds from user feedback

5. **Context Compression**
   - Summarize long chunks before LLM context
   - Reduce token usage while maintaining quality

## Conclusion

These improvements focus on **quality over quantity** in RAG retrieval:
- Stricter thresholds reduce false positives
- Tiered source filtering ensures best sources shown
- Improved LLM prompts reduce hallucination
- Conservative fallback prevents low-quality matches

The result should be **higher accuracy, better source attribution, and improved user trust** in the RAG system.

---

**Last Updated:** November 15, 2025
**Author:** Claude Code Agent
**Version:** 1.0
