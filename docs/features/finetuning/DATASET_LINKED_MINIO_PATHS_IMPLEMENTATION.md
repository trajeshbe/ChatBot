# Dataset-Linked MinIO Paths - Implementation Plan

**Date**: 2025-12-18
**Status**: 📝 PROPOSED - Awaiting Approval
**Priority**: P1 - High Value Enhancement

---

## 🎯 Goal

Associate fine-tuned model checkpoints with their training datasets using the organizational hierarchy MinIO path builder.

---

## 💡 Current vs Proposed Structure

### Current Structure (Disconnected):

```
❌ DATASETS:
finetuning/
└── datasets/
    └── story8/
        └── {dataset_id}/
            └── story8.jsonl

❌ CHECKPOINTS (NO CONNECTION TO DATASET):
finetuning/
└── AI-ML/
    └── Research/
        └── qwen-testing/
            └── finetuning/
                └── checkpoints/
                    └── qwen_test_job/
                        └── final/
                            ├── adapter_model/
                            └── merged_model/
```

**Problems**:
- ❌ No connection between model and dataset
- ❌ Hard to find which dataset trained which model
- ❌ No organizational context
- ❌ Difficult to manage in multi-tenant scenarios

---

### Proposed Structure (Dataset-Linked):

```
✅ UNIFIED HIERARCHY:
documents/
└── technology/                          # Department
    └── backend-development/             # Team
        └── global/                      # Project
            └── admin/                   # User
                └── finetuning/
                    └── datasets/
                        └── story8/      # Dataset Name
                            ├── {dataset_id}/
                            │   └── story8.jsonl
                            │
                            └── checkpoints/     # ← NEW: Checkpoints under dataset!
                                └── qwen_test_job/
                                    └── {job_id}/
                                        └── final/
                                            ├── adapter_model/
                                            └── merged_model/
```

**Benefits**:
- ✅ **Direct Dataset Association** - Model checkpoints live under their dataset
- ✅ **Organizational Context** - dept/team/project/user hierarchy
- ✅ **RBAC Integration** - Access control follows org structure
- ✅ **Traceability** - Easy to trace: dataset → job → checkpoints → deployed model
- ✅ **Multi-Tenancy** - Multiple teams can have same dataset names without conflicts
- ✅ **Scalability** - Clear structure for thousands of models/datasets

---

## 📊 Path Examples

### Example 1: Story Dataset

**Dataset**:
```
documents/technology/backend-development/global/admin/finetuning/datasets/story8/3b8234e1-b542-44ad-9c09-f45059888511/story8.jsonl
```

**Checkpoints** (under same dataset):
```
documents/technology/backend-development/global/admin/finetuning/datasets/story8/checkpoints/qwen-story-job/c4ad0963-b194-4f85-b816-3fd0fdaaff9d/final/adapter_model/
documents/technology/backend-development/global/admin/finetuning/datasets/story8/checkpoints/qwen-story-job/c4ad0963-b194-4f85-b816-3fd0fdaaff9d/final/merged_model/
```

### Example 2: Multi-User Scenario

**User 1 (Admin)**:
```
documents/technology/backend-development/global/admin/finetuning/datasets/story8/checkpoints/...
```

**User 2 (John)**:
```
documents/technology/backend-development/global/john/finetuning/datasets/story8/checkpoints/...
```

**User 3 (Sarah in Different Team)**:
```
documents/technology/data-science/ml-platform/sarah/finetuning/datasets/story8/checkpoints/...
```

---

## 🛠️ Implementation Changes

### 1. Add New MinIOPathBuilder Method

**File**: `backend/app/services/minio_path_builder.py`

