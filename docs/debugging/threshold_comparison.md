# THRESHOLD MISMATCH FOUND!

## UI Defaults (frontend/src/components/RAGSettings.tsx)
```
similarity_threshold: 0.70 (70%)
min_similarity_threshold: 0.55 (55%)
no_relevant_docs_threshold: 0.65 (65%)
```

## Backend Config (backend/app/core/config.py)
```
SIMILARITY_THRESHOLD: 0.75 (75%)
MIN_SIMILARITY_THRESHOLD: 0.60 (60%)
NO_RELEVANT_DOCS_THRESHOLD: 0.70 (70%)
```

## Question:
Is the backend USING the UI values or IGNORING them?

Let me check the backend API endpoint...
