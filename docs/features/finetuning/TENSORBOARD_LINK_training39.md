# TensorBoard Link for choles-qa-real-training39

## 📊 Training Job Details

- **Job Name**: choles-qa-real-training39
- **Job ID**: `c5ec9d51-4154-4b11-b732-9cb95b21995d`
- **Status**: Running (started at 2025-12-22 08:18:07 UTC)
- **Dataset**: company_qa_dataset (9 training samples, 1 validation sample)
- **Base Model**: Qwen/Qwen2.5-1.5B-Instruct
- **GPU**: GPU 0 (6.0GB VRAM allocated)

---

## 🔗 TensorBoard Links

### Main TensorBoard Dashboard:
**http://localhost:6006/**

### Direct Link to Loss Graph:
**http://localhost:6006/#timeseries&runFilter=c5ec9d51-4154-4b11-b732-9cb95b21995d**

### Alternative View - Scalars Tab:
**http://localhost:6006/#scalars&runFilter=c5ec9d51-4154-4b11-b732-9cb95b21995d**

---

## ⏱️ When Will Loss Graph Appear?

TensorBoard event files are created during training. You should see the loss graph appear:

1. **Initial appearance**: After the first training step completes (~1-2 minutes after training starts)
2. **Updates**: Real-time updates every few steps (every 30-60 seconds during training)
3. **Full graph**: Complete loss curve after all epochs finish

### Current Status:
- Training container started: ✅ (at 08:18:08 UTC)
- Model loading: In progress... (takes 1-2 min for Qwen 1.5B)
- First training step: Expected at ~08:19-08:20 UTC
- **First loss data point**: Should appear in TensorBoard by ~08:20 UTC

---

## 🔄 How to View the Loss Graph

### Option 1: Direct Link (Recommended)
Click this link once training starts logging metrics:
**http://localhost:6006/#timeseries&runFilter=c5ec9d51-4154-4b11-b732-9cb95b21995d**

### Option 2: Navigate Manually
1. Open: http://localhost:6006/
2. Look for your run: `c5ec9d51-4154-4b11-b732-9cb95b21995d`
3. Click on **"Scalars"** or **"Time Series"** tab
4. Select metrics: `train/loss`, `eval/loss`
5. Graph will update automatically as training progresses

### Option 3: Filter by Name
1. Open: http://localhost:6006/
2. In the top filter box, type: `c5ec9d51`
3. Your training run will be highlighted
4. Click on it to view graphs

---

## 📈 Expected Metrics

You should see these metrics in TensorBoard:

### Training Metrics:
- **train/loss** - Training loss (should decrease over time)
- **train/grad_norm** - Gradient norm
- **train/learning_rate** - Learning rate schedule
- **train/epoch** - Current epoch

### Evaluation Metrics:
- **eval/loss** - Validation loss
- **eval/accuracy** - Validation accuracy (if applicable)

### System Metrics:
- **train/samples_per_second** - Training throughput
- **train/steps_per_second** - Step speed

---

## 🐛 Troubleshooting

### "No runs found" in TensorBoard?

**Check 1: Is training actually running?**
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT status FROM finetuning_jobs WHERE id = 'c5ec9d51-4154-4b11-b732-9cb95b21995d';"
```
Should return: `running`

**Check 2: Are event files being created?**
```bash
docker-compose exec tensorboard find /logs/c5ec9d51-4154-4b11-b732-9cb95b21995d -name "*.tfevents.*"
```
Should return paths to event files (may be empty initially, files created after first step)

**Check 3: Training container logs**
```bash
docker-compose logs celery-worker --tail 100 | grep -E "(c5ec9d51|loss|step)"
```
Look for training progress messages

**Check 4: Refresh TensorBoard**
- Click the "Reload" button (circular arrow icon) in TensorBoard UI
- Or refresh browser: `Ctrl+Shift+R` (Windows) / `Cmd+Shift+R` (Mac)

### Graph appears but no data?

Training is still initializing. Wait 2-5 minutes after training starts for:
1. Model download/loading
2. Dataset loading
3. First training step to complete
4. TensorBoard event file to be written

### Only seeing old runs?

Use the **run filter** to show only your current job:
- Filter text: `c5ec9d51-4154-4b11-b732-9cb95b21995d`
- Or partial: `c5ec9d51`

---

## 📂 Log Directory Structure

```
/logs/c5ec9d51-4154-4b11-b732-9cb95b21995d/
├── input/          # Input dataset
├── logs/           # TensorBoard event files (*.tfevents.*)
├── output/         # Trained model checkpoints
└── temp/           # Temporary files
```

TensorBoard reads from: `/logs/c5ec9d51-4154-4b11-b732-9cb95b21995d/logs/`

---

## 🎯 Quick Access

**Copy-paste this link** (works once training starts logging):

```
http://localhost:6006/#timeseries&runFilter=c5ec9d51-4154-4b11-b732-9cb95b21995d
```

**Or just the job ID for filtering**:
```
c5ec9d51-4154-4b11-b732-9cb95b21995d
```

---

## ⏰ Timeline

- **08:18:07** - Training job submitted ✅
- **08:18:08** - Container started ✅
- **08:18-08:19** - Model loading (in progress...)
- **08:19-08:20** - First training step (expected)
- **08:20+** - Loss graph appears in TensorBoard 📊

**Current time**: Check current UTC time and compare to timeline above.

**Estimated wait**: 1-3 minutes from training start (08:18:07) until first loss data point appears.

---

## 🔄 Auto-Refresh

TensorBoard auto-refreshes every 30 seconds. If you don't see your run:
1. Wait 1-2 minutes
2. Click the reload button in TensorBoard
3. Check that training is still running (status query above)

---

**Summary**: Your training is running! Open the link below and wait 1-3 minutes for the loss graph to appear:

🔗 **http://localhost:6006/#timeseries&runFilter=c5ec9d51-4154-4b11-b732-9cb95b21995d**

---

**End of Document**