**Add Method**:
```python
@staticmethod
def build_finetuning_checkpoint_with_dataset(
    department_name: str,
    team_name: str,
    project_name: str,
    username: str,
    dataset_name: str,           # ← NEW: Link to dataset
    job_name: str,
    job_id: str,
    checkpoint_stage: str,        # 'final', 'epoch-1', 'epoch-2', etc.
    model_type: str,              # 'adapter_model', 'merged_model'
    filename: str = ""
) -> str:
    """
    Build hierarchical MinIO path for fine-tuning checkpoints under dataset.

    Args:
        department_name: Department (e.g., 'Technology')
        team_name: Team (e.g., 'Backend Development')
        project_name: Project (e.g., 'global', 'ChatBot RAG')
        username: User's username (e.g., 'admin')
        dataset_name: Dataset name (e.g., 'story8', 'cloudsync-qa')
        job_name: Job name (e.g., 'qwen-story-job')
        job_id: Unique job ID (UUID)
        checkpoint_stage: Stage ('final', 'epoch-1', 'epoch-2', 'best')
        model_type: Type ('adapter_model', 'merged_model')
        filename: Specific file name (empty for directory path)

    Returns:
        Full MinIO path string

    Examples:
        >>> build_finetuning_checkpoint_with_dataset(
        ...     department_name='Technology',
        ...     team_name='Backend Development',
        ...     project_name='global',
        ...     username='admin',
        ...     dataset_name='story8',
        ...     job_name='qwen-story-job',
        ...     job_id='c4ad0963-b194-4f85-b816-3fd0fdaaff9d',
        ...     checkpoint_stage='final',
        ...     model_type='merged_model',
        ...     filename='model.safetensors'
        ... )
        'documents/technology/backend-development/global/admin/finetuning/datasets/story8/checkpoints/qwen-story-job/c4ad0963-b194-4f85-b816-3fd0fdaaff9d/final/merged_model/model.safetensors'
    """
    # Sanitize components
    sanitized_dept = MinIOPathBuilder.sanitize(department_name)
    sanitized_team = MinIOPathBuilder.sanitize(team_name)
    sanitized_project = MinIOPathBuilder.sanitize(project_name)
    sanitized_username = MinIOPathBuilder.sanitize(username)
    sanitized_dataset = MinIOPathBuilder.sanitize(dataset_name)
    sanitized_job = MinIOPathBuilder.sanitize(job_name)

    # Build path
    path = (
        f"documents/{sanitized_dept}/{sanitized_team}/{sanitized_project}/"
        f"{sanitized_username}/finetuning/datasets/{sanitized_dataset}/"
        f"checkpoints/{sanitized_job}/{job_id}/{checkpoint_stage}/{model_type}"
    )

    if filename:
        path += f"/{filename}"

    logger.debug(f"Built dataset-linked checkpoint path: {path}")
    return path
```

---

### 2. Update Database Schema

**Add Dataset Association to Jobs**:

```sql
-- Migration: Add dataset_id foreign key to finetuning_jobs

ALTER TABLE finetuning_jobs
ADD COLUMN dataset_id UUID REFERENCES finetuning_datasets(id) ON DELETE SET NULL;

-- Add index for performance
CREATE INDEX idx_finetuning_jobs_dataset_id ON finetuning_jobs(dataset_id);

-- Update existing jobs (optional - set to NULL if dataset unknown)
-- UPDATE finetuning_jobs SET dataset_id = NULL WHERE dataset_id IS NULL;
```

---

### 3. Update FineTuningJob Model

**File**: `backend/app/models/finetuning_models.py`

**Add Field**:
```python
class FineTuningJob(Base):
    __tablename__ = "finetuning_jobs"

    # ... existing fields ...

    dataset_id = Column(UUID(as_uuid=True), ForeignKey("finetuning_datasets.id", ondelete="SET NULL"))

    # Add relationship
    dataset = relationship("FineTuningDataset", back_populates="jobs")
```

**Update Dataset Model**:
```python
class FineTuningDataset(Base):
    __tablename__ = "finetuning_datasets"

    # ... existing fields ...

    # Add relationship
    jobs = relationship("FineTuningJob", back_populates="dataset")
```

---

### 4. Update Training Job Creation

**File**: `backend/app/api/routes/finetuning_routes.py`

**Modify** `submit_finetuning_job` endpoint:

