# Testing Ollama Deployment - Quick Guide

## Your Model Info

**Model ID**: `242b3688-f220-47a4-b146-64e33d14a244`
**Model Name**: `choles-qa-real-training49_model`
**Job ID**: `dfcb97c3-8167-4a66-8d90-2bca5e4c6709`
**Base Model**: `Qwen/Qwen2.5-1.5B-Instruct`
**Adapter Location**: `/workspace/finetuning/dfcb97c3-8167-4a66-8d90-2bca5e4c6709/output/adapter_model`

## Option 1: Deploy via UI (Recommended)

### Steps:
1. **Login** to your application
2. **Navigate** to: Governance & Audit → Model Registry
3. **Find** model: "choles-qa-real-training49_model"
4. **Click** "⚡ Deploy to Ollama" button
5. **Wait** ~10-15 minutes (watch backend logs for progress)
6. **Verify** status changes to "Deployed"
7. **Test** in Chat UI by selecting the model from dropdown

### Expected Timeline:
```
[00:00] Deploy button clicked
[00:01] Adapter detected, starting merge...
[03:00] Merge complete, starting GGUF conversion...
[13:00] GGUF complete, deploying to Ollama...
[15:00] ✅ Deployment complete!
```

## Option 2: Deploy via API

### Using curl:
```bash
# Set your auth token
TOKEN="your-jwt-token-here"

# Deploy model
curl -X POST \
  http://localhost:8000/api/v1/finetuning/models/242b3688-f220-47a4-b146-64e33d14a244/deploy-ollama \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name_override": "choles-qa-ft",
    "parameters": "{\"temperature\": 0.7, \"top_p\": 0.9}"
  }'
```

### Expected Response:
```json
{
  "status": "deployed",
  "model_id": "242b3688-f220-47a4-b146-64e33d14a244",
  "model_name": "choles-qa-real-training49_model",
  "ollama_model_name": "choles-qa-ft",
  "deployment_url": "http://ollama:11434/api/generate",
  "merged_model_path": "/workspace/finetuning/dfcb97c3-8167-4a66-8d90-2bca5e4c6709/output/merged_model",
  "gguf_path": "/workspace/finetuning/dfcb97c3-8167-4a66-8d90-2bca5e4c6709/output/gguf/model-q4_K_M.gguf",
  "message": "Model successfully deployed to Ollama as 'choles-qa-ft'"
}
```

## Monitoring Deployment Progress

### Backend Logs:
```bash
# Follow backend logs
docker-compose logs -f backend | grep -E "ollama|deploy|merge|gguf"

# Expected output:
# 🚀 Deploying model choles-qa-ft to Ollama
# 📦 Detected LoRA adapter - merge required for Ollama
# 🔄 Merging adapter into base model...
# Loading base model (this may take 2-3 minutes)...
# Loading adapter...
# Merging (this may take 2-3 minutes)...
# ✅ Merge completed successfully
# 🔄 Converting merged model to GGUF for Ollama...
# Converting to GGUF (this may take 5-10 minutes)...
# ✅ GGUF created: 900.5 MB at /workspace/.../gguf/model-q4_K_M.gguf
# ✅ Model deployed to Ollama: choles-qa-ft
```

### Database Status:
```bash
# Check model status in database
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT
  name,
  status,
  ollama_model_name,
  deployment_url
FROM finetuned_models
WHERE id = '242b3688-f220-47a4-b146-64e33d14a244';
"

# Expected output:
#              name               | status  | ollama_model_name |      deployment_url
# --------------------------------+---------+-------------------+---------------------------
#  choles-qa-real-training49_model| deployed| choles-qa-ft      | http://ollama:11434/...
```

## Verifying Deployment

### Check Ollama:
```bash
# List Ollama models
docker-compose exec ollama ollama list

# Expected output should include:
# NAME              ID              SIZE      MODIFIED
# choles-qa-ft      abc123def...    900 MB    2 minutes ago
```

### Test Inference:
```bash
# Test with Ollama CLI
docker-compose exec ollama ollama run choles-qa-ft "What is Choles Food Technologies?"

# Expected response (based on training data):
# Choles Food Technologies is a company that develops AI-powered solutions
# for the food industry, including TomatoGrade, an automated tomato quality
# assessment system...
```

### Test via API:
```bash
# Query Ollama API directly
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "choles-qa-ft",
    "prompt": "What is TomatoGrade?",
    "stream": false
  }' | jq '.response'
```

## Testing in Chat UI

### Steps:
1. **Open** chat interface (http://localhost:3001)
2. **Click** model dropdown
3. **Select** "choles-qa-ft" (or your model name)
4. **Ask** test questions:
   - "What is Choles Food Technologies?"
   - "What is TomatoGrade?"
   - "How does TomatoGrade AI determine tomato quality?"
   - "What are the benefits of using TomatoGrade?"

### Expected Behavior:
- Model responds with information from training data
- Answers are specific to Choles/TomatoGrade
- Response quality reflects fine-tuned knowledge

## Troubleshooting

### Issue: Deployment stuck at "Merging..."
```bash
# Check if transformers/peft dependencies are available
docker-compose exec backend python -c "
import transformers
import peft
print('✅ Dependencies OK')
"

# Check GPU availability
nvidia-smi
```

### Issue: GGUF conversion fails
```bash
# Check if llama.cpp cloned successfully
docker-compose exec backend ls -la /tmp/llama.cpp

# Manual conversion test
docker-compose exec backend bash -c "
cd /tmp/llama.cpp
python convert_hf_to_gguf.py --help
"
```

### Issue: Model not appearing in Ollama
```bash
# Check Ollama logs
docker-compose logs ollama | tail -50

# Verify Ollama is healthy
curl http://localhost:11434/api/tags
```

### Issue: Chat UI doesn't show model
```bash
# Check model registry API
curl http://localhost:8000/api/v1/finetuning/models-chat | jq '.[] | select(.status=="deployed")'

# Refresh UI (Ctrl+Shift+R)
# Check browser console for errors
```

## Cleanup / Undeploy

### Via UI:
1. Navigate to: Governance & Audit → Model Registry
2. Find model: "choles-qa-real-training49_model"
3. Click "Undeploy" button

### Via API:
```bash
curl -X POST \
  http://localhost:8000/api/v1/finetuning/models/242b3688-f220-47a4-b146-64e33d14a244/undeploy \
  -H "Authorization: Bearer ${TOKEN}"
```

### Via Ollama CLI:
```bash
# Remove model from Ollama
docker-compose exec ollama ollama rm choles-qa-ft
```

## Performance Benchmarks

### Inference Speed (Approximate):
- **Tokens/sec**: ~30-50 tokens/sec (depends on GPU)
- **First token latency**: ~500ms
- **Memory usage**: ~2-3 GB GPU RAM

### Model Sizes:
- **Adapter**: 8.4 MB
- **Merged (FP16)**: 2.8 GB
- **GGUF (q4_K_M)**: ~900 MB

## Next Steps After Deployment

1. **Test thoroughly** with multiple questions
2. **Compare** responses to base model
3. **Evaluate** quality using test questions
4. **Monitor** performance metrics
5. **Iterate** on training data if needed
6. **Deploy** to production environment

---

**Summary**: `/tmp/OLLAMA_DEPLOYMENT_UPDATE_SUMMARY.md`
**Status**: Ready to test
**Estimated Time**: 10-15 minutes for first deployment
