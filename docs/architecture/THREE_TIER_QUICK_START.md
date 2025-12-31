# Three-Tier Reorganization - Quick Start Guide

**Date**: 2025-12-31
**Status**: Ready to Execute
**Estimated Time**: 2-3 hours for Phase 1

---

## 🎯 What You're About to Do

Reorganize the existing codebase into a 3-tier architecture:
- **Tier 1**: Core Platform (all existing code)
- **Tier 2**: Pluggable Modules (for future expansion)
- **Tier 3**: Customer Configurations (for future expansion)

**Impact**: File locations change, imports update, **zero** business logic changes

---

## ✅ Prerequisites

- [ ] Git working tree is clean (no uncommitted changes)
- [ ] Docker containers are running
- [ ] Backend tests pass (`pytest backend/tests/`)
- [ ] You're on branch: `feature/three-tier-architecture-reorganization`

**Check current status**:
```bash
git status                # Should show docs/architecture/ and scripts/migration/ changes
git branch --show-current # Should show: feature/three-tier-architecture-reorganization
docker-compose ps         # All services should be "Up"
```

---

## 🚀 Execution Steps

### Step 1: Commit Planning Docs (5 min)

```bash
# Commit the reorganization plan and scripts
git add docs/architecture/THREE_TIER_*.md
git add scripts/migration/

git commit -m "docs: Add three-tier reorganization plan, scripts, and branching strategy

- Add comprehensive reorganization plan (THREE_TIER_REORGANIZATION_PLAN.md)
- Add quick summary (THREE_TIER_REORGANIZATION_SUMMARY.md)
- Add branching strategy with rollback procedures
- Add migration scripts (01, 02 - structure and file moves)
- Create backup branch: backup/pre-three-tier-reorg-2025-12-31"

git log --oneline -1  # Verify commit
```

### Step 2: Create Directory Structure (10 min)

```bash
# Make script executable
chmod +x scripts/migration/01_create_tier_structure.sh

# Run structure creation
./scripts/migration/01_create_tier_structure.sh

# Expected output:
# ✅ Tier 1 structure created
# ✅ Tier 2 structure created
# ✅ Tier 3 structure created
# ✅ __init__.py files created
# ✅ README files created

# Verify structure
ls -R backend/app/tier-1/ | head -20
ls backend/app/tier-2/
ls backend/app/tier-3/

# Commit structure
git add backend/app/tier-1/ backend/app/tier-2/ backend/app/tier-3/
git commit -m "refactor: Create tier-1, tier-2, tier-3 directory structure

- Add tier-1/ with 15 logical subdirectories (infrastructure, llm, embeddings, etc.)
- Add tier-2/ for future pluggable modules
- Add tier-3/ for future customer configurations
- Add README.md in each tier explaining purpose and import patterns"

git log --oneline -2  # Verify commits
```

### Step 3: Move Files to Tier 1 (30-45 min)

```bash
# Make script executable
chmod +x scripts/migration/02_move_tier1_files.sh

# Run file migration
./scripts/migration/02_move_tier1_files.sh

# Expected output:
# ✅ Moved: core/config.py → tier-1/infrastructure/config.py
# ✅ Moved: services/llm_service.py → tier-1/llm/llm_service.py
# ... (51+ files moved)

# Review moved files
git status | grep "renamed:"

# Check for any remaining files in old locations
ls backend/app/services/*.py | wc -l  # Should be 0 or very few

# Commit file moves (this preserves git history)
git add -A
git commit -m "refactor: Move all services to tier-1 structure

Moved 51+ service files to appropriate tier-1 subdirectories:
- Core infrastructure → tier-1/infrastructure/
- LLM services → tier-1/llm/
- Embedding services → tier-1/embeddings/
- RAG services → tier-1/rag/
- Document processing → tier-1/document_processing/
- Agent framework → tier-1/agents/
- Platform services → tier-1/platform_services/
- Fine-tuning → tier-1/finetuning/
- Data extraction → tier-1/data_extraction/
- NLP processing → tier-1/nlp_processing/
- Evaluation → tier-1/evaluation/
- Export services → tier-1/export/
- CV processing → tier-1/cv_processing/

All moves done with 'git mv' to preserve file history."

git log --oneline -3  # Verify commits
```

### Step 4: Update Import Paths (60-90 min)

**Note**: This step requires creating the Python import updater script first.

```bash
# Create the import updater script
# (You'll need to create this based on the detailed plan)

# Run import updater
python scripts/migration/03_update_imports.py

# Expected output:
# ✅ Updated: backend/app/api/routes/models.py
# ✅ Updated: backend/app/api/routes/rag_pipeline_routes.py
# ... (100+ files updated)

# Check for syntax errors
python -m compileall backend/app/

# Expected output: No errors

# Commit import updates
git add -A
git commit -m "refactor: Update all import paths for tier-1 structure

Updated imports in:
- API routes (30+ files)
- Tasks (5 files)
- Tests (100+ files)
- Main entry points (2 files)

All imports now use tier-1.* paths:
- from app.services.llm_service → from app.tier_1.llm.llm_service
- from app.core.config → from app.tier_1.infrastructure.config
- from app.rag_pipeline → from app.tier_1.rag.pipeline"

git log --oneline -4  # Verify commits
```