```python
@router.post("/jobs")
async def submit_finetuning_job(
    request: FineTuningJobRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # ... existing code ...

    # Get user's organizational context
    user = await db.execute(select(User).where(User.id == current_user.id))
    user = user.scalar_one()

    # Get project/team/dept
    project = await db.execute(select(Project).where(Project.id == user.project_id))
    project = project.scalar_one()

    team = await db.execute(select(Team).where(Team.id == project.team_id))
    team = team.scalar_one()

    dept = await db.execute(select(Department).where(Department.id == team.department_id))
    dept = dept.scalar_one()

    # Get dataset
    dataset = await db.execute(
        select(FineTuningDataset).where(FineTuningDataset.id == request.dataset_id)
    )
    dataset = dataset.scalar_one_or_none()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Build checkpoint path using dataset linkage
    from app.services.minio_path_builder import MinIOPathBuilder

    checkpoint_base_path = MinIOPathBuilder.build_finetuning_checkpoint_with_dataset(
        department_name=dept.name,
        team_name=team.name,
        project_name=project.name,
        username=user.username,
        dataset_name=dataset.name,
        job_name=request.job_name,
        job_id=str(job.id),
        checkpoint_stage="final",
        model_type="merged_model",
        filename=""  # Directory path
    )

    # Create job with dataset association
    job = FineTuningJob(
        # ... existing fields ...
        dataset_id=dataset.id,  # ← NEW: Link to dataset
        minio_checkpoint_path=checkpoint_base_path,
        # ... rest of fields ...
    )

    db.add(job)
    await db.commit()
```

---

### 5. Update Training Worker

**File**: `backend/app/services/finetuning/finetuning_service.py`

**Modify Path Construction**:

```python
async def run_training_job(self, job_id: str):
    # ... get job from database ...

    # Get dataset for path construction
    dataset = await self.db.execute(
        select(FineTuningDataset).where(FineTuningDataset.id == job.dataset_id)
    )
    dataset = dataset.scalar_one()

    # Build output paths using dataset linkage
    adapter_path = MinIOPathBuilder.build_finetuning_checkpoint_with_dataset(
        department_name=job.department,
        team_name=job.team,
        project_name=job.project,
        username=job.username,
        dataset_name=dataset.name,    # ← Use dataset name
        job_name=job.name,
        job_id=str(job.id),
        checkpoint_stage="final",
        model_type="adapter_model",
        filename=""
    )

    merged_path = MinIOPathBuilder.build_finetuning_checkpoint_with_dataset(
        department_name=job.department,
        team_name=job.team,
        project_name=job.project,
        username=job.username,
        dataset_name=dataset.name,    # ← Use dataset name
        job_name=job.name,
        job_id=str(job.id),
        checkpoint_stage="final",
        model_type="merged_model",
        filename=""
    )

    # Upload to MinIO using these paths
    # ...
```

---

### 6. Update API Response

**File**: `backend/app/api/routes/finetuning_routes.py`

**Modify** `list_models_public`:

```python
@router.get("/models-public")
async def list_models_public(db: AsyncSession = Depends(get_db)):
    # ... existing query ...

    models_response = []
    for m in models_list:
        minio_path = None
        dataset_name = None

        if m.job_id:
            # Get job with dataset
            job_query = (
                select(FineTuningJob, FineTuningDataset)
                .join(FineTuningDataset, FineTuningJob.dataset_id == FineTuningDataset.id)
                .where(FineTuningJob.id == m.job_id)
            )
            result = await db.execute(job_query)
            row = result.first()

            if row:
                job, dataset = row
                dataset_name = dataset.name

                # Path now includes dataset
                minio_path = job.minio_checkpoint_path  # Already includes dataset!

        models_response.append({
            "id": str(m.id),
            "name": m.name,
            # ... other fields ...
            "minio_path": minio_path,
            "dataset_name": dataset_name,  # ← NEW: Show dataset name in UI
        })

    return {"models": models_response}
```

---

### 7. Update Frontend UI

**File**: `frontend/src/components/finetuning/DeploymentManager.tsx`

**Add Dataset Name Display**:

