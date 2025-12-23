# End-to-End Finetuning Demonstration

**Date**: 2025-12-20
**Purpose**: Demonstrate complete finetuning pipeline with two real-world scenarios

---

## 🎯 Demo Scenarios

### Scenario 1: Supervised Fine-Tuning (SFT)
**Objective**: Teach Qwen 1.5B about a specific company (Choles Food Technologies) that it doesn't know about

**Before Finetuning**: Model will give generic/incorrect answers
**After Finetuning**: Model will provide accurate, specific information

**Dataset**: 10 Q&A pairs about Choles Food Technologies
- Company information
- Products (TomatoGrade AI system)
- Technology details
- Quality grading thresholds

### Scenario 2: GRPO Reasoning Model
**Objective**: Train model to perform step-by-step reasoning for tomato color grading decisions

**Use Case**: Product technologist needs to set accept/reject thresholds based on tomato coloration
**Before Training**: Model may give direct answers without reasoning
**After Training**: Model provides detailed step-by-step analysis with proper reasoning

**Dataset**: 6 reasoning examples with:
- RGB color values
- Step-by-step analysis
- Threshold evaluation
- Final classification (Premium/Standard/Reject)

---

## 📁 MinIO Organizational Structure

```
minio://
└── finetuning-datasets/
    └── demos/
        └── choles-food-tech/
            ├── sft/
            │   └── company_qa_dataset.jsonl (10 examples)
            └── grpo/
                └── tomato_grading_reasoning.jsonl (6 examples)

finetuning-outputs/
└── demos/
    └── choles-food-tech/
        ├── sft_job_<timestamp>/
        │   ├── checkpoint-*/
        │   └── merged_model/
        └── grpo_job_<timestamp>/
            ├── checkpoint-*/
            └── merged_model/
```

---

## 📊 Test Plan

### Phase 1: SFT Demonstration

#### 1.1 Pre-Finetuning Test ❌ (Expected to Fail)

**Test Question**: "What is the main product of Choles Food Technologies?"

**Expected Base Model Response**:
- "I don't have information about Choles Food Technologies"
- Generic answer about food technology companies
- Hallucinated/incorrect information

#### 1.2 Upload SFT Dataset

**File**: `/tmp/company_qa_dataset.jsonl`
**Format**: ChatML (messages format)
**Size**: 10 examples
**Path**: `demos/choles-food-tech/sft/`

#### 1.3 Run SFT Finetuning

**Configuration**:
- Model: `Qwen/Qwen2.5-1.5B-Instruct`
- Method: `peft` (LoRA)
- Epochs: 3
- Learning Rate: 2e-4
- LoRA Rank: 8
- LoRA Alpha: 16

**Expected Duration**: ~5-10 minutes

#### 1.4 Post-Finetuning Test ✅ (Expected to Pass)

**Test Question**: "What is the main product of Choles Food Technologies?"

**Expected Finetuned Model Response**:
"Choles Food Technologies specializes in automated food quality assessment systems, with their flagship product being the TomatoGrade AI system for tomato color and ripeness grading."

**Additional Test Questions**:
1. "Who is the Chief Product Technologist at Choles?"
2. "What are the RGB thresholds for Premium grade tomatoes?"
3. "What is the accuracy of Choles TomatoGrade AI?"

---

### Phase 2: GRPO Reasoning Demonstration

#### 2.1 Pre-Training Test (Base Reasoning)

**Test Problem**: "A tomato has RGB values of R=195, G=140, B=120. The color is uniformly distributed. Should this be accepted for Premium grade?"

**Expected Base Model Response**:
- Direct answer without reasoning
- Missing threshold analysis
- No step-by-step evaluation

#### 2.2 Upload GRPO Dataset

**File**: `/tmp/tomato_grading_reasoning.jsonl`
**Format**: Reasoning CoT (Chain-of-Thought)
**Size**: 6 examples with detailed reasoning
**Path**: `demos/choles-food-tech/grpo/`

**Example Entry Structure**:
```json
{
  "prompt": "RGB question...",
  "reasoning": [
    "Step 1: Check red channel...",
    "Step 2: Calculate R/G ratio...",
    "Step 3: Verify uniformity...",
    "Conclusion: ..."
  ],
  "answer": "Accept/Reject",
  "ground_truth": "Accept/Reject"
}
```

#### 2.3 Run GRPO Training

**Configuration**:
- Model: Fine-tuned Qwen 1.5B from Phase 1
- Method: `rlhf_grpo`
- Epochs: 2
- Group Size: 2
- Learning Rate: 1e-5
- Reward Functions: Multi-reward (6 functions)

**Expected Duration**: ~10-15 minutes

**Metrics to Monitor**:
- Total reward score (target: >0.75)
- Correctness reward (target: >0.85)
- Reasoning clarity (target: >0.80)
- Step count (optimal: 4-6 steps)

