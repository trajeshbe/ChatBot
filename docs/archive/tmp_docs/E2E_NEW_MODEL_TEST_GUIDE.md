# End-to-End New Model Training Test Guide

**Date**: 2025-12-23
**Purpose**: Complete workflow test from training → one-click deployment → inference
**Estimated Time**: 30-40 minutes total

---

## Overview

This guide walks through creating a new fine-tuned model and testing the complete one-click deployment feature.

### Workflow Steps

1. **Create Training Job** (via UI or API)
2. **Monitor Training** (5-10 minutes)
3. **Test One-Click Deployment** (via Governance UI)
4. **Verify in Chat UI**
5. **Test Inference**

---

## Prerequisites

### Check Services Status

```bash
docker-compose ps | grep -E "(backend|ollama|postgres|frontend|celery|finetuning-trainer)"
```

All should show "Up".

### Check GPU Availability

```bash
nvidia-smi
```

Should show available GPU memory.

### Check Existing Dataset

```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT id, name, num_samples, is_valid 
   FROM finetuning_datasets 
   WHERE is_valid = true 
   ORDER BY uploaded_at DESC 
   LIMIT 5;"
```

We'll use: **qwen_test_dataset** (10 samples, valid)

---

## Method 1: UI-Based Testing (Recommended)

### Step 1: Navigate to Fine-Tuning Hub

1. Open browser: `http://localhost:3001`
2. Click **"Fine-Tuning Hub"** tab
3. Click **"Create New Job"** or **"Start Training"**

### Step 2: Configure Training Job

**Training Configuration**:
- **Job Name**: `test-deployment-e2e-001`
- **Dataset**: Select "qwen_test_dataset"
- **Base Model**: `Qwen/Qwen2.5-1.5B-Instruct`
- **Training Method**: LoRA (default)
- **Epochs**: 3
- **Learning Rate**: 2e-4
- **Batch Size**: 4
- **Max Seq Length**: 512

**Advanced (Optional)**:
- **LoRA Rank**: 16
- **LoRA Alpha**: 32
- **LoRA Dropout**: 0.1

### Step 3: Submit Training Job

1. Click **"Submit Training Job"**
2. Note the **Job ID** displayed
3. Training will start automatically

### Step 4: Monitor Training Progress

**In UI**:
- Training status updates in real-time
- Progress bar shows current epoch/step
- ETA displayed

**Expected Output**:
```
Status: Running
Epoch 1/3 - Step 2/3 - Loss: 0.45
ETA: 7 minutes
```

**Via Logs** (optional):
```bash
docker-compose logs -f finetuning-trainer | grep -E "(Epoch|Loss|Training|✅)"
```

### Step 5: Wait for Training Completion

**Duration**: 5-10 minutes for 10 samples, 3 epochs

**Success Indicators**:
- Status changes to "Completed"
- Green checkmark appears
- "Deploy Model" button becomes enabled

### Step 6: Navigate to Governance & Audit

1. Click **"Governance & Audit"** tab
2. Find your model in "Pending Approvals" section
3. Model name: `test-deployment-e2e-001_model`

### Step 7: One-Click Deployment

1. Find the **"Quick Deployment"** section (gradient purple/indigo background)
2. Click **"Quick Deploy"** button
3. Watch real-time progress:
   - ✅ Step 1: Approve Model
   - ⏳ Step 2: Merge LoRA Adapter (5-15 min)
   - ⏳ Step 3: Deploy to Ollama

**Expected Duration**: 10-20 minutes total

### Step 8: Monitor Deployment

**In UI**:
- Progress bar updates
- Step-by-step status messages
- "Deployment Complete!" when finished

**Via Logs** (optional):
```bash
docker-compose logs -f --tail=100 backend | grep -E "(Deploy|merge|GGUF|Ollama)"
```

Expected log sequence:
```
📦 Detected LoRA adapter - merge required
🔄 Merging adapter into base model...
✅ Merge complete: 2.9 GB
🔄 Converting to GGUF f16...
✅ GGUF conversion successful: 3.1 GB
🚀 Deploying to Ollama...
✅ Deployment successful!
```

### Step 9: Verify in Chat UI

1. Go to **"Chat"** tab
2. Click **refresh icon** next to model dropdown
3. Look for your model: `test-deployment-e2e-001_model-v1`
4. Select the model from dropdown