```typescript
interface DeployedModel {
  // ... existing fields ...
  minio_path?: string;
  dataset_name?: string;  // ← NEW
}

// In UI component:
{/* Dataset Info */}
{model.dataset_name && (
  <div className="mb-4 p-3 bg-blue-50 rounded-lg">
    <p className="text-xs text-gray-500 mb-1">Training Dataset</p>
    <p className="text-sm font-medium text-gray-900">{model.dataset_name}</p>
  </div>
)}

{/* MinIO Artifacts Link */}
{model.minio_path && (
  <div className="pt-3 border-t border-gray-200">
    <div className="flex items-center justify-between">
      <span className="text-sm font-medium text-gray-700">
        📦 Model Artifacts ({model.dataset_name || 'unknown dataset'})
      </span>
      <a
        href={`http://localhost:9001/browser/documents/${model.minio_path}`}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm text-blue-600 hover:text-blue-800 underline"
      >
        View in MinIO
      </a>
    </div>
  </div>
)}
```

---

## 🎨 UI Mockup

### Deployment Manager Card:

```
┌────────────────────────────────────────────────┐
│ qwen_story_model  v1.0  ✓ Deployed            │
│ Base Model: Qwen/Qwen2.5-1.5B                 │
│ Ollama Model: qwen-story-v1                    │
│                                                │
│ ──────────────────────────────────────────────│
│                                                │
│ Training Dataset                               │
│ story8                          ← NEW          │
│                                                │
│ ──────────────────────────────────────────────│
│                                                │
│ 📦 Model Artifacts (story8)     ← NEW         │
│ [📄 View in MinIO]                            │
│                                                │
│ ──────────────────────────────────────────────│
│                                                │
│ [ Undeploy Model ]                             │
└────────────────────────────────────────────────┘
```

---

## 📊 Benefits Summary

### Traceability

**Before**:
```
❓ Model: qwen-test-v1
   ❓ Trained on which dataset?
   ❓ Where are checkpoints?
   ❓ Who trained it?
```

**After**:
```
✅ Model: qwen-story-v1
   ✅ Dataset: story8
   ✅ Path: documents/technology/.../admin/finetuning/datasets/story8/checkpoints/...
   ✅ User: admin
   ✅ Team: Backend Development
   ✅ Department: Technology
