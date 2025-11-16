# Debugging Documentation

Debugging tools, troubleshooting guides, and diagnostic references.

## 📖 Available Guides

### [DEBUG_QUICK_REFERENCE.md](./DEBUG_QUICK_REFERENCE.md)
Quick reference for common debugging tasks.
- Quick diagnostic commands
- Common issues and solutions
- Useful scripts reference

### [DEBUG_TOOLS_README.md](./DEBUG_TOOLS_README.md)
Comprehensive guide to debugging tools available in the repository.
- Script descriptions
- Usage examples
- Tool categories

### [RAG_DEBUGGING_GUIDE.md](./RAG_DEBUGGING_GUIDE.md)
In-depth guide for debugging the RAG system.
- RAG pipeline debugging
- Vector search troubleshooting
- Embedding issues
- Document processing problems

### [RAG_DEBUG_QUICK_REFERENCE.md](./RAG_DEBUG_QUICK_REFERENCE.md)
Quick reference for RAG-specific debugging.
- Common RAG issues
- Quick diagnostic checks
- Performance troubleshooting

---

## 🛠️ Debugging Scripts

All debugging scripts are located in `../../scripts/debugging/`:

- `diagnose-backend.sh` - Backend health diagnostics
- `diagnose-documents.sh` - Document processing status
- `diagnose-llama.sh` - LLM service diagnostics
- `debug-rag.sh` - RAG pipeline debugging
- `debug-frontend.sh` - Frontend debugging
- `check-backend-errors.sh` - Backend error logs
- `check-backend-logs.sh` - Backend logs viewer
- `check-documents.sh` - Document database status
- `check-upload-logs.sh` - Upload logs viewer
- `debug_session_query.py` - Session query debugging
- `check_embeddings.py` - Embedding validation

See [../../scripts/debugging/README.md](../../scripts/debugging/README.md) for detailed script documentation.

---

## 🚨 Common Issues

### Backend Won't Start
```bash
../../scripts/debugging/diagnose-backend.sh
docker-compose logs backend
```

### Documents Not Processing
```bash
../../scripts/debugging/diagnose-documents.sh
../../scripts/debugging/check-documents.sh
```

### RAG Queries Failing
```bash
../../scripts/debugging/debug-rag.sh
python ../../scripts/debugging/check_embeddings.py
```

### Database Connection Issues
```bash
docker-compose exec postgres pg_isready
docker-compose logs postgres
```

---

## 🔗 Related Documentation

- **Setup**: [../setup/](../setup/) - Initial setup guides
- **Architecture**: [../architecture/](../architecture/) - System design
- **Guides**: [../guides/](../guides/) - User guides

---

**Last Updated**: 2025-11-16
