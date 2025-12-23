# Training13 with Comprehensive Monitoring

**Date**: 2025-12-21
**Purpose**: Create training13 with real-time monitoring to definitively verify real training occurs

---

## Why Training13?

Based on training12 analysis:
- ✅ FIX #2 verified: MinIO path uses `itm11`
- ⚠️ FIX #1 uncertain: Duration was only 6 minutes (suspicious for real training)
- ❌ No container logs available (auto-removed)

**Solution**: Create training13 with **real-time monitoring** before container is removed

---

## Pre-Flight Checklist

Before creating training13, verify both fixes are still active:

```bash
# 1. Verify real training code is uncommented
docker-compose exec backend grep -A 5 "REAL TRAINING - Now enabled" /app/app/services/finetuning/trainers/peft_trainer.py

# Should show:
# REAL TRAINING - Now enabled!
# from transformers import Trainer, DataCollatorForSeq2Seq

# 2. Verify team query fix
docker-compose exec backend grep -A 8 "Get user's primary team from user_teams" /app/app/api/routes/finetuning_routes.py

# Should show SQL query to user_teams table

# 3. Check backend status
docker-compose ps backend
# Should be: Up (healthy)
```

---

## Step 1: Create Training13 via UI

1. Go to **Fine-Tuning** page
2. Fill in details:
   - **Job Name**: `choles-qa-real-training13`
   - **Base Model**: `Qwen/Qwen2.5-1.5B-Instruct`
   - **Dataset**: `company_qa_dataset.jsonl`
   - **Method**: PEFT (LoRA)
   - **Quantization**: 4-bit
   - **Epochs**: 3
   - **Batch Size**: 4
   - **Learning Rate**: 2e-4

3. Click **Submit Training Job**

4. **IMMEDIATELY** note the job ID from the response or database

---

## Step 2: Get Job ID and Container Name

```bash
# Get job ID from database
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
SELECT id, name, status, created_at
FROM finetuning_jobs
WHERE name = 'choles-qa-real-training13'
ORDER BY created_at DESC
LIMIT 1;"

# Save the ID (e.g., abc123-def456-...)
export JOB_ID="<paste-job-id-here>"

# Container name will be: finetuning-<job_id>
export CONTAINER_NAME="finetuning-$JOB_ID"

echo "Job ID: $JOB_ID"
echo "Container: $CONTAINER_NAME"
```

---

## Step 3: Monitor Training in Real-Time

### Terminal 1: Container Logs (Full)

```bash
# Follow all container logs
docker logs -f $CONTAINER_NAME 2>&1 | tee /tmp/training13_full_logs.txt
```

**Keep this running!** This captures everything.

### Terminal 2: Training Progress

```bash
# Monitor for training-specific logs
docker logs -f $CONTAINER_NAME 2>&1 | grep -E "Epoch|Step|Loss|Training|Mock|REAL|dataset|samples"
```

### Terminal 3: Database Status

```bash
# Monitor database updates every 10 seconds
watch -n 10 "docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \"
SELECT status, training_stage, current_epoch, current_step, train_loss, updated_at
FROM finetuning_jobs
WHERE id = '$JOB_ID';
\""
```

---

## Step 4: What to Look For

### ✅ REAL TRAINING Indicators

```
🚀 Starting REAL training (NOT mock)...
Loaded 10 training samples
Epoch 1/3:
  Step 1/4: Loss: 2.451
  Step 2/4: Loss: 2.103
  Step 3/4: Loss: 1.892
  Step 4/4: Loss: 1.734
Epoch 2/3:
  Step 1/4: Loss: 1.623
  ...
✅ Training completed!
   Final loss: 1.234
✅ REAL Training Completed Successfully!
```

### ❌ MOCK TRAINING Indicators

```
⚠️ No dataset provided, creating mock training result with merge step
✅ Adapter saved to /workspace/output/adapter_model
🔄 Merging PEFT adapters into base model...
✅ Mock training with merge completed successfully
```

---

## Step 5: Critical Checkpoints

### Checkpoint 1: Container Started (0-2 minutes)

```bash
# Verify container exists
docker ps | grep $CONTAINER_NAME

# Should show: Up X seconds
```

### Checkpoint 2: Dataset Loading (2-3 minutes)

```bash
# Check for dataset loading
docker logs $CONTAINER_NAME 2>&1 | grep -i "dataset"

# Expected:
# Loading dataset from /workspace/input/dataset...
# ✅ Loaded 10 training samples
```

**If you see "No dataset provided"**: ❌ Training will be mock!

### Checkpoint 3: Training Started (3-5 minutes)

```bash
# Check for training start
docker logs $CONTAINER_NAME 2>&1 | grep -E "Starting.*training"

# Expected:
# 🚀 Starting REAL training (NOT mock)...

# NOT expected:
# ✅ Mock training with merge completed successfully
```

### Checkpoint 4: Epoch Progress (5-20 minutes)

```bash
# Check for epoch/step logs
docker logs $CONTAINER_NAME 2>&1 | grep -E "Epoch|Step.*Loss"

# Expected:
# Epoch 1/3:
#   Step 1/4: Loss: 2.451
#   Step 2/4: Loss: 2.103
```

**If no Epoch/Step logs**: ❌ Mock training occurred!

### Checkpoint 5: Completion (15-30 minutes)

```bash
# Check final message
docker logs $CONTAINER_NAME 2>&1 | tail -20

# Expected:
# ✅ REAL Training Completed Successfully!

# NOT expected:
# ✅ Mock training with merge completed successfully
```

