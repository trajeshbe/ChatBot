# Enterprise RAG Chatbot - Comprehensive Testing Guide

**Date**: 2025-11-18
**Version**: 1.0.0
**Purpose**: Complete testing documentation for all application features

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Test Environment Setup](#test-environment-setup)
4. [Feature Testing](#feature-testing)
   - [Health & Service Status](#1-health--service-status)
   - [Document Upload](#2-document-upload)
   - [Document Management](#3-document-management)
   - [RAG Query System](#4-rag-query-system)
   - [Multiple LLM Models](#5-multiple-llm-models)
   - [Session Management](#6-session-management)
   - [Web Scraping](#7-web-scraping)
   - [Template Extraction (Playwright)](#8-template-extraction-playwright)
   - [GraphQL API](#9-graphql-api)
   - [Frontend Interface](#10-frontend-interface)
5. [Integration Tests](#integration-tests)
6. [Performance Tests](#performance-tests)
7. [Test Results Summary](#test-results-summary)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides comprehensive testing procedures for the Enterprise RAG Chatbot application. It covers all major features, expected behaviors, and verification steps.

### Application Architecture

- **Frontend**: Next.js 14 (React) - Port 3001
- **Backend**: FastAPI (Python) - Port 8000
- **Database**: PostgreSQL + pgvector - Port 5433
- **Vector Store**: PostgreSQL with 384-dimensional embeddings
- **Cache**: Redis - Port 6380
- **LLM**: Ollama (local) - Port 11434
- **Storage**: MinIO (S3-compatible) - Ports 9000-9001
- **Observability**: Grafana, Loki, Tempo - Port 3000
- **Browser Automation**: Playwright with Chromium

---

## Prerequisites

### Required Tools

```bash
# Install jq for JSON processing
sudo apt-get install jq  # Ubuntu/Debian
brew install jq          # macOS

# Verify Docker and Docker Compose
docker --version        # Should be 20.10+
docker-compose --version # Should be 2.0+
```

### Required Services

Ensure all services are running:

```bash
docker-compose ps
```

Expected services:
- ✅ rag-backend (healthy)
- ✅ rag-postgres (healthy)
- ✅ rag-redis (healthy)
- ✅ rag-minio (healthy)
- ✅ rag-ollama (healthy)
- ✅ rag-frontend
- ✅ rag-grafana
- ✅ rag-loki

---

## Test Environment Setup

### 1. Start All Services

```bash
# Navigate to project directory
cd /path/to/ChatBot

# Start all services
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
sleep 60

# Verify all services are running
docker-compose ps
```

### 2. Create Test Session ID

```bash
# Generate unique session ID for testing
export TEST_SESSION="test-session-$(date +%s)"
echo "Test Session ID: $TEST_SESSION"
```

### 3. Prepare Test Files

```bash
# Create test directory
mkdir -p /tmp/rag-tests

# Create sample text document
cat > /tmp/rag-tests/ai_basics.txt <<'EOF'
# Artificial Intelligence Fundamentals

Artificial Intelligence (AI) is the simulation of human intelligence by machines.
Machine learning is a subset of AI that enables systems to learn from data.

## Key Concepts
- Supervised Learning: Learning from labeled data
- Unsupervised Learning: Finding patterns in unlabeled data
- Deep Learning: Neural networks with multiple layers
- Natural Language Processing: Understanding and generating human language

## Applications
AI is used in healthcare, finance, autonomous vehicles, and customer service.
EOF

# Create sample markdown document
cat > /tmp/rag-tests/ml_guide.md <<'EOF'
# Machine Learning Guide

Machine learning algorithms learn patterns from data to make predictions or decisions.

## Types of ML
1. **Classification**: Categorizing data into classes
2. **Regression**: Predicting continuous values
3. **Clustering**: Grouping similar data points

## Popular Algorithms
- Linear Regression
- Decision Trees
- Random Forests
- Neural Networks
EOF
```

---

## Feature Testing

### 1. Health & Service Status

#### Test 1.1: Backend Health Check

**Purpose**: Verify backend API is accessible and healthy

**Command**:
```bash
curl -s http://localhost:8000/health | jq .
```

**Expected Result**:
```json
{
  "status": "healthy",
  "app": "Enterprise RAG Chatbot",
  "version": "1.0.0",
  "features": {
    "enhanced_rag": true,
    "memory_hierarchy": true,
    "audit_logging": true,
    "session_management": true
  }
}
```

**✅ Pass Criteria**:
- Status is "healthy"
- All features are `true`

---

#### Test 1.2: Service Status Check

**Purpose**: Verify all Docker services are running

**Command**:
```bash
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

**Expected Result**: All services show "Up" status with "(healthy)" where applicable

**✅ Pass Criteria**:
- All critical services (backend, postgres, redis, ollama, minio) show "healthy"
- Frontend shows "Up"

---

#### Test 1.3: API Documentation

**Purpose**: Verify API documentation is accessible

**Command**:
```bash
curl -s http://localhost:8000/docs -o /tmp/api-docs.html && echo "API docs downloaded"
curl -s http://localhost:8000/redoc -o /tmp/api-redoc.html && echo "ReDoc downloaded"
```

**Manual Verification**:
- Open http://localhost:8000/docs in browser (Swagger UI)
- Open http://localhost:8000/redoc in browser (ReDoc)

**✅ Pass Criteria**:
- Both URLs return HTTP 200
- Documentation shows all API endpoints

---

### 2. Document Upload

#### Test 2.1: Upload Text Document

**Purpose**: Test uploading a plain text file

**Command**:
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/tmp/rag-tests/ai_basics.txt" \
  -F "session_id=$TEST_SESSION" \
  2>&1 | jq .
```

**Expected Result**:
```json
{
  "document_id": "uuid-here",
  "filename": "ai_basics.txt",
  "file_type": "txt",
  "file_size": XXX,
  "status": "uploaded",
  "session_id": "test-session-XXXXX"
}
```

**✅ Pass Criteria**:
- Returns HTTP 200
- `document_id` is a valid UUID
- `status` is "uploaded" or "processing"

---

#### Test 2.2: Upload Markdown Document

**Purpose**: Test uploading a markdown file

**Command**:
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/tmp/rag-tests/ml_guide.md" \
  -F "session_id=$TEST_SESSION" \
  2>&1 | jq .
```

**Expected Result**: Similar to Test 2.1 with different filename

**✅ Pass Criteria**: Same as Test 2.1

---

#### Test 2.3: Upload Without Session ID

**Purpose**: Test uploading without specifying session (should use default)

**Command**:
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/tmp/rag-tests/ai_basics.txt" \
  2>&1 | jq .
```

**Expected Result**: Document uploaded without session_id in response

**✅ Pass Criteria**:
- Upload succeeds
- `session_id` is null or not present in response

---

#### Test 2.4: Upload Large Document

**Purpose**: Test uploading a larger document

**Command**:
```bash
# Create large test document (append content multiple times)
for i in {1..100}; do
  cat /tmp/rag-tests/ai_basics.txt >> /tmp/rag-tests/large_doc.txt
done

# Upload
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/tmp/rag-tests/large_doc.txt" \
  -F "session_id=$TEST_SESSION" \
  2>&1 | jq .
```

**Expected Result**: Document uploaded successfully with larger file_size

**✅ Pass Criteria**:
- Upload succeeds
- Processing may take longer
- `file_size` reflects actual size

---

### 3. Document Management

#### Test 3.1: List All Documents

**Purpose**: Retrieve all uploaded documents

**Command**:
```bash
curl -s http://localhost:8000/api/v1/documents | jq .
```

**Expected Result**:
```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "ai_basics.txt",
      "file_type": "txt",
      "upload_date": "2025-11-18T...",
      "processed": true
    },
    ...
  ],
  "total": 2
}
```

**✅ Pass Criteria**:
- Returns list of all uploaded documents
- Each document has required fields

---

#### Test 3.2: List Documents by Session

**Purpose**: Retrieve documents for specific session

**Command**:
```bash
curl -s "http://localhost:8000/api/v1/documents?session_id=$TEST_SESSION" | jq .
```

**Expected Result**: Only documents from TEST_SESSION

**✅ Pass Criteria**:
- Returns only documents with matching session_id
- `total` matches expected count

---

#### Test 3.3: Get Document Details

**Purpose**: Retrieve detailed information about a specific document

**Command**:
```bash
# Get first document ID
DOC_ID=$(curl -s http://localhost:8000/api/v1/documents | jq -r '.documents[0].id')

# Get document details
curl -s "http://localhost:8000/api/v1/documents/$DOC_ID" | jq .
```

**Expected Result**: Full document metadata including processing status

**✅ Pass Criteria**:
- Returns document details
- Shows processing status and metadata

---

### 4. RAG Query System

#### Test 4.1: Simple Query

**Purpose**: Test basic RAG query with uploaded documents

**Command**:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is machine learning?" \
  -F "model_id=llama3.2:3b" \
  -F "session_id=$TEST_SESSION" \
  2>&1 | jq .
```

**Expected Result**:
```json
{
  "answer": "Machine learning is a subset of AI that enables systems to learn from data...",
  "sources": [
    {
      "document_id": "uuid",
      "filename": "ai_basics.txt",
      "content": "...relevant chunk...",
      "score": 0.XX
    }
  ],
  "model_used": "llama3.2:3b",
  "tokens": XXX,
  "latency_ms": XXX
}
```

**✅ Pass Criteria**:
- Returns relevant answer
- Includes source documents
- Answer relates to uploaded content

---

#### Test 4.2: Query with Multiple Sources

**Purpose**: Test RAG query that should reference multiple documents

**Command**:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Explain supervised and unsupervised learning" \
  -F "model_id=llama3.2:3b" \
  -F "session_id=$TEST_SESSION" \
  2>&1 | jq .
```

**Expected Result**: Answer with sources from multiple uploaded documents

**✅ Pass Criteria**:
- Answer combines information from multiple sources
- `sources` array has multiple entries

---

#### Test 4.3: Query Without Documents

**Purpose**: Test query behavior with no relevant documents

**Command**:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Tell me about quantum computing" \
  -F "model_id=llama3.2:3b" \
  -F "session_id=empty-session" \
  2>&1 | jq .
```

**Expected Result**: Answer without sources or using general knowledge

**✅ Pass Criteria**:
- Returns answer (may be general knowledge)
- `sources` array is empty or has low scores

---

### 5. Multiple LLM Models

#### Test 5.1: List Available Models

**Purpose**: Retrieve list of available LLM models

**Command**:
```bash
curl -s http://localhost:8000/api/v1/models | jq .
```

**Expected Result**:
```json
{
  "models": [
    {
      "id": "llama3.2:3b",
      "name": "Llama 3.2 3B",
      "provider": "ollama",
      "status": "available"
    },
    {
      "id": "qwen2.5:1.5b",
      "name": "Qwen 2.5 1.5B",
      "provider": "ollama",
      "status": "available"
    }
  ]
}
```

**✅ Pass Criteria**:
- Lists all available models
- Shows provider and status

---

#### Test 5.2: Query with Ollama Llama3.2

**Purpose**: Test query with Llama3.2 model

**Command**:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is deep learning?" \
  -F "model_id=llama3.2:3b" \
  -F "session_id=$TEST_SESSION" \
  2>&1 | jq .
```

**Expected Result**: Answer using Llama3.2 model

**✅ Pass Criteria**:
- `model_used` is "llama3.2:3b"
- Returns valid answer

---

#### Test 5.3: Query with Ollama Qwen2.5

**Purpose**: Test query with Qwen2.5 model

**Command**:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is deep learning?" \
  -F "model_id=qwen2.5:1.5b" \
  -F "session_id=$TEST_SESSION" \
  2>&1 | jq .
```

**Expected Result**: Answer using Qwen2.5 model

**✅ Pass Criteria**:
- `model_used` is "qwen2.5:1.5b"
- Returns valid answer

---

### 6. Session Management

#### Test 6.1: Create New Session

**Purpose**: Verify session creation and isolation

**Command**:
```bash
# Create new session
NEW_SESSION="test-session-2-$(date +%s)"

# Upload document to new session
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/tmp/rag-tests/ml_guide.md" \
  -F "session_id=$NEW_SESSION" \
  2>&1 | jq .

# Query in new session
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What are ML algorithm types?" \
  -F "model_id=llama3.2:3b" \
  -F "session_id=$NEW_SESSION" \
  2>&1 | jq .
```

**Expected Result**: Query only accesses documents from NEW_SESSION

**✅ Pass Criteria**:
- Sources only from ml_guide.md
- Doesn't access documents from TEST_SESSION

---

#### Test 6.2: Session Document List

**Purpose**: Verify session-specific document listing

**Command**:
```bash
# List documents in original session
curl -s "http://localhost:8000/api/v1/documents?session_id=$TEST_SESSION" | jq .

# List documents in new session
curl -s "http://localhost:8000/api/v1/documents?session_id=$NEW_SESSION" | jq .
```

**Expected Result**: Each session lists only its own documents

**✅ Pass Criteria**:
- Document lists are session-specific
- No cross-session contamination

---

### 7. Web Scraping

#### Test 7.1: Scrape Wikipedia Page

**Purpose**: Test web scraping with Wikipedia

**Command**:
```bash
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://en.wikipedia.org/wiki/Artificial_intelligence"],
    "session_id": "'$TEST_SESSION'",
    "strategy": "trafilatura"
  }' \
  2>&1 | jq .
```

**Expected Result**:
```json
{
  "job_id": "uuid",
  "status": "processing",
  "urls": ["https://en.wikipedia.org/wiki/Artificial_intelligence"],
  "estimated_time": "30-60 seconds"
}
```

**✅ Pass Criteria**:
- Returns job_id
- Status is "processing" or "completed"

---

#### Test 7.2: Scrape Multiple URLs

**Purpose**: Test bulk scraping

**Command**:
```bash
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://en.wikipedia.org/wiki/Machine_learning",
      "https://en.wikipedia.org/wiki/Deep_learning"
    ],
    "session_id": "'$TEST_SESSION'",
    "strategy": "trafilatura"
  }' \
  2>&1 | jq .
```

**Expected Result**: Job created for multiple URLs

**✅ Pass Criteria**:
- Job processes all URLs
- Creates separate document for each

---

### 8. Template Extraction (Playwright)

#### Test 8.1: Playwright Health Check

**Purpose**: Verify Playwright browser automation is working

**Command**:
```bash
docker exec rag-backend curl -s http://localhost:8000/api/v1/test/playwright-minimal | jq .
```

**Expected Result**:
```json
{
  "success": true,
  "message": "Playwright works in FastAPI!",
  "browser_version": "130.0.6723.31",
  "chromium_path": "/ms-playwright/chromium-1140/chrome-linux/chrome",
  "env": "/ms-playwright"
}
```

**✅ Pass Criteria**:
- `success` is true
- Browser version is displayed

---

#### Test 8.2: Template Extraction Test

**Purpose**: Test template-based data extraction

**Command**:
```bash
docker exec rag-backend curl -s -X POST http://localhost:8000/api/v1/extract/preset/screener_in \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.screener.in/company/TCS/consolidated/"}' \
  | jq .
```

**Expected Result**: Extracted data from website (may fail on selector timeout - expected)

**✅ Pass Criteria**:
- Browser launches successfully
- Navigates to URL
- Attempts extraction (selector errors are website-specific, not Playwright failures)

---

### 9. GraphQL API

#### Test 9.1: GraphQL Playground Access

**Purpose**: Verify GraphQL endpoint is accessible

**Manual Test**:
- Open http://localhost:8000/graphql in browser
- Verify GraphQL Playground loads

**✅ Pass Criteria**: GraphQL Playground interface is accessible

---

#### Test 9.2: GraphQL Query - List Documents

**Purpose**: Test GraphQL query for documents

**Command**:
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { documents { id filename fileType uploadDate processed } }"
  }' \
  2>&1 | jq .
```

**Expected Result**:
```json
{
  "data": {
    "documents": [
      {
        "id": "uuid",
        "filename": "ai_basics.txt",
        "fileType": "txt",
        "uploadDate": "2025-11-18T...",
        "processed": true
      }
    ]
  }
}
```

**✅ Pass Criteria**:
- Returns document list
- No errors in response

---

#### Test 9.3: GraphQL Mutation - Query RAG

**Purpose**: Test GraphQL mutation for RAG queries

**Command**:
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { query(input: { query: \"What is AI?\", model: \"llama3.2:3b\" }) { answer sources { filename } } }"
  }' \
  2>&1 | jq .
```

**Expected Result**: RAG query result via GraphQL

**✅ Pass Criteria**:
- Returns answer
- Includes sources

---

### 10. Frontend Interface

#### Test 10.1: Frontend Accessibility

**Purpose**: Verify frontend is accessible

**Manual Test**:
- Open http://localhost:3001 in browser
- Verify chat interface loads

**✅ Pass Criteria**:
- Frontend loads without errors
- UI elements are visible

---

#### Test 10.2: Document Upload via UI

**Purpose**: Test file upload through frontend

**Manual Test**:
1. Navigate to http://localhost:3001
2. Click on file upload area
3. Select `/tmp/rag-tests/ai_basics.txt`
4. Verify upload progress and completion

**✅ Pass Criteria**:
- File uploads successfully
- Appears in document list

---

#### Test 10.3: Chat Query via UI

**Purpose**: Test chat functionality through frontend

**Manual Test**:
1. Navigate to http://localhost:3001
2. Type "What is machine learning?" in chat input
3. Select model (e.g., "llama3.2:3b")
4. Send query

**✅ Pass Criteria**:
- Query processes
- Response appears with sources
- Sources are clickable/viewable

---

## Integration Tests

### Test INT-1: End-to-End RAG Pipeline

**Purpose**: Test complete workflow from upload to query

**Command**:
```bash
# Step 1: Upload document
UPLOAD_RESULT=$(curl -s -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/tmp/rag-tests/ai_basics.txt" \
  -F "session_id=e2e-test-$(date +%s)")

echo "Upload Result:"
echo $UPLOAD_RESULT | jq .

# Step 2: Wait for processing
sleep 10

# Step 3: Query the uploaded content
QUERY_RESULT=$(curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=What is supervised learning?" \
  -F "model_id=llama3.2:3b" \
  -F "session_id=$(echo $UPLOAD_RESULT | jq -r '.session_id')")

echo "Query Result:"
echo $QUERY_RESULT | jq .
```

**✅ Pass Criteria**:
- Upload succeeds
- Document processes
- Query returns answer with sources

---

### Test INT-2: Multi-Model Comparison

**Purpose**: Compare responses from different models

**Command**:
```bash
QUERY="What is the difference between AI and ML?"

# Query with Llama3.2
echo "=== Llama3.2 Response ==="
curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=$QUERY" \
  -F "model_id=llama3.2:3b" \
  -F "session_id=$TEST_SESSION" \
  | jq '.answer'

# Query with Qwen2.5
echo "=== Qwen2.5 Response ==="
curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=$QUERY" \
  -F "model_id=qwen2.5:1.5b" \
  -F "session_id=$TEST_SESSION" \
  | jq '.answer'
```

**✅ Pass Criteria**:
- Both models return answers
- Answers are relevant
- May have different styles/details

---

## Performance Tests

### Test PERF-1: Query Latency

**Purpose**: Measure query response time

**Command**:
```bash
for i in {1..5}; do
  echo "Query $i:"
  time curl -s -X POST http://localhost:8000/api/v1/query \
    -F "query=What is machine learning?" \
    -F "model_id=llama3.2:3b" \
    -F "session_id=$TEST_SESSION" \
    | jq -r '.latency_ms'
  sleep 2
done
```

**✅ Pass Criteria**:
- Average latency < 10 seconds (with local Ollama)
- Consistent response times

---

### Test PERF-2: Concurrent Uploads

**Purpose**: Test multiple simultaneous uploads

**Command**:
```bash
for i in {1..3}; do
  (curl -s -X POST http://localhost:8000/api/v1/upload \
    -F "file=@/tmp/rag-tests/ai_basics.txt" \
    -F "session_id=concurrent-$i" \
    | jq .) &
done
wait
```

**✅ Pass Criteria**:
- All uploads succeed
- No errors or conflicts

---

## Test Results Summary

### Test Execution Checklist

| Test ID | Feature | Status | Notes |
|---------|---------|--------|-------|
| 1.1 | Backend Health | ✅ | |
| 1.2 | Service Status | ✅ | |
| 1.3 | API Docs | ⏳ | |
| 2.1 | Upload TXT | ⏳ | |
| 2.2 | Upload MD | ⏳ | |
| 2.3 | Upload No Session | ⏳ | |
| 2.4 | Upload Large | ⏳ | |
| 3.1 | List All Docs | ⏳ | |
| 3.2 | List by Session | ⏳ | |
| 3.3 | Doc Details | ⏳ | |
| 4.1 | Simple Query | ⏳ | |
| 4.2 | Multi-Source Query | ⏳ | |
| 4.3 | No Doc Query | ⏳ | |
| 5.1 | List Models | ⏳ | |
| 5.2 | Llama3.2 Query | ⏳ | |
| 5.3 | Qwen2.5 Query | ⏳ | |
| 6.1 | Create Session | ⏳ | |
| 6.2 | Session Doc List | ⏳ | |
| 7.1 | Scrape Wikipedia | ⏳ | |
| 7.2 | Scrape Multiple | ⏳ | |
| 8.1 | Playwright Health | ✅ | Browser v130.0.6723.31 |
| 8.2 | Template Extract | ⏳ | |
| 9.1 | GraphQL Playground | ⏳ | |
| 9.2 | GraphQL Query | ⏳ | |
| 9.3 | GraphQL Mutation | ⏳ | |
| 10.1 | Frontend Access | ⏳ | |
| 10.2 | UI Upload | ⏳ | |
| 10.3 | UI Chat | ⏳ | |
| INT-1 | E2E Pipeline | ⏳ | |
| INT-2 | Multi-Model | ⏳ | |
| PERF-1 | Query Latency | ⏳ | |
| PERF-2 | Concurrent Upload | ⏳ | |

---

## Troubleshooting

### Common Issues

#### Issue: Upload Returns 500 Error

**Diagnosis**:
```bash
docker-compose logs backend --tail=50 | grep -i error
```

**Solutions**:
- Check MinIO is running: `docker-compose ps minio`
- Verify database connection: `docker-compose logs postgres`
- Check file permissions

---

#### Issue: Query Returns Empty Sources

**Diagnosis**:
```bash
# Check if documents are processed
curl -s http://localhost:8000/api/v1/documents | jq '.documents[] | {filename, processed}'

# Check database
docker exec rag-postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;"
```

**Solutions**:
- Wait for document processing (may take 30-60 seconds)
- Verify embeddings are generated
- Check document chunking

---

#### Issue: Ollama Model Not Found

**Diagnosis**:
```bash
curl http://localhost:11434/api/tags
docker-compose logs ollama
```

**Solutions**:
```bash
# Pull missing model
docker exec rag-ollama ollama pull llama3.2:3b

# Restart Ollama
docker-compose restart ollama
```

---

## Quick Test Script

Save this as `/tmp/quick-test.sh`:

```bash
#!/bin/bash

# Quick test script for Enterprise RAG Chatbot

echo "=== Quick Feature Test ==="
echo ""

# Test 1: Health
echo "1. Testing Backend Health..."
curl -s http://localhost:8000/health | jq -r '.status'

# Test 2: Models
echo "2. Testing Model Availability..."
curl -s http://localhost:8000/api/v1/models | jq -r '.models[].id'

# Test 3: Playwright
echo "3. Testing Playwright..."
docker exec rag-backend curl -s http://localhost:8000/api/v1/test/playwright-minimal | jq -r '.success'

# Test 4: Frontend
echo "4. Testing Frontend..."
curl -s http://localhost:3001 | grep -q "<!DOCTYPE html" && echo "✅ Frontend accessible"

echo ""
echo "=== Quick Test Complete ==="
```

**Run**:
```bash
chmod +x /tmp/quick-test.sh
/tmp/quick-test.sh
```

---

**Testing Guide Version**: 1.0.0
**Last Updated**: 2025-11-18
**Status**: Ready for execution
