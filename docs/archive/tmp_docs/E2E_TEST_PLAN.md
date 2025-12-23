# End-to-End Deployment Test Plan

## Objective
Deploy `choles-qa-real-training49_model` to Ollama and verify it responds correctly to Choles Food Technologies questions.

## Test Environment

**Model**: choles-qa-real-training49_model
**Model ID**: 242b3688-f220-47a4-b146-64e33d14a244
**Job ID**: dfcb97c3-8167-4a66-8d90-2bca5e4c6709
**Base Model**: Qwen/Qwen2.5-1.5B-Instruct
**Adapter Size**: 8.4 MB
**Training Dataset**: company_qa_dataset.jsonl (Choles Food Technologies Q&A)
**Target Ollama Name**: choles-qa-ft

## Pre-Deployment Checklist

### 1. Verify Build Completion
```bash
# Check if new backend image exists
docker images | grep chatbot-backend

# Should show a recent image (< 1 hour old)
```

### 2. Restart Backend Services
```bash
docker-compose restart backend celery-worker

# Wait 30 seconds for services to start
sleep 30

# Verify services are healthy
docker-compose ps | grep -E "(backend|celery-worker)"
```

### 3. Verify New Transformers Version
```bash
docker-compose exec backend pip show transformers

# Expected: Version: 4.40.0 or higher (not 4.36.0)
```

## Phase 1: Deployment

### Step 1: Trigger Deployment
```bash
curl -X POST "http://localhost:8000/api/v1/finetuning/models-public/242b3688-f220-47a4-b146-64e33d14a244/deploy" \
  -H "Content-Type: application/json" \
  -d '{
    "deployment_target": "ollama",
    "deployment_config": {
      "model_name": "choles-qa-ft",
      "base_model": "Qwen/Qwen2.5-1.5B-Instruct"
    }
  }'
```

**Expected Response**:
```json
{
  "status": "deploying",
  "model_id": "242b3688-f220-47a4-b146-64e33d14a244",
  "ollama_model_name": "choles-qa-ft"
}
```

**NOT Expected** (old error):
```json
{
  "detail": "Failed to merge adapter into base model: KeyError: 'qwen2'"
}
```

### Step 2: Monitor Deployment Progress

```bash
# Watch backend logs
docker-compose logs -f backend | grep -E "(🚀|Deploy|merge|GGUF|✅|❌)"
```

**Expected Log Sequence**:
```
🚀 Deploying model choles-qa-real-training49_model to Ollama as choles-qa-ft
   Adapter path: /workspace/finetuning/dfcb97c3-8167-4a66-8d90-2bca5e4c6709/output/adapter_model
   Base model: Qwen/Qwen2.5-1.5B-Instruct

[0-3 min] 🔄 Merging adapter into base model...
[0-3 min] Loading base model: Qwen/Qwen2.5-1.5B-Instruct
[0-3 min] Loading adapter from adapter_model
[0-3 min] Merging...
[0-3 min] ✅ Merge completed: /workspace/finetuning/.../merged_model

[3-13 min] 🔄 Converting to GGUF...
[3-13 min] Cloning llama.cpp (if needed)
[3-13 min] Converting HuggingFace model to GGUF
[3-13 min] Quantizing to q4_K_M
[3-13 min] ✅ GGUF created: ~900 MB

[13-15 min] 🔄 Deploying to Ollama...
[13-15 min] Generating Modelfile
[13-15 min] Creating model in Ollama
[13-15 min] ✅ Model deployed to Ollama: choles-qa-ft
```

### Step 3: Verify Deployment in Database

```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
  SELECT id, name, status, ollama_model_name, deployment_url
  FROM finetuned_models
  WHERE id = '242b3688-f220-47a4-b146-64e33d14a244';
"
```

**Expected**:
```
status = 'deployed'
ollama_model_name = 'choles-qa-ft'
deployment_url = 'http://ollama:11434/api/generate'
```

## Phase 2: Ollama Verification

### Step 1: Check Model in Ollama
```bash
docker-compose exec ollama ollama list
```

**Expected Output**:
```
NAME                MODIFIED        SIZE
choles-qa-ft        X minutes ago   900 MB
```

### Step 2: Verify Model Files
```bash
docker-compose exec backend ls -lah /workspace/finetuning/dfcb97c3-8167-4a66-8d90-2bca5e4c6709/output/
```

**Expected**:
```
drwxr-xr-x adapter_model/    # 8.4 MB (original LoRA adapter)
drwxr-xr-x merged_model/     # ~3 GB (merged full model)
drwxr-xr-x gguf/              # ~900 MB (GGUF quantized)
```

## Phase 3: Inference Testing

### Test Questions (From Training Data)

Based on the dataset we inspected earlier, here are test questions:

1. **Company Overview**:
   ```
   Q: "What is Choles Food Technologies?"
   Expected: "Choles Food Technologies specializes in automated food quality assessment systems..."
   ```

2. **Main Product**:
   ```
   Q: "What is the main product of Choles Food Technologies?"
   Expected: "TomatoGrade AI system for tomato color and ripeness grading"
   ```

3. **TomatoGrade AI**:
   ```
   Q: "What is TomatoGrade AI?"
   Expected: Information about automated tomato grading system
   ```

4. **Technology**:
   ```
   Q: "What technology does Choles Food Technologies use?"
   Expected: Computer vision, AI, machine learning for food quality assessment
   ```

