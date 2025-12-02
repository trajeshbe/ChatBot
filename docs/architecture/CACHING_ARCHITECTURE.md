# Caching Architecture Guide

**Last Updated**: 2025-12-02
**Purpose**: Comprehensive guide to the caching system in the Enterprise RAG Chatbot

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Cache Types](#cache-types)
3. [Redis Cache](#redis-cache)
4. [PostgreSQL Query Cache](#postgresql-query-cache)
5. [Comparison](#comparison)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The Enterprise RAG Chatbot uses **two distinct caching layers** for optimal performance:

1. **Redis Cache** - Fast in-memory cache for embeddings
2. **PostgreSQL Query Cache** - Semantic cache for RAG query results

Both caches work together to minimize redundant computations and reduce latency.

---

## Cache Types

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      User Query                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│         STEP 1: Generate Query Embedding               │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Check Redis Cache (Embedding Service)           │ │
│  │  - Key: "emb:<text_hash>"                        │ │
│  │  - TTL: 1 hour                                    │ │
│  │  - Storage: In-memory (Redis)                    │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
│  Cache Hit? ──Yes──> Return cached embedding           │
│       │                                                 │
│       No                                                │
│       ▼                                                 │
│  Generate embedding with SentenceTransformer           │
│  Store in Redis for future use                         │
└────────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│      STEP 2: Check Semantic Query Cache                │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Check PostgreSQL Query Cache (RAG Service)      │ │
│  │  - Similarity: cosine(query_embedding, cached)   │ │
│  │  - Threshold: 0.95                               │ │
│  │  - TTL: 1 hour (default)                         │ │
│  │  - Storage: PostgreSQL table                     │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
│  Cache Hit? ──Yes──> Return cached RAG response        │
│       │                                                 │
│       No                                                │
│       ▼                                                 │
│  Execute full RAG pipeline:                             │
│  1. Vector similarity search                            │
│  2. Reranking                                           │
│  3. LLM generation                                      │
│  4. Store result in query_cache                         │
└────────────────────────────────────────────────────────┘
```

---

## Redis Cache

### Purpose
**Fast in-memory caching of embedding vectors** to avoid recomputing embeddings for identical or similar text.

### Location
**Service**: `backend/app/services/embedding_service.py`

### How It Works

```python
# 1. Generate cache key from text
import hashlib
text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
cache_key = f"emb:{text_hash}"

# 2. Check cache
cached_embedding = await redis_client.get(cache_key)
if cached_embedding:
    return json.loads(cached_embedding)  # Cache HIT

# 3. Generate embedding (cache MISS)
embedding = model.encode(text)

# 4. Store in Redis with TTL
await redis_client.setex(
    cache_key,
    3600,  # 1 hour TTL
    json.dumps(embedding.tolist())
)
```

### Configuration

```python
# In backend/app/core/config.py
REDIS_URL = "redis://redis:6379/0"
REDIS_TTL = 3600  # 1 hour
```

### Storage Details

| Property | Value |
|----------|-------|
| **Storage** | In-memory (Redis) |
| **Key Format** | `emb:<sha256_hash>` |
| **Value Format** | JSON array of floats |
| **TTL** | 3600 seconds (1 hour) |
| **Size** | ~1.5 KB per embedding (384 dimensions) |
| **Eviction** | LRU (Least Recently Used) |

### Benefits

✅ **Fast**: In-memory access (< 1ms)
✅ **Reduces LLM API calls**: No need to regenerate embeddings
✅ **Scales horizontally**: Redis cluster support
✅ **Automatic cleanup**: TTL-based expiration

---

## PostgreSQL Query Cache

### Purpose
**Semantic caching of complete RAG query results** to avoid re-executing expensive RAG pipelines for similar questions.

### Location
**Service**: `backend/app/services/rag_service.py`
**Table**: `query_cache` (PostgreSQL)

### How It Works

```python
# 1. Generate query embedding (using Redis cache above)
query_embedding = await embedding_service.get_embedding(query_text)

# 2. Search for semantically similar cached queries
query = """
    SELECT response, sources,
           1 - (query_embedding <=> $1::vector) as similarity
    FROM query_cache
    WHERE 1 - (query_embedding <=> $1::vector) > 0.95
      AND EXTRACT(EPOCH FROM (NOW() - created_at)) < ttl_seconds
    ORDER BY similarity DESC
    LIMIT 1
"""

# 3. If found, return cached response (cache HIT)
if cached_result:
    return cached_result['response']

# 4. Execute full RAG pipeline (cache MISS)
rag_result = await execute_rag_pipeline(query)

# 5. Store result in query_cache
INSERT INTO query_cache (
    query_text,
    query_embedding,
    response,
    sources,
    ttl_seconds
) VALUES ($1, $2::vector, $3, $4, 3600)
```

### Database Schema

```sql
CREATE TABLE query_cache (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text       TEXT NOT NULL,
    query_embedding  VECTOR(384),
    response         JSONB NOT NULL,
    sources          JSONB DEFAULT '[]'::jsonb,
    model_id         VARCHAR(100),
    hit_count        INTEGER DEFAULT 0,
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ttl_seconds      INTEGER DEFAULT 3600
);

-- Indexes for fast lookups
CREATE INDEX idx_query_cache_embedding
    ON query_cache USING ivfflat (query_embedding vector_cosine_ops);
CREATE INDEX idx_query_cache_created_at
    ON query_cache (created_at DESC);
CREATE INDEX idx_query_cache_ttl
    ON query_cache (created_at, ttl_seconds);
```

### Configuration

```python
# Similarity threshold for cache hit (0.0 - 1.0)
CACHE_SIMILARITY_THRESHOLD = 0.95  # Very high = exact match

# Time-to-live in seconds
DEFAULT_CACHE_TTL = 3600  # 1 hour
```

### Storage Details

| Property | Value |
|----------|-------|
| **Storage** | PostgreSQL table |
| **Similarity Metric** | Cosine similarity (pgvector) |
| **Threshold** | 0.95 (95% similarity required) |
| **TTL** | 3600 seconds (configurable per entry) |
| **Size** | ~10-50 KB per cached query (varies) |
| **Cleanup** | Manual or scheduled (delete expired) |

### Benefits

✅ **Semantic matching**: Finds similar queries, not just exact matches
✅ **Complete responses**: Caches entire RAG pipeline result
✅ **Source attribution**: Stores source documents
✅ **Analytics**: Tracks hit_count for popular queries
✅ **Persistent**: Survives backend restarts (unlike Redis)

---

## Comparison

### Redis Cache vs PostgreSQL Query Cache

| Feature | Redis Cache | PostgreSQL Query Cache |
|---------|-------------|------------------------|
| **What it caches** | Embedding vectors only | Complete RAG responses |
| **Cache key** | Text hash | Embedding vector (semantic) |
| **Match type** | Exact text match | Semantic similarity (0.95+) |
| **Speed** | Ultra-fast (< 1ms) | Fast (10-50ms) |
| **Storage** | In-memory | Disk (persistent) |
| **Size per entry** | ~1.5 KB | ~10-50 KB |
| **TTL** | 1 hour (fixed) | 1 hour (configurable) |
| **Survives restart** | ❌ No | ✅ Yes |
| **Use case** | Embedding generation | Full RAG pipeline |
| **Benefit** | Faster embedding | Skip entire RAG execution |

### Cache Hit Flow

```
Query: "What are the children's books?"

┌──────────────────────────────────────────────────────────┐
│ Redis Cache Check (Embedding)                            │
├──────────────────────────────────────────────────────────┤
│ Key: emb:a3f8d9c2...                                     │
│ ✅ HIT: Return [0.047, -0.089, ...]                      │
│ Saved: 50ms (model inference time)                       │
└──────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│ PostgreSQL Query Cache Check (RAG Result)                │
├──────────────────────────────────────────────────────────┤
│ Similarity Search: Find similar cached queries           │
│ Best Match: "Tell me about children books" (0.97)        │
│ ✅ HIT: Return cached response                           │
│ Saved: 2-5 seconds (vector search + LLM time)            │
└──────────────────────────────────────────────────────────┘
           │
           ▼
      Return to User (Total time: ~100ms instead of 5s)
```

---

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_EMBEDDING_TTL=3600  # 1 hour

# Query Cache Configuration
QUERY_CACHE_SIMILARITY_THRESHOLD=0.95  # 95% similarity
DEFAULT_QUERY_CACHE_TTL=3600  # 1 hour
```

### Runtime Configuration

```python
# Per-query cache control
result = await rag_service.query(
    query_text="What are children's books?",
    use_cache=True,  # Enable cache checking
    session_id="session-123"
)
```

### Disable Caching (Development/Testing)

```python
# Disable Redis cache
REDIS_URL=None

# Disable query cache
use_cache=False  # in query parameters
```

---

## Troubleshooting

### Issue: Redis Cache Not Working

**Symptoms**: Embeddings regenerated every time

**Diagnosis**:
```bash
# Check Redis connection
docker-compose logs redis | grep "Ready to accept connections"

# Check Redis keys
docker-compose exec redis redis-cli KEYS "emb:*"
```

**Fix**:
```bash
# Restart Redis
docker-compose restart redis

# Check Redis URL in .env
REDIS_URL=redis://redis:6379/0
```

---

### Issue: Query Cache Column Missing

**Symptoms**: `ERROR: column "sources" does not exist`

**Diagnosis**:
```sql
-- Check table schema
\d query_cache
```

**Fix**:
```bash
# Apply migration
psql -U postgres -d ragchatbot < migrations/015_fix_query_cache_schema.sql
```

---

### Issue: Cache Not Expiring

**Symptoms**: Old results returned

**Diagnosis**:
```sql
-- Check expired entries
SELECT COUNT(*),
       AVG(EXTRACT(EPOCH FROM (NOW() - created_at))) as avg_age_seconds
FROM query_cache
WHERE EXTRACT(EPOCH FROM (NOW() - created_at)) > ttl_seconds;
```

**Fix**:
```sql
-- Clean up expired entries
DELETE FROM query_cache
WHERE EXTRACT(EPOCH FROM (NOW() - created_at)) > COALESCE(ttl_seconds, 3600);
```

---

### Issue: Low Cache Hit Rate

**Diagnosis**:
```sql
-- Check cache statistics
SELECT
    COUNT(*) as total_entries,
    AVG(hit_count) as avg_hits,
    MAX(hit_count) as max_hits
FROM query_cache
WHERE created_at > NOW() - INTERVAL '1 day';
```

**Optimization**:
- Lower similarity threshold (0.90 instead of 0.95)
- Increase TTL for frequently asked questions
- Pre-populate cache with common queries

---

## Cache Maintenance

### Scheduled Cleanup

```sql
-- Create cleanup function
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM query_cache
    WHERE EXTRACT(EPOCH FROM (NOW() - created_at)) > COALESCE(ttl_seconds, 3600);
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup (using pg_cron or external scheduler)
-- Every hour: SELECT cleanup_expired_cache();
```

### Monitor Cache Performance

```sql
-- Cache hit statistics
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as queries_cached,
    SUM(hit_count) as total_hits,
    AVG(hit_count) as avg_hits_per_query
FROM query_cache
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

---

## Best Practices

### ✅ DO

- Enable caching in production for better performance
- Monitor cache hit rates to tune similarity threshold
- Set appropriate TTL based on data freshness requirements
- Clean up expired cache entries regularly
- Use semantic cache for expensive queries

### ❌ DON'T

- Set similarity threshold too low (< 0.90) - may return irrelevant cached results
- Cache sensitive/PII data without encryption
- Disable caching in production without good reason
- Let cache grow indefinitely without cleanup
- Cache real-time data with long TTL

---

## Performance Impact

### With Caching

```
┌─────────────────────────────────────────────┐
│ Query: "Tell me about children's books"     │
├─────────────────────────────────────────────┤
│ Redis Cache Hit (embedding): 1ms            │
│ Query Cache Hit (RAG result): 50ms          │
│ ────────────────────────────────────────────│
│ Total: ~51ms ✅                              │
└─────────────────────────────────────────────┘
```

### Without Caching

```
┌─────────────────────────────────────────────┐
│ Query: "Tell me about children's books"     │
├─────────────────────────────────────────────┤
│ Generate embedding: 50ms                    │
│ Vector search: 200ms                        │
│ Reranking: 500ms                            │
│ LLM generation: 3000ms                      │
│ ────────────────────────────────────────────│
│ Total: ~3750ms ❌                            │
└─────────────────────────────────────────────┘
```

**Speedup**: **73x faster** with both caches hit!

---

## Summary

The Enterprise RAG Chatbot uses a **two-tier caching strategy**:

1. **Redis Cache** (Tier 1) - Lightning-fast embedding cache
2. **PostgreSQL Query Cache** (Tier 2) - Semantic RAG result cache

Both work together to deliver:
- ⚡ **73x faster** responses for cached queries
- 💰 **Reduced costs** (fewer LLM API calls)
- 📊 **Better scalability** (reduced database load)
- 🎯 **Semantic matching** (similar questions cached)

---

**End of Caching Architecture Guide**
