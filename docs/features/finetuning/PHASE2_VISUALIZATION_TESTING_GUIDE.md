# Phase 2: Real-Time Visualization - Testing & Integration Guide

**Date**: 2025-12-20
**Status**: ✅ **READY FOR TESTING**

---

## 🎯 What Was Built

### Backend Metrics System ✅
1. **20 Prometheus Metrics** - Extended finetuning_metrics.py
2. **RewardMetricsEmitter** - 470 lines, emits to 4 destinations
3. **GRPO Trainer Integration** - Full metrics emission during training
4. **TensorBoard Logging** - Automatic Rewards/* scalars

### Frontend Visualization ✅
1. **Grafana Dashboard** - `reasoning-rewards-dashboard.json` (8 panels)
2. **React Component** - `RewardBreakdownChart.tsx` (440 lines)

---

## 📋 Pre-Testing Checklist

### 1. Verify Services Running

```bash
# Check all services
docker-compose ps

# Should see:
# ✅ backend (port 8000)
# ✅ frontend (port 3001)
# ✅ prometheus (port 9090)
# ✅ grafana (port 3000)
# ✅ postgres (port 5432)
```

### 2. Verify Prometheus Metrics Available

```bash
# Check metrics endpoint
curl http://localhost:8000/metrics | grep reward_

# Expected output (sample):
# reward_total_score{batch="0",job_id="test",job_name="GRPO Training",response_idx="0"} 0.85
# reward_correctness_score{...} 0.90
# reward_batch_avg_total{...} 0.83
# ...
```

### 3. Import Grafana Dashboard

**Manual Import**:
1. Open Grafana: http://localhost:3000
2. Login: `admin` / `admin` (or configured credentials)
3. Go to **Dashboards** → **Import**
4. Click **Upload JSON file**
5. Select: `observability/grafana/dashboards/reasoning-rewards-dashboard.json`
6. Click **Import**

**Expected Result**: Dashboard appears with 8 panels:
- Total Reward Trend
- Reward Breakdown (Stacked Area)
- Reasoning Quality Metrics
- Reward Weights Configuration
- 4 Gauge/Stat panels

---

## 🧪 Testing Scenarios

### Scenario 1: Backend Metrics Emission (Unit Test)

**Test**: Verify metrics emitter works in isolation

```bash
# Create test script
cd backend

cat > test_metrics_emitter.py << 'EOF'
import sys
sys.path.insert(0, '/app')

from app.services.finetuning.rewards.metrics_emitter import RewardMetricsEmitter

# Initialize emitter
emitter = RewardMetricsEmitter(
    job_id="test_job_123",
    job_name="Test GRPO Training",
    enable_prometheus=True,
    enable_websocket=False,
    enable_tensorboard=False
)

# Emit test metrics
breakdown = {
    "Correctness": {"score": 0.90, "weight": 2.0, "contribution": 1.80, "applicable": True},
    "ReasoningClarity": {"score": 0.80, "weight": 1.5, "contribution": 1.20, "applicable": True},
    "StepByStep": {"score": 1.00, "weight": 1.0, "contribution": 1.00, "applicable": True},
    "Efficiency": {"score": 0.70, "weight": 0.8, "contribution": 0.56, "applicable": True},
    "MathematicalNotation": {"score": 0.85, "weight": 1.2, "contribution": 1.02, "applicable": False},
    "Coherence": {"score": 0.95, "weight": 1.0, "contribution": 0.95, "applicable": True}
}

emitter.emit_reward_breakdown(
    total_reward=0.85,
    breakdown=breakdown,
    batch_idx=0,
    response_idx=0,
    reasoning_steps=["Step 1", "Step 2", "Step 3", "Step 4"],
    step=0
)

emitter.emit_batch_aggregates(
    batch_idx=0,
    avg_total_reward=0.83,
    avg_rewards={"Correctness": 0.88, "ReasoningClarity": 0.79},
    avg_steps_count=4.2,
    avg_tokens_per_step=22.5
)

emitter.emit_reward_weights({
    "Correctness": 2.0,
    "ReasoningClarity": 1.5,
    "StepByStep": 1.0,
    "Efficiency": 0.8,
    "MathematicalNotation": 1.2,
    "Coherence": 1.0
})

print("✅ Metrics emitted successfully!")

# Check Prometheus metrics
import requests
response = requests.get("http://localhost:8000/metrics")
if "reward_total_score" in response.text:
    print("✅ Prometheus metrics available!")
else:
    print("❌ Prometheus metrics NOT found!")

emitter.close()
EOF

# Run test
docker-compose exec backend python /app/test_metrics_emitter.py
```

**Expected Output**:
```
✅ Metrics emitted successfully!
✅ Prometheus metrics available!
```

**Verify in Prometheus**:
```bash
# Query Prometheus
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=reward_total_score{job_id="test_job_123"}'

# Expected: {"status":"success", "data":{"result":[{"metric":{...}, "value":[timestamp, "0.85"]}]}}
```

---

### Scenario 2: TensorBoard Logging Test

**Test**: Verify TensorBoard receives metrics

```bash
# Check TensorBoard logs directory
docker-compose exec backend ls -la /workspace/output/logs/

# Should see: test_job_123/ directory

# View TensorBoard events
docker-compose exec backend python -c "
from tensorboard.backend.event_processing import event_accumulator
import glob

log_dir = '/workspace/output/logs/test_job_123'
ea = event_accumulator.EventAccumulator(log_dir)
ea.Reload()

print('Available tags:', ea.Tags())
print('Scalars:', ea.scalars.Keys())
"
```

**Access TensorBoard**:
```bash
# TensorBoard should already be running
open http://localhost:6006

# Navigate to:
# - Scalars → Rewards/Total/Response_0
# - Scalars → Rewards/Correctness/Response_0
# - Scalars → Reasoning/StepCount/Response_0
```

**Expected**: Line charts showing reward trends

---

### Scenario 3: WebSocket Streaming Test

**Test**: Verify real-time WebSocket messages

**Option A: Browser Console**
```javascript
// Open browser console (F12) and run:
const ws = new WebSocket('ws://localhost:8000/ws/jobs/test_job_123/metrics');

ws.onopen = () => console.log('✅ Connected');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('📊 Received:', data.type, data);
};
ws.onerror = (error) => console.error('❌ Error:', error);
```

**Option B: Python Client**
```python
# Create WebSocket client
cat > test_websocket.py << 'EOF'
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/jobs/test_job_123/metrics"
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket")

        # Wait for messages
        for i in range(5):
            message = await websocket.recv()
            data = json.parse(message)
            print(f"📊 Received: {data['type']}")

asyncio.run(test_websocket())
EOF

python test_websocket.py
```

**Expected Messages**:
```json
{
  "type": "multi_reward_breakdown",
  "batch_idx": 0,
  "total_reward": 0.85,
  "breakdown": { ... },
  "reasoning_steps_count": 4
}
```

---

### Scenario 4: End-to-End GRPO Training Test

**Test**: Run actual GRPO training and verify all metrics

#### Step 1: Prepare Test Dataset

```bash
# Create simple reasoning dataset
cat > /tmp/test_reasoning_dataset.jsonl << 'EOF'
{"prompt": "What is 2 + 2?", "reasoning": ["Let me add 2 and 2", "2 + 2 = 4"], "answer": "4", "ground_truth": "4"}
{"prompt": "What is 5 * 3?", "reasoning": ["Let me multiply 5 by 3", "5 * 3 = 15"], "answer": "15", "ground_truth": "15"}
{"prompt": "What is 10 / 2?", "reasoning": ["Let me divide 10 by 2", "10 / 2 = 5"], "answer": "5", "ground_truth": "5"}
EOF

# Upload to backend
docker-compose cp /tmp/test_reasoning_dataset.jsonl backend:/tmp/

# Upload via API (or use UI)
curl -X POST http://localhost:8000/api/v1/finetuning/datasets \
  -F "file=@/tmp/test_reasoning_dataset.jsonl" \
  -F "name=Test Reasoning Dataset" \
  -F "format=reasoning_cot"
```

#### Step 2: Create and Submit GRPO Job

```bash
# Create job via API
curl -X POST http://localhost:8000/api/v1/finetuning/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "Test GRPO Reasoning",
    "training_method": "rlhf_grpo",
    "dataset_id": "<dataset_id_from_upload>",
    "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
    "config": {
      "num_epochs": 1,
      "group_size": 2,
      "learning_rate": 1e-5,
      "max_length": 512
    }
  }'

# Get job ID from response
JOB_ID="<job_id_from_response>"

# Submit job
curl -X POST http://localhost:8000/api/v1/finetuning/jobs/${JOB_ID}/submit
```

#### Step 3: Monitor All Visualization Destinations

**Terminal 1: Backend Logs**
```bash
docker-compose logs -f backend | grep -E "Metrics emitter|Total Reward|Batch"
```

**Expected Output**:
```
INFO:     ✅ Metrics emitter initialized for job grpo_20251220_143000
INFO:     📊 Total Reward: 0.850
INFO:     Batch 0: Avg Reward=0.830, Advantages=[0.05, -0.03]
```

**Terminal 2: Prometheus Metrics**
```bash
watch -n 2 'curl -s "http://localhost:9090/api/v1/query?query=reward_total_score" | jq ".data.result[0].value[1]"'
```

**Expected**: Values updating every 2 seconds

**Browser 1: TensorBoard**
```
Open: http://localhost:6006
Navigate: Scalars → Rewards/Total/Response_0
```

**Expected**: Line chart updating in real-time

**Browser 2: Grafana**
```
Open: http://localhost:3000
Navigate: Dashboards → Reasoning Model - Multi-Reward Training
```

**Expected**: All 8 panels updating with live data

**Browser 3: Frontend React Component**
```
Open: http://localhost:3001/finetuning
Click: "Monitor" tab for the running job
```

**Expected**: RewardBreakdownChart component showing:
- Current total reward
- Bar chart with reward breakdown
- Line chart with reward trends
- Stacked area chart
- Reasoning quality metrics
- Reward weights display

#### Step 4: Verify Data Consistency

```bash
# Compare values across destinations

# 1. Prometheus
PROM_VALUE=$(curl -s "http://localhost:9090/api/v1/query?query=reward_total_score" | jq -r '.data.result[0].value[1]')

# 2. Backend logs
BACKEND_VALUE=$(docker-compose logs backend | grep "Total Reward" | tail -1 | grep -oP '[\d\.]+')

# 3. TensorBoard (manual check via UI)

echo "Prometheus: $PROM_VALUE"
echo "Backend Log: $BACKEND_VALUE"

# Values should match (within rounding)
```

---

## 🎨 Frontend Integration

### Adding RewardBreakdownChart to Finetuning Page

**File**: `frontend/src/pages/finetuning.tsx` (or wherever monitoring is shown)

```typescript
import RewardBreakdownChart from '@/components/finetuning/RewardBreakdownChart';

// In the job monitoring section:
{selectedJob && selectedJob.training_method === 'rlhf_grpo' && (
  <div className="mt-6">
    <h3 className="text-lg font-semibold mb-4">Multi-Reward Analysis</h3>
    <RewardBreakdownChart jobId={selectedJob.id} />
  </div>
)}
```

### Alternative: Add as Tab in MonitoringDashboard

**File**: `frontend/src/components/finetuning/MonitoringDashboard.tsx`

```typescript
import RewardBreakdownChart from './RewardBreakdownChart';

// Add state for tab selection
const [activeTab, setActiveTab] = useState<'overview' | 'rewards'>('overview');

// Add tab buttons
<div className="flex gap-2 mb-4">
  <button
    onClick={() => setActiveTab('overview')}
    className={`px-4 py-2 rounded ${activeTab === 'overview' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
  >
    Overview
  </button>
  <button
    onClick={() => setActiveTab('rewards')}
    className={`px-4 py-2 rounded ${activeTab === 'rewards' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
  >
    Reward Analysis
  </button>
</div>

// Render component
{activeTab === 'rewards' && (
  <RewardBreakdownChart jobId={jobId} />
)}
```

---

## 🐛 Troubleshooting

### Issue 1: Metrics Not Appearing in Prometheus

**Symptoms**: `curl http://localhost:8000/metrics` doesn't show `reward_*` metrics

**Solution**:
```bash
# 1. Verify metrics module imported in main.py
docker-compose exec backend grep "finetuning_metrics" /app/app/main.py

# 2. Restart backend
docker-compose restart backend

# 3. Check for import errors
docker-compose logs backend | grep -i error
```

### Issue 2: TensorBoard Not Showing Scalars

**Symptoms**: TensorBoard UI empty or missing Rewards/* section

**Solution**:
```bash
# 1. Check log directory exists
docker-compose exec backend ls -la /workspace/output/logs/

# 2. Verify SummaryWriter created files
docker-compose exec backend find /workspace/output/logs/ -name "events.out.tfevents.*"

# 3. Restart TensorBoard
docker-compose restart tensorboard

# 4. Clear browser cache and reload
```

### Issue 3: WebSocket Connection Failed

**Symptoms**: Frontend shows "Disconnected" or console errors

**Solution**:
```bash
# 1. Check WebSocket route exists
curl http://localhost:8000/api/docs | grep -i websocket

# 2. Verify job ID is correct
echo "Job ID: ${JOB_ID}"

# 3. Check CORS settings in backend
docker-compose exec backend grep -i cors /app/app/main.py

# 4. Test WebSocket directly
wscat -c ws://localhost:8000/ws/jobs/${JOB_ID}/metrics
```

### Issue 4: Grafana Dashboard Not Loading

**Symptoms**: Dashboard import fails or panels show "No data"

**Solution**:
```bash
# 1. Verify Prometheus data source configured
# Grafana UI → Configuration → Data Sources → Prometheus
# URL should be: http://prometheus:9090

# 2. Test Prometheus query manually
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=reward_total_score'

# 3. Check dashboard JSON is valid
jq . observability/grafana/dashboards/reasoning-rewards-dashboard.json

# 4. Re-import dashboard with fresh ID
```

### Issue 5: Frontend Component Not Rendering

**Symptoms**: RewardBreakdownChart not visible or crashes

**Solution**:
```bash
# 1. Check browser console for errors
# F12 → Console

# 2. Verify Recharts installed
cd frontend
npm list recharts

# 3. Rebuild frontend
npm run build

# 4. Check WebSocket URL in component
# Should match backend port (8000)
```

---

## ✅ Success Criteria

### Backend Metrics ✅
- [ ] Prometheus /metrics endpoint shows 20 reward metrics
- [ ] TensorBoard shows Rewards/* and Reasoning/* scalars
- [ ] Backend logs show "Metrics emitter initialized"
- [ ] Backend logs show "Total Reward: X.XXX"

### Grafana Dashboard ✅
- [ ] Dashboard imports without errors
- [ ] All 8 panels visible
- [ ] Panels show data after GRPO training starts
- [ ] Total reward trend line chart updates
- [ ] Stacked area chart shows all 6 rewards

### Frontend Component ✅
- [ ] Component renders without errors
- [ ] WebSocket connects (green indicator)
- [ ] Current total reward displays
- [ ] Bar chart shows reward breakdown
- [ ] Line chart shows trends
- [ ] Reasoning quality metrics visible

### End-to-End ✅
- [ ] GRPO training emits metrics every batch
- [ ] Metrics visible in all 4 destinations simultaneously
- [ ] Values consistent across Prometheus/TensorBoard/WebSocket
- [ ] No errors in backend/frontend logs
- [ ] Real-time updates working (< 1 second latency)

---

## 📊 Expected Visualizations

### Grafana Dashboard Panels

**Panel 1: Total Reward Trend**
- Type: Line chart
- Shows: Single line of total reward over batches
- Color: Black (bold)

**Panel 2: Reward Breakdown (Stacked Area)**
- Type: Stacked area chart
- Shows: 6 colored areas representing each reward
- Colors: Green, Blue, Purple, Orange, Red, Yellow

**Panel 3: Reasoning Quality Metrics**
- Type: Dual-axis line chart
- Left Y: Steps count (optimal: 3-7)
- Right Y: Tokens/step (optimal: 15-50)

**Panel 4: Reward Weights**
- Type: Bar gauge
- Shows: 6 bars with weight values
- Colors: Gradient based on magnitude

**Panels 5-8: Current Stats**
- Type: Gauge/Stat
- Shows: Latest values for total reward, correctness, steps, tokens/step

### Frontend Component Sections

**Section 1: Connection Status**
- Shows: Green/red indicator + "Live Metrics" or "Disconnected"

**Section 2: Current Total Reward**
- Large number display (0.XXX)
- Gradient background (green to blue)

**Section 3: Current Breakdown Bar Chart**
- Bars for each reward (score and contribution)
- Blue bars for score, green bars for contribution

**Section 4: Reward Weights**
- Grid of 6 cards
- Each shows icon, name, and weight value

**Section 5: Reward Trends Line Chart**
- Multiple colored lines (one per reward + total)
- X-axis: Batch number
- Y-axis: Score (0-1)

**Section 6: Reward Contribution Stacked Area**
- Filled areas stacked on top of each other
- Shows proportional contribution over time

**Section 7: Reasoning Quality**
- Dual-axis line chart
- Purple line: steps count
- Orange line: tokens/step
- Info boxes showing optimal ranges

---

## 🚀 Quick Start Commands

```bash
# 1. Verify services
docker-compose ps

# 2. Check Prometheus metrics
curl http://localhost:8000/metrics | grep reward_

# 3. Import Grafana dashboard
# Manual: http://localhost:3000 → Dashboards → Import → Upload reasoning-rewards-dashboard.json

# 4. Run test GRPO job
# (Follow Scenario 4 above)

# 5. Monitor in multiple windows:

# Terminal 1: Backend logs
docker-compose logs -f backend | grep -E "Metrics|Reward"

# Terminal 2: Prometheus query
watch -n 2 'curl -s "http://localhost:9090/api/v1/query?query=reward_total_score"'

# Browser 1: TensorBoard
open http://localhost:6006

# Browser 2: Grafana
open http://localhost:3000

# Browser 3: Frontend
open http://localhost:3001/finetuning
```

---

## 📝 Next Steps After Testing

1. **If Testing Succeeds**:
   - ✅ Mark Phase 2 as 100% complete
   - Document any configuration changes needed
   - Create user guide for interpreting visualizations
   - Add to main documentation (CLAUDE.md, STATUS.md)

2. **If Issues Found**:
   - Debug using troubleshooting section above
   - File GitHub issues if infrastructure problems
   - Update code as needed
   - Re-test

3. **Production Deployment**:
   - Ensure Grafana dashboards provisioned automatically
   - Configure Prometheus retention (default: 15 days)
   - Set up TensorBoard persistence
   - Document WebSocket authentication if needed

---

## 🎓 Understanding the Metrics

### Reward Scores (0.0 - 1.0)
- **Correctness**: How accurate is the answer?
- **ReasoningClarity**: Is the logic clear and well-structured?
- **StepByStep**: Appropriate granularity (3-7 steps optimal)?
- **Efficiency**: Concise reasoning (15-50 tokens/step optimal)?
- **MathematicalNotation**: Proper use of formulas/units?
- **Coherence**: No contradictions in reasoning?

### Weights
- Multipliers applied to raw scores
- Higher weight = more importance
- Default: Correctness (2.0), Clarity (1.5), others (0.8-1.2)

### Contributions
- `contribution = score * weight`
- Total reward = sum of all contributions / sum of weights

### Reasoning Quality
- **Steps Count**: Number of reasoning steps (optimal: 3-7)
- **Tokens/Step**: Average tokens per step (optimal: 15-50)
- Too few steps = superficial reasoning
- Too many steps = verbose/inefficient

---

**End of Testing Guide - Ready for Validation!**
