# Master Documentation Index

**Last Updated**: 2025-12-31
**Purpose**: Central index for all project documentation

---

## 🎯 Start Here

| For... | Go To | Time |
|--------|-------|------|
| **New Developers** | [CLAUDE.md](../CLAUDE.md) → [CONTRIBUTING.md](../CONTRIBUTING.md) | 30 min |
| **Fine-Tuning Users** | [docs/features/finetuning/00_README_START_HERE.md](./features/finetuning/00_README_START_HERE.md) | 10 min |
| **System Status** | [STATUS.md](../STATUS.md) | 5 min |
| **Debugging Issues** | [docs/debugging/README.md](./debugging/README.md) | Varies |
| **Query Performance** | [docs/debugging/QWEN_VL_QUERY_TRACE_2025-12-31.md](./debugging/QWEN_VL_QUERY_TRACE_2025-12-31.md) | 15 min |

---

## 🆕 Latest Updates (2025-12-31)

### Documentation Organization
✅ **16 files moved from root to organized subdirectories**

**Debugging & Traces** (7 files → `docs/debugging/`):
- ARCHITECTURE_DIAGRAM_QUERY_TRACE.md - Complete vision query trace
- QWEN_VL_QUERY_TRACE_2025-12-31.md - Qwen VL performance analysis (3m 42s execution)
- VISION_MODEL_TIMEOUT_ISSUE.md - Vision model timeout investigation
- PROJECT_ID_LINKAGE_BUGS_ANALYSIS.md - Project linkage bug analysis
- MINIO_PERSISTENCE_INVESTIGATION_COMPLETE.md - MinIO persistence investigation
- TRAINER_IMAGE_MISMATCH_ROOT_CAUSE.md - Training image mismatch root cause
- project_upload_bug_analysis.md - Upload bug stale closure analysis

**Testing** (1 file → `docs/testing/`):
- FILE_UPLOAD_PROJECT_MAPPING_TEST_REPORT.md - Comprehensive upload mapping tests

**Bug Fixes** (5 files → `docs/fixes/`):
- PROJECT_UPLOAD_BUG_FIX_COMPLETE.md - React stale closure bug fix
- DATASET_PREPROCESSING_FIX_COMPLETE.md - Dataset preprocessing fixes
- TEXT_COLUMN_TRAINER_FIX_COMPLETE.md - Text column trainer fixes
- UI_FIXES_IMPLEMENTATION_COMPLETE.md - UI bug fixes
- FINETUNING_UI_ISSUES_AND_FIXES.md - Fine-tuning UI fixes

**Fine-Tuning Planning** (2 files → `docs/features/finetuning/`):
- FINETUNING_COMPREHENSIVE_IMPLEMENTATION_ROADMAP.md - Implementation roadmap
- FINETUNING_EVALUATION_AND_LOGGING_IMPLEMENTATION_PLAN.md - Evaluation & logging plan

**Meta** (1 file → `docs/meta/`):
- DOCUMENTATION_ORGANIZATION_COMPLETE_2025-12-23.md - Organization history

**Root Directory**: ✅ Now contains only 5 essential docs (README, CLAUDE, STATUS, CONTRIBUTING, NEXT_STEPS)

---

## 📁 Documentation Structure

```
docs/
├── features/                    # Feature-specific documentation
│   ├── finetuning/             # ⭐ Fine-tuning (79 docs)
│   │   ├── 00_README_START_HERE.md  # Quick start guide
│   │   ├── MAYANDI_MANZIL_SUCCESS_REPORT.md  # Success story
│   │   ├── FINETUNING_IMPROVEMENTS_COMPLETE.md  # Hyperparameter guide
│   │   ├── PERMANENT_FIXES_APPLIED.md  # All bug fixes
│   │   └── ... (70+ more docs)
│   ├── frontend/               # Frontend features
│   └── project_estimator/      # Project estimator features
│
├── architecture/               # System architecture
├── debugging/                  # Debugging guides
├── evaluation/                 # Evaluation & testing
├── analysis/                   # System analysis
├── compatibility/              # Compatibility reports
├── agent_implementations/      # Agent implementations
├── build_snapshots/           # Build snapshots
│
└── archive/                    # Archived documentation
    ├── root_docs/             # Old root-level docs (4 docs)
    └── tmp_docs/              # Temporary docs (113 docs)
```

---

## 📚 Documentation by Category

### 1. Fine-Tuning (⭐ 79 Documents)
**Location**: `docs/features/finetuning/`
**Start**: [00_README_START_HERE.md](./features/finetuning/00_README_START_HERE.md)

