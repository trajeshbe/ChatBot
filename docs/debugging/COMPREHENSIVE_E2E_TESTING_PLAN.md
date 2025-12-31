# Comprehensive End-to-End Testing Plan

**Date**: 2025-12-20
**Purpose**: Validate complete finetuning pipeline with UI, observability, and GRPO implementation
**Reference**: https://github.com/aburkov/theLMbook/blob/main/GRPO_From_Scratch_Multi_GPU_DataParallel_Qwen_2_5_1_5B_Instruct.ipynb

---

## 🎯 Testing Objectives

### 1. Functional Validation
- ✅ SFT training pipeline (Qwen 1.5B with custom dataset)
- ✅ GRPO reasoning training (multi-reward framework)
- ✅ Dataset upload and management
- ✅ Model lifecycle (train → checkpoint → merge → inference)

### 2. UI Feature Validation
- ✅ Dataset upload interface
- ✅ Job creation and configuration
- ✅ Real-time training monitoring
- ✅ Metrics visualization (charts, gauges, trends)
- ✅ Job management (pause, resume, cancel)
- ✅ Model deployment and testing

### 3. Observability Dashboard Validation
- ✅ Grafana dashboards (finetuning metrics + reasoning rewards)
- ✅ TensorBoard integration
- ✅ Prometheus metrics
- ✅ WebSocket real-time streaming
- ✅ Frontend React component (RewardBreakdownChart)

### 4. GRPO Implementation Validation
- ✅ Compare with reference implementation (theLMbook)
- ✅ Validate reward calculation
- ✅ Verify group-based advantage computation
- ✅ Test multi-GPU support (if available)
- ✅ Validate metrics emission

---

## 📋 Pre-Testing Checklist

### Services Status
```bash
# 1. Check all services running
docker-compose ps

# Expected services:
# ✅ backend (port 8000)
# ✅ frontend (port 3001)
# ✅ postgres (port 5432)
# ✅ minio (port 9000/9001)
# ✅ ollama (port 11434)
# ✅ prometheus (port 9090)
# ✅ grafana (port 3000)
# ✅ tensorboard (port 6006)
```

### Access URLs Verification
```bash
# Backend API
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Frontend
curl -I http://localhost:3001
# Expected: 200 OK

# Prometheus
curl http://localhost:9090/-/healthy
# Expected: Prometheus is Healthy.

# Grafana
curl -I http://localhost:3000
# Expected: 200 OK

# TensorBoard
curl -I http://localhost:6006
# Expected: 200 OK

# MinIO
curl http://localhost:9001
# Expected: MinIO Console
```

### Dataset Preparation
```bash
# 1. SFT Dataset (already created)
cat /tmp/company_qa_dataset.jsonl | wc -l
# Expected: 10 lines

# 2. GRPO Reasoning Dataset (already created)
cat /tmp/tomato_grading_reasoning.jsonl | wc -l
# Expected: 6 lines

# 3. Verify format
head -1 /tmp/company_qa_dataset.jsonl | jq '.'
head -1 /tmp/tomato_grading_reasoning.jsonl | jq '.'
```

---

## 🧪 Test Scenario 1: SFT Training (Company Knowledge)

### 1.1 Pre-Training Baseline Test

**Objective**: Verify base model doesn't know about Choles Food Technologies

**Test via Ollama API**:
```bash
curl -s http://localhost:11434/api/generate \
  -d '{
    "model": "qwen2.5:1.5b",
    "prompt": "What is the main product of Choles Food Technologies?",
    "stream": false
  }' | jq -r '.response'
```

**Expected Response**:
- "I don't have information about Choles Food Technologies"
- Generic/vague answer about food technology
- Hallucinated information

**✅ Success Criteria**: Model admits lack of knowledge or gives incorrect info

---

### 1.2 UI Test: Dataset Upload

**Steps**:
1. Open Frontend: http://localhost:3001
2. Navigate to **Finetuning** section
3. Click **Upload Dataset**
4. Select `/tmp/company_qa_dataset.jsonl`
5. Fill form:
   - Name: `Choles Company Q&A`
   - Description: `Custom dataset about Choles Food Technologies`
   - Format: `Chat (ChatML)`
6. Click **Upload**

