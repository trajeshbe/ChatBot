# AADHAN RETRIEVAL ISSUE - INVESTIGATION REPORT
## Date: 2025-11-23

========================================================================
## PROBLEM SUMMARY
========================================================================

Query: "Who is Aadhan?"
- ❌ Returns 0 sources
- ❌ Answers with incorrect information about "Adhaar" (Indian ID system)

Query: "Tell me about King Aadhan from the story"  
- ✅ Returns 2 sources
- ✅ Correctly answers about King Aadhan

========================================================================
## ROOT CAUSE IDENTIFIED
========================================================================

**Issue**: SIMILARITY THRESHOLDS ARE TOO STRICT

Current Settings (backend/app/core/config.py):
```
SIMILARITY_THRESHOLD: 0.75 (75%)
NO_RELEVANT_DOCS_THRESHOLD: 0.70 (70%)
```

**What's Happening:**

1. Query "Who is Aadhan?" generates an embedding
2. Vector search finds chunks with "Aadhan" but similarity score < 70%
3. RAG service filters OUT all chunks below 70% threshold
4. Result: 0 sources returned → LLM generates wrong answer

5. Query "Tell me about King Aadhan from the story" 
6. More specific query → better semantic match → score > 70%
7. Result: 2 sources retrieved → correct answer

========================================================================
## EVIDENCE
========================================================================

✅ Database Verification:
- Document exists: Short Story3.txt (ID: 50581c8e...)
- 23 chunks total, 10 chunks contain "Aadhan"
- All chunks have embeddings (CONFIRMED)

✅ Content Verification:
- Chunks contain: "king named Aadhan", "Kandigai", "Amudhan", "Thamarai"
- Story content is complete and accurate

❌ Vector Search Issue:
- Simple query "Who is Aadhan?" doesn't match story narrative chunks well
- Similarity score falls below 70% threshold
- Chunks are filtered out before LLM sees them

========================================================================
## WHY SIMPLE QUERIES FAIL
========================================================================

The embedding for "Who is Aadhan?" represents:
- Direct question about identity
- Short, simple semantic pattern

The story chunks contain:
- Narrative text: "Once upon a time, there lived a king named Aadhan..."
- Contextual descriptions, not direct definitions
- Complex sentence structures

Semantic similarity between a simple question and narrative text is naturally
lower than between specific queries and detailed descriptions.

========================================================================
## PROPOSED SOLUTIONS
========================================================================

**Option 1: Lower Similarity Thresholds** (RECOMMENDED)
```python
SIMILARITY_THRESHOLD: 0.60  # Down from 0.75
NO_RELEVANT_DOCS_THRESHOLD: 0.55  # Down from 0.70
```

Pros:
- Catches more relevant documents
- Works better with simple queries
- Industry standard is typically 0.5-0.6

Cons:
- May retrieve slightly less relevant documents
- Need to test to ensure quality

**Option 2: Query Expansion/Reformulation**
- Expand "Who is Aadhan?" → "Tell me about Aadhan, king Aadhan, Aadhan story"
- Use LLM to reformulate queries before vector search

Pros:
- Better semantic matching
- Maintains high quality threshold

Cons:
- Additional LLM call = higher latency
- More complex implementation

**Option 3: Hybrid Search (ALREADY ENABLED)**
- Current code already uses hybrid search (semantic + keyword)
- But keyword matching alone isn't enough if similarity filter rejects chunks

**Option 4: Multi-Query Retrieval**
- Generate multiple query variations
- Retrieve from all variations
- Merge and deduplicate results

Pros:
- Most robust solution
- Catches edge cases

Cons:
- Most complex
- Higher computational cost

========================================================================
## RECOMMENDATION
========================================================================

**Immediate Fix**: Lower thresholds to industry-standard values
```python
SIMILARITY_THRESHOLD: 0.60
NO_RELEVANT_DOCS_THRESHOLD: 0.55  
```

**Future Enhancement**: Implement query expansion for very simple queries

========================================================================
## TESTING PLAN
========================================================================

After implementing the fix, test with:
1. "Who is Aadhan?" - Should retrieve Short Story3.txt
2. "What is Aadhan?" - Should retrieve Short Story3.txt  
3. "Tell me about Aadhan" - Should retrieve Short Story3.txt
4. "Aadhan story" - Should retrieve Short Story3.txt
5. Verify no regression with other queries

