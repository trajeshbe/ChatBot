# GraphQL API Examples

This file contains example GraphQL queries and mutations for testing the RAG chatbot API.

## Access GraphQL Playground

Open your browser and navigate to: http://localhost:8000/graphql

## Example Queries

### 1. Simple Query (Fast RAG)

```graphql
query SimpleQuery {
  query(input: {
    query: "What documents do I have?"
    useCache: true
  }) {
    answer
    model
    tokensUsed
    latencyMs
    numSources
    cached
    sources {
      id
      filename
      sourceType
      relevance
      excerpt
    }
  }
}
```

### 2. Agentic Query (LangGraph Workflow)

```graphql
query AgenticQuery {
  agenticQuery(input: {
    query: "Analyze the key insights from my documents"
    useCache: false
  }) {
    answer
    model
    tokensUsed
    numSources
    sources {
      id
      filename
      sourceType
      sourceUrl
      relevance
      excerpt
    }
  }
}
```

### 3. Get All Documents

```graphql
query GetDocuments {
  documents {
    id
    filename
    fileType
    fileSize
    sourceType
    sourceUrl
    processed
    uploadDate
  }
}
```

## Example Mutations

### 1. Upload Document (Note: Use REST API for file uploads)

For file uploads, use the REST API endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/path/to/your/document.pdf"
```

### 2. Scrape Single URL

```graphql
mutation ScrapeURL {
  scrapeUrl(input: {
    url: "https://example.com/article"
    scrapePrompt: "Extract the main content and key points"
  }) {
    success
    jobId
    documentId
    title
    contentLength
    url
  }
}
```

### 3. Scrape Multiple URLs

```graphql
mutation ScrapeMultipleURLs {
  scrapeMultipleUrls(input: {
    urls: [
      "https://example.com/article1",
      "https://example.com/article2"
    ]
    scrapePrompt: "Extract main content"
  }) {
    success
    jobId
    documentId
    title
    contentLength
    url
    error
  }
}
```

## Testing with curl

### Query via REST API
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What documents do I have?" \
  -F "use_cache=true"
```

### Query via GraphQL
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { query(input: { query: \"Hello\", useCache: true }) { answer model } }"
  }'
```

## Frontend Usage

The frontend at http://localhost:3001 uses the REST API endpoints:
- Chat: `POST /api/v1/query`
- Upload: `POST /api/v1/upload`
- Scrape: `POST /api/v1/scrape`

## Troubleshooting

### Error: "Sorry, I encountered an error"
- **Cause**: Missing OpenAI API key
- **Fix**: Add your OpenAI API key to `.env` file:
  ```bash
  OPENAI_API_KEY=sk-your-actual-key-here
  ```
- Then restart the backend:
  ```bash
  docker compose restart backend
  ```

### Error: "Syntax Error: Unexpected <EOF>"
- **Cause**: Accessing GraphQL endpoint without a query
- **Fix**: Use the GraphQL playground at http://localhost:8000/graphql or send proper GraphQL queries

### No Documents Found
- Upload some documents first using the frontend or REST API
- Or scrape some URLs using the GraphQL mutation above

## Two Query Modes

The chatbot has two query modes:

1. **Simple Query** (`query`): Fast, direct RAG with caching
   - Best for: Simple questions, quick lookups
   - Features: Semantic caching, low latency

2. **Agentic Query** (`agenticQuery`): LangGraph workflow
   - Best for: Complex analysis, multi-step reasoning
   - Features: Intent analysis, validation, regeneration
   - Uses: LangGraph state machine with multiple nodes