**UI Validation**:
- ✅ Upload progress bar appears
- ✅ Success notification shown
- ✅ Dataset appears in datasets list
- ✅ Shows correct # of examples (10)
- ✅ Preview shows first few examples
- ✅ Download/delete buttons available

**Backend Validation**:
```bash
# Check MinIO
docker exec minio-container mc ls local/finetuning-datasets/

# Check database
docker exec postgres psql -U postgres -d ragchatbot \
  -c "SELECT name, num_examples, format FROM finetuning_datasets ORDER BY created_at DESC LIMIT 1;"
```

**✅ Success Criteria**: Dataset uploaded, stored in MinIO, DB record created

---

### 1.3 UI Test: SFT Job Creation

**Steps**:
1. Click **Create Fine-Tuning Job**
2. Fill configuration form:
   - **Job Name**: `Choles SFT - Company Knowledge`
   - **Base Model**: `Qwen/Qwen2.5-1.5B-Instruct`
   - **Dataset**: Select `Choles Company Q&A`
   - **Training Method**: `PEFT (LoRA)`
   - **Hyperparameters**:
     - Epochs: `3`
     - Learning Rate: `2e-4`
     - Batch Size: `2`
     - LoRA Rank: `8`
     - LoRA Alpha: `16`
3. Click **Create Job**
4. Click **Start Training**

**UI Validation**:
- ✅ Form validation works (required fields)
- ✅ Model selector shows HuggingFace models
- ✅ Dataset selector shows uploaded datasets
- ✅ Hyperparameter sliders/inputs work
- ✅ Preview shows estimated training time
- ✅ Job created successfully
- ✅ Job appears in jobs list with status "queued"

**✅ Success Criteria**: Job created and submitted to queue

---

### 1.4 UI Test: Training Monitoring

**Real-Time Monitoring**:

**Frontend UI**:
1. Navigate to **Jobs** tab
2. Click on `Choles SFT - Company Knowledge` job
3. Observe real-time updates:
   - ✅ Status changes: `queued` → `running` → `completed`
   - ✅ Progress bar updates (0% → 100%)
   - ✅ Current epoch displays (1/3, 2/3, 3/3)
   - ✅ Loss metrics chart updates
   - ✅ Training logs stream in console
   - ✅ GPU utilization (if available)
   - ✅ ETA countdown timer

**Grafana Dashboard**:
1. Open: http://localhost:3000
2. Navigate to **Fine-Tuning Training Metrics** dashboard
3. Verify panels updating:
   - ✅ Training Loss (decreasing trend)
   - ✅ Evaluation Loss (stable/decreasing)
   - ✅ Current Epoch (incrementing)
   - ✅ Progress Percentage (0-100%)
   - ✅ Job Status (training)

**TensorBoard**:
1. Open: http://localhost:6006
2. Navigate to **Scalars** tab
3. Verify:
   - ✅ `train/loss` chart (decreasing)
   - ✅ `eval/loss` chart
   - ✅ `train/learning_rate` chart
   - ✅ Charts auto-refresh

**Backend Logs**:
```bash
docker-compose logs -f backend | grep -E "SFT|Training|Epoch|Loss"
```

**Expected Log Output**:
```
INFO: Starting SFT training for job: <job_id>
INFO: Epoch 1/3 - Step 1/15 - Loss: 2.345
INFO: Epoch 1/3 - Step 5/15 - Loss: 1.987
...
INFO: Epoch 3/3 completed - Avg Loss: 0.456
INFO: Training completed successfully
INFO: Saving model to MinIO...
```

**✅ Success Criteria**: All monitoring interfaces show consistent, real-time data

---

### 1.5 Post-Training Model Test

**Wait for Training Completion**:
- Status: `completed`
- Progress: `100%`
- Output model available

**Test Finetuned Model**:

**Option 1: Via UI**:
1. Navigate to **Model Testing** section
2. Select finetuned model from dropdown
3. Enter prompt: `"What is the main product of Choles Food Technologies?"`
4. Click **Generate**

**Expected Response**:
```
Choles Food Technologies specializes in automated food quality assessment systems,
with their flagship product being the TomatoGrade AI system for tomato color and
ripeness grading.
```

