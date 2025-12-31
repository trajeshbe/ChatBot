# Observability Dashboards Status Report

**Date**: 2025-12-20 10:25 UTC
**Training Job**: `3f68e08f-1739-43e0-9d03-8685a77b74e7`
**Container**: `87ee23971c16`

---

## 📊 Dashboard Access URLs

| Dashboard | URL | Status | Notes |
|-----------|-----|--------|-------|
| **TensorBoard** | http://localhost:6006 | ✅ Running | Mounted to `finetuning_workspaces:/logs` |
| **Grafana** | http://localhost:3000 | ✅ Running | admin/admin |
| **Prometheus** | http://localhost:9090 | ✅ Running | Metrics scraping |
| **Frontend UI** | http://localhost:3001 | ✅ Running | Finetuning page |

---

## 🔍 Current Training Status

### Job Information
- **Job ID**: `3f68e08f-1739-43e0-9d03-8685a77b74e7`
- **Celery Task**: `546cb87e-69e4-4546-a1f8-0cc34939d458`
- **Container**: `87ee23971c16`
- **Status**: Running (Model loading phase)
- **GPU Allocated**: GPU 0 (6.0GB reserved)

### Training Configuration
```json
{
  "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
  "quantization": "4bit",
  "method": "peft",
  "epochs": 3,
  "batch_size": 4,
  "learning_rate": 0.0002,
  "lora_r": 8,
  "lora_alpha": 16
}
```

### Log Locations
- **Training Logs**: `/workspace/finetuning/3f68e08f-1739-43e0-9d03-8685a77b74e7/logs`
- **Output Dir**: `/workspace/finetuning/3f68e08f-1739-43e0-9d03-8685a77b74e7/output`
- **Checkpoints**: `/workspace/finetuning/3f68e08f-1739-43e0-9d03-8685a77b74e7/output/checkpoints`

---

## 📈 Expected Metrics in Each Dashboard

### 1. TensorBoard (http://localhost:6006)

**Expected Scalars**:
- `train/loss` - Training loss per step
- `train/learning_rate` - LR schedule
- `train/epoch` - Current epoch progress
- `train/global_step` - Global step counter

**Path**: Logs written to job-specific directory under `/logs/finetuning/{job_id}/`

**How to Access**:
1. Open http://localhost:6006
2. Wait for logs to appear (usually within first few training steps)
3. Select "Scalars" tab
4. View real-time training metrics

### 2. Grafana (http://localhost:3000)

**Dashboard**: "Reasoning Model - Multi-Reward Training"
**Panel ID**: Check if dashboard exists for PEFT jobs

**Expected Panels** (for GRPO jobs):
- Total Reward Trend
- Reward Breakdown
- Reasoning Quality Metrics
- Reward Weights

**Note**: Current SFT job may not emit reward metrics. GRPO job will show full dashboard.

**How to Access**:
1. Open http://localhost:3000
2. Login: admin/admin
3. Navigate to Dashboards → Reasoning Model
4. Select time range and job filter

### 3. Prometheus (http://localhost:9090)

**Expected Metrics** (for GRPO jobs):
```promql
reward_total_score{job_id="3f68e08f-1739-43e0-9d03-8685a77b74e7"}
reward_correctness_score{job_id="3f68e08f-1739-43e0-9d03-8685a77b74e7"}
reward_batch_avg_total{job_id="3f68e08f-1739-43e0-9d03-8685a77b74e7"}
reasoning_avg_steps_count{job_id="3f68e08f-1739-43e0-9d03-8685a77b74e7"}
```

**How to Access**:
1. Open http://localhost:9090
2. Go to Graph tab
3. Enter metric query
4. Execute and view results

### 4. Frontend UI (http://localhost:3001)

**Page**: Fine-Tuning Dashboard
**Component**: `RewardBreakdownChart.tsx`

**Expected Features**:
- Job list with status
- Real-time progress updates (WebSocket)
- Training metrics (for GRPO jobs)
- Reward breakdown charts (for GRPO jobs)

**How to Access**:
1. Open http://localhost:3001
2. Navigate to Fine-Tuning section
3. Find job `3f68e08f-1739-43e0-9d03-8685a77b74e7`
4. View real-time status and metrics

---

## ⚠️ Current Issues

### Issue 1: TensorBoard Shows No Data (Yet)
**Reason**: Training is still in model loading phase
**Fix**: Wait for first training step (usually 30-60 seconds after model loads)
**Verification**: Check container logs for "Step 1" or "Epoch 1/3"

### Issue 2: Grafana Dashboard May Be Empty
**Reason**: Multi-reward metrics are only emitted for GRPO jobs, not PEFT/SFT
**Expected**: SFT job won't show reward breakdowns
**Solution**: Create general finetuning dashboard for SFT jobs

### Issue 3: Frontend May Not Show Live Metrics
**Reason**: WebSocket endpoint may need frontend refresh
**Fix**: Refresh frontend page after job starts training

---

## ✅ Monitoring Commands

### Check Training Container Logs
```bash
docker logs -f 87ee23971c16
```

### Check Specific Training Metrics
```bash
docker logs 87ee23971c16 | grep -E "Epoch|Step|Loss|lr"
```

### Check TensorBoard Logs Directory
```bash
docker exec 87ee23971c16 ls -la /workspace/finetuning/3f68e08f-1739-43e0-9d03-8685a77b74e7/logs/
```

### Monitor Celery Worker
```bash
docker-compose logs -f celery-worker | grep "3f68e08f"
```

### Check Job Status via API
```bash
curl -H "Authorization: Bearer $(cat /tmp/admin_token.txt)" \
  http://localhost:8000/api/v1/finetuning/jobs/3f68e08f-1739-43e0-9d03-8685a77b74e7 | jq '.'
```

---

## 🎯 Next Steps

1. **Wait for Model Loading** (~30-60 seconds)
2. **Verify Training Starts** - Look for "Step 1/X" in logs
3. **Check TensorBoard** - Refresh browser, look for scalars
4. **Monitor Progress** - Check all 4 dashboards
5. **Document Findings** - Note which dashboards work for SFT vs GRPO

---

**Status**: Training in progress, monitoring enabled ✅