### Step 5: Test Everything (30-60 min)

```bash
# Rebuild Docker image
docker-compose build backend --no-cache

# Expected: Build should succeed

# Start services
docker-compose up -d

# Wait for backend to be ready
sleep 10

# Test health endpoint
curl http://localhost:8000/health

# Expected: {"status":"healthy"}

# Run backend tests
docker-compose exec backend pytest backend/tests/ -v

# Expected: All tests pass (may take 10-20 min)

# If tests pass, commit success marker
git commit --allow-empty -m "test: All tests pass after three-tier reorganization ✅"
```

### Step 6: Final Verification (15 min)

```bash
# Check for any broken imports
find backend/app -name "*.py" -exec python -m py_compile {} \; 2>&1 | grep -i error

# Expected: No output (no errors)

# Check Docker build
docker-compose ps

# Expected: All services "Up" and healthy

# Test API endpoints
curl http://localhost:8000/api/docs  # Should return Swagger UI HTML
curl http://localhost:8000/graphql   # Should return GraphQL playground

# Check frontend builds
cd frontend
npm run build

# Expected: Build successful
cd ..

# Final commit
git commit --allow-empty -m "chore: Three-tier reorganization complete

Summary:
- 51+ services moved to tier-1 structure
- 200+ import paths updated
- All tests passing
- Docker build successful
- Zero business logic changes
- Git history preserved with 'git mv'

Ready to merge to main branch."

git log --oneline -6  # Review all commits
```

---

## 📊 Expected Results

After completion, you should have:

### Git Commits (6 total)
1. ✅ Planning docs and scripts
2. ✅ Directory structure creation
3. ✅ File moves (git history preserved)
4. ✅ Import path updates
5. ✅ Tests passing marker
6. ✅ Completion marker

### Directory Structure
```
backend/app/
├── tier-1/          # ← All existing code (organized)
├── tier-2/          # ← Empty (ready for modules)
├── tier-3/          # ← Empty (ready for customer configs)
├── api/             # ← Updated imports
├── models/          # ← Unchanged
├── schemas/         # ← Unchanged
└── ...
```

### Test Results
- ✅ All pytest tests pass
- ✅ Docker build succeeds
- ✅ API health check returns 200
- ✅ No import errors
- ✅ Frontend builds successfully

---

## 🔄 If Something Goes Wrong

### Minor Issue
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Fix issue
# ... make fixes ...

# Recommit
git add -A
git commit -m "refactor: Fix issue with ..."
```

### Major Issue - Restart
```bash
# Go back to backup
git checkout backup/pre-three-tier-reorg-2025-12-31

# Delete broken feature branch
git branch -D feature/three-tier-architecture-reorganization

# Start fresh
git checkout -b feature/three-tier-architecture-reorganization-v2

# Begin again from Step 1
```

### Nuclear Option - Complete Rollback
```bash
# Restore from backup
git checkout backup/pre-three-tier-reorg-2025-12-31

# Verify it works
docker-compose restart backend
curl http://localhost:8000/health

# This restores exact pre-reorganization state
```

---

## ✅ Success Criteria

All must be true before merging to main:

- [ ] All 6 commits created
- [ ] All tests pass (100%)
- [ ] Docker build succeeds
- [ ] API health check returns 200
- [ ] No Python import errors
- [ ] Frontend builds successfully
- [ ] No broken imports (`python -m compileall backend/app`)
- [ ] Git history preserved (use `git log --follow <file>` to verify)

---

## 🎉 Next Steps After Success

### Merge to Main
```bash
# Push feature branch
git push -u origin feature/three-tier-architecture-reorganization

# Switch to main
git checkout claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK

# Merge
git merge feature/three-tier-architecture-reorganization --no-ff

# Tag the reorganization
git tag -a v1.0.0-three-tier-reorg -m "Three-tier architecture reorganization complete"

# Push to remote
git push origin claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK --tags
```

### Update Documentation
- [ ] Update CLAUDE.md with new structure
- [ ] Update README.md with new import patterns
- [ ] Update architecture diagrams
- [ ] Create developer migration guide

### Celebrate 🎊
You've successfully reorganized the codebase with zero disruption!

---

## 📞 Help & Resources

**Documentation**:
- [Detailed Plan](./THREE_TIER_REORGANIZATION_PLAN.md) - Full migration guide (200+ lines)
- [Summary](./THREE_TIER_REORGANIZATION_SUMMARY.md) - Quick overview
- [Branching Strategy](./THREE_TIER_BRANCHING_STRATEGY.md) - Rollback procedures

**Scripts**:
- `scripts/migration/01_create_tier_structure.sh` - Create directories
- `scripts/migration/02_move_tier1_files.sh` - Move files
- `scripts/migration/03_update_imports.py` - Update imports (TO BE CREATED)

**Current Status**:
```bash
git branch --show-current  # Check active branch
git status                 # Check uncommitted changes
git log --oneline -5       # Check recent commits
```

---

**Ready to begin?** Start with Step 1!

**Estimated Total Time**: 2-3 hours

**Risk Level**: 🟡 Medium (well-mitigated with backup branch)

---

**Last Updated**: 2025-12-31
**Status**: 🟢 Ready to Execute

---

**End of Quick Start Guide**