**Option 2: Via API**:
```bash
# Get model ID/path
MODEL_ID="<job_id>"

# Test inference
curl -X POST http://localhost:8000/api/v1/inference \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "'$MODEL_ID'",
    "prompt": "What is the main product of Choles Food Technologies?",
    "max_tokens": 150
  }'
```

**Additional Test Questions**:
```bash
# Test 2
"Who is the Chief Product Technologist at Choles?"
# Expected: "Dr. Sarah Martinez"

# Test 3
"What are the RGB thresholds for Premium grade tomatoes?"
# Expected: "R>180, R/G ratio >1.3"

# Test 4
"What is the accuracy of Choles TomatoGrade AI?"
# Expected: "97.5% accuracy"
```

**✅ Success Criteria**:
- ✅ Model responds with accurate, specific information
- ✅ 4/4 test questions answered correctly
- ✅ No generic/hallucinated responses
- ✅ Clear improvement over base model

---

## 🧪 Test Scenario 2: GRPO Reasoning Training (Tomato Grading)

### 2.1 GRPO Implementation Validation

**Compare with Reference Implementation**:

**Reference**: https://github.com/aburkov/theLMbook/blob/main/GRPO_From_Scratch_Multi_GPU_DataParallel_Qwen_2_5_1_5B_Instruct.ipynb

**Key Components to Validate**:

#### A. Reward Calculation
**Reference Code** (theLMbook):
```python
def compute_reward(response, ground_truth):
    # Simple correctness reward
    return 1.0 if response.strip() == ground_truth.strip() else 0.0
```

**Our Implementation** (`backend/app/services/finetuning/trainers/rlhf_grpo_trainer.py:211-320`):
```python
def compute_reward(
    response, reward_model=None, prompt="", ground_truth=None,
    metadata=None, use_multi_reward=True, metrics_emitter=None,
    batch_idx=0, response_idx=0, step=None
) -> tuple:
    # Multi-reward framework with 6 reward functions
    # Returns (total_reward, breakdown, reasoning_steps)
```

**Validation**:
```bash
# Check our implementation
grep -A 50 "def compute_reward" backend/app/services/finetuning/trainers/rlhf_grpo_trainer.py

# Verify multi-reward calculator
cat backend/app/services/finetuning/rewards/calculator.py | grep -A 20 "class ReasoningRewardCalculator"
```

**✅ Differences (Enhancements)**:
- ✅ Multi-reward (6 functions) vs single correctness
- ✅ Reasoning step extraction
- ✅ Metrics emission
- ✅ Domain-specific rewards (math notation, coherence)

#### B. Group-Based Advantage Computation
**Reference Code** (theLMbook):
```python
def compute_group_advantages(responses, rewards):
    # Normalize within group
    mean_reward = np.mean(rewards)
    std_reward = np.std(rewards) + 1e-8
    advantages = (rewards - mean_reward) / std_reward
    return advantages
```

**Our Implementation** (`backend/app/services/finetuning/trainers/rlhf_grpo_trainer.py:~180`):
```python
def compute_group_advantages(responses: list, rewards: list) -> list:
    """Compute advantages using group statistics (GRPO core)"""
    # Same normalization logic
```

**Validation**:
```bash
grep -A 10 "def compute_group_advantages" backend/app/services/finetuning/trainers/rlhf_grpo_trainer.py
```

**✅ Success Criteria**: Implementation matches reference algorithm

#### C. Training Loop Structure
**Reference Structure** (theLMbook):
```python
for epoch in range(num_epochs):
    for batch in dataset:
        # 1. Generate K responses per prompt (group_size=K)
        responses = generate_responses(model, prompt, group_size)

        # 2. Compute rewards for each response
        rewards = [compute_reward(r, ground_truth) for r in responses]

        # 3. Compute group advantages
        advantages = compute_group_advantages(responses, rewards)

        # 4. Policy gradient update
        loss = compute_policy_loss(advantages)
        loss.backward()
        optimizer.step()
```