---

## Step 6: Post-Training Verification

### 1. Check Training Duration

```bash
# Get job timestamps
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
SELECT
  name,
  created_at,
  updated_at,
  EXTRACT(EPOCH FROM (updated_at - created_at))/60 as duration_minutes,
  status
FROM finetuning_jobs
WHERE name = 'choles-qa-real-training13';"
```

**Expected**: 15-30 minutes for real training
**Suspicious**: 6-8 minutes (indicates mock training)

### 2. Check MinIO Path

```bash
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
SELECT minio_checkpoint_path
FROM finetuning_jobs
WHERE name = 'choles-qa-real-training13';"
```

**Expected**: `technology/itm11/...`
**Wrong**: `technology/backend-development/...`

### 3. Save Complete Logs

```bash
# Save logs before container is removed
docker logs $CONTAINER_NAME > /tmp/training13_complete_logs.txt 2>&1

echo "Logs saved to /tmp/training13_complete_logs.txt"
```

### 4. Run Base vs Fine-Tuned Test

```bash
# Update the test script with training13 job ID
# Then run the functional test from Option 1
```

---

## Troubleshooting During Training

### Issue: "No dataset provided"

**Cause**: Dataset failed to download from MinIO

**Solution**:
```bash
# Check if dataset exists in MinIO
docker-compose exec backend python3 << 'EOF'
from minio import Minio
import os

client = Minio(
    "minio:9000",
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False
)

# Check dataset path
path = "technology/itm11/science/admin/finetuning/datasets/company_qa_dataset.jsonl"
try:
    client.stat_object("documents", path)
    print(f"✅ Dataset exists: {path}")
except Exception as e:
    print(f"❌ Dataset not found: {e}")
EOF
```

### Issue: Container exits immediately

**Cause**: Configuration error or missing dependencies

**Solution**:
```bash
# Check container exit status
docker ps -a | grep $CONTAINER_NAME

# Check container logs
docker logs $CONTAINER_NAME 2>&1 | head -50
```

### Issue: "REAL training" message but no Epoch/Step logs

**Cause**: Dataset loaded but training failed to start

**Solution**:
```bash
# Check for errors after "Starting REAL training"
docker logs $CONTAINER_NAME 2>&1 | grep -A 20 "Starting REAL training"
```

---

## Success Criteria

Training13 is successful if ALL of these are true:

- ✅ Container runs for 15-30 minutes (not 6-8)
- ✅ Logs show "🚀 Starting REAL training (NOT mock)..."
- ✅ Logs show "Loaded X training samples" (not "No dataset provided")
- ✅ Logs show "Epoch 1/3:", "Epoch 2/3:", "Epoch 3/3:"
- ✅ Logs show "Step X/Y: Loss: X.XXX" progression
- ✅ Logs show "✅ REAL Training Completed Successfully!" (not "Mock training")
- ✅ MinIO path uses `technology/itm11/...`
- ✅ Final loss is different from initial loss (learning occurred)
- ✅ Functional test shows fine-tuned model answers company questions correctly

---

## Quick Monitoring Script

Save this as `/tmp/monitor_training13.sh`:

```bash
#!/bin/bash

# Usage: ./monitor_training13.sh <job_id>

JOB_ID=$1

if [ -z "$JOB_ID" ]; then
    echo "Usage: $0 <job_id>"
    echo "Get job_id from: docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \"SELECT id FROM finetuning_jobs WHERE name = 'choles-qa-real-training13';\""
    exit 1
fi

CONTAINER_NAME="finetuning-$JOB_ID"

echo "Monitoring Training Job: $JOB_ID"
echo "Container: $CONTAINER_NAME"
echo "============================================================"

# Wait for container to start
echo "Waiting for container to start..."
for i in {1..30}; do
    if docker ps | grep -q $CONTAINER_NAME; then
        echo "✅ Container started!"
        break
    fi
    sleep 2
done

# Monitor key indicators
echo ""
echo "============================================================"
echo "KEY TRAINING INDICATORS"
echo "============================================================"

sleep 10

echo ""
echo "1. Dataset Loading:"
docker logs $CONTAINER_NAME 2>&1 | grep -i "dataset\|samples" | head -5

echo ""
echo "2. Training Type:"
docker logs $CONTAINER_NAME 2>&1 | grep -E "REAL training|Mock training"

echo ""
echo "3. Training Progress:"
docker logs $CONTAINER_NAME 2>&1 | grep -E "Epoch|Step.*Loss" | head -10

echo ""
echo "4. Database Status:"
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
SELECT status, training_stage, current_epoch, current_step, train_loss
FROM finetuning_jobs
WHERE id = '$JOB_ID';"

echo ""
echo "============================================================"
echo "Continue monitoring with:"
echo "  docker logs -f $CONTAINER_NAME"
echo "============================================================"
```

Run with:
```bash
chmod +x /tmp/monitor_training13.sh
/tmp/monitor_training13.sh <job_id>
```

---

## Summary

**Option 2 provides**:
- Real-time monitoring before logs are lost
- Multiple verification checkpoints
- Clear success/failure indicators
- Complete log preservation
- Immediate detection of mock training

**When to use**: After Option 1 (functional test) if training12 shows mock training, or if you want definitive proof that real training is working.

---

**Next Steps**:
1. Wait for Option 1 (functional test) results
2. If test shows mock training → Create training13 with monitoring
3. If test shows real training → Both fixes are verified ✅

---

**End of Guide**