#### 2.4 Post-Training Test ✅ (Expected Reasoning)

**Test Problem**: "A tomato shows R=155, G=145, B=130 with slight green patches (15% surface). What grade?"

**Expected GRPO Model Response**:
```
Let me evaluate this tomato systematically:

Step 1: Check red channel - R=155, which is above Standard threshold (R>140) but below Premium (R>180)

Step 2: Calculate R/G ratio - 155/145 = 1.07, which is below both Premium (>1.3) and Standard (>1.1) thresholds

Step 3: Assess color uniformity - Green patches covering 15% indicates non-uniform color

Step 4: Determine grade - R value suggests Standard range, but R/G ratio fails Standard requirements

Conclusion: Reject - R/G ratio (1.07) below Standard threshold (1.1)
```

---

## 🧪 Detailed Testing Steps

### Step 1: Test Base Model (Before Any Finetuning)

```bash
# Test via curl
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "What is the main product of Choles Food Technologies?",
    "model": "qwen2.5:1.5b",
    "conversation_only": true
  }'

# Expected: Generic/incorrect answer
```

### Step 2: Upload SFT Dataset

```bash
# Upload via API
curl -X POST http://localhost:8000/api/v1/finetuning/datasets/upload \
  -F "file=@/tmp/company_qa_dataset.jsonl" \
  -F "name=Choles Company Q&A" \
  -F "description=Custom dataset about Choles Food Technologies" \
  -F "format=chat"

# Get dataset ID from response
DATASET_ID_SFT="<dataset_id>"
```

### Step 3: Create and Run SFT Job

```bash
# Create job
curl -X POST http://localhost:8000/api/v1/finetuning/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Choles SFT - Company Knowledge",
    "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
    "dataset_id": "'$DATASET_ID_SFT'",
    "training_method": "peft",
    "hyperparameters": {
      "num_train_epochs": 3,
      "learning_rate": 2e-4,
      "per_device_train_batch_size": 2,
      "gradient_accumulation_steps": 4,
      "lora_r": 8,
      "lora_alpha": 16,
      "lora_dropout": 0.05
    }
  }'

# Get job ID
JOB_ID_SFT="<job_id>"

# Submit job
curl -X POST http://localhost:8000/api/v1/finetuning/jobs/${JOB_ID_SFT}/submit

# Monitor progress
watch -n 5 'curl -s http://localhost:8000/api/v1/finetuning/jobs/'$JOB_ID_SFT' | jq ".status, .progress"'
```

### Step 4: Test Finetuned Model

```bash
# Wait for job completion (status: "completed")

# Test with same question
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "What is the main product of Choles Food Technologies?",
    "model": "'$JOB_ID_SFT'",  # Use finetuned model
    "conversation_only": true
  }'

# Expected: Accurate answer about TomatoGrade AI
```

### Step 5: Upload GRPO Reasoning Dataset

```bash
# Upload reasoning dataset
curl -X POST http://localhost:8000/api/v1/finetuning/datasets/upload \
  -F "file=@/tmp/tomato_grading_reasoning.jsonl" \
  -F "name=Tomato Grading Reasoning" \
  -F "description=Reasoning dataset for tomato color grading with thresholds" \
  -F "format=reasoning_cot"

# Get dataset ID
DATASET_ID_GRPO="<dataset_id>"
```

### Step 6: Create and Run GRPO Job

```bash
# Create GRPO job (using SFT model as base)
curl -X POST http://localhost:8000/api/v1/finetuning/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Choles GRPO - Tomato Reasoning",
    "base_model": "'$JOB_ID_SFT'",  # Use SFT-finetuned model
    "dataset_id": "'$DATASET_ID_GRPO'",
    "training_method": "rlhf_grpo",
    "hyperparameters": {
      "num_train_epochs": 2,
      "group_size": 2,
      "learning_rate": 1e-5,
      "per_device_train_batch_size": 1
    }
  }'

# Get job ID
JOB_ID_GRPO="<job_id>"

# Submit job
curl -X POST http://localhost:8000/api/v1/finetuning/jobs/${JOB_ID_GRPO}/submit

# Monitor with metrics
# Terminal 1: Backend logs
docker-compose logs -f backend | grep -E "Total Reward|Batch"

# Terminal 2: Prometheus metrics
watch -n 2 'curl -s "http://localhost:9090/api/v1/query?query=reward_total_score"'

# Browser: TensorBoard
open http://localhost:6006

# Browser: Grafana
open http://localhost:3000
```

### Step 7: Test GRPO Reasoning Model

```bash
# Test reasoning capability
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "A tomato has RGB values R=155, G=145, B=130 with 15% green patches. What grade should it receive?",
    "model": "'$JOB_ID_GRPO'",
    "conversation_only": true
  }'

# Expected: Step-by-step reasoning with final classification
```

---

## ✅ Success Criteria