**Our Implementation** (`backend/app/services/finetuning/trainers/rlhf_grpo_trainer.py:~540-645`):
```python
for epoch in range(num_epochs):
    for batch_idx, batch in enumerate(dataset):
        # 1. Generate group_size responses
        responses = generate_responses(...)

        # 2. Compute multi-rewards with metrics
        reward_results = [
            compute_reward(..., metrics_emitter=...)
            for i, r in enumerate(responses)
        ]
        rewards = [r[0] for r in reward_results]

        # 3. Emit batch aggregates
        metrics_emitter.emit_batch_aggregates(...)

        # 4. Group advantages
        advantages = compute_group_advantages(responses, rewards)

        # 5. Policy gradient update
        # ... (same as reference)
```

**Validation**:
```bash
grep -A 100 "for epoch in range" backend/app/services/finetuning/trainers/rlhf_grpo_trainer.py | head -120
```

**✅ Success Criteria**: Training loop follows GRPO algorithm structure

---

### 2.2 UI Test: GRPO Dataset Upload

**Steps**:
1. Open Frontend: http://localhost:3001
2. Navigate to **Finetuning** → **Datasets**
3. Click **Upload Dataset**
4. Select `/tmp/tomato_grading_reasoning.jsonl`
5. Fill form:
   - Name: `Tomato Grading Reasoning`
   - Description: `Reasoning dataset for tomato color grading with step-by-step threshold analysis`
   - Format: `Reasoning (Chain-of-Thought)`
6. Click **Upload**

**UI Validation**:
- ✅ CoT format selector available
- ✅ Preview shows `prompt`, `reasoning`, `answer` fields
- ✅ Reasoning steps displayed as list
- ✅ Dataset statistics: 6 examples, avg reasoning steps: 4-6

**✅ Success Criteria**: Reasoning dataset uploaded with correct format

---

### 2.3 UI Test: GRPO Job Creation

**Steps**:
1. Click **Create Fine-Tuning Job**
2. Fill configuration:
   - **Job Name**: `Choles GRPO - Tomato Reasoning`
   - **Base Model**: Select finetuned SFT model from Scenario 1
   - **Dataset**: `Tomato Grading Reasoning`
   - **Training Method**: `RLHF-GRPO`
   - **Hyperparameters**:
     - Epochs: `2`
     - Group Size: `2`
     - Learning Rate: `1e-5`
     - Batch Size: `1`
   - **Reward Configuration**:
     - Enable Multi-Reward: ✅
     - Correctness Weight: `2.0`
     - Reasoning Clarity Weight: `1.5`
     - Step-by-Step Weight: `1.0`
     - Efficiency Weight: `0.8`
3. Click **Create Job**
4. Click **Start Training**

**UI Validation**:
- ✅ GRPO-specific options appear
- ✅ Group size selector (2-8)
- ✅ Reward weights sliders
- ✅ Multi-reward toggle
- ✅ Preview shows expected metrics

**✅ Success Criteria**: GRPO job created with multi-reward config

---

### 2.4 Observability Dashboard Validation (CRITICAL)

**This validates Phase 2 implementation!**

#### A. Grafana - Reasoning Rewards Dashboard

**Steps**:
1. Open http://localhost:3000
2. Navigate to **Dashboards** → **Reasoning Model - Multi-Reward Training**

**Panels to Validate** (8 panels):

**Panel 1: Total Reward Trend**
- ✅ Line chart shows total reward over batches
- ✅ Y-axis: 0.0-1.0 scale
- ✅ X-axis: Batch number
- ✅ Trend: Generally increasing (0.5 → 0.8+)
- ✅ Auto-refreshes every 5 seconds

**Panel 2: Reward Breakdown (Stacked Area)**
- ✅ 6 colored areas (one per reward function)
- ✅ Colors: Green (Correctness), Blue (Clarity), Purple (Step), Orange (Efficiency), Red (Math), Yellow (Coherence)
- ✅ Areas stack to show proportional contribution
- ✅ Dominant rewards visible (Correctness should be largest)

**Panel 3: Reasoning Quality Metrics**
- ✅ Dual-axis line chart
- ✅ Left Y: Steps count (purple line, target: 4-6)
- ✅ Right Y: Tokens/step (orange line, target: 15-50)
- ✅ Both converging to optimal ranges

**Panel 4: Reward Weights Configuration**
- ✅ Bar gauge showing 6 weights
- ✅ Correctness: 2.0 (highest)
- ✅ Clarity: 1.5
- ✅ Others: 0.8-1.2
- ✅ Color-coded by magnitude

