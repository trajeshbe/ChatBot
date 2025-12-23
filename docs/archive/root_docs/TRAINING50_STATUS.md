# Fine-Tuning Job: choles-qa-real-training50

**Job ID**: `0d088e56-7986-47e2-961d-0245a9c318af`
**Celery Task ID**: `bff0df17-c4d8-4325-8a0b-528475642707`
**Status**: 🟡 **RUNNING** - Model Loading Phase
**Started**: 2025-12-23 06:35:10 UTC
**Last Updated**: 2025-12-23 06:37:00 UTC (auto-generated)

---

## 📊 Job Configuration

| Parameter | Value |
|-----------|-------|
| **Base Model** | Qwen/Qwen2.5-1.5B-Instruct |
| **Method** | PEFT (LoRA/QLoRA) |
| **Dataset** | company_qa_dataset.jsonl |
| **Dataset Format** | chat |
| **Quantization** | 4-bit (QLoRA) |
| **GPU** | NVIDIA GeForce RTX 5060 Laptop GPU (8GB) |
| **GPU Count** | 1 |

### Hyperparameters

```json
{
  "learning_rate": 0.0002,
  "num_epochs": 3,
  "batch_size": 4,
  "gradient_accumulation_steps": 4,
  "lora_r": 16,
  "lora_alpha": 32,
  "lora_dropout": 0.05,
  "target_modules": ["q_proj", "v_proj"],
  "warmup_steps": 100,
  "max_seq_length": 2048
}
```

**Effective Batch Size**: 4 (batch) × 4 (accumulation) = **16 samples per update**

---

## 🔄 Current Status

### Training Stage: **Model Loading**

The training container is currently loading the Qwen2.5-1.5B model with 4-bit quantization. This is normal and can take 2-5 minutes depending on disk I/O.

**Container**: `finetuning-0d088e56-7986-47e2-961d-0245a9c318af`
**Status**: ✅ Running (healthy)
**Started**: 2025-12-23 06:35:12 UTC
**Uptime**: ~2 minutes

### Resource Usage (as of last check)

| Resource | Usage |
|----------|-------|
| **CPU** | 11.29% |
| **Memory** | 1.7 GB / 11.5 GB (14.76%) |
| **GPU Memory** | 0 MiB / 8151 MiB (0%) - Not yet loaded |
| **GPU Utilization** | 0% - Waiting for model |

### Progress Indicators

- ✅ Dependencies loaded
- ✅ Tokenizer loaded
- ✅ 4-bit quantization configured
- 🔄 **Currently**: Loading model from HuggingFace cache
- ⏳ **Next**: Load dataset and prepare training
- ⏳ **Then**: Begin training (3 epochs)

### Training Metrics

**Database Status**:
- Total metrics recorded: 0 (training not started yet)
- Current epoch: N/A
- Current step: N/A
- Progress: 0%

---

## 📂 Paths

| Type | Path |
|------|------|
| **Dataset** | `/workspace/finetuning/0d088e56-7986-47e2-961d-0245a9c318af/input` |
| **Output** | `/workspace/finetuning/0d088e56-7986-47e2-961d-0245a9c318af/output` |
| **Checkpoints** | `/workspace/finetuning/0d088e56-7986-47e2-961d-0245a9c318af/output/checkpoints` |
| **Logs** | `/workspace/finetuning/0d088e56-7986-47e2-961d-0245a9c318af/logs` |
| **MinIO Dataset** | `technology/itm11/global/admin/finetuning/datasets/company_qa_dataset/added64c-16fd-42a9-9370-e08f2516f198/company_qa_dataset.jsonl` |

---

## 🖥️ Monitoring Commands

### Live Log Monitoring

```bash
# Follow training logs in real-time
docker logs -f finetuning-0d088e56-7986-47e2-961d-0245a9c318af

# Last 100 lines
docker logs --tail=100 finetuning-0d088e56-7986-47e2-961d-0245a9c318af

# New logs only (last 30 seconds)
docker logs --tail=50 --since=30s finetuning-0d088e56-7986-47e2-961d-0245a9c318af
```

### Resource Monitoring

```bash
# Container stats
docker stats finetuning-0d088e56-7986-47e2-961d-0245a9c318af

# GPU usage
docker exec finetuning-0d088e56-7986-47e2-961d-0245a9c318af nvidia-smi

# Watch GPU usage (updates every 2 seconds)
watch -n 2 "docker exec finetuning-0d088e56-7986-47e2-961d-0245a9c318af nvidia-smi"
```

### Database Monitoring

```bash
# Check job status
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT status, progress, training_stage, current_epoch, current_step, updated_at
   FROM finetuning_jobs
   WHERE id = '0d088e56-7986-47e2-961d-0245a9c318af';"

# Check training metrics
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT epoch, step, train_loss, eval_loss, gpu_utilization, timestamp
   FROM training_metrics
   WHERE job_id = '0d088e56-7986-47e2-961d-0245a9c318af'
   ORDER BY timestamp DESC LIMIT 10;"

# Count total metrics
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) as total_metrics, MAX(epoch) as max_epoch, MAX(step) as max_step,
          AVG(train_loss) as avg_train_loss
   FROM training_metrics
   WHERE job_id = '0d088e56-7986-47e2-961d-0245a9c318af';"
```

