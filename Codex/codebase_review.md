# Codebase Security & Architecture Findings

## Key Risks
- Default admin bootstrap with fixed creds and weak hashing in `backend/app/main.py:157-187` (admin/admin123, unsalted SHA256) enables immediate takeover.
- Insecure defaults in `backend/app/core/config.py:11-52` (`DEBUG=True`, hard-coded `SECRET_KEY`, default DB/MinIO/Redis creds, 8-day tokens) make production unsafe if not overridden.
- Unprotected direct LLM endpoint `/api/v1/llm/test` in `backend/app/main.py:245-293` bypasses RAG and lacks auth/rate limits—cost, data-exfiltration, and prompt-injection vector.
- Unauthenticated uploads in `backend/app/main.py:296-430` push files to MinIO/DB without type/size limits or malware scanning—storage abuse and retrieval poisoning risk.
- Critical init failures are swallowed as warnings (e.g., `backend/app/main.py:92-155`; document/session association in `backend/app/services/document_service.py:70-115`), allowing partial startup without health signaling.
- Secrets embedded in code and no TLS for MinIO/DB/Redis (`backend/app/core/config.py:47-67`), risking credential leakage and MITM.
- No enforced authN/Z or rate limiting across REST/GraphQL; anonymous flow (`backend/app/main.py:69-83`) plus permissive CORS exposes APIs publicly.
- Password storage uses plain SHA256 (`backend/app/main.py:170-183`), not a KDF (bcrypt/argon2).

## Gaps / Questions
- Target auth model (OIDC/JWT/API keys) and required per-route roles?
- Planned admission/WAF policies to block default creds and enforce TLS to stateful services?
- Tenant isolation and quotas for uploads, scraping, and LLM usage?
- PII/secret screening before embedding or logging?

## Recommended Actions
1. Remove or gate default admin creation; switch to bcrypt/argon2 hashing.
2. Enforce env/secret-driven config; refuse startup in non-dev when placeholders/DEBUG/TLS-off are present.
3. Add authN/Z middleware and rate limiting; lock down `/api/v1/llm/test`, upload, and scraping routes to authorized roles only.
4. Harden ingestion: file type/size allowlist, AV scan, content sanitization, per-tenant buckets/prefixes, and WAF checks.
5. Fail fast on critical init errors; surface readiness probes/alerts when dependencies (DB, MinIO, LLM) are unavailable.
6. Externalize secrets (CSI/External Secrets), require TLS for MinIO/Postgres/Redis; add OPA/Gatekeeper rules (non-root, image signing, resource limits).
7. Add security tests (auth required, upload validation, RAG vs direct LLM path) and CI policies to block default creds/config drift.
