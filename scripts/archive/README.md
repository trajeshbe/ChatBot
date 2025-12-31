# Archived Scripts

**⚠️ DEPRECATED**: These scripts are kept for historical reference only.

This directory contains old, deprecated, or superseded scripts. They are no longer actively maintained and may not work with the current version of the system.

## Why These Scripts Are Archived

These scripts were created during development to fix specific issues or provide temporary functionality. They have been replaced by:
- Better implementations in the main codebase
- More robust scripts in the active directories
- Built-in features in the application

---

## Archived Scripts

### Database Fixes
- `fix-embedding-dimensions.sh` - Fixed embedding dimension mismatches (now handled in migration)
- `fix_embeddings.sh` - Fixed embedding generation issues (now handled in embedding_service.py)
- `check-db-direct.sh` - Direct database checks (use `../debugging/check-documents.sh` instead)

### Service Fixes
- `fix-llama-models.sh` - Fixed Ollama model issues (use `../setup/setup-ollama.sh` instead)
- `fix-permissions.sh` - Fixed file permissions (handled in docker-compose now)
- `quick-fix-backend.sh` - Quick backend fixes (use `../debugging/diagnose-backend.sh` instead)

### Setup Scripts
- `quick-setup-and-fix.sh` - Quick setup with fixes (use `../setup/` scripts instead)
- `verify-and-rebuild.sh` - Rebuild services (use `make rebuild` instead)
- `restart-and-test.sh` - Restart and test (use `make down && make up` instead)
- `quick-start.sh` - Old quick start (use `../setup/start-services.sh` instead)

### Test Scripts
- `test-cors.sh` - CORS testing (CORS is now properly configured)
- `diagnose_session_documents.py` - Session diagnostics (use `../debugging/debug_session_query.py` instead)

---

## If You Need to Use These Scripts

**Don't.** Instead:

1. Check if there's an updated version in `../setup/`, `../testing/`, `../debugging/`, or `../maintenance/`
2. Review the [documentation](../../docs/) for current procedures
3. Use the Makefile commands (`make help` for list)
4. If you need functionality from an archived script, consider:
   - Implementing it properly in the application code
   - Creating a new, improved script in the appropriate directory

---

## Deletion Policy

These scripts may be deleted in future releases. If you depend on any of these scripts, please:
1. Migrate to the new alternatives
2. Copy the script to your own location if absolutely necessary
3. Report why you need it so we can consider adding proper support

---

**Last Updated**: 2025-11-16