**Top Documents**:
- [MAYANDI_MANZIL_SUCCESS_REPORT.md](./features/finetuning/MAYANDI_MANZIL_SUCCESS_REPORT.md) - 100% accuracy success story
- [FINETUNING_IMPROVEMENTS_COMPLETE.md](./features/finetuning/FINETUNING_IMPROVEMENTS_COMPLETE.md) - Hyperparameter guide
- [PERMANENT_FIXES_APPLIED.md](./features/finetuning/PERMANENT_FIXES_APPLIED.md) - All permanent fixes
- [END_TO_END_FINETUNING_ARCHITECTURE.md](./features/finetuning/END_TO_END_FINETUNING_ARCHITECTURE.md) - Complete architecture

**Stats**:
- ✅ Production-ready pipeline
- ✅ All bugs permanently fixed
- ✅ 7 presets available in UI
- ✅ Proven: 0% → 100% accuracy in real use case

### 2. Core Documentation (Root Level)
**Location**: Repository root

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | Project overview & quick start |
| [CLAUDE.md](../CLAUDE.md) | ⭐ AI assistant development guide (850 lines) |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contribution guidelines |
| [STATUS.md](../STATUS.md) | Current project status |
| [NEXT_STEPS.md](../NEXT_STEPS.md) | Roadmap & next steps |

### 3. Architecture Documentation
**Location**: `docs/architecture/`

**Key Documents**:
- System design patterns
- Database schemas
- Service architecture
- Data flow diagrams

### 4. Debugging & Troubleshooting
**Location**: `docs/debugging/`

**Key Documents**:
- Debug guides
- Troubleshooting procedures
- Log analysis
- Root cause analysis

### 5. Evaluation & Testing
**Location**: `docs/evaluation/`

**Key Documents**:
- Evaluation guides
- Test plans
- Metrics & benchmarks
- Quality assurance

### 6. Feature Documentation
**Location**: `docs/features/`

**Subdirectories**:
- `finetuning/` - Fine-tuning features (79 docs)
- `frontend/` - Frontend features
- `project_estimator/` - Project estimator

### 7. Archive (Historical)
**Location**: `docs/archive/`

**Subdirectories**:
- `root_docs/` - Old root-level docs (4 docs)
- `tmp_docs/` - Temporary docs (113 docs)

**Note**: Archived docs preserved for historical reference. Use current docs for active development.

---

## 🚀 Common Scenarios

### Scenario 1: "I want to fine-tune a model"
1. Read: [docs/features/finetuning/00_README_START_HERE.md](./features/finetuning/00_README_START_HERE.md)
2. Follow: [docs/features/finetuning/END_TO_END_FINETUNING_DEMO.md](./features/finetuning/END_TO_END_FINETUNING_DEMO.md)
3. Select preset: "🎯 Small Dataset Intensive" in UI
4. Monitor: Training progress in Fine-Tuning Hub
5. Deploy: Click "Merge & Deploy to Ollama"

### Scenario 2: "My model is hallucinating"
1. Read: [docs/features/finetuning/MAYANDI_MANZIL_SUCCESS_REPORT.md](./features/finetuning/MAYANDI_MANZIL_SUCCESS_REPORT.md)
2. Check: Training steps ≥ dataset_size × 10
3. Increase: Epochs or use "Small Dataset Intensive" preset
4. Retrain: With optimized hyperparameters

### Scenario 3: "Something is broken"
1. Check: [docs/debugging/](./debugging/)
2. Review: [docs/features/finetuning/PERMANENT_FIXES_APPLIED.md](./features/finetuning/PERMANENT_FIXES_APPLIED.md)
3. Search: docs/ for specific error messages

### Scenario 4: "I'm new to the codebase"
1. Read: [CLAUDE.md](../CLAUDE.md) (main development guide)
2. Review: [CONTRIBUTING.md](../CONTRIBUTING.md)
3. Check: [STATUS.md](../STATUS.md)
4. Explore: docs/ subdirectories based on needs

---

## 📊 Documentation Statistics

| Category | Count | Status |
|----------|-------|--------|
| Root Docs (Core) | 5 | ✅ Current |
| Fine-Tuning Docs | 81 (+2) | ✅ Current |
| Debugging Docs | 15 (+7) | ✅ Current |
| Testing Docs | 5 (+1) | ✅ Current |
| Fix Reports | 10 (+5) | ✅ Current |
| Meta Docs | 5 (+1) | ✅ Current |
| Architecture Docs | ~20 | ✅ Current |
| Other Active Docs | ~50 | ✅ Current |
| **Total Active Docs** | **~191** | ✅ Organized |
| Archived (root) | 4 | 📦 Historical |
| Archived (tmp) | 113 | 📦 Historical |
| **Total Archive** | **117** | 📦 Preserved |
| **GRAND TOTAL** | **308** | ✅ Fully Organized |