### Step 10: Test Inference

**In Chat UI**:
1. Type a test question related to your training data
2. Send message
3. Verify model responds

**Via CLI** (alternative):
```bash
docker-compose exec ollama ollama list | grep test-deployment
docker-compose exec ollama ollama run test-deployment-e2e-001_model-v1 "Test question here"
```

---

## Method 2: API-Based Testing

### Step 1: Create Training Job via API

```bash
# Get dataset ID
DATASET_ID=$(docker-compose exec postgres psql -U postgres -d ragchatbot -t -c \
  "SELECT id FROM finetuning_datasets WHERE name = 'qwen_test_dataset' LIMIT 1;" | tr -d ' ')

echo "Dataset ID: $DATASET_ID"

# Create training job
curl -X POST "http://localhost:8000/api/v1/finetuning/jobs" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"test-api-e2e-001\",
    \"base_model\": \"Qwen/Qwen2.5-1.5B-Instruct\",
    \"dataset_id\": \"$DATASET_ID\",
    \"hyperparameters\": {
      \"num_train_epochs\": 3,
      \"learning_rate\": 0.0002,
      \"per_device_train_batch_size\": 4,
      \"max_seq_length\": 512,
      \"lora_r\": 16,
      \"lora_alpha\": 32,
      \"lora_dropout\": 0.1
    }
  }"
```

### Step 2: Get Job ID and Submit

```bash
# Response will include job_id, save it
JOB_ID="<job-id-from-response>"

# Submit job to training queue
curl -X POST "http://localhost:8000/api/v1/finetuning/jobs/${JOB_ID}/submit"
```

### Step 3: Monitor Training

```bash
# Check status
curl "http://localhost:8000/api/v1/finetuning/jobs/${JOB_ID}" | jq '.status, .progress'

# Or watch logs
docker-compose logs -f finetuning-trainer | grep -E "(Epoch|Loss|✅)"
```

### Step 4: Wait for Completion

Poll status every 30 seconds:

```bash
while true; do
  STATUS=$(curl -s "http://localhost:8000/api/v1/finetuning/jobs/${JOB_ID}" | jq -r '.status')
  echo "Status: $STATUS"
  if [ "$STATUS" = "completed" ]; then
    echo "Training complete!"
    break
  fi
  sleep 30
done
```

### Step 5: Get Model ID

```bash
MODEL_ID=$(curl -s "http://localhost:8000/api/v1/finetuning/jobs/${JOB_ID}" | jq -r '.model_id')
echo "Model ID: $MODEL_ID"
```

### Step 6: One-Click Deployment via API

```bash
curl -X POST "http://localhost:8000/api/v1/finetuning/models-public/${MODEL_ID}/deploy" \
  -H "Content-Type: application/json" \
  -d '{
    "deployment_target": "ollama",
    "deployment_config": {
      "model_name": "test-api-e2e-001",
      "base_model": "Qwen/Qwen2.5-1.5B-Instruct"
    }
  }' &

# Monitor logs
docker-compose logs -f --tail=100 backend | grep -E "(Deploy|merge|GGUF|Ollama|✅)"
```

**Duration**: 10-20 minutes

### Step 7: Verify Deployment

```bash
# Check database
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT id, name, status, ollama_model_name 
   FROM finetuned_models 
   WHERE id = '$MODEL_ID';"

# Expected: status = 'deployed', ollama_model_name = 'test-api-e2e-001'

# Check Ollama
docker-compose exec ollama ollama list | grep test-api-e2e
```

### Step 8: Test Inference

```bash
docker-compose exec ollama ollama run test-api-e2e-001 "What is the purpose of this test?"
```

---

## Verification Checklist

### Training Phase ✅

- [ ] Training job created successfully
- [ ] Training started (logs show "Epoch 1/3")
- [ ] Training completed (status = 'completed')
- [ ] LoRA adapter created (~8 MB)
- [ ] Model registered in database

### Deployment Phase ✅

- [ ] Model appears in Governance & Audit UI
- [ ] "Quick Deploy" button visible
- [ ] Deployment started successfully
- [ ] Merge completed (2.9 GB merged model)
- [ ] GGUF conversion completed (3.1 GB f16)
- [ ] Ollama deployment successful
- [ ] Database status updated to 'deployed'

