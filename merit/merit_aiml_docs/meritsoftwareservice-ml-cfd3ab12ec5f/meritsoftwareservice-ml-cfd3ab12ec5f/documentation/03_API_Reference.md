# Merit ML Platform - API Reference
## Complete API Documentation

---

## Table of Contents
1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [Endpoints](#endpoints)
   - [Health Check](#health-check)
   - [Named Entity Recognition](#named-entity-recognition-ner)
   - [Relation Extraction](#relation-extraction-rel)
   - [QA Indexer](#qa-indexer)
   - [QA Chat](#qa-chat)
   - [Talend Pulse](#talend-pulse)
5. [Response Codes](#response-codes)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)

---

## API Overview

**Base URL**: `http://<server-ip>:5001`

**Protocol**: HTTP/HTTPS

**Content-Type**: `application/json`

**Authentication**: HTTP Basic Auth (required on all endpoints except health check)

**API Version**: 1.0.0

---

## Authentication

All API endpoints (except `/`) require HTTP Basic Authentication.

### Setting Up Credentials

Credentials are configured via environment variables:

```bash
# .env file
usr=your_api_username
pwd=your_secure_password
```

### Making Authenticated Requests

**cURL**:
```bash
curl -u username:password \
  -X POST http://localhost:5001/ner \
  -H "Content-Type: application/json" \
  -d '{"fileId": "doc_001", "path": "document.pdf", "labels": ["person", "organization"]}'
```

**Python**:
```python
import requests

response = requests.post(
    "http://localhost:5001/ner",
    auth=("username", "password"),
    json={
        "fileId": "doc_001",
        "path": "document.pdf",
        "labels": ["person", "organization"]
    }
)
```

**JavaScript**:
```javascript
const response = await fetch('http://localhost:5001/ner', {
  method: 'POST',
  headers: {
    'Authorization': 'Basic ' + btoa('username:password'),
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    fileId: 'doc_001',
    path: 'document.pdf',
    labels: ['person', 'organization']
  })
});
```

### Authentication Errors

**401 Unauthorized**:
```json
{
  "error": "Unauthorized",
  "message": "The server could not verify that you are authorized to access the URL requested."
}
```

---

## Common Patterns

### Request ID Pattern

All endpoints (except health check) return a `request_id` for tracking:

```json
{
  "message": "Value added to the stream",
  "request_id": "a3d7f821-9c4e-4b5a-b3d1-f9e8d7c6b5a4"
}
```

Use the `request_id` to poll the status stream for results.

### Status Stream Polling

Results are published to the status stream. Poll using Redis client:

```python
import redis

redis_client = redis.StrictRedis(
    host='172.27.140.191',
    port=6380,
    password='redis_password',
    decode_responses=True
)

# Poll status stream
messages = redis_client.xread({
    'status_stream_kn': '0'  # or use last_id for incremental polling
}, count=10, block=5000)

for stream, entries in messages:
    for message_id, data in entries:
        if data.get('request_id') == your_request_id:
            print(data)
```

### Work Mode Suffixes

Stream names vary by deployment mode:

- **Production**: `status_stream_kn`
- **Development**: `status_stream_kn_dev`
- **Testing**: `status_stream_kn_test`

Configure via environment variable:
```bash
work_mode=""        # Production
work_mode="_dev"    # Development
work_mode="_test"   # Testing
```

---

## Endpoints

### Health Check

**Endpoint**: `GET /` or `POST /`

**Description**: Verify API server is running

**Authentication**: Not required

**Request**:
```bash
curl http://localhost:5001/
```

**Response**:
```
welcome
```

**Status Code**: `200 OK`

---

### Named Entity Recognition (NER)

**Endpoint**: `POST /ner`

**Description**: Extract named entities from PDF documents using zero-shot GLiNER model

**Authentication**: Required

#### Request Schema

```json
{
  "fileId": "string (required)",
  "path": "string (required, must end with .pdf)",
  "labels": ["string", "string", ...] (required, min 3 chars each)
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fileId` | string | Yes | Unique identifier for the document |
| `path` | string | Yes | File path to PDF (local or SFTP). Must end with `.pdf` |
| `labels` | array[string] | Yes | Entity types to extract. Each label must be ≥ 3 characters |

#### Example Request

```bash
curl -u username:password \
  -X POST http://localhost:5001/ner \
  -H "Content-Type: application/json" \
  -d '{
    "fileId": "contract_001",
    "path": "/documents/contract.pdf",
    "labels": ["person", "organization", "location", "date", "amount"]
  }'
```

#### Success Response

```json
{
  "message": "Value added to the stream",
  "request_id": "f9e8d7c6-b5a4-4321-9876-1234567890ab"
}
```

**Status Code**: `200 OK`

#### Status Stream Response

Poll `status_stream_kn` for results:

```json
{
  "request_id": "f9e8d7c6-b5a4-4321-9876-1234567890ab",
  "fileId": "contract_001",
  "path": "/documents/contract.pdf",
  "page": "1",
  "chunk": "1",
  "text": "John Doe works at Acme Corp in New York...",
  "entities": "[{\"entity\": \"person\", \"span\": \"John Doe\", \"start\": 0, \"end\": 8, \"score\": 0.95}, {\"entity\": \"organization\", \"span\": \"Acme Corp\", \"start\": 18, \"end\": 27, \"score\": 0.92}]",
  "status": "Done",
  "EOF": "True"
}
```

#### Entity Schema

Each entity contains:
```json
{
  "entity": "person",           // Entity type/label
  "span": "John Doe",           // Extracted text
  "start": 0,                   // Character start position
  "end": 8,                     // Character end position
  "score": 0.95                 // Confidence score (0-1)
}
```

#### Validation Errors

**Invalid label length**:
```json
{
  "issues": [
    {
      "error": "value_error",
      "key": "labels",
      "msg": "Invalid labels (req. min 3 chars): ['ab', 'person']"
    }
  ]
}
```

**Invalid file type**:
```json
{
  "issues": [
    {
      "error": "value_error",
      "key": "path",
      "msg": "Invalid file type - supported type [pdf]: document.txt"
    }
  ]
}
```

---

### Relation Extraction (REL)

**Endpoint**: `POST /rel`

**Description**: Extract relationships between entities in documents. **Requires prior NER processing** on the same `fileId`.

**Authentication**: Required

#### Request Schema

```json
{
  "fileId": "string (required)",
  "path": "string (required, must end with .pdf)"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fileId` | string | Yes | Document identifier (must have existing NER results) |
| `path` | string | Yes | File path to PDF. Must end with `.pdf` |

#### Example Request

```bash
curl -u username:password \
  -X POST http://localhost:5001/rel \
  -H "Content-Type: application/json" \
  -d '{
    "fileId": "contract_001",
    "path": "/documents/contract.pdf"
  }'
```

#### Success Response

```json
{
  "message": "Value added to the stream",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Status Code**: `200 OK`

#### Status Stream Response

```json
{
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "fileId": "contract_001",
  "path": "/documents/contract.pdf",
  "page": "1",
  "chunk": "1",
  "text": "John Doe works at Acme Corp...",
  "relation": "[{\"head\": \"John Doe\", \"relation\": \"works_at\", \"tail\": \"Acme Corp\"}, {\"head\": \"Acme Corp\", \"relation\": \"located_in\", \"tail\": \"New York\"}]",
  "status": "Done",
  "EOF": "True"
}
```

#### Relationship Schema

Each relationship contains:
```json
{
  "head": "John Doe",           // Source entity
  "relation": "works_at",       // Relationship type
  "tail": "Acme Corp"           // Target entity
}
```

#### Notes

- Relation extraction requires existing NER results in cache (`ner_rel_tbl`)
- If no entities found, returns empty array: `"relation": "[]"`
- Processes after all chunks with `EOF=True` are ready
- Automatically deduplicates entities by span

#### Error Scenarios

**No NER results found**:
```json
{
  "request_id": "...",
  "fileId": "contract_001",
  "status": "Failed",
  "error": "Entity not found"
}
```

---

### QA Indexer

**Endpoint**: `POST /qa_indexer`

**Description**: Index PDF documents for question answering. Creates vector embeddings and stores in ChromaDB.

**Authentication**: Required

#### Request Schema

```json
{
  "input_files": [
    {
      "fileId": "string (required)",
      "path": "string (required, must end with .pdf)"
    }
  ]
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input_files` | array[object] | Yes | List of PDF files to index |
| `input_files[].fileId` | string | Yes | Unique identifier for each file |
| `input_files[].path` | string | Yes | File path to PDF. Must end with `.pdf` |

#### Example Request

```bash
curl -u username:password \
  -X POST http://localhost:5001/qa_indexer \
  -H "Content-Type: application/json" \
  -d '{
    "input_files": [
      {
        "fileId": "manual_001",
        "path": "/docs/user_manual.pdf"
      },
      {
        "fileId": "manual_002",
        "path": "/docs/admin_guide.pdf"
      }
    ]
  }'
```

#### Success Response

```json
{
  "message": "Value added to the stream",
  "request_id": "12345678-90ab-cdef-1234-567890abcdef",
  "session_id": "abcdef12-3456-7890-abcd-ef1234567890"
}
```

**Status Code**: `200 OK`

**Important**: Save the `session_id` for subsequent QA chat requests.

#### Status Stream Response

```json
{
  "request_id": "12345678-90ab-cdef-1234-567890abcdef",
  "session_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "mode": "qa_indexer",
  "status": "Done"
}
```

#### Processing Steps

1. **Document Parsing**: PDF → Markdown conversion with header extraction
2. **Semantic Chunking**: Split by headers (H1, H2, H3) preserving context
3. **Embedding Generation**: BAAI/llm-embedder creates 768-dim vectors
4. **Vector Storage**: Stored in ChromaDB collection (name = `session_id`)
5. **Cache Cleanup**: Temporary data removed from `qa_tbl`

#### Notes

- Each indexing request creates a new `session_id`
- If files already parsed (in `doc_tbl`), reuses cached data
- ChromaDB collection cleared before indexing (overwrites previous session with same ID)
- Supports multiple files in single request

---

### QA Chat

**Endpoint**: `POST /qa_chat`

**Description**: Ask questions about indexed documents using RAG (Retrieval-Augmented Generation)

**Authentication**: Required

**Prerequisites**: Documents must be indexed via `/qa_indexer` first

#### Request Schema

```json
{
  "session_id": "string (required, min 5 chars)",
  "question": "string (required, min 5 chars)",
  "llm_model_name": "string (required, min 5 chars)",
  "model_provider_name": "string (required, min 3 chars)"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | Session ID from `/qa_indexer` response (min 5 chars) |
| `question` | string | Yes | Question to ask about the documents (min 5 chars) |
| `llm_model_name` | string | Yes | LLM model to use (e.g., `gpt-4o-mini`) |
| `model_provider_name` | string | Yes | LLM provider (e.g., `openai`, `groq`) |

#### Example Request

```bash
curl -u username:password \
  -X POST http://localhost:5001/qa_chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abcdef12-3456-7890-abcd-ef1234567890",
    "question": "What are the installation requirements?",
    "llm_model_name": "gpt-4o-mini",
    "model_provider_name": "openai"
  }'
```

#### Success Response

```json
{
  "message": "Value added to the stream",
  "request_id": "fedcba09-8765-4321-dcba-0987654321fe"
}
```

**Status Code**: `200 OK`

#### Status Stream Response

**Successful Answer**:
```json
{
  "request_id": "fedcba09-8765-4321-dcba-0987654321fe",
  "session_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "question": "What are the installation requirements?",
  "generation": "The installation requirements are: Python 3.8+, 16GB RAM, NVIDIA GPU with 8GB VRAM, and 50GB storage space.",
  "documents": "[{\"fileId\": \"manual_001\", \"path\": \"/docs/user_manual.pdf\", \"page\": \"5\", \"chunk\": \"2\", \"text\": \"System Requirements: Python 3.8+...\"}]",
  "mode": "qa_chat",
  "status": "Done"
}
```

**No Answer Found**:
```json
{
  "request_id": "fedcba09-8765-4321-dcba-0987654321fe",
  "session_id": "abcdef12-3456-7890-abcd-ef1234567890",
  "question": "What is the meaning of life?",
  "generation": "I don't know.",
  "documents": "[]",
  "mode": "qa_chat",
  "status": "Done"
}
```

**Session Not Found**:
```json
{
  "request_id": "fedcba09-8765-4321-dcba-0987654321fe",
  "session_id": "invalid-session-id",
  "generation": "Session not found",
  "documents": "[]",
  "status": "Failed"
}
```

#### Document Source Schema

Each source document contains:
```json
{
  "fileId": "manual_001",
  "path": "/docs/user_manual.pdf",
  "page": "5",
  "chunk": "2",
  "text": "Relevant text excerpt used to answer the question..."
}
```

#### RAG Pipeline

1. **Session Validation**: Check ChromaDB collection exists
2. **Retrieval**: MMR search retrieves 50 candidate chunks
3. **Reranking**: Cross-encoder reranks to top 3 most relevant
4. **Generation**: LLM generates answer using context
5. **Source Attribution**: Returns source documents with answer

#### Notes

- Session must exist (created via `/qa_indexer`)
- Answers only from indexed documents (not general knowledge)
- If answer not found in context, returns "I don't know."
- Supports multiple LLM providers (OpenAI, Groq, etc.)

---

### Talend Pulse

**Endpoint**: `POST /talend_pulse`

**Description**: Score candidate resumes against job descriptions for recruitment

**Authentication**: Required

#### Request Schema

```json
{
  "cv_files": [
    {
      "fileId": "string (required)",
      "path": "string (required, must end with .pdf)"
    }
  ],
  "jd_file": {
    "fileId": "string (required)",
    "path": "string (required, must end with .txt)"
  }
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cv_files` | array[object] | Yes | List of candidate resume PDFs |
| `cv_files[].fileId` | string | Yes | Unique identifier for resume |
| `cv_files[].path` | string | Yes | SFTP path to resume PDF |
| `jd_file` | object | Yes | Job description file |
| `jd_file.fileId` | string | Yes | Unique identifier for JD |
| `jd_file.path` | string | Yes | SFTP path to JD text file (`.txt`) |

#### Example Request

```bash
curl -u username:password \
  -X POST http://localhost:5001/talend_pulse \
  -H "Content-Type: application/json" \
  -d '{
    "jd_file": {
      "fileId": "jd_swe_001",
      "path": "/jds/software_engineer.txt"
    },
    "cv_files": [
      {
        "fileId": "cv_candidate_001",
        "path": "/resumes/john_doe.pdf"
      },
      {
        "fileId": "cv_candidate_002",
        "path": "/resumes/jane_smith.pdf"
      }
    ]
  }'
```

#### Success Response

```json
{
  "message": "Value added to the stream",
  "request_id": "11223344-5566-7788-99aa-bbccddeeff00"
}
```

**Status Code**: `200 OK`

#### Status Stream Response

**Per Candidate** (multiple messages, one per CV):

```json
{
  "request_id": "11223344-5566-7788-99aa-bbccddeeff00",
  "mode": "talend_pulse",
  "fileId": "cv_candidate_001",
  "path": "/resumes/john_doe.pdf",
  "response": "{\"Candidate Name\": \"John Doe\", \"Overall Score\": \"85\", \"Skill_score\": [{\"Specification\": \"Python_Skills\", \"Required\": \"Python\", \"Candidate Score\": \"9\", \"Candidate Justification\": \"5 years experience...\"}, ...]}",
  "file_status": "Done",
  "status": "In Progress"
}
```

**Final Message** (after all CVs processed):
```json
{
  "request_id": "11223344-5566-7788-99aa-bbccddeeff00",
  "mode": "talend_pulse",
  "fileId": "cv_candidate_002",
  "path": "/resumes/jane_smith.pdf",
  "response": "{...}",
  "file_status": "Done",
  "status": "Done"
}
```

#### Response Schema

The `response` field contains a JSON string with:

```json
{
  "Candidate Name": "John Doe",
  "Overall Score": "85",
  "Skill_score": [
    {
      "Specification": "Python_Skills",
      "Required": "Python",
      "Candidate Score": "9",
      "Candidate Justification": "Candidate has 5 years of Python experience with Django and Flask frameworks."
    },
    {
      "Specification": "Experience",
      "Required": "5+ years software development",
      "Candidate Score": "8",
      "Candidate Justification": "6 years of software development experience across multiple domains."
    }
  ]
}
```

#### Scoring System

- **Overall Score**: 0-100 aggregate score
- **Skill Scores**: 0-10 per requirement
- **Justifications**: AI-generated reasoning for each score

#### Notes

- Job description must be `.txt` file on SFTP server
- Resumes must be `.pdf` files on SFTP server
- Processing is sequential: JD parsed first, then each CV
- Status messages published per CV (allows real-time progress tracking)
- Final message has `"status": "Done"`

#### Failed CV Processing

```json
{
  "request_id": "11223344-5566-7788-99aa-bbccddeeff00",
  "fileId": "cv_candidate_003",
  "path": "/resumes/corrupted.pdf",
  "response": "{}",
  "file_status": "Failed",
  "status": "Done"
}
```

---

## Response Codes

| Code | Description | Scenario |
|------|-------------|----------|
| `200 OK` | Success | Request accepted and queued |
| `400 Bad Request` | Validation error | Invalid request schema or parameters |
| `401 Unauthorized` | Authentication failed | Missing or invalid credentials |
| `500 Internal Server Error` | Server error | Unexpected exception during processing |

---

## Error Handling

### Validation Errors (400)

**Pydantic validation failure**:
```json
{
  "issues": [
    {
      "error": "missing",
      "key": "fileId",
      "msg": "Field required"
    },
    {
      "error": "value_error",
      "key": "labels",
      "msg": "Invalid labels (req. min 3 chars): ['ab']"
    }
  ]
}
```

### HTTP Exceptions (400-500)

**Standard format**:
```json
{
  "error": "Bad Request",
  "message": "The browser (or proxy) sent a request that this server could not understand."
}
```

### Internal Server Errors (500)

```json
{
  "error": "Internal Server Error - <exception details>"
}
```

### Status Stream Errors

**Failed processing**:
```json
{
  "request_id": "...",
  "fileId": "...",
  "status": "Failed",
  "error": "Processing failed: <reason>"
}
```

**Dead letter queue**:
- Failed tasks moved to `<service>_dead_letter_stream` after max retries
- Check DLQ for permanently failed tasks

---

## Rate Limiting

**Current Implementation**: No hard rate limits

**Recommended Client-Side Limits**:
- Max 10 concurrent requests per service
- 100 requests/minute per API key
- Implement exponential backoff for retries

**Worker Capacity**:
- NER: 50 pages/minute
- Relation: 20 pages/minute
- QA Indexing: 100 pages/minute
- QA Chat: 10 queries/minute
- Talend Pulse: 5 CVs/minute

---

## Examples

### Complete NER Workflow

```python
import requests
import redis
import json
import time

# Configuration
API_URL = "http://localhost:5001"
AUTH = ("username", "password")
REDIS_HOST = "172.27.140.191"
REDIS_PORT = 6380
REDIS_PASSWORD = "redis_password"

# 1. Submit NER request
response = requests.post(
    f"{API_URL}/ner",
    auth=AUTH,
    json={
        "fileId": "contract_123",
        "path": "/documents/contract.pdf",
        "labels": ["person", "organization", "date", "amount"]
    }
)
request_id = response.json()["request_id"]
print(f"Request ID: {request_id}")

# 2. Poll status stream
redis_client = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

last_id = "0"
results = []

while True:
    messages = redis_client.xread(
        {"status_stream_kn": last_id},
        count=10,
        block=5000
    )

    if messages:
        for stream, entries in messages:
            for message_id, data in entries:
                last_id = message_id

                if data.get("request_id") == request_id:
                    print(f"Page {data['page']}, Chunk {data['chunk']}: {data['status']}")
                    results.append(data)

                    if data.get("EOF") == "True":
                        print("Processing complete!")
                        break

        if results and results[-1].get("EOF") == "True":
            break

    time.sleep(1)

# 3. Parse results
for result in results:
    entities = json.loads(result["entities"])
    print(f"\nPage {result['page']}, Chunk {result['chunk']}:")
    for entity in entities:
        print(f"  {entity['entity']}: {entity['span']} (score: {entity['score']:.2f})")
```

### Complete QA Workflow

```python
import requests
import redis
import json

API_URL = "http://localhost:5001"
AUTH = ("username", "password")

# 1. Index documents
index_response = requests.post(
    f"{API_URL}/qa_indexer",
    auth=AUTH,
    json={
        "input_files": [
            {"fileId": "manual_001", "path": "/docs/user_manual.pdf"},
            {"fileId": "manual_002", "path": "/docs/admin_guide.pdf"}
        ]
    }
)

session_id = index_response.json()["session_id"]
print(f"Session ID: {session_id}")

# Wait for indexing to complete (poll status stream)
# ... (similar to NER example)

# 2. Ask questions
questions = [
    "What are the installation requirements?",
    "How do I configure the database?",
    "What are the security best practices?"
]

for question in questions:
    response = requests.post(
        f"{API_URL}/qa_chat",
        auth=AUTH,
        json={
            "session_id": session_id,
            "question": question,
            "llm_model_name": "gpt-4o-mini",
            "model_provider_name": "openai"
        }
    )

    request_id = response.json()["request_id"]

    # Poll for answer
    # ... (poll status_stream_kn)

    print(f"\nQ: {question}")
    print(f"A: {answer['generation']}")
    print(f"Sources: {len(json.loads(answer['documents']))} documents")
```

### Talend Pulse Workflow

```python
import requests

API_URL = "http://localhost:5001"
AUTH = ("username", "password")

response = requests.post(
    f"{API_URL}/talend_pulse",
    auth=AUTH,
    json={
        "jd_file": {
            "fileId": "jd_001",
            "path": "/jds/senior_engineer.txt"
        },
        "cv_files": [
            {"fileId": "cv_001", "path": "/resumes/candidate_1.pdf"},
            {"fileId": "cv_002", "path": "/resumes/candidate_2.pdf"},
            {"fileId": "cv_003", "path": "/resumes/candidate_3.pdf"}
        ]
    }
)

request_id = response.json()["request_id"]

# Poll status stream for results
# Each CV will produce a separate status message
# Final message will have "status": "Done"

# Parse and rank candidates by Overall Score
```

---

## Best Practices

### 1. Request ID Management
- Always store `request_id` and `session_id` from responses
- Use request IDs for result tracking and debugging
- Include request IDs in logs and error reports

### 2. Status Stream Polling
- Use incremental polling with `last_id` to avoid re-reading messages
- Implement timeout logic (e.g., 5 minutes for NER/REL, 10 minutes for QA)
- Handle `EOF=True` flag to detect completion

### 3. Error Handling
- Always check HTTP status codes
- Parse validation errors from `issues` array
- Monitor dead-letter queues for permanent failures
- Implement retry logic with exponential backoff

### 4. Performance Optimization
- Cache frequently accessed documents
- Reuse QA sessions for multiple questions
- Batch file uploads when possible
- Use appropriate worker counts for load

### 5. Security
- Never hardcode credentials in code
- Use environment variables or secret managers
- Rotate API credentials regularly
- Use HTTPS in production

---

## API Client Libraries

### Python Client Example

```python
class MeritMLClient:
    def __init__(self, base_url, username, password, redis_config):
        self.base_url = base_url
        self.auth = (username, password)
        self.redis_client = redis.StrictRedis(**redis_config)

    def submit_ner(self, file_id, path, labels):
        response = requests.post(
            f"{self.base_url}/ner",
            auth=self.auth,
            json={"fileId": file_id, "path": path, "labels": labels}
        )
        response.raise_for_status()
        return response.json()["request_id"]

    def poll_results(self, request_id, timeout=300):
        start_time = time.time()
        last_id = "0"
        results = []

        while time.time() - start_time < timeout:
            messages = self.redis_client.xread(
                {"status_stream_kn": last_id},
                count=10,
                block=5000
            )

            for stream, entries in messages:
                for message_id, data in entries:
                    last_id = message_id
                    if data.get("request_id") == request_id:
                        results.append(data)
                        if data.get("EOF") == "True" or data.get("status") == "Done":
                            return results

            time.sleep(1)

        raise TimeoutError(f"Results not received within {timeout}s")

# Usage
client = MeritMLClient(
    base_url="http://localhost:5001",
    username="api_user",
    password="api_pass",
    redis_config={
        "host": "172.27.140.191",
        "port": 6380,
        "password": "redis_password",
        "decode_responses": True
    }
)

request_id = client.submit_ner("doc_001", "/docs/contract.pdf", ["person", "org"])
results = client.poll_results(request_id)
```

---

**Document Version**: 1.0.0
**Last Updated**: December 2024
**Platform**: Merit ML Platform - Knowledge Agent