### SFT Success Criteria

| Metric | Pre-Finetuning | Post-Finetuning | Status |
|--------|----------------|-----------------|--------|
| **Accuracy on Company Info** | ~0% (doesn't know) | ~100% | ⏳ Pending |
| **Specific Product Names** | ❌ Generic | ✅ TomatoGrade AI | ⏳ Pending |
| **Technical Details** | ❌ Vague | ✅ RGB thresholds | ⏳ Pending |
| **People Names** | ❌ Unknown | ✅ Dr. Sarah Martinez | ⏳ Pending |

### GRPO Success Criteria

| Metric | Pre-Training | Post-Training | Status |
|--------|--------------|---------------|--------|
| **Reasoning Steps** | 0-1 | 4-6 | ⏳ Pending |
| **Threshold Evaluation** | ❌ Missing | ✅ Present | ⏳ Pending |
| **R/G Ratio Calculation** | ❌ Missing | ✅ Calculated | ⏳ Pending |
| **Total Reward Score** | N/A | >0.75 | ⏳ Pending |
| **Correctness Reward** | N/A | >0.85 | ⏳ Pending |

---

## 📊 Expected Metrics (GRPO Training)

### Reward Trends

**Batch 0** (Initial):
- Total Reward: ~0.50 (baseline)
- Correctness: ~0.60
- Reasoning Clarity: ~0.45
- Step Count: ~2-3 (too few)

**Batch 5** (Mid-training):
- Total Reward: ~0.68
- Correctness: ~0.75
- Reasoning Clarity: ~0.65
- Step Count: ~4 (improving)

**Batch 10** (End):
- Total Reward: ~0.82
- Correctness: ~0.90
- Reasoning Clarity: ~0.85
- Step Count: ~5 (optimal)

### TensorBoard Visualizations

**Expected Charts**:
1. `Rewards/Total/Response_0` - Upward trend
2. `Rewards/Correctness/Response_0` - Improving accuracy
3. `Rewards/ReasoningClarity/Response_0` - Better structure
4. `Reasoning/StepCount/Response_0` - Converging to 4-6

---

## 🎯 Demo Script

### Quick Demo (30 minutes)

```bash
# 1. Test base model
./demo_scripts/test_base_model.sh

# 2. Upload datasets
./demo_scripts/upload_datasets.sh

# 3. Run SFT (5-10 min)
./demo_scripts/run_sft_job.sh

# 4. Test SFT model
./demo_scripts/test_sft_model.sh

# 5. Run GRPO (10-15 min)
./demo_scripts/run_grpo_job.sh

# 6. Monitor dashboards
# - Grafana: http://localhost:3000
# - TensorBoard: http://localhost:6006

# 7. Test GRPO model
./demo_scripts/test_grpo_model.sh
```

---

## 📁 Files Reference

**Datasets**:
- `/tmp/company_qa_dataset.jsonl` - SFT Q&A (10 examples)
- `/tmp/tomato_grading_reasoning.jsonl` - GRPO reasoning (6 examples)

**MinIO Paths**:
- `finetuning-datasets/demos/choles-food-tech/sft/`
- `finetuning-datasets/demos/choles-food-tech/grpo/`

**Output Models**:
- SFT Model: `finetuning-outputs/demos/choles-food-tech/sft_job_<id>/`
- GRPO Model: `finetuning-outputs/demos/choles-food-tech/grpo_job_<id>/`

---

## 🔍 Monitoring Dashboards

### Grafana Dashboard
**URL**: http://localhost:3000
**Dashboard**: Reasoning Model - Multi-Reward Training
**Panels to Watch**:
- Total Reward Trend (should increase)
- Reward Breakdown (stacked area)
- Reasoning Quality (steps count converging to 4-6)

### TensorBoard
**URL**: http://localhost:6006
**Scalars to Monitor**:
- `Rewards/Total/Response_0`
- `Rewards/Correctness/Response_0`
- `Reasoning/StepCount/Response_0`

### Prometheus
**URL**: http://localhost:9090
**Key Queries**:
```promql
reward_total_score{job_id="grpo_job_id"}
reward_correctness_score{job_id="grpo_job_id"}
reasoning_avg_steps_count{job_id="grpo_job_id"}
```

---

## 🎓 Learning Outcomes

### SFT Demonstration Shows:
✅ How to teach model specific factual knowledge
✅ Domain adaptation to company/product information
✅ Small dataset (10 examples) can be effective
✅ Before/after comparison validates finetuning

### GRPO Demonstration Shows:
✅ Step-by-step reasoning development
✅ Multi-reward framework in action
✅ Real-time metrics visualization
✅ Threshold-based decision making
✅ Domain-specific quality assessment

---

**Status**: ⏳ Ready to Execute
**Estimated Total Time**: ~30-40 minutes
**Prerequisites**: Docker services running, datasets created