### Test 1: Ollama CLI
```bash
# Test Question 1
docker-compose exec ollama ollama run choles-qa-ft "What is Choles Food Technologies?"

# Test Question 2
docker-compose exec ollama ollama run choles-qa-ft "What is the main product of Choles Food Technologies?"

# Test Question 3
docker-compose exec ollama ollama run choles-qa-ft "What is TomatoGrade AI?"
```

**Success Criteria**:
- ✅ Model responds (no errors)
- ✅ Response mentions "Choles Food Technologies"
- ✅ Response mentions "TomatoGrade AI" or "tomato grading"
- ✅ Response is coherent and relevant to the question
- ✅ Response reflects training data (company-specific info)

### Test 2: Via Backend API
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Choles Food Technologies?",
    "model": "choles-qa-ft"
  }'
```

**Expected Response**:
```json
{
  "answer": "Choles Food Technologies specializes in automated food quality assessment systems, with their flagship product being the TomatoGrade AI system...",
  "model": "choles-qa-ft",
  "sources": []
}
```

### Test 3: Comparison with Base Model

To verify fine-tuning worked, compare responses:

```bash
# Fine-tuned model
echo "=== FINE-TUNED MODEL ==="
docker-compose exec ollama ollama run choles-qa-ft "What is Choles Food Technologies?"

# Base model (if available)
echo "=== BASE MODEL (for comparison) ==="
docker-compose exec ollama ollama run qwen2.5:1.5b-instruct "What is Choles Food Technologies?"
```

**Expected Difference**:
- Base model: Generic response or "I don't have information..."
- Fine-tuned model: Specific company details from training data

## Phase 4: Chat UI Integration (Optional)

### Step 1: Check Model Dropdown
1. Open http://localhost:3001
2. Look for model dropdown/selector
3. Verify "choles-qa-ft" appears in the list

### Step 2: Test Chat
1. Select "choles-qa-ft" from dropdown
2. Ask: "What is Choles Food Technologies?"
3. Ask: "What is TomatoGrade AI?"
4. Ask: "What products does the company offer?"

**Success Criteria**:
- ✅ Model appears in dropdown
- ✅ Can select and use model
- ✅ Responses are company-specific
- ✅ No errors in UI

## Validation Checklist

### Deployment Success
- [ ] Build completed successfully (transformers >=4.40.0)
- [ ] Backend restarted without errors
- [ ] Deployment API call succeeded
- [ ] Merge operation completed (no KeyError)
- [ ] GGUF conversion completed
- [ ] Ollama deployment completed
- [ ] Database status = 'deployed'
- [ ] ollama_model_name = 'choles-qa-ft'

### Model Verification
- [ ] Model appears in `ollama list`
- [ ] Model size ~900 MB (GGUF)
- [ ] merged_model directory exists (~3 GB)
- [ ] gguf directory exists (~900 MB)

### Inference Quality
- [ ] Model responds to questions (no errors)
- [ ] Responses include company-specific information
- [ ] Responses mention "Choles Food Technologies"
- [ ] Responses mention "TomatoGrade AI"
- [ ] Responses are coherent and relevant
- [ ] Fine-tuned model performs better than base model

### Integration
- [ ] Model appears in chat UI dropdown
- [ ] Can be selected and used in chat
- [ ] Backend API accepts model name
- [ ] No errors in logs during inference

## Troubleshooting

### Issue: Merge Still Fails with KeyError
**Check**:
```bash
docker-compose exec backend python -c "import transformers; print(transformers.__version__)"
```

**Solution**: If still 4.36.0, backend didn't restart with new image:
```bash
docker-compose stop backend celery-worker
docker-compose up -d backend celery-worker
```

### Issue: GGUF Conversion Fails
**Check llama.cpp**:
```bash
docker-compose exec backend ls -la /tmp/llama.cpp
```

**Solution**: If missing, llama.cpp clone failed. Check network/disk space.

### Issue: Model Not in Ollama
**Check Ollama logs**:
```bash
docker-compose logs ollama | tail -100
```

**Check Modelfile**:
```bash
docker-compose exec backend ls -la /workspace/finetuning/dfcb97c3-8167-4a66-8d90-2bca5e4c6709/output/gguf/
```

### Issue: Poor Inference Quality
**Possible causes**:
1. Model deployed but using base model (not fine-tuned)
2. GGUF conversion corrupted weights
3. Adapter didn't merge correctly

**Verification**:
```bash
# Check merged model size (should be ~3 GB, not 1.5 GB)
docker-compose exec backend du -sh /workspace/finetuning/dfcb97c3-8167-4a66-8d90-2bca5e4c6709/output/merged_model
```

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| **Deployment Time** | 10-15 minutes | ⏳ |
| **Merge Success** | No KeyError | ⏳ |
| **GGUF Size** | ~900 MB | ⏳ |
| **Ollama Listing** | choles-qa-ft present | ⏳ |
| **Inference Speed** | 30-50 tokens/sec | ⏳ |
| **Response Quality** | Company-specific info | ⏳ |
| **UI Integration** | Model in dropdown | ⏳ |

## Timeline

| Time | Event |
|------|-------|
| T+0 | Backend build completes |
| T+1 | Backend restarted |
| T+2 | Deployment triggered |
| T+5 | Merge completes |
| T+15 | GGUF conversion completes |
| T+17 | Ollama deployment completes |
| T+18 | First inference test |
| T+20 | Full validation complete |

---

**Test Start**: After backend build completes
**Expected Duration**: 20-25 minutes total
**Final Goal**: Working fine-tuned model answering Choles Food Technologies questions accurately