### TensorBoard

```bash
# Access TensorBoard (if enabled)
# URL: http://localhost:6006

# Check if TensorBoard is running
curl -s http://localhost:6006 | grep -q "TensorBoard" && echo "TensorBoard is running" || echo "TensorBoard not available"
```

---

## ⏱️ Expected Timeline

Based on typical Qwen2.5-1.5B fine-tuning with these parameters:

| Phase | Estimated Duration | Status |
|-------|-------------------|--------|
| **Model Loading** | 2-5 minutes | 🔄 In Progress |
| **Dataset Loading** | 30-60 seconds | ⏳ Pending |
| **Training Setup** | 30-60 seconds | ⏳ Pending |
| **Epoch 1** | 10-30 minutes* | ⏳ Pending |
| **Epoch 2** | 10-30 minutes* | ⏳ Pending |
| **Epoch 3** | 10-30 minutes* | ⏳ Pending |
| **Final Checkpoint** | 1-2 minutes | ⏳ Pending |
| **Model Merge** | 2-5 minutes | ⏳ Pending |
| **Upload to MinIO** | 1-2 minutes | ⏳ Pending |

**Total Estimated Time**: 35-100 minutes (depends on dataset size)

*Time per epoch depends on dataset size. Estimate assumes 100-500 samples.

---

## 🎯 What to Expect Next

1. **Model Loading Complete** (~2-3 more minutes)
   - You'll see: "Model loaded successfully" in logs
   - GPU memory will jump to ~4-6 GB

2. **Dataset Loading** (~30-60 seconds)
   - Logs will show number of training samples
   - Train/validation split information

3. **Training Begins**
   - Loss values will start appearing
   - Progress bars for each epoch
   - Metrics saved to database every few steps

4. **Checkpoints**
   - Saved at the end of each epoch
   - Uploaded to MinIO automatically

5. **Completion**
   - Final model merged (LoRA adapters + base model)
   - Uploaded to MinIO
   - Job status changes to "completed"
   - Model available in registry

---

## 📈 Success Indicators

Watch for these in the logs:

- ✅ "Model loaded successfully"
- ✅ "Trainable parameters: X (Y% of total)"
- ✅ "Training started"
- ✅ "Epoch 1/3"
- ✅ Loss values decreasing over time
- ✅ "Training completed successfully"
- ✅ "Model merged and saved"

---

## ⚠️ Potential Issues

### If training hangs at "Loading model...":
- **Cause**: Model download or disk I/O slow
- **Check**: `docker stats` for high I/O wait
- **Solution**: Wait 5-10 minutes. If still stuck, check disk space and container logs for errors

### If GPU memory error occurs:
- **Cause**: Model too large for 8GB GPU
- **Check**: Logs for "CUDA out of memory"
- **Solution**: Already using 4-bit quantization (should fit). If still issues, reduce `batch_size` to 2

### If training is very slow:
- **Cause**: CPU-only training or low GPU utilization
- **Check**: `nvidia-smi` shows GPU usage
- **Solution**: Ensure GPU is detected (`nvidia-smi` in container)

---

## 📝 Current Logs

**Last Known Log Entry** (as of 06:37:00 UTC):
```
2025-12-23 06:35:27,506 - __main__ - INFO - Loading model Qwen/Qwen2.5-1.5B-Instruct...
```

**Log Line Count**: 40 lines (still initializing)

---

## 🔗 Related Resources

- **Job Database Entry**: `finetuning_jobs` table, ID `0d088e56-7986-47e2-961d-0245a9c318af`
- **Dataset**: `finetuning_datasets` table, ID `added64c-16fd-42a9-9370-e08f2516f198`
- **Celery Task**: `bff0df17-c4d8-4325-8a0b-528475642707`
- **Container**: `finetuning-0d088e56-7986-47e2-961d-0245a9c318af`

---

## 🔄 Auto-Refresh

To continuously monitor this job, run:

```bash
# Every 10 seconds, show latest status
watch -n 10 '
  echo "=== JOB STATUS ===" && \
  docker-compose exec postgres psql -U postgres -d ragchatbot -t -c \
    "SELECT status, progress, training_stage, current_epoch, current_step
     FROM finetuning_jobs
     WHERE id = '\''0d088e56-7986-47e2-961d-0245a9c318af'\'';" && \
  echo "" && \
  echo "=== LATEST LOGS ===" && \
  docker logs --tail=10 finetuning-0d088e56-7986-47e2-961d-0245a9c318af 2>&1 | tail -10 && \
  echo "" && \
  echo "=== GPU STATUS ===" && \
  docker exec finetuning-0d088e56-7986-47e2-961d-0245a9c318af nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader 2>/dev/null || echo "GPU not yet loaded"
'
```

---

**Next Update**: Check logs in 5-10 minutes for training progress or run monitoring commands above.
