# Debugging Scripts

Diagnostic and debugging scripts for troubleshooting system issues.

## Available Scripts

### Service Diagnostics

#### `diagnose-backend.sh`
Diagnose backend service health and issues.
```bash
./diagnose-backend.sh
```

#### `diagnose-documents.sh`
Diagnose document processing status and issues.
```bash
./diagnose-documents.sh
```

#### `diagnose-llama.sh`
Diagnose Ollama/LLM service status.
```bash
./diagnose-llama.sh
```

---

### Log Analysis

#### `check-backend-errors.sh`
Check backend logs for errors.
```bash
./check-backend-errors.sh
```

#### `check-backend-logs.sh`
View backend logs in real-time.
```bash
./check-backend-logs.sh
```

#### `check-upload-logs.sh`
View document upload logs.
```bash
./check-upload-logs.sh
```

---

### Status Checks

#### `check-documents.sh`
Check document database status and statistics.
```bash
./check-documents.sh
```

---

### RAG Debugging

#### `debug-rag.sh`
Debug RAG pipeline queries and responses.
```bash
./debug-rag.sh
```

---

### Frontend Debugging

#### `debug-frontend.sh`
Debug frontend service and connections.
```bash
./debug-frontend.sh
```

---

### Python Debugging Tools

#### `check_embeddings.py`
Validate document embeddings in database.
```bash
python check_embeddings.py
```

#### `debug_session_query.py`
Debug session-specific queries and memory.
```bash
python debug_session_query.py
```

---

## 🔍 Common Debugging Workflows

### Backend Issues
```bash
# 1. Check if backend is running
docker-compose ps backend

# 2. Check for errors
./check-backend-errors.sh

# 3. Run diagnostics
./diagnose-backend.sh

# 4. View full logs
./check-backend-logs.sh
```

### Document Processing Issues
```bash
# 1. Check document status
./check-documents.sh

# 2. Run document diagnostics
./diagnose-documents.sh

# 3. Validate embeddings
python check_embeddings.py
```

### RAG Query Issues
```bash
# 1. Debug RAG pipeline
./debug-rag.sh

# 2. Check embeddings
python check_embeddings.py

# 3. Debug session queries
python debug_session_query.py
```

### LLM Issues
```bash
# 1. Diagnose LLM service
./diagnose-llama.sh

# 2. Check Ollama status
curl http://localhost:11434/api/tags
```

---

## 🔗 Related Documentation

- [../../docs/debugging/](../../docs/debugging/) - Debugging guides
- [../../docs/debugging/DEBUG_QUICK_REFERENCE.md](../../docs/debugging/DEBUG_QUICK_REFERENCE.md)
- [../../docs/debugging/RAG_DEBUGGING_GUIDE.md](../../docs/debugging/RAG_DEBUGGING_GUIDE.md)

---

**Last Updated**: 2025-11-16