```

### RBAC Integration

```
Permissions:
- Admin can access: documents/technology/backend-development/global/admin/finetuning/**
- John can access: documents/technology/backend-development/global/john/finetuning/**
- Teams isolated automatically
```

### Multi-Tenancy

```
Technology Dept → Backend Team → User Admin → Dataset story8 → Model qwen-v1
Technology Dept → Data Science Team → User Sarah → Dataset story8 → Model gpt-v1
Data Operations Dept → Analytics Team → User Bob → Dataset story8 → Model llama-v1
```

**All have same dataset name "story8" but isolated by org hierarchy!**

---

## 🔄 Migration Strategy

### For Existing Data:

**Option 1: Leave As-Is (Recommended)**
- Existing models keep old paths
- New models use new path structure
- No data migration needed

**Option 2: Migrate Existing Models**
```python
# Migration script
async def migrate_checkpoint_paths():
    # Get all jobs
    jobs = await db.execute(select(FineTuningJob).where(FineTuningJob.dataset_id.isnot(None)))

    for job in jobs.scalars():
        dataset = await db.execute(select(FineTuningDataset).where(FineTuningDataset.id == job.dataset_id))
        dataset = dataset.scalar_one()

        # Build new path
        new_path = MinIOPathBuilder.build_finetuning_checkpoint_with_dataset(...)

        # Copy files in MinIO from old path to new path
        minio_client.copy_object(old_path, new_path)

        # Update database
        job.minio_checkpoint_path = new_path
        await db.commit()
```

---

## 🧪 Testing Plan

### 1. Unit Tests

```python
def test_dataset_linked_checkpoint_path():
    path = MinIOPathBuilder.build_finetuning_checkpoint_with_dataset(
        department_name="Technology",
        team_name="Backend Development",
        project_name="global",
        username="admin",
        dataset_name="story8",
        job_name="qwen-story-job",
        job_id="123e4567-e89b-12d3-a456-426614174000",
        checkpoint_stage="final",
        model_type="merged_model",
        filename="model.safetensors"
    )

    expected = (
        "documents/technology/backend-development/global/admin/"
        "finetuning/datasets/story8/checkpoints/qwen-story-job/"
        "123e4567-e89b-12d3-a456-426614174000/final/merged_model/model.safetensors"
    )

    assert path == expected
```

### 2. Integration Tests

```python
async def test_training_job_with_dataset_linked_paths():
    # Create dataset
    dataset = await create_test_dataset(name="story8")

    # Create training job
    job = await submit_finetuning_job(dataset_id=dataset.id, ...)

    # Verify checkpoint path includes dataset
    assert "datasets/story8/checkpoints" in job.minio_checkpoint_path
```

### 3. E2E Test

1. Upload dataset "story8"
2. Create training job using "story8"
3. Verify checkpoint path: `documents/.../datasets/story8/checkpoints/...`
4. Deploy model
5. Check UI shows dataset name
6. Click MinIO link - verify opens correct path

---

## 📋 Implementation Checklist

### Phase 1: Database & Models
- [ ] Add `dataset_id` column to `finetuning_jobs` table
- [ ] Add foreign key constraint and index
- [ ] Update SQLAlchemy models with relationships
- [ ] Create migration script

### Phase 2: Path Builder
- [ ] Add `build_finetuning_checkpoint_with_dataset()` method
- [ ] Write unit tests for new method
- [ ] Test with various inputs

### Phase 3: Backend Integration
- [ ] Update job submission to use dataset-linked paths
- [ ] Update training worker to use new paths
- [ ] Update MinIO upload logic
- [ ] Update API responses to include dataset name

### Phase 4: Frontend
- [ ] Update TypeScript interface with `dataset_name`
- [ ] Add dataset name display in UI
- [ ] Update MinIO link to use new path format
- [ ] Test UI with new fields

### Phase 5: Testing
- [ ] Unit tests for path builder
- [ ] Integration tests for job creation
- [ ] E2E tests for complete workflow
- [ ] Manual testing with real datasets

### Phase 6: Documentation
- [ ] Update API documentation
- [ ] Update architecture docs
- [ ] Add migration guide
- [ ] Update README with new path structure

---

## 🚀 Rollout Plan

### Week 1: Database & Models
- Create migration
- Update models
- Deploy to dev environment

### Week 2: Backend Implementation
- Implement path builder method
- Update job creation logic
- Update training worker

### Week 3: Frontend & Testing
- Update UI components
- Write tests
- QA in staging

### Week 4: Production Deployment
- Deploy to production
- Monitor for issues
- Document final setup

---

## 💡 Alternative Approaches

### Option 1: Flat with Dataset Prefix (Simpler)
```
finetuning/datasets/story8/checkpoints/qwen-job/final/merged_model/
```
- ❌ No organizational hierarchy
- ❌ No RBAC integration
- ✅ Simpler implementation

### Option 2: Current with Dataset Link (Metadata Only)
```
Keep current paths, add dataset_id to database only
```
- ❌ No path-based traceability
- ❌ Harder to navigate MinIO manually
- ✅ No path migration needed

### Option 3: Proposed (Dataset Under Org Hierarchy) ⭐
```
documents/technology/backend-dev/global/admin/finetuning/datasets/story8/checkpoints/...
```
- ✅ Full organizational context
- ✅ RBAC integration
- ✅ Traceability
- ✅ Scalable
- ⚠️ Longer paths

---

## 🎯 Recommendation

**Proceed with Option 3 (Proposed Approach)**

**Rationale**:
1. ✅ **Best long-term architecture** - Aligns with existing organizational path builder
2. ✅ **RBAC-ready** - Security follows org structure automatically
3. ✅ **Scalable** - Works for 1 user or 10,000 users across departments
4. ✅ **Traceability** - Clear dataset → checkpoint → model lineage
5. ✅ **Future-proof** - Supports advanced features (team sharing, project transfers)

**Trade-offs Accepted**:
- ⚠️ Longer paths (acceptable - MinIO has 1024-char limit, we're well under)
- ⚠️ Requires dataset association (good - enforces data governance)

---

**Date**: 2025-12-18
**Author**: Claude
**Status**: 📝 PROPOSED - Ready for implementation approval
**Estimated Effort**: 2-3 weeks
**Risk Level**: Low (backward compatible, opt-in for new models)
