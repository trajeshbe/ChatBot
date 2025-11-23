# Validation Plan (/validate)

This runs through real user workflows described in README (upload → chat; web scraping; RAG answers) plus available tooling.

## Step 0: User Workflows (from docs)
- Upload documents (PDF/DOCX/TXT/JSON/MD) → automatic chunking/embedding → query in Chat tab.
- Web Scraping tab: submit URL (+ optional instructions) → content extracted/embedded → query with context.
- Chat/GraphQL: ask questions, get cited answers; model selection optional.

## Phase 1: Linting
- Backend (pylint): `cd backend && pylint app`
- Frontend (Next lint): `cd frontend && npm run lint`

## Phase 2: Type Checking
- Frontend TypeScript: `cd frontend && npx tsc --noEmit`

## Phase 3: Style Checking
- Backend formatting: `cd backend && black --check app tests`

## Phase 4: Unit/Integration Tests
- Backend tests: `cd backend && pytest tests -v`
- Legacy/top-level checks (optional extra coverage): `pytest test_rag_pipeline.py test_template_extraction_ui.py test_smart_template_mapping.py -v`

## Phase 5: End-to-End Workflows (mirror actual usage)
_Pre-flight: start stack (DB/Redis/MinIO/backend/frontend) and ensure deps installed._
```
docker-compose up -d postgres redis minio backend frontend
./scripts/setup/setup-database.sh  # if first run
```

### E2E-1 Upload → RAG Answer with Citations
1) Upload a sample doc:  
`curl -F "file=@docs/README.md" http://localhost:8000/api/v1/upload`
2) Ask a question via robust RAG pipeline:  
`curl -X POST http://localhost:8000/api/v1/rag-pipeline/query -H "Content-Type: application/json" -d '{"query":"What docs are available?","session_id":"sess-upload"}'`
3) Validate: response has `sources`/`citations`, `model_used`, `latency_ms`, `cache_hit` flag. Verify sources reference the uploaded file.

### E2E-2 Web Scraping → Retrieval
1) Scrape a URL into the KB:  
`curl -X POST http://localhost:8000/api/v1/scraper/scrape -H "Content-Type: application/json" -d '{"url":"https://example.com","scrape_prompt":"Extract main heading","session_id":"sess-scrape"}'`
2) Query using same session to prioritize scraped content:  
`curl -X POST http://localhost:8000/api/v1/rag-pipeline/query -H "Content-Type: application/json" -d '{"query":"What is the site about?","session_id":"sess-scrape"}'`
3) Validate: answer cites scraped source (filename/source_url) and shows session-short-term hits.

### E2E-3 Chat API (GraphQL/REST) Path Sanity
1) REST health check: `curl http://localhost:8000/health`
2) Direct LLM smoke test (dev-only):  
`curl -X POST http://localhost:8000/api/v1/llm/test -F "prompt=hello" -F "model_id=qwen2.5:1.5b"`
3) Optional GraphQL ping (ensure schema live):  
`curl -X POST http://localhost:8000/graphql -H "Content-Type: application/json" -d '{"query":"{ __typename }"}'`

### E2E-4 Project Estimator Agentic Workflow (LangGraph)
1) Run estimator endpoint with sample inputs:  
`curl -X POST http://localhost:8000/api/v1/project-estimator/generate-agentic -F "project_name=Sample App" -F "project_scope=Build a chat app" -F "requirements_file=@docs/README.md" -F "samples_file=@docs/features/project_estimator/samples/VISUALIZATION_GUIDE.md"`
2) Validate: response includes BRD/Cost outputs and workflow visualization fields; generated files present in response or storage.

### E2E-5 LangGraph Extraction Workflow (Scraper → Workflow DAG)
1) Trigger extraction workflow via API route (if exposed) or directly via script:  
`python - <<'PY'\nimport asyncio\nfrom app.services.webscraper.workflows import extraction_workflow\nasync def main():\n    wf = extraction_workflow.ExtractionWorkflow()\n    result = await wf.run({\"urls\": [\"https://example.com\"], \"session_id\": \"sess-wf\"})\n    print(result)\nasyncio.run(main())\nPY`
2) Validate: workflow_status == completed, artifacts stored (MinIO), chunks/embeddings created in Postgres, and log shows DAG steps executed.

### E2E Validation Goals
- Storage path works: MinIO accepts uploads; Postgres/pgvector stores chunks/embeddings; Redis cache reachable.
- Retrieval path works: RAG pipeline returns answers with citations for both uploaded docs and scraped content.
- Agentic paths work: Project Estimator LangGraph workflow produces BRD/cost/workflow outputs; Extraction workflow DAG runs to completion with stored artifacts.
- LLM path works: at least one model responds (vLLM/Ollama/external), and latency/token fields populate.
- Observability endpoints basic health respond (health, optional GraphQL). Clean up with `docker-compose down` when done.
