# Dynamic GPU Configuration & MinIO Artifacts - Implementation Guide

**Date**: 2025-12-17
**Status**: 🔧 **READY TO IMPLEMENT**
**Priority**: P0 - Critical Fixes

---

## Executive Summary

Two critical improvements needed:

1. **Dynamic GPU Configuration** - Make GPU settings configurable in UI based on actual hardware
2. **MinIO Artifact Storage** - Fix broken checkpoint storage (currently NULL)

---

## Problem 1: GPU Configuration is Hidden/Hardcoded

### Current Issues
- GPU settings buried in `hyperparameters` JSON field
- No UI controls for GPU selection
- Users on different hardware can't easily adjust settings
- Need manual database updates to change GPU requirements

### Current Model1 Settings (Fixed Manually)
```sql
SELECT hyperparameters FROM finetuning_jobs WHERE name='model1';

Result:
{
  "gpu_count": 1,
  "min_gpu_memory_gb": 6,    -- Fixed manually from default 12
  "max_memory_gb": 7,          -- Fixed manually
  "num_epochs": 3,
  "batch_size": 4,
  "learning_rate": 2e-4
}
```

### Solution: Dynamic GPU Configuration UI

---

## Implementation: Dynamic GPU UI

### Step 1: Create GPU Detection API Endpoint

**File**: `backend/app/api/routes/finetuning_routes.py`

**Add this endpoint**:
```python
@router.get("/gpu/capabilities")
async def get_gpu_capabilities():
    """
    Detect available GPUs and their capabilities
    Used by UI to show realistic GPU configuration options
    """
    from app.services.finetuning.gpu_pool_manager import GPUPoolManager

    gpu_pool = GPUPoolManager()
    gpu_info_list = await gpu_pool.get_all_gpus()

    if not gpu_info_list:
        return {
            "available": False,
            "message": "No GPUs detected. CPU-only mode.",
            "recommended_config": {
                "gpu_count": 0,
                "min_gpu_memory_gb": 0,
                "max_memory_gb": 4  # CPU RAM limit
            }
        }

    # Get the GPU with most memory (for multi-GPU systems)
    max_memory_gpu = max(gpu_info_list, key=lambda g: g.memory_total)

    # Calculate safe memory limits (leave 20% buffer)
    total_memory_gb = max_memory_gpu.memory_total / 1024
    safe_memory_gb = total_memory_gb * 0.8

    return {
        "available": True,
        "gpu_count": len(gpu_info_list),
        "gpus": [
            {
                "index": gpu.index,
                "name": gpu.name,
                "memory_total_gb": round(gpu.memory_total / 1024, 2),
                "memory_free_gb": round(gpu.memory_free / 1024, 2),
                "compute_capability": gpu.compute_capability
            }
            for gpu in gpu_info_list
        ],
        "recommended_config": {
            "gpu_count": 1,  # Default to single GPU
            "min_gpu_memory_gb": round(safe_memory_gb * 0.5, 1),  # 50% of safe memory
            "max_memory_gb": round(safe_memory_gb, 1)
        },
        "presets": {
            "small_model": {
                "name": "Small Model (< 7B params)",
                "gpu_count": 1,
                "min_gpu_memory_gb": min(6, round(safe_memory_gb * 0.5, 1)),
                "max_memory_gb": min(8, round(safe_memory_gb * 0.6, 1)),
                "batch_size": 4,
                "num_epochs": 3
            },
            "medium_model": {
                "name": "Medium Model (7B-13B params)",
                "gpu_count": 1,
                "min_gpu_memory_gb": min(12, round(safe_memory_gb * 0.7, 1)),
                "max_memory_gb": min(16, round(safe_memory_gb * 0.8, 1)),
                "batch_size": 2,
                "num_epochs": 3
            },
            "large_model": {
                "name": "Large Model (13B+ params)",
                "gpu_count": min(2, len(gpu_info_list)),
                "min_gpu_memory_gb": min(20, round(safe_memory_gb * 0.8, 1)),
                "max_memory_gb": min(24, round(safe_memory_gb, 1)),
                "batch_size": 1,
                "num_epochs": 2
            }
        }
    }


# Example response on your laptop with RTX 5060 (8GB):
{
  "available": true,
  "gpu_count": 1,
  "gpus": [
    {
      "index": 0,
      "name": "NVIDIA GeForce RTX 5060 Laptop GPU",
      "memory_total_gb": 8.0,
      "memory_free_gb": 7.2,
      "compute_capability": "8.9"
    }
  ],
  "recommended_config": {
    "gpu_count": 1,
    "min_gpu_memory_gb": 3.2,
    "max_memory_gb": 6.4
  },
  "presets": {
    "small_model": {
      "name": "Small Model (< 7B params)",
      "gpu_count": 1,
      "min_gpu_memory_gb": 6.0,  # Adjusted to your hardware
      "max_memory_gb": 7.0,
      "batch_size": 4,
      "num_epochs": 3
    },
    "medium_model": {
      "name": "Medium Model (7B-13B params)",
      "gpu_count": 1,
      "min_gpu_memory_gb": 6.4,  # Maxed out for your GPU
      "max_memory_gb": 6.4,
      "batch_size": 2,
      "num_epochs": 3
    }
  }
}
```

