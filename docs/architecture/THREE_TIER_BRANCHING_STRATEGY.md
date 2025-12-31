# Three-Tier Reorganization - Branching Strategy

**Date**: 2025-12-31
**Purpose**: Safe, rollback-friendly branch strategy for three-tier reorganization

---

## 🌳 Branch Structure

```
claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK (main)
├── backup/pre-three-tier-reorg-2025-12-31          ← Safety backup
└── feature/three-tier-architecture-reorganization   ← Active work (YOU ARE HERE)
```

---

## 📋 Branch Descriptions

### 1. Main Branch
**Name**: `claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK`
**Status**: Protected - Working application
**Purpose**: Production-ready code, always stable

### 2. Backup Branch
**Name**: `backup/pre-three-tier-reorg-2025-12-31`
**Status**: Frozen snapshot (as of 2025-12-31)
**Purpose**: **Rollback point** - exact state before reorganization

**Usage**: If reorganization fails, switch back:
```bash
git checkout backup/pre-three-tier-reorg-2025-12-31
git checkout -b recovery/restore-pre-reorg
# Review and push
```

### 3. Feature Branch (ACTIVE)
**Name**: `feature/three-tier-architecture-reorganization`
**Status**: ✅ Active development
**Purpose**: Three-tier reorganization work

**Current Status**:
- Created: 2025-12-31
- Base: `claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK`
- Work in progress: Reorganization scripts and plans created

---

## 🚀 Workflow

### Phase 1: Setup (COMPLETE ✅)
```bash
# 1. Create backup branch
git checkout -b backup/pre-three-tier-reorg-2025-12-31

# 2. Return to main
git checkout claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK

# 3. Create feature branch
git checkout -b feature/three-tier-architecture-reorganization
```

### Phase 2: Development (IN PROGRESS 🔄)
```bash
# Currently on: feature/three-tier-architecture-reorganization

# 1. Commit planning docs (already created)
git add docs/architecture/THREE_TIER_*.md
git add scripts/migration/
git commit -m "docs: Add three-tier reorganization plan and scripts"

# 2. Run reorganization scripts
chmod +x scripts/migration/*.sh
./scripts/migration/01_create_tier_structure.sh
# ... (continue with other scripts)

# 3. Commit changes incrementally
git add backend/app/tier-1/
git commit -m "refactor: Create tier-1 directory structure"

git add <moved files>
git commit -m "refactor: Move services to tier-1 structure"

# 4. Update imports
python scripts/migration/03_update_imports.py
git add -A
git commit -m "refactor: Update import paths for tier-1"
```

### Phase 3: Testing (TO DO)
```bash
# 1. Run tests
docker-compose build backend
docker-compose up -d
pytest backend/tests/

# 2. If tests pass
git commit -m "test: Verify all tests pass after reorganization"

# 3. If tests fail
git stash          # Save current work
git reset --hard HEAD~1  # Undo last commit
# Fix issues and retry
```

### Phase 4: Merge (TO DO)
```bash
# Only after all tests pass!

# 1. Push feature branch
git push -u origin feature/three-tier-architecture-reorganization

# 2. Create pull request (or merge directly)
git checkout claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK
git merge feature/three-tier-architecture-reorganization

# 3. Push to main
git push origin claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK
```

---

## 🔄 Rollback Scenarios

### Scenario 1: Minor Issue During Development
**Problem**: Made a mistake in feature branch
**Solution**: Undo last commit
```bash
git checkout feature/three-tier-architecture-reorganization
git reset --soft HEAD~1  # Keep changes, undo commit
# OR
git reset --hard HEAD~1  # Discard changes and commit
```

### Scenario 2: Major Issue - Need Fresh Start
**Problem**: Feature branch is broken, need to restart
**Solution**: Delete feature branch, create new one from backup
```bash
git checkout backup/pre-three-tier-reorg-2025-12-31
git branch -D feature/three-tier-architecture-reorganization
git checkout -b feature/three-tier-architecture-reorganization-v2
```

### Scenario 3: Critical - Rollback After Merge
**Problem**: Merged to main, but production is broken
**Solution**: Revert merge commit
```bash
git checkout claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK
git log  # Find merge commit hash
git revert -m 1 <merge-commit-hash>
git push origin claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK
```

### Scenario 4: Nuclear Option - Complete Restore
**Problem**: Everything broken, need exact pre-reorg state
**Solution**: Force restore from backup
```bash
git checkout backup/pre-three-tier-reorg-2025-12-31
git checkout -b recovery/restore-working-state

# Verify everything works
docker-compose down -v
docker-compose up -d
# Run tests

# If confirmed working, replace main
git checkout claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK
git reset --hard backup/pre-three-tier-reorg-2025-12-31
git push --force-with-lease origin claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK
```

---

## ✅ Safety Checklist

Before each major step:

### Before Running Scripts
- [ ] Currently on `feature/three-tier-architecture-reorganization`
- [ ] Backup branch exists: `backup/pre-three-tier-reorg-2025-12-31`
- [ ] All current work committed
- [ ] Docker containers running (to test rollback)

### Before Committing
- [ ] Files moved correctly (`git status`)
- [ ] No broken imports (`python -m compileall backend/app`)
- [ ] Tests pass (at least unit tests)

### Before Merging to Main
- [ ] **ALL tests pass** (100% success rate)
- [ ] Docker build succeeds
- [ ] API health check passes
- [ ] Code review complete (if team process)
- [ ] Rollback plan documented

---

## 📊 Branch Status Commands

```bash
# Show all branches
git branch -a

# Show current branch
git branch --show-current

# Show backup branch exists
git branch | grep backup

# Show uncommitted changes
git status --short

# Show commit history
git log --oneline -10

# Compare branches
git diff backup/pre-three-tier-reorg-2025-12-31..feature/three-tier-architecture-reorganization --stat
```

---

## 🎯 Current Status

**Active Branch**: `feature/three-tier-architecture-reorganization`

**Completed**:
- ✅ Backup branch created (`backup/pre-three-tier-reorg-2025-12-31`)
- ✅ Feature branch created (`feature/three-tier-architecture-reorganization`)
- ✅ Planning documents created:
  - `docs/architecture/THREE_TIER_REORGANIZATION_PLAN.md`
  - `docs/architecture/THREE_TIER_REORGANIZATION_SUMMARY.md`
  - `docs/architecture/THREE_TIER_BRANCHING_STRATEGY.md`
- ✅ Migration scripts created:
  - `scripts/migration/01_create_tier_structure.sh`
  - `scripts/migration/02_move_tier1_files.sh`

**Next Steps**:
1. Commit planning docs and scripts
2. Run `01_create_tier_structure.sh`
3. Run `02_move_tier1_files.sh`
4. Create and run `03_update_imports.py`
5. Test thoroughly
6. Merge if tests pass

---

## 📞 Emergency Contacts

If you need to rollback:

```bash
# Quick rollback to backup
git checkout backup/pre-three-tier-reorg-2025-12-31

# Verify it works
docker-compose restart backend
curl http://localhost:8000/health
```

**Remember**: The backup branch is your safety net. It contains the exact working state from before reorganization began.

---

**Last Updated**: 2025-12-31
**Maintained By**: Development Team
**Status**: 🟢 Active - Safe to proceed

---

**End of Branching Strategy**
