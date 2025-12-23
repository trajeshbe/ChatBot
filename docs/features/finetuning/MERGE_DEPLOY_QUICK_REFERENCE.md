# Model Merge & Deploy - Quick Reference

> **Quick guide for ML engineers to merge and deploy fine-tuned models**

---

## 🚀 Quick Start (3 Steps)

### Step 1: Request Merge (5-15 min)

**UI Path**: Admin → Fine-Tuning Hub → **Merge Models**

1. Find your model (blue "Adapter Only" badge)
2. Click: **Request Merge**
3. Confirm dialog
4. Wait for green "Merged" badge (auto-updates)

**API**:
```bash
curl -X POST http://localhost:8000/api/v1/finetuning/models/{model_id}/merge \
  -H "Content-Type: application/json" \
  -d '{
    "base_model_name": "Qwen/Qwen2.5-1.5B-Instruct",
    "force_cpu": false
  }'
```

---

### Step 2: Deploy to Ollama (1 min)

**UI Path**: Fine-Tuning Hub → **Deployment** tab

1. Select your merged model
2. Choose deployment target: `ollama`
3. Enter model name: `my-model-v1`
4. Click: **Deploy Model**

**API**:
```bash
curl -X POST http://localhost:8000/api/v1/finetuning/models/{model_id}/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "deployment_target": "ollama",
    "deployment_config": {
      "model_name": "my-model-v1"
    }
  }'
```

---

### Step 3: Use in Chat

**UI Path**: Chat page → Model dropdown

1. Open model selector
2. Find your model in "Ollama" section
3. Select and start chatting!

---

## 📋 Status Reference

| Badge | Meaning | Next Action |
|-------|---------|-------------|
| 🔵 Adapter Only | Not merged | Click "Request Merge" |
| 🟡 Merging... | In progress | Wait 5-15 min |
| 🟢 Merged | Ready | Click "Deploy Model" |
| 🔴 Merge Failed | Error | Click "Retry Merge" |
| ✅ Deployed | Live | Use in Chat |

---

## 🔍 Check Status

### UI
- **Merge Models** page: Real-time status badges
- **Deployment** tab: Merge warnings/success

### API
```bash
# Get merge status
curl http://localhost:8000/api/v1/finetuning/models/{model_id}/merge-status

# Get all models
curl http://localhost:8000/api/v1/finetuning/models-public
```

### Database
```sql
SELECT name, status, merged_model_path, merge_duration_seconds
FROM finetuned_models
WHERE status IN ('merging', 'merged', 'deployed')
ORDER BY merge_requested_at DESC;
```

---

## ⚠️ Common Issues

### "Model must be merged before deployment"
✅ **Solution**: Go to Merge Models → Request Merge → Wait for completion

### Merge stuck at "Merging..." for > 20 min
✅ **Solution**: Check Celery worker logs
```bash
docker-compose logs celery-worker
```

### Deployed model not in Chat UI dropdown
✅ **Solution**: Verify deployment
```bash
curl http://localhost:11434/api/tags  # Check Ollama
```
Then refresh Chat UI

---

## 🎯 Best Practices

1. **Always merge before deploy** - Deploying adapters directly is not supported
2. **Wait for merge to complete** - Don't deploy while status is "merging"
3. **Use descriptive names** - e.g., `customer-support-qwen-v2`
4. **Test before deploying** - Use evaluation metrics first
5. **Monitor performance** - Check inference latency after deployment

---

## 📞 Need Help?

- **Documentation**: `docs/features/finetuning/MODEL_MERGE_AND_DEPLOY_COMPLETE.md`
- **Logs**: `docker-compose logs backend celery-worker`
- **Support**: Check Celery task status and database records

---

**Powered by**: LoRA + PEFT + Celery + Ollama