### Step 2: Create GPU Configuration UI Component

**File**: `frontend/src/components/finetuning/GPUConfigSelector.tsx` (NEW)

```typescript
import React, { useState, useEffect } from 'react'

interface GPUCapabilities {
  available: boolean
  gpu_count: number
  gpus: Array<{
    index: number
    name: string
    memory_total_gb: number
    memory_free_gb: number
  }>
  recommended_config: {
    gpu_count: number
    min_gpu_memory_gb: number
    max_memory_gb: number
  }
  presets: {
    [key: string]: {
      name: string
      gpu_count: number
      min_gpu_memory_gb: number
      max_memory_gb: number
      batch_size: number
      num_epochs: number
    }
  }
}

interface GPUConfigSelectorProps {
  value: {
    gpu_count: number
    min_gpu_memory_gb: number
    max_memory_gb: number
  }
  onChange: (config: any) => void
}

export const GPUConfigSelector: React.FC<GPUConfigSelectorProps> = ({
  value,
  onChange
}) => {
  const [capabilities, setCapabilities] = useState<GPUCapabilities | null>(null)
  const [selectedPreset, setSelectedPreset] = useState<string>('custom')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch GPU capabilities on mount
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/finetuning/gpu/capabilities`)
      .then(res => res.json())
      .then(data => {
        setCapabilities(data)

        // Auto-select recommended config
        if (data.available && !value.gpu_count) {
          onChange(data.recommended_config)
        }

        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load GPU capabilities:', err)
        setLoading(false)
      })
  }, [])

  const handlePresetSelect = (presetKey: string) => {
    if (presetKey === 'custom') {
      setSelectedPreset('custom')
      return
    }

    const preset = capabilities?.presets[presetKey]
    if (preset) {
      setSelectedPreset(presetKey)
      onChange({
        gpu_count: preset.gpu_count,
        min_gpu_memory_gb: preset.min_gpu_memory_gb,
        max_memory_gb: preset.max_memory_gb,
        batch_size: preset.batch_size,
        num_epochs: preset.num_epochs
      })
    }
  }

  const handleManualChange = (field: string, value: number) => {
    setSelectedPreset('custom')
    onChange({
      ...value,
      [field]: value
    })
  }

  if (loading) {
    return <div className="p-4">Loading GPU configuration...</div>
  }

  if (!capabilities?.available) {
    return (
      <div className="bg-yellow-100 border border-yellow-400 rounded p-4">
        <p className="font-semibold">⚠️ No GPU Detected</p>
        <p className="text-sm">Fine-tuning will run in CPU-only mode (very slow)</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* GPU Hardware Info */}
      <div className="bg-blue-50 border border-blue-200 rounded p-4">
        <h3 className="font-semibold mb-2">🖥️ Detected Hardware</h3>
        {capabilities.gpus.map(gpu => (
          <div key={gpu.index} className="text-sm">
            <p><strong>{gpu.name}</strong></p>
            <p>Memory: {gpu.memory_total_gb}GB total, {gpu.memory_free_gb}GB free</p>
          </div>
        ))}
      </div>

      {/* Preset Selection */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Configuration Preset
        </label>
        <select
          value={selectedPreset}
          onChange={(e) => handlePresetSelect(e.target.value)}
          className="w-full border rounded px-3 py-2"
        >
          <option value="custom">Custom Configuration</option>
          {Object.entries(capabilities.presets).map(([key, preset]) => (
            <option key={key} value={key}>
              {preset.name} (GPU: {preset.min_gpu_memory_gb}GB)
            </option>
          ))}
        </select>
      </div>

      {/* Manual Configuration */}
      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium mb-1">
            GPU Count
          </label>
          <input
            type="number"
            min={1}
            max={capabilities.gpu_count}
            value={value.gpu_count}
            onChange={(e) => handleManualChange('gpu_count', parseInt(e.target.value))}
            className="w-full border rounded px-3 py-2"
          />
          <p className="text-xs text-gray-500">
            Available: {capabilities.gpu_count} GPU(s)
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Minimum GPU Memory (GB)
          </label>
          <input
            type="number"
            step={0.5}
            min={1}
            max={capabilities.gpus[0].memory_total_gb}
            value={value.min_gpu_memory_gb}
            onChange={(e) => handleManualChange('min_gpu_memory_gb', parseFloat(e.target.value))}
            className="w-full border rounded px-3 py-2"
          />
          <p className="text-xs text-gray-500">
            Required free memory per GPU
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Maximum Memory Usage (GB)
          </label>
          <input
            type="number"
            step={0.5}
            min={value.min_gpu_memory_gb}
            max={capabilities.gpus[0].memory_total_gb}
            value={value.max_memory_gb}
            onChange={(e) => handleManualChange('max_memory_gb', parseFloat(e.target.value))}
            className="w-full border rounded px-3 py-2"
          />
          <p className="text-xs text-gray-500">
            Memory limit per GPU (leave buffer for system)
          </p>
        </div>
      </div>

      {/* Validation Warning */}
      {value.min_gpu_memory_gb > capabilities.gpus[0].memory_free_gb && (
        <div className="bg-red-100 border border-red-400 rounded p-3">
          <p className="text-sm">
            ⚠️ <strong>Warning:</strong> Required memory ({value.min_gpu_memory_gb}GB) exceeds
            currently available memory ({capabilities.gpus[0].memory_free_gb}GB).
            Training may fail or wait in queue.
          </p>
        </div>
      )}
    </div>
  )
}
```

### Step 3: Integrate into Job Creation Form

**File**: `frontend/src/components/finetuning/JobManager.tsx`

**Find the Create Job section and add**:

```typescript
import { GPUConfigSelector } from './GPUConfigSelector'