**Panels 5-8: Current Stats**
- ✅ Panel 5: Current Total Reward (gauge, 0-1)
- ✅ Panel 6: Current Correctness (gauge, 0-1)
- ✅ Panel 7: Current Avg Steps (stat, target 3-7)
- ✅ Panel 8: Current Avg Tokens/Step (stat, target 15-50)

**Time Range Validation**:
- ✅ Last 6 hours default
- ✅ Auto-refresh enabled
- ✅ Data retention working

**PromQL Queries Test**:
```bash
# Test queries manually
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=reward_total_score'

curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=reward_correctness_score'

curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=reasoning_avg_steps_count'
```

**✅ Success Criteria**: All 8 panels display live data, queries return metrics

#### B. TensorBoard - Rewards Scalars

**Steps**:
1. Open http://localhost:6006
2. Navigate to **Scalars** tab

**Expected Scalars**:
```
Scalars/
├── Rewards/
│   ├── Total/
│   │   ├── Response_0
│   │   └── Response_1
│   ├── Correctness/Response_0
│   ├── ReasoningClarity/Response_0
│   ├── StepByStep/Response_0
│   ├── Efficiency/Response_0
│   ├── MathematicalNotation/Response_0
│   ├── Coherence/Response_0
│   ├── Correctness_Contribution/Response_0
│   └── ... (contributions for each)
└── Reasoning/
    ├── StepCount/Response_0
    └── AvgTokensPerStep/Response_0
```

**Validation**:
- ✅ All reward scalars present
- ✅ Total reward trend upward
- ✅ Correctness improving (0.6 → 0.9+)
- ✅ Step count converging to 4-6
- ✅ Charts smooth and continuous

**✅ Success Criteria**: TensorBoard shows all reward metrics

#### C. Frontend React Component (RewardBreakdownChart)

**Steps**:
1. Frontend: http://localhost:3001
2. Navigate to job monitoring page
3. Click **Reward Analysis** tab

**Component Sections to Validate** (7 sections):

**Section 1: Connection Status**
- ✅ Green indicator showing "🔴 Live Metrics"
- ✅ WebSocket connected message
- ✅ No error messages

**Section 2: Current Total Reward**
- ✅ Large number display (e.g., "0.850")
- ✅ Gradient background (green to blue)
- ✅ Count: "6 active reward functions"
- ✅ Updates in real-time (< 1 second latency)

**Section 3: Current Breakdown Bar Chart**
- ✅ 6 bars (one per reward)
- ✅ Each bar shows score + contribution
- ✅ Blue bars for score, green for contribution
- ✅ X-axis labels readable (angled 45°)
- ✅ Y-axis: 0-1 scale
- ✅ Tooltip on hover

**Section 4: Reward Weights Display**
- ✅ Grid layout (2-3 columns)
- ✅ 6 cards with icons
- ✅ Each shows name + weight value
- ✅ Color-coded by reward type
- ✅ Format: "2.0x" notation

**Section 5: Reward Trends Line Chart**
- ✅ 7 lines (total + 6 rewards)
- ✅ Black line for total (bold)
- ✅ Colored lines for each reward
- ✅ Legend with last/mean values
- ✅ X-axis: Batch number
- ✅ Y-axis: Score (0-1)
- ✅ Smooth interpolation
- ✅ Keeps last 100 points

**Section 6: Contribution Stacked Area**
- ✅ 6 stacked areas
- ✅ Colors match line chart
- ✅ Shows proportional contribution
- ✅ Opacity 0.6 for visibility
- ✅ Tooltip shows all values

**Section 7: Reasoning Quality Metrics**
- ✅ Dual-axis line chart
- ✅ Purple line: steps count (left Y)
- ✅ Orange line: tokens/step (right Y)
- ✅ Legend clear
- ✅ Info boxes showing optimal ranges:
  - "Optimal Steps: 3-7 steps"
  - "Optimal Tokens/Step: 15-50 tokens"

**WebSocket Message Validation**:

Open browser console (F12) and verify messages:
```javascript
{
  type: "multi_reward_breakdown",
  batch_idx: 5,
  total_reward: 0.83,
  breakdown: {
    Correctness: {score: 0.88, weight: 2.0, contribution: 1.76, applicable: true},
    ReasoningClarity: {score: 0.79, weight: 1.5, contribution: 1.19, applicable: true},
    // ... others
  },
  reasoning_steps_count: 5
}
```

