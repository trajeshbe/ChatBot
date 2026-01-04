# API Integration Layer - Two-Way Customer Application Integration

**Version:** 1.0.0
**Date:** 2026-01-03
**Purpose:** Enable customers to consume GenAI app as a service AND integrate bi-directionally with their applications
**Extends:** ENTERPRISE_EXPORT_WIZARD_COMPLETE_IMPLEMENTATION_PLAN.md

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Integration Patterns](#integration-patterns)
3. [API Architecture](#api-architecture)
4. [REST API Specification](#rest-api-specification)
5. [GraphQL API](#graphql-api)
6. [WebSocket/SSE for Real-Time](#websocket-sse-for-real-time)
7. [Webhook System (Customer → GenAI)](#webhook-system-customer--genai)
8. [Event-Driven Integration](#event-driven-integration)
9. [Authentication & Authorization](#authentication--authorization)
10. [SDK Generation](#sdk-generation)
11. [API Gateway Layer](#api-gateway-layer)
12. [Rate Limiting & Quotas](#rate-limiting--quotas)
13. [Bi-Directional Data Sync](#bi-directional-data-sync)
14. [Integration Examples](#integration-examples)
15. [Monitoring & Analytics](#monitoring--analytics)
16. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

### The Integration Challenge

Customers need to:
1. **Consume GenAI as a Service** - Call RAG/LLM APIs from their applications
2. **Embed UI Components** - iframe/Web Components in their apps
3. **Receive Real-Time Updates** - Get notified when GenAI processes complete
4. **Bi-Directional Data Flow** - Push data to GenAI, receive results back
5. **Enterprise Integration** - Connect to existing systems (CRM, ERP, databases)

### The Solution: Comprehensive API Integration Layer

A multi-protocol, bi-directional integration framework that enables:

- ✅ **REST APIs** - Standard HTTP endpoints for all operations
- ✅ **GraphQL** - Flexible queries for complex data retrieval
- ✅ **WebSockets/SSE** - Real-time streaming responses
- ✅ **Webhooks** - Event-driven notifications to customer systems
- ✅ **SDKs** - Auto-generated client libraries (Python, JS/TS, Java, C#, Go)
- ✅ **API Gateway** - Rate limiting, auth, transformation, logging
- ✅ **Event Bus** - Kafka/RabbitMQ for async messaging
- ✅ **Embeddable Widgets** - Drop-in UI components

### Business Impact

- **Faster Integration**: Days instead of weeks
- **Developer Experience**: Comprehensive SDKs + Postman collections
- **Flexibility**: Multiple integration patterns for different use cases
- **Enterprise-Ready**: OAuth2, API keys, RBAC, audit logging
- **Scalability**: Handle millions of API calls/day

---

## Integration Patterns

### Pattern 1: API-First (Headless GenAI)

**Use Case**: Customer has existing UI, wants to add GenAI capabilities

```
┌─────────────────────┐
│  Customer Frontend  │
│   (React/Angular)   │
└──────────┬──────────┘
           │ REST/GraphQL
           ▼
┌─────────────────────┐
│   GenAI API Layer   │
│   (FastAPI/Kong)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   RAG/LLM Backend   │
│  (Exported Package) │
└─────────────────────┘
```

**Integration Points**:
- `/api/v1/query` - RAG question answering
- `/api/v1/documents` - Document management
- `/api/v1/chat` - Conversational interface
- `/api/v1/embeddings` - Generate embeddings

---

### Pattern 2: Embedded UI (Widget Integration)

**Use Case**: Customer wants to embed GenAI chat interface in their app

```
┌──────────────────────────────────────┐
│       Customer Application           │
│                                      │
│  ┌─────────────────────────────┐   │
│  │  <genai-chat-widget />      │   │
│  │  (Web Component/iframe)     │   │
│  └─────────────┬───────────────┘   │
│                │                    │
└────────────────┼────────────────────┘
                 │ postMessage/API
                 ▼
         ┌───────────────┐
         │  GenAI API    │
         └───────────────┘
```

**Integration Methods**:
- Web Components (standards-based)
- iframe with postMessage
- React/Vue/Angular components (via SDK)

---

### Pattern 3: Webhook-Driven (Event-Based)

**Use Case**: Customer wants to be notified when GenAI completes async tasks

```
┌─────────────────────┐
│  Customer Backend   │
│  (receives events)  │
└──────────▲──────────┘
           │ Webhooks
           │
┌──────────┴──────────┐
│  GenAI Event Bus    │
│  (Kafka/RabbitMQ)   │
└──────────▲──────────┘
           │
┌──────────┴──────────┐
│  RAG/LLM Backend    │
│  (emits events)     │
└─────────────────────┘
```

**Events**:
- `document.processed` - Document ingestion complete
- `query.completed` - RAG query finished
- `model.finetuned` - Fine-tuning job done
- `error.occurred` - Error handling

---

### Pattern 4: Bi-Directional Sync

**Use Case**: Customer's CRM data syncs with GenAI, results flow back

```
┌─────────────────────┐     ┌─────────────────────┐
│  Customer CRM       │◄───►│  GenAI App          │
│  (Salesforce/HubSpot│     │  (RAG + Vector DB)  │
└─────────────────────┘     └─────────────────────┘
        │                            │
        │    Bi-directional sync     │
        │    (REST + Webhooks)       │
        │                            │
   Data Push ────────────────────► Ingest
   Results ◄──────────────────────  Query
```

**Sync Mechanisms**:
- Customer → GenAI: REST POST/PUT for data push
- GenAI → Customer: Webhooks for results delivery
- Scheduled sync jobs (cron/Prefect)
- Real-time via WebSockets

---

## API Architecture

### Layered API Design

```
┌─────────────────────────────────────────────────────────┐
│                   API Gateway Layer                      │
│  (Kong/Tyk/AWS API Gateway - Auth, Rate Limit, Transform)│
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  REST API   │ │  GraphQL    │ │ WebSocket   │
│  (FastAPI)  │ │ (Strawberry)│ │  (Socket.IO)│
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       └───────────────┼───────────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │   Business Logic Layer   │
        │  (Services/Controllers)  │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │   Data Access Layer      │
        │  (PostgreSQL + Vector DB)│
        └──────────────────────────┘
```

### API Versioning Strategy

**URL-Based Versioning** (Recommended for REST):
```
https://api.customer.com/v1/query
https://api.customer.com/v2/query  (breaking changes)
```

**Header-Based Versioning** (Alternative):
```
GET /api/query
Accept: application/vnd.genai.v1+json
```

**Backwards Compatibility**:
- Maintain v1 for 12 months after v2 release
- Deprecation notices in response headers
- Migration guides for each version

---

## REST API Specification

### Core Endpoints

#### 1. Query API (RAG)

**POST /api/v1/query**

```json
// Request
{
  "query": "What are the key features of our product?",
  "session_id": "optional-session-123",
  "context": {
    "user_id": "customer-user-456",
    "metadata": {"department": "sales"}
  },
  "options": {
    "max_tokens": 500,
    "temperature": 0.7,
    "include_sources": true,
    "rerank": true
  }
}

// Response
{
  "answer": "The key features include...",
  "confidence": 0.92,
  "sources": [
    {
      "document_id": "doc-123",
      "document_name": "Product Spec.pdf",
      "page": 5,
      "score": 0.89,
      "snippet": "Key features: 1. AI-powered..."
    }
  ],
  "metadata": {
    "tokens_used": 342,
    "latency_ms": 1234,
    "model": "gpt-4o-mini",
    "pipeline": "hybrid"
  },
  "request_id": "req-abc123"
}
```

**Error Response**:
```json
{
  "error": {
    "code": "QUERY_FAILED",
    "message": "Failed to process query",
    "details": "Insufficient context in documents",
    "request_id": "req-abc123",
    "timestamp": "2026-01-03T10:30:00Z"
  }
}
```

---

#### 2. Document Management API

**POST /api/v1/documents**

```bash
# Upload document
curl -X POST https://api.customer.com/v1/documents \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@document.pdf" \
  -F "metadata={\"category\":\"product\",\"confidential\":false}"
```

```json
// Response
{
  "document_id": "doc-123",
  "filename": "document.pdf",
  "status": "processing",
  "processing_id": "proc-456",
  "estimated_completion": "2026-01-03T10:32:00Z",
  "webhook_url": "https://customer.com/webhooks/document-processed"
}
```

**GET /api/v1/documents**

```json
// Response
{
  "documents": [
    {
      "document_id": "doc-123",
      "filename": "Product Spec.pdf",
      "file_type": "application/pdf",
      "file_size": 2048576,
      "uploaded_at": "2026-01-03T10:00:00Z",
      "processed": true,
      "chunk_count": 45,
      "metadata": {"category": "product"}
    }
  ],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

**DELETE /api/v1/documents/{document_id}**

```json
// Response
{
  "status": "deleted",
  "document_id": "doc-123",
  "chunks_removed": 45
}
```

---

#### 3. Chat/Conversation API

**POST /api/v1/chat**

```json
// Request (streaming response)
{
  "message": "Tell me about our product",
  "session_id": "session-789",
  "stream": true,
  "options": {
    "max_tokens": 500,
    "temperature": 0.7
  }
}

// SSE Response (Server-Sent Events)
data: {"type":"start","request_id":"req-123"}

data: {"type":"token","content":"The"}

data: {"type":"token","content":" product"}

data: {"type":"token","content":" features"}

data: {"type":"sources","sources":[{"document_id":"doc-123","score":0.89}]}

data: {"type":"done","tokens_used":342}
```

**GET /api/v1/chat/sessions/{session_id}**

```json
// Response
{
  "session_id": "session-789",
  "created_at": "2026-01-03T09:00:00Z",
  "messages": [
    {
      "role": "user",
      "content": "Tell me about our product",
      "timestamp": "2026-01-03T09:01:00Z"
    },
    {
      "role": "assistant",
      "content": "The product features...",
      "sources": [...],
      "timestamp": "2026-01-03T09:01:05Z"
    }
  ],
  "metadata": {
    "total_messages": 2,
    "total_tokens": 850
  }
}
```

---

#### 4. Embeddings API

**POST /api/v1/embeddings**

```json
// Request
{
  "texts": [
    "This is a sample text",
    "Another piece of text"
  ],
  "model": "all-MiniLM-L6-v2"
}

// Response
{
  "embeddings": [
    [0.123, 0.456, 0.789, ...],  // 384-dim vector
    [0.234, 0.567, 0.890, ...]
  ],
  "model": "all-MiniLM-L6-v2",
  "dimensions": 384,
  "tokens_used": 20
}
```

---

#### 5. Search API

**POST /api/v1/search**

```json
// Request
{
  "query": "product specifications",
  "filters": {
    "category": "product",
    "date_range": {
      "start": "2025-01-01",
      "end": "2026-01-03"
    }
  },
  "limit": 10,
  "search_type": "hybrid"  // semantic | keyword | hybrid
}

// Response
{
  "results": [
    {
      "document_id": "doc-123",
      "document_name": "Product Spec.pdf",
      "page": 5,
      "score": 0.92,
      "snippet": "Technical specifications include...",
      "metadata": {"category": "product"}
    }
  ],
  "total_results": 25,
  "search_type": "hybrid"
}
```

---

#### 6. Batch Processing API

**POST /api/v1/batch/query**

```json
// Request (process multiple queries in batch)
{
  "queries": [
    {"query": "What is the product cost?", "context": {"user_id": "user1"}},
    {"query": "What are the features?", "context": {"user_id": "user2"}},
    {"query": "What is the warranty?", "context": {"user_id": "user3"}}
  ],
  "options": {
    "parallel": true,
    "max_concurrent": 5
  }
}

// Response
{
  "batch_id": "batch-456",
  "status": "processing",
  "total_queries": 3,
  "webhook_url": "https://customer.com/webhooks/batch-complete"
}

// Later: GET /api/v1/batch/batch-456
{
  "batch_id": "batch-456",
  "status": "completed",
  "results": [
    {"query": "What is the product cost?", "answer": "...", "confidence": 0.89},
    {"query": "What are the features?", "answer": "...", "confidence": 0.92},
    {"query": "What is the warranty?", "answer": "...", "confidence": 0.87}
  ],
  "processing_time_ms": 3456
}
```

---

## GraphQL API

### Schema Definition

```graphql
# Root Query
type Query {
  # Query RAG system
  query(
    query: String!
    sessionId: String
    options: QueryOptions
  ): QueryResponse!

  # Get documents
  documents(
    sessionId: String
    category: String
    limit: Int = 20
    offset: Int = 0
  ): DocumentConnection!

  # Get chat session
  chatSession(sessionId: ID!): ChatSession

  # Search documents
  search(
    query: String!
    filters: SearchFilters
    limit: Int = 10
  ): [SearchResult!]!
}

# Mutation
type Mutation {
  # Upload document
  uploadDocument(
    file: Upload!
    metadata: JSON
  ): Document!

  # Send chat message
  sendMessage(
    sessionId: ID!
    message: String!
    options: MessageOptions
  ): Message!

  # Delete document
  deleteDocument(documentId: ID!): Boolean!
}

# Subscription (WebSocket)
type Subscription {
  # Listen to document processing
  documentProcessing(documentId: ID!): ProcessingStatus!

  # Listen to chat messages
  chatMessages(sessionId: ID!): Message!

  # Listen to query results
  queryResults(requestId: ID!): QueryResponse!
}

# Types
type QueryResponse {
  answer: String!
  confidence: Float!
  sources: [Source!]!
  metadata: QueryMetadata!
  requestId: ID!
}

type Source {
  documentId: ID!
  documentName: String!
  page: Int
  score: Float!
  snippet: String!
}

type Document {
  id: ID!
  filename: String!
  fileType: String!
  fileSize: Int!
  uploadedAt: DateTime!
  processed: Boolean!
  chunkCount: Int
  metadata: JSON
}

type ChatSession {
  id: ID!
  createdAt: DateTime!
  messages: [Message!]!
  totalMessages: Int!
  totalTokens: Int!
}

type Message {
  id: ID!
  role: Role!
  content: String!
  sources: [Source!]
  timestamp: DateTime!
}

enum Role {
  USER
  ASSISTANT
  SYSTEM
}

input QueryOptions {
  maxTokens: Int = 500
  temperature: Float = 0.7
  includeSources: Boolean = true
  rerank: Boolean = true
}

input SearchFilters {
  category: String
  dateRange: DateRangeInput
  metadata: JSON
}

input DateRangeInput {
  start: DateTime
  end: DateTime
}
```

### Example GraphQL Queries

**Query RAG System**:
```graphql
query GetAnswer {
  query(
    query: "What are the product features?"
    options: {
      maxTokens: 500
      temperature: 0.7
      includeSources: true
    }
  ) {
    answer
    confidence
    sources {
      documentName
      page
      score
      snippet
    }
    metadata {
      tokensUsed
      latencyMs
      model
    }
  }
}
```

**Upload and Track Document**:
```graphql
mutation UploadDoc {
  uploadDocument(
    file: $file
    metadata: {category: "product", confidential: false}
  ) {
    id
    filename
    processed
  }
}

subscription TrackProcessing($docId: ID!) {
  documentProcessing(documentId: $docId) {
    status
    progress
    chunksProcessed
    estimatedCompletion
  }
}
```

---

## WebSocket/SSE for Real-Time

### Server-Sent Events (SSE) for Streaming

**Endpoint**: `GET /api/v1/stream/query`

```javascript
// Client-side JavaScript
const eventSource = new EventSource(
  'https://api.customer.com/v1/stream/query?' +
  'query=What%20are%20the%20features&' +
  'api_key=YOUR_API_KEY'
);

eventSource.addEventListener('token', (e) => {
  const data = JSON.parse(e.data);
  console.log('Token:', data.content);
  // Append to UI
});

eventSource.addEventListener('sources', (e) => {
  const data = JSON.parse(e.data);
  console.log('Sources:', data.sources);
});

eventSource.addEventListener('done', (e) => {
  console.log('Complete');
  eventSource.close();
});

eventSource.addEventListener('error', (e) => {
  console.error('Error:', e);
  eventSource.close();
});
```

---

### WebSocket for Bi-Directional Communication

**Endpoint**: `ws://api.customer.com/v1/ws`

```javascript
// Client-side
const ws = new WebSocket('wss://api.customer.com/v1/ws');

ws.onopen = () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    api_key: 'YOUR_API_KEY'
  }));

  // Send query
  ws.send(JSON.stringify({
    type: 'query',
    query: 'What are the features?',
    session_id: 'session-123'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'auth_success':
      console.log('Authenticated');
      break;
    case 'token':
      console.log('Token:', data.content);
      break;
    case 'sources':
      console.log('Sources:', data.sources);
      break;
    case 'done':
      console.log('Complete');
      break;
    case 'error':
      console.error('Error:', data.error);
      break;
  }
};
```

---

## Webhook System (Customer → GenAI)

### Webhook Configuration

**POST /api/v1/webhooks**

```json
// Register webhook
{
  "url": "https://customer.com/webhooks/genai",
  "events": [
    "document.processed",
    "query.completed",
    "error.occurred"
  ],
  "secret": "webhook_secret_for_signature",
  "active": true
}

// Response
{
  "webhook_id": "webhook-123",
  "url": "https://customer.com/webhooks/genai",
  "events": ["document.processed", "query.completed", "error.occurred"],
  "created_at": "2026-01-03T10:00:00Z"
}
```

### Webhook Payload

**Event: `document.processed`**

```json
POST https://customer.com/webhooks/genai
Headers:
  X-GenAI-Event: document.processed
  X-GenAI-Signature: sha256=abcdef123456  # HMAC signature
  X-GenAI-Webhook-ID: webhook-123

Body:
{
  "event": "document.processed",
  "timestamp": "2026-01-03T10:05:00Z",
  "data": {
    "document_id": "doc-123",
    "filename": "Product Spec.pdf",
    "status": "completed",
    "chunk_count": 45,
    "processing_time_ms": 12345
  }
}
```

**Event: `query.completed`**

```json
{
  "event": "query.completed",
  "timestamp": "2026-01-03T10:06:00Z",
  "data": {
    "request_id": "req-abc123",
    "query": "What are the features?",
    "answer": "The key features include...",
    "confidence": 0.92,
    "sources": [...],
    "processing_time_ms": 1234
  }
}
```

### Webhook Verification (Security)

```python
# Customer-side webhook handler
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    """Verify GenAI webhook signature."""
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        f"sha256={expected_signature}",
        signature
    )

@app.post("/webhooks/genai")
async def handle_genai_webhook(request: Request):
    # Get signature from header
    signature = request.headers.get("X-GenAI-Signature")

    # Get payload
    payload = await request.body()

    # Verify
    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process event
    data = await request.json()
    event_type = data["event"]

    if event_type == "document.processed":
        # Handle document processing completion
        process_document_complete(data["data"])

    return {"status": "received"}
```

---

## Event-Driven Integration

### Event Bus Architecture

```
┌─────────────────────┐
│  GenAI Backend      │
│                     │
│  ┌───────────────┐ │
│  │ Event Emitter │ │──┐
│  └───────────────┘ │  │
└─────────────────────┘  │
                         │ Publish
                         ▼
              ┌──────────────────┐
              │   Kafka/RabbitMQ │
              │   (Event Bus)    │
              └────────┬─────────┘
                       │ Subscribe
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Customer A  │ │ Customer B  │ │ Webhook     │
│ Consumer    │ │ Consumer    │ │ Dispatcher  │
└─────────────┘ └─────────────┘ └─────────────┘
```

### Event Schema

**Topic: `genai.documents`**

```json
{
  "event_id": "evt-123",
  "event_type": "document.processed",
  "timestamp": "2026-01-03T10:05:00Z",
  "tenant_id": "customer-456",
  "data": {
    "document_id": "doc-123",
    "filename": "Product Spec.pdf",
    "status": "completed",
    "chunk_count": 45
  }
}
```

**Topic: `genai.queries`**

```json
{
  "event_id": "evt-124",
  "event_type": "query.completed",
  "timestamp": "2026-01-03T10:06:00Z",
  "tenant_id": "customer-456",
  "data": {
    "request_id": "req-abc123",
    "query": "What are the features?",
    "answer": "...",
    "confidence": 0.92
  }
}
```

### Kafka Consumer (Customer-Side)

```python
from kafka import KafkaConsumer
import json

# Customer's Kafka consumer
consumer = KafkaConsumer(
    'genai.documents',
    'genai.queries',
    bootstrap_servers=['kafka.customer.com:9092'],
    group_id='customer-app',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    event = message.value

    if event['event_type'] == 'document.processed':
        # Handle document processing
        update_document_status(event['data']['document_id'], 'processed')

    elif event['event_type'] == 'query.completed':
        # Handle query completion
        send_answer_to_user(event['data']['answer'])
```

---

## Authentication & Authorization

### API Key Authentication

**Header-Based**:
```bash
curl -X POST https://api.customer.com/v1/query \
  -H "X-API-Key: sk_live_abc123def456" \
  -H "Content-Type: application/json" \
  -d '{"query":"What are the features?"}'
```

**Bearer Token**:
```bash
curl -X POST https://api.customer.com/v1/query \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"What are the features?"}'
```

### OAuth 2.0 (Enterprise)

**Authorization Code Flow**:

```
1. Customer app redirects user to GenAI OAuth endpoint
   https://auth.customer.com/oauth/authorize?
     client_id=YOUR_CLIENT_ID&
     redirect_uri=https://customer-app.com/callback&
     response_type=code&
     scope=query:read documents:write

2. User authorizes

3. GenAI redirects back with code
   https://customer-app.com/callback?code=AUTH_CODE

4. Customer app exchanges code for token
   POST https://auth.customer.com/oauth/token
   {
     "grant_type": "authorization_code",
     "code": "AUTH_CODE",
     "client_id": "YOUR_CLIENT_ID",
     "client_secret": "YOUR_CLIENT_SECRET"
   }

5. Response
   {
     "access_token": "eyJhbGc...",
     "token_type": "Bearer",
     "expires_in": 3600,
     "refresh_token": "def456...",
     "scope": "query:read documents:write"
   }

6. Use access token for API calls
   curl -H "Authorization: Bearer eyJhbGc..."
```

### JWT Token Validation

```python
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/v1/query")
async def query(request: QueryRequest, user = Depends(verify_token)):
    # user contains decoded JWT payload
    # { "user_id": "user-123", "tenant_id": "customer-456", "scopes": ["query:read"] }
    pass
```

### Role-Based Access Control (RBAC)

```python
from enum import Enum
from fastapi import Depends

class Permission(str, Enum):
    QUERY_READ = "query:read"
    QUERY_WRITE = "query:write"
    DOCUMENTS_READ = "documents:read"
    DOCUMENTS_WRITE = "documents:write"
    ADMIN = "admin"

def require_permission(permission: Permission):
    """Dependency to check user has required permission."""
    async def check_permission(user = Depends(verify_token)):
        if permission.value not in user.get("scopes", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return check_permission

@app.post("/api/v1/query")
async def query(
    request: QueryRequest,
    user = Depends(require_permission(Permission.QUERY_READ))
):
    # Only users with query:read permission can call this
    pass

@app.delete("/api/v1/documents/{document_id}")
async def delete_document(
    document_id: str,
    user = Depends(require_permission(Permission.DOCUMENTS_WRITE))
):
    # Only users with documents:write permission can delete
    pass
```

---

## SDK Generation

### Auto-Generated Client Libraries

**Python SDK**:

```python
# pip install genai-client

from genai_client import GenAIClient

# Initialize client
client = GenAIClient(
    api_key="YOUR_API_KEY",
    base_url="https://api.customer.com"
)

# Query RAG system
response = client.query(
    query="What are the product features?",
    options={
        "max_tokens": 500,
        "temperature": 0.7,
        "include_sources": True
    }
)

print(f"Answer: {response.answer}")
print(f"Confidence: {response.confidence}")
for source in response.sources:
    print(f"  - {source.document_name} (page {source.page})")

# Upload document
document = client.documents.upload(
    file_path="./product_spec.pdf",
    metadata={"category": "product"}
)
print(f"Uploaded: {document.id}")

# Stream chat
for chunk in client.chat.stream(
    message="Tell me about the product",
    session_id="session-123"
):
    print(chunk.content, end="", flush=True)

# Batch queries
batch = client.batch.query([
    {"query": "What is the cost?"},
    {"query": "What are the features?"},
    {"query": "What is the warranty?"}
])
print(f"Batch ID: {batch.id}")

# Wait for completion
results = batch.wait()
for result in results:
    print(f"Q: {result.query}")
    print(f"A: {result.answer}\n")
```

**JavaScript/TypeScript SDK**:

```typescript
// npm install @genai/client

import { GenAIClient } from '@genai/client';

// Initialize
const client = new GenAIClient({
  apiKey: 'YOUR_API_KEY',
  baseUrl: 'https://api.customer.com'
});

// Query
const response = await client.query({
  query: 'What are the product features?',
  options: {
    maxTokens: 500,
    temperature: 0.7,
    includeSources: true
  }
});

console.log('Answer:', response.answer);
console.log('Confidence:', response.confidence);

// Upload document
const document = await client.documents.upload({
  file: fileInput.files[0],
  metadata: { category: 'product' }
});

// Stream chat
const stream = client.chat.stream({
  message: 'Tell me about the product',
  sessionId: 'session-123'
});

for await (const chunk of stream) {
  process.stdout.write(chunk.content);
}

// WebSocket connection
const ws = client.connect();
ws.on('message', (data) => {
  console.log('Received:', data);
});
ws.send({ type: 'query', query: 'What are the features?' });
```

**Java SDK**:

```java
// Maven: com.genai:client:1.0.0

import com.genai.client.GenAIClient;
import com.genai.client.models.*;

// Initialize
GenAIClient client = new GenAIClient.Builder()
    .apiKey("YOUR_API_KEY")
    .baseUrl("https://api.customer.com")
    .build();

// Query
QueryRequest request = new QueryRequest.Builder()
    .query("What are the product features?")
    .options(new QueryOptions.Builder()
        .maxTokens(500)
        .temperature(0.7)
        .includeSources(true)
        .build())
    .build();

QueryResponse response = client.query(request);
System.out.println("Answer: " + response.getAnswer());
System.out.println("Confidence: " + response.getConfidence());

// Upload document
File file = new File("product_spec.pdf");
Document document = client.documents().upload(file, Map.of("category", "product"));
System.out.println("Document ID: " + document.getId());

// Stream chat
client.chat().stream("Tell me about the product", "session-123")
    .forEach(chunk -> System.out.print(chunk.getContent()));
```

**C# SDK**:

```csharp
// NuGet: GenAI.Client

using GenAI.Client;

// Initialize
var client = new GenAIClient("YOUR_API_KEY", "https://api.customer.com");

// Query
var response = await client.QueryAsync(new QueryRequest
{
    Query = "What are the product features?",
    Options = new QueryOptions
    {
        MaxTokens = 500,
        Temperature = 0.7,
        IncludeSources = true
    }
});

Console.WriteLine($"Answer: {response.Answer}");
Console.WriteLine($"Confidence: {response.Confidence}");

// Upload document
var document = await client.Documents.UploadAsync(
    "product_spec.pdf",
    new { category = "product" }
);

// Stream chat
await foreach (var chunk in client.Chat.StreamAsync("Tell me about the product", "session-123"))
{
    Console.Write(chunk.Content);
}
```

---

## API Gateway Layer

### Kong API Gateway Configuration

```yaml
# kong.yml - API Gateway configuration

services:
  - name: genai-api
    url: http://backend:8000
    routes:
      - name: api-routes
        paths:
          - /api/v1
        strip_path: false
    plugins:
      # Rate limiting
      - name: rate-limiting
        config:
          minute: 100
          hour: 1000
          policy: local

      # Authentication
      - name: key-auth
        config:
          key_names:
            - X-API-Key
            - Authorization

      # Request transformation
      - name: request-transformer
        config:
          add:
            headers:
              - X-Gateway-Timestamp:$(date +%s)
              - X-Request-ID:$(uuidgen)

      # Response transformation
      - name: response-transformer
        config:
          add:
            headers:
              - X-RateLimit-Remaining:$(remaining)
              - X-RateLimit-Reset:$(reset)

      # CORS
      - name: cors
        config:
          origins:
            - https://customer-app.com
          methods:
            - GET
            - POST
            - PUT
            - DELETE
          headers:
            - Authorization
            - Content-Type
          credentials: true

      # Caching
      - name: proxy-cache
        config:
          strategy: memory
          content_type:
            - application/json
          cache_ttl: 300

      # Request logging
      - name: file-log
        config:
          path: /var/log/kong/api-access.log

      # Circuit breaker
      - name: circuit-breaker
        config:
          threshold: 10
          window_size: 60
          recovery_time: 30
```

### Rate Limiting Configuration

```python
# backend/app/api/middleware/rate_limiter.py

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
from typing import Dict

class RateLimiter:
    """In-memory rate limiter with sliding window."""

    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)

    async def check_rate_limit(
        self,
        request: Request,
        limit: int = 100,
        window: int = 60
    ):
        """Check if request exceeds rate limit."""
        # Get identifier (API key or IP)
        api_key = request.headers.get("X-API-Key") or request.client.host

        # Current time
        now = time.time()

        # Remove old requests outside window
        self.requests[api_key] = [
            ts for ts in self.requests[api_key]
            if now - ts < window
        ]

        # Check limit
        if len(self.requests[api_key]) >= limit:
            reset_time = int(self.requests[api_key][0] + window)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time - int(now))
                }
            )

        # Add current request
        self.requests[api_key].append(now)

        # Add headers
        request.state.rate_limit_remaining = limit - len(self.requests[api_key])
        request.state.rate_limit_reset = int(now + window)

# Middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/v1"):
        await rate_limiter.check_rate_limit(request)

    response = await call_next(request)

    # Add rate limit headers
    if hasattr(request.state, "rate_limit_remaining"):
        response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
        response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)

    return response
```

---

## Bi-Directional Data Sync

### Use Case: Salesforce Integration

**Scenario**: Sync Salesforce opportunity data to GenAI, get insights back

```python
# backend/app/integrations/salesforce_sync.py

from simple_salesforce import Salesforce
import asyncio

class SalesforceIntegration:
    """Bi-directional sync with Salesforce."""

    def __init__(self, username, password, security_token):
        self.sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token
        )

    async def sync_opportunities_to_genai(self, db):
        """Pull Salesforce opportunities and index in GenAI."""
        # Query Salesforce
        opportunities = self.sf.query(
            "SELECT Id, Name, Description, Amount, StageName "
            "FROM Opportunity WHERE StageName IN ('Prospecting', 'Qualification')"
        )

        for opp in opportunities['records']:
            # Create document in GenAI
            document_text = f"""
            Opportunity: {opp['Name']}
            Amount: ${opp['Amount']}
            Stage: {opp['StageName']}
            Description: {opp['Description']}
            """

            # Store in GenAI (will be vectorized)
            await document_service.store_text_document(
                db=db,
                content=document_text,
                filename=f"salesforce_opp_{opp['Id']}.txt",
                metadata={
                    "source": "salesforce",
                    "type": "opportunity",
                    "salesforce_id": opp['Id'],
                    "stage": opp['StageName']
                }
            )

        return len(opportunities['records'])

    async def update_salesforce_with_insights(self, opportunity_id, insights):
        """Push GenAI insights back to Salesforce."""
        # Update Salesforce opportunity
        self.sf.Opportunity.update(
            opportunity_id,
            {
                'GenAI_Insights__c': insights['summary'],
                'Recommended_Action__c': insights['recommended_action'],
                'Confidence_Score__c': insights['confidence']
            }
        )

# Scheduled sync job (Prefect/Celery)
@prefect.task
async def sync_salesforce_bidirectional():
    """Bi-directional sync job."""

    # 1. Pull from Salesforce to GenAI
    synced_count = await salesforce.sync_opportunities_to_genai(db)
    print(f"Synced {synced_count} opportunities to GenAI")

    # 2. Generate insights for each opportunity
    opportunities = await db.execute(
        "SELECT * FROM documents WHERE metadata->>'source' = 'salesforce'"
    )

    for opp in opportunities:
        # Query GenAI for insights
        insights = await rag_service.query(
            query=f"What are the key insights for opportunity {opp.metadata['salesforce_id']}?",
            session_id=None
        )

        # Push back to Salesforce
        await salesforce.update_salesforce_with_insights(
            opp.metadata['salesforce_id'],
            {
                'summary': insights['answer'],
                'recommended_action': extract_action(insights['answer']),
                'confidence': insights['confidence']
            }
        )

# Schedule: Run every hour
@prefect.flow(schedule=IntervalSchedule(interval=timedelta(hours=1)))
async def salesforce_sync_flow():
    await sync_salesforce_bidirectional()
```

---

## Integration Examples

### Example 1: React Application Integration

```tsx
// React component using GenAI API

import React, { useState } from 'react';
import { GenAIClient } from '@genai/client';

const client = new GenAIClient({
  apiKey: process.env.REACT_APP_GENAI_API_KEY,
  baseUrl: 'https://api.customer.com'
});

export const ChatComponent: React.FC = () => {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const handleQuery = async () => {
    setLoading(true);
    try {
      const response = await client.query({
        query,
        options: {
          maxTokens: 500,
          includeSources: true
        }
      });
      setAnswer(response.answer);
    } catch (error) {
      console.error('Query failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-component">
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask a question..."
      />
      <button onClick={handleQuery} disabled={loading}>
        {loading ? 'Loading...' : 'Ask'}
      </button>
      {answer && (
        <div className="answer">
          <h3>Answer:</h3>
          <p>{answer}</p>
        </div>
      )}
    </div>
  );
};
```

---

### Example 2: Python Backend Integration

```python
# Django/Flask app integrating with GenAI

from genai_client import GenAIClient
from flask import Flask, request, jsonify

app = Flask(__name__)
client = GenAIClient(
    api_key=os.environ['GENAI_API_KEY'],
    base_url='https://api.customer.com'
)

@app.route('/api/search', methods=['POST'])
def search_documents():
    """Search customer documents using GenAI."""
    data = request.json

    # Query GenAI
    response = client.query(
        query=data['query'],
        options={
            'max_tokens': 500,
            'include_sources': True
        }
    )

    return jsonify({
        'answer': response.answer,
        'confidence': response.confidence,
        'sources': [
            {
                'name': s.document_name,
                'page': s.page,
                'snippet': s.snippet
            }
            for s in response.sources
        ]
    })

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Upload document to GenAI."""
    file = request.files['file']

    # Upload to GenAI
    document = client.documents.upload(
        file=file,
        metadata={
            'uploaded_by': request.user.id,
            'category': request.form.get('category')
        }
    )

    return jsonify({
        'document_id': document.id,
        'status': 'processing'
    })
```

---

### Example 3: Mobile App Integration (React Native)

```typescript
// React Native app using GenAI

import { GenAIClient } from '@genai/client';
import { useState } from 'react';
import { View, TextInput, Button, Text } from 'react-native';

const client = new GenAIClient({
  apiKey: process.env.GENAI_API_KEY,
  baseUrl: 'https://api.customer.com'
});

export const ChatScreen = () => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);

  const sendMessage = async () => {
    // Add user message
    setMessages([...messages, { role: 'user', content: query }]);

    // Stream response
    const stream = client.chat.stream({
      message: query,
      sessionId: 'mobile-session-123'
    });

    let assistantMessage = '';
    for await (const chunk of stream) {
      assistantMessage += chunk.content;
      // Update UI with streaming response
      setMessages([
        ...messages,
        { role: 'user', content: query },
        { role: 'assistant', content: assistantMessage }
      ]);
    }

    setQuery('');
  };

  return (
    <View>
      {messages.map((msg, idx) => (
        <Text key={idx}>{msg.role}: {msg.content}</Text>
      ))}
      <TextInput
        value={query}
        onChangeText={setQuery}
        placeholder="Ask a question..."
      />
      <Button title="Send" onPress={sendMessage} />
    </View>
  );
};
```

---

## Monitoring & Analytics

### API Metrics Dashboard

**Prometheus Metrics**:

```python
# backend/app/api/middleware/metrics.py

from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

api_active_requests = Gauge(
    'api_active_requests',
    'Active API requests',
    ['endpoint']
)

tokens_used_total = Counter(
    'tokens_used_total',
    'Total tokens used',
    ['model']
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    # Track active requests
    api_active_requests.labels(endpoint=request.url.path).inc()

    # Track request duration
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    # Record metrics
    api_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    api_request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    api_active_requests.labels(endpoint=request.url.path).dec()

    return response
```

**Grafana Dashboard Queries**:

```promql
# Request rate (requests per second)
rate(api_requests_total[5m])

# Average latency
rate(api_request_duration_seconds_sum[5m]) / rate(api_request_duration_seconds_count[5m])

# Error rate
rate(api_requests_total{status=~"5.."}[5m]) / rate(api_requests_total[5m])

# Active requests
sum(api_active_requests)

# Token usage per model
rate(tokens_used_total[1h])
```

---

## Implementation Roadmap

### Phase 1: Core API Layer (Weeks 1-2)

**Week 1**:
- ✅ REST API endpoints (query, documents, chat, search)
- ✅ Request/response schemas (Pydantic)
- ✅ Error handling and validation
- ✅ API versioning setup

**Week 2**:
- ✅ GraphQL API (Strawberry)
- ✅ WebSocket/SSE implementation
- ✅ Authentication (API keys, JWT)
- ✅ Rate limiting

**Deliverables**:
- Functional REST + GraphQL APIs
- WebSocket streaming
- Basic auth + rate limiting

---

### Phase 2: Webhook & Event System (Weeks 3-4)

**Week 3**:
- ✅ Webhook registration system
- ✅ Event emitter in backend
- ✅ Signature verification
- ✅ Retry logic for failed webhooks

**Week 4**:
- ✅ Kafka/RabbitMQ integration
- ✅ Event consumers
- ✅ Dead letter queue
- ✅ Event replay capability

**Deliverables**:
- Webhook system with retries
- Event-driven architecture
- Customer event consumers

---

### Phase 3: SDK Generation (Weeks 5-6)

**Week 5**:
- ✅ OpenAPI spec generation
- ✅ Python SDK (auto-generated)
- ✅ JavaScript/TypeScript SDK
- ✅ SDK documentation

**Week 6**:
- ✅ Java SDK
- ✅ C# SDK
- ✅ Go SDK (optional)
- ✅ SDK examples and tutorials

**Deliverables**:
- 5 language SDKs
- Comprehensive documentation
- Code examples

---

### Phase 4: API Gateway & Security (Weeks 7-8)

**Week 7**:
- ✅ Kong API Gateway setup
- ✅ OAuth2 implementation
- ✅ RBAC system
- ✅ API key management UI

**Week 8**:
- ✅ Advanced rate limiting (per-tier)
- ✅ Request transformation
- ✅ Response caching
- ✅ Circuit breaker

**Deliverables**:
- Production-ready API Gateway
- Enterprise auth (OAuth2 + RBAC)
- Advanced security features

---

### Phase 5: Integration Examples (Weeks 9-10)

**Week 9**:
- ✅ React integration example
- ✅ Python (Django/Flask) example
- ✅ React Native mobile example
- ✅ Salesforce bi-directional sync

**Week 10**:
- ✅ HubSpot integration
- ✅ Slack bot integration
- ✅ Zapier/Make.com connectors
- ✅ Custom webhooks cookbook

**Deliverables**:
- 8+ integration examples
- Bi-directional sync patterns
- Integration cookbook

---

### Phase 6: Monitoring & Documentation (Weeks 11-12)

**Week 11**:
- ✅ Prometheus metrics
- ✅ Grafana dashboards
- ✅ API usage analytics
- ✅ Customer-facing analytics portal

**Week 12**:
- ✅ OpenAPI/Swagger docs
- ✅ Postman collections
- ✅ Interactive API explorer
- ✅ Video tutorials

**Deliverables**:
- Complete API documentation
- Monitoring dashboards
- Analytics portal
- Video tutorials

---

## Summary

### What This Adds to Export Wizard

1. **API-First Architecture** - Customers can consume GenAI as headless service
2. **Multiple Integration Patterns** - REST, GraphQL, WebSocket, Webhooks, Event Bus
3. **Bi-Directional Sync** - Data flows both ways (customer ↔ GenAI)
4. **Auto-Generated SDKs** - 5+ language support out of box
5. **Enterprise Security** - OAuth2, RBAC, API Gateway
6. **Real-Time Capabilities** - Streaming responses, WebSocket, SSE
7. **Event-Driven** - Kafka/RabbitMQ for async messaging
8. **Embeddable UI** - Web Components, iframe widgets

### Timeline & Resources

- **Timeline**: 12 weeks (3 months)
- **Team**: 4-5 engineers
  - 2 backend engineers (API development)
  - 1 frontend engineer (SDK + widgets)
  - 1 DevOps engineer (API Gateway, monitoring)
  - 1 technical writer (documentation)

### Cost Estimate

- **Development**: $250K - $350K
- **Total Export Wizard + API Layer**: $650K - $950K

### Revenue Impact

- **API Tier Pricing**:
  - **Tier 4 - Starter**: $50K/year + $0.001/API call
  - **Tier 4 - Professional**: $100K/year + $0.0005/API call
  - **Tier 4 - Enterprise**: $250K/year + unlimited API calls

- **Year 1 Revenue Projection**: $3M (20 customers × $150K avg)
- **ROI**: 450% in Year 1

---

**Next Steps**: Integrate this API Integration Layer into ENTERPRISE_EXPORT_WIZARD_COMPLETE_IMPLEMENTATION_PLAN.md as Phase 7.