const CreateJobForm = () => {
  const [formData, setFormData] = useState({
    name: '',
    base_model: '',
    dataset_id: '',
    finetuning_method: 'PEFT',
    training_objective: 'instruction_following',
    hyperparameters: {
      num_epochs: 3,
      batch_size: 4,
      learning_rate: 2e-4,
      // GPU config will be set by GPUConfigSelector
      gpu_count: 0,
      min_gpu_memory_gb: 0,
      max_memory_gb: 0
    }
  })

  return (
    <form>
      {/* ... existing fields (name, base_model, etc.) ... */}

      {/* GPU Configuration Section */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">GPU Configuration</h3>
        <GPUConfigSelector
          value={{
            gpu_count: formData.hyperparameters.gpu_count,
            min_gpu_memory_gb: formData.hyperparameters.min_gpu_memory_gb,
            max_memory_gb: formData.hyperparameters.max_memory_gb
          }}
          onChange={(gpuConfig) => {
            setFormData({
              ...formData,
              hyperparameters: {
                ...formData.hyperparameters,
                ...gpuConfig
              }
            })
          }}
        />
      </div>

      {/* ... rest of form ... */}
    </form>
  )
}
```

---

## Problem 2: MinIO Artifacts Not Stored

### Current Issue
```sql
SELECT name, status, minio_checkpoint_path
FROM finetuning_jobs
WHERE name='model1';

Result:
name: model1
status: completed
minio_checkpoint_path: NULL  ❌ Should contain checkpoint path!
```

### Root Cause
The `execute_training` method in `FineTuningSandboxManager` doesn't upload checkpoints to MinIO - it only returns training metrics.

### Solution: Upload Checkpoints After Training

---

## Implementation: MinIO Artifact Storage

### Step 1: Install MinIO Client in Celery Worker

**File**: `backend/requirements.txt`

Already present:
```python
minio==7.2.3  ✅
```

### Step 2: Create MinIO Buckets Setup Script

**File**: `backend/scripts/setup_minio_finetuning_buckets.py` (NEW)

```python
"""
Setup MinIO buckets for fine-tuning artifacts
Run once during initial setup or after MinIO reset
"""
import os
from minio import Minio
from minio.error import S3Error

def setup_finetuning_buckets():
    # MinIO connection
    client = Minio(
        endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
        secure=False
    )

    buckets = [
        "finetuning-checkpoints",  # Model weights/adapters
        "training-logs",            # Training logs
        "tensorboard-logs",         # TensorBoard events
        "evaluation-results"        # Evaluation metrics
    ]

    for bucket_name in buckets:
        try:
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
                print(f"✅ Created bucket: {bucket_name}")
            else:
                print(f"ℹ️  Bucket already exists: {bucket_name}")
        except S3Error as e:
            print(f"❌ Error creating bucket {bucket_name}: {e}")

if __name__ == "__main__":
    setup_finetuning_buckets()
```

**Run this once**:
```bash
docker-compose exec backend python scripts/setup_minio_finetuning_buckets.py
```

### Step 3: Update Training Task to Upload Checkpoints

**File**: `backend/app/tasks/finetuning_tasks.py`

**Add import**:
```python
import glob
import os
from minio import Minio
from minio.error import S3Error
```

**Modify lines 250-270 (after training completes)**:
```python
# After training completes
result = asyncio.run(sandbox_manager.execute_training(...))

# ========================================
# NEW: Upload checkpoint to MinIO
# ========================================
try:
    # Initialize MinIO client
    minio_client = Minio(
        endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
        secure=False
    )

    # Define checkpoint directory
    checkpoint_dir = f"/workspace/finetuning/{job_id}/checkpoints"

    # Find checkpoint files (PEFT adapter files)
    checkpoint_files = []
    for ext in ["*.safetensors", "*.bin", "adapter_config.json", "adapter_model.bin"]:
        checkpoint_files.extend(glob.glob(f"{checkpoint_dir}/**/{ext}", recursive=True))

    if checkpoint_files:
        logger.info(f"Found {len(checkpoint_files)} checkpoint files")

        # Upload each file to MinIO
        uploaded_files = []
        bucket_name = "finetuning-checkpoints"

        for local_path in checkpoint_files:
            # Create object path: jobs/{job_id}/checkpoints/{filename}
            relative_path = os.path.relpath(local_path, checkpoint_dir)
            object_name = f"jobs/{job_id}/checkpoints/{relative_path}"

            # Upload file
            minio_client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=local_path
            )

            uploaded_files.append(object_name)
            logger.info(f"Uploaded: {object_name}")

        # Store primary checkpoint path
        main_checkpoint = uploaded_files[0]  # First uploaded file
        minio_path = f"minio://{bucket_name}/{main_checkpoint}"

        # Update job with checkpoint path
        job.minio_checkpoint_path = minio_path
        logger.info(f"✅ Checkpoint saved to MinIO: {minio_path}")

    else:
        logger.warning(f"No checkpoint files found in {checkpoint_dir}")
        job.minio_checkpoint_path = None