**✅ Success Criteria**: All 7 sections render correctly, WebSocket streams live data

#### D. Prometheus Metrics Direct Validation

**Test Metrics Endpoint**:
```bash
curl http://localhost:8000/metrics | grep reward_

# Expected metrics:
# reward_total_score{batch="5",job_id="...",job_name="...",response_idx="0"} 0.83
# reward_correctness_score{...} 0.88
# reward_batch_avg_total{batch="5",...} 0.81
# reward_weight_correctness{...} 2.0
# reasoning_avg_steps_count{...} 4.8
# reasoning_avg_tokens_per_step{...} 23.5
```

**Query Prometheus Directly**:
```bash
# Total reward
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=avg(reward_total_score) by (job_id)'

# Reasoning steps trend
curl -G http://localhost:9090/api/v1/query_range \
  --data-urlencode 'query=reasoning_avg_steps_count' \
  --data-urlencode 'start=2025-12-20T00:00:00Z' \
  --data-urlencode 'end=2025-12-20T23:59:59Z' \
  --data-urlencode 'step=15s'
```

**✅ Success Criteria**: All 20 reward metrics available in Prometheus

---

### 2.5 Training Completion and Model Test

**Wait for Training Completion**:
- Monitor all 4 dashboards simultaneously
- Verify consistent metrics across all

**Final Metrics Validation**:

**Expected Final Values**:
| Metric | Target | Acceptable Range |
|--------|--------|------------------|
| Total Reward | >0.75 | 0.75-0.95 |
| Correctness | >0.85 | 0.85-1.00 |
| Reasoning Clarity | >0.80 | 0.75-0.95 |
| Step Count | 4-6 | 3-7 |
| Tokens/Step | 15-50 | 10-75 |

**Test Reasoning Model**:

**Test Case 1: Premium Grade**
```
Prompt: "A tomato has RGB values R=195, G=140, B=120.
The color is uniformly distributed. Should this be accepted for Premium grade?"

Expected Response:
"Let me analyze the tomato step by step:

Step 1: Check red channel value - R=195 exceeds Premium threshold of R>180 ✓

Step 2: Calculate R/G ratio - 195/140 = 1.39, which exceeds Premium requirement of R/G>1.3 ✓

Step 3: Verify color uniformity - Uniformly distributed across surface ✓

Step 4: Check for defects - None mentioned ✓

Conclusion: All Premium grade criteria satisfied

Answer: Accept for Premium grade"
```

**Test Case 2: Reject Grade**
```
Prompt: "A tomato shows R=155, G=145, B=130 with 15% green patches. What grade?"

Expected Response:
"Let me evaluate systematically:

Step 1: Red channel - R=155, above Standard (R>140) but below Premium (R>180)

Step 2: R/G ratio - 155/145 = 1.07, below both Premium (>1.3) and Standard (>1.1)

Step 3: Color uniformity - 15% green patches indicates non-uniform color

Step 4: Determine grade - R/G ratio fails Standard threshold

Conclusion: Reject - R/G ratio (1.07) below Standard minimum (1.1)"
```

**✅ Success Criteria**:
- ✅ Model provides step-by-step reasoning
- ✅ Calculates R/G ratio correctly
- ✅ Evaluates against thresholds
- ✅ Reaches correct conclusion
- ✅ 4-6 reasoning steps
- ✅ 2/2 test cases correct

---

## 📊 GRPO Validation Checklist

### Algorithm Compliance (vs theLMbook reference)

| Component | Reference | Our Implementation | Status |
|-----------|-----------|-------------------|--------|
| **Group-based sampling** | ✅ K responses per prompt | ✅ `group_size` parameter | ⏳ Validate |
| **Reward calculation** | ✅ Correctness only | ✅ Multi-reward (6 functions) | ⏳ Validate |
| **Advantage computation** | ✅ Group normalization | ✅ Same algorithm | ⏳ Validate |
| **Policy gradient** | ✅ PPO-style update | ✅ Same approach | ⏳ Validate |
| **Multi-GPU support** | ✅ DataParallel | ⏳ Pending | ⏳ Test |