### Inference Phase ✅

- [ ] Model appears in Chat UI dropdown (after refresh)
- [ ] Model can be selected
- [ ] Model responds to queries
- [ ] Responses are relevant (based on training data)
- [ ] No errors in logs

---

## Expected Artifacts

After successful end-to-end test:

```
/workspace/finetuning/<job-id>/
├── output/
│   ├── adapter_model/          # ~8.4 MB LoRA adapter
│   ├── merged_model/           # ~2.9 GB merged model
│   │   ├── model.safetensors
│   │   ├── config.json
│   │   └── tokenizer files
│   └── gguf/
│       └── model-f16.gguf      # ~3.1 GB GGUF file
```

**Database Records**:
- `finetuning_jobs` table: Status = 'completed'
- `finetuned_models` table: Status = 'deployed'

**Ollama**:
- Model listed in `ollama list`
- Model size: ~3.1 GB

---

## Troubleshooting

### Training Issues

**Problem**: Training fails with "GPU out of memory"

**Solution**:
```bash
# Reduce batch size
"per_device_train_batch_size": 2

# Or reduce sequence length
"max_seq_length": 256
```

**Problem**: Training stuck at 0%

**Solution**:
```bash
# Check celery worker
docker-compose logs celery-worker | tail -50

# Restart if needed
docker-compose restart celery-worker
```

### Deployment Issues

**Problem**: "Ollama deployment failed: Unknown deployment error"

**Solution**:
```bash
# Check transformers and PEFT versions
docker-compose exec backend pip show transformers peft

# Should be: transformers>=4.40.0, peft>=0.18.0
# If not, rebuild backend:
docker-compose build backend --no-cache
docker-compose stop backend celery-worker
docker-compose rm -f backend celery-worker
docker-compose up -d backend celery-worker
```

**Problem**: GGUF conversion fails

**Solution**: Already fixed! Code automatically falls back to f16 for K-quants.

**Problem**: Model doesn't appear in Chat UI

**Solution**: Click the refresh icon next to model dropdown.

---

## Performance Benchmarks

### Training (10 samples, 3 epochs)

| Metric | Expected Value |
|--------|---------------|
| Duration | 5-10 minutes |
| Adapter Size | ~8 MB |
| GPU Memory | ~4-6 GB |
| Success Rate | 100% |

### Deployment

| Stage | Duration | Output Size |
|-------|----------|-------------|
| Merge | 2-5 min | 2.9 GB |
| GGUF Conversion | 3-8 min | 3.1 GB |
| Ollama Deploy | 1-2 min | 3.1 GB |
| **Total** | **10-20 min** | **3.1 GB** |

### Inference

| Metric | Expected Value |
|--------|---------------|
| First Token Latency | 200-500ms |
| Tokens/Second | 20-50 (CPU) / 100-200 (GPU) |
| Model Size (VRAM) | ~3 GB |

---

## Success Criteria

End-to-end test is successful when ALL of the following are true:

1. ✅ Training completes without errors
2. ✅ LoRA adapter is generated (~8 MB)
3. ✅ Model appears in Governance UI
4. ✅ One-click deployment completes successfully
5. ✅ Merged model is created (2.9 GB)
6. ✅ GGUF file is created (3.1 GB)
7. ✅ Model is deployed to Ollama
8. ✅ Database status = 'deployed'
9. ✅ Model appears in Chat UI dropdown
10. ✅ Model responds to inference queries

---

## Next Steps After Successful Test

1. **Test with larger dataset** (100+ samples)
2. **Test different base models** (different sizes)
3. **Evaluate model quality** (compare responses to base model)
4. **Benchmark performance** (tokens/second, memory usage)
5. **Test model versioning** (deploy multiple versions)

---

## Documentation

**Full Implementation Details**: `/tmp/ONE_CLICK_DEPLOYMENT_COMPLETE_SUMMARY.md`
**Previous Session**: `/tmp/FINAL_SUCCESS_SUMMARY.md`
**Architecture**: `docs/architecture/` in repository

---

**Last Updated**: 2025-12-23
**Status**: READY FOR TESTING
**Estimated Total Time**: 30-40 minutes