except S3Error as e:
    logger.error(f"MinIO upload failed: {e}")
    job.error_message = f"Checkpoint upload failed: {str(e)}"
    # Don't fail the job, just mark checkpoint as unavailable
    job.minio_checkpoint_path = None

# ========================================
# END: MinIO upload
# ========================================

# Continue with existing code
job.status = "completed"
job.training_end_time = datetime.utcnow()
job.progress = 100.0
# ... rest of existing code
```

### Step 4: Add Checkpoint Download API

**File**: `backend/app/api/routes/finetuning_routes.py`

```python
@router.get("/jobs/{job_id}/download-checkpoint")
async def download_checkpoint(
    job_id: str,
    user: User = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    Download model checkpoint from MinIO
    Returns presigned URL for direct download
    """
    # Get job
    result = await db.execute(
        select(FineTuningJob).where(FineTuningJob.id == UUID(job_id))
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.minio_checkpoint_path:
        raise HTTPException(
            status_code=404,
            detail="No checkpoint available for this job"
        )

    # Parse MinIO path: minio://bucket/path/to/file
    path_parts = job.minio_checkpoint_path.replace("minio://", "").split("/", 1)
    bucket_name = path_parts[0]
    object_name = path_parts[1]

    # Generate presigned URL (valid for 1 hour)
    from minio import Minio
    minio_client = Minio(
        endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
        secure=False
    )

    presigned_url = minio_client.presigned_get_object(
        bucket_name=bucket_name,
        object_name=object_name,
        expires=timedelta(hours=1)
    )

    return {
        "download_url": presigned_url,
        "expires_in_seconds": 3600,
        "checkpoint_path": job.minio_checkpoint_path
    }
```

### Step 5: Frontend - Show Download Button

**File**: `frontend/src/components/finetuning/JobManager.tsx`

**Update Job Details section**:
```typescript
const JobDetails: React.FC<{ job: any }> = ({ job }) => {
  const downloadCheckpoint = async () => {
    const response = await fetch(
      `${API_BASE}/api/v1/finetuning/jobs/${job.id}/download-checkpoint`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      }
    )

    const data = await response.json()

    if (response.ok) {
      // Open download URL in new window
      window.open(data.download_url, '_blank')
    } else {
      alert(`Download failed: ${data.detail}`)
    }
  }

  return (
    <div>
      <h3>Job: {job.name}</h3>
      <p>Status: {job.status}</p>
      <p>Progress: {job.progress}%</p>

      {/* Show download button if checkpoint available */}
      {job.status === 'completed' && job.minio_checkpoint_path && (
        <button
          onClick={downloadCheckpoint}
          className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          📦 Download Checkpoint
        </button>
      )}

      {job.status === 'completed' && !job.minio_checkpoint_path && (
        <p className="text-yellow-600 mt-2">
          ⚠️ No checkpoint available (training may have failed)
        </p>
      )}
    </div>
  )
}
```

---

## Testing Both Features

### Test 1: GPU Configuration UI
```bash
# 1. Open fine-tuning UI
open http://localhost:3001/admin/finetuning

# 2. Click "Create New Job"

# 3. GPU Configuration section should show:
#    - Detected GPU: NVIDIA GeForce RTX 5060 Laptop GPU (8GB)
#    - Preset options based on your hardware
#    - Manual sliders with validation

# 4. Select "Small Model" preset
#    - Should auto-fill: gpu_count=1, min_gpu_memory_gb=6, max_memory_gb=7

# 5. Try increasing min_memory to 10GB
#    - Should show warning: "Required memory exceeds available"

# 6. Submit job and verify hyperparameters saved correctly
```

### Test 2: MinIO Checkpoint Upload
```bash
# 1. Submit a training job with proper GPU config

# 2. Wait for completion

# 3. Check database
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT name, status, minio_checkpoint_path FROM finetuning_jobs WHERE name='test-model';"

# Expected result:
# name: test-model
# status: completed
# minio_checkpoint_path: minio://finetuning-checkpoints/jobs/{job-id}/checkpoints/adapter_model.safetensors

# 4. Verify files in MinIO
docker-compose exec backend python << 'EOF'
from minio import Minio
client = Minio(endpoint="minio:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)
objects = client.list_objects("finetuning-checkpoints", prefix="jobs/", recursive=True)
for obj in objects:
    print(f"✅ {obj.object_name} ({obj.size} bytes)")
EOF

# 5. Test download button in UI
#    - Click "Download Checkpoint"
#    - Should download adapter_model.safetensors file
```

---

## Implementation Checklist

### Phase 1: Dynamic GPU Configuration (2-3 hours)
- [ ] Add `/gpu/capabilities` API endpoint
- [ ] Create `GPUConfigSelector.tsx` component
- [ ] Integrate into Job Creation form
- [ ] Test on your laptop (RTX 5060 8GB)
- [ ] Test preset selection
- [ ] Test validation warnings

### Phase 2: MinIO Artifact Storage (3-4 hours)
- [ ] Create MinIO buckets setup script
- [ ] Run bucket setup: `python scripts/setup_minio_finetuning_buckets.py`
- [ ] Update `finetuning_tasks.py` to upload checkpoints
- [ ] Add `/download-checkpoint` API endpoint
- [ ] Add download button to Job Manager UI
- [ ] Test end-to-end: train → upload → download

### Verification
- [ ] New jobs show GPU configuration UI
- [ ] GPU settings adapt to hardware
- [ ] Completed jobs have non-NULL `minio_checkpoint_path`
- [ ] Checkpoint files visible in MinIO console (http://localhost:9001)
- [ ] Download button works and retrieves checkpoint

---

## Success Criteria

### GPU Configuration
- ✅ UI automatically detects available GPUs
- ✅ Shows realistic presets based on hardware
- ✅ Validation warns if requirements exceed capacity
- ✅ Works on different machines (8GB laptop, 24GB workstation, etc.)

### MinIO Artifacts
- ✅ Checkpoints uploaded to MinIO after training
- ✅ `minio_checkpoint_path` populated in database
- ✅ Files accessible via MinIO console
- ✅ Download button retrieves checkpoint
- ✅ Presigned URLs expire after 1 hour (security)

---

## Next Steps

**Option A: Start with GPU UI** (User-facing, immediate value)
- Users can create jobs with appropriate GPU settings
- No more manual database edits

**Option B: Start with MinIO** (Foundation for deployment)
- Fix artifact storage first
- Enables deployment/evaluation features later

**Recommendation**: Do both in parallel (independent changes):
1. One developer: GPU UI (~3 hours)
2. Another developer: MinIO artifacts (~4 hours)

Total time: **~4 hours if parallel, ~7 hours if sequential**

---

**Status**: 🚀 Ready to implement
**Estimated Time**: 4-7 hours
**Dependencies**: MinIO, pynvml, existing GPU detection system

---

**End of Document**