### Metrics Validation

| Metric | Expected Behavior | Status |
|--------|------------------|--------|
| **Total Reward** | Increases 0.5→0.8+ | ⏳ Monitor |
| **Correctness** | Improves 0.6→0.9+ | ⏳ Monitor |
| **Reasoning Clarity** | Improves 0.5→0.8+ | ⏳ Monitor |
| **Step Count** | Converges to 4-6 | ⏳ Monitor |
| **Loss** | Decreases | ⏳ Monitor |

---

## ✅ Overall Success Criteria

### Functional
- ✅ SFT: Base model → Finetuned model shows clear improvement
- ✅ GRPO: Model learns step-by-step reasoning
- ✅ Datasets upload and process correctly
- ✅ Models train without errors
- ✅ Checkpoints save to MinIO
- ✅ Models available for inference

### UI/UX
- ✅ All UI features work (upload, create, monitor, test)
- ✅ Real-time updates < 1 second latency
- ✅ No broken links or error messages
- ✅ Forms validate inputs correctly
- ✅ Charts render smoothly
- ✅ Navigation intuitive

### Observability
- ✅ 4 visualization destinations working:
  - Grafana: 8 panels with live data
  - TensorBoard: All reward scalars present
  - Frontend: 7 component sections functional
  - Prometheus: 20 metrics available
- ✅ Metrics consistent across all destinations
- ✅ WebSocket streaming < 100ms latency
- ✅ No data loss or gaps

### GRPO Implementation
- ✅ Matches reference algorithm structure
- ✅ Multi-reward framework functional
- ✅ Group advantages calculated correctly
- ✅ Metrics emission integrated
- ✅ Final model shows reasoning capability

---

## 🎯 Test Execution Order

### Phase 1: Pre-Flight (5 mins)
1. ✅ Check all services running
2. ✅ Verify access URLs
3. ✅ Prepare datasets

### Phase 2: SFT Scenario (15-20 mins)
1. ✅ Test base model (baseline)
2. ✅ Upload SFT dataset
3. ✅ Create SFT job
4. ✅ Monitor training (all dashboards)
5. ✅ Test finetuned model

### Phase 3: GRPO Scenario (20-25 mins)
1. ✅ Upload GRPO dataset
2. ✅ Create GRPO job
3. ✅ Monitor training (all 4 dashboards simultaneously)
4. ✅ Validate GRPO implementation
5. ✅ Test reasoning model

### Phase 4: Validation (10 mins)
1. ✅ Cross-check metrics across destinations
2. ✅ Verify data consistency
3. ✅ Test edge cases
4. ✅ Document results

**Total Estimated Time**: ~50-60 minutes

---

## 📝 Test Results Template

```markdown
# Test Execution Results

## Date: 2025-12-20
## Tester: [Name]

### Scenario 1: SFT Training
- [ ] Base model test: PASS/FAIL
- [ ] Dataset upload: PASS/FAIL
- [ ] Job creation: PASS/FAIL
- [ ] Training completion: PASS/FAIL
- [ ] Model improvement: PASS/FAIL
- Notes: _______________

### Scenario 2: GRPO Training
- [ ] Dataset upload: PASS/FAIL
- [ ] Job creation: PASS/FAIL
- [ ] Grafana dashboard: PASS/FAIL (8/8 panels)
- [ ] TensorBoard: PASS/FAIL
- [ ] Frontend component: PASS/FAIL (7/7 sections)
- [ ] Prometheus metrics: PASS/FAIL (20/20 metrics)
- [ ] Reasoning quality: PASS/FAIL
- Notes: _______________

### GRPO Validation
- [ ] Algorithm matches reference: PASS/FAIL
- [ ] Metrics emission: PASS/FAIL
- [ ] Final model reasoning: PASS/FAIL
- Notes: _______________

### Issues Found
1. _______________
2. _______________

### Overall Result
- [ ] ALL TESTS PASSED
- [ ] PARTIAL PASS (__ / __ tests)
- [ ] FAILED

### Screenshots
- Grafana dashboard: [attach]
- Frontend component: [attach]
- TensorBoard: [attach]
```

---

**End of Comprehensive Testing Plan**