**Last Cleanup**: 2025-12-31
**Docs Moved (Today)**: 16 files organized
**Docs Moved (Total)**: 133 files organized
**Root Cleaned**: ✅ Only 5 essential docs remain

---

## 🔍 Finding Documentation

### By Topic
- **Fine-Tuning**: `docs/features/finetuning/`
- **Architecture**: `docs/architecture/`
- **Debugging**: `docs/debugging/`
- **Testing**: `docs/evaluation/`

### By File Name
```bash
# Search all docs
find docs/ -name "*keyword*.md"

# Search fine-tuning docs
ls docs/features/finetuning/ | grep keyword

# Search archived docs
find docs/archive/ -name "*keyword*.md"
```

### By Content
```bash
# Search content in current docs
grep -r "search term" docs/ --include="*.md" --exclude-dir=archive

# Search fine-tuning docs only
grep -r "search term" docs/features/finetuning/ --include="*.md"
```

---

## 📝 Documentation Guidelines

### For New Documents
1. **Categorize**: Determine correct subdirectory
2. **Name Clearly**: Use descriptive, consistent naming
3. **Add to Index**: Update relevant README files
4. **Cross-Reference**: Link to related docs

### For Updates
1. **Update Date**: Change "Last Updated" timestamp
2. **Update Status**: Mark as current/deprecated
3. **Update Index**: If moving or renaming
4. **Preserve History**: Move old versions to archive/

### For Archiving
1. **Archive Location**: `docs/archive/tmp_docs/` for temporary, `docs/archive/root_docs/` for root-level
2. **Update Index**: Remove from current, add to archive index
3. **Preserve Content**: Don't delete, move to archive
4. **Add Context**: Note why archived and replacement location

---

## 🎯 Priority Documentation

### Must-Read (Everyone)
1. [CLAUDE.md](../CLAUDE.md) - Development guide
2. [README.md](../README.md) - Project overview
3. [STATUS.md](../STATUS.md) - Current state

### Must-Read (Fine-Tuning Users)
1. [docs/features/finetuning/00_README_START_HERE.md](./features/finetuning/00_README_START_HERE.md)
2. [docs/features/finetuning/MAYANDI_MANZIL_SUCCESS_REPORT.md](./features/finetuning/MAYANDI_MANZIL_SUCCESS_REPORT.md)
3. [docs/features/finetuning/FINETUNING_IMPROVEMENTS_COMPLETE.md](./features/finetuning/FINETUNING_IMPROVEMENTS_COMPLETE.md)

### Must-Read (Developers)
1. [CLAUDE.md](../CLAUDE.md) - AI assistant rules
2. [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
3. [docs/architecture/](./architecture/) - System architecture

---

## 📞 Need Help?

1. **Check This Index**: Find relevant category
2. **Read Specific Docs**: Navigate to subdirectory
3. **Search Content**: Use grep/find commands
4. **Check Archive**: If looking for historical info

---

## 🎉 Recent Updates

### 2025-12-31 Update
**✅ 16 additional files organized from root directory**

**New Debugging Documentation**:
- Complete query tracing with performance analysis
- Vision model optimization guides (43x performance improvement documented)
- Upload bug fixes with root cause analysis
- MinIO persistence investigations

**New Test & Fix Reports**:
- Comprehensive upload project mapping tests
- React stale closure bug fix
- Fine-tuning UI fixes and improvements

**Impact**:
- Root directory: 21 files → 5 files (only essentials)
- Total active docs: 84 → ~191
- Grand total: 201 → 308 documents

### 2025-12-23 Update
**✅ Major documentation reorganization (117 files)**

**Fine-Tuning Success**:
- Mayandi Manzil: 100% accuracy (vs 100% hallucination)
- Small Dataset Intensive preset added
- All bugs permanently fixed
- Complete documentation created

**Documentation Organization**:
- Moved 11 fine-tuning docs from root → `docs/features/finetuning/`
- Moved 4 old training reports → `docs/archive/root_docs/`
- Moved 113 tmp docs → `docs/archive/tmp_docs/`
- Created `00_README_START_HERE.md` quick-start guide

**Stats**:
- **Before**: 117 docs scattered across root, /tmp, docs/
- **After**: 84 active docs organized + 117 archived
- **Improvement**: Clear structure, easy navigation

---

**Maintained By**: Development Team
**Last Major Cleanup**: 2025-12-31
**Total Documents**: 308 (~191 active + 117 archived)
**Status**: ✅ Fully Organized
