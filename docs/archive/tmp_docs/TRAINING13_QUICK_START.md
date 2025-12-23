# Training13 Quick Start Guide

**Purpose**: Create and monitor training13 to verify real training occurs

---

## Quick Start (3 Steps)

### Step 1: Run the Automated Script
```bash
bash /tmp/create_training13.sh
```

This script will:
1. ✅ Verify fixes are active
2. ✅ Guide you through job creation via UI
3. ✅ Auto-detect job ID and container
4. ✅ Check initial indicators
5. ✅ Provide monitoring commands

---

### Step 2: Monitor in Real-Time (3 Terminals)

**Terminal 1 - Full Logs** (saves to file):
```bash
docker logs -f $TRAINING13_CONTAINER 2>&1 | tee /tmp/training13_full_logs.txt
```

**Terminal 2 - Training Progress** (filtered):
```bash
/tmp/monitor_training13_live.sh $TRAINING13_JOB_ID
```

**Terminal 3 - Database Status** (updates every 10 sec):
```bash
watch -n 10 "docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \"SELECT status, training_stage, current_epoch, current_step, train_loss FROM finetuning_jobs WHERE id = '$TRAINING13_JOB_ID';\""
```

---

### Step 3: Verify Success

**After 15-30 minutes**, check for these indicators:

✅ **Real Training Confirmed**:
```
Logs show:
  🚀 Starting REAL training (NOT mock)...
  Loaded 10 training samples
  Epoch 1/3:
    Step 1/4: Loss: 2.451
    Step 2/4: Loss: 2.103
    ...
  ✅ REAL Training Completed Successfully!

Duration: 15-30 minutes
Team: ITM11
Path: technology/itm11/...
```

❌ **Mock Training Detected**:
```
Logs show:
  ⚠️ No dataset provided
  ✅ Mock training with merge completed successfully

Duration: 6-8 minutes
No Epoch/Step logs
```

---

## Save Logs Before Container Removal

**IMPORTANT**: Container auto-removes after completion!

```bash
# Save complete logs
docker logs $TRAINING13_CONTAINER > /tmp/training13_complete_logs.txt 2>&1

echo "Logs saved to /tmp/training13_complete_logs.txt"
```

---

## Manual Job Creation (If Not Using Script)

1. Go to: http://localhost:3001/finetuning
2. Fill in:
   - **Job Name**: `choles-qa-real-training13`
   - **Base Model**: `Qwen/Qwen2.5-1.5B-Instruct`
   - **Dataset**: `company_qa_dataset.jsonl`
   - **Method**: PEFT (LoRA)
   - **Quantization**: 4-bit
   - **Epochs**: 3
   - **Batch Size**: 4
   - **Learning Rate**: 2e-4
3. Submit
4. Get job ID:
   ```bash
   docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
   SELECT id FROM finetuning_jobs
   WHERE name = 'choles-qa-real-training13'
   ORDER BY created_at DESC
   LIMIT 1;"
   ```
5. Follow monitoring commands above

---

## Key Success Criteria

| Criterion | Expected (Real) | Suspicious (Mock) |
|-----------|----------------|-------------------|
| **Duration** | 15-30 minutes | 6-8 minutes |
| **Log Message** | "REAL training (NOT mock)" | "Mock training" |
| **Dataset** | "Loaded X samples" | "No dataset provided" |
| **Epochs** | "Epoch 1/3:", "2/3:", "3/3:" | No epoch logs |
| **Steps** | "Step X/Y: Loss: X.XXX" | No step logs |
| **Team** | ITM11 | ITM11 ✅ (this is fixed) |
| **Path** | technology/itm11/... | technology/itm11/... ✅ (this is fixed) |

---

## Troubleshooting

**Container doesn't start**:
```bash
# Check Celery logs
docker-compose logs celery | grep training13
```

**"No dataset provided" in logs**:
```bash
# Check if dataset exists in MinIO
docker-compose exec backend python3 << 'EOF'
from minio import Minio
import os
client = Minio("minio:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)
path = "technology/itm11/science/admin/finetuning/datasets/company_qa_dataset.jsonl"
try:
    client.stat_object("documents", path)
    print(f"✅ Dataset exists: {path}")
except Exception as e:
    print(f"❌ Dataset not found: {e}")
EOF
```

**Training seems stuck**:
```bash
# Check database status
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
SELECT status, training_stage, current_epoch, updated_at
FROM finetuning_jobs
WHERE name = 'choles-qa-real-training13';"
```

---

## Summary

✅ **Option 2 is ready!**

1. Run: `bash /tmp/create_training13.sh`
2. Follow the prompts
3. Monitor in 3 terminals
4. Wait 15-30 minutes
5. Verify real training occurred

**Files Available**:
- `/tmp/create_training13.sh` - Automated creation & monitoring script
- `/tmp/monitor_training13_live.sh` - Live progress monitoring (auto-created)
- `/tmp/TRAINING13_MONITORING_GUIDE.md` - Detailed guide
- `/tmp/TRAINING13_QUICK_START.md` - This quick reference

---

**End of Quick Start**
